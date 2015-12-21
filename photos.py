# coding:utf-8
import os
import uuid
import flask
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

IMAGES = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.bmp')


def addslash(url):
    if not url:
        return None
    if url.endswith('/'):
        return url
    return url + '/'


class UploadNotAllowed(Exception):
    """
    This exception is raised if the upload was not allowed. You should catch
    it in your view code and display an appropriate message to the user.
    """


class PhotoManagerConfiguration(object):
    """
    保存PhotoManager的配置

    :param destination: 保存照片的目录
    :param base_url: 显示照片的url根路径
    :param thumb_destination: 保存缩略图的目录
    :param thumb_base_url: 显示缩略图的url根路径
    :param allow: 允许的文件扩展名
    """

    def __init__(self, destination, base_url, thumb_destination=None, thumb_base_url=None, allow=IMAGES):
        self.destination = destination
        self.base_url = addslash(base_url)
        self.thumb_destination = thumb_destination or self.destination
        self.thumb_base_url = addslash(thumb_base_url) or self.base_url
        self.allow = allow

    @property
    def tuple(self):
        return (self.destination, self.base_url,
                self.thumb_destination, self.thumb_base_url,
                self.allow)

    def __eq__(self, other):
        return self.tuple == other.tuple


class PhotoManager(object):
    """
    处理产品照片的上传，保存，生成缩略图。

    设置项目
    |Key                  | Default             | Description
    |---------------------|---------------------|-------------------
    |MEDIA_PHOTOS_FOLDER  | 'media/photos'      | 保存照片的目录
    |MEDIA_THUMBS_FOLDER  | 'media/photos'      | 保存缩略图的目录
    |MEDIA_PHOTOS_URL     | '/media/photos/'    | 显示照片的url根路径
    |MEDIA_THUMBS_URL     | '/media/photos/'    | 显示缩略图的url根路径


    主要方法
    save(file):保存文件
    url(filename):返回文件url
    thumb(filename):返回缩略图url，自动生成并缓存缩略图
    """

    def __init__(self, app=None, ):
        self.config = None
        self.blueprint = flask.Blueprint('photo_manager', __name__)
        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def init_app(self, app):
        self.app = app

        destination = app.config.get('MEDIA_PHOTOS_FOLDER', 'media/photos')
        base_url = app.config.get('MEDIA_PHOTOS_URL', '/media/photos/')
        thumb_destination = app.config.get('MEDIA_THUMBS_FOLDER')
        thumb_base_url = app.config.get('MEDIA_THUMBS_URL')

        self.config = PhotoManagerConfiguration(destination, base_url, thumb_destination, thumb_base_url)
        self.set_routes()
        self.app.register_blueprint(self.blueprint)

    def export_photo(self, filename):
        path = self.config.destination
        return flask.send_from_directory(path, filename)

    def set_routes(self):
        full_url = self.config.base_url + '<filename>'
        self.blueprint.add_url_rule(full_url, endpoint='export_photo', view_func=self.export_photo)

    @staticmethod
    def resolve_conflict(target_folder, basename):
        """
        If a file with the selected name already exists in the target folder,
        this method is called to resolve the conflict. It should return a new
        basename for the file.

        :param target_folder: The absolute path to the target.
        :param basename: The file's original basename.
        """
        name, ext = os.path.splitext(basename)
        count = 0
        while True:
            count += 1
            newname = '%s_%d%s' % (name, count, ext)
            if not os.path.exists(os.path.join(target_folder, newname)):
                return newname

    @staticmethod
    def url(filename):
        """
        :param filename: The filename to return the URL for.
        """
        return flask.url_for('photo_manager.export_photo', filename=filename)

    def save(self, storage, name=None, random_name=True):
        """
        保存文件到设定路径

        :param storage: 需要保存的文件，应该是一个FileStorage对象
        :param name: 如果为None，自动生成文件名。
                     可以包含目录路径, 如``photos.save(file, name="someguy/photo_123.")``
        :param random_name: 是否生成随机文件名，仅挡name=None时有效
        """
        if not isinstance(storage, FileStorage):
            raise TypeError("storage must be a werkzeug.FileStorage")

        basename, ext = os.path.splitext(storage.filename)

        if not (ext in self.config.allow):
            raise UploadNotAllowed()

        if name:
            basename = name
        elif random_name:
            basename = uuid.uuid4().hex + ext
        else:
            basename = basename + ext
        basename = secure_filename(basename)

        target_folder = self.config.destination
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        if os.path.exists(os.path.join(target_folder, basename)):
            basename = self.resolve_conflict(target_folder, basename)

        target = os.path.join(target_folder, basename)
        storage.save(target)
        return basename