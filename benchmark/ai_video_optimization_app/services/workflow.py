"""Workflow loader for ComfyUI API JSON workflows.

Loads exported ComfyUI workflow JSON files and supports parameter
replacement through class-name-based mapping without hardcoding node IDs.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from orchestrator.exceptions import WorkflowLoadError, WorkflowValidationError


class WorkflowLoader:
    """Utility for loading and modifying ComfyUI workflow JSON.

    Supports loading from files and replacing node parameters
    by node class name or node ID. Parameter mappings can be
    configured through YAML config.
    """

    def __init__(self, workflows_dir: str = "workflows") -> None:
        """Initialize the workflow loader.

        Args:
            workflows_dir: Directory containing workflow JSON files.
        """
        self._workflows_dir = Path(workflows_dir)
        logger.info(f"WorkflowLoader initialized: {self._workflows_dir}")

    # ── Load ──────────────────────────────────────────────────────

    def load(self, name: str) -> dict[str, Any]:
        """Load a workflow by name.

        Args:
            name: Workflow filename (with or without .json extension).

        Returns:
            Parsed workflow JSON as a dictionary.

        Raises:
            WorkflowLoadError: If the workflow file does not exist.
            WorkflowValidationError: If the file is not valid JSON.
        """
        if not name.endswith(".json"):
            name = name + ".json"
        path = self._workflows_dir / name
        if not path.exists():
            raise WorkflowLoadError(f"Workflow not found: {path}")

        try:
            with open(path) as f:
                workflow = json.load(f)
        except json.JSONDecodeError as exc:
            raise WorkflowValidationError(
                f"Invalid JSON in {path}: {exc}"
            ) from exc

        if not isinstance(workflow, dict):
            raise WorkflowValidationError(
                f"Workflow must be a JSON object (got {type(workflow).__name__})"
            )

        logger.info(f"Loaded workflow: {name} ({len(workflow)} nodes)")
        return workflow

    # ── Parameter replacement by class name ───────────────────────

    def replace_parameters(
        self,
        workflow: dict[str, Any],
        replacements: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Replace node parameters by class name.

        Replacements are keyed by class_type. For each matching node,
        the specified input parameters are updated.

        Args:
            workflow: The workflow JSON dictionary.
            replacements: Mapping of class_type -> {input_key: value}.

        Returns:
            Updated workflow dictionary (original unchanged).
        """
        result = copy.deepcopy(workflow)
        for node_id, node_data in result.items():
            class_type = node_data.get("class_type", "")
            if class_type in replacements:
                inputs = node_data.setdefault("inputs", {})
                for param, value in replacements[class_type].items():
                    inputs[param] = value
                    logger.debug(
                        f"Replaced {class_type}.{param} = {value} (node {node_id})"
                    )
        return result

    # ── Parameter replacement by node ID ──────────────────────────

    def replace_by_id(
        self,
        workflow: dict[str, Any],
        node_id: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Replace parameters for a specific node by its ID.

        Args:
            workflow: The workflow JSON dictionary.
            node_id: The node ID to modify.
            parameters: Parameter key-value pairs to update.

        Returns:
            Updated workflow dictionary (original unchanged).
        """
        result = copy.deepcopy(workflow)
        if node_id in result:
            inputs = result[node_id].setdefault("inputs", {})
            inputs.update(parameters)
            logger.debug(f"Updated node {node_id} with {len(parameters)} parameters")
        else:
            logger.warning(f"Node {node_id} not found in workflow")
        return result

    # ── Convenience setters ───────────────────────────────────────

    def set_prompt(
        self,
        workflow: dict[str, Any],
        prompt: str,
        negative_prompt: str = "",
    ) -> dict[str, Any]:
        """Update CLIPTextEncode nodes with new prompt values.

        Targets nodes with class_type 'CLIPTextEncode'. The first match
        gets the positive prompt, the second gets the negative prompt.

        Args:
            workflow: The workflow JSON dictionary.
            prompt: Positive prompt text.
            negative_prompt: Negative prompt text.

        Returns:
            Updated workflow dictionary.
        """
        result = self._replace_by_class(
            workflow, "CLIPTextEncode", {"text": prompt}
        )
        if negative_prompt:
            # Find the second CLIPTextEncode node for negative prompt
            result = self._replace_second_by_class(
                result, "CLIPTextEncode", {"text": negative_prompt}
            )
        logger.info(f"Set prompt (len={len(prompt)}), negative (len={len(negative_prompt)})")
        return result

    def set_seed(
        self,
        workflow: dict[str, Any],
        seed: int,
    ) -> dict[str, Any]:
        """Update seed value in all nodes that have a 'seed' input.

        Targets CommonNoise, KSampler, and any node with a 'seed' input.

        Args:
            workflow: The workflow JSON dictionary.
            seed: Random seed value.

        Returns:
            Updated workflow dictionary.
        """
        result = copy.deepcopy(workflow)
        for node_id, node_data in result.items():
            inputs = node_data.get("inputs", {})
            if "seed" in inputs:
                inputs["seed"] = seed
                logger.debug(f"Set seed={seed} on node {node_id}")
        return result

    def set_cfg(
        self,
        workflow: dict[str, Any],
        cfg: float,
    ) -> dict[str, Any]:
        """Update CFG scale in KSampler nodes.

        Args:
            workflow: The workflow JSON dictionary.
            cfg: CFG scale value.

        Returns:
            Updated workflow dictionary.
        """
        result = self._replace_by_class(workflow, "KSampler", {"cfg": cfg})
        logger.debug(f"Set cfg={cfg}")
        return result

    def set_noise(
        self,
        workflow: dict[str, Any],
        noise: float,
    ) -> dict[str, Any]:
        """Update noise level in noise-related nodes.

        Args:
            workflow: The workflow JSON dictionary.
            noise: Noise level value.

        Returns:
            Updated workflow dictionary.
        """
        result = copy.deepcopy(workflow)
        for node_id, node_data in result.items():
            inputs = node_data.get("inputs", {})
            if "noise" in inputs:
                inputs["noise"] = noise
                logger.debug(f"Set noise={noise} on node {node_id}")
        return result

    def set_steps(
        self,
        workflow: dict[str, Any],
        steps: int,
    ) -> dict[str, Any]:
        """Update inference steps in KSampler nodes.

        Args:
            workflow: The workflow JSON dictionary.
            steps: Number of inference steps.

        Returns:
            Updated workflow dictionary.
        """
        result = self._replace_by_class(workflow, "KSampler", {"steps": steps})
        logger.debug(f"Set steps={steps}")
        return result

    # ── Batch apply from config ───────────────────────────────────

    def apply_config(
        self,
        workflow: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply a batch of parameter changes from a config dict.

        Expected config keys:
            prompt, negative_prompt, seed, cfg, noise, steps,
            replacements (class_type -> {key: value})

        Args:
            workflow: The workflow JSON dictionary.
            config: Configuration dictionary.

        Returns:
            Updated workflow dictionary.
        """
        result = workflow

        if "prompt" in config or "negative_prompt" in config:
            result = self.set_prompt(
                result,
                prompt=config.get("prompt", ""),
                negative_prompt=config.get("negative_prompt", ""),
            )
        if "seed" in config:
            result = self.set_seed(result, config["seed"])
        if "cfg" in config:
            result = self.set_cfg(result, config["cfg"])
        if "noise" in config:
            result = self.set_noise(result, config["noise"])
        if "steps" in config:
            result = self.set_steps(result, config["steps"])
        if "replacements" in config:
            result = self.replace_parameters(result, config["replacements"])

        logger.info(f"Applied config with {len(config)} keys to workflow")
        return result

    # ── Internal helpers ──────────────────────────────────────────

    @staticmethod
    def _replace_by_class(
        workflow: dict[str, Any],
        class_type: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Replace params on the first node matching class_type."""
        result = copy.deepcopy(workflow)
        for node_id, node_data in result.items():
            if node_data.get("class_type") == class_type:
                inputs = node_data.setdefault("inputs", {})
                inputs.update(params)
                return result
        logger.warning(f"No node with class_type '{class_type}' found")
        return result

    @staticmethod
    def _replace_second_by_class(
        workflow: dict[str, Any],
        class_type: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Replace params on the second node matching class_type."""
        result = copy.deepcopy(workflow)
        found = False
        for node_id, node_data in result.items():
            if node_data.get("class_type") == class_type:
                if found:
                    inputs = node_data.setdefault("inputs", {})
                    inputs.update(params)
                    return result
                found = True
        logger.warning(f"Second node with class_type '{class_type}' not found")
        return result