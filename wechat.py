# coding: utf-8
"""
WeChat OAuth2 extension for Flask
"""
from functools import wraps
import time
import random
import string
import hashlib

import flask
from flask import current_app, url_for
from flask.signals import Namespace

try:
    from urllib import quote
    from urllib import urlencode
    from urlparse import urljoin
except ImportError:
    from urllib.parse import quote
    from urllib.parse import urljoin
    from urllib.parse import urlencode

try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen

try:
    import simplejson as json
except ImportError:
    import json

_signals = Namespace()
wx_userinfo_fetched = _signals.signal('wx-userinfo-fetched')

blueprint = flask.Blueprint('wx_auth', __name__)


@blueprint.route('/authorize')
def authorize():
    auth_url = WXOAuth2.create_authorize_url(redirect_uri=url_for('.callback', _external=True))
    return flask.redirect(auth_url)


@blueprint.route('/callback')
def callback():
    code = flask.request.args.get('code', None)
    if not code:
        return flask.redirect(url_for(current_app.config['WX_OAUTH2_REFUSED_ROUTE']))
    validate_url = WXOAuth2.create_validate_url(code)
    validate_data = json.loads(urlopen(validate_url).read().strip().decode('utf8', 'ignore'))
    if u'openid' not in validate_data or u'access_token' not in validate_data:
        raise Exception('No response data from weixin access token api')
    wx_openid_session_key = current_app.config['WX_OPENID_SESSION_KEY']
    wx_oauth2_token_session_key = current_app.config['WX_OAUTH2_TOKEN_SESSION_KEY']
    openid = validate_data[u'openid']
    access_token = validate_data[u'access_token']
    flask.session[wx_openid_session_key] = openid
    flask.session[wx_oauth2_token_session_key] = access_token
    userinfo_url = WXOAuth2.create_userinfo_url(token=access_token, openid=openid)
    userinfo_resp = urlopen(userinfo_url).read().strip().decode('utf8', 'ignore')
    userinfo_data = json.loads(userinfo_resp)
    wx_oauth2_userinfo_session_key = current_app.config['WX_OAUTH2_USERINFO_SESSION_KEY']
    flask.session[wx_oauth2_userinfo_session_key] = userinfo_data

    wx_userinfo_fetched.send(current_app._get_current_object(), userinfo=userinfo_data)

    next_url = flask.session.get(current_app.config['WX_OAUTH2_NEXT_SESSION_KEY'],
                                 current_app.config['WX_OAUTH2_AFTER_ROUTE'])
    return flask.redirect(next_url)


@blueprint.route('/no_auth')
def no_auth():
    return u'您没有向我们授权获取个人信息'


@blueprint.route('/after')
def after():
    return u'感谢您的支持。'


def auth_required(function):
    @wraps(function)
    def wrap(*args, **kwargs):
        wx_openid_session_key = current_app.config['WX_OPENID_SESSION_KEY']
        wx_oauth2_next_session_key = current_app.config['WX_OAUTH2_NEXT_SESSION_KEY']
        if wx_openid_session_key not in flask.session:
            flask.session[wx_oauth2_next_session_key] = flask.request.path
            return flask.redirect(url_for('wx_auth.authorize'))
        else:
            return function(*args, **kwargs)

    return wrap


