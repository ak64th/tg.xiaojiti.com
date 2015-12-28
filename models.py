# coding=utf-8
import datetime

from peewee import *
from flask_peewee.auth import BaseUser
from app import db


class Base(db.Model):
    created = DateTimeField(default=datetime.datetime.now)
    modified = DateTimeField(default=datetime.datetime.now)

    def save(self, *args, **kwargs):
        self.modified = datetime.datetime.now()
        return super(Base, self).save(*args, **kwargs)


# 网站网页端用户
class User(Base, BaseUser):
    username = CharField()
    password = CharField()
    active = BooleanField(default=True)
    admin = BooleanField(default=False)

    def __unicode__(self):
        return self.username
    

# 记录来访微信用户信息
#  app.logger.debug(resp2)
#  {
#    "openid": "oXhUnw7OIvYKGj8ljstNJzXUZeZ0",
#    "nickname": "郁骏",
#    "sex": 0,
#    "language": "en",
#    "city": "",
#    "province": "",
#    "country": "中国",
#    "headimgurl": "",
#    "privilege": []
#  }
class WXUser(Base):
    openid = CharField()
    nickname = CharField(null=True)
    sex = BooleanField(null=True)
    language = CharField(null=True)
    city = CharField(null=True)
    province = CharField(null=True)
    country = CharField(null=True)
    headimgurl = CharField(null=True)
    privilege = CharField(null=True)

    def __unicode__(self):
        return self.openid


class Group(Base):
    leader = ForeignKeyField(WXUser)
    title = CharField()
    finished = BooleanField(default=False)

    @property
    def members(self):
        return (WXUser
                .select(WXUser)
                .join(Purchase, on=Purchase.buyer)
                .where(Purchase.product << self.products))

    def __unicode__(self):
        return self.title


class Product(Base):
    group = ForeignKeyField(Group, related_name='products')
    title = CharField()
    content = TextField()
    price = DecimalField()
    photo = CharField(null=True)

    @property
    def buyers(self):
        return (WXUser
                .select(WXUser)
                .join(Purchase, on=Purchase.buyer)
                .where(Purchase.product == self.id))

    def __unicode__(self):
        return '%s - Group:%s' % (self.title, self.group)


# 保存微信授权信息，用appid标识不同应用的access_token
class WxAccessToken(Base):
    appid = CharField()
    token = CharField(null=True)
    expires_in = IntegerField(null=True)

    def __unicode__(self):
        return self.token


# 保存微信授权信息，用appid标识不同应用的jsapi_ticket
class WxJsapiTicket(Base):
    appid = CharField()
    ticket = CharField(null=True)
    expires_in = IntegerField(null=True)

    def __unicode__(self):
        return self.ticket


class Purchase(Base):
    buyer = ForeignKeyField(WXUser)
    product = ForeignKeyField(Product)
    group = ForeignKeyField(Group)
    amount = IntegerField()

    def __unicode__(self):
        return 'Buyer:%s - Product:%s' % (self.buyer, self.product)
