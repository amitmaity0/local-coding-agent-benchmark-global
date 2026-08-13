"""Custom exceptions for MotionForge."""


class MotionForgeError(Exception):
    """Base exception for all MotionForge errors."""


class ComfyUIError(MotionForgeError):
    """Base exception for ComfyUI-related errors."""


class ComfyUIConnectionError(ComfyUIError):
    """Raised when ComfyUI is unreachable."""


class ComfyUISubmitError(ComfyUIError):
    """Raised when workflow submission fails."""


class ComfyUIExecutionError(ComfyUIError):
    """Raised when a workflow execution fails."""


class ComfyUITimeoutError(ComfyUIError):
    """Raised when a workflow execution times out."""


class ComfyUIWebSocketError(ComfyUIError):
    """Raised when WebSocket communication fails."""


class WorkflowError(MotionForgeError):
    """Base exception for workflow-related errors."""


class WorkflowLoadError(WorkflowError):
    """Raised when a workflow file cannot be loaded."""


class WorkflowValidationError(WorkflowError):
    """Raised when a workflow JSON is invalid."""


class StorageError(MotionForgeError):
    """Raised when artifact storage operations fail."""


class ArtifactDownloadError(StorageError):
    """Raised when artifact download fails."""


# ── Video Analysis Errors ───────────────────────────────────────


class VideoAnalysisError(MotionForgeError):
    """Base exception for video analysis errors."""


class VideoNotFoundError(VideoAnalysisError):
    """Raised when the video file is missing."""


class LMStudioConnectionError(VideoAnalysisError):
    """Raised when LM Studio is unreachable."""


class LMStudioTimeoutError(VideoAnalysisError):
    """Raised when LM Studio request times out."""


class LMStudioResponseError(VideoAnalysisError):
    """Raised when LM Studio returns an unexpected response."""


class ReportValidationError(VideoAnalysisError):
    """Raised when a QA report fails validation."""


# ── Optimization Errors ─────────────────────────────────────────────


class OptimizationError(MotionForgeError):
    """Base exception for optimization errors."""


class OptimizationConnectionError(OptimizationError):
    """Raised when LM Studio is unreachable during optimization."""


class OptimizationTimeoutError(OptimizationError):
    """Raised when the optimization request times out."""


class OptimizationResponseError(OptimizationError):
    """Raised when LM Studio returns an unexpected response for optimization."""


class OptimizationValidationError(OptimizationError):
    """Raised when the optimization response fails schema validation."""


class MissingQAResportError(OptimizationError):
    """Raised when the QA report required for optimization is missing."""