from flask_peewee.rest import RestAPI, Authentication

from app import app
from auth import auth
from models import WXUser, Group, Product, Purchase


class TestAuthentication(Authentication):
    """
    Always allow operation
    """

    def authorize(self):
        return True


test_auth = TestAuthentication(auth)

api = RestAPI(app, prefix='/api/v1', default_auth=test_auth)

api.register(WXUser)
api.register(Group)
api.register(Product)
api.register(Purchase)