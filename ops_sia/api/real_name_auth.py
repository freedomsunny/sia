# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import json
from sqlalchemy import and_

from ops_sia.plugins.JsonResponses import BaseHander
from ops_sia.api.auth import auth as Auth
from ops_sia.plugins.upload_file import *
from ops_sia.plugins.real_name_auth import AuthInfoParser, RealNameAuth, AuthInfoCMDBParser
from ops_sia.plugins.ocmdb import CMDBOpreate
from ops_sia.options import get_options
from ops_sia.plugins.wechat_notify import WechatNotify
from ops_sia.plugins.sms_auth import send_msg
from ops_sia.db.models import AuthInfo, db_session

import ops_sia.log as logging

LOG = logging.getLogger(__name__)

url_map = {
    r"/realauth": "RealNameAuthAPI",
    r"/realauth/(?P<id>.+)": "RealNameAuthAPI",
    r"/hookcallback": "CMDBHookBack",
    r"/realauth_old": "RealNameAuthOld"
}

options = get_options()


class RealNameAuthAPI(BaseHander, Auth.BaseAuth):
    def get(self, **kwargs):
        try:
            user_id = str(self.path_kwargs.get('id', "")).strip()
            id = self.get_argument("id", "").strip()
            auth_type = self.get_argument("auth_type", "").strip()
            result = RealNameAuth.get_auth_info(user_id=user_id,
                                                id=id,
                                                auth_type=auth_type)
            self.json_response(code=0, result=result)
        except Exception as e:
            self.json_response(code=1, result={}, message=e)

    def post(self):
        try:
            data_obj = AuthInfoParser(self, self.context)
            # 存数据库
            auth_info_obj = RealNameAuth.add_auth_info(data_obj)
            if isinstance(auth_info_obj, dict):
                self.write(auth_info_obj)
                return
            auth_info_obj.image_list = []
            for field_name, files in self.request.files.items():
                for file in files:
                    image = send_file(file, auth_info_id=auth_info_obj.id)
                    auth_info_obj.image_list.append({'id': image.id, 'url': get_pictuer_url(image.name)})
            for notify_user in options.wechat_realname_auth_notify:
                WechatNotify.send_msg2user(user_id=notify_user,
                                           operator=data_obj.user_name,
                                           title=u"实名认证",
                                           content=u"用户创建了实名认证申请",
                                           token=data_obj.token)

            # 更新到cmdb
            CMDBOpreate.syncdata2cmdb(resouce_type="new_realauth", id=auth_info_obj.id)
            self.json_response(code=0, result=auth_info_obj)
        except Exception as e:
            self.json_response(code=1, result={}, message=e)

    def put(self, **kwargs):
        try:
            id = str(self.path_kwargs.get('id', "")).strip()
            data = json.loads(self.request.body)

            result = RealNameAuth.update_auth_info(id=id,
                                                   data=data)
            if result:
                for notify_user in options.wechat_realname_auth_notify:
                    WechatNotify.send_msg2user(user_id=notify_user,
                                               operator=self.context.get("user").get("user").get("name"),
                                               title=u"实名认证",
                                               content=u"用户更新了实名认证申请",
                                               token=self.context.get("token"))
            # 更新到cmdb
            CMDBOpreate.syncdata2cmdb(resouce_type="new_realauth", id=id)
            self.json_response(code=0, result=result)
        except Exception as e:
            self.json_response(code=1, result={}, message=e)

    def delete(self):
        id = str(self.path_kwargs.get('id', "")).strip()


class CMDBHookBack(BaseHander, Auth.Base):
    def get(self):
        id = self.get_argument("uuid", "").strip()
        result = CMDBOpreate.get_cmdb_info_by_uuid(uuid=id)
        if not result:
            self.write({"code": 0, "message": "", "data": []})
            return
        data_obj = AuthInfoCMDBParser(data=result)
        db_obj = AuthInfo.query.filter(AuthInfo.id == data_obj.id).first()

        if data_obj.status == 1:
            msg = options.sms_real_name_auth_template.format("已", ".")
            # 更新状态为已通过
            db_obj.status = data_obj.status
        elif data_obj.status == 0:
            msg = options.sms_real_name_auth_template.format("未", ",请重新提交申请")
            # 删除申请
            db_obj.status = data_obj.status
            db_obj.deleted = True
        else:
            em = "undefine status code <{0}>".format(data_obj.status)
            LOG.exception(em)
            self.json_response(code=1, result=[], message=em)
            return
        # 发送短信
        send_msg(phone=data_obj.auth_phone, msg=msg)
        db_session.commit()
        # 同步数据到cmdb
        CMDBOpreate.syncdata2cmdb(resouce_type="new_realauth", id=id)
        self.json_response(code=0, result=db_obj)


class RealNameAuthOld(BaseHander, Auth.BaseAuth):
    def get(self):
        user_id = self.context.get("user_id")
        if not user_id:
            em = "参数错误"
            self.write({"code": 1, "result": em})
            return
        result = CMDBOpreate.real_name_auth(user_id)
        if not result:
            em = "获取用户信息失败"
            self.write({"code": 1, "result": em})
            return
        # 状态为0（审核不通过）
        # 状态为1（审核通过）
        status = result.get("status")
        if status == 1:
            self.write({"code": 0, "result": ""})
            return
        if status == 0:
            em = "审核不通过"
            self.write({"code": 1, "result": em})
            return

