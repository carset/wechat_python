#!/usr/bin/env python
# -*- encoding:utf-8 -*-
import hashlib
import urllib
import json
import requests
from app import app, cache


def create_button(payload):
    """
        创建微信菜单
    :param payload:
    :return:
    """
    url = 'https://api.weixin.qq.com/cgi-bin/menu/create?access_token=%s' % get_token()
    response = requests.post(url, data=payload).json()
    app.logger.debug(payload)
    if response is not None and response['errcode'] == 0:
        return True
    else:
        app.logger.error(response)
        return False


def get_button():
    """
        自定义菜单查询
    :return:
    """
    url = 'https://api.weixin.qq.com/cgi-bin/menu/get?access_token=%s' % get_token()
    response = requests.get(url).json()
    if response is not None and 'menu' in response:
        return response
    else:
        app.logger.error(response)
        return {}


def auth(token, open_id):
    """
        验证用户是否有效
    :param token:
    :param open_id:
    :return:
    """
    service_url = 'https://api.weixin.qq.com/sns/auth?access_token=%s&openid=%s' % (token, open_id)
    response = requests.get(service_url).json()
    if response is not None and 'errcode' in response:
        return True
    else:
        app.logger.error(response)
        return False


def refresh_token(token):
    """
        重新刷新Token
    :param token:
    :return:
    """
    url = 'https://api.weixin.qq.com/sns/oauth2/refresh_token?appid=%s&grant_type=refresh_token&refresh_token=%s' % (
        app.config.get('WX_APP_ID'), token)
    response = requests.get(url).json()
    if response is not None and 'access_token' in response:
        return response
    else:
        app.logger.error(response)
        return None


def access_token(code):
    """
        获取授权Token
    :param code:
    :return:
    """
    url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code' \
          % (app.config.get('WX_APP_ID'), app.config.get('WX_APP_SECRET'), code)
    response = requests.get(url).json()
    if response is not None and 'access_token' in response:
        return response
    else:
        response['url'] = url
        app.logger.error(response)
        return None


def url_for_code(redirect_uri, scope='snsapi_base', state=None):
    """
        生成授权用的链接
    :param redirect_uri:
    :param scope:
    :param state:
    :return:
    """
    url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=%s&redirect_uri=%s&response_type=code&scope=%s' \
          '&state=%s#wechat_redirect' % (app.config.get('WX_APP_ID'),
                                         urllib.quote(redirect_uri, safe=""),  # 按微信开放平台规则,url需要进行编码
                                         scope,
                                         state)
    return url


def _get_app_token(app_id, secret):
    """
        从接口获取应用TOKEN
    :param app_id:
    :param secret:
    :return:
    """
    url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % (app_id, secret)
    response = requests.get(url).json()
    if response is not None and 'access_token' in response:
        return response['access_token']
    else:
        app.logger.error(response)
        return None


@cache.cached(timeout=2 * 60 * 60, key_prefix='_jsapi_token')  # 缓存2小时
def get_jsapi_ticket():
    """
        获取jsapi_ticket
    :return:
    """
    url = 'https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=%s&type=jsapi' % (get_token())
    response = requests.get(url).json()
    if response is not None and 'ticket' in response:
        return response['ticket']
    else:
        app.logger.error(response)
        return None


def create_signature(noncestr, timestamp, url):
    """
        生成jsapi签名
    :param noncestr:
    :param timestamp:
    :param url:
    :return:
    """
    _str = 'jsapi_ticket=%s&noncestr=%s&timestamp=%s&url=%s' % (get_jsapi_ticket(), noncestr, timestamp, url)
    return hashlib.sha1(_str).hexdigest()


@cache.cached(timeout=2 * 60 * 60, key_prefix='_app_token')  # 缓存2小时
def get_token():
    """
        获取应用TOKEN
    :return:
    """
    return _get_app_token(app.config.get('WX_APP_ID'), app.config.get('WX_APP_SECRET'))


def get_user_list(next_id=None, ret=list()):
    """
        获取关注的用户列表
    :param next_id:
    :param ret:
    :return:
    """
    if next_id != u'':
        _next_open_id = '&next_openid=%s' % next_id if next_id is not None else ''
        url = 'https://api.weixin.qq.com/cgi-bin/user/get?access_token=%s%s' % (get_token(), _next_open_id)
        response = requests.get(url).json()
        if response is not None and 'data' in response:
            ret.extend(response['data']['openid'])
        get_user_list(response['next_openid'], ret)
    return ret


def get_user_info(open_id):
    """
        单条获取用户信息
    :param open_id:
    :return:
    """
    url = 'https://api.weixin.qq.com/cgi-bin/user/info?access_token=%s&openid=%s&lang=zh_CN' % (get_token(), open_id)
    response = requests.get(url).json()
    if response is not None and 'openid' in response:
        return response
    else:
        app.logger.error(response)
        return None


def batch_get_user_info(users):
    """
    批量获取用户信息
    :param users:
    :return:
    """
    url = 'https://api.weixin.qq.com/cgi-bin/user/info/batchget?access_token=%s' % (get_token())
    payload = dict(user_list=[])
    for user in users:
        payload['user_list'].append({'openid': user})
    response = requests.post(url, json.dumps(payload)).json()
    if response is not None and 'user_info_list' in response:
        return response['user_info_list']
    else:
        app.logger.error(response)
        return None


def add_custom(custom):
    """
        添加客服
    :param custom:
    :return:
    """
    url = 'https://api.weixin.qq.com/customservice/kfaccount/add?access_token=%s' % get_token()
    payload = json.dumps(custom)
    app.logger.debug(payload)
    response = requests.post(url, payload).json()
    if response is not None and response['errcode'] == 0:
        return True
    else:
        app.logger.error(response)
        return False


def update_custom(custom):
    """
        更新客服信息
    :param custom:
    :return:
    """
    url = 'https://api.weixin.qq.com/customservice/kfaccount/update?access_token=%s' % get_token()
    payload = json.dumps(custom)
    app.logger.debug(payload)
    response = requests.post(url, payload).json()
    if response is not None and response['errcode'] == 0:
        return True
    else:
        app.logger.error(response)
        return False


def del_custom(custom):
    """
        删除客服
    :param custom:
    :return:
    """
    url = 'https://api.weixin.qq.com/customservice/kfaccount/del?access_token=%s' % get_token()
    payload = json.dumps(custom)
    app.logger.debug(payload)
    response = requests.post(url, payload).json()
    if response is not None and response['errcode'] == 0:
        return True
    else:
        app.logger.error(response)
        return False


def get_custom():
    """
        获取所有客服信息
    :return:
    """
    url = 'https://api.weixin.qq.com/cgi-bin/customservice/getkflist?access_token=%s' % get_token()
    response = requests.get(url).json()
    if response is not None and 'kf_list' in response:
        return response['kf_list']
    else:
        app.logger.error(response)
        return None


def send_custom_message(message):
    """
        发送客服消息
    :param message:
    :return:
    """
    url = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=%s' % get_token()
    response = requests.post(url, message).json()
    if response is not None and response['errcode'] == 0:
        return True
    else:
        app.logger.error(response)
        return False


def add_material(image_path):
    """
        上传图片
    :param image_path:
    :return:
    """
    url = 'https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=%s' % get_token()
    response = requests.post(url, {'type': 'image'}, files={'media': open(image_path)}).json()
    if response is not None and 'media_id' in response:
        return response
    else:
        app.logger.error(response)
        return False


def md5(text):
    m = hashlib.md5()
    m.update(text)
    return m.hexdigest()

# End
