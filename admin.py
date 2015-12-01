# coding=utf-8
from flask_peewee.admin import Admin, ModelAdmin
from app import app
from models import WXUser, Group, Product, Purchase
from auth import auth


class Base(ModelAdmin):
    exclude = ('id', 'created', 'modified')


class WXUserAdmin(Base):
    columns = ('id', 'openid')


class GroupAdmin(Base):
    columns = ('id', 'leader', 'title', 'content', 'created', 'modified')


class ProductAdmin(Base):
    columns = ('id', 'title', 'content', 'price', 'group', 'created', 'modified')


class PurchaseAdmin(Base):
    columns = ('id', 'buyer', 'product', 'amount', 'created', 'modified')


class UserAdmin(Base):
    columns = ['id', 'username', 'active', 'admin']

    def save_model(self, instance, form, adding=False):
        orig_password = instance.password
        user = super(UserAdmin, self).save_model(instance, form, adding)
        if orig_password != form.password.data:
            user.set_password(form.password.data)
            user.save()
        return user


admin = Admin(app, auth, branding=u'团购助手后台')
auth.register_admin(admin, UserAdmin)
admin.register(WXUser, WXUserAdmin)
admin.register(Group, GroupAdmin)
admin.register(Product, ProductAdmin)
admin.register(Purchase, PurchaseAdmin)
