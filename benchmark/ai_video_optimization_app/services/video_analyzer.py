"""Video Quality Analysis service.

Submits generated videos to LM Studio for structured quality evaluation
and produces QAReport objects for the orchestration engine.
"""

from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from loguru import logger

from orchestrator.config import LMStudioConfig
from orchestrator.exceptions import (
    LMStudioConnectionError,
    LMStudioResponseError,
    LMStudioTimeoutError,
    ReportValidationError,
    VideoNotFoundError,
)
from orchestrator.models import QAReport


class VideoAnalyzer:
    """Analyzes generated videos using LM Studio vision model.

    Submits MP4 files to an OpenAI-compatible Chat Completions API,
    parses structured JSON responses, and persists QA reports.
    """

    _prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "video_analysis.md"

    def __init__(self, config: LMStudioConfig) -> None:
        """Initialize the analyzer with LM Studio configuration.

        Args:
            config: LM Studio connection settings.
        """
        self._config = config
        self._base_url = f"http://{config.host}:{config.port}/v1"
        self._system_prompt = self._load_prompt()
        logger.info(f"VideoAnalyzer initialized: {self._base_url}")

    # ── Public API ───────────────────────────────────────────────

    def analyze(self, video_path: str | Path) -> QAReport:
        """Analyze a video and return a structured QA report.

        Encodes the video as base64 and submits it to LM Studio's
        OpenAI-compatible vision endpoint. Parses and validates the
        JSON response into a QAReport.

        Args:
            video_path: Path to the MP4 file to analyze.

        Returns:
            Validated QAReport.

        Raises:
            VideoNotFoundError: If the video file does not exist.
            LMStudioConnectionError: If LM Studio is unreachable.
            LMStudioTimeoutError: If the request times out.
            LMStudioResponseError: If the response is malformed.
            ReportValidationError: If the parsed report fails validation.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise VideoNotFoundError(f"Video not found: {video_path}")

        logger.info(f"Analysis started: {video_path.name}")
        start = time.monotonic()

        # Encode video
        base64_video = base64.b64encode(video_path.read_bytes()).decode("utf-8")
        mime_type = "video/mp4" if video_path.suffix == ".mp4" else "video/*"

        # Build request
        url = f"{self._base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": self._config.model,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_video}",
                            },
                        },
                        {
                            "type": "text",
                            "text": "Analyze this video and return a structured JSON quality report.",
                        },
                    ],
                },
            ],
            "temperature": 0.0,
        }

        # Submit request
        try:
            response = httpx.post(
                url,
                json=payload,
                timeout=self._config.timeout,
            )
        except httpx.ConnectError as exc:
            raise LMStudioConnectionError(
                f"Cannot connect to LM Studio at {self._base_url}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise LMStudioTimeoutError(
                f"LM Studio request timed out after {self._config.timeout}s: {exc}"
            ) from exc

        duration = time.monotonic() - start

        if response.status_code != 200:
            raise LMStudioResponseError(
                f"LM Studio returned HTTP {response.status_code}: {response.text[:500]}"
            )

        # Parse response
        try:
            body = response.json()
        except json.JSONDecodeError as exc:
            raise LMStudioResponseError(
                f"Invalid JSON from LM Studio: {exc}"
            ) from exc

        # Extract content from OpenAI-compatible response
        try:
            raw_text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LMStudioResponseError(
                f"Unexpected response structure from LM Studio: {exc}"
            ) from exc

        # Log token usage if available
        if "usage" in body:
            usage = body["usage"]
            logger.info(
                f"Token usage: prompt={usage.get('prompt_tokens', '?')}, "
                f"completion={usage.get('completion_tokens', '?')}, "
                f"total={usage.get('total_tokens', '?')}"
            )

        logger.info(f"Analysis finished: {video_path.name} duration={duration:.1f}s")

        # Parse and validate report
        report = self._parse_response(raw_text, video_path)
        return report

    def validate_report(self, report: QAReport) -> bool:
        """Validate a QA report has all required fields with correct ranges.

        Args:
            report: QA report to validate.

        Returns:
            True if valid.

        Raises:
            ReportValidationError: If validation fails.
        """
        try:
            report.model_validate(report.model_dump())
        except Exception as exc:
            raise ReportValidationError(f"Report validation failed: {exc}") from exc

        # Check score ranges
        score_fields = [
            "overall_score",
            "identity_score",
            "motion_score",
            "camera_score",
            "hands_score",
            "face_score",
            "lighting_score",
            "physics_score",
            "lip_sync_score",
            "continuity_score",
        ]
        for field in score_fields:
            value = getattr(report, field)
            if not (0.0 <= value <= 1.0):
                raise ReportValidationError(
                    f"Score '{field}'={value} out of range [0.0, 1.0]"
                )

        logger.info("Report validation passed")
        return True

    def save_report(
        self,
        report: QAReport,
        experiment_id: str,
        iteration: int,
        experiments_dir: str | Path = "experiments",
        candidate_number: Optional[int] = None,
    ) -> Path:
        """Save QA report files to the experiment directory.

        Creates:
            experiments/<experiment_id>/iteration_<N>/[candidate_<N>/]
                qa_report.json  - validated report
                qa_raw.json     - raw LLM response
                analysis.log    - analysis metadata

        Args:
            report: Validated QA report.
            experiment_id: Experiment identifier.
            iteration: Iteration number.
            experiments_dir: Base experiments directory.
            candidate_number: Optional candidate number within iteration.

        Returns:
            Path to the report directory.
        """
        experiments_dir = Path(experiments_dir)
        if candidate_number is not None:
            report_dir = (
                experiments_dir / experiment_id
                / f"iteration_{iteration:03d}"
                / f"candidate_{candidate_number:03d}"
            )
        else:
            report_dir = (
                experiments_dir / experiment_id
                / f"iteration_{iteration:03d}"
            )
        report_dir.mkdir(parents=True, exist_ok=True)

        # Save validated report
        report_path = report_dir / "qa_report.json"
        report_path.write_text(json.dumps(report.model_dump(mode="json"), indent=2))

        # Save raw response
        raw_path = report_dir / "qa_raw.json"
        raw_path.write_text(
            json.dumps({"raw_response": report.raw_response}, indent=2)
        )

        # Save analysis log
        log_path = report_dir / "analysis.log"
        log_entry = {
            "experiment_id": experiment_id,
            "iteration": iteration,
            "iteration_id": report.iteration_id,
            "timestamp": report.timestamp.isoformat(),
            "overall_score": report.overall_score,
            "scores": {
                "identity": report.identity_score,
                "motion": report.motion_score,
                "camera": report.camera_score,
                "hands": report.hands_score,
                "face": report.face_score,
                "lighting": report.lighting_score,
                "physics": report.physics_score,
                "lip_sync": report.lip_sync_score,
                "continuity": report.continuity_score,
            },
            "issues_count": len(report.issues),
            "recommendations_count": len(report.recommendations),
        }
        log_path.write_text(json.dumps(log_entry, indent=2))

        logger.info(f"Report saved: {iter_dir}")
        return iter_dir

    # ── Internal helpers ─────────────────────────────────────────

    @classmethod
    def _load_prompt(cls) -> str:
        """Load the video analysis system prompt from disk."""
        if cls._prompt_path.exists():
            return cls._prompt_path.read_text().strip()
        logger.warning(
            f"Prompt file not found at {cls._prompt_path}; using default"
        )
        return "Analyze this video and return a structured JSON quality report."

    def _parse_response(
        self, raw_text: str, video_path: Path
    ) -> QAReport:
        """Parse raw LLM response into a validated QAReport.

        Strips markdown code fences if present, then attempts JSON parsing.
        """
        # Strip markdown code fences
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LMStudioResponseError(
                f"Failed to parse JSON from LLM response: {exc}\n"
                f"Raw response: {raw_text[:500]}"
            ) from exc

        # Build QAReport with raw response preserved
        report_data: dict[str, Any] = {
            "iteration_id": str(video_path),
            "overall_score": data.get("overall_score", 0.0),
            "identity_score": data.get("identity_score", 0.0),
            "motion_score": data.get("motion_score", 0.0),
            "camera_score": data.get("camera_score", 0.0),
            "hands_score": data.get("hands_score", 0.0),
            "face_score": data.get("face_score", 0.0),
            "lighting_score": data.get("lighting_score", 0.0),
            "physics_score": data.get("physics_score", 0.0),
            "lip_sync_score": data.get("lip_sync_score", 0.0),
            "continuity_score": data.get("continuity_score", 0.0),
            "issues": data.get("issues", []),
            "strengths": data.get("strengths", []),
            "summary": data.get("summary", ""),
            "recommendations": data.get("recommendations", []),
            "raw_response": raw_text,
            "timestamp": datetime.now(timezone.utc),
        }

        try:
            report = QAReport(**report_data)
            self.validate_report(report)
        except ReportValidationError:
            raise
        except Exception as exc:
            raise ReportValidationError(
                f"Failed to construct QAReport from response: {exc}\n"
                f"Data: {json.dumps(data, indent=2)[:500]}"
            ) from exc

        return report