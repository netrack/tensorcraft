# TensorCraft

[![Build Status][BuildStatus]](https://travis-ci.org/netrack/tensorcraft)
[![tensorcraft][SnapCraft]](https://snapcraft.io/tensorcraft)

The TensorCraft is a HTTP server that serves [Keras](https://github.com/keras-team/keras)
models using TensorFlow runtime.

_Currently TensorCraft is in beta, client and server API may change in the
future versions_.

This server solves such problems as:

* Versioning of models.
* Warehousing of models.
* Enabling CI/CD for machine-learning models.

## Installation

### Installation Using Snap

This is the recommended way to install `tensorcraft`. Simply run the following
command:
```bash
snap install tensorcraft --devmode --edge
snap start tensorcraft
```

### Installation Using Docker

TensorCraft can be used as a Docker container. The major note on this approach is
that `tensorflow` library that is installed into the Docker image is not compiled
with support of AVX instructions or GPU.
```bash
docker pull netrack/tensorcraft:latest
```

In order to start the container, run the following command:
```bash
docker run -it -p 5678:5678/tcp netrack/tensorcraft
```

You can optinally specify volume to persist models between restarts of conatiner:
```bash
docker run -it -p 5678:5678/tcp -v tensorcraft:/var/run/tensorcraft netrack/tensorcraft
```

### Installation Using PyPi

Install latest version from pypi repository.
```bash
pip install tensorcraft
```

## Using TensorCraft

### Keras Requirements

Currently, `tensorcraft` supports only models in the TensorFlow Saved Model, therefore
in order to publish Keras model, it must be saved as Saved Model at first.

Considering the following Keras model:
```py
from tensorflow import keras
from tensorflow.keras import layers

inputs = keras.Input(shape=(8,), name='digits')
x = layers.Dense(4, activation='relu', name='dense_1')(inputs)
x = layers.Dense(4, activation='relu', name='dense_2')(x)
outputs = layers.Dense(2, activation='softmax', name='predictions')(x)

model = keras.Model(inputs=inputs, outputs=outputs, name='3_layer_mlp')
```

Save it using the `export_saved_model` function from the 2.0 TensorFlow API:
```py
keras.experimental.export_saved_model(model, "3_layer_mlp")
```

### Starting Server

To start server run `server` command:
```sh
sudo tensorcraft server
```

By default it starts listening _unsecured_ port on localhost at `http://localhost:5678`.

Default configuration saves models to `/var/lib/tensorcraft` directory. Apart of
that server requires access to `/var/run` directory in order to save pid file
there.

### Pushing New Model

Note, both client and server of `tensorcraft` application share the same code
base. This implies the need to install a lot of server dependencies for a
client. This will be improved in uncoming versions.

Once model saved in directory, pack it using `tar` utility. For instance, this
is how it will look like for `3_layer_mlp` model from the previous example:
```sh
tar -cf 3_layer_mlp.tar 3_layer_mlp
```

Now the model packed into the archive can be pushed to the server under the
arbitrary tag:
```sh
tensorcraft push --name 3_layer_mlp --tag 0.0.1 3_layer_mlp.tar
```

### Listing Available Models

You can list all available models on the server using the following command:
```sh
tensorcraft list
```

After the execution of `list` command you'll see to available models:
```sh
3_layer_mlp:0.0.1
3_layer_mlp:latest
```

This is the features of `tensorcraft` server, each published model name results in
creation of _model group_. Each model group has it's `latest` tag, that references
the _latest pushed model_.

### Removing Model

Remove of the unused model can be performed in using `remove` command:
```sh
tensorcraft remove --name 3_layer_mlp --tag 0.0.1
```

Execution of `remove` commands results in the remove of the model itself, and
the model group, when is is the last model in the group.

### Using Model

In order to use the pushed model, `tensorcraft` exposes REST API. An example query
to the server looks like this:
```sh
curl -X POST https://localhost:5678/models/3_layer_mlp/0.0.1/predict -d \
    '{"x": [[1.0, 2.1, 1.43, 4.43, 12.1, 3.2, 1.44, 2.3]]}'
```

# License

The code and docs are released under the [Apache 2.0 license](LICENSE).

[BuildStatus]:   https://travis-ci.org/netrack/tensorcraft.svg?branch=master
[SnapCraft]:     https://snapcraft.io/tensorcraft/badge.svg
