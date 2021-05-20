#!/usr/bin/python3

import sys, os
from subprocess import check_call

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(THIS_DIR, '../../tree-builder/py'))

from osutils import makelink_url, makelink_scut, getLinkSuffix, rm_rf
from ft_utils import TREE_NODE, extractPersonName, getLinkMaker

ftb = os.path.normpath(os.path.join(THIS_DIR,'..','..','tree-builder','py','ftb.py'))

check_links = [ sys.executable, ftb, 'chklinks' ]
fix_links = [ sys.executable, ftb, 'fixlinks' ]

def runin(cmd, dir):
    cwd = os.getcwd()
    os.chdir(dir)
    try:
        check_call(cmd)
    finally:
        os.chdir(cwd)
        
   
class Tree:
    def __init__(self, treeRoot, linkMaker = makelink_url, absLinks = False):
        self.treeRoot = treeRoot
        self.mklnk = linkMaker
        self.absLinks = absLinks
        
        if self.mklnk is makelink_url:
            absLinks = True
        self.lnk_suffix = getLinkSuffix(self.mklnk)

    def create_spouse_link(self, lnk, tgt): 
        lnk += self.lnk_suffix
        
        if not self.absLinks:
            tgt = os.path.relpath(tgt, os.path.dirname(lnk))
        
        self.mklnk(tgt, lnk)       
    

class Person:
    def __init__(self, tree, personPath):
        self.tree = tree
        self.fullPath = os.path.join(self.tree.treeRoot, personPath)
        os.makedirs(self.fullPath)
        
    def marry(self, other, rel='s'):
        if rel == 'w':
            me_rel = 'h'
        elif rel == 'h':
            me_rel = 'w'
        else:
            me_rel = 's'
            
        me_name    = extractPersonName(self.fullPath)
        other_name = extractPersonName(other.fullPath)
        
        me_to_other_lnk = os.path.join(self.fullPath,rel+'. '+other_name[1]+' '+other_name[0])
        other_to_me_lnk = os.path.join(other.fullPath,me_rel+'. '+me_name[1]+' '+me_name[0])
                
        self.tree.create_spouse_link(me_to_other_lnk, other.fullPath)
        self.tree.create_spouse_link(other_to_me_lnk, self.fullPath)


class Test1:
    def __init__(self):
        self.buildDir = os.path.join(THIS_DIR, 'build')
        
        self.origTree = os.path.join(self.buildDir, 'original')
        self.gappedTree = os.path.join(self.buildDir, 'gapped')
        self.fixedTree = os.path.join(self.buildDir, 'fixed')
        
    def setup(self):
        self.cleanup()

    def makeTree(self, dir, CLAN, head, head_p1=''):
        tp = Tree(os.path.join(dir, TREE_NODE), getLinkMaker(None), absLinks = False)
        
        dave = Person(tp, os.path.join(CLAN,   head, head_p1,'Dave'))
        jane = Person(tp, os.path.join('CLAN2','Baz','Jane'))
        
        dave.marry(jane, 'w')

    def gapTree(self, tree, CLAN, newHead, oldHead):
        clanDir = os.path.join(tree,'tree',CLAN)
        
        # Move the current clan head to a temp
        os.rename(os.path.join(clanDir, oldHead), os.path.join(clanDir, '_t'))
        # Create the new head (dir)
        os.mkdir(os.path.join(clanDir, newHead))
        # Move the old head (the temp) to be under the new head
        os.rename(os.path.join(clanDir, '_t'), os.path.join(clanDir, newHead,oldHead))
        
    def cleanup(self):
        rm_rf(self.buildDir)
        
    def execute(self):
        CLAN = 'CLAN1'
        origHead = 'Bob'
       
        self.makeTree(self.origTree, CLAN, origHead)
        treeDir = os.path.join(self.origTree, TREE_NODE)
        
        print("> Checking origTree - should have no bad links")
        cmd = check_links
        runin(cmd, treeDir)
        
        rm_rf(self.origTree)
        
        # --------
        
        newHead = 'William'
        
        self.makeTree(self.gappedTree, CLAN, origHead)
        self.gapTree(self.gappedTree, CLAN, newHead, origHead)
        treeDir = os.path.join(self.gappedTree, TREE_NODE)
        
        # relative links: both (2) links will be bad
        # absolute links: 1 bad link
        print("> Checking gappedTree - should have 2 bad links")
        cmd = check_links
        runin(cmd, treeDir)
        
        cmd = fix_links
        cmd.append('findings')
        runin(cmd, treeDir)
        
        #  -------------------
        
        print("> Checking gappedTree after fixing - should have no bad links")
        cmd = check_links
        runin(cmd, treeDir)
        
        self.makeTree(self.fixedTree, CLAN, newHead, origHead)
     
    def run(self):
        try:
            self.setup()
            self.execute()
        except:
            raise
        finally:
            pass #self.cleanup()
                
##

Test1().run()
