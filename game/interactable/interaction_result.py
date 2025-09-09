from dark_libraries import immutable

@immutable
class InteractionResult:
    R_QUIET_SUCCESS = ""
    R_LOUD_SUCCESS  = "Success"

    R_FAILED        = "Failed"
    R_NOTHING_THERE = "Nothing to do"
    R_KEYBROKE      = "Key broke"
    R_LOCKED        = "Locked"

    def __init__(self, success: bool, message: str = ""):
        self.success = success
        self.message = message

    @classmethod
    def nothing(cls):
        return cls(success=False, message=cls.R_NOTHING_THERE)

    @classmethod
    def result(cls, message: str):
        if message in [cls.R_QUIET_SUCCESS, cls.R_LOUD_SUCCESS]:
            return cls.ok(message)
        else:
            return cls.error(message)
        
    @classmethod
    def ok(cls, message=R_QUIET_SUCCESS):
        return cls(success=True, message=message)

    @classmethod
    def error(cls, message=R_FAILED):
        return cls(success=False, message=message)

