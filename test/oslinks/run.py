#!/usr/bin/python3

import sys, os

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(THIS_DIR, '../../tree-builder/py'))

from osutils import makelink_scut, readlink, rm_rf


class Test1:
    def __init__(self):
        self.buildDir = os.path.join(THIS_DIR, 'build')
        
    def setup(self):
        self.cleanup()
        os.makedirs(self.buildDir)
        
    def cleanup(self):
        rm_rf(self.buildDir, ignore_errors=True)
        
    def execute(self):
        linkName = os.path.join(self.buildDir, "here")
        
        # must use windows '\'
        tgt = r"C:\Users\neilferg\Documents\scut"
        
        makelink_scut(tgt, linkName)
        
        print(readlink(linkName+'.lnk'))
           
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
