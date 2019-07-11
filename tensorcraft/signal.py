class Signal:
    """Registers the signal subscribers and delivers signal when necessary."""

    def __init__(self):
        self.receivers = []

    def append(self, receiver):
        self.receivers.append(receiver)

    async def send(self, *args, **kwargs):
        for receiver in frozenset(self.receivers):
            await receiver(*args, **kwargs)
