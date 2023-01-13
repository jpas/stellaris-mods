from abc import ABC
from stellaris.ast import *


class ColonyAutomation:
    def __init__(self, defn):
        match defn:
            case Statement(Label(label), _, exps):
                pass
            case _:
                raise ValueError

    def to_ast(self):
        return Statement(self.label, '=', ...)


class ColonyAutomationCategory:
    def __init__(self, defn):
        match defn:
            case Statement(Label(label), _, exps):
                pass
            case _:
                raise ValueError

        self.label = label

    def to_ast(self):
        return Statement(self.label, '=', ...)
