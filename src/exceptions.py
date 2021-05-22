"""Exceptions hierarchy

RatStalkerError
|
'---CommandError
|
'---MessageError
|
'---MatrixError
"""



class RatStalkerError(Exception):
    """Base exception class for the bot"""
    def __init__(self, message="RatStalker Error"):
        super().__init__(message)

class CommandError(RatStalkerError):
    """Exception for command execution"""
    def __init__(self, message="Execution Error"):
        super().__init__(message)

class MessageError(RatStalkerError):
    """Exception for messages"""
    def __init__(self, message="Message Error"):
        super().__init__(message)

class MatrixError(RatStalkerError):
    """Exception for Matrix protocol"""
    def __init__(self, message="Matrix Error"):
        super().__init__(message)
