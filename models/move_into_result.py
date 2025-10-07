
from dark_libraries.custom_decorators import auto_init, immutable

@immutable
@auto_init
class MoveIntoResult:
    traversal_allowed: bool
    alternative_action_taken: bool