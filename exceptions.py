"""Exceptions hierarchy

RatStalkerError
|
'---InvalidCommandError
|
'---CommandExecutionError
|
'---MatrixError
"""



class RatStalkerError(Exception):
    """Base exception class for the bot"""
    def __init__(self, message="RatStalker Error"):
        super().__init__(message)

class InvalidCommandError(RatStalkerError):
    """Exception for invalid command"""
    def __init__(self, message="Invalid Command"):
        super().__init__(message)

class CommandExecutionError(RatStalkerError):
    """Exception for command execution"""
    def __init__(self, message="Execution Error"):
        super().__init__(message)

class CommandExecutionError(RatStalkerError):
    """Exception for command execution"""
    def __init__(self, message="Execution Error"):
        super().__init__(message)

class MatrixError(RatStalkerError):
    """Exception for Matrix protocol"""
    def __init__(self, message="Matrix Error"):
        super().__init__(message)
