import re

class Logger:

    @classmethod
    def _to_snake_case(cls, s):
        s = re.sub(r'[\s\-]+', '_', s)                    # Replace spaces and hyphens with underscores
        s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)     # Add underscore before capital letters
        s = re.sub(r'[^\w_]', '', s)                      # Remove non-word characters
        return s.lower()

    def __init__(self, instance):
        snek_case_name = __class__._to_snake_case(instance.__class__.__name__)
        self.prefix = f"[{snek_case_name}:{id(instance)}] "

    def log(self, msg):
        print(self.prefix, msg)