class RagError(Exception):
    """Base for all pipeline errors."""


class STTError(RagError):
    """Speech-to-text provider failure."""


class EmptyTranscriptError(RagError):
    """STT returned an empty string."""


class EmbeddingError(RagError):
    """Query embedding failed."""


class RetrievalError(RagError):
    """Vector search failed or timed out."""


class GenerationError(RagError):
    """LLM generation failed or returned malformed output."""


class GenerationTimeoutError(GenerationError):
    """Generation exceeded the time budget."""


class GuardrailError(RagError):
    """Unexpected guardrail failure (not a refusal — an internal error)."""


class IndexNotLoadedError(RagError):
    """Vector index has not been loaded yet."""


class ProviderRateLimitError(RagError):
    """Provider returned 429."""


class ValidationError(RagError):
    """Pydantic or schema validation failure."""
