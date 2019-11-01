from typing import Callable


def urlto(path: str) -> Callable:
    def _to(func):
        func.url = path
        return func
    return _to
