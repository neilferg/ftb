#!/usr/bin/python3

import sys, os
from shutil import copytree, copy
from subprocess import check_call

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(THIS_DIR, '../../tree-builder/py'))

from osutils import makelink, makelink_url, islink, getLinkSuffix, rm_rf


ml_link_is_url = (os.name != 'posix')
#ml_link_is_url = True

def create_marriage_link(tgt, lnk):
    if ml_link_is_url:
        mklnk = makelink_url
    else:
        tgt = os.path.relpath(tgt, os.path.dirname(lnk))
        mklnk = os.symlink
    
    suffix = getLinkSuffix(mklnk)
    
    lnk += suffix
    
    mklnk(tgt, lnk)
        

class Test1:
    def __init__(self):
        self.buildDir = os.path.join(THIS_DIR, 'build')
        
        self.links = [           
            # link (will be created/deleted -> target
            ('tree/BAMPOT/Bob/w. Elizabeth Smith',          'tree/SMITH/Elizabeth'),
            ('tree/SMITH/Elizabeth/h. Bob Bampot',          'tree/BAMPOT/Bob'),
            
            ('tree/BAMPOT/Bob/Dave/p. Christina Swindle',   None),
            
            ('tree/BAMPOT/Bob/Jane/h. Baz Clan_Baremin',    'tree/CLAN_FOO/Bar/Baz'),
            ('tree/CLAN_FOO/Bar/Baz/w. Jane Bampot',        'tree/BAMPOT/Bob/Jane'),
        ]
        
    def setup(self):
        self.cleanup()
        
        # System template
        copytree(os.path.join(THIS_DIR, '../../templates/NewTree'), self.buildDir, symlinks=True)
        treeDir = os.path.join(self.buildDir,'tree')
        
        # Test data template (clans)
        treeData = os.path.join(THIS_DIR, 'tree')
        for e in os.listdir(treeData):
            p = os.path.join(treeData, e)
            if os.path.isdir(p):
                copytree(p, os.path.join(treeDir,e))
            else:
                copy(p, treeDir)
                
        # Create marriage links    
        for lnk, tgt in self.links:
            lnk = os.path.abspath(os.path.join(self.buildDir, lnk))
            if tgt is None:
                tgt = '/tmp/null'
            else:
                tgt = os.path.abspath(os.path.join(self.buildDir, tgt))
            create_marriage_link(tgt, lnk)
            
        makelink('../../..', os.path.join(self.buildDir, 'ftb'))
        
        copy(os.path.join(THIS_DIR, '../../help.htm'), treeDir)
    
    def cleanup(self):
        rm_rf(self.buildDir)
        
    def execute(self):
        os.chdir(self.buildDir)
        check_call([sys.executable, 'build.py'])
    
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
