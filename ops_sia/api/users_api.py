# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import json
import datetime
import tornado.web
import uuid
from sqlalchemy import and_


from ops_sia.plugins.JsonResponses import BaseHander
from ops_sia.plugins.users_plugins import UserManager
from ops_sia.utils import get_token
from ops_sia.api.auth import auth as Auth
from ops_sia.plugins.sms_auth import SendSmsMsg
from ops_sia.db.models import RegisterPhones, db_session


import ops_sia.log as logging

LOG = logging.getLogger(__name__)

url_map = {
    r"/test/sayhello": "SayHello",
    r"/user/adduser": "AddUser",
    r"/user/reset_password": "RestPassword",
    r"/user/verifyuser": "VerifyUser",
    r"/user/syncpwd": "AuthChangePassword",
    r"/user/checkexist": "CheckUserExist",
    r"/user/realnameauth": "UserRealNameAuth",
    r"/user/userinfo": "UserInfo",
    r"/user/changphone": "UpdatePhone",
}


class SayHello(BaseHander):
    def get(self):
        msg = "Hello Word"
        self.write(msg)


# class AddUser(BaseHander,  Auth.Base):
#     def post(self):
#         """只发送邮件到用户邮箱中，不实际添加用户"""
#         try:
#             data = json.loads(self.request.body)
#             user_name = data.get("user_name")
#             password = data.get("password")
#             description = data.get("description")
#             url = data.get("url")
#             register_method = data.get("register_method")
#             # 检查用户是否存在
#             ret = UserManager.get_user_id_by_name(user_name)
#             if ret[0]:
#                 self.set_status(409)
#                 return
#             if register_method == 1:
#                 if not user_name or not password:
#                     em = "Invalid parameter for register user"
#                     LOG.exception(em)
#                     self.set_status(400)
#                     return
#                 ret = UserManager.send_register_email2user(user_name, password, description, url)
#                 if not ret[0]:
#                     return ret[1]
#             if register_method == 0:
#                 pass
#
#         except Exception as e:
#             LOG.exception(e)
#             self.set_status(500)


class AddUser(BaseHander,  Auth.Base):
    def post(self):
        try:
            data = json.loads(self.request.body)
            user_name = data.get("user_name").strip()
            password = data.get("password").strip()
            phone = str(data.get("phone")).strip()
            session_id = data.get("session_id").strip()
            auth_code = str(data.get("auth_code")).strip()
            description = json.dumps({"phone": phone})
            if not user_name:
                self.write({"code": 1, "result": "用户名无效"})
                self.set_status(500)
                return
            if not password:
                self.write({"code": 1, "result": "密码无效"})
                self.set_status(500)
                return
            if not phone:
                self.write({"code": 1, "result": "手机号无效"})
                self.set_status(500)
                return
            if not session_id:
                self.write({"code": 1, "result": "会话ID无效"})
                self.set_status(500)
                return
            # 检查用户是否存在
            ret = UserManager.get_user_id_by_name(user_name)
            if ret[0]:
                self.set_status(409)
                self.write({"code": 1, "result": "用户已存在"})
                return
            # 检查验证码
            ret = SendSmsMsg.check_phone(session_id + "_" + phone)
            if not ret:
                self.write({"code":1, "result": "无效的验证码"})
                self.set_status(500)
                return
            if str(auth_code) != str(ret):
                self.write({"code": 1, "result": "无效的验证码"})
                self.set_status(500)
                return
            # 检查手机号码是否被注册
            phone_check = RegisterPhones.query.filter(RegisterPhones.phone == phone).first()
            if phone_check:
                self.set_status(409)
                self.write({"code": 1, "result": "手机已被注册"})
                return
            ret = UserManager.create_user_project(user_name, password, description)
            if not ret[0]:
                self.write({"code": 1, "result": "创建失败"})
                return
            # 添加到数据库
            user_id = UserManager.get_user_id_by_name(user_name)
            db_obj = RegisterPhones(id=str(uuid.uuid1()),
                                    user_name=user_name,
                                    user_id=user_id,
                                    phone=phone)
            db_session.add(db_obj)
            db_session.commit()
            # 清除redis中的数据
            SendSmsMsg.delete_phone_auth_code(session_id + "_" + phone)
            self.write({"code": 0, "result": "创建成功"})
        except Exception as e:
            LOG.exception(e)
            self.set_status(500)
            self.write({"code": 1, "result": "未知错误{0}".format(e)})


class CheckUserExist(BaseHander, Auth.Base):
    def get(self):
        user_name = self.get_argument("user_name").strip()
        ret = UserManager.get_user_id_by_name(user_name)
        if ret[0]:
            self.set_status(409)
            self.write({"code": 409, "result": "用户已存在"})
            return
        self.write({"code": 200, "result": ""})


class CheckPhoneExist(BaseHander, Auth.Base):
    def get(self):
        phone = self.get_argument("phone").strip()


class VerifyUser(BaseHander,  Auth.Base):
    """通过rand_id来验证用户，真正的添加用户"""
    def post(self):
        try:
            data = json.loads(self.request.body)
            rand_id = data.get("id")
            ret = UserManager.create_user_project(rand_id)
            if not ret[0]:
                self.set_status(ret[1])
        except Exception as e:
            em = "verify user error....msg: <{0}>".format(e)
            LOG.exception(em)
            self.set_status(500)


