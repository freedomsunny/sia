#!encoding=utf-8
from sqlalchemy import and_

from ops_sia.options import get_options
from ops_sia.utils import get_http, post_http, put_http, patch_http, get_token, parse_url
import ops_sia.log as logging
import json

LOG = logging.getLogger(__name__)

options = get_options()


class CMDBOpreate(object):
    def __init__(self):
        pass

    @staticmethod
    def real_name_auth(user_id):
        """从cmdb处获取实名认证信息"""
        admin_token = get_token()
        if not admin_token:
            em = "get admin token error"
            LOG.exception(em)
            return False
        headers = {'X-Auth-Token': admin_token}
        # 生成请求url
        url = parse_url(options.cmdb_host,
                        path="/work_orders/",
                        port=options.cmdb_port,
                        user_id=user_id,
                        title="实名认证",
                        is_admin=True)
        ret = get_http(url=url, headers=headers)
        if ret.json().get("code") != 0:
            em = "get real name auth from cmdb error"
            LOG.exception(em)
            return False
        data = ret.json()
        if data.get("data"):
            return ret.json().get("data")[0]
        return False

    @staticmethod
    def get_cmdb_info_by_uuid(uuid):
        """根据uuid从cmdb获取数据"""
        try:
            admin_token = get_token()
            url = "{0}/assets/{1}".format(options.cmdb_ep, uuid)
            headers = {'X-Auth-Token': admin_token.strip()}
            ret = get_http(url=url, headers=headers)
            if ret.status_code != 200:
                em = "get data from cmdb error...."
                LOG.exception(em)
                return {}
            return ret.json()
        except Exception as e:
            em = "get data from cmdb error. msg: <{0}>".format(e)
            LOG.exception(em)
            return {}

    @staticmethod
    def syncdata2cmdb(resouce_type, id):
        url = options.sync_api + "/sync/" + id
        data = {"resource_type": resouce_type}
        result = put_http(url=url, data=json.dumps(data))
        if result.status_code >= 400:
            em = "sync data to cmdb error. resource type: <{0}>  resource id: <{1}>".format(resouce_type,
                                                                                            id)
            LOG.exception(em)
        return False