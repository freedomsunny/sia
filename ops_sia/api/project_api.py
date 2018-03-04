# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import json
import datetime
import tornado.web

from ops_sia.plugins.JsonResponses import BaseHander
from ops_sia.plugins.project_plugins import ProjectManager
from ops_sia.api.auth import auth as Auth
import ops_sia.log as logging

LOG = logging.getLogger(__name__)
url_map = {
    # r"/project/create$": "CreateProject",
    # r"/project/getid$": "GetProjectIdByName",
    # r"/project/update$": "UpdateUserProject",
}


class CreateProject(BaseHander, Auth.Base):
    def post(self):
        try:
            data = json.loads(self.request.body)
            project_name = data.get("project_name")
            description = data.get("description")
            ret = ProjectManager.create_project(project_name, description)
            if not ret[0]:
                self.set_status(ret[1])
        except Exception as e:
            LOG.exception(e)
            self.set_status(500)


class GetProjectIdByName(BaseHander,  Auth.Base):
    def get(self):
        try:
            project_name = self.get_argument("project_name", '')
            ret = ProjectManager.get_project_id_by_name(project_name)
            if not ret[0]:
                self.set_status(ret[1])
        except Exception as e:
            LOG.exception(e)
            self.set_status(500)


class UpdateUserProject(BaseHander,  Auth.Base):
    def post(self):
        try:
            data = json.loads(self.request.body)
            user_name = data.get("user_name")
            project_name = data.get("project_name")
            member = data.get("member", "_member_")
            ret = ProjectManager.update_project_user(user_name, project_name, member)
            if not ret[0]:
                self.set_status(ret[1])
        except Exception as e:
            LOG.exception(e)
            self.set_status(500)
