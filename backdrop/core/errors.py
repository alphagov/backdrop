class BackdropError(StandardError):
    pass


class ParseError(BackdropError):
    pass


class ValidationError(BackdropError):
    pass


class DataSetCreationError(BackdropError):
    pass


class InvalidSortError(ValueError):
    pass


class InvalidOperationError(ValueError):
    """Raised if an invalid collect function is provided, or if an error
    is raised from a collect function"""
    pass
