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


class ModelError(Exception):

    error_code = 600

    def __init__(self, name: str, tag: str):
        self.name = name
        self.tag = tag


class NotFoundError(ModelError):
    """Exception raised on missing model."""

    error_code = 604

    def __str__(self):
        return f"Model {self.name}:{self.tag} not found"


class NotLoadedError(ModelError):
    """Exception raised on attempt to use not loaded model."""

    error_code = 609

    def __str__(self):
        return f"Model {self.name}:{self.tag} is not loaded"


class DuplicateError(ModelError):
    """Exception raised on attempt to save model with the same name and tag."""

    error_code = 610

    def __str__(self):
        return f"Model {self.name}:{self.tag} is a duplicate"


class LatestTagError(ModelError):
    """Exception raised on attempt to save model with latest tag."""

    error_code = 611

    def __str__(self):
        return f"Model {self.name}:{self.tag} cannot be latest"
