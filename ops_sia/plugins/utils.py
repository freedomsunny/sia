# -*- coding: utf-8 -*-
import re
import random
import time
from urllib import urlencode, unquote

# e_mail about
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib

# import md5 about
try:
    import hashlib

    md5_constructor = hashlib.md5
    md5_hmac = md5_constructor
    sha_constructor = hashlib.sha1
    sha_hmac = sha_constructor
except ImportError:
    import md5

    md5_constructor = md5.new
    md5_hmac = md5
    import sha

    sha_constructor = sha.new
    sha_hmac = sha

from ops_sia.utils import generate_uuid
from ops_sia.options import get_options
import ops_sia.log as logging

from ops_sia import utils

LOG = logging.getLogger(__name__)

plugins_utils_opts = [
    {"name": "from_email",
     "default": 'account_support@xiangcloud.com.cn',
     "help": '',
     "type": str},
    {"name": "from_email_password",
     "default": 'TOrkym13o7F+Zpg/Eu3xb0Uc',
     "help": '',
     "type": str},
    {"name": "smtp_server",
     "default": 'smtp.xiangcloud.com.cn',
     "help": '',
     "type": str},
    {"name": "md5_key",
     "default": 'd41d8cd98f0b204e9800998ecf8427e',
     "help": '',
     "type": str},
    {"name": "password_length",
     "default": 8,
     "help": '',
     "type": int},
    {"name": "pwd_types",
     "default": 2,
     "help": '',
     "type": int},
]

options = get_options(plugins_utils_opts)


def check_user_name(user_name):
    """user name must be e_mail"""
    pat = re.compile(r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+){0,4}$')
    ret = re.match(pat, user_name)
    if not ret:
        em = "user name :<{0}> is not valid. user name must be e_mail".format(user_name)
        LOG.exception(em)
        return False
    return True


class CheckPassword(object):
    """by default password must be ge 8bit and >= 2 types"""
    def __init__(self, password):
        self.password = password
        self.password_types = 0
        # init
        self.check_contain_upper()
        self.check_contain_num()
        self.check_contain_lower()
        self.check_symbol()
        # result
        self.result = self.check_password()

    # 长度
    def check_len(self):
        return len(self.password) >= options.password_length

    # 大写字母
    def check_contain_upper(self):
        pattern = re.compile('[A-Z]+')
        match = pattern.findall(self.password)
        if match:
            self.password_types += 1

    # 数字
    def check_contain_num(self):
        pattern = re.compile('[0-9]+')
        match = pattern.findall(self.password)
        if match:
            self.password_types += 1

    # 小写字母
    def check_contain_lower(self):
        pattern = re.compile('[a-z]+')
        match = pattern.findall(self.password)
        if match:
            self.password_types += 1

    # 特殊字符
    def check_symbol(self):
        pattern = re.compile('([^a-z0-9A-Z])+')
        match = pattern.findall(self.password)
        if match:
            self.password_types += 1

    def check_password(self):
        if not self.check_len():
            em = "password can not less than 8 bit."
            LOG.exception(em)
            return False
        if self.password_types < options.pwd_types:
            em = "password types can not less than 2 kinds"
            LOG.exception(em)
            return False
        return True


def check_password(password):
    """password must ge 8 bit"""
    # pat = re.compile(r'^(?=.*[A-Za-z])(?=.*[0-9])\w{8,}$')
    # ret = re.match(pat, password)
    # if not ret:
    #     em = "password %s is not strong." % password
    #     LOG.exception(em)
    #     return False
    o = CheckPassword(password)
    return o.result


def generate_random_no():
    """generate a random number"""
    trade_no = time.strftime('%Y%m%d%H%m%S', time.localtime(time.time()))
    rand_num = str(random.random())[2:15]
    return trade_no + rand_num


def send_email(receiver_email, content, subject, port=25, from_email=options.from_email, from_email_password=options.from_email_password):
    """send mail to dst_email address"""
    try:
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = _format_addr(from_email)
        msg['To'] = _format_addr(u'<%s>' % receiver_email)
        msg['Subject'] = Header(subject, 'utf-8').encode()

        server = smtplib.SMTP(options.smtp_server, port)
        server.set_debuglevel(1)
        server.login(from_email, from_email_password)
        server.sendmail(from_email, [receiver_email], msg.as_string())
        server.quit()
        return True, 200
    except Exception as e:
        em = "send mail to <{0}> error. msg: {1}".format(receiver_email, e)
        LOG.exception(em)
        return False, 500


def verify_random_no_by_md5(prestr):
    ret = md5_constructor(prestr + options.md5_key).hexdigest()
    return ret


def generate_url(url):
    rand_str = generate_random_no()
    full_url = url + "?&id={0}".format(rand_str)
    return rand_str, full_url


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(),
                       addr.encode('utf-8') if isinstance(addr, unicode) else addr))

def check_phone():
    """手机号是否合法"""
    pass
