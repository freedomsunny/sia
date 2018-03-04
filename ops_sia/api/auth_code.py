# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import json
import tornado.web

from ops_sia.plugins.JsonResponses import BaseHander
from ops_sia.plugins.code_auth import CodeAuth
from ops_sia.utils import get_token
from ops_sia.api.auth import auth as Auth
from ops_sia.cache import Backend
from ops_sia.options import get_options
options = get_options()



import ops_sia.log as logging

LOG = logging.getLogger(__name__)

url_map = {
    r"/auth_code": "AuthCodeApi",
    # r"/usr/getuserid": "GetIdByUserName"
}


class AuthCodeApi(BaseHander, Auth.Base):
    def get(self):
        session_id = self.get_argument("session_id", "").strip()
        obj = CodeAuth()
        img, code_str = obj.gene_code()
        self.set_header("Content-type", "image/png")
        self.write(img)
        cache = Backend()
        cache.conn.set("{0}_image_auth_code".format(session_id), code_str)
        cache.conn.expire("{0}_image_auth_code".format(session_id), options.auth_code_valid_time)

        # self.write({"code": 0,
        #             "message": "",
        #             "data": {"img": img,
        #                      "code_str": code_str}
        #             }
        #            )
        # 存redis


