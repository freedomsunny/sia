# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import json
import tornado.web

from ops_sia.plugins.JsonResponses import BaseHander
from ops_sia.api.auth import auth as Auth
from ops_sia.plugins.sms_auth import  SendSmsMsg, send_msg
from ops_sia.options import get_options
import ops_sia.log as logging
from ops_sia.db.models import RegisterPhones, db_session
from ops_sia.plugins.code_auth import CodeAuth

options = get_options()

LOG = logging.getLogger(__name__)

url_map = {
    r"/sms_auth_code": "SmsAuthCode",
    r"/checkphone": "CheckPhoneExist",
    r"/checkauthcode": "CheckAuthCode",
    r"/sendrealauthmsg": "SendRealAuthSMS",

}


class SmsAuthCode(BaseHander, Auth.Base):
    def get(self):
        phone = self.get_argument("phone").strip()
        image_auth_code = self.get_argument("image_auth_code").strip()
        session_id = self.get_argument("session_id").strip()
        # session_id_sms =  session_id + phone
        session_id_sms = str(session_id).strip() + "_" + str(phone).strip()
        # 检查用户发送短信间隔
        ret = SendSmsMsg.check_phone(session_id + "_")
        if ret:
            self.write({"code": 1,
                        "result": "时间间隔小于{0}秒，请稍后再试".format(options.auth_code_interval)})
            return
        # 检查图片验证码。2018/03/02添加，用于防止刷短信(hyj)
        image_auth_obj = CodeAuth()
        result = image_auth_obj.check_auth_code(session_id= "{0}_image_auth_code".format(session_id),
                                                auth_code=image_auth_code)
        if not result:
            self.write({"code": 1,
                        "result": "验证码错误"})
            return
        # 生成随机验证码
        sms_auth_code = SendSmsMsg.gen_sms_auth_code()
        # 发送短信
        result = send_msg(phone=phone, msg=options.sms_msg_template.format(sms_auth_code))
        if result:
            self.write({"code": 0,
                        "result": ""})
            # 保存信息到redis中
            SendSmsMsg.save_phone_auth_code(session_id_sms, sms_auth_code)
            return
        self.set_status(500)
        self.write({"code": 1,
                    "result": "发送失败"})


class CheckPhoneExist(BaseHander, Auth.Base):
    def get(self):
        phone = self.get_argument("phone").strip()
        # 检查手机号码是否被注册
        phone_check = RegisterPhones.query.filter(RegisterPhones.phone == phone).first()
        if phone_check:
            self.set_status(409)
            self.write({"code": 1, "result": "手机已被注册"})
            return
        self.write({"code": 0, "result": ""})


class CheckAuthCode(BaseHander, Auth.Base):
    def get(self):
        """检查验证码是否正确"""
        session_id = self.get_argument("session_id").strip()
        auth_code = self.get_argument("auth_code").strip()
        if not auth_code or not session_id:
            self.write({"code": 1, "result": "无效参数"})
        ret = SendSmsMsg.check_auth_code(session_id, auth_code)
        self.write(ret)


class SendRealAuthSMS(BaseHander, Auth.BaseAuth):
    """用于实名认证通知用户"""
    def post(self):
        """
        1  通过
        0  不通过
        """
        data = json.loads(self.request.body)
        msg_type = int(str(data.get("msg_type", "")).strip())
        phone = str(data.get("phone", "")).strip()
        if not msg_type or not phone:
            self.write({"code": 1,
                        "result": "参数错误"})
        if msg_type == 1:
            msg = options.sms_real_name_auth_template.format("已", ".")
        elif msg_type == 0:
            msg = options.sms_real_name_auth_template.format("未", ",请重新提交申请")
        else:
            em = "undefine type"
            LOG.exception(em)
            return {}
        # 发送短信
        result = send_msg(phone=phone, msg=msg)
        if result:
            self.write({"code": 0,
                        "result": ""})
        self.write({"code": 1,
                    "result": "发送信息失败"})
