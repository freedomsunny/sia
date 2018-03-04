#!encoding=utf-8
from sqlalchemy import and_
import json

from ops_sia.options import get_options
from ops_sia.utils import get_http, post_http, put_http, patch_http, get_token, parse_url
import ops_sia.log as logging
LOG = logging.getLogger(__name__)


options = get_options()


####################################
#
# 微信通知
#
####################################


class WechatNotify(object):
    @staticmethod
    def send_msg2user(user_id, operator, title, content, token):
        """
        :param user_id: 接收消息的用户
        :param operator: 发起消息的用户
        :param title: 标题
        :param content: 内容
        :param token: 认证令牌
        :return:
        """
        # 微信通知
        url = options.wechat_ep + "worder_reply_msg"
        data = {"user_id": user_id,
                "operator": operator,
                "title": title,
                "content": content
                }
        headers = {"Content-Type": "application/json",
                   "X-Auth-Token": token}
        result = post_http(url=url, headers=headers, data=json.dumps(data))
        if result.json().get("code") != 0:
            em = "send notify from <{0}> to wecaht <{1}> error.".format(operator, user_id)
            LOG.exception(em)


