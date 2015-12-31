# coding=utf-8
from flask_peewee.rest import RestAPI, RestResource, Authentication

from app import app
from auth import auth
from models import WXUser, Group, Product, Purchase


class TestAuthentication(Authentication):
    """
    Always allow operation
    """

    def authorize(self):
        return True

# 增大每次查询最大项目数
class BaseResource(RestResource):
    paginate_by = 100


test_auth = TestAuthentication(auth)

api = RestAPI(app, prefix='/api/v1', default_auth=test_auth)

api.register(WXUser, provider=BaseResource)
api.register(Group, provider=BaseResource)
api.register(Product, provider=BaseResource)
api.register(Purchase, provider=BaseResource)