#!/usr/bin/python3

import os, sys

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(THIS_DIR,'..','..','..','ft','tree-builder','py'))

from osutils import rm_rf
from ft_export import Exporter


srcRoot = THIS_DIR
exportDir = os.path.join(THIS_DIR, 'exported')

rm_rf(exportDir)
os.makedirs(exportDir, exist_ok=True)

Exporter(srcRoot).export(exportDir)
