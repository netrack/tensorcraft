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


class _ModelErrorMeta(type):

    error_mapping = {}

    def __new__(cls, *args, **kwargs):
        klass = super().__new__(cls, *args, **kwargs)
        if hasattr(klass, "error_code"):
            cls.error_mapping[klass.error_code] = klass
        return klass

    def from_error_code(self, error_code: str):
        return self.error_mapping.get(error_code, ModelError)


class ModelError(Exception, metaclass=_ModelErrorMeta):

    error_code = "Model Error"

    def __init__(self, name: str, tag: str):
        self.name = name
        self.tag = tag


class NotFoundError(ModelError):
    """Exception raised on missing model."""

    error_code = "Model Not Found"

    def __str__(self):
        return f"Model {self.name}:{self.tag} not found"


class NotLoadedError(ModelError):
    """Exception raised on attempt to use not loaded model."""

    error_code = "Model Not Loaded"

    def __str__(self):
        return f"Model {self.name}:{self.tag} is not loaded"


class DuplicateError(ModelError):
    """Exception raised on attempt to save model with the same name and tag."""

    error_code = "Model Duplicate"

    def __str__(self):
        return f"Model {self.name}:{self.tag} is a duplicate"


class LatestTagError(ModelError):
    """Exception raised on attempt to save model with latest tag."""

    error_code = "Model Latest Tag"

    def __str__(self):
        return f"Model {self.name}:{self.tag} cannot be latest"
