# coding=utf-8
from flask import request, redirect, render_template, jsonify, render_template_string
from peewee import create_model_tables
import simplejson as json

from app import app
from models import User, WXUser, Group, Product, Purchase
from auth import auth
from admin import admin
from api import api
from wechat import WXOAuth2, auth_required, wx_userinfo_fetched
from photos import PhotoManager, UploadNotAllowed

auth.setup()
admin.setup()
api.setup()

wx_auth = WXOAuth2()
wx_auth.init_app(app, '/wx_auth')

photo_manager = PhotoManager()
photo_manager.init_app(app)


@app.route('/upload', methods=['POST', 'GET'])
def upload_handler():
    filename = None
    if request.method == 'POST':
        photo = request.files['photo']
        if photo:
            try:
                filename = photo_manager.save(photo)
                # thumb_url = photo_manager.thumb_url(filename)
                # return redirect(thumb_url)
            except UploadNotAllowed:
                app.logger.debug('UploadNotAllowed')
    return render_template_string(u"""
    <form action="{{ url_for('upload_handler') }}" method="post" enctype="multipart/form-data">
      <input name='photo' type="file" id="photo"/>
      <input type="submit" value='上传'/>
    </form>
    {% if image_name %}
    <a href="{{ photo_url_for(image_name) }}"><img src="{{ thumb_url_for(image_name, size='100x100', crop='fit') }}"/></a>
    {% endif %}
    """, image_name=filename)

@app.route('/wechat')
@auth_required
def show_wechat_user_info():
    return jsonify(wx_auth.userinfo)


@wx_userinfo_fetched.connect_via(app)
def save_wx_userinfo(sender, userinfo):
    app.logger.debug(u'WeChat User %s authorized us for personal info: %s' % (userinfo['openid'], userinfo))
    # WeChat User oXhUnw7OIvYKGj8ljstNJzXUZeZ0 authorized us for personal info:
    # {u'province': u'', u'openid': u'oXhUnw7OIvYKGj8ljstNJzXUZeZ0', u'headimgurl': u'', u'language': u'en',
    # u'city': u'', u'country': u'\u4e2d\u56fd', u'sex': 0, u'privilege': [], u'nickname': u'\u90c1\u9a8f'}
    wx_user, created = WXUser.get_or_create(openid=userinfo['openid'])
    for key, value in userinfo.items():
        if not hasattr(wx_user, key):
            continue
        # privilege字段是一个json数组
        if isinstance(value, list):
            value = u','.join(value)
        setattr(wx_user, key, value)
    wx_user.save()


@app.route('/group_leader/')
@auth_required
def group_leader():
    # wx_user = WXUser.get(WXUser.openid == 'oXhUnw7OIvYKGj8ljstNJzXUZeZ0')
    wx_user = WXUser.get(WXUser.openid == wx_auth.openid)
    # 调用api插件来输出json，保证json序列化的一致性
    wx_user_resource = api._registry[WXUser]
    wx_user_data = json.dumps(wx_user_resource.serialize_object(wx_user))
    return render_template('group_leader.html', wx_user_data=wx_user_data)

@app.route('/group_member/')
@auth_required
def group_member():
    # wx_user = WXUser.get(WXUser.openid == 'oXhUnw7OIvYKGj8ljstNJzXUZeZ0')
    wx_user = WXUser.get(WXUser.openid == wx_auth.openid)
    wx_user_resource = api._registry[WXUser]
    wx_user_data = json.dumps(wx_user_resource.serialize_object(wx_user))
    return render_template('group_member.html', wx_user_data=wx_user_data)


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

    u, _ = WXUser.get_or_create(openid='oXhUnw7OIvYKGj8ljstNJzXUZeZ0')
    g, _ = Group.get_or_create(leader=u, title=u'白菜团')
    Product.get_or_create(group=g, title=u'一般小白菜', defaults=dict(content=u'可以吃', price=12.4))
    Product.get_or_create(group=g, title=u'辐射大白菜', defaults=dict(content=u'巨大', price=100))
    for group_name in (u'跑鞋团', u'啤酒团', u'桑拿团', u'烧鸡团', u'烤肉团', u'坦克团'):
        Group.get_or_create(leader=u, title=group_name)

    app.run(host='0.0.0.0', debug=True, threaded=True)