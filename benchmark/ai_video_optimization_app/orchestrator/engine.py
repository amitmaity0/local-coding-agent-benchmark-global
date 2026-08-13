"""Orchestration engine for experiment lifecycle management.

The Engine class owns the optimization lifecycle and coordinates
between services, state management, and persistence.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger

from orchestrator.config import AppConfig
from orchestrator.database import get_session, init_db
from orchestrator.evaluator import StoppingReason
from orchestrator.models import (
    Candidate,
    CandidateORM,
    Experiment,
    ExperimentCreate,
    ExperimentORM,
    Iteration,
    IterationORM,
    Job,
    OptimizationResult,
    QAReport,
)
from orchestrator.ranking import rank_candidates, select_best_candidate
from orchestrator.state import ExperimentState, transition


class Engine:
    """Orchestration engine managing experiment lifecycle.

    Coordinates ComfyUI generation, LM Studio optimization, and QA analysis
    through a state-machine-driven workflow.
    """

    def __init__(self, config: AppConfig) -> None:
        """Initialize the engine with application configuration.

        Args:
            config: Application configuration.
        """
        self._config = config
        init_db(config.database)
        logger.info("Engine initialized")

    def create_experiment(self, data: ExperimentCreate) -> Experiment:
        """Create a new experiment.

        Args:
            data: Experiment creation parameters.

        Returns:
            The created Experiment with assigned ID.
        """
        exp_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        exp_orm = ExperimentORM(
            id=exp_id,
            prompt=data.prompt,
            negative_prompt=data.negative_prompt,
            workflow_template=data.workflow_template,
            target_score=data.target_score,
            max_iterations=data.max_iterations,
            seed=data.seed,
            cfg=data.cfg,
            noise=data.noise,
            status=ExperimentState.NEW.value,
            created_at=now,
            updated_at=now,
        )

        with get_session() as session:
            session.add(exp_orm)
            session.flush()

        logger.info(f"Experiment created: {exp_id}")
        return self._orm_to_model(exp_orm)

    def start_experiment(self, experiment_id: str) -> Experiment:
        """Start an experiment by transitioning it to QUEUED.

        Args:
            experiment_id: ID of the experiment to start.

        Returns:
            Updated Experiment.

        Raises:
            ValueError: If experiment not found or transition invalid.
        """
        with get_session() as session:
            exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
            if not exp:
                raise ValueError(f"Experiment not found: {experiment_id}")
            current = ExperimentState(exp.status)
            exp.status = transition(current, ExperimentState.QUEUED).value
            exp.updated_at = datetime.now(timezone.utc)
            session.flush()

        logger.info(f"Experiment started: {experiment_id}")
        return self._orm_to_model(exp)

    def pause_experiment(self, experiment_id: str) -> Experiment:
        """Pause a running experiment.

        Note: Pause transitions to QUEUED if currently GENERATING/ANALYZING/OPTIMIZING.

        Args:
            experiment_id: ID of the experiment to pause.

        Returns:
            Updated Experiment.
        """
        with get_session() as session:
            exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
            if not exp:
                raise ValueError(f"Experiment not found: {experiment_id}")
            logger.info(f"Experiment paused: {experiment_id}")
            exp.updated_at = datetime.now(timezone.utc)
            session.flush()
        return self._orm_to_model(exp)

    def cancel_experiment(self, experiment_id: str) -> Experiment:
        """Cancel an experiment.

        Sets the experiment status to CANCELLED. The run_loop will detect
        this flag and stop creating new iterations after finishing the
        current API call.

        Args:
            experiment_id: ID of the experiment to cancel.

        Returns:
            Updated Experiment.

        Raises:
            ValueError: If experiment not found or already terminal.
        """
        with get_session() as session:
            exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
            if not exp:
                raise ValueError(f"Experiment not found: {experiment_id}")
            current = ExperimentState(exp.status)
            exp.status = transition(current, ExperimentState.CANCELLED).value
            if not exp.stopping_reason:
                exp.stopping_reason = StoppingReason.USER_CANCELLED.value
            exp.updated_at = datetime.now(timezone.utc)
            session.flush()

        logger.info(f"Experiment cancelled: {experiment_id}")
        return self._orm_to_model(exp)

    def get_status(self, experiment_id: str) -> Experiment:
        """Get current experiment status.

        Args:
            experiment_id: ID of the experiment.

        Returns:
            Current Experiment state.

        Raises:
            ValueError: If experiment not found.
        """
        with get_session() as session:
            exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
            if not exp:
                raise ValueError(f"Experiment not found: {experiment_id}")
            return self._orm_to_model(exp)

    def list_experiments(self) -> list[Experiment]:
        """List all experiments ordered by creation time (newest first).

        Returns:
            List of all Experiments.
        """
        with get_session() as session:
            rows = (
                session.query(ExperimentORM)
                .order_by(ExperimentORM.created_at.desc())
                .all()
            )
            return [self._orm_to_model(r) for r in rows]

    def get_iterations(self, experiment_id: str) -> list[Iteration]:
        """Get all iterations for an experiment.

        Args:
            experiment_id: ID of the experiment.

        Returns:
            List of Iteration objects.
        """
        with get_session() as session:
            rows = (
                session.query(IterationORM)
                .filter_by(experiment_id=experiment_id)
                .order_by(IterationORM.number.asc())
                .all()
            )
            return [self._orm_to_iteration(r) for r in rows]

    def get_candidates(
        self, experiment_id: str, iteration: int
    ) -> list[Candidate]:
        """Get all candidates for a specific iteration.

        Args:
            experiment_id: ID of the experiment.
            iteration: Iteration number.

        Returns:
            List of Candidate objects.
        """
        import json

        with get_session() as session:
            it = (
                session.query(IterationORM)
                .filter_by(experiment_id=experiment_id, number=iteration)
                .first()
            )
            if not it:
                return []

            rows = (
                session.query(CandidateORM)
                .filter_by(iteration_id=it.id)
                .order_by(CandidateORM.number.asc())
                .all()
            )

        candidates = []
        for r in rows:
            qa_report = None
            if r.qa_report:
                try:
                    qa_report = json.loads(r.qa_report)
                except (json.JSONDecodeError, TypeError):
                    pass

            candidates.append(
                Candidate(
                    candidate_id=r.id,
                    iteration=iteration,
                    seed=r.seed,
                    workflow=r.workflow or "",
                    output_video=r.output_video,
                    qa_report=qa_report,
                    optimization_score=r.optimization_score,
                    artifact_directory=r.artifact_directory,
                    generation_time=r.generation_time,
                    status=r.status,
                    is_best_in_iteration=bool(r.is_best_in_iteration),
                    is_best_in_experiment=bool(r.is_best_in_experiment),
                    created_at=r.created_at,
                )
            )
        return candidates

    def get_progress(self, experiment_id: str) -> dict:
        """Get detailed progress information for an experiment.

        Returns progress data suitable for the dashboard including
        score history, best result tracking, and estimated remaining iterations.

        Args:
            experiment_id: ID of the experiment.

        Returns:
            Dict with progress details.
        """
        with get_session() as session:
            exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
            if not exp:
                raise ValueError(f"Experiment not found: {experiment_id}")

            iterations = (
                session.query(IterationORM)
                .filter_by(experiment_id=experiment_id)
                .order_by(IterationORM.number.asc())
                .all()
            )

        score_history = []
        for it in iterations:
            if it.score is not None:
                score_history.append(
                    {"iteration": it.number, "score": it.score}
                )

        # Estimate remaining iterations based on average improvement
        remaining = 0
        if score_history and exp.status not in (
            ExperimentState.COMPLETED.value,
            ExperimentState.FAILED.value,
            ExperimentState.CANCELLED.value,
        ):
            avg_improvement = 0.0
            if len(score_history) >= 2:
                improvements = [
                    score_history[i]["score"] - score_history[i - 1]["score"]
                    for i in range(1, len(score_history))
                ]
                avg_improvement = sum(improvements) / len(improvements)

            if avg_improvement > 0:
                gap = exp.target_score - (exp.score or 0)
                remaining = max(0, int(gap / avg_improvement) + 1)
            remaining = min(remaining, exp.max_iterations - exp.current_iteration)

        return {
            "experiment_id": exp.id,
            "status": exp.status,
            "current_iteration": exp.current_iteration,
            "max_iterations": exp.max_iterations,
            "score": exp.score,
            "best_score": exp.best_score,
            "best_iteration": exp.best_iteration,
            "target_score": exp.target_score,
            "stopping_reason": exp.stopping_reason,
            "optimizer_confidence": exp.optimizer_confidence,
            "score_history": score_history,
            "estimated_remaining": remaining,
            "total_iterations": len(iterations),
            "updated_at": exp.updated_at.isoformat() if exp.updated_at else None,
        }

    def generate(
        self,
        experiment_id: str,
        iteration: int = 1,
        candidate_number: Optional[int] = None,
    ) -> dict[str, str]:
        """Run a single generation iteration for an experiment.

        Loads the workflow template, injects experiment parameters,
        submits to ComfyUI, waits for completion, and downloads artifacts.

        Args:
            experiment_id: ID of the experiment.
            iteration: Iteration number.
            candidate_number: Optional candidate number within iteration.

        Returns:
            Dict with 'output_files' list and 'prompt_id'.

        Raises:
            ValueError: If experiment not found.
        """
        from services.comfyui import ComfyUIService
        from services.workflow import WorkflowLoader

        # Load experiment
        with get_session() as session:
            exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
            if not exp:
                raise ValueError(f"Experiment not found: {experiment_id}")

        logger.info(
            f"Generating: exp={experiment_id} iter={iteration}"
            + (f" cand={candidate_number}" if candidate_number else "")
            + f" prompt={exp.prompt[:50]}..."
        )

        # Build workflow
        loader = WorkflowLoader(self._config.workflows_dir)
        if exp.workflow_template:
            workflow = loader.load(exp.workflow_template)
        else:
            workflow = {}

        # Inject parameters
        workflow = loader.set_prompt(
            workflow,
            prompt=exp.prompt,
            negative_prompt=exp.negative_prompt,
        )
        if exp.seed is not None:
            workflow = loader.set_seed(workflow, exp.seed)
        workflow = loader.set_cfg(workflow, exp.cfg)
        workflow = loader.set_noise(workflow, exp.noise)

        # Submit and wait
        comfy = ComfyUIService(self._config.comfyui)
        result = comfy.generate(
            workflow=workflow,
            experiment_id=experiment_id,
            iteration=iteration,
            storage_base=self._config.experiments_dir,
            candidate_number=candidate_number,
        )

        # Record iteration in DB
        output_path = result.output_files[0] if result.output_files else None
        with get_session() as session:
            # Ensure iteration record exists
            it_orm = (
                session.query(IterationORM)
                .filter_by(experiment_id=experiment_id, number=iteration)
                .first()
            )
            if not it_orm:
                it_orm = IterationORM(
                    experiment_id=experiment_id,
                    number=iteration,
                    status="completed" if result.success else "failed",
                    output_path=output_path,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(it_orm)
            else:
                it_orm.status = "completed" if result.success else "failed"

            # Update experiment
            exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
            if exp:
                exp.current_iteration = iteration
                exp.updated_at = datetime.now(timezone.utc)
            session.flush()

        logger.info(
            f"Generation done: exp={experiment_id} iter={iteration}"
            + (f" cand={candidate_number}" if candidate_number else "")
            + f" success={result.success} files={len(result.output_files)}"
        )
        return {
            "output_files": result.output_files,
            "prompt_id": result.prompt_id,
            "success": result.success,
            "duration": result.duration_seconds,
        }

    def generate_candidate(
        self,
        experiment_id: str,
        iteration: int,
        candidate_number: int,
        seed: int,
    ) -> Candidate:
        """Generate a single candidate with a unique seed.

        Args:
            experiment_id: Experiment ID.
            iteration: Iteration number.
            candidate_number: Candidate number within iteration.
            seed: Unique seed for this candidate.

        Returns:
            Candidate object with generation results.

        Raises:
            ValueError: If experiment not found.
        """
        import time

        from services.storage import Storage

        cand_id = str(uuid.uuid4())
        start_time = time.time()

        logger.info(
            f"Candidate started: exp={experiment_id} iter={iteration} "
            f"cand={candidate_number} seed={seed}"
        )

        # Temporarily override seed for this candidate
        with get_session() as session:
            exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
            if not exp:
                raise ValueError(f"Experiment not found: {experiment_id}")
            original_seed = exp.seed
            exp.seed = seed
            session.flush()

        # Create candidate record
        with get_session() as session:
            # Ensure iteration exists
            it_orm = (
                session.query(IterationORM)
                .filter_by(experiment_id=experiment_id, number=iteration)
                .first()
            )
            if not it_orm:
                it_orm = IterationORM(
                    experiment_id=experiment_id,
                    number=iteration,
                    status="generating",
                    created_at=datetime.now(timezone.utc),
                )
                session.add(it_orm)
                session.flush()

            cand_orm = CandidateORM(
                id=cand_id,
                iteration_id=it_orm.id,
                number=candidate_number,
                seed=seed,
                status="generating",
                created_at=datetime.now(timezone.utc),
            )
            session.add(cand_orm)
            session.flush()

        # Generate with candidate-specific seed
        status = "completed"
        output_video = None
        artifact_dir = None
        workflow_json = ""
        try:
            gen_result = self.generate(
                experiment_id, iteration, candidate_number=candidate_number
            )
            output_video = (
                gen_result["output_files"][0]
                if gen_result.get("output_files")
                else None
            )
            # Get artifact directory
            storage = Storage(self._config.experiments_dir)
            artifact_dir = str(
                storage.candidate_dir(experiment_id, iteration, candidate_number)
            )
            # Load workflow JSON if saved
            wf_path = (
                Path(artifact_dir) / "workflow.json"
                if artifact_dir
                else None
            )
            if wf_path and wf_path.exists():
                workflow_json = wf_path.read_text()
        except Exception as exc:
            logger.error(
                f"Candidate failed: exp={experiment_id} iter={iteration} "
                f"cand={candidate_number} error={exc}"
            )
            status = "failed"
        finally:
            # Restore original seed
            with get_session() as session:
                exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
                if exp and original_seed is not None:
                    exp.seed = original_seed
                    session.flush()

        generation_time = time.time() - start_time

        # Update candidate record
        with get_session() as session:
            cand = session.query(CandidateORM).filter_by(id=cand_id).first()
            if cand:
                cand.status = status
                cand.output_video = output_video
                cand.artifact_directory = artifact_dir
                cand.workflow = workflow_json
                cand.generation_time = generation_time
                session.flush()

        logger.info(
            f"Candidate completed: exp={experiment_id} iter={iteration} "
            f"cand={candidate_number} status={status} "
            f"time={generation_time:.1f}s"
        )

        return Candidate(
            candidate_id=cand_id,
            iteration=iteration,
            seed=seed,
            workflow=workflow_json,
            output_video=output_video,
            artifact_directory=artifact_dir,
            generation_time=generation_time,
            status=status,
        )

    def analyze(
        self,
        experiment_id: str,
        iteration: int = 1,
        candidate_number: Optional[int] = None,
    ) -> QAReport:
        """Analyze the generated video for an experiment iteration.

        Submits the video artifact to LM Studio for quality evaluation,
        validates the report, and persists it to the experiment directory.

        New flow:
            generate() -> analyze() -> save QA report -> return report

        Args:
            experiment_id: ID of the experiment.
            iteration: Iteration number.
            candidate_number: Optional candidate number within iteration.

        Returns:
            Validated QAReport.

        Raises:
            ValueError: If experiment or iteration not found.
            VideoAnalysisError: If analysis fails.
        """
        from services.video_analyzer import VideoAnalyzer

        # Load experiment
        with get_session() as session:
            exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
            if not exp:
                raise ValueError(f"Experiment not found: {experiment_id}")

            # Find the iteration's output path
            it = (
                session.query(IterationORM)
                .filter_by(experiment_id=experiment_id, number=iteration)
                .first()
            )
            if not it:
                raise ValueError(
                    f"Iteration {iteration} not found for experiment {experiment_id}"
                )
            if not it.output_path:
                raise ValueError(
                    f"Iteration {iteration} has no output video for experiment {experiment_id}"
                )

        video_path = it.output_path
        logger.info(
            f"Analyzing: exp={experiment_id} iter={iteration}"
            + (f" cand={candidate_number}" if candidate_number else "")
            + f" video={video_path}"
        )

        # Run analysis
        analyzer = VideoAnalyzer(self._config.lmstudio)
        report = analyzer.analyze(video_path)

        # Save report
        report_dir = analyzer.save_report(
            report=report,
            experiment_id=experiment_id,
            iteration=iteration,
            experiments_dir=self._config.experiments_dir,
            candidate_number=candidate_number,
        )

        # Update iteration with report path
        with get_session() as session:
            it = (
                session.query(IterationORM)
                .filter_by(experiment_id=experiment_id, number=iteration)
                .first()
            )
            if it:
                it.report_path = str(report_dir / "qa_report.json")
                it.score = report.overall_score
                session.flush()

        logger.info(
            f"Analysis done: exp={experiment_id} iter={iteration}"
            + (f" cand={candidate_number}" if candidate_number else "")
            + f" score={report.overall_score:.3f} issues={len(report.issues)}"
        )
        return report

    def analyze_candidate(
        self,
        experiment_id: str,
        candidate: Candidate,
    ) -> QAReport:
        """Analyze a single candidate's video.

        Args:
            experiment_id: Experiment ID.
            candidate: Candidate to analyze.

        Returns:
            Validated QAReport.
        """
        logger.info(
            f"Analyzing candidate: exp={experiment_id} iter={candidate.iteration} "
            f"cand={candidate.candidate_id[:8]}"
        )

        # Find candidate's output video
        with get_session() as session:
            cand_orm = session.query(CandidateORM).filter_by(
                id=candidate.candidate_id
            ).first()
            if not cand_orm or not cand_orm.output_video:
                raise ValueError(
                    f"Candidate {candidate.candidate_id[:8]} has no output video"
                )
            video_path = cand_orm.output_video

        # Run analysis
        from services.video_analyzer import VideoAnalyzer

        analyzer = VideoAnalyzer(self._config.lmstudio)
        report = analyzer.analyze(video_path)

        # Save report to candidate directory
        report_dir = analyzer.save_report(
            report=report,
            experiment_id=experiment_id,
            iteration=candidate.iteration,
            experiments_dir=self._config.experiments_dir,
            candidate_number=candidate.iteration,
        )

        # Update candidate with QA report
        import json

        with get_session() as session:
            cand = session.query(CandidateORM).filter_by(
                id=candidate.candidate_id
            ).first()
            if cand:
                cand.qa_report = json.dumps(report.model_dump(mode="json"))
                cand.optimization_score = report.overall_score
                cand.status = "analyzed"
                session.flush()

        # Update in-memory candidate
        candidate.qa_report = report.model_dump(mode="json")
        candidate.optimization_score = report.overall_score

        logger.info(
            f"Candidate analyzed: iter={candidate.iteration} "
            f"cand={candidate.candidate_id[:8]} "
            f"score={report.overall_score:.3f}"
        )
        return report

    def optimize(
        self,
        experiment_id: str,
        iteration: int = 1,
    ) -> OptimizationResult:
        """Optimize prompt and parameters based on QA analysis.

        Submits the current generation parameters and QA report to LM Studio
        for optimization. Stores the OptimizationResult without triggering
        another generation.

        New flow:
            generate() -> analyze() -> optimize() -> save result -> stop

        Args:
            experiment_id: ID of the experiment.
            iteration: Iteration number.

        Returns:
            Validated OptimizationResult.

        Raises:
            ValueError: If experiment or iteration not found.
            OptimizationError: If optimization fails.
        """
        from services.optimizer import Optimizer

        from orchestrator.optimization_strategy import (
            build_optimization_context,
            CandidateHistory,
            determine_strategy,
            OptimizationConfig,
        )

        # Load experiment
        with get_session() as session:
            exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
            if not exp:
                raise ValueError(f"Experiment not found: {experiment_id}")

            # Find the iteration
            it = (
                session.query(IterationORM)
                .filter_by(experiment_id=experiment_id, number=iteration)
                .first()
            )
            if not it:
                raise ValueError(
                    f"Iteration {iteration} not found for experiment {experiment_id}"
                )

        # Load QA report
        if not it.report_path:
            raise ValueError(
                f"Iteration {iteration} has no QA report for experiment {experiment_id}"
            )

        import json

        with open(it.report_path) as f:
            qa_data = json.load(f)

        qa_report = QAReport(**qa_data)
        qa_report_dict = qa_report.model_dump()

        # Build candidate history from iteration records
        with get_session() as session:
            all_iterations = (
                session.query(IterationORM)
                .filter_by(experiment_id=experiment_id)
                .order_by(IterationORM.number.asc())
                .all()
            )

        score_history: list[float] = []
        prev_score: Optional[float] = None
        for it_orm in all_iterations:
            if it_orm.score is not None:
                score_history.append(it_orm.score)
                prev_score = it_orm.score

        current_score = it.score if it.score is not None else 0.0
        best_score = exp.best_score if exp.best_score is not None else 0.0

        history = CandidateHistory(
            best_score=best_score,
            current_score=current_score,
            previous_score=prev_score,
            score_history=score_history,
            iteration_number=iteration,
        )

        # Determine optimization strategy
        opt_config = OptimizationConfig(
            improvement_threshold=self._config.optimization.improvement_threshold,
            plateau_iterations=self._config.optimization.plateau_iterations,
            targeted_score_threshold=self._config.optimization.targeted_score_threshold,
            recovery_regression_threshold=self._config.optimization.recovery_regression_threshold,
            exploration_probability=self._config.optimization.exploration_probability,
        )

        strategy = determine_strategy(qa_report_dict, history, opt_config)

        # Build optimization context
        context = build_optimization_context(
            strategy=strategy,
            qa_report=qa_report_dict,
            current_candidate={
                "seed": exp.seed,
                "cfg": exp.cfg,
                "noise": exp.noise,
            },
            best_candidate={
                "seed": exp.best_parameters.get("seed"),
                "cfg": exp.best_parameters.get("cfg"),
                "noise": exp.best_parameters.get("noise"),
                "prompt": exp.best_prompt,
            } if exp.best_prompt else None,
            iteration_number=iteration,
        )

        # Build job object for optimizer context
        job = Job(
            id=it.id,
            experiment_id=experiment_id,
            iteration=iteration,
            status="optimizing",
            created_at=it.created_at,
        )

        logger.info(
            f"Optimizing: exp={experiment_id} iter={iteration} "
            f"score={qa_report.overall_score:.3f} "
            f"mode={strategy.mode.value}"
        )

        # Log strategy decision
        logger.info(
            f"Optimization strategy: mode={strategy.mode.value} "
            f"focus={strategy.focus_areas} "
            f"modified={strategy.parameters_modified} "
            f"preserved={strategy.parameters_preserved} "
            f"reasoning={strategy.reasoning}"
        )

        # Run optimization
        optimizer = Optimizer(self._config.lmstudio)
        result = optimizer.optimize(job, qa_report, context)

        # Save optimization result
        optimizer.save_optimization(
            result=result,
            experiment_id=experiment_id,
            iteration=iteration,
            experiments_dir=self._config.experiments_dir,
        )

        logger.info(
            f"Optimization done: exp={experiment_id} iter={iteration} "
            f"confidence={result.confidence:.2f} "
            f"mode={result.optimization_mode} "
            f"improvements={len(result.expected_improvements)}"
        )
        return result

    # ── Autonomous Optimization Loop ──────────────────────────


    # ── Internal helpers ──────────────────────────────────────

    @staticmethod
    def _orm_to_model(orm: ExperimentORM) -> Experiment:
        """Convert ORM model to Pydantic Experiment."""
        import json

        best_params = {}
        if orm.best_parameters:
            try:
                best_params = json.loads(orm.best_parameters)
            except (json.JSONDecodeError, TypeError):
                best_params = {}

        return Experiment(
            id=orm.id,
            prompt=orm.prompt,
            negative_prompt=orm.negative_prompt,
            workflow_template=orm.workflow_template,
            target_score=orm.target_score,
            max_iterations=orm.max_iterations,
            seed=orm.seed,
            cfg=orm.cfg,
            noise=orm.noise,
            status=ExperimentState(orm.status),
            current_iteration=orm.current_iteration,
            score=orm.score,
            best_score=orm.best_score,
            best_iteration=orm.best_iteration,
            best_prompt=orm.best_prompt or "",
            best_parameters=best_params,
            stopping_reason=orm.stopping_reason,
            optimizer_confidence=orm.optimizer_confidence,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    @staticmethod
    def _orm_to_iteration(orm: IterationORM) -> Iteration:
        """Convert ORM model to Pydantic Iteration."""
        return Iteration(
            id=orm.id,
            experiment_id=orm.experiment_id,
            number=orm.number,
            score=orm.score,
            artifact_path=orm.artifact_path,
            report_path=orm.report_path,
            output_path=orm.output_path,
            status=orm.status,
            created_at=orm.created_at,
        )

    def _set_status(
        self, experiment_id: str, state: ExperimentState
    ) -> None:
        """Update experiment status with state transition validation.

        Args:
            experiment_id: Experiment ID.
            state: New state to transition to.
        """
        with get_session() as session:
            exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
            if not exp:
                return
            current = ExperimentState(exp.status)
            try:
                exp.status = transition(current, state).value
            except ValueError:
                # If transition is invalid, set directly (for resume/recovery)
                logger.warning(
                    f"Direct status set {current.value} -> {state.value} "
                    f"for {experiment_id}"
                )
                exp.status = state.value
            exp.updated_at = datetime.now(timezone.utc)
            session.flush()

    def _update_experiment(
        self,
        experiment_id: str,
        *,
        current_iteration: Optional[int] = None,
        score: Optional[float] = None,
        best_score: Optional[float] = None,
        best_iteration: Optional[int] = None,
        best_prompt: Optional[str] = None,
        best_parameters: Optional[dict] = None,
        optimizer_confidence: Optional[float] = None,
        stopping_reason: Optional[str] = None,
        failure_detail: Optional[str] = None,
    ) -> None:
        """Update experiment progress fields in the database.

        Args:
            experiment_id: Experiment ID.
            current_iteration: Current iteration number.
            score: Latest QA score.
            best_score: Best score seen so far.
            best_iteration: Iteration with best score.
            best_prompt: Prompt that produced best score.
            best_parameters: Parameters that produced best score.
            optimizer_confidence: Latest optimizer confidence.
            stopping_reason: Reason the loop stopped.
            failure_detail: Details of a failure.
        """
        import json

        with get_session() as session:
            exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
            if not exp:
                return
            if current_iteration is not None:
                exp.current_iteration = current_iteration
            if score is not None:
                exp.score = score
            if best_score is not None:
                exp.best_score = best_score
            if best_iteration is not None:
                exp.best_iteration = best_iteration
            if best_prompt is not None:
                exp.best_prompt = best_prompt
            if best_parameters is not None:
                exp.best_parameters = json.dumps(best_parameters)
            if optimizer_confidence is not None:
                exp.optimizer_confidence = optimizer_confidence
            if stopping_reason is not None:
                exp.stopping_reason = stopping_reason
            if failure_detail is not None:
                # Append to stopping reason if not already set
                if exp.stopping_reason:
                    exp.stopping_reason = (
                        f"{exp.stopping_reason}: {failure_detail}"
                    )
                else:
                    exp.stopping_reason = failure_detail
            exp.updated_at = datetime.now(timezone.utc)
            session.flush()

    def _update_experiment_params(
        self,
        experiment_id: str,
        *,
        prompt: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        cfg: Optional[float] = None,
        noise: Optional[float] = None,
        seed: Optional[int] = None,
    ) -> None:
        """Update experiment generation parameters for the next iteration.

        Args:
            experiment_id: Experiment ID.
            prompt: New prompt.
            negative_prompt: New negative prompt.
            cfg: New CFG scale.
            noise: New noise level.
            seed: New seed.
        """
        with get_session() as session:
            exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
            if not exp:
                return
            if prompt is not None:
                exp.prompt = prompt
            if negative_prompt is not None:
                exp.negative_prompt = negative_prompt
            if cfg is not None:
                exp.cfg = cfg
            if noise is not None:
                exp.noise = noise
            if seed is not None:
                exp.seed = seed
            exp.updated_at = datetime.now(timezone.utc)
            session.flush()

    def _save_iteration_metadata(
        self,
        *,
        experiment_id: str,
        iteration: int,
        prompt: str,
        cfg: float,
        noise: float,
        seed: Optional[int],
        score: float,
        confidence: float,
        improvement: float,
    ) -> None:
        """Save metadata.json for an iteration directory.

        Args:
            experiment_id: Experiment ID.
            iteration: Iteration number.
            prompt: Prompt used.
            cfg: CFG scale used.
            noise: Noise level used.
            seed: Seed used.
            score: QA score.
            confidence: Optimizer confidence.
            improvement: Score improvement from best.
        """
        import json

        from pathlib import Path

        iter_dir = (
            Path(self._config.experiments_dir)
            / experiment_id
            / f"iteration_{iteration:03d}"
        )
        iter_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "experiment_id": experiment_id,
            "iteration": iteration,
            "prompt": prompt,
            "parameters": {
                "cfg": cfg,
                "noise": noise,
                "seed": seed,
            },
            "score": score,
            "optimizer_confidence": confidence,
            "improvement": round(improvement, 6),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        meta_path = iter_dir / "metadata.json"
        meta_path.write_text(json.dumps(metadata, indent=2))