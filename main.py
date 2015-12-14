# coding=utf-8
from flask import render_template, session, jsonify, url_for, request
from peewee import create_model_tables
from app import app
from models import User, WXUser, Group, Product, Purchase
from auth import auth
from admin import admin
from api import api
from werkzeug.utils import redirect
from urllib import quote_plus, urlopen


auth.setup()
admin.setup()
api.setup()

APPID = 'wx7d620788ff94134b'
SECRET = 'a958b8b85075fc1665a58bf21ac8a5d6'


@app.route('/wechat')
def index():
    if 'wechat_user' in session:
        return jsonify(session['wechat_user'])
    return redirect(url_for('login'))


@app.route('/login')
def login():
    # https://open.weixin.qq.com/connect/oauth2/authorize?appid=wx7d620788ff94134b&redirect_uri=http%3A%2F%2Ftg.xiaojiti.com%3A5000%2Fcallback&response_type=code&scope=snsapi_userinfo&state=STATE#wechat_redirect
    # https://open.weixin.qq.com/connect/oauth2/authorize?appid=wx7d620788ff94134b&redirect_uri=http%3A%2F%2Ftg.xiaojiti.com%3A5000%2Fcallback&response_type=code&scope=snsapi_userinfo&state=123#wechat_redirect
    authorize_url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=' + APPID + \
                    '&redirect_uri=' + quote_plus(url_for('.callback', _external=True), safe='') + \
                    '&response_type=code&scope=snsapi_userinfo&state=STATE#wechat_redirect'
    return redirect(authorize_url)


@app.route('/callback')
def callback():
    def create_validate_url(code):
        return 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=' + APPID + \
               '&secret=' + SECRET + '&code=' + code + '&grant_type=authorization_code'

    code = request.args.get('code', None)
    if code:
        validate_url = create_validate_url(code)
        resp = urlopen(validate_url).read().strip().decode('utf8', 'ignore')
        return u'Resp: %s' % resp
    return u'Error: no code'


@app.route('/logout')
def logout():
    session.pop('wechat_user', None)
    return 'OK'


@app.route('/group_leader/')
def group_leader():
    return render_template('group_leader.html')


if __name__ == '__main__':
    import logging
    import logging.handlers

    logger = logging.getLogger('peewee')
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(stream_handler)

    create_model_tables(models=(User, WXUser, Group, Product, Purchase), fail_silently=True)

    # 创建测试用户
    from flask_peewee.utils import make_password

    defaults = dict(password=make_password('123456'), admin=True)
    User.get_or_create(username='admin', defaults=defaults)

    wx_user, _ = WXUser.get_or_create(openid='ba39kz15abg2')
    for group_name in (u'白菜团', u'跑鞋团', u'啤酒团', u'桑拿团', u'烧鸡团', u'烤肉团', u'坦克团'):
        Group.get_or_create(leader=wx_user, title=group_name, defaults={'content': u'团购%s' % group_name[:-1]})
    Product.get_or_create(group=1, title=u'一般小白菜', defaults=dict(content=u'可以吃', price=12.4))
    Product.get_or_create(group=1, title=u'辐射大白菜', defaults=dict(content=u'巨大', price=100))

    app.run(host='0.0.0.0', debug=True, threaded=True)