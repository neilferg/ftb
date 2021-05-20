import os
import re

from osutils import getLinkSuffix, oktodo, islink, readlink_f
from ft_utils import isClan, isPerson, getLinkMaker, extractPersonName, NULL_LNK


class PartnerLink:
    REL_HUSBAND = 'h'
    REL_WIFE    = 'w'
    REL_PARTNER = 'p'
    
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
            
            match = PartnerLink.LINK_RE.match(f)
            if match is None:
                continue

            m = PartnerLink()
            m.relationship = match.groups()[0]
            num = match.groups()[1]
            if num == '':
                num = '1'
            lclName = match.groups()[2].split()
            m.forename = " ".join(lclName[0:-1])
            m.surname = lclName[-1].upper()
            m.path = PartnerLink.getPath(f_full)
            
            spouses.append( (num, m) )

        spouses.sort(key=lambda m: m[0])
        return [m[1] for m in spouses]
            
    @staticmethod
    def getPath(p):
        try:
            tgt = readlink_f(p)
        except:
            print("Can't read spouse link %s" % (p))
            tgt = NULL_LNK
        if tgt.endswith(NULL_LNK):
            tgt = None
            
        return tgt
    
    @staticmethod
    def getMyRelationship(partnerRelationship):
        if partnerRelationship == PartnerLink.REL_WIFE:
            return PartnerLink.REL_HUSBAND
        elif partnerRelationship == PartnerLink.REL_HUSBAND:
            return PartnerLink.REL_WIFE
        else:
            return PartnerLink.REL_PARTNER

    def makeFakePath(self, root):
        return os.path.join(root, self.surname, "_FAKE_", self.forename)


def _create_spouse_link(lnk, tgt, mklnk, absLink):
    lnk_suffix = getLinkSuffix(mklnk)
    lnk += lnk_suffix
    
    if not absLink:
        tgt = os.path.relpath(tgt, os.path.dirname(lnk))
    
    mklnk(tgt, lnk)
    
# Create spouse links from 'me' (cwd) to 'other'
def bond(other_path, relationship=PartnerLink.REL_PARTNER, linkType=None, me_path=None, force=False, absLink=False, quiet=False):
    mklnk = getLinkMaker(linkType)
    
    if me_path is None:
        me_path = os.path.abspath('.')
        
    me_name = extractPersonName(me_path)
    if (not isClan(me_name[0])) or (not isPerson(me_name[1])):
        raise Exception("my path %s is not a valid person" % (me_path))
    
    other_name = extractPersonName(other_path)
    if (not isClan(other_name[0])) or (not isPerson(other_name[1])):
        raise Exception("spouse path %s is not a valid person" % (other_path))
    
    me_rel = PartnerLink.getMyRelationship(relationship)
    
    me_to_other_lnk = os.path.join(me_path,relationship+'. '+other_name[1]+' '+other_name[0])
    other_to_me_lnk = os.path.join(other_path,me_rel+'. '+me_name[1]+' '+me_name[0])
    
    if os.path.exists(me_to_other_lnk) and not force:
        raise Exception("Spouse link already exists @ %s" % (me_to_other_lnk))
 
    if os.path.exists(other_to_me_lnk) and not force:
        raise Exception("Spouse link already exists @ %s" % (other_to_me_lnk))
    
    if not quiet:
        print("create: '%s' -> '%s'" % (me_to_other_lnk, other_path))
        print("create: '%s' -> '%s'" % (other_to_me_lnk, me_path))
    
    if quiet or oktodo("OK to create links?"):
        if os.path.exists(me_to_other_lnk):
            os.remove(me_to_other_lnk)
        if os.path.exists(other_to_me_lnk):
            os.remove(other_to_me_lnk)
        
        _create_spouse_link(me_to_other_lnk, other_path, mklnk, absLink)
        _create_spouse_link(other_to_me_lnk, me_path, mklnk, absLink)
    