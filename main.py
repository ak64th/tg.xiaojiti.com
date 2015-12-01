# coding=utf-8
from flask import render_template
from peewee import create_model_tables
from app import app
from models import User, WXUser, Group, Product, Purchase
from auth import auth
from admin import admin
from api import api


auth.setup()
admin.setup()
api.setup()

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

    app.run()