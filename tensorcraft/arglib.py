import inspect


def filter_callable_arguments(callable, **kwargs):
    argnames = inspect.getfullargspec(callable)
    return {k: v for k, v in kwargs.items() if k in argnames.args}
