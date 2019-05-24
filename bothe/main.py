import aiohttp
import aiohttp.web
import numpy
import json
import yaml
import schema

import bothe.module.keras
import bothe.web.server


k = bothe.module.keras.Keras()
SCHEMA = schema.Schema([{"name": schema.And(str, len), **k.schema()}])


with open("bothe.yml") as f:
    config = yaml.full_load(f)


cfg = SCHEMA.validate(config)[0]
k.prepare(cfg)


s = bothe.web.server.Server()
s.handle(k)
s.serve()
