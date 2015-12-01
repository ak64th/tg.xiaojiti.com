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
class WXUser(Base):
    openid = CharField()

    def __unicode__(self):
        return self.openid


class Group(Base):
    leader = ForeignKeyField(WXUser)
    title = CharField()
    content = TextField()

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

    @property
    def buyers(self):
        return (WXUser
                .select(WXUser)
                .join(Purchase, on=Purchase.buyer)
                .where(Purchase.product == self.id))

    def __unicode__(self):
        return '%s - Group:%s' % (self.title, self.group)


class Purchase(Base):
    buyer = ForeignKeyField(WXUser)
    product = ForeignKeyField(Product)
    amount = IntegerField()

    def __unicode__(self):
        return 'Buyer:%s - Product:%s' % (self.buyer, self.product)
