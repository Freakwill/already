#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""PEG for description logics

names of atomic concepts start with a captial letter,
names of individuals start with a lower letter

An atomic concepts are concepts
~A, A|A, A & A, some r A, all r A, are concepts, where A is an concept

i:A, A=A, A<=A, A>=A, A<A, A>A are formulas

! i:A, ! A::B is declarations
! A:=B is a definition
"""

import pyparsing as pp
from actions import *
from calculators import *

concept = pp.Forward()

atomic_concept = pp.pyparsing_common.identifier('content')
atomic_concept.addParseAction(ConceptAction)

type_check = pp.Suppress(':') + atomic_concept('type')
individul = pp.pyparsing_common.identifier('content')
individul.addParseAction(IndividualAction)

individual_set = pp.Suppress('{') + pp.delimitedList(individul, ',') + pp.Suppress('}')
atomic_concept_ = atomic_concept | individual_set.addParseAction(IndividualSetAction)

atomic_relation = pp.pyparsing_common.identifier
quantifier = ((pp.Keyword('more') | pp.Keyword('less') | pp.Keyword('equal'))+pp.pyparsing_common.integer) \
| pp.Keyword('some') | pp.Keyword('only')
quantifier.addParseAction(QuantifierAction)
restriction = quantifier('quantifier') + atomic_relation('relation') + pp.Suppress('.')

r = restriction.parseString('only r. A')[0]

individul_variable = pp.Combine('$' + individul)('name') + pp.Optional(type_check)
concept_variable = pp.Combine('$' + atomic_concept)('name') + pp.Optional(type_check)

individul_variable.addParseAction(IndividualVariableAction)

opList = [('~', 1, pp.opAssoc.RIGHT, NegationAction), 
(restriction, 1, pp.opAssoc.RIGHT, RestrictionAction),
('&', 2, pp.opAssoc.LEFT, AndAction), ('|', 2, pp.opAssoc.LEFT, OrAction), ('^', 2, pp.opAssoc.LEFT, XorAction)]
concept = pp.infixNotation(atomic_concept_, opList)

concept_tuple = pp.delimitedList(concept, ',')('concepts')
concept_tuple.addParseAction(ConceptTupleAction)

individual_declaration = pp.Suppress('!') + individul + pp.Suppress(':') + concept_tuple
individual_declaration.addParseAction(DeclarationAction)
concept_declaration = pp.Suppress('!') + concept + pp.Suppress('::') + concept_tuple
concept_declaration.addParseAction(ConceptDeclarationAction)
definition = pp.Suppress('!') + concept + pp.Suppress(':=') + concept
definition.addParseAction(DefinitionAction) 

mapping_formula = concept + '->' + concept
mapping_formula.addParseAction(MappingFormulaAction)
relation_tuple = (atomic_relation | mapping_formula)
relation_declaration = pp.Suppress('!') + atomic_relation + pp.Suppress('::') + relation_tuple
relation_declaration.addParseAction(RelationDeclarationAction)

declaration = concept_declaration ^ definition ^ individual_declaration

containing_formula = individul + ':' + concept
containing_formula.addParseAction(ContainingFormulaAction)
compare = pp.oneOf(['<=', '>=', '==', '<', '>'])
comparison_formula = concept + compare + concept
comparison_formula.addParseAction(FormulaAction)
formula = comparison_formula ^ containing_formula


statement = declaration ^ formula

# question = concept + compare + concept + pp.Suppress('?')
# sentence = question ^ formula

statement_sequence = pp.delimitedList(statement, ';')
statement_sequence.addParseAction(StatementSequenceAction)


def parse(s:str):
    return statement_sequence.parseString(s)[0]

from owlready2 import *

calc=OwlreadyCalculator()
calc.set_constant('Thing', Thing)

onto = get_ontology("http://test.org/onto.owl")

with onto:
    r = parse("""
        ! I:: Thing;
        ! J:: I;
        ! i: I;
        ! R :: I -> J;
        """)
    print(r.eval(calc))
    print(calc.memory)
