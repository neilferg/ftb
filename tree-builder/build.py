#!/usr/bin/python3

from shutil import copy, copytree
import os, sys

try:
    from jsmin import jsmin
except:
    def jsmin(txt):
        return txt
        
THIS_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(THIS_DIR, 'py'))

from osutils import rm_rf

DIST = os.path.join(THIS_DIR,'..','dist')

CSSOUT = os.path.join(DIST,'css')
CSSSRC = os.path.join(THIS_DIR,'css')

IMGOUT = os.path.join(DIST,'images')
IMGSRC = os.path.join(THIS_DIR,'images')

JSOUT = os.path.join(DIST,'js')
JSLIB = os.path.join(THIS_DIR,'..','lib-js')
JSSRC = os.path.join(THIS_DIR,'js')

HELPOUT = os.path.join(DIST,'help')
HELPSRC = os.path.join(THIS_DIR,'..','help')

PICBOX = os.path.join(THIS_DIR,'..','lib-js','picboxjs')
        
def copyappend(base, append):
    with open(base, 'ab') as fout:
        with open(append, 'rb') as fin:
            data = fin.read()
        fout.write(data)
        
def clean():
    rm_rf(DIST)

def buildHelp():
    copytree(HELPSRC, HELPOUT)

def concat(opFile, files):
    for i, f in enumerate(files):
        if i == 0:
            copy(f, opFile)
        else:
            copyappend(opFile, f)
    
def buildImages():
    copytree(IMGSRC, IMGOUT)
    copy(os.path.join(PICBOX,'images', 'picbox-closebutton.png'),  IMGOUT)
    copy(os.path.join(PICBOX,'images', 'picbox-loading.gif'),      IMGOUT)
    copy(os.path.join(PICBOX,'images', 'picbox-navbtns.png'),      IMGOUT)

def buildCss():
    os.makedirs(CSSOUT)
    copy(os.path.join(CSSSRC, 'ftb.css'),       CSSOUT)
    copyappend(os.path.join(CSSOUT, 'ftb.css'), os.path.join(PICBOX, 'css', 'picbox.css'))

def buildJs():
    os.makedirs(JSOUT)
    
    concat(os.path.join(JSOUT, 'ftb-predom.js'),
           [ os.path.join(JSSRC, 'iframe_resizer.js'),
             os.path.join(JSSRC, 'ftb-predom.js'),
           ])
    
    concat(os.path.join(JSOUT, 'ftb-postdom.js'),
           [ os.path.join(JSLIB, 'jquery-1.6.4.js'), # for picbox
             os.path.join(PICBOX,'js', 'picbox.js'),
             os.path.join(JSSRC, 'ftb-encrypt.js'),
             #os.path.join(JSSRC, 'iframe_resizer.js'),  # in predom
             os.path.join(JSSRC, 'ftb-common.js'),
             os.path.join(JSSRC, 'ftb-postdom.js'),
           ])
     
    copy(os.path.join(JSSRC, 'search.js'),            JSOUT)

    concat(os.path.join(JSOUT, 'ftb-tree-postdom.js'),
           [ os.path.join(JSLIB, 'jquery-1.6.4.js'),
             os.path.join(JSLIB, 'jquery.maphilight.js'),
             os.path.join(JSLIB, 'wz_jsgraphics.js'),
             os.path.join(JSSRC, 'treegraph_hilight.js'),
             os.path.join(JSSRC, 'ftb-common.js'),
             os.path.join(JSSRC, 'ftb-encrypt.js'),
             os.path.join(JSSRC, 'ftb-tree-postdom.js'),
           ])

def build():
    clean()
    buildHelp()
    buildImages()
    buildCss()
    buildJs()
    
##
    
build()
