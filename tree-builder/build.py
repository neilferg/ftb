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
    
    copy(os.path.join(JSLIB, 'jquery-1.6.4.js'),      os.path.join(JSOUT, 'jquery.js'))
    copy(os.path.join(JSLIB, 'jquery.maphilight.js'), JSOUT)
    copy(os.path.join(JSLIB, 'wz_jsgraphics.js'),     JSOUT)
    
    ftb_pre = os.path.join(JSOUT, 'ftb-predom.js')
    copy(               os.path.join(JSSRC, 'ftb-predom.js'), ftb_pre)
    #copy(               os.path.join(JSSRC, 'iframe_resizer.js'), ftb_pre)
    #copyappend(ftb_pre, os.path.join(JSSRC, 'ftb-predom.js'))
    
    ftb_post = os.path.join(JSOUT, 'ftb-postdom.js')
    copy(                 os.path.join(JSLIB, 'jquery-1.6.4.js'), ftb_post) # for picbox
    copyappend(ftb_post, os.path.join(PICBOX,'js', 'picbox.js'))
    #copyappend(ftb_post, os.path.join(JSSRC, 'ftb-encrypt.js'))
    copyappend(ftb_post, os.path.join(JSSRC, 'iframe_resizer.js'))
    copyappend(ftb_post, os.path.join(JSSRC, 'ftb-postdom.js'))
     
    copy(os.path.join(JSSRC, 'search.js'),            JSOUT)
    copy(os.path.join(JSSRC, 'treegraph_hilight.js'), JSOUT)

def build():
    clean()
    buildHelp()
    buildImages()
    buildCss()
    buildJs()
    
##
    
build()
