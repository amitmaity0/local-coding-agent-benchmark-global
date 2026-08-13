"""Optimizer service for prompt and parameter optimization.

Sends the current generation parameters and QA report to LM Studio
and produces an OptimizationResult with improved settings for the
next iteration.
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from loguru import logger

from orchestrator.config import LMStudioConfig
from orchestrator.exceptions import (
    MissingQAResportError,
    OptimizationConnectionError,
    OptimizationError,
    OptimizationResponseError,
    OptimizationTimeoutError,
    OptimizationValidationError,
)
from orchestrator.models import Job, OptimizationResult, QAReport


class Optimizer:
    """Optimizes generation prompts and parameters using LM Studio.

    Receives the current generation parameters and QA report, then asks
    an LLM to produce an improved prompt and updated generation parameters.
    Does NOT execute another generation — only produces the next candidate.
    """

    _prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "optimization.md"

    def __init__(self, config: LMStudioConfig) -> None:
        """Initialize the optimizer with LM Studio configuration.

        Args:
            config: LM Studio connection settings.
        """
        self._config = config
        self._base_url = f"http://{config.host}:{config.port}/v1"
        self._system_prompt = self._load_prompt()
        logger.info(f"Optimizer initialized: {self._base_url}")

    # ── Public API ─────────────────────────────────────────────────

    def optimize(
        self,
        job: Job,
        qa_report: QAReport,
        optimization_context: dict | None = None,
    ) -> OptimizationResult:
        """Request LLM to optimize prompt and parameters.

        Sends the current prompt, negative prompt, generation parameters,
        QA report, and optional optimization context to LM Studio.
        Receives structured JSON and validates it into an OptimizationResult.

        Args:
            job: Current job containing experiment context.
            qa_report: Quality analysis report from the previous iteration.
            optimization_context: Optional context from optimization strategy,
                including mode, focus areas, parameters to modify/preserve.

        Returns:
            Validated OptimizationResult.

        Raises:
            MissingQAResportError: If qa_report is None.
            OptimizationConnectionError: If LM Studio is unreachable.
            OptimizationTimeoutError: If the request times out.
            OptimizationResponseError: If the response is malformed.
            OptimizationValidationError: If the response fails validation.
        """
        if qa_report is None:
            raise MissingQAResportError(
                "QA report is required for optimization but was not provided"
            )

        logger.info(
            f"Optimization started: experiment={job.experiment_id} "
            f"iteration={job.iteration}"
        )
        start = time.monotonic()

        # Build user message with context
        user_content = self._build_optimization_request(
            qa_report, optimization_context
        )

        # Build request payload
        payload: dict[str, Any] = {
            "model": self._config.model,
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }

        # Submit request
        raw_response = ""
        try:
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                timeout=self._config.timeout,
            )
        except httpx.ConnectError as exc:
            raise OptimizationConnectionError(
                f"Cannot connect to LM Studio at {self._base_url}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise OptimizationTimeoutError(
                f"Optimization request timed out after {self._config.timeout}s: {exc}"
            ) from exc

        duration = time.monotonic() - start

        if response.status_code != 200:
            raise OptimizationResponseError(
                f"LM Studio returned HTTP {response.status_code}: {response.text[:500]}"
            )

        # Parse API response
        try:
            body = response.json()
        except json.JSONDecodeError as exc:
            raise OptimizationResponseError(
                f"Invalid JSON from LM Studio: {exc}"
            ) from exc

        # Extract content
        try:
            raw_response = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise OptimizationResponseError(
                f"Unexpected response structure from LM Studio: {exc}"
            ) from exc

        # Log token usage
        if "usage" in body:
            usage = body["usage"]
            logger.info(
                f"Optimization token usage: "
                f"prompt={usage.get('prompt_tokens', '?')}, "
                f"completion={usage.get('completion_tokens', '?')}, "
                f"total={usage.get('total_tokens', '?')}"
            )

        logger.info(
            f"Optimization response received: {job.experiment_id} "
            f"iter={job.iteration} duration={duration:.1f}s"
        )

        # Parse and validate
        result = self._parse_response(
            raw_response, job, optimization_context
        )
        return result

    @staticmethod
    def validate_response(response: OptimizationResult) -> bool:
        """Validate an OptimizationResult has all required fields with correct ranges.

        Args:
            response: OptimizationResult to validate.

        Returns:
            True if valid.

        Raises:
            OptimizationValidationError: If validation fails.
        """
        try:
            response.model_validate(response.model_dump())
        except Exception as exc:
            raise OptimizationValidationError(
                f"Optimization result validation failed: {exc}"
            ) from exc

        # Validate parameter constraints explicitly
        if not (0.5 <= response.new_cfg <= 10.0):
            raise OptimizationValidationError(
                f"CFG {response.new_cfg} out of range [0.5, 10.0]"
            )
        if not (0.0 <= response.new_noise <= 1.0):
            raise OptimizationValidationError(
                f"Noise {response.new_noise} out of range [0.0, 1.0]"
            )
        if not (1 <= response.new_steps <= 100):
            raise OptimizationValidationError(
                f"Steps {response.new_steps} out of range [1, 100]"
            )
        if response.new_seed <= 0:
            raise OptimizationValidationError(
                f"Seed {response.new_seed} must be a positive integer"
            )
        if not (0.0 <= response.confidence <= 1.0):
            raise OptimizationValidationError(
                f"Confidence {response.confidence} out of range [0.0, 1.0]"
            )

        logger.info("Optimization result validation passed")
        return True

    def save_optimization(
        self,
        result: OptimizationResult,
        experiment_id: str,
        iteration: int,
        experiments_dir: str | Path = "experiments",
    ) -> Path:
        """Save optimization result files to the experiment directory.

        Creates:
            experiments/<experiment_id>/iteration_<N>/
                optimization.json   - validated optimization result
                optimization_raw.json - raw LLM response

        Args:
            result: Validated OptimizationResult.
            experiment_id: Experiment identifier.
            iteration: Iteration number.
            experiments_dir: Base experiments directory.

        Returns:
            Path to the iteration directory.
        """
        experiments_dir = Path(experiments_dir)
        iter_dir = experiments_dir / experiment_id / f"iteration_{iteration:03d}"
        iter_dir.mkdir(parents=True, exist_ok=True)

        # Save validated result
        opt_path = iter_dir / "optimization.json"
        opt_path.write_text(json.dumps(result.model_dump(mode="json"), indent=2))

        # Save raw response
        raw_path = iter_dir / "optimization_raw.json"
        raw_path.write_text(
            json.dumps({"raw_response": result.raw_response}, indent=2)
        )

        logger.info(
            f"Optimization saved: {iter_dir} "
            f"confidence={result.confidence:.2f}"
        )
        return iter_dir

    # ── Internal helpers ───────────────────────────────────────────

    @classmethod
    def _load_prompt(cls) -> str:
        """Load the optimization system prompt from disk."""
        if cls._prompt_path.exists():
            return cls._prompt_path.read_text().strip()
        logger.warning(
            f"Optimization prompt not found at {cls._prompt_path}; using default"
        )
        return "You are a video generation prompt and parameter optimizer."

    def _build_optimization_request(
        self,
        qa_report: QAReport,
        optimization_context: dict | None = None,
    ) -> str:
        """Build the user message for the optimization request.

        Args:
            qa_report: QA report containing current state and feedback.
            optimization_context: Optional strategy context with mode,
                focus areas, parameters to modify/preserve.

        Returns:
            Formatted user message string.
        """
        scores = {
            "overall": qa_report.overall_score,
            "identity": qa_report.identity_score,
            "motion": qa_report.motion_score,
            "camera": qa_report.camera_score,
            "hands": qa_report.hands_score,
            "face": qa_report.face_score,
            "lighting": qa_report.lighting_score,
            "physics": qa_report.physics_score,
            "lip_sync": qa_report.lip_sync_score,
            "continuity": qa_report.continuity_score,
        }

        lines = [
            "## Current Generation Parameters",
            f"- Overall QA Score: {qa_report.overall_score:.3f}",
            "",
            "### Per-Dimension Scores",
        ]
        for dim, score in scores.items():
            lines.append(f"- {dim}: {score:.3f}")

        lines.append("")
        if qa_report.issues:
            lines.append("### Issues")
            for issue in qa_report.issues:
                lines.append(f"- {issue}")

        lines.append("")
        if qa_report.strengths:
            lines.append("### Strengths")
            for strength in qa_report.strengths:
                lines.append(f"- {strength}")

        lines.append("")
        if qa_report.recommendations:
            lines.append("### Recommendations")
            for rec in qa_report.recommendations:
                lines.append(f"- {rec}")

        lines.append("")
        if qa_report.summary:
            lines.append(f"### Summary\n{qa_report.summary}")

        # Add strategy context if available
        if optimization_context:
            lines.append("")
            lines.append("## Optimization Strategy")
            mode = optimization_context.get("optimization_mode", "REFINE")
            lines.append(f"- Mode: {mode}")

            focus = optimization_context.get("focus_areas", [])
            if focus:
                lines.append(f"- Focus Areas: {', '.join(focus)}")

            modified = optimization_context.get("parameters_modified", [])
            if modified:
                lines.append(f"- Parameters to Modify: {', '.join(modified)}")

            preserved = optimization_context.get("parameters_preserved", [])
            if preserved:
                lines.append(
                    f"- Parameters to Preserve (DO NOT CHANGE): "
                    f"{', '.join(preserved)}"
                )

            reasoning = optimization_context.get("strategy_reasoning", "")
            if reasoning:
                lines.append(f"- Strategy Reasoning: {reasoning}")

            iteration = optimization_context.get("iteration_number")
            if iteration is not None:
                lines.append(f"- Iteration Number: {iteration}")

        lines.append(
            "\nPlease produce an improved prompt and updated parameters "
            "to address the issues above."
        )
        return "\n".join(lines)

    def _parse_response(
        self,
        raw_text: str,
        job: Job,
        optimization_context: dict | None = None,
    ) -> OptimizationResult:
        """Parse raw LLM response into a validated OptimizationResult.

        Strips markdown code fences if present, then attempts JSON parsing.
        Generates a new seed if one is not provided by the LLM.

        Args:
            raw_text: Raw LLM response text.
            job: Current job for context.
            optimization_context: Optional strategy context.

        Returns:
            Validated OptimizationResult.

        Raises:
            OptimizationResponseError: If JSON parsing fails.
            OptimizationValidationError: If validation fails.
        """
        # Strip markdown code fences
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first line (opening fence)
            cleaned = "\n".join(lines[1:])
            # Remove last line if it's a closing fence
            if cleaned.endswith("```"):
                cleaned = "\n".join(cleaned.split("\n")[:-1])
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise OptimizationResponseError(
                f"Failed to parse JSON from optimization response: {exc}\n"
                f"Raw response: {raw_text[:500]}"
            ) from exc

        # Build result data — generate seed if missing
        seed = data.get("new_seed")
        if seed is None or seed <= 0:
            seed = random.randint(1, 2**31 - 1)

        # Extract strategy fields from context (or from response if provided)
        opt_mode = data.get(
            "optimization_mode",
            optimization_context.get("optimization_mode", "REFINE")
            if optimization_context
            else "REFINE",
        )
        focus = data.get(
            "focus_areas",
            optimization_context.get("focus_areas", [])
            if optimization_context
            else [],
        )
        params_modified = data.get(
            "parameters_modified",
            optimization_context.get("parameters_modified", [])
            if optimization_context
            else [],
        )
        params_preserved = data.get(
            "parameters_preserved",
            optimization_context.get("parameters_preserved", [])
            if optimization_context
            else [],
        )

        result_data: dict[str, Any] = {
            "new_prompt": data.get("new_prompt", ""),
            "new_negative_prompt": data.get("new_negative_prompt", ""),
            "new_seed": seed,
            "new_cfg": data.get("new_cfg", 7.0),
            "new_noise": data.get("new_noise", 0.1),
            "new_steps": data.get("new_steps", 30),
            "reasoning": data.get("reasoning", ""),
            "parameter_changes": data.get("parameter_changes", {}),
            "expected_improvements": data.get("expected_improvements", []),
            "confidence": data.get("confidence", 0.5),
            "raw_response": raw_text,
            "timestamp": datetime.now(timezone.utc),
            "optimization_mode": opt_mode,
            "focus_areas": focus,
            "parameters_modified": params_modified,
            "parameters_preserved": params_preserved,
        }

        try:
            result = OptimizationResult(**result_data)
        except Exception as exc:
            raise OptimizationValidationError(
                f"Failed to construct OptimizationResult: {exc}\n"
                f"Data: {json.dumps(data, indent=2)[:500]}"
            ) from exc

        # Validate
        self.validate_response(result)

        # Log strategy decision
        logger.info(
            f"Optimization strategy: mode={result.optimization_mode} "
            f"focus={result.focus_areas} "
            f"modified={result.parameters_modified} "
            f"preserved={result.parameters_preserved}"
        )

        # Log parameter changes
        if result.parameter_changes:
            for param, change in result.parameter_changes.items():
                logger.info(f"Parameter change: {param} -> {change}")

        # Log prompt changes
        if result.new_prompt:
            logger.info(
                f"Prompt optimized: {len(result.new_prompt)} chars"
            )

        logger.info(
            f"Optimization completed: experiment={job.experiment_id} "
            f"iter={job.iteration} confidence={result.confidence:.2f}"
        )

        return result