class AppError(Exception):
    pass


class FetchError(AppError):
    pass


class ParseError(AppError):
    pass


class StorageError(AppError):
    pass