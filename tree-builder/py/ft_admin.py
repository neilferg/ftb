import os
from fnmatch import fnmatch

from osutils import islink, readlink
from osutils import INTERNET_SCUT_SUFFIX, WINDOWS_SCUT_SUFFIX, BCKf, TMPf
from osutils import readlink_url, readlink_scut

from ft_utils import AUTOGEN_FILES, NULL_LNK
from ft_utils import extractPersonName


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


BAD_CANTREAD   = 0
BAD_TGTNOEXIST = 1
BAD_NOBACKLINK = 2

def listBadLinks_help():
    print("key: l -> tgt : link <l> pointing to target <tgt>")
    print("        [...] : path doesn't exist")

def _addBad(bads, casetype, lnk, tgt):
    bads.append( (casetype, lnk, tgt) )    
    if casetype == BAD_CANTREAD:
        print("CantRead:   %s -> [???]" % (lnk))
    elif casetype == BAD_TGTNOEXIST:
        print("TgtNoExist: %s -> [%s]" % (lnk, tgt))
    elif casetype == BAD_NOBACKLINK:
        print("NoBackLink: [%s] -> %s" % (lnk, tgt))

def listBadLinks(treeRoot):
    bads = []
    treeRoot = os.path.abspath(treeRoot)
    for root, dirs, files in os.walk(treeRoot):
        files.extend(dirs) # linux ln to dir appear in dirs
        
        for f in files:
            if f.startswith(BCKf) or f.startswith(TMPf):
                continue
            
            linkName = os.path.join(root, f)
            
            if not islink(linkName):
                continue
            
            # We don't use osutils.readlink() here as it always returns
            # an absolute path. If the link is a relative symlink then
            # the resolved path, if it doesn't exist, will be confusing. We
            # need to return the relative path instead
            try:
                if linkName.endswith(INTERNET_SCUT_SUFFIX):
                    linkTgt = readlink_url(linkName)
                elif linkName.endswith(WINDOWS_SCUT_SUFFIX):
                    linkTgt = readlink_scut(linkName)
                elif os.path.islink(linkName):
                    linkTgt = os.readlink(linkName)
                else:
                    raise ValueError("Unrecognised link @ %s" % (linkName))
            except:
                _addBad(bads, BAD_CANTREAD, linkName, None)
                continue
            
            if linkTgt.endswith(NULL_LNK):
                continue
            
            # Get the target's absolute path (wrt the linkName's parent directory)
            if not os.path.isabs(linkTgt):
                lnkCwd = os.path.dirname(linkName)
                linkTgt_abs = os.path.join(lnkCwd, linkTgt)
            else:
                linkTgt_abs = linkTgt
         
            if not os.path.exists(linkTgt_abs):
                _addBad(bads, BAD_TGTNOEXIST, linkName, linkTgt)
                continue
            
            if 0:
                path = root
                if os.path.isdir(linkTgt_abs) and not findLinkTo(path, linkTgt_abs):
                    clan, name = extractPersonName(path)
                    # We can't determine sex here hence the 'p.'
                    expLnk = os.path.join(linkTgt_abs, 'p. %s %s' % (name.capitalize(), clan.capitalize()))
                    _addBad(bads, BAD_NOBACKLINK, expLnk, path)
                
    return bads

def findLinkTo(path, inDir):
    '''Search <inDir> looking for a link that has <path> as its target'''
    
    for f in os.listdir(inDir):
        f = os.path.join(inDir, f)
        
        if not islink(f):
            continue
        
        try:
            linkTgt = readlink(os.path.join(inDir, f))
        except ValueError:
            continue
            
        if linkTgt == path:
            return True
        
    return False
