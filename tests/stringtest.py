import random
import string


def random_string(length=5):
    return "".join(random.sample(string.ascii_letters, length))
