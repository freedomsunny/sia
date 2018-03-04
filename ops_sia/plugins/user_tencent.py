#!encoding=utf-8
from sqlalchemy import and_
import re
import json
import uuid

from threading import Thread

from ops_sia.options import get_options
from ops_sia.utils import get_http, post_http, put_http, patch_http, get_token
import ops_sia.log as logging
from ops_sia.plugins.utils import check_user_name, check_password, send_email, generate_url, CheckPassword
from ops_sia import cache
from ops_sia.plugins.project_plugins import ProjectManager
from ops_sia.db.models import RegisterPhones, db_session
from ops_sia.plugins.sms_auth import SendSmsMsg
LOG = logging.getLogger(__name__)

users_tencent_opts = [
    {"name": "testbbbb",
     "default": "",
     "help": '',
     "type": str},
]

options = get_options(users_tencent_opts)


class TencentUserManager(object):
    def add_user(self):
        pass

    def update_user(self):
        pass

    def delete_user(self):
        pass
