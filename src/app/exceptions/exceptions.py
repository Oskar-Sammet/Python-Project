class BaseAppException(Exception):
    """Base for all of our application exceptions"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

        super().__init__(self.message)

class ConflictException(BaseAppException):
    """File conflict exception for our application"""

    def __init__(self, message: str):
        super().__init__(message, status_code=409)

class NotFoundException(BaseAppException):
    """File not found exception for our application"""

    def __init__(self, message: str):
        super().__init__(message, status_code=404)

class TypeNotSupportedException(BaseAppException):
    """File type not supported exception for our application"""
    def __init__(self, message: str):
        super().__init__(message, status_code=502)