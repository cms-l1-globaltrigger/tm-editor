Cuts
====

Overview of cut types and usage.

======  ======  ========  =====  ====  =====  =====
Object  Type    Name      Range  Data  Scale  Notes
======  ======  ========  =====  ====  =====  =====
MU      ETA     MU-ETA    yes    no    yes
MU      PHI     MU-PHI    yes    no    yes
MU      ISO     MU-ISO    no     yes   no
MU      QLTY    MU-QLTY   no     yes   no
MU      CHG     MU-CHG    no     yes   no
EG      ETA     EG-ETA    yes    no    yes
EG      PHI     EG-PHI    yes    no    yes
EG      ISO     EG-ISO    no     yes   no
EG      QLTY    EG-QLTY   no     yes   no
JET     ETA     JET-ETA   yes    no    yes
JET     PHI     JET-PHI   yes    no    yes
JET     QLTY    JET-QLTY  no     yes   no
TAU     ETA     TAU-ETA   yes    no    yes
TAU     PHI     TAU-PHI   yes    no    yes
TAU     ISO     TAU-ISO   no     yes   no
TAU     QLTY    TAU-QLTY  no     yes   no
ETM     PHI     ETM-PHI   yes    no    yes
HTM     PHI     HTM-PHI   yes    no    yes
COMB    CHGCOR  CHGCOR    no     yes   no
DIST    DETA    DETA      yes    no    (yes)  ranges validated at assignment
DIST    DPHI    DPHI      yes    no    (yes)  ranges validated at assignment
DIST    DR      DR        yes    no    (yes)  ranges validated at assignment
MASS    MASS    MASS      yes    no    (yes)  not specified yet
======  ======  ========  =====  ====  =====  =====

Parsing cuts
------------

In order to extract cuts from an algorithm expression, you have to make use of
the ``tmGrammar.Object_parser`` and ``tmGrammar.FunctionParser`` static functions.

This functions populate a previously created struct with an attribute *cuts*
holding the assigned cuts as tmTable.Row instances.

>>> import tmGrammar
>>> o = tmGrammar.Object_Item()
>>> if not tmGrammar.Object_parser(token, o):
>>>     raise ValueError(token)
>>> print o.cuts
