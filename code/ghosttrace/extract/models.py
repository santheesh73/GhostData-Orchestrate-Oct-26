from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class TextUnit:
    locator: str
    text: str
    page: int
    bbox: tuple[float, ...] = ()


@dataclass(frozen=True, slots=True)
class Transcript:
    backend: str
    version: str
    pages: int
    units: tuple[TextUnit, ...]
    incomplete_pages: tuple[int, ...] = ()

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ModelReply:
    text: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    cached_input_tokens: int | None = None
    refused: bool = False


class ExtractionError(ValueError):
    """Sanitized extraction failure; never contains raw provider responses."""
