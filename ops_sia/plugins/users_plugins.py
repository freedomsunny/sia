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

users_opts = [
    {"name": "password_verify_timeout",
     "default": 86400,
     "help": '',
     "type": int},
    {"name": "send_register_timeout",
     "default": 86400,
     "help": '',
     "type": int},
    {"name": "old_platform_userid_ep",
     "default": 'http://10.2.0.61:8108/entity/bss_db/b_customer_info?custom_account=',
     "help": "old platform get user's end point",
     "type": str},
]

options = get_options(users_opts)


class UserManager(object):
    @staticmethod
    def add_user(user_name, password, description=""):
        """add user to openstack"""
        try:
            # check user_name is it valid
            if not check_user_name(user_name):
                return False, 400
            # check password is it strong
            if not check_password(password):
                return False, 400

            admin_token = get_token()
            if not admin_token:
                em = "get admin token error"
                LOG.exception(em)
                return False, 500
            header = {'Content-type': 'application/json', 'X-Auth-Token': admin_token.strip()}
            data = {
                "user": {
                    "enabled": True,
                    "name": user_name,
                    "password": password,
                    "description": description
                }
            }
            data = json.dumps(data)
            ret = post_http(url=options.user_ep, data=data, headers=header)
            if ret.status_code != 201:
                if ret.status_code == 409:
                    em = "create user error. name: <{0}>. user is already exist".format(user_name)
                    LOG.exception(em)
                    return False, ret.status_code
                em = "create user error. name: <{0}>".format(user_name)
                LOG.exception(em)
                return False, ret.status_code
            return True, 200
        except Exception as e:
            LOG.exception(e)
            return False, 500

    @staticmethod
    def get_user_id_by_name(user_name):
        try:
            # check user_name is it valid
            if not check_user_name(user_name):
                return False, 400
            admin_token = get_token()
            if not admin_token:
                em = "get admin token error"
                LOG.exception(em)
                return False, 500
            header = {'Content-type': 'application/json', 'X-Auth-Token': admin_token.strip()}
            ret = get_http(url=options.user_ep + "?name=%s" % user_name, headers=header)
            if ret.status_code != 200:
                em = "get user's id error"
                LOG.exception(em)
                return False, 500
            data = ret.json()
            return True, data.get('users')[0].get("id")
        except Exception as e:
            LOG.exception(e)
            return False, 500

    @staticmethod
    def get_user_info(token, user_id):
        url = options.keystone_endpoint + "/users/" + user_id
        headers = {'X-Auth-Token': token}
        ret = get_http(url=url, headers=headers)
        if ret.status_code != 200:
            em = u"获取用户信息失败"
            LOG.exception(em)
            return False, 500
        return True, ret.json()

    @staticmethod
    def reset_password(user_name, url):
        """just send e_mail to user email"""
        try:
            backend = cache.Backend()
            # check user name is it valid
            if not check_user_name(user_name):
                return False, 400
            # check user is it exist
            user_id = UserManager.get_user_id_by_name(user_name)
            if not user_id[0]:
                em = "user name <{0}> is not exist.".format(user_name)
                LOG.exception(em)
                return False, 400
            rand_id, reset_pass_url = generate_url(url)
            content = u"""
                      {0} 您好！
                      密码重置说明
    
                      ----------------------------------------------------------------------
    
                      您只需在提交请求后的24小时内，通过点击下面的链接重置您的密码：
                       {1}
    
                      (如果上面不是链接形式，请将该地址手工粘贴到浏览器地址栏再访问)
    
                      在上面的链接所打开的页面中输入新的密码后提交，您即可使用新的密码登录平台了。
    
                                                                                        此致    
                                                                                        象云团队
                      """ .format(user_name, reset_pass_url)
            subject = u'密码找回【象云科技】'
            task = Thread(target=lambda: send_email(user_name, content, subject))
            task.setDaemon(True)
            task.start()
            backend.set(id=rand_id, user_msg={"user_name": user_name, "user_id": user_id[1]},
                        timeout=options.password_verify_timeout)
            return True, 200
        except Exception as e:
            LOG.exception(e)
            return False, 500

    @staticmethod
    def reset_password_os(rand_id, password):
        """reset password from OpenStack"""
        try:
            # check password is it strong
            if not check_password(password):
                return False, 400
            backend = cache.Backend()
            user_data = backend.get(rand_id)
            if not user_data:
                em = "can not found rand_id from redis"
                LOG.exception(em)
                return False, 400
            user_id = user_data.get("user_id")
            admin_token = get_token()
            url = options.user_ep + "/%s" % user_id
            header = {'Content-type': 'application/json', 'X-Auth-Token': admin_token.strip()}
            data = {
                "user": {
                    "password": password
                }
            }
            data = json.dumps(data)
            ret = patch_http(url=url, headers=header, data=data)
            if ret.status_code != 200:
                em = "update user's password error. user id: <{0}>".format(user_id)
                LOG.exception(em)
                return False, ret.status_code
            backend.delete(rand_id)
            return True, 200
        except Exception as e:
            em = "reset password error, msg: {0}".format(e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def send_register_email2user(user_name, password, description, url):
        try:
            backend = cache.Backend()
            # check user name is it valid
            if not check_user_name(user_name):
                return False, 400
            rand_id, reg_url = generate_url(url)
            content = u"""
                        邮箱验证
                        
                        Hi，{0}
                        
                        感谢您注册象云科技！我们需要对您的地址有效性进行验证以避免垃圾邮件或地址被盗用。
                        
                        {1}
                        
                        请您在24小时内点击该链接，也可以将链接复制到浏览器地址栏访问。
                        
                        本邮件由系统自动发出，请勿直接回复！
                        
                                                                                        此致    
                                                                                        象云团队
                        """.format(user_name, reg_url)
            subject = u'邮箱验证【象云科技】'
            task = Thread(target=lambda: send_email(user_name, content, subject))
            task.setDaemon(True)
            task.start()
            backend.set(id=rand_id, user_msg={"user_name": user_name, "password": password, "description": description},
                        timeout=options.send_register_timeout)
            return True, 200
        except Exception as e:
            em = u"send register email to user error. user_name: <{0}> msg: <{1}>".format(user_name, e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def create_user_project(user_name, password, description, rand_id=None):
        """添加用户、添加项目、将用户加入到项目"""
        try:
            # backend = cache.Backend()
            # data = backend.get(rand_id)
            # if not data:
            #     em = "create user project error. can not get data from redis. rand id: <{0}>".format(rand_id)
            #     LOG.exception(em)
            #     return False, 400
            # user_name = data.get("user_name")
            # password = data.get("password")
            # description = data.get("description")

            # 先添加用户
            ret = UserManager.add_user(user_name, password, description=description)
            if not ret[0]:
                return ret
            # 获取用户ID
            user_id = UserManager.get_user_id_by_name(user_name)
            if not user_id[0]:
                return False, user_id
            # 再添加项目
            ret = ProjectManager.create_project(user_name, enabled=True)
            if not ret[0]:
                return ret
            # 用户与项目进行关联
            ret = ProjectManager.update_project_user(user_id, user_name, user_name, member="user")
            if not ret[0]:
                return ret
            # 注册用户同步添加到腾讯云账号

            # backend.delete(rand_id)
            return True, 200
        except Exception as e:
            em = "create user and project error msg: <{0}>".format(e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def change_user_password_os(user_id, password):
        try:
            admin_token = get_token()
            if not admin_token:
                em = "can not get admin token"
                LOG.exception(em)
                return False, 500
            url = options.user_ep + "/%s" % user_id
            header = {'Content-type': 'application/json', 'X-Auth-Token': admin_token.strip()}
            data = {
                "user": {
                    "password": password
                }
            }
            data = json.dumps(data)
            ret = patch_http(url=url, headers=header, data=data)
            if ret.status_code != 200:
                em = "update user's password error. user id: <{0}>".format(user_id)
                LOG.exception(em)
                return False, ret.status_code
            return True, 200
        except Exception as e:
            em = "change user password error. user id: <{0}>. msg: <{1}>".format(user_id, e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def auth_user_by_password(user_name, password):
        try:
            data = {'username': user_name,
                    'password': password
                    }
            ret = post_http(url=options.old_keystone_admin_endpoint, data=data).json()
            if ret.get("code") != 0:
                return False, 500
            return True, 200
        except Exception as e:
            em = "auth user error. user name: <{0}> msg: <{1}>".format(user_name, e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def get_old_platform_user_id(user_name):
        try:
            url = options.old_platform_userid_ep + user_name
            ret = get_http(url=url).json()
            if ret.get("code") != 0:
                return False, 500
            return True, ret.get("objects")[0].get("id")
        except Exception as e:
            em = "get user id from old platform error. user name: <{0}>. msg: <{1}>".format(user_name, e)
            LOG.exception(em)
            return False, 500

    @staticmethod
    def add_user_info(user_id, user_name, name, company):
        """添加用户信息"""
        user_info = RegisterPhones.query.filter(RegisterPhones.user_id == user_id).first()
        # 找到，更新
        if user_info:
            if name:
                user_info.name = name
            if company:
                user_info.company = company
        # 未找到，添加
        else:
            # 检查验证码
            user_info = RegisterPhones(id=str(uuid.uuid1()),
                                       user_name=user_name,
                                       user_id=user_id,
                                       name=name,
                                       company=company,
                                       )
            db_session.add(user_info)

        db_session.commit()
        return {"code": 0, "result": ""}

    @staticmethod
    def update_user_info(user_id, **kwargs):
        """不能更新手机号，需要调用单独的接口"""
        user_info = RegisterPhones.query.filter(RegisterPhones.user_id == user_id).first()
        if not user_info:
            em = u"未找到记录"
            return {"code": 1, "result": em}
        name = kwargs.get("name", "")
        company = kwargs.get("company", "")
        RegisterPhones.query.filter(RegisterPhones.user_id == user_id).\
            update({RegisterPhones.name: name,
                    RegisterPhones.company: company})

        db_session.commit()
        return {"code": 0, "result": ""}

    @staticmethod
    def update_phone(new_phone, session_id, auth_code, user_id, user_name):
        """用户修改手机号码"""
        session_id = session_id + "_" + new_phone
        # 检查验证码
        ret = SendSmsMsg.check_auth_code(session_id=session_id, auth_code=auth_code)
        if ret.get("code") != 0:
            return ret
        db_obj = RegisterPhones.query.filter(RegisterPhones.user_id == user_id).first()
        if not db_obj:
            # 没有就添加
            add_obj = RegisterPhones(id=str(uuid.uuid1()),
                                     user_id=user_id,
                                     phone=new_phone,
                                     user_name=user_name
                                     )
            db_session.add(add_obj)

        else:
            RegisterPhones.query.filter(RegisterPhones.user_id == user_id).\
                update({RegisterPhones.phone: new_phone,
                        RegisterPhones.user_name: user_name})
        db_session.commit()
        return {"code": 0, "result": ""}

    @staticmethod
    def get_userinfo(user_id, token):
        # 先从本地查找
        db_obj = RegisterPhones.query.filter(RegisterPhones.user_id == user_id).first()
        if db_obj:
            return db_obj
        # 本地没找到，从keystone里找
        user_desc = UserManager.get_user_info(token=token, user_id=user_id)
        if not user_desc[0]:
            em = u"获取用户信息失败"
            return {"code": 1, "result": em}
        if user_desc:
            result = {}
            description = user_desc[1].get("user").get("description")
            user_name = user_desc[1].get("user").get("name")
            if description:
                result = json.loads(user_desc[1].get("user").get("description"))

            result["is_sms_auth"] = 0
            result["user_name"] = user_name

            return result

        return {}
