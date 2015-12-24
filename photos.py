# coding:utf-8
import os
import uuid
import errno

import flask
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage


try:
    from PIL import Image, ImageOps
except ImportError:
    raise RuntimeError('Image module of PIL needs to be installed')

IMAGES = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.bmp', '.webp')


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
        self.thumb_destination = thumb_destination
        self.thumb_base_url = addslash(thumb_base_url)
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
    |MEDIA_THUMBS_FOLDER  | 'media/thumbs'      | 保存缩略图的目录
    |MEDIA_PHOTOS_URL     | '/media/photos/'    | 显示照片的url根路径
    |MEDIA_THUMBS_URL     | '/media/thumbs/'    | 显示缩略图的url根路径


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
        thumb_destination = app.config.get('MEDIA_THUMBS_FOLDER', 'media/thumbs')
        thumb_base_url = app.config.get('MEDIA_THUMBS_URL', '/media/thumbs/')

        self.config = PhotoManagerConfiguration(destination, base_url, thumb_destination, thumb_base_url)

        self.blueprint.add_url_rule(self.config.base_url + '<filename>',
                                    endpoint='export_photo', view_func=self.export_photo)
        self.blueprint.add_url_rule(self.config.thumb_base_url + '<miniature>',
                                    endpoint='export_thumb', view_func=self.export_thumb)
        self.app.register_blueprint(self.blueprint)

        self.app.jinja_env.globals.update(photo_url_for=self.url)
        self.app.jinja_env.globals.update(thumb_url_for=self.thumb_url)

    def export_photo(self, filename):
        path = self.config.destination
        return flask.send_from_directory(path, filename)

    def export_thumb(self, miniature):
        return flask.send_from_directory(self.config.thumb_destination, miniature)

    def resolve_conflict(self, target_folder, basename):
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

    def thumb_url(self, filename, **options):
        miniature = self.make_thumb(filename, override=False, **options)
        if not miniature:
            abort(404)
        return flask.url_for('photo_manager.export_thumb', miniature=miniature)


    def make_thumb(self, filename, miniature=None, override=False, size='96x96',
                   width=None, height=None, crop=None, bg=None, quality=85):
        """
        生成缩略图

        :param filename: 图像源文件名
        :param miniature: 缩略图文件名，如果为None则按照参数自动生成
        :param override: 是否覆盖同名文件
        :param size: 缩略图尺寸，当width和height参数之一为None时生效
        :param width: 缩略图宽度
        :param height: 缩略图高度
        :param crop: 是否需要裁剪
        :param bg: 背景颜色
        :param quality: 图像压缩质量
        """
        if not width or not height:
            width, height = [int(x) for x in size.split('x')]

        name, fm = os.path.splitext(filename)

        if not miniature:
            miniature = self._get_name(name, fm, size, crop, bg, quality)

        thumb_filename = flask.safe_join(self.config.thumb_destination, miniature)
        self._ensure_path(thumb_filename)

        if not os.path.exists(thumb_filename) or override:
            original_filename = flask.safe_join(self.config.destination, filename)
            if not os.path.exists(original_filename):
                return None

            thumb_size = (width, height)

            try:
                image = Image.open(original_filename)
            except IOError:
                return None

            if crop == 'fit':
                img = ImageOps.fit(image, thumb_size, Image.ANTIALIAS)
            else:
                img = image.copy()
                img.thumbnail((width, height), Image.ANTIALIAS)

            if bg:
                img = self._bg_square(img, bg)

            img.save(thumb_filename, image.format, quality=quality)

        return miniature


    def save(self, storage, name=None, random_name=True, process=None, **options):
        """
        保存文件到设定路径

        :param storage: 需要保存的文件，应该是一个FileStorage对象
        :param name: 如果为None，自动生成文件名。
                     可以包含目录路径, 如``photos.save(file, name="someguy/photo_123.")``
        :param random_name: 是否生成随机文件名，仅挡name=None时有效
        :param process: 对图片的预处理，可以选择```'resize'```或None
        :param width: 对图片的预处理参数，限制图片宽度
        :param height: 对图片的预处理参数，限制图片高度
        """
        if not isinstance(storage, FileStorage):
            raise TypeError("storage must be a werkzeug.FileStorage")

        basename, ext = os.path.splitext(storage.filename)
        ext = ext.lower()

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

        if process == 'resize':
            width = options.pop('width', 1024)
            height = options.pop('height', 1024)
            image = Image.open(storage)
            image.thumbnail((width, height), Image.ANTIALIAS)
            image.save(target, image.format)
        else:
            storage.save(target)

        return basename

    @staticmethod
    def _get_name(name, fm, *args):
        for v in args:
            if v:
                name += '_%s' % v
        name += fm

        return name

    @staticmethod
    def _ensure_path(full_path):
        directory = os.path.dirname(full_path)

        try:
            if not os.path.exists(full_path):
                os.makedirs(directory)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    @staticmethod
    def _bg_square(img, color=0xff):
        size = (max(img.size),) * 2
        layer = Image.new('L', size, color)
        layer.paste(img, tuple(map(lambda x: (x[0] - x[1]) / 2, zip(size, img.size))))
        return layer