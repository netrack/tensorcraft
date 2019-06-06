import numpy


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


class Model:
    """Machine-leaning model

    Attributes:
        model -- instance of keras model
        name -- the name of the model
        tag -- the tag of the model
    """

    def __init__(self, name: str, tag: str, model=None):
        self.model = model
        self.name = name
        self.tag = tag

    def load(self, loader):
        """Load the model from the given loader."""
        raise NotImplementedError

    def predict(self, x):
        x = numpy.array(x)

        # Calculate the shape of the input data and validate it with the
        # model parameters. This exception is handled by the server in
        # order to return an appropriate error to the client.
        _, *expected_dims = self.model.input_shape
        _, *actual_dims = x.shape

        if expected_dims != actual_dims:
            raise InputShapeError(expected_dims, actual_dims)

        return self.model.predict(x).tolist()

    def todict(self):
        return dict(name=self.name, tag=self.tag)

    def __str__(self):
        return "Model(name={0}, tag={1})".format(self.name, self.tag)
