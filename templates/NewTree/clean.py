#!/usr/bin/python3

import sys, os
import argparse

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(THIS_DIR, 'ftb/tree-builder/py'))

from ft_utils import TREE_NODE
from ft_admin import cleanupfiles

parser = argparse.ArgumentParser(description='Clean up')

# Optional parameters
parser.add_argument('-d', '--dryrun', action="store_true", default=False,
                    help='Not for real')

args = parser.parse_args()

tree = os.path.join(THIS_DIR, TREE_NODE)
cleanupfiles(tree, dryrun = args.dryrun)
