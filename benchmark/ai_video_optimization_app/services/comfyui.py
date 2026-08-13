"""ComfyUI service for video generation.

Provides interface for submitting workflows, monitoring execution via
WebSocket, and retrieving generated artifacts from ComfyUI.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx
import websockets.sync.client
from loguru import logger

from orchestrator.config import ComfyUIConfig
from orchestrator.exceptions import (
    ArtifactDownloadError,
    ComfyUIConnectionError,
    ComfyUIExecutionError,
    ComfyUISubmitError,
    ComfyUITimeoutError,
    ComfyUIWebSocketError,
)


@dataclass
class GenerationResult:
    """Result from a ComfyUI generation job."""

    success: bool
    prompt_id: str = ""
    output_files: list[str] = field(default_factory=list)
    error: Optional[str] = None
    duration_seconds: float = 0.0


class ComfyUIService:
    """Service for interacting with ComfyUI.

    Handles workflow submission, WebSocket-based monitoring,
    and artifact retrieval.
    """

    def __init__(self, config: ComfyUIConfig) -> None:
        """Initialize the ComfyUI service.

        Args:
            config: ComfyUI connection configuration.
        """
        self._config = config
        self._base_url = f"http://{config.host}:{config.port}"
        self._ws_url = f"ws://{config.host}:{config.port}/ws"
        logger.info(f"ComfyUIService initialized: {self._base_url}")

    # ── Public API ────────────────────────────────────────────────

    def health_check(self) -> bool:
        """Check if ComfyUI is reachable.

        Returns:
            True if ComfyUI responds, False otherwise.
        """
        try:
            resp = httpx.get(f"{self._base_url}/system_stats", timeout=5)
            return resp.status_code == 200
        except httpx.RequestError:
            return False

    def submit_workflow(
        self,
        workflow: dict[str, Any],
        client_id: str = "",
    ) -> str:
        """Submit a workflow to ComfyUI for execution.

        Args:
            workflow: The ComfyUI workflow JSON (node dict).
            client_id: Optional client ID for WebSocket subscription.

        Returns:
            The prompt_id returned by ComfyUI.

        Raises:
            ComfyUIConnectionError: If ComfyUI is unreachable.
            ComfyUISubmitError: If submission fails.
        """
        payload: dict[str, Any] = {"prompt": workflow}
        if client_id:
            payload["client_id"] = client_id

        try:
            resp = httpx.post(
                f"{self._base_url}/prompt",
                json=payload,
                timeout=30,
            )
        except httpx.RequestError as exc:
            raise ComfyUIConnectionError(
                f"Cannot reach ComfyUI at {self._base_url}: {exc}"
            ) from exc

        if resp.status_code != 200:
            raise ComfyUISubmitError(
                f"Submission failed (HTTP {resp.status_code}): {resp.text}"
            )

        prompt_id = resp.json().get("prompt_id", "")
        logger.info(f"Workflow submitted: prompt_id={prompt_id}")
        return prompt_id

    def wait_for_completion(
        self,
        prompt_id: str,
        client_id: str = "",
        timeout: Optional[int] = None,
    ) -> GenerationResult:
        """Wait for a submitted workflow to complete via WebSocket.

        Args:
            prompt_id: The prompt_id from submit_workflow.
            client_id: Client ID for WebSocket subscription.
            timeout: Max seconds to wait (falls back to config).

        Returns:
            GenerationResult with success status.

        Raises:
            ComfyUITimeoutError: If execution exceeds timeout.
            ComfyUIWebSocketError: If WebSocket communication fails.
        """
        if timeout is None:
            timeout = self._config.websocket_timeout

        start = time.time()
        logger.info(f"Waiting for prompt_id={prompt_id} (timeout={timeout}s)")

        try:
            with websockets.sync.client.connect(
                f"{self._ws_url}?clientId={client_id}",
                additional_headers={"Origin": self._base_url},
                open_timeout=10,
            ) as ws:
                deadline = start + timeout

                while time.time() < deadline:
                    try:
                        msg = ws.recv(timeout=min(2.0, deadline - time.time()))
                        data = json.loads(msg)
                        event = data.get("type", "")

                        if event == "executing":
                            data_payload = data.get("data", {})
                            node = data_payload.get("node")
                            if node is None:
                                # Execution finished
                                duration = time.time() - start
                                logger.info(
                                    f"Execution complete for {prompt_id} "
                                    f"in {duration:.1f}s"
                                )
                                return GenerationResult(
                                    success=True,
                                    prompt_id=prompt_id,
                                    duration_seconds=duration,
                                )

                        if event == "execution_error":
                            duration = time.time() - start
                            logger.error(
                                f"Execution error for {prompt_id}: "
                                f"{data.get('data', {})}"
                            )
                            return GenerationResult(
                                success=False,
                                prompt_id=prompt_id,
                                error=json.dumps(data.get("data", {})),
                                duration_seconds=duration,
                            )
                    except TimeoutError:
                        continue
                    except Exception as exc:
                        logger.warning(f"WebSocket recv error: {exc}")
                        continue

        except websockets.exceptions.ConnectionClosed as exc:
            raise ComfyUIWebSocketError(
                f"WebSocket disconnected: {exc}"
            ) from exc
        except OSError as exc:
            raise ComfyUIWebSocketError(
                f"Cannot connect to WebSocket at {self._ws_url}: {exc}"
            ) from exc

        duration = time.time() - start
        logger.warning(f"Timeout waiting for prompt_id={prompt_id} after {duration:.1f}s")
        raise ComfyUITimeoutError(
            f"Workflow {prompt_id} did not complete within {timeout}s"
        )

    def get_history(self, prompt_id: str) -> dict[str, Any]:
        """Get execution history for a prompt.

        Args:
            prompt_id: The prompt_id to query.

        Returns:
            History data from ComfyUI.

        Raises:
            ComfyUIConnectionError: If ComfyUI is unreachable.
        """
        try:
            resp = httpx.get(
                f"{self._base_url}/history/{prompt_id}",
                timeout=10,
            )
        except httpx.RequestError as exc:
            raise ComfyUIConnectionError(
                f"Cannot reach ComfyUI: {exc}"
            ) from exc

        if resp.status_code != 200:
            return {}
        return resp.json()

    def get_outputs(self, prompt_id: str) -> list[dict[str, str]]:
        """Get output file references for a completed prompt.

        Args:
            prompt_id: The prompt_id to query.

        Returns:
            List of dicts with 'filename', 'subfolder', 'type' keys.

        Raises:
            ComfyUIConnectionError: If ComfyUI is unreachable.
        """
        history = self.get_history(prompt_id)
        prompt_data = history.get(prompt_id, {})
        outputs = prompt_data.get("outputs", {})

        files: list[dict[str, str]] = []
        for node_id, node_output in outputs.items():
            if isinstance(node_output, dict):
                for key in ("images", "gifs", "videos"):
                    items = node_output.get(key, [])
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                files.append({
                                    "filename": item.get("filename", ""),
                                    "subfolder": item.get("subfolder", ""),
                                    "type": item.get("type", "output"),
                                })

        logger.info(f"Found {len(files)} output files for {prompt_id}")
        return files

    def download_output(
        self,
        filename: str,
        subfolder: str = "",
        filetype: str = "output",
        dest_path: str = "",
    ) -> str:
        """Download a generated file from ComfyUI.

        Args:
            filename: The file name from ComfyUI output.
            subfolder: Subfolder within the output directory.
            filetype: Type of output ('output', 'input', 'temp').
            dest_path: Destination file path. If empty, uses filename.

        Returns:
            Absolute path to the downloaded file.

        Raises:
            ComfyUIConnectionError: If ComfyUI is unreachable.
            ArtifactDownloadError: If download fails.
        """
        url = f"{self._base_url}/view"
        params = {"filename": filename, "subfolder": subfolder, "type": filetype}

        try:
            resp = httpx.get(url, params=params, timeout=120)
        except httpx.RequestError as exc:
            raise ComfyUIConnectionError(
                f"Cannot reach ComfyUI: {exc}"
            ) from exc

        if resp.status_code != 200:
            raise ArtifactDownloadError(
                f"Download failed (HTTP {resp.status_code}): {filename}"
            )

        target = dest_path or filename
        with open(target, "wb") as f:
            f.write(resp.content)

        logger.info(f"Downloaded {filename} -> {target} ({len(resp.content)} bytes)")
        return target

    def generate(
        self,
        workflow: dict[str, Any],
        experiment_id: str = "",
        iteration: int = 1,
        storage_base: str = "experiments",
        candidate_number: Optional[int] = None,
    ) -> GenerationResult:
        """Full generation pipeline: submit, wait, download.

        Args:
            workflow: The ComfyUI workflow JSON.
            experiment_id: Experiment identifier for storage.
            iteration: Iteration number.
            storage_base: Base directory for artifacts.
            candidate_number: Optional candidate number within iteration.

        Returns:
            GenerationResult with output file paths.
        """
        import uuid

        client_id = str(uuid.uuid4())
        logger.info(
            f"Starting generation: exp={experiment_id} iter={iteration}"
            + (f" cand={candidate_number}" if candidate_number else "")
        )

        # Submit
        prompt_id = self.submit_workflow(workflow, client_id=client_id)

        # Wait for completion
        result = self.wait_for_completion(prompt_id, client_id=client_id)

        if not result.success:
            logger.error(f"Generation failed: {result.error}")
            return result

        # Determine storage path
        if candidate_number is not None:
            iter_dir = (
                f"{storage_base}/{experiment_id}/"
                f"iteration_{iteration:03d}/"
                f"candidate_{candidate_number:03d}"
            )
        else:
            iter_dir = (
                f"{storage_base}/{experiment_id}/"
                f"iteration_{iteration:03d}"
            )

        # Download outputs
        outputs = self.get_outputs(prompt_id)
        for item in outputs:
            filename = item["filename"]
            subfolder = item.get("subfolder", "")
            filetype = item.get("type", "output")
            dest = f"{iter_dir}/{filename}"

            try:
                import os
                os.makedirs(iter_dir, exist_ok=True)
                self.download_output(
                    filename, subfolder, filetype, dest_path=dest
                )
                result.output_files.append(dest)
            except Exception as exc:
                logger.warning(f"Failed to download {filename}: {exc}")

        # Save workflow JSON for reference
        if experiment_id and iteration:
            try:
                wf_path = f"{iter_dir}/workflow.json"
                import os
                os.makedirs(iter_dir, exist_ok=True)
                with open(wf_path, "w") as f:
                    json.dump(workflow, f, indent=2)
                logger.info(f"Saved workflow JSON: {wf_path}")
            except Exception as exc:
                logger.warning(f"Failed to save workflow JSON: {exc}")

        logger.info(
            f"Generation complete: exp={experiment_id} iter={iteration} "
            f"files={len(result.output_files)}"
        )
        return result