#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
communication diagram:
            parse(string)          eval(action)            store/update
--> [:Parser]   ----->   [:Action]    ----->   [calculator]  <----->   [Owlready object]
"""

from parser import *

class BaseLanguage:
    def make_parser(self, enablePackrat=True):
        raise NotImplementedError

    def matches(self, s):
        if not hasattr(self, 'expression'):
            self.make_parser()
        return self.expression.matches(s)

    def parse(self, s):
        if not hasattr(self, 'expression'):
            self.make_parser()
        return self.expression.parseString(s)[0]

    def parseFile(self, filename):
        with open(filename, 'r') as fo:
            return self.parse(fo.read())


class DL(BaseLanguage):
    pass