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
        return ("Input shape is '%(expected_dims)s', while "
                "'%(actual_dims)s' is given.") % {
                    "expected_dims": self.expected_dims,
                    "actual_dims": self.actual_dims}
