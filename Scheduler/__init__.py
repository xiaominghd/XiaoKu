"""
@author: Gonghf
@date: 2025/11/6
@description: 
"""
from collections import defaultdict
from typing import List


class Msg:

    def __init__(self, role, content, is_send):

        self.role = role
        self.content = content
        self.is_send = is_send

class MessageBank:

    def __init__(self):

        self.message_list_dict = defaultdict(list)

    def append(self, message:Msg):

        self.message_list_dict['not_send'].append(message) # 往未发送的列表中新添加信息

    def send(self):

        message = self.message_list_dict['not_send'].pop(0)  # 从已经发送的
        message.is_send = True
        self.message_list_dict['send'].append(message)

        return message

    @staticmethod
    def get_history_info(infos:List[Msg]):

        infos = infos[::-1]  # 先反转一下

        return [{"role":info.role,"content":info.content} for info in infos]


