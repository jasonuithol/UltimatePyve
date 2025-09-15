from typing import Any
from dark_libraries import immutable

@immutable
class InteractionResult:
    R_QUIET_SUCCESS = ""
    R_LOUD_SUCCESS  = "Success"

    R_FAILED        = "Failed"
    R_NOTHING_THERE = "Nothing to do"
    R_KEYBROKE      = "Key broke"
    R_LOCKED        = "Locked"
    R_FOUND_ITEM    = "Found something"

    def __init__(self, success: bool, message: str = "", payload: Any = None):
        self.success = success
        self.message = message
        self.payload = payload

    @classmethod
    def nothing(cls):
        return cls(success=False, message=cls.R_NOTHING_THERE)

    @classmethod
    def result(cls, message: str = "", payload: Any = None):
        if message in [cls.R_QUIET_SUCCESS, cls.R_LOUD_SUCCESS]:
            return cls.ok(message=message, payload=payload)
        else:
            return cls.error(message=message, payload=payload)
        
    @classmethod
    def ok(cls, message=R_QUIET_SUCCESS, payload: Any = None):
        return cls(success=True, message=message, payload=payload)

    @classmethod
    def error(cls, message=R_FAILED, payload: Any = None):
        return cls(success=False, message=message, payload=payload)

