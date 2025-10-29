import re
import colorama
import sys

from datetime import datetime
from typing import Callable

type SuffixFunc = Callable[[], str]

MESSAGE_COLUMN_OFFSET = 54 # you better have a wide screen !

class Logger:

    @classmethod
    def _to_snake_case(cls, s):
        s = re.sub(r'[\s\-]+', '_', s)                    # Replace spaces and hyphens with underscores
        s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)     # Add underscore before capital letters
        s = re.sub(r'[^\w_]', '', s)                      # Remove non-word characters
        return s.lower()

    @classmethod
    def _objectid_suffix_func(cls, logged_instance) -> SuffixFunc:
        return lambda: id(logged_instance)

    def __init__(self, instance, use_object_id_suffix = False):
        self.set_prefix_mode(
            class_prefix         = __class__._to_snake_case(instance.__class__.__name__),
            instance_suffix_func = __class__._objectid_suffix_func(instance) if use_object_id_suffix else None
        )
        self.show_debug = "-debug" in sys.argv

    def set_prefix_mode(self, class_prefix: str, instance_suffix_func: SuffixFunc):

        if instance_suffix_func is None:
            self.prefix = f"{class_prefix}"
        else:
            self.prefix = f"{class_prefix}:{instance_suffix_func()}"

    def log(self, msg):
        ascii_control_code_prefix = colorama.Style.RESET_ALL

        # Make 3rd party messages stand out
        ascii_control_code_suffix = colorama.Style.BRIGHT + colorama.Fore.CYAN

        if "ERROR" in msg:
            ascii_control_code_prefix = colorama.Style.BRIGHT + colorama.Fore.RED

        elif "WARN" in msg:
            ascii_control_code_prefix = colorama.Style.BRIGHT + colorama.Fore.YELLOW

        elif "DEBUG" in msg:
            if self.show_debug == False:
                return

        else:
            # the "default" level.  consider it the INFO level.
            if self.show_debug == True:
                ascii_control_code_prefix = colorama.Style.BRIGHT + colorama.Fore.WHITE

        time_prefix = datetime.now().time().isoformat(timespec="milliseconds")
        entire_prefix = f"[{time_prefix} {self.prefix}]".ljust(MESSAGE_COLUMN_OFFSET)
        print(ascii_control_code_prefix + entire_prefix + msg + ascii_control_code_suffix)
        
class LoggerMixin:
    def __init__(self):
        self._logger = Logger(self)
        self.log = self._logger.log
        super().__init__()

    # ---------------------------------------------------------------------------------------
    #
    # WARNING: Adding an _after_inject handler here will break the _after_inject handler of
    #          every class that has multiple inheritence that includes this as an ancestor.
    #
    # ---------------------------------------------------------------------------------------
