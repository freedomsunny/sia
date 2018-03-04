# encoding=utf-8
# !/usr/bin/env python
import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, DateTime, Text, Float, DECIMAL, \
    VARCHAR
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, object_mapper, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import uuid

from ops_sia.options import get_options
from ops_sia import utils

options = get_options()
# pool_recycle should less than MySQL wait_timeout
engine = create_engine(options.sql_connection, convert_unicode=True, poolclass=NullPool)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def get_session():
    return db_session


def generate_uuid():
    return str(uuid.uuid1())


def model_query(*args, **kwargs):
    pass


def init_db():
    Base.metadata.create_all(bind=engine)


class OpsBase(object):
    """Base class for Ops Models."""
    __table_args__ = {'mysql_engine': 'InnoDB'}
    __table_initialized__ = False
    created_at = Column(DateTime, default=utils.utcnow)
    updated_at = Column(DateTime, onupdate=utils.utcnow)
    deleted_at = Column(DateTime)
    deleted = Column(Boolean, default=False)
    metadata = None

    def save(self, session=None):
        """Save this object."""
        if not session:
            session = db_session
        session.add(self)
        session.flush()
        session.commit()

    def delete(self, session=None):
        """Delete this object."""
        self.deleted = True
        self.deleted_at = utils.utcnow()
        self.save(session=session)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __iter__(self):
        self._i = iter(object_mapper(self).columns)
        return self

    def next(self):
        n = self._i.next().name
        return n, getattr(self, n)

    def update(self, values):
        """Make the model object behave like a dict"""
        for k, v in values.iteritems():
            setattr(self, k, v)

    def iteritems(self):
        """Make the model object behave like a dict.

        Includes attributes from joins."""
        local = dict(self)
        joined = dict([(k, v) for k, v in self.__dict__.iteritems()
                       if not k[0] == '_'])
        local.update(joined)
        return local.iteritems()


class RegisterPhones(Base, OpsBase):
    """count api caled"""
    __tablename__ = 'register_phone'
    id = Column(String(64), primary_key=True)
    user_name = Column(String(128))
    user_id = Column(String(128))
    e_mail = Column(String(128))
    name = Column(String(36))
    company = Column(String(36))
    phone = Column(String(36))
    # is real name auth
    is_real_auth = Column(Boolean, default=False)
    is_sms_auth = Column(Boolean, default=False)

    def __init__(self, id, user_name=None, user_id=None, phone=None, is_real_auth=False, e_mail=None, name=None,
                 company=None, is_sms_auth=None):
        self.id = id
        self.user_name = user_name
        self.user_id = user_id
        self.phone = phone
        self.e_mail = e_mail
        self.name = name
        self.company = company
        self.is_real_auth = is_real_auth
        self.is_sms_auth = is_sms_auth


class AuthInfo(Base, OpsBase):
    """用于存储用户的实名认证信息"""
    __tablename__ = 'real_name_auth_info'
    id = Column(String(64), primary_key=True, default=generate_uuid)
    user_id = Column(String(256))
    user_name = Column(String(256))
    # 认证名，公司/个人
    auth_name = Column(String(256))
    auth_phone = Column(String(36))
    # 认证类型
    # 个人    1
    # 企业    2
    auth_type = Column(Integer)
    # 认证金额（腾讯随机打0.01~0.99元到银行账号用于确认）
    auth_money = Column(DECIMAL(50, 2), default=0)
    # 认证id  营业执照号/身份证号
    # company_id = Column(String(256))
    auth_id = Column(String(256))
    # 开户银行
    bank_name = Column(String(256))
    # 银行所在地
    bank_address = Column(String(256))
    # 银行所在地
    bank_area = Column(String(256))
    # 支行名
    bank_branch_name = Column(String(256))
    # 银行账号
    bank_id = Column(String(256))
    # 状态
    # 0 未通过
    # 1 通过
    status = Column(Boolean, default=False)


class Images(Base, OpsBase):
    """图片"""
    __tablename__ = 'images'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=True)
    url = Column(String(128), nullable=True)
    type = Column(String(128), nullable=True)
    size = Column(Integer, nullable=True)
    auth_info_id = Column(String(36))
    image_type = Column(String(36))


class APICount(Base, OpsBase):
    """count api caled"""
    __tablename__ = 'api_count'
    id = Column(Integer, primary_key=True)
    name = Column(String(128))
    url = Column(String(1024))
    count = Column(Integer)


def register_models(tables):
    """Register Models and create metadata.
    tablese = (Costlog,)
    """
    models = tables
    for model in models:
        model.metadata.create_all(engine)


register_models((APICount, RegisterPhones, AuthInfo, Images))
