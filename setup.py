#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="sia",
    version='1.0',
    description="sia lib",
    author="huangyingjun",
    install_requires=[
        "SQLAlchemy",
        "mysql",
        "mysql-connector-python-rf",
        "MySQL-python",
        "tornado",
        "eventlet",
        "redis",
        "requests",
        "netaddr",
    ],

    scripts=[
        "bin/sia_api",
        "bin/ops_admin.py",
    ],

    packages=find_packages(),
    data_files=[
        ('/etc/ops_sia', ['etc/ops_sia.conf']),
        ('/var/log/ops_sia', []),
    ],
)
