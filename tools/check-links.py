#!/usr/bin/python3

import os
import argparse

import pth; pth.setPythonpath()

from ft_utils import getTreeRoot
from ft_admin import listBadLinks, listBadLinks_help, BAD_CANTREAD, BAD_TGTNOEXIST, BAD_NOBACKLINK


def outputFindings(fs, bads):
    cantread = []
    tgtnoexist = []
    nobacklnk = []
    for caseType, lnk, tgt in bads:
        if caseType == BAD_CANTREAD:
            cantread.append(lnk)
        elif caseType == BAD_TGTNOEXIST:
            tgtnoexist.append( (lnk, tgt) )
        elif caseType == BAD_NOBACKLINK:
            nobacklnk.append( (lnk, tgt) )
      
    if len(cantread) > 0:
        fs.write('# The following links could not be read\n')
        fs.write('# You need to correct these manually\n')
        for lnk in cantread:
            fs.write("CantRead('%s')\n" % (lnk))
        fs.write('\n\n')
            
    if len(tgtnoexist) > 0:
        fs.write('# The following links have targets but they are pointing to\n')
        fs.write('# non-existent locations. An automated fix may be possible:\n')
        fs.write('# TgtNoExist() will check for rebasing the root and\n')
        fs.write('# attempt to plug a generation gap at the top of clan trees\n')
        for lnk, tgt in tgtnoexist:
            fs.write("TgtNoExist(r'%s',\n" % (lnk))
            fs.write("           r'%s')\n" % (tgt))
        fs.write('\n\n')
            
    if len(nobacklnk) > 0:
        fs.write('# A backlink is missing to a spouse\n')
        fs.write('# The 1st arg is the suggested link that needs to be created\n')
        fs.write('# this should be modified manually to indicate the relationship\n')
        fs.write("# i.e 'p.' -> 'h.' or 'w.'\n")
        fs.write('# NoBacklink() will then create the links\n')
        for lnk, tgt in nobacklnk:
            fs.write("NoBacklink(r'%s',\n" % (lnk))
            fs.write("           r'%s')\n" % (tgt))
        fs.write('\n\n')

def analyse(treeRoot, findings_file):
    findings_file = os.path.abspath(findings_file)
    print("Tree-root is:", treeRoot)
    listBadLinks_help()
    print()
    
    bads = listBadLinks(treeRoot)
    
    if (len(bads) > 0) and (findings_file is not None):
        with open(findings_file, 'w') as fs:
            outputFindings(fs, bads)
            
    print()
    if len(bads) > 0:
        print("Found %d bad links (report is in '%s')" % (len(bads), findings_file))
    else:
        print("All links are OK")
         
           
parser = argparse.ArgumentParser(description='Check Links')

# Optional parameters
parser.add_argument('-f', '--findings', type=str, default='findings',
                    help='Filename where findings will be written')

# The positional parameter optionally specifies the tree-root
parser.add_argument('treeroot', metavar='treeroot', type=str, nargs='?',
                    help='Tree Root (default search cwd)')

args = parser.parse_args()

treeRoot = args.treeroot
if treeRoot is None:
    treeRoot = getTreeRoot()
    
analyse(treeRoot, args.findings)
