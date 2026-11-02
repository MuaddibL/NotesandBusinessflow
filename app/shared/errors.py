"""The one error shape of the system: a machine code plus Turkish text (docs/conventions.md)."""


class AppError(Exception):
    """Base for errors the user may be shown: machine-readable ``code``, Turkish text."""

    code = "app_error"
    title = "İşlem tamamlanamadı"
    detail = "İstenen işlem tamamlanamadı."


class DomainError(AppError):
    """A business rule violation. Subclasses set ``code``, ``title`` and ``detail`` (Turkish)."""

    code = "domain_error"
    title = "İşlem kurala aykırı"
    detail = "İstenen işlem bir iş kuralını ihlal ediyor."


class StorageError(AppError):
    """The data file cannot be opened or migrated — infrastructure, not a business rule.

    Kept outside the ``DomainError`` family on purpose: ``docs/conventions.md`` requires business
    rule errors to subclass ``DomainError``, and a corrupt file or a missing write permission is
    neither. The user-facing text never carries the path or the underlying message.
    """

    code = "storage_unavailable"
    title = "Veri dosyası açılamadı"
    detail = "Uygulama verisi açılamadı. Dosya bozuk olabilir veya yazma izni olmayabilir."
