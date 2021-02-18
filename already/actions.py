#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyparsing_ext as ppx
from owlready2 import *
from keywords import *


class AtomAction(ppx.BaseAction):
    names = ('content', 'type')
    _depth = 1

    def __init__(self, *args, **kwargs):
        super(AtomAction, self).__init__(*args, **kwargs)
        if self.content in KEYWORDS:
            raise NameError('Do not use keywords for naming an individual or a concept')

    def toFormula(self):
        return self.content

    def eval(self, calculator):
        return calculator[self.content]

    def update(self, calculator, x):
        return calculator.update({self.content:x})

    def __radd__(self, s):
        return s + self.content

    @property
    def depth(self):
        return self._depth

    def contained_in(self, calculator):
        return self.content in calculator


class VariableAction(AtomAction):

    value = ''

    def eval(self, calculator):
        if 'type' in self:
            return f'x:{self.type}'
        else:
            return 'x'

class ConstantAction(AtomAction):
    def __eq__(self, other):
        if isinstance(other, str):
            return self.content == other
        else:
            return self.content == other.content

class IndividualAction(ConstantAction):
    def __init__(self, *args, **kwargs):
        super(IndividualAction, self).__init__(*args, **kwargs)
        if self.content[0].lstrip('_').isupper():
            raise Exception('A name for individual should start with lower case letters.')

    def toConcept(self):
        return OneOf({self.eval(calculator)})

class VariableConceptAction(AtomAction):
    names = ('type',)
    value = ''

    def __str__(self, calculator):
        if 'type' in self:
            return f'X:{self.type}'
        else:
            return 'X'


class ConceptAction(ConstantAction):
    # only for atomic concept
    def __init__(self, *args, **kwargs):
        super(ConceptAction, self).__init__(*args, **kwargs)
        if not self.content[0].isupper():
            raise Exception('A name for concept should start with captial letters.')


class RelationAction(ConstantAction):
    def create(self, calculator, *bases):
        calculator.update({self.content: types.new_class(self.content, bases=bases)})


class RestrictionAction(ppx.RightUnaryOperatorAction):
    pass


class NegationAction(ppx.RightUnaryOperatorAction):
    def eval(self, calculator):
        return calculator(self.function)(self.operand)


class BinaryOperatorAction(ppx.BinaryOperatorAction):

    def eval(self, calculator):
        return calculator(self.function)([arg.eval(calculator) for arg in self.args])


class AndAction(BinaryOperatorAction):
    pass


class OrAction(BinaryOperatorAction):
    pass


class XorAction(BinaryOperatorAction):
    pass


class DeclarationAction(ppx.BaseAction):
    def __init__(self, instring='', loc=0, tokens=[]):
        super(DeclarationAction, self).__init__(instring, loc, tokens)
        self.lhs, self.concept = self.tokens
    
    @property
    def lhs_name(self):
        # left hand side of declaration
        return self.lhs.content

    def eval(self, calculator):
        self.create(calculator)

    def create(self, calculator, klass=Thing):
        concept = self.concept.eval(calculator)
        indiviudal_name = self.lhs_name
        if isinstance(self.concept, ConceptAction):
            calculator.update({indiviudal_name: concept(indiviudal_name)})
        else:
            calculator.update({indiviudal_name: klass(indiviudal_name)})
            calculator[indiviudal_name].is_a.append(concept)


class ConceptDeclarationAction(DeclarationAction):

    def create(self, calculator, klass=Thing):

        concept = self.concept.eval(calculator)
        concept_name = self.lhs_name
        if isinstance(self.concept, ConceptAction):
            bases = (concept,)
            calculator.update[concept_name] = types.new_class(concept_name, bases=bases)
            calculator[concept_name].is_a.append(concept)
        else:
            bases = (klass,)
            calculator.update[concept_name] = types.new_class(concept_name, bases=bases)
            calculator[concept_name].is_a.append(concept)


class DefinitionAction(DeclarationAction):

    def create(self, calculator, klass=Thing):
        concept = self.concept.eval(calculator)
        concept_name = self.lhs_name
        if isinstance(self.concept, ConceptAction):
            calculator.update[self.concept_name] = self.concept
        else:
            bases = (klass,)
            calculator.update[self.concept_name] = types.new_class(self.concept_name, bases=bases)
            calculator[self.indiviudal_name].equivalent_to.append(concept)


class FormulaAction(ppx.BinaryOperatorAction):
    def __init__(self, instring='', loc=0, tokens=[]):
        self.args = tokens[0::2]
        if len(set(tokens[1::2]))==1:
            self.ishybrid = False
            self.function = tokens[1]
        else:
            self.ishybrid = True
            self.function = tokens[1::2]
        self.associative = True

class ContainingFormulaAction(FormulaAction):
    def __init__(self, instring='', loc=0, tokens=[]):
        super(ContainingFormulaAction, self).__init__(instring, loc, tokens)
        self.individual, self.concept = self.args

    def eval(self, calculator):
        individual = self.individual.eval(calculator)
        concept = self.concept.eval(calculator)
        return concept in individual.INDIRECT_is_a

class ComparisonFormulaAction(FormulaAction):
    def __init__(self, instring='', loc=0, tokens=[]):
        super(ComparisonFormulaAction, self).__init__(instring, loc, tokens)

    def eval(self, calculator):
        for left, right in zip(self.args[:-1], self.args[1:]):
            if not calculator(self.function)(left, right):
                return False
        else:
            return True


class StatementSequenceAction(ppx.BaseAction):
    def eval(self, calculator):
        for token in self.tokens:
            ret = token.eval(calculator)
        return ret


