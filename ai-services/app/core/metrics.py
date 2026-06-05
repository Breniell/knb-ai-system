from collections import defaultdict


class InMemoryMetrics:
    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)

    def inc(self, key: str, by: int = 1) -> None:
        self._counters[key] += by

    def snapshot(self) -> dict[str, int]:
        return dict(self._counters)


metrics = InMemoryMetrics()