class WXOAuth2(object):
    """
    WeChat OAuth2 client
    Required Configs:

    |Key             |
    |----------------|
    |WX_APP_ID       |
    |WX_APP_SECRET   |

    Optional Configs:

    |Key                              | Default                                               |
    |---------------------------------|-------------------------------------------------------|
    |WX_OPENID_SESSION_KEY            | _WX_OPENID                                            |
    |WX_OAUTH2_TOKEN_SESSION_KEY      | _WX_OAUTH2_TOKEN                                      |
    |WX_OAUTH2_USERINFO_SESSION_KEY   | _WX_OAUTH2_USERINFO                                   |
    |WX_AUTHORIZE_URL_BASE            | 'https://open.weixin.qq.com/connect/oauth2/authorize' |
    |WX_ACCESS_TOKEN_URL_BASE         | 'https://api.weixin.qq.com/sns/oauth2/access_token'   |
    |WX_USERINFO_URL_BASE             | 'https://api.weixin.qq.com/sns/userinfo'              |
    |WX_OAUTH2_NEXT_SESSION_KEY       | 'WX_OAUTH2_NEXT'                                      |
    |WX_OAUTH2_REFUSED_ROUTE          | '.no_auth'                                            |
    |WX_OAUTH2_AFTER_ROUTE            | '.after'                                            |
    """

    def __init__(self, app=None, url_prefix=None):
        self._app = app
        if app is not None:
            self.init_app(app, url_prefix)

    def init_app(self, app, url_prefix=None):
        self._app = app
        # Configuration defaults
        app.config.setdefault('WX_OPENID_SESSION_KEY', '_WX_OPENID')
        app.config.setdefault('WX_OAUTH2_TOKEN_SESSION_KEY', '_WX_OAUTH2_TOKEN')
        app.config.setdefault('WX_OAUTH2_USERINFO_SESSION_KEY', '_WX_OAUTH2_USERINFO')
        app.config.setdefault('WX_AUTHORIZE_URL_BASE', 'https://open.weixin.qq.com/connect/oauth2/authorize')
        app.config.setdefault('WX_ACCESS_TOKEN_URL_BASE', 'https://api.weixin.qq.com/sns/oauth2/access_token')
        app.config.setdefault('WX_USERINFO_URL_BASE', 'https://api.weixin.qq.com/sns/userinfo')
        app.config.setdefault('WX_OAUTH2_NEXT_SESSION_KEY', 'WX_OAUTH2_NEXT')
        app.config.setdefault('WX_OAUTH2_REFUSED_ROUTE', '.no_auth')
        app.config.setdefault('WX_OAUTH2_AFTER_ROUTE', '.after')

        app.register_blueprint(blueprint, url_prefix=url_prefix)


    @staticmethod
    def create_url(base, *query):
        query = filter(lambda pair: pair[1] is not None, query)
        url = urljoin(base, '?{0}'.format(urlencode(list(query))))
        return url

    @staticmethod
    def create_authorize_url(redirect_uri, scope='snsapi_userinfo', state=None):
        authorize_url_base = current_app.config['WX_AUTHORIZE_URL_BASE']
        return WXOAuth2.create_url(authorize_url_base,
                                   ('appid', current_app.config['WX_APP_ID']),
                                   ('redirect_uri', redirect_uri),
                                   ('response_type', 'code'),
                                   ('scope', scope),
                                   ('state', state)) + '#wechat_redirect'


    @staticmethod
    def create_validate_url(code):
        validate_url_base = current_app.config['WX_ACCESS_TOKEN_URL_BASE']
        return WXOAuth2.create_url(validate_url_base,
                                   ('appid', current_app.config['WX_APP_ID']),
                                   ('secret', current_app.config['WX_APP_SECRET']),
                                   ('code', code),
                                   ('grant_type', 'authorization_code'))


    @staticmethod
    def create_userinfo_url(token, openid, lang='zh_CN'):
        userinfo_url_base = current_app.config['WX_USERINFO_URL_BASE']
        return WXOAuth2.create_url(userinfo_url_base,
                                   ('access_token', token),
                                   ('openid', openid),
                                   ('lang', lang))

    @property
    def app(self):
        return self._app or current_app

    @property
    def openid(self):
        return flask.session.get(
            self.app.config['WX_OPENID_SESSION_KEY'], None)

    @property
    def access_token(self):
        return flask.session.get(
            self.app.config['WX_OAUTH2_TOKEN_SESSION_KEY'], None)

    @property
    def userinfo(self):
        return flask.session.get(
            self.app.config['WX_OAUTH2_USERINFO_SESSION_KEY'], None)


class Sign:
    """
    用于生成jsapi验证签名
    """
    def __init__(self, jsapi_ticket, url):
        self.ret = {
            'nonceStr': self.__create_nonce_str(),
            'jsapi_ticket': jsapi_ticket,
            'timestamp': self.__create_timestamp(),
            'url': url
        }

    def __create_nonce_str(self):
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(15))

    def __create_timestamp(self):
        return int(time.time())

    def sign(self):
        s = '&'.join(['%s=%s' % (key.lower(), self.ret[key]) for key in sorted(self.ret)])
        self.ret['signature'] = hashlib.sha1(s).hexdigest()
        return self.ret