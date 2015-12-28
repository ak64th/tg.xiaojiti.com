# coding=utf-8
"""
定时任务，获取微信access_token和jsapi_ticket
需要在独立进程内运行，比如通过uwsgi的mule

    uwsgi --http-socket :4000 --mule=tasks.py --wsgi-file=main.py

"""
import os
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from peewee import DoesNotExist
from models import WxAccessToken, WxJsapiTicket
from wechat import WXOAuth2
from app import app

try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen

try:
    import simplejson as json
except ImportError:
    import json

WX_APP_ID = app.config['WX_APP_ID']
WX_APP_SECRET = app.config['WX_APP_SECRET']

DEFAULT_ACCESS_TOKEN_EXPIRE_TIME = 7200  # 默认到期时间

create_url = WXOAuth2.create_url


def create_access_token_url(appid=WX_APP_ID, secret=WX_APP_SECRET):
    return create_url('https://api.weixin.qq.com/cgi-bin/token',
                      ('grant_type', 'client_credential'),
                      ('appid', appid),
                      ('secret', secret))


# ?access_token=ACCESS_TOKEN&type=jsapi
def create_jsapi_ticket_url(token):
    return create_url('https://api.weixin.qq.com/cgi-bin/ticket/getticket',
                      ('access_token', token),
                      ('type', 'jsapi'))


def update_access_token():
    access_token_url = create_access_token_url()
    ret_text = urlopen(access_token_url).read().strip().decode('utf8', 'ignore')
    ret_data = json.loads(ret_text)
    if u'access_token' not in ret_data:
        raise Exception('Error occurs when trying to get access token')

    token, expire = ret_data[u'access_token'], ret_data[u'expires_in']

    # 读取或创建记录
    wx_access_token, _ = WxAccessToken.get_or_create(appid=WX_APP_ID)
    wx_access_token.token = token
    wx_access_token.expires_in = expire
    if not wx_access_token.save():
        raise Exception('Error occurs when saving access token to database')

    print('Get access token %s which will expire in %s seconds' % (token, expire))
    return token, int(expire)


def update_jsapi_ticket():
    try:
        wx_access_token = WxAccessToken.get(WxAccessToken.appid == WX_APP_ID)
    except DoesNotExist:
        raise Exception('Need to get access token before request for jsapi ticket')

    jsapi_ticket_url = create_jsapi_ticket_url(wx_access_token.token)
    ret_text = urlopen(jsapi_ticket_url).read().strip().decode('utf8', 'ignore')
    ret_data = json.loads(ret_text)

    if u'ticket' not in ret_data:
        raise Exception('Error occurs when trying to get jsapi ticket')

    ticket, expire = ret_data[u'ticket'], ret_data[u'expires_in']

    wx_jsapi_ticket, _ = WxJsapiTicket.get_or_create(appid=WX_APP_ID)
    wx_jsapi_ticket.ticket = ticket
    wx_jsapi_ticket.expires_in = expire
    if not wx_jsapi_ticket.save():
        raise Exception('Error occurs when saving jsapi ticket to database')

    print('Get jsapi ticket %s which will expire in %s seconds' % (ticket, expire))
    return ticket, int(expire)


if __name__ == '__main__':
    # 确保数据表已经创建
    WxAccessToken.create_table(fail_silently=True)
    WxJsapiTicket.create_table(fail_silently=True)

    # 设置定时器
    scheduler = BlockingScheduler()

    # 第一次运行，根据返回值设置任务间隔
    access_token, expires_in = update_access_token()
    scheduler.add_job(update_access_token, 'interval', seconds=(expires_in // 2))

    ticket, expires_in = update_jsapi_ticket()
    scheduler.add_job(update_jsapi_ticket, 'interval', seconds=(expires_in // 2))

    logger = logging.getLogger('apscheduler.executors.default')
    logger.setLevel(logging.DEBUG)
    steam_handler = logging.StreamHandler()
    logger.addHandler(steam_handler)

    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
