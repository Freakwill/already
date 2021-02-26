#!/usr/bin/env python3


class Speak(object):

    def __init__(self, content):
        self.__content = content

    @property
    def content(self):
        return self.__content

class Question(Speak):
    pass
    
class Respond(Speak):
    pass
