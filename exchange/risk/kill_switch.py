class KillSwitch:
    def __init__(self):
        self._enabled = False

    def trigger(self):
        self._enabled = True

    def reset(self):
        self._enabled = False

    def is_triggered(self) -> bool:
        return self._enabled
