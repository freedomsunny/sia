#!encoding=utf-8
from sqlalchemy import and_
import re
import json
import uuid

from threading import Thread

from ops_sia.utils import get_token, post_http, get_http, put_http
from ops_sia.options import get_options
import ops_sia.log as logging
from ops_sia.db.models import db_session, AuthInfo, RegisterPhones, Images
from ops_sia.plugins.sms_auth import SendSmsMsg
from ops_sia.plugins.upload_file import get_pictuer_url


LOG = logging.getLogger(__name__)

users_tencent_opts = [
    {"name": "ccccc",
     "default": "",
     "help": '',
     "type": str},
]

options = get_options(users_tencent_opts)


class RealNameAuth(object):
    @staticmethod
    def add_auth_info(data):
        # 不能重复申请
        result = AuthInfo.query.filter(and_(AuthInfo.deleted == False,
                                            AuthInfo.user_id == data.user_id,
                                            )).first()
        if result:
            return {"code": 1, "message": u"请勿重复提交申请"}
        # 检查手机是否被注册
        result_old = RegisterPhones.query.filter(and_(RegisterPhones.phone == data.auth_phone,
                                                      RegisterPhones.is_real_auth == True)).first()
        result_new = AuthInfo.query.filter(and_(AuthInfo.deleted == False,
                                                AuthInfo.auth_phone == data.auth_phone,
                                                AuthInfo.status == True)).first()
        if result_old or result_new:
            return {"code": 1, "message": u"手机已被注册"}
        # 检查验证码
        result = SendSmsMsg.check_auth_code(data.session_id, data.auth_code)
        if result.get("code") != 0:
            return result
        db_obj = AuthInfo()
        db_obj.user_id = data.user_id
        db_obj.user_name = data.user_name
        db_obj.auth_name = data.auth_name
        db_obj.auth_phone = data.auth_phone
        db_obj.auth_type = data.auth_type
        db_obj.auth_id = data.auth_id
        db_obj.bank_name = data.bank_name
        db_obj.bank_address = data.bank_address
        db_obj.bank_area = data.bank_area
        db_obj.bank_branch_name = data.bank_branch_name
        db_obj.bank_id = data.bank_id
        db_obj.save()

        # # post 数据到腾迅
        # # 企业用户
        # if db_obj.auth_type == "enterprise":
        #     post_data = {"type": db_obj.auth_type,
        #                  "accountName": db_obj.auth_name,
        #                  "accountId": db_obj.bank_id,
        #                  "bankName": db_obj.bank_name,
        #                  "bankId": db_obj.bank_id,
        #                  "provinceName": "enterprise",
        #                  "provinceId": "enterprise",
        #                  "cityName": "enterprise",
        #                  "cityId": "enterprise",
        #                  }
        #     headers = {"X-Auth-Token": data.token,
        #                "Content-Type": "application/json",
        #                "TxToken": data.TxToken,
        #                "TxKey": data.TxKey,
        #                "TxId": data.TxId
        #                }
        #     url = "{0}/cloud/tencent/auth".format(options.api_gateway_url)
        #     tx_ret = post_http(url=url, data=json.dumps(post_data), headers=headers)
        #     print "tx ret post real auth==========", tx_ret.json()
        #     # 从腾迅云读取实名认证状态
        #     url = "{0}/cloud/tencent/auth".format(options.api_gateway_url)
        #     tx_ret = get_http(url=url, headers=headers)
        #     print "tx ret get real auth==========", tx_ret.json()

        LOG.debug("add real name auth <{0}> to db".format(db_obj.id))

        return db_obj

    @staticmethod
    def update_auth_info(id, data):
        # 只能更新腾讯打款过来的金额
        result = AuthInfo.query.filter(and_(AuthInfo.id == id,
                                            AuthInfo.deleted == False)).first()
        if not result:
            em = "can not found id: <{0}> from authinfo".format(id)
            LOG.exception(em)
            return {}
        result.auth_money = data.get("auth_money")
        db_session.commit()
        result.image_list = []
        images = Images.query.filter(and_(Images.deleted == False,
                                          Images.auth_info_id == result.id)).all()

        for image in images:
            result.image_list.append({"id": image.id, "url": get_pictuer_url(image.name)})

        return result

    @staticmethod
    def delete_auth_info(id):
        result = AuthInfo.query.filter(and_(AuthInfo.id == id,
                                            AuthInfo.deleted == False)).first()
        # 认证已通过，不能删除
        if result.status:
            return False
        result.deleted = True

        db_session.commit()
        return result

    @staticmethod
    def get_auth_info(user_id, id=None, auth_type=None):
        result = []
        auth_infos = AuthInfo.query.filter(and_(AuthInfo.user_id == user_id,
                                            AuthInfo.deleted == False,
                                            )).all()
        if id:
            auth_infos = AuthInfo.query.filter(and_(AuthInfo.user_id == user_id,
                                                AuthInfo.deleted == False,
                                                AuthInfo.id == id
                                                )).all()
        elif auth_type:
            auth_infos = AuthInfo.query.filter(and_(AuthInfo.user_id == user_id,
                                                AuthInfo.deleted == False,
                                                AuthInfo.auth_type == auth_type
                                                )).all()
        # if not auth_infos:
        #     return {}
        for auth_info in auth_infos:
            # 得到图片
            images = Images.query.filter(and_(Images.deleted == False,
                                              Images.auth_info_id == auth_info.id)).all()
            auth_info.image_list = []
            for image in images:
                auth_info.image_list.append({"id": image.id, "url": get_pictuer_url(image.name)})
            result.append(auth_info)
        # 老的实名认证获取信息
        admin_token = get_token()
        if admin_token:
            url = options.worder_ep + u"/work_orders/?title=实名认证&user_id={0}&status=1&is_admin=True".format(user_id)
            headers = {"X-Auth-Token": admin_token.strip()}
            ret = get_http(url=url, headers=headers).json()
            if ret.get("code") == 0 and ret.get("data"):
                auth_type = ret.get("data")[0].get("app_service_id")
                # 企业申请
                if auth_type == "98ff8097-f1f0-11e7-815d-00b367deaa81":
                    auth_type = 2
                # 个人申请
                if auth_type == "98af11e3-f1f0-11e7-a7e8-004b6ca3331e":
                    auth_type = 1
                data_obj = AuthInfo()
                data_obj.image_list = ret.get("data")[0].get("image_list")
                data_obj.auth_type = auth_type
                data_obj.status = ret.get("data")[0].get("status")
                data_obj.created_at = ret.get("data")[0].get("created_at")
                data_obj.user_id = ret.get("data")[0].get("user_id")
                data_obj.user_name = ret.get("data")[0].get("user_name")
                data_obj.auth_phone = ret.get("data")[0].get("auth_phone")
                data_obj.auth_id = ret.get("data")[0].get("auth_id")
                result.append(data_obj)

        return result


