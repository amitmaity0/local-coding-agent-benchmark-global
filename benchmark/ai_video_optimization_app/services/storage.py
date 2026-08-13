"""Storage helper for experiment artifacts.

Manages the directory structure for experiment outputs, iterations,
and metadata files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from loguru import logger


class Storage:
    """File storage manager for experiment artifacts.

    Organizes outputs as:
        experiments/
            experiment_x/
                iteration_001/
                    candidate_001/
                    candidate_002/
                iteration_002/
                metadata.json
                report.json
                output.mp4
    """

    def __init__(self, base_dir: str = "experiments") -> None:
        """Initialize storage with base directory.

        Args:
            base_dir: Root directory for experiment storage.
        """
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage initialized: {self._base_dir}")

    def experiment_dir(self, experiment_id: str) -> Path:
        """Get the directory path for an experiment.

        Args:
            experiment_id: Experiment identifier.

        Returns:
            Path to the experiment directory.
        """
        exp_dir = self._base_dir / experiment_id
        exp_dir.mkdir(parents=True, exist_ok=True)
        return exp_dir

    def iteration_dir(self, experiment_id: str, iteration: int) -> Path:
        """Get the directory path for a specific iteration.

        Args:
            experiment_id: Experiment identifier.
            iteration: Iteration number.

        Returns:
            Path to the iteration directory.
        """
        it_dir = self.experiment_dir(experiment_id) / f"iteration_{iteration:03d}"
        it_dir.mkdir(parents=True, exist_ok=True)
        return it_dir

    def candidate_dir(
        self, experiment_id: str, iteration: int, candidate_number: int
    ) -> Path:
        """Get the directory path for a specific candidate.

        Args:
            experiment_id: Experiment identifier.
            iteration: Iteration number.
            candidate_number: Candidate number within the iteration.

        Returns:
            Path to the candidate directory.
        """
        cand_dir = (
            self.iteration_dir(experiment_id, iteration)
            / f"candidate_{candidate_number:03d}"
        )
        cand_dir.mkdir(parents=True, exist_ok=True)
        return cand_dir

    def save_metadata(
        self, experiment_id: str, metadata: dict[str, Any]
    ) -> str:
        """Save experiment metadata to JSON file.

        Args:
            experiment_id: Experiment identifier.
            metadata: Metadata dictionary.

        Returns:
            Absolute path to the saved file.
        """
        path = self.experiment_dir(experiment_id) / "metadata.json"
        with open(path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)
        logger.info(f"Saved metadata: {path}")
        return str(path)

    def load_metadata(self, experiment_id: str) -> Optional[dict[str, Any]]:
        """Load experiment metadata from JSON file.

        Args:
            experiment_id: Experiment identifier.

        Returns:
            Metadata dictionary or None if not found.
        """
        path = self.experiment_dir(experiment_id) / "metadata.json"
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def save_report(
        self, experiment_id: str, report: dict[str, Any]
    ) -> str:
        """Save analysis report to JSON file.

        Args:
            experiment_id: Experiment identifier.
            report: Report dictionary.

        Returns:
            Absolute path to the saved file.
        """
        path = self.experiment_dir(experiment_id) / "report.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Saved report: {path}")
        return str(path)

    def save_artifact(
        self,
        experiment_id: str,
        iteration: int,
        filename: str,
        content: bytes,
    ) -> str:
        """Save a binary artifact file.

        Args:
            experiment_id: Experiment identifier.
            iteration: Iteration number.
            filename: Artifact filename.
            content: File content bytes.

        Returns:
            Absolute path to the saved file.
        """
        path = self.iteration_dir(experiment_id, iteration) / filename
        with open(path, "wb") as f:
            f.write(content)
        logger.info(f"Saved artifact: {path}")
        return str(path)