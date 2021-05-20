#!/usr/bin/python3

import os
import argparse
import ntpath

import pth; pth.setPythonpath()

from osutils import getLinkSuffix, readlink_scut, readlink_url, fwdslash
from osutils import makelink_url, makelink_scut
from osutils import INTERNET_SCUT_SUFFIX, WINDOWS_SCUT_SUFFIX, BCKf, TMPf
from ft_utils import NULL_LNK, TREE_NODE, getTreeRoot, tryRebaseLink, makelink_withbck

# To remove the backups:
# find . -name '__bck_*' -exec rm {} +

class Converter:
    def __init__(self, dryrun, rootPath, oldRootNode, link_type, absLinks):
        self.dryrun = dryrun
        self.rootPath = os.path.abspath(rootPath)
        self.oldRootNode = oldRootNode
        self.mklnk = self.getLinkMaker(link_type)
        self.newLnkSuffix = getLinkSuffix(self.mklnk)
        
        self.absLinks = absLinks
        if (self.mklnk is not os.symlink) and (not self.absLinks):
            print("Forcing absolute links")
            self.absLinks = True
        
    def getLinkMaker(self, link_type):
        '''Return the function used to make the link type '''
        
        if link_type == 'url':
            return makelink_url
        elif (link_type == 'sym') and (os.name == 'posix'):
            return os.symlink
        elif (link_type == 'scut') and (os.name == 'nt'):
            return makelink_scut
        else:
            raise Exception("Unsupported link type %s" % (link_type))
    
    def convert_links(self):
        numLinks = 0
        noTarget = []
            
        if os.name == 'posix':
            # This was originally /dev/null. Meld, however doesn't see it!
            NULL_LINK_TGT = '/tmp/'+NULL_LNK
        else:
            NULL_LINK_TGT = os.path.join(self.rootPath, '_'+NULL_LNK)
        
        for root, dirs, files in os.walk(self.rootPath):
            # The templates dir contains example links: don't convert these
            if 'templates' in dirs:
                dirs.remove('templates')
                
            # In linux, symlinks pointing to directories are treated by os.walk
            # as directories, so we identify them here and append to the files list
            for d in dirs:
                fullPath = os.path.join(root, d)
                if os.path.islink(fullPath):
                    files.append(d)
                
            for f in files:
                # Get full path to link
                lnkName = os.path.join(root, f)
                
                # NF_DEBUG: SHOULD WE LOOK FOR SPOUSE LINKS ONLY? i.e 'w. ' etc
                
                if f.startswith(BCKf) or f.startswith(TMPf):
                    # might want to delete these now
                    #os.remove(lnkName)
                    continue

                # Deliberately not using osutils.readlink() here so that we can get
                # any relative symlinks
                if lnkName.endswith(INTERNET_SCUT_SUFFIX):
                    tgt = readlink_url(lnkName) # always absolute
                elif lnkName.endswith(WINDOWS_SCUT_SUFFIX):
                    tgt = readlink_scut(lnkName) # abs or rel (pref rel)
                elif os.path.islink(lnkName):
                    # use os.readlink() to preserve a relative path if present - it
                    # makes the rebasing more resilient
                    tgt = os.readlink(lnkName)
                else:
                    continue # not a link
                
                numLinks += 1
                #print("FOUND", lnkName)
                
                if tgt.endswith(NULL_LNK):
                    newTgt = NULL_LINK_TGT
                else:
                    # Discard any windows drive
                    drv, tgt = ntpath.splitdrive(tgt)
    
                    # Normalise the path to use the os.sep for this OS
                    tgt = fwdslash(tgt)
                    tgt = os.path.normpath(tgt)
                  
                    # Try rebase
                    rebased = tryRebaseLink(tgt, treeRoot, self.oldRootNode)
                    if rebased is not None:
                        newTgt = rebased
                    else:
                        # If we've not managed to rebase by this point then the only valid
                        # case is a link is a relative pointing to something WITHIN
                        # its parent CLAN directory
                        if not os.path.isabs(tgt):
                            # make it absolute
                            newTgt = os.path.normpath(os.path.join(root, tgt))
                        else:
                            # Very probably junk; just preserve it as is
                            newTgt = tgt
    
                    if not os.path.exists(newTgt):
                        # The target doesn't exist. Make note of it, but plough on
                        noTarget.append( (lnkName, newTgt) )
                    else:
                        # Don't convert non-existent targets to relative - it'll
                        # just confuse things further when attemping to manually fix
                        if not self.absLinks: # make relative
                            newTgt = os.path.relpath(newTgt, root)
    
                makelink_withbck(newTgt, lnkName, self.mklnk, self.newLnkSuffix, self.dryrun)           
    
        print("numLinks", numLinks)
        if len(noTarget) != 0:
            print("WARN: The following %d targets don't exist:" % (len(noTarget)))
            for lnk, tgt in noTarget:
                print("%s from %s" % (tgt, lnk))
    
##

if __name__ == '__main__':
    linkTypes = ['url']
    if os.name == 'posix':
        linkTypes.append('sym')
    elif os.name == 'nt':
        linkTypes.append('scut')
        
    parser = argparse.ArgumentParser(description='Convert Links')

    # Optional parameters
    parser.add_argument('-l', '--link_type', type=str, default='url', choices=linkTypes,
                        help='Link type to be used')
    parser.add_argument('-a', '--abs_links', action="store_true", default=False,
                        help='Use absolute paths in sym links')
    parser.add_argument('-r', '--root_node', type=str, default=TREE_NODE,
                        help='Alternative tree root node (for incoming targets)')
    parser.add_argument('-d', '--dryrun', action="store_true", default=False,
                        help='Not for real')

    # The positional parameter optionally specifies the tree-root
    parser.add_argument('treeroot', metavar='treeroot', type=str, nargs='?',
                        help='Tree Root (default search cwd)')

    args = parser.parse_args()
    
    treeRoot = args.treeroot
    if treeRoot is None:
        treeRoot = getTreeRoot()
    print("Tree-root is:", treeRoot)
    
    incomingRootNode = args.root_node
    
    converter = Converter(args.dryrun, treeRoot, incomingRootNode, args.link_type, args.abs_links)
    converter.convert_links()
         