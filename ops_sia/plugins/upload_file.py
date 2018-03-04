import os
import time

from tornado.httpclient import HTTPError
from tornado.options import options
from tornado.web import StaticFileHandler

from ops_sia.db.models import Images
from ops_sia.exception import *


def get_upload_path():
    upload_path = options.file_path

    if upload_path:
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        return upload_path


def make_id():
    return str(int(round(time.time() * 1000)))


def check_picture(file, max_size=None, type=None):
    if not max_size:
        max_size = 10*1024*1024
    if not type:
        type = ['jpg', 'jpeg', 'png']
    if not file:
        raise NotExist(message=file.name)
    else:
        filesize = len(file.body)
        fileformat = file.content_type.replace('image/', '')
        if filesize > max_size:
            return

        if fileformat.lower() not in type:
            raise FileFormatException(file_format=fileformat)
        file.size = filesize
        file.type = fileformat
        return file


def upload_picture(file):
    upload_path = get_upload_path()
    filename = '%s.%s' % (make_id(), file.content_type.replace('image/', ''))
    filepath = os.path.join(upload_path, filename)
    with open(filepath, 'wb') as up:
        up.write(file.body)

    return filename


def validate_absolute_path(absolute_path):
    if not os.path.exists(absolute_path):
        raise HTTPError(404)
    if not os.path.isfile(absolute_path):
        raise HTTPError(403, "this file is not exist")
    return absolute_path


def get_upload_content(filename):

    upload_path = get_upload_path()

    filepath = os.path.join(upload_path, filename)
    filepath = validate_absolute_path(filepath)

    return StaticFileHandler.get_content(filepath)


def send_file(file, **kwargs):

    file = check_picture(file)
    filename = upload_picture(file)
    image_obj = Images()
    data = {'name': filename, 'size': file.size, 'type': file.content_type}
    if kwargs.get('auth_info_id'):
        data.update(auth_info_id=kwargs.get('auth_info_id'))
    image_obj.update(data)
    image_obj.save()
    return image_obj


def get_pictuer_url(file_name):
    return 'http://{0}:{1}/picture/{2}'.format(options.floting_ip, options.api_port, file_name.strip())

