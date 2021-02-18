#!/usr/bin/env python3
# -*- coding: utf-8 -*-

anaphora = '@'

class BaseCalculator:
    """Base Class for Semantic Calculator

    memory: assignment for variables
    dictionary: intereption for constants
    """
    def __init__(self, memory=None, dictionary=None):
        self.__memory = {} if memory is None else memory
        self.__dictionary = {} if dictionary is None else dictionary

    @property
    def memory(self):
        return self.__memory

    @property
    def dictionary(self):
        return self.__dictionary

    def set_constant(self, k, v):
        self.__dictionary[k] = v

    def __getitem__(self, k):
        if k in self.memory:
            return self.memory[k]
        elif k in self.dictionary:
            return self.dictionary[k]
        else:
            raise NameError(f'{k} is not definded.')

    def __setitem__(self, k, v):
        if k in self.dictionary:
            raise NameError(f'{k} could not be redefinded.')
        else:
            self.__memory[k] = v
        self.__memory[anaphora] = v

    def set(self, **kwargs):
        for k, v in kwargs:
            if k in self.dictionary:
                raise NameError(f'{k} could not be redefinded.')
            else:
                self.__memory[k] = v
        self.__memory[anaphora] = v

    def __call__(self, x):
        raise NotImplementedError

    def __contains__(self, x):
        return x in self.memory or x in self.dictionary


from utils import *

def si_a(A, B):
    return is_a(B, A)

def eq(A, B):
    return B in A.INDIRECT_equivalent_to

class OwlreadyCalculator(BaseCalculator):
    """Calculator for Owlready

    provide the semantics of constants and operators in DLs.
    """
    def __init__(self, memory={}):
        dictionary = {'|':Or, '&': And, '~': Not, '<=': is_a, '=>': si_a, '==': eq}
        super(OwlreadyCalculator, self).__init__(memory, dictionary)


    def __call__(self, x, *args, **kwargs):
        if args or kwargs:
            return self(x)(*args, **kwargs)
        if x in self:
            return self[x]
        else:
            return globals()[x]