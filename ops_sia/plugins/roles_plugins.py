#!encoding=utf-8
from sqlalchemy import and_
import re
import json

from ops_sia.options import get_options
from ops_sia.utils import get_http, post_http, get_token
import ops_sia.log as logging

LOG = logging.getLogger(__name__)

options = get_options()


class RolesManager(object):
    @staticmethod
    def get_role_id_by_name(member_name="user"):
        try:
            admin_token = get_token()
            if not admin_token:
                return False, 500
            header = {'Content-type': 'application/json', 'X-Auth-Token': admin_token.strip()}
            ret = get_http(url=options.roles_ep + "?name=%s" % member_name,
                           headers=header)
            if ret.status_code != 200:
                em = "get role id error....."
                LOG.exception(em)
                return False, ret.status_code
            roles = ret.json().get("roles")
            if not roles:
                em = "can not get member name from OpenStack. name: <{0}>".format(member_name)
                LOG.exception(em)
                return False, 500
            return True, ''.join([s.get("id") for s in roles if s.get("name") == member_name])
        except Exception as e:
            LOG.exception(e)
            return False, 500
