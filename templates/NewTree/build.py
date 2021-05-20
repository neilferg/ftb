#!/usr/bin/python3

import os, sys

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(THIS_DIR, 'ftb/tree-builder/py'))

import ft_build

PROJ_ROOT = THIS_DIR
TREE_ROOT = os.path.join(PROJ_ROOT, 'tree')
pf = ft_build.initAndScan(TREE_ROOT)

ft_build.MakeWeb(pf).make()

print("DONE!")
