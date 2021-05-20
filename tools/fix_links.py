#!/usr/bin/python3

import argparse
import os
import ntpath
from glob import glob

import pth; pth.setPythonpath()

from ft_utils import getTreeRoot, trySplitPathAtNode, CLAN_RE, tryRebaseLink, makelink_withbck
from osutils import INTERNET_SCUT_SUFFIX, WINDOWS_SCUT_SUFFIX, makelink_url


class Fixer:
    def __init__(self, dryrun, genlvl):
        self.init = False
        self.dryrun = dryrun
        self.genlvl = genlvl
        print("dryrun=%s, genlvl=%d" % (self.dryrun, self.genlvl))
        
    def getTreeRoot(self, lnk):
        treeRoot = getTreeRoot(lnk)
        if not os.path.exists(treeRoot):
            raise Exception("Treeroot doesn't exist '%s'" % (treeRoot))
        return treeRoot
        
    def tryToFix(self, findings_file):
        map = {
            'CantRead': self.CantRead,
            'TgtNoExist': self.TgtNoExist,
            'NoBacklink': self.NoBacklink,
        }
        
        exec(compile(open(findings_file, "rb").read(), findings_file, 'exec'), map)
        
    def getLinkMaker(self, existingLnk):
        if existingLnk.endswith(INTERNET_SCUT_SUFFIX):
             return makelink_url
        elif existingLnk.endswith(WINDOWS_SCUT_SUFFIX):
             return makelink_scut(linkName)
        elif os.path.islink(existingLnk):
             return os.symlink
        else:
             raise Exception("Unsupported link type '%s'" % (existingLnk))
     
    def CantRead(self, tgt):
        pass
        
    def TgtNoExist(self, lnk, tgt):
        treeRoot = getTreeRoot(lnk)

        mklnk = self.getLinkMaker(lnk)

        info = "not resolved"
        resolvedTgt = self.TgtNoExist_tryRebase(treeRoot, lnk, tgt)
        if resolvedTgt is not None:
            info = "rebased"
            
        if resolvedTgt is None:
            resolvedTgt = self.TgtNoExist_tryGengap(treeRoot, lnk, tgt)
            if resolvedTgt is not None:
                info = "gengap plugged"
            
        if resolvedTgt is None:
            print("ERROR: failed to fix", tgt)
            return
        
        print(lnk, info)
        print("    old:", tgt, "-> new:", resolvedTgt)
        
        makelink_withbck(resolvedTgt, lnk, mklnk, dryrun=self.dryrun)
        
    def TgtNoExist_tryRebase(self, treeRoot, lnk, tgt):
        rebased = tryRebaseLink(tgt, treeRoot)
        if (rebased is not None) and os.path.exists(rebased):
            if not ntpath.isabs(tgt):
                rebased = os.path.relpath(rebased, os.path.dirname(lnk))
            return rebased
        
        return None

    # tryGengap will also rebase, but using the CLAN node instead of TREE node
    def TgtNoExist_tryGengap(self, treeRoot, lnk, tgt):
        headtail = trySplitPathAtNode(tgt, CLAN_RE, nodeInHead=False)
        if headtail is None:
            print("ERROR: failed to find clan node")
            return None
        
        pth = headtail[1].split(os.sep)
        clan = pth[0]
        # check that clan exists
        if not os.path.exists(os.path.join(treeRoot, clan)):
            print("ERROR: clan %s doesn't exist" % (clan))
            return None
        
        # check that only one person at clan head
        # (can override to omit this check)
        
        # Make up glob pattern: insert a wildcard node
        if len(pth) < self.genlvl:
            print("ERROR: not enough generations")
            return None
        
        pth.insert(self.genlvl, '*')
        pth = os.path.join(treeRoot, *pth) # absolute path
        
        # If we get exactly ONE glob match, we assume that it's a
        # generation gap that's now plugged
        matches = glob(pth)
        if len(matches) == 1:
            newTgt = matches[0]
            if not ntpath.isabs(tgt):
                newTgt = os.path.relpath(newTgt, os.path.dirname(lnk))
            return newTgt
        
        return None

    def NoBacklink(self, lnk, tgt):
        print("NoBacklink", lnk, tgt, self.init)
        

parser = argparse.ArgumentParser(description='Fix Links')

# Optional parameters
parser.add_argument('-d', '--dryrun', action="store_true", default=False,
                    help='Not for real')
parser.add_argument('-g', '--genlvl', type=int, default=1,
                    help='Generation level (1=clan head default)')

# The positional parameter specifies the findings file
parser.add_argument('findings_file', metavar='findings_file', type=str, nargs=1,
                    help='Findings file (from previous check)')

args = parser.parse_args()

fixer = Fixer(args.dryrun, args.genlvl)

fixer.tryToFix(args.findings_file[0])
