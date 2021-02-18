#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""PEG for description logics

names of atomic concepts start with a captial letter,
names of individuals start with a lower letter

An atomic concepts are concepts
~A, A|A, A & A, some r A, all r A, are concepts, where A is an concept

i:A, A=A, A<=A, A>=A, A<A, A>A are formulas

let i:A, let A::B is declarations
let A:=B is a definition
"""

import pyparsing as pp
from actions import *
from calculators import *

concept = pp.Forward()

atomic_concept = pp.pyparsing_common.identifier('content')
atomic_concept.addParseAction(ConceptAction)

# type_check = pp.Suppress(':') + atomic_concept('content')
individul = pp.pyparsing_common.identifier('content')
individul.addParseAction(IndividualAction)

atomic_concept_ = atomic_concept | pp.Suppress('{') + pp.delimitedList(individul, ',') + pp.Suppress('}')

atomic_relation = pp.pyparsing_common.identifier
quantifier = (pp.Keyword('some') | pp.Keyword('only') | pp.Literal('>=') + pp.pyparsing_common.integer
| pp.Literal('<=')+pp.pyparsing_common.integer | pp.Literal('=')+pp.pyparsing_common.integer)
restriction = quantifier + atomic_relation + pp.Suppress('.')

individul_variable = '$' + individul
concept_variable = '$' + atomic_concept

opList = [('~', 1, pp.opAssoc.RIGHT, NegationAction), 
(restriction, 1, pp.opAssoc.RIGHT, RestrictionAction),
('&', 2, pp.opAssoc.LEFT, AndAction), ('|', 2, pp.opAssoc.LEFT, OrAction), ('^', 2, pp.opAssoc.LEFT, XorAction)]
concept = pp.infixNotation(atomic_concept_, opList)

declaration = pp.Keyword('let').suppress() + individul + pp.Suppress(':') + concept
declaration.addParseAction(DeclarationAction)
concept_declaration = pp.Keyword('let').suppress() + concept + pp.Suppress('::') + concept
concept_declaration.addParseAction(ConceptDeclarationAction)
definition = pp.Keyword('let').suppress() + concept + pp.Suppress(':=') + concept
definition.addParseAction(DefinitionAction) 


containing_formula = individul + ':' + concept
containing_formula.addParseAction(ContainingFormulaAction)
compare = pp.oneOf(['<=', '>=', '==', '<', '>'])
comparison_formula = concept + compare + concept
comparison_formula.addParseAction(FormulaAction)
formula = comparison_formula ^ containing_formula

statement = concept_declaration ^ definition ^ declaration ^ formula

question = concept + compare + concept + pp.Suppress('?')
sentence = question ^ formula

statement_sequence = pp.delimitedList(statement, ';')
statement_sequence.addParseAction(StatementSequenceAction)

# a=concept.parseString('B | C & D')
# print(a[0].eval(calc))

def parse(s:str):
    return statement_sequence.parseString(s)[0]

from owlready2 import *

calc=OwlreadyCalculator()
calc.set_constant('Thing', Thing)

onto = get_ontology("http://test.org/onto.owl")

with onto:
    r = parse('let Thing:: Thing; let i: Thing; let B :: Thing; let A :: Thing;let j: B; i:B; A | B<= Thing;')
    print(r.eval(calc))
    print(calc.memory)
