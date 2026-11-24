from nova.models import Permission

class PolicyGate:
    def __init__(self, granted: set[Permission] | None = None) -> None:
        self.granted = granted if granted is not None else {Permission.NONE, Permission.MEMORY_READ, Permission.MEMORY_WRITE}

    def allows(self, permission: Permission) -> bool:
        return permission in self.granted
