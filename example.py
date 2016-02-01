#!/usr/bin/env python
# -*- encoding:utf-8 -*-
import datetime

from flask import Blueprint
from flask import render_template
from flask import request

from app import csrf, app
from .helpers import MessageResolver
from .helpers import message_handler
from .helpers import verify_signature

gateway = Blueprint('gateway', __name__, url_prefix='/gw')


@gateway.route('/receive', methods=['GET'])
def verify():
    """
        接口验证
    :return:
    """
    if verify_signature(request.args.get('signature'), request.args.get('timestamp'),
                        request.args.get('nonce')):
        return render_template('gw/message.html', data=request.args.get('echostr'))
    else:
        return render_template("gw/fail.html")


@gateway.route('/receive', methods=['POST'])
@csrf.exempt
def receive():
    """
        接受微信事件通知
        # 设置微信服务器地址为 xxxxx/gw/receive
    :return:
    """
    if verify_signature(request.args.get('signature'), request.args.get('timestamp'),
                        request.args.get('nonce')):
        resolver = MessageResolver(request.data)
        # print request.data
        return resolver.handle()


@message_handler(None)
def default_handler(resolver):
    return render_template("gw/message/default.html")


@message_handler('click', 'search_device')
def find_device(resolver):
    """
    :param resolver:
    :return:
    """
    from_user = resolver.xpath('FromUserName')
    to_user = resolver.xpath('ToUserName')
    # ...
    


@message_handler('scancode_waitmsg', 'scan_device_qrcode')
def device_detail_handler(resolver):
    """
    :param resolver:
    :return:
    """
    from_user = resolver.xpath('FromUserName')
    to_user = resolver.xpath('ToUserName')
    code = resolver.xpath('ScanCodeInfo/ScanResult')
    # ...

# End
