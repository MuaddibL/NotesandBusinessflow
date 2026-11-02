"""The one error shape of the system: a machine code plus Turkish text (docs/conventions.md)."""


class DomainError(Exception):
    """A business rule violation. Subclasses set ``code``, ``title`` and ``detail`` (Turkish)."""

    code = "domain_error"
    title = "İşlem kurala aykırı"
    detail = "İstenen işlem bir iş kuralını ihlal ediyor."