class AuthInfoParser(object):
    def __init__(self, data, user_context):
        # 认证名，公司名称/个人姓名
        self.auth_name = data.get_argument("auth_name", "")
        self.auth_phone = data.get_argument("auth_phone", "")
        # 手机验证码
        self.auth_code = data.get_argument("auth_code", "")
        # session id
        self.session_id = data.get_argument("session_id", "") + "_" + self.auth_phone
        # 认证类型
        # 个人    1
        # 企业    2
        # self.auth_type = "enterprise" if int(data.get_argument("auth_type", "")) == 2 else "individual"
        self.auth_type = int(data.get_argument("auth_type", ""))
        # 认证id  营业执照号/身份证号
        self.auth_id = data.get_argument("auth_id", "")
        # 开户银行
        self.bank_name = data.get_argument("bank_name", "")
        # 银行所在地
        self.bank_address = data.get_argument("bank_address", "")
        # 银行所在区域
        self.bank_area = data.get_argument("bank_area", "")
        # 支行名
        self.bank_branch_name = data.get_argument("bank_branch_name", "")
        # 银行账号
        self.bank_id = data.get_argument("bank_id", "")
        # 用户相关
        self.token = user_context.get("token")
        self.user_name = user_context.get("user").get("user").get("name")
        self.user_id = user_context.get("user_id")
        self.TxToken = user_context.get("TxToken")
        self.TxKey = user_context.get("TxKey")
        self.TxId = user_context.get("TxId")


class AuthInfoCMDBParser(object):
    """解析来自cmdb的数据"""
    def __init__(self, data):
        # 状态
        # 0 ： 未实名
        # 1 ： 打款中（提交银行卡信息后即为此状态）
        # 2 ： 未实名，银行卡信息不正确
        # 3: 用户输入打款金额并且正确后, 完成实名，变为状态3
        self.status = data.get("property").get("status")
        self.auth_phone = data.get("property").get("auth_phone")
        self.id = data.get("uuid")

