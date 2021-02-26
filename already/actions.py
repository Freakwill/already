#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyparsing_ext as ppx
from owlready2 import *
from keywords import *
from utils import *


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

    def __radd__(self, s):
        return s + self.content

    @property
    def depth(self):
        return self._depth

    def contained_in(self, calculator):
        return self.content in calculator


class VariableAction(AtomAction):
    names = ('name', 'type')


class IndividualVariableAction(VariableAction):

    def eval(self, calculator):
        return lambda x: self.eval(calculator | {self.name:x})

class ConceptVariableAction(VariableAction):

    def eval(self, calculator):
        return lambda X: self.eval(calculator | {self.name:X})


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
        return OneOf([{self.eval(calculator)}])


class IndividualSetAction(ConstantAction):
    def __init__(self, *args, **kwargs):
        super(IndividualSetAction, self).__init__(*args, **kwargs)
        self.individuals = self.tokens[:]

    def eval(self, calculator):
        return OneOf([i.eval(calculator) for i in self.individuals])

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

class QuantifierAction(ppx.BaseAction):
    def __init__(self, *args, **kwargs):
        super(QuantifierAction, self).__init__(*args, **kwargs)
        self.content = self.tokens[0]
        if len(self.tokens)==2:
            self.num = self.tokens[1]

    def __call__(self, r):
        if self.content=='some':
            return r.some
        elif self.content=='only':
            return r.only
        elif self.content == 'more':
            return lambda A: r.min(self.num, A)
        elif self.content == 'less':
            return lambda A: r.max(self.num, A)
        elif self.content == 'exact':
            return lambda A: r.exactly(self.num, A)

    def __eq__(self, other):
        if isinstance(other, QuantifierAction):
            return self.content == other.content
        elif isinstance(other, str):
            return self.content == other
        else:
            raise TypeError(f'"{other}" should be an instance of QuantifierAction or str.')


class RestrictionAction(ppx.RightUnaryOperatorAction):
    names = ('quantifier', 'relation')

    def eval(self, calculator):
        return self.quantifier(self.relation)(self.operand)

    def __repr__(self):
        if self.quantifier == 'some':
            s = '∃'
        elif self.quantifier == 'only':
            s = '∀'
        elif self.quantifier == 'more':
            s = 'Q>={self.num}'
        elif self.quantifier == 'less':
            s = 'Q<={self.num}'
        elif self.quantifier == 'exact':
            s = 'Q={self.num}'
        s += f' {self.relation}.'
        arg = self.operand
        s += f'{arg:p}' if isinstance(arg, (AndAction, OrAction)) else f'{arg}'
        return s



class NegationAction(ppx.RightUnaryOperatorAction):
    def eval(self, calculator):
        return calculator(self.function)(self.operand)

    def __repr__(self):
        s = '~'
        arg = self.operand
        s += f'{arg:p}' if isinstance(arg, (AndAction, OrAction)) else f'{arg}'
        return s


class BinaryOperatorAction(ppx.BinaryOperatorAction):

    def eval(self, calculator):
        return calculator(self.function)([arg.eval(calculator) for arg in self.args])


class AndAction(BinaryOperatorAction):
    def __repr__(self):
        return ' & '.join(f'{arg:p}' if isinstance(arg, OrAction) else f'{arg}' for arg in self.args)


class OrAction(BinaryOperatorAction):
    pass


class XorAction(BinaryOperatorAction):
    pass

class ConceptTupleAction(ppx.BaseAction):
    names = ('concepts',)
    def __init__(self, instring='', loc=0, tokens=[]):
        super(ConceptTupleAction, self).__init__(instring, loc, tokens)
        self.concepts = self.tokens
    
    def eval(self, calculator):
        return (tuple([c.eval(calculator) for c in self.concepts if isinstance(c, ConceptAction)]),
        tuple([c.eval(calculator) for c in self.concepts if not isinstance(c, ConceptAction)]))


class DeclarationAction(ppx.BaseAction):
    def __init__(self, instring='', loc=0, tokens=[]):
        super(DeclarationAction, self).__init__(instring, loc, tokens)
        self.lhs, self.base_concepts = self.tokens

    @property
    def lhs_name(self):
        # left hand side of declaration
        return self.lhs.content

    def eval(self, calculator):
        self.create(calculator)

    def create(self, calculator, klass=Thing):
        bases, others = self.base_concepts.eval(calculator)

        indiviudal_name = self.lhs_name
        if bases:
            concept = bases[0]
            calculator[indiviudal_name] = concept(indiviudal_name)
            for concept in bases:
                calculator[indiviudal_name].is_a.append(concept)
        for other in others:
            calculator[indiviudal_name].is_a.append(other)


class ConceptDeclarationAction(DeclarationAction):

    def create(self, calculator, klass=Thing):
        bases, others = self.base_concepts.eval(calculator)
        concept_name = self.lhs_name
        if not bases:
            bases = (klass,)
        calculator[concept_name] = types.new_class(concept_name, bases=bases)
        for other in others:
            calculator[concept_name].is_a.append(other)


class RelationDeclarationAction(DeclarationAction):

    def create(self, calculator, klass=ObjectProperty):
        bases, others = self.base_concepts.eval(calculator)
        relation_name = self.lhs_name
        if not bases:
            bases = (klass,)
        calculator[relation_name] = types.new_class(concept_name, bases=bases)
        for other in others:
            calculator[relation_name].is_a.append(other)

class DefinitionAction(DeclarationAction):

    def create(self, calculator, klass=Thing):
        concept = self.concept.eval(calculator)
        concept_name = self.lhs_name
        if isinstance(self.concept, ConceptAction):
            calculator[self.concept_name] = self.concept
        else:
            bases = (klass,)
            calculator[self.concept_name] = types.new_class(self.concept_name, bases=bases)
            calculator[self.concept_name].equivalent_to.append(concept)


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
        return is_instance_of(individual, concept)

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


class MappingFormulaAction(FormulaAction):
    def eval(self, calculator):
        left, right = self.args
        return left >> right
