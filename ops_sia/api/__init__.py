#coding=utf8

from ops_sia.api.utils import load_url_map
from ops_sia import log as logging

LOG = logging.getLogger('api')

url_map = load_url_map(__path__, __package__, log=LOG)
