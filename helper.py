#!/usr/bin/env python
# -*- encoding:utf-8 -*-
import hashlib
from xml.etree import ElementTree
from werkzeug.security import safe_str_cmp
from app import app


def verify_signature(signature, timestamp, nonce):
    """
        验证签名
    :param signature:
    :param timestamp:
    :param nonce:
    :return:
    """
    if signature is None or timestamp is None or nonce is None:
        return False
    sequence = (app.config.get('WX_APP_TOKEN'), timestamp, nonce)
    sequence = sorted(sequence)
    tmp_str = ''.join(sequence)
    sha1 = hashlib.sha1()
    sha1.update(tmp_str)
    return safe_str_cmp(sha1.hexdigest(), signature)


def message_handler(message_type, event_key=None):
    """
        注册消息处理事件
    :param message_type:
    :param event_key:
    :return:
    """
    def wrap(f):
        MessageResolver.handle_methods.setdefault(message_type, {})
        MessageResolver.handle_methods[message_type][event_key] = f
        return f

    return wrap


class MessageResolver(object):
    """
        消息处理器
    """
    handle_methods = dict()

    def __init__(self, xml_text):
        self.xml = ElementTree.fromstring(xml_text)

    def xpath(self, path, default=None):
        return self.xml.findtext(path, default=default)

    def handle(self):
        _type = self.xpath('Event')
        if _type is None:
            _type = self.xpath('MsgType')
        c = MessageResolver.handle_methods.get(_type.lower())
        if c is not None:
            return c.get(self.xpath('EventKey'))(self)
        raise KeyError

        # End
