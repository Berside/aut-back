#!/usr/bin/python3
# -*- coding: utf-8 -*-
#Модуль чтения конфигурации

import json
import os

dirpath = os.path.dirname(__file__)
configpath = os.path.join(dirpath + "/config", 'config.json')

configuration = {}
with open(configpath) as file:
    json_str = file.read()

configuration = json.loads(json_str)

swaggerpath = os.path.join(dirpath + "/config", 'swagger.json')
swagger_data = {}
with open(swaggerpath) as file:
    json_str = file.read()
swagger_data = json.loads(json_str)