# Saving Keras Model During Training

One of the possible ways of using `tensorcraft` is publising model snapshots to
the server on each epoch end.
```py
from keras.models import Sequential
from keras.layers import Dense, Activation
from tensorcraft.callbacks import ModelCheckpoint

model = keras.Sequential()
model.add(Dense(32, input_dim=784))
model.add(Activation('relu'))

model.compile(optimizer='sgd', loss='binary_crossentropy')
model.fit(x_train, y_train, callbacks=[ModelCheckpoint(verbose=1)], epochs=100)
```
