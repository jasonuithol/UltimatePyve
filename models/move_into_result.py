class MoveIntoResult(tuple):
    __slots__ = ()

    def __new__(cls, traversal_allowed: bool, alternative_action_taken: bool):
        return super().__new__(cls, (traversal_allowed, alternative_action_taken))

    @property
    def traversal_allowed(self) -> bool:
        return self[0]

    @property
    def alternative_action_taken(self) -> bool:
        return self[1]