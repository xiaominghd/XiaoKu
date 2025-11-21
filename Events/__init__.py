"""
@author: Gonghf
@date: 2025/11/9
@description: 
"""
from typing import List

class Event:

    def __init__(self, name:str=None, history:List=None, summary:str=None, back_ground:str=None, score:int=None):

        self.name = name

        self.history = history
        if history is None:
            self.history = []

        self.summary = summary
        if summary is None:
            self.summary = ""

        self.back_ground = back_ground

