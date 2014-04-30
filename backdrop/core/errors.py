class BackdropError(StandardError):
    pass


class ParseError(BackdropError):
    pass


class ValidationError(BackdropError):
    pass


class PutNonEmptyNotImplementedError(BackdropError):
    pass
