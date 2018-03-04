# -*- coding:utf-8 -*-
# from __future__ import unicode_literals
import json
import datetime
import tornado.web
from tornado.web import url, StaticFileHandler

import uuid
from sqlalchemy import and_


from ops_sia.plugins.JsonResponses import BaseHander
from ops_sia.plugins.upload_file import *
from ops_sia.utils import get_token
from ops_sia.api.auth import auth as Auth
from ops_sia.plugins.sms_auth import SendSmsMsg
from ops_sia.db.models import RegisterPhones, db_session
from ops_sia.options import get_options
import ops_sia.log as logging


LOG = logging.getLogger(__name__)

url_map = {
        r"/picture/(?P<fname>.+)$": "FileUpload",
}
options = get_options()


class FileUpload(BaseHander, Auth.Base):
    def get(self, **kwargs):
        file_name = str(self.path_kwargs.get('fname', "")).strip()
        try:
            with open(options.file_path + file_name, "rb") as F:
                self.set_header("Content-type", "image/png")
                self.write(F.read())
        except:
            pass

    def post(self):
        pass
