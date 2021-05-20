import os
import ntpath
import re

from osutils import islink, readlink, BCKf, TMPf, getLinkSuffix
from osutils import stripKnownSuffixes, INTERNET_SCUT_SUFFIX, WINDOWS_SCUT_SUFFIX
  
TREE_NODE = "tree"
CLAN_RE = re.compile('[A-Z][A-Z]+') # at least two upper case
_re_type = type(CLAN_RE)

HTML_IDX = "index.html"
NULL_LNK = "null" # path ends with this '/dev/null', 'C:\ft\_null'
PERSON_IDX = "www_index.htm"
PERSON_IDX_ = "www_index_.htm"
PRIVATE = "_PRIVATE"
CLANTREE = "_clanTree" # .dot, .htm, .png

# This is pretty nasty, I know. These are the strings
# that we search & replace for in the html templates
FT_ROOT_subst_leader = '="'
FTB_ROOT_subst  = FT_ROOT_subst_leader+'../../tree-builder/' # -> .../ftb/dist/
TREE_ROOT_subst = FT_ROOT_subst_leader+'../../../tree/'

AUTOGEN_FILES = [ PERSON_IDX, PERSON_IDX_, BCKf+'*', TMPf+'*', CLANTREE+'.*', 'searchRecs.js', 'families.html' ]

# Microsoft 'Mark of the web' - insert immediately before <html> tag
MOTW = "<!-- saved from url=(0014)about:internet -->\n"

# If nodePattern is found, returns (head, tail)
# If nodeInHead=True  <nodePattern> node is in head
#              =False <nodePattern> node is in tail
# If nodePattern is not found, returns None
# nodePattern may be a string or RE 
def trySplitPathAtNode(path, nodePattern, nodeInHead):
    # As <path> may have come from either windows or linux we need
    # to handle both. As the python ntpath utilities can handle both
    # '\' and '/' path seps, this is what we use.
    path = ntpath.normpath(path)
    
    # remove any windows drive first as it complicates
    # the splitting operation (it'll be added back at the end)
    drv, path = ntpath.splitdrive(path)
    
    splitPath = path.split(ntpath.sep)
    
    pos = len(splitPath) - 1 # searching backwards
    foundAt = -1
    
    if isinstance(nodePattern, _re_type):
        while pos >= 0:
            if nodePattern.match(splitPath[pos]) is not None:
                foundAt = pos
                break
            pos -= 1
    else:
        while pos >= 0:
            if splitPath[pos] == nodePattern:
                foundAt = pos
                break
            pos -= 1
        
    if foundAt == -1:
        return None

    # Reassemble the path string, using the 'proper' os.sep for this OS
    if nodeInHead:
        return drv+os.sep.join(splitPath[0:foundAt+1]), os.sep.join(splitPath[foundAt+1:])
    else:
        if (len(splitPath[0]) == 0) and (foundAt == 1):
            splitPath[0] = os.sep
        return drv+os.sep.join(splitPath[0:foundAt]), os.sep.join(splitPath[foundAt:])
    
def getTreeRoot(path = None, rootNode = TREE_NODE):
    '''Get the tree root from the path'''
    if path is None:
        path = os.getcwd()
        
    headtail = trySplitPathAtNode(path, rootNode, nodeInHead=True)
    if headtail is None:
        raise Exception("Couldn't find tree-root node '%s' in path %s" % (rootNode, path))
    
    return headtail[0]

def tryRebaseLink(tgt, treeRoot, treeRootNode = TREE_NODE):
    headtail = trySplitPathAtNode(tgt, treeRootNode, nodeInHead=True)
    if headtail is None: # look for the CLAN node instead
        headtail = trySplitPathAtNode(tgt, CLAN_RE, nodeInHead=False)

    if headtail is not None:
        # rebase: add new head (root) to the tail
        return os.path.join(treeRoot, headtail[1])
    else:
        return None
    
SUFFIXES = [ INTERNET_SCUT_SUFFIX, WINDOWS_SCUT_SUFFIX ]
    
def makelink_withbck(newTgt, oldLnk, mklnk_fn, newLnkSuffix=None, dryrun=False):
    if newLnkSuffix is None:
        newLnkSuffix = getLinkSuffix(mklnk_fn)
    
    root, oldLink_bn = os.path.split(oldLnk)
    
    oldLink_bck = os.path.join(root, BCKf+oldLink_bn)
    
    oldLink_bn_extless = stripKnownSuffixes(oldLink_bn, SUFFIXES)
    
    # The new link is created as a temporary first
    newLink_tmp = os.path.join(root, TMPf+oldLink_bn_extless+newLnkSuffix)
    
    # and this is what the temp link will be moved to eventually
    newLink = os.path.join(root, oldLink_bn_extless+newLnkSuffix)
    
    if dryrun:     
        print("mklnk(%s,\n" \
              "      %s)" % (newTgt, newLink_tmp))
        if os.path.exists(oldLnk):
            print("rename(%s,\n" \
                  "       %s)" % (oldLnk, oldLink_bck))
        print("rename(%s,\n" \
              "       %s)" % (newLink_tmp, newLink))
    else:
        # We do try/excepts here rather than os.path.exists() this
        # is because linux symlinks that point to non-existent targets
        # return os.path.exists() -> False.
        
        # Try to create the new link as a temporary first. If this fails
        # then the old link will be preserved as is
        try:
            os.remove(newLink_tmp)
        except:
            pass
            
        mklnk_fn(newTgt, newLink_tmp)
        
        # Backup the current link
        try:
            os.remove(oldLink_bck)
        except:
            pass
            
        try:
            os.rename(oldLnk, oldLink_bck)
        except:
            pass
        
        # Now rename the tmp link to be our new link
        os.rename(newLink_tmp, newLink)
            
        #os.remove(bckLnk)
        
        print("%s -> %s" % (newLink, newTgt))

def extractPersonName(path):
    headtail = trySplitPathAtNode(path, CLAN_RE, nodeInHead=False)
    if headtail is None:
        raise Exception("Couldn't find CLAN_RE node '%s' in path" % (path))
    
    path = headtail[1].split(os.sep)
    return (path[0], path[-1]) # ('CLAN', 'Forename')


class SpouseLink:
    LINK_RE = re.compile(r"([hwp])([0-9]*?)\.\s+([a-zA-Z ]*)")
    
    def __init__(self):
        self.path = None
        self.forename = self.surname = None
        self.relationship = None

    @staticmethod
    def find(d):
        spouses = []
        for f in os.listdir(d):
            f_full = os.path.join(d, f)
            
            if not islink(f_full):
                continue
            
            match = SpouseLink.LINK_RE.match(f)
            if match is None:
                continue

            m = SpouseLink()
            m.relationship = match.groups()[0]
            num = match.groups()[1]
            if num == '':
                num = '1'
            lclName = match.groups()[2].split()
            m.forename = " ".join(lclName[0:-1])
            m.surname = lclName[-1].upper()
            m.path = SpouseLink.getPath(f_full)
            
            spouses.append( (num, m) )

        spouses.sort(key=lambda m: m[0])
        return [m[1] for m in spouses]
            
    @staticmethod
    def getPath(p):
        try:
            tgt = readlink(p)
        except:
            print("Can't read spouse link %s" % (p))
            tgt = NULL_LNK
        if tgt.endswith(NULL_LNK):
            tgt = None
            
        return tgt

    def makeFakePath(self, root):
        return os.path.join(root, self.surname, "_FAKE_", self.forename)
