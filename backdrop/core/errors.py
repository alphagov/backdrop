class BackdropError(StandardError):
    pass


class ParseError(BackdropError):
    pass


class ValidationError(BackdropError):
    pass


class InvalidSortError(ValueError):
    pass
