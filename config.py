# -*- coding: utf-8 -*-

import configparser
import logging
import os
from typing import *

logger = logging.getLogger(__name__)

CONFIG_PATH_LIST = [
    os.path.join('config', 'config.ini'),
    os.path.join('config', 'config.example.ini')
]

_config: Optional['AppConfig'] = None


def init():
    if reload():
        return
    logger.warning('Using default config')
    global _config
    _config = AppConfig()


def reload():
    config_path = ''
    for path in CONFIG_PATH_LIST:
        if os.path.exists(path):
            config_path = path
            break
    if config_path == '':
        return False

    config = AppConfig()
    if not config.load(config_path):
        return False
    global _config
    _config = config
    return True


def get_config():
    return _config


class AppConfig:
    def __init__(self):
        self.database_url = 'sqlite:///data/database.db'
        self.tornado_xheaders = False

    def load(self, path):
        try:
            config = configparser.ConfigParser()
            config.read(path, 'utf-8-sig')

            self._load_app_config(config)
        except Exception as e:
            logger.exception(f'Failed to load config: {e}')
            return False
        return True

    def _load_app_config(self, config):
        app_section = config['app']
        self.database_url = app_section['database_url']
        self.tornado_xheaders = app_section.getboolean('tornado_xheaders')


def _str_to_list(value, item_type: Type = str, container_type: Type = list):
    value = value.strip()
    if value == '':
        return container_type
    items = value.split(',')
    items = map(lambda item: item.strip(), items)
    if item_type is not str:
        items = map(lambda item: item_type(item), items)
    return container_type(items)
