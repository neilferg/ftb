import os
from fnmatch import fnmatch
from shutil import copy

from osutils import islink, readlink_f, makelink
from ft_utils import AUTOGEN_FILES, TREE_NODE
from ft_bond import bond, PartnerLink


def isAutogenFile(d, f):
    for e in AUTOGEN_FILES:
        if fnmatch(f, e):
            return os.path.join(d, f)
    
    return None
       
def cleanupfiles(rootdir, dryrun = False, predicate = isAutogenFile):
    for root, dirs, files in os.walk(rootdir):
        files.extend(dirs)
        
        for f in files:
            f = predicate(root, f)
            if f is not None:
                if dryrun:
                    print("rm %s" % (f))
                else:
                    os.remove(f)

def findLinkTo(path, inDir):
    '''Search <inDir> looking for a link that has <path> as its target'''
    
    for f in os.listdir(inDir):
        f = os.path.join(inDir, f)
        
        if not islink(f):
            continue
        
        try:
            linkTgt = readlink_f(os.path.join(inDir, f))
        except ValueError:
            continue
            
        if linkTgt == path:
            return True
        
    return False

def add_exampleTree(treeNode, treeTempl):
    for root, dirs, files in os.walk(treeTempl):
        for d in dirs:
            dst = os.path.join(root,d)
            dst = os.path.relpath(dst, treeTempl)
            dst = os.path.join(treeNode,dst) 
            os.makedirs(dst, exist_ok=True)
            
        for f in files:
            if f == '.keep':
                continue
            
            src = os.path.join(root,f)
            dst = os.path.relpath(src, treeTempl)
            dst = os.path.join(treeNode,dst)
            if not os.path.exists(dst):
                copy(src, dst)
              
    bond(os.path.join(treeNode,'SMITH/William/Elizabeth'), PartnerLink.REL_WIFE, quiet=True,
         me_path=os.path.join(treeNode,'BAMPOT/Bob'))
    
    bond(os.path.join(treeNode,'BAREMIN/John/Agnes'), PartnerLink.REL_WIFE, quiet=True,
         me_path=os.path.join(treeNode,'BAMPOT/Bob/Dave'))
    
def _addRegen(projDir):
    script = '''#!/usr/bin/python3
import sys, os
sys.path.append('/opt/ftb/tree-builder/py')
from ft_utils import TREE_NODE
import ftb

os.chdir(os.path.join(os.path.dirname(__file__),TREE_NODE))
ftb.cli(['build'])
'''
    f = os.path.join(projDir, 'BUILD.py')
    with open(f, 'w') as fs:
        fs.write(script)    
    os.chmod(f, 0o775)
        
def init_new(projDir='.', allowNonEmpty=False, addExample=False):
    projDir = os.path.abspath(projDir)
    os.makedirs(projDir, exist_ok=True)
    
    if (len(os.listdir(projDir)) != 0) and (not allowNonEmpty):
        raise Exception("Project directory %s is not empty" % (projDir))
    
    d = os.path.dirname(__file__)
    FTB = os.path.abspath(os.path.join(d,'..','..'))
    TEMPL = os.path.join(FTB,'templates','NewTree')
    
    treeNode = os.path.join(projDir,TREE_NODE)
            
    os.makedirs(os.path.join(treeNode,'_null'), exist_ok=True)
    
    INDEX = os.path.join(TEMPL,'index.html')
    index = os.path.join(treeNode,'index.html')
    if not os.path.exists(index):
        copy(INDEX, index)
      
    HELP_INDEX = os.path.join(FTB,'help.htm')
    help_index = os.path.join(treeNode,'help.htm')
    if not os.path.exists(help_index):
        copy(HELP_INDEX, help_index)
        
    ftb = os.path.join(projDir,'ftb')
    if not os.path.exists(ftb):
        makelink(FTB, ftb)
        
    README = '''To build the html navigator:
    cd tree
    ftb build
'''
    readme = os.path.join(projDir,'README.txt')
    if not os.path.exists(readme):
        with open(readme, 'w') as fs:
            fs.write(README)
            
    _addRegen(projDir)
            
    if addExample:
        add_exampleTree(treeNode, os.path.join(TEMPL,'example'))
            
