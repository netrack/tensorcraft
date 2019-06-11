class InputShapeError(Exception):
    """Exception raised for invalid model input shape

    Attributes:
        expected_dims -- model's dimensions
        actual_dims -- input dimensions
    """

    def __init__(self, expected_dims, actual_dims):
        self.expected_dims = tuple(expected_dims)
        self.actual_dims = tuple(actual_dims)

    def __str__(self):
        return "Input shape is {0}, while {1} is given.".format(
            self.expected_dims, self.actual_dims)


class NotFoundError(Exception):
    """Exception raised on missing model

    Attributes:
        name --- model name
        tag -- model tag
    """

    def __init__(self, name: str, tag: str):
        self.name = name
        self.tag = tag

    def __str__(self):
        return "Model {0}:{1} not found".format(self.name, self.tag)


class NotLoadedError(Exception):
    """Exception raised on attempt to use not loaded model.

    Attributes:
        name -- model name
        tag -- model tag
    """

    def __init__(self, name: str, tag: str):
        self.name = name
        self.tag = tag

    def __str__(self):
        return "Model {0}:{1} is not loaded".format(self.name, self.tag)
