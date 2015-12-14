import unittest

import flask
from ..wechat import WXOAuth2


class TestWXOAuth2(unittest.TestCase):
    def setUp(self):
        self.app = flask.Flask(__name__)
        self.wx_auth = WXOAuth2()
        self.wx_auth.init_app(self.app)
        self.app.testing = True

        self.app.config['WX_APP_ID'] = 'wx7d620788ff94134b'
        self.app.config['WX_APP_SECRET'] = 'a958b8b85075fc1665a58bf21ac8a5d6'

        self.ctx = self.app.test_request_context('/')
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_create_authorize_url(self):
        authorize_url = self.wx_auth.create_authorize_url(
            'http://tg.xiaojiti.com:5000/callback', scope='snsapi_base', state=123)
        self.assertEqual(authorize_url,
                         'https://open.weixin.qq.com/connect/oauth2/authorize?appid=wx7d620788ff94134b&'
                         'redirect_uri=http%3A%2F%2Ftg.xiaojiti.com%3A5000%2Fcallback&'
                         'response_type=code&scope=snsapi_base&state=123#wechat_redirect')

    def test_create_validate_url(self):
        validate_url = self.wx_auth.create_validate_url(code='ad3ZXdfVbzcxbvaINaRV4a2dd')
        self.assertEqual(validate_url,
                         'https://api.weixin.qq.com/sns/oauth2/access_token?appid=wx7d620788ff94134b'
                         '&secret=a958b8b85075fc1665a58bf21ac8a5d6&code=ad3ZXdfVbzcxbvaINaRV4a2dd'
                         '&grant_type=authorization_code')

    def test_create_userinfo_url(self):
        token = 'OezXcEiiBSKSxW0eoylIeD2ON97OFscb2KrQBm1dkGyp1LLMlXfkpirqVWuOebgAyYKpCA5jyGNNt8wesvFlCJKd-H-qk' \
                'm_y13DMQV3KrsvK60kT4fJWRMrXiJ7WMiivrv_53GUOKY0C2b5gOQY47w'
        openid = 'oXhUnw7OIvYKGj8ljstNJzXUZeZ0'
        userinfo_url = self.wx_auth.create_userinfo_url(token=token, openid=openid, lang='zh_CN')
        self.assertEqual(userinfo_url,
                         'https://api.weixin.qq.com/sns/userinfo?access_token=' +
                         token + '&openid=' + openid + '&lang=zh_CN')


if __name__ == '__main__':
    unittest.main()