class RestPassword(BaseHander,  Auth.Base):
    def post(self):
        """just send mail to user's e_mail"""
        try:
            data = json.loads(self.request.body)
            user_name = data.get("user_name")
            url = data.get("url")
            if not user_name or not url:
                em = "Invalid parameter"
                LOG.exception(em)
                self.set_status(400)
                return
            ret = UserManager.reset_password(user_name, url)
            if not ret[0]:
                self.set_status(ret[1])
        except Exception as e:
            LOG.exception(e)
            self.set_status(500)

    def put(self):
        """reset user's password from OpenStack"""
        try:
            data = json.loads(self.request.body)
            rand_id = data.get("rand_id")
            password = data.get("password")
            if not rand_id or not password:
                em = "Invalid parameter"
                LOG.exception(em)
                self.set_status(400)
                return
            ret = UserManager.reset_password_os(rand_id, password)
            if not ret[0]:
                self.set_status(ret[1])
        except Exception as e:
            LOG.exception(e)
            self.set_status(500)


class AuthChangePassword(BaseHander,  Auth.Base):
    def post(self):
        """auth user from old platform.
        if auth success change password to new platform
        else not do anythings"""
        try:
            data = json.loads(self.request.body)
            user_name = data.get("user_name")
            password = data.get("password")
            if not user_name or not password:
                em = "argument error.... "
                LOG.exception(em)
                self.set_status(400)
                return
            # check user is it auth successful from old platform
            ret = UserManager.auth_user_by_password(user_name, password)
            if not ret[0]:
                self.set_status(ret[1])
                return
            # check user is it exist at new platform
            ret = UserManager.get_user_id_by_name(user_name)
            if ret[0]:
                user_id = ret[1]
                # if auth successful. change password
                ret = UserManager.change_user_password_os(user_id, password)
                if not ret[0]:
                    self.set_status(500)
        except Exception as e:
            em = "auth change user error. user_name: <{0}>. msg: <{1}>".format(user_name, e)
            LOG.exception(em)
            return self.set_status(500)


class UserRealNameAuth(BaseHander,  Auth.BaseAuth):
    """用户在cmdb实名认证成功后，将认证信息同步到用户管理（sia）中"""
    def post(self):
        data = json.loads(self.request.body)
        user_id = str(data.get("user_id", "")).strip()
        user_name = str(data.get("user_name", "")).strip()
        auth_phone = str(data.get("auth_phone", "")).strip()
        if not user_id or not auth_phone:
            em = "Error. sync user real name auth. argment error"
            LOG.exception(em)
            self.write({"code": 1, "result": em})
            return
        # 更新数据库，如果存在则更新，不存在则添加
        check_user = RegisterPhones.query.filter(RegisterPhones.user_id == user_id).first()
        if not check_user:
            db_obj = RegisterPhones(id=str(uuid.uuid1()),
                                    user_name=user_name,
                                    user_id=user_id,
                                    phone=auth_phone,
                                    is_real_auth=True,
                                    is_sms_auth=True)
            db_session.add(db_obj)
        else:
            # 实名认证的手机和注册的手机是否相同
            if check_user.phone != auth_phone:
                self.write({"code": 1, "result": "与注册手机不相符，请重新输入手机号"})
                return
            check_user.is_real_auth = True
            check_user.is_sms_auth = True
        db_session.commit()
        self.write({"code": 0, "result": ""})


class UserInfo(BaseHander, Auth.BaseAuth):
    """个人信息"""
    def post(self):
        data = json.loads(self.request.body)

        name = data.get("name", "")
        user_name = str(data.get("user_name", "")).strip()
        company = data.get("company", "")
        user_id = self.context.get("user_id")
        ret = UserManager.add_user_info(user_id=user_id,
                                        user_name=user_name,
                                        name=name,
                                        company=company)

        self.json_response(1, result=ret)

    def put(self):
        data = json.loads(self.request.body)

        name = data.get("name", "")
        company = data.get("company", "")
        user_id = self.context.get("user_id")
        user_name = self.context.get("user_name")
        ret = UserManager.update_user_info(user_id=user_id,
                                           name=name,
                                           company=company,
                                           user_name=user_name)
        self.write(ret)

    def get(self):
        """获取用户信息"""
        user_id = self.context.get("user_id").strip()
        token = self.context.get("token").strip()
        ret = UserManager.get_userinfo(user_id=user_id,
                                       token=token)
        if ret:
            self.json_response(0, result=ret)
        else:
            self.json_response(1, result=ret)


class UpdatePhone(BaseHander, Auth.BaseAuth):
    """修改用户手机"""
    def put(self):
        data = json.loads(self.request.body)
        phone = str(data.get("phone", "")).strip()
        user_name = str(data.get("user_name", "")).strip()
        session_id = str(data.get("session_id", "")).strip()
        auth_code = str(data.get("auth_code", "")).strip()
        user_id = self.context.get("user_id", "")
        # 检查手机号是否被注册使用
        db_obj = RegisterPhones.query.filter(RegisterPhones.phone == phone).first()
        if db_obj:
            em = u"手机号已被注册"
            self.write({"code": 1, "result": em})
            return
        if not phone:
            em = u"无效手机号"
            self.write({"code": 1, "result": em})
            return
        if not session_id:
            em = u"无效会话id"
            self.write({"code": 1, "result": em})
            return
        if not auth_code:
            em = u"无效验证码"
            self.write({"code": 1, "result": em})
            return
        ret = UserManager.update_phone(new_phone=phone,
                                       session_id=session_id,
                                       auth_code=auth_code,
                                       user_id=user_id,
                                       user_name=user_name)
        self.write(ret)
