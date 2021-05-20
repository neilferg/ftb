import os, sys

THIS_DIR = os.path.abspath(os.path.dirname(__file__))

def setPythonpath():
    paths = [ os.path.join(THIS_DIR,'..','tree-builder','py'),
            ]
    
    for p in paths:
        if not p in sys.path:
            sys.path.append(p)
