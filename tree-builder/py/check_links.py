#!/usr/bin/python3

import os
from glob import glob
import ntpath
 
from ft_utils import isClan, isPerson, NULL_LNK, CLAN_RE, tryRebaseLink, trySplitPathAtNode, extractPersonName
from ft_admin import findLinkTo
from osutils import BCKf, TMPf, islink, readlink_url, readlink_scut
from osutils import INTERNET_SCUT_SUFFIX, WINDOWS_SCUT_SUFFIX

STATUS_READERROR = 'X'
STATUS_REBASED   = 'R'
STATUS_GENGAP    = 'G'
STATUS_OK        = 'O'

def readLink(link):
    # We don't use osutils.readlink() here as it always returns
    # an absolute path. If the link is a relative symlink then
    # the resolved path, if it doesn't exist, will be confusing. We
    # need to return the relative path instead
    linkTgt = None
    try:
        if link.endswith(INTERNET_SCUT_SUFFIX):
            linkTgt = readlink_url(link)
        elif link.endswith(WINDOWS_SCUT_SUFFIX):
            linkTgt = readlink_scut(link)
        elif os.path.islink(link):
            linkTgt = os.readlink(link)
        else:
            raise ValueError("Unrecognised link @ %s" % (link))
    except:
        pass
    
    return linkTgt

def absTgtpath(link, linkTgt):
    if ntpath.isabs(linkTgt):
        return linkTgt
    else:
        lnkCwd = os.path.dirname(link)
        return os.path.normpath(os.path.join(lnkCwd, linkTgt))


class Link:
    def __init__(self, link, linkTgt):
        self.link = link
        self.linkTgt = linkTgt
        self.revisedLinkTgt = None
        self.status = "" if linkTgt is not None else STATUS_READERROR
        
class Backlink:
    def __init__(self, link1, linkTgt1, link2, linkTgt2):
        self.link1 = link1
        self.linkTgt1 = linkTgt1
        self.link2 = link2
        self.linkTgt2 = linkTgt2
        
              
