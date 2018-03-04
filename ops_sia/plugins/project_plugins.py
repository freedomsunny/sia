#!encoding=utf-8
from sqlalchemy import and_
import re
import json

from ops_sia.options import get_options
from ops_sia.utils import get_http, post_http, put_http, patch_http, get_token
import ops_sia.log as logging
from ops_sia.plugins.utils import check_user_name
from ops_sia.plugins.roles_plugins import RolesManager

LOG = logging.getLogger(__name__)


options = get_options()


class ProjectManager(object):
    @staticmethod
    def create_project(project_name, description="", enabled=False):
        data = {
            "project": {
                "description": description,
                "domain_id": "default",
                "enabled": enabled,
                "is_domain": False,
                "name": project_name
            }
        }
        if not check_user_name(project_name):
            return False, 400
        try:
            admin_token = get_token()
            if not admin_token:
                return False, 500
            data = json.dumps(data)
            header = {'Content-type': 'application/json', 'X-Auth-Token': admin_token.strip()}
            ret = post_http(url=options.project_ep, data=data, headers=header)
            if ret.status_code != 201:
                if ret.status_code == 409:
                    em = "create project error. name: <{0}>. project is already exist".format(project_name)
                    LOG.exception(em)
                    return False, ret.status_code
                em = "create project error. name: <{0}>".format(project_name)
                LOG.exception(em)
                return False, ret.status_code
            return True, 200
        except Exception as e:
            LOG.exception(e)
            return False, 500

    @staticmethod
    def get_project_id_by_name(project_name):
        if not check_user_name(project_name):
            return False, 400
        try:
            admin_token = get_token()
            if not admin_token:
                return False, 500
            header = {'Content-type': 'application/json', 'X-Auth-Token': admin_token.strip()}
            ret = get_http(url=options.project_ep + '?name=%s' % project_name, headers=header)
            if ret.status_code != 200:
                em = "get project id by name error. name: <{0}>".format(project_name)
                LOG.exception(em)
                return False, ret.status_code
            project_id = ret.json().get("projects")[0].get("id")
            return True, project_id
        except Exception as e:
            LOG.exception(e)
            return False, 500

    @staticmethod
    def update_project_user(user_id, user_name, project_name, member):
        if not check_user_name(user_name):
            return 0
        try:
            # user_id = UserManager.get_user_id_by_name(user_name)
            # if not user_id[0]:
            #     return False, user_id[1]
            project_id = ProjectManager.get_project_id_by_name(project_name)
            if not project_id[0]:
                return False, project_id[1]
            admin_token = get_token()
            if not admin_token:
                return False, 500
            role_id = RolesManager.get_role_id_by_name(member)
            if not role_id[0]:
                return False, role_id[1]
            header = {'X-Auth-Token': admin_token.strip()}
            ret = put_http(url=options.project_ep + '/%s/users/%s/roles/%s' % (project_id[1], user_id[1], role_id[1]),
                           headers=header)
            if ret.status_code != 204:
                em = "update project user failure"
                LOG.exception(em)
                return False, 500
            return True, 200
        except Exception as e:
            LOG.exception(e)
            return False, 500

    @staticmethod
    def change_project_status(project_id, status):
        """this method to change project status by project id
            status: is a boolean  True or False
        """
        try:
            data = {
                "project": {
                    "enabled": status,
                }
            }
            admin_token = get_token()
            if not admin_token:
                em = "change project status error. can not get admin token"
                LOG.exception(em)
                return False, 500
            data = json.dumps(data)
            header = {'X-Auth-Token': admin_token.strip()}
            ret = patch_http(headers=header, data=data)
            if ret.status_code != 200:
                em = "change project status error. project id: <{0}>".format(project_id)
                LOG.exception(em)
                return False, ret.status_code
            return True, 200
        except Exception as e:
            em = "change project status error. id: <{0}>. msg: <{1}>".format(project_id, e)
            LOG.exception(em)
            return False, 500