class LinkAnalyser:
    def __init__(self, treeRoot, findings_file = None):
        self.treeRoot = os.path.abspath(treeRoot)
        self.clans = self.getValidClans(self.treeRoot)
        self.findings_file = findings_file
        if self.findings_file is not None:
            self.findings_file = os.path.abspath(self.findings_file)
    
    def getValidClans(self, treeRoot):
        clans = []
        for e in os.listdir(treeRoot):
            if isClan(e):
                clans.append(e)
        return clans
    
    def scanTree(self, resolver):
        bad_links = []
        
        for root, dirs, files in os.walk(self.treeRoot):
            files.extend(dirs) # linux ln to dir appear in dirs
            
            for f in files:
                if f.startswith(BCKf) or f.startswith(TMPf):
                    continue
                
                link = os.path.join(root, f)
                
                if not islink(link):
                    continue
                
                linkTgt = readLink(link)
                
                if linkTgt is None:
                    bad_links.append( Link(link, None) )
                    continue
                
                if linkTgt.endswith(NULL_LNK):
                    continue
                
                resolver(link, linkTgt, bad_links)
                
        return bad_links
    
    def resolver(self, link, linkTgt, bad_links):
        lnk = Link(link, linkTgt)
        
        origTgt_abs = absTgtpath(lnk.link, lnk.linkTgt)
        
        if os.path.exists(origTgt_abs):
            # Link exists: check that it is pointing to something
            # within (under) the tree
            if origTgt_abs.find(self.treeRoot) != 0:
                bad_links.append(lnk)
            return
        
        tgt = lnk.linkTgt
        newTgt = tryRebaseLink(tgt, self.treeRoot, validClans=self.clans)
        # If the link can't be rebased then there's no further 'fixes' we can do
        if newTgt is None:
            bad_links.append(lnk)
            return
        
        # See if we've actually changed the link at all
        newTgt = os.path.normpath(newTgt)            
        if newTgt != origTgt_abs: 
            lnk.status += STATUS_REBASED
            
        tgt = newTgt # abs path
            
        if not os.path.exists(tgt):
            newTgt = self.tryGenGap(lnk.link, tgt)
            if newTgt is not None:
                tgt = newTgt
                lnk.status += STATUS_GENGAP
                
        if os.path.exists(tgt):
            lnk.status += STATUS_OK
        
        # If the original link was relative then make the revised one too
        if not ntpath.isabs(lnk.linkTgt):
            tgt = os.path.relpath(tgt, os.path.dirname(lnk.link))
                        
        if tgt != lnk.linkTgt:
            lnk.revisedLinkTgt = tgt
             
        bad_links.append(lnk)
        
    def tryGenGap(self, link, linkTgt):
        headtail = trySplitPathAtNode(linkTgt, CLAN_RE, nodeInHead=False)
        if headtail is None:
            #print("ERROR: failed to find clan node")
            return None
        
        pth = headtail[1].split(os.sep)
        clan = pth[0]
        
        # check that clan exists
        if not clan in self.clans:
            #print("ERROR: clan %s doesn't exist" % (clan))
            return None
        
        # Make up glob pattern: insert a wildcard node        
        pth.insert(1, '*')
        pth = os.path.join(self.treeRoot, *pth) # absolute path
        
        # If we get exactly ONE glob match, we assume that it's a
        # generation gap that's now plugged
        matches = glob(pth)
        if len(matches) == 1:
            newTgt = matches[0]
            return newTgt
        
        return None
    
    def resolver_backlink(self, link, linkTgt, bad_links): 
        linkTgt_abs = absTgtpath(link, linkTgt)
        
        if not os.path.exists(linkTgt_abs):
            # Quietly skip
            return
        
        path = os.path.dirname(link)
        if not os.path.isdir(path):
            return
        
        tmp = path.split(os.sep)
        if not isPerson(tmp[-1]):
            return
        
        tmp = linkTgt_abs.split(os.sep)
        if not isPerson(tmp[-1]):
            return
        
        # Go to the linkTgt_abs directory and look for a link which has
        # path as its target
        if not findLinkTo(path, linkTgt_abs):
            clan, name = extractPersonName(path)
            # We can't determine sex here hence the 'p.'
            newLink = os.path.join(linkTgt_abs, 'p. %s %s' % (name.capitalize(), clan.capitalize()))
            
            # Make the new link relative if the original one was
            if not ntpath.isabs(linkTgt):
                path = os.path.relpath(path, os.path.dirname(newLink))
            
            bad_links.append( Backlink(link, linkTgt, newLink, path) )
    
    def analyse(self, backlinks=False):
        resolver = self.resolver if (not backlinks) else self.resolver_backlink
        bads = self.scanTree(resolver)
        
        if (len(bads) > 0):
            reportTxt = "Found %d bad links" % (len(bads))
            
            if (self.findings_file is not None):
                with open(self.findings_file, 'w') as fs:
                    self.outputFindings(fs, bads)
                reportTxt += " (report is in '%s')" % (self.findings_file)
        else:
            reportTxt = "All links are OK"
                
        print(reportTxt)

    def outputFindings(self, fs, bads):
        cantread = []
        resolved = []
        unresolved = []
        backlink = []
        
        for lnk in bads:
            if isinstance(lnk, Backlink):
                backlink.append(lnk)
            elif lnk.status.find(STATUS_READERROR) != -1:
                cantread.append(lnk)
            elif lnk.status.find(STATUS_OK) != -1:
                resolved.append(lnk)
            else:
                unresolved.append(lnk)
          
        if len(cantread) > 0:
            fs.write('# The following links could not be read\n')
            fs.write('# You need to correct these manually\n')
            for lnk in cantread:
                fs.write("CantRead('%s')\n" % (lnk.link))
            fs.write('\n\n')
                
        if len(resolved) > 0:
            fs.write('# The following links have been repaired\n')
            for lnk in resolved:
                fs.write("Auto(r\"%s\",\n" % (lnk.link))
                fs.write("     r\"%s\",\n" % (lnk.linkTgt))
                fs.write("     r\"%s\",\n" % (lnk.revisedLinkTgt))
                fs.write("     \"%s\")\n" % (lnk.status))
            fs.write('\n\n')
            
        if len(unresolved) > 0:
            fs.write('# It has not been possible to repair the following links.\n')
            fs.write('# (partial fixes may have been applied)\n')
            for lnk in unresolved:
                fs.write("Man(r\"%s\",\n" % (lnk.link))
                fs.write("    r\"%s\",\n" % (lnk.linkTgt))
                fs.write("    r\"%s\",\n" % (lnk.revisedLinkTgt))
                fs.write("    \"%s\")\n" % (lnk.status))
            fs.write('\n\n')
            
        if len(backlink) > 0:
            fs.write('# The following links are missing\n')
            for lnk in backlink:
                fs.write("Backlink(r'%s',\n" % (lnk.link1))
                fs.write("         r'%s',\n" % (lnk.linkTgt1))
                fs.write("         r'%s',\n" % (lnk.link2))
                fs.write("         r'%s')\n" % (lnk.linkTgt2))
            fs.write('\n\n')
            