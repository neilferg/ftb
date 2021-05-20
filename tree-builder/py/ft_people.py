import os.path
from osutils import getFileVersion
from ft_utils import tryRebaseLink, PRIVATE, isClan, isPerson
from ft_bond import PartnerLink
import ft_vital


ID_START = 1000

class PersonFactory:
    def __init__(self, root):
        self.people = {}
        self.root = os.path.abspath(root)
        self.splitroot = self.root.split(os.sep)
        
        #self.defaultPrivate = None # inspect filesys to determine
        self.defaultPrivate = False  # include everyone
        self.id = ID_START
        self.treeFrozen = False
        
    def getVersion(self):
        return '1.0.2'
    
        LAUNCHER = os.path.join(self.root, "scripts", "launcher", "release", "FamilyTree.exe")
        return getFileVersion(LAUNCHER)

    def getPerson(self, path):
        path = os.path.abspath(path)
        splitpath = path.split(os.sep)

        if (len(splitpath) <= len(self.splitroot)) or (not isPerson(splitpath[-1])):
            return None
        
        p = self.people.get(path)
        
        if (p is None) and (not self.treeFrozen):
            p = Person(self.id, path, self)
            self.id += 1
            self.people[path] = p
            
        return p
        
    def getClans(self):
        clans = []
        for p in self.people.values():
            if p.fake:
                continue
            
            clan = p.surname()
            
            if not clan in clans:
                clans.append(clan)
                
        return clans

    def getClanPeople(self, clan):
        for p in self.people.values():
            if p.surname() == clan:
                yield p
            
    def getClanGeneration(self, clan, gen):
        for p in self.people.values():
            if p.surname() == clan and p.generation() == gen:
                yield p
            
    def scan(self):
        for root, dirs, files in os.walk(self.root):
            skip = []
            for d in dirs:
                if isPerson(d):
                    p = self.getPerson(os.path.join(root, d))
                    # Need to lookup spouses so that any links are scanned
                    p.spouses()
                    p.getVitalRecords()
                elif not isClan(d):
                    skip.append(d)

            for s in skip:
                dirs.remove(s)
            
        self.treeFrozen = True

        # 2nd pass try to resolve marriage VRs
        for p in self.people.values():
            if p.fake:
                continue
            p.crossSearchMarriageVrs()
            
class Person:
    def __init__(self, _id, path, peopleFact):
        self.id = _id
        self.path = os.path.abspath(path)
        self.peopleFact = peopleFact
        
        self.fake = (not os.path.exists(path))
        self.splitpath = self.path.split(os.sep)
        self.sex = None
        self.birthVr = self.deathVr = self.marriageVrs = None
        self.private = peopleFact.defaultPrivate
        
    def generation(self):
        return len(self.splitpath) - len(self.peopleFact.splitroot) - 2
        
    def isPrivate(self):
        if self.private is None:
            if os.path.exists(os.path.join(self.path, PRIVATE)):
                self.private = True
            else:
                parent = self.parent()
                if parent is None:
                    self.private = False
                else:
                    self.private = parent.isPrivate()
        
        return self.private
    
    def clanPath(self):
        return "/".join(self.splitpath[len(self.peopleFact.splitroot):])

    def getIdStr(self):
        return str(self.id)
        
    def surname(self):
        return self.splitpath[len(self.peopleFact.splitroot)]
        #return self.peopleFact.getClan(self.splitpath)

    def forename(self):
        return self.splitpath[-1]

    def name(self):
        return " ".join([self.forename(), self.surname()])

    def __str__(self):
        return self.name()
    
    # parent from filesys
    def parent(self):
        f = self.splitpath[:-1]
        if self.fake or len(f) <= len(self.peopleFact.splitroot) + 1:
            return None
        else:
            return self.peopleFact.getPerson(os.sep.join(f))

    def isFather(self):
        return (self.getSex() == 'M')

    def isMother(self):
        return (self.getSex() == 'F')

    def getFather(self):
        immParent = self.parent()
        if immParent is None:
            return None
            
        if immParent.isFather():
            return immParent
        else:
            return self.getSpouseParent(immParent, 'father')
        
    def getMother(self):
        immParent = self.parent()
        if immParent is None:
            return None
            
        if immParent.isMother():
            return immParent
        else:
            return self.getSpouseParent(immParent, 'mother')

    def getSpouseParent(self, immParent, parentType):
        name = None
        if self.birthVr is not None:
            name = getattr(self.birthVr, parentType)

        # try marriages
        if (name is None) and (self.marriageVrs is not None):
            for mr in self.marriageVrs:
                if mr is None:
                    continue
                
                if parentType == 'father':
                    name = mr.getFather(self.getSex())
                else:
                    name = mr.getMother(self.getSex())
                if name is not None: break

        # try death
        if (name is None) and (self.deathVr is not None):
            name = getattr(self.deathVr, parentType)

        if name is None: return None
        
        for s in immParent.spouses():
            if s.nameMatch(name):
                return s
        print("Failed to find child %s's %s obj '%s'" % (self.clanPath(), parentType, name))

    def nameMatch(self, name):
        nameElem = name.strip().upper().split()
        tryForename = self.forename().upper()
        trySurname = self.surname().upper()
        return tryForename.startswith(nameElem[0]) and trySurname.startswith(nameElem[-1])
        
    def spouses(self):
        spouses = []
        if self.fake:
            return spouses

        # spouses are sorted 1, 2 ...
        for sl in PartnerLink.find(self.path):
            sex = None
            if sl.relationship == 'h':
                sex='F'
            elif sl.relationship == 'w':
                sex='M'

            sp = sl.path
            
            # This really shouldn't be here. Bad links should be fixed before we
            # run this. But let's try it anyway!
            if (sp is not None) and (not os.path.exists(sp)):
                sp = tryRebaseLink(sp, self.peopleFact.root)
            
            if sp is None:
                sp = sl.makeFakePath(self.peopleFact.root)
                s = self.peopleFact.getPerson(sp)
                if sl.relationship == 'h':
                    s.sex='M'
                elif sl.relationship == 'w':
                    s.sex='F'
                    
            if (self.sex is None) and (sex is not None):
                self.sex = sex
                    
            s = self.peopleFact.getPerson(sp)
            if not s.isPrivate():
                spouses.append(s)

        return spouses
    
    def children(self):
        if self.fake: return []
        
        withBD = []
        withoutBD = []
        
        for f in os.listdir(self.path):
            p = os.path.join(self.path, f)
            if os.path.isdir(p) and isPerson(f):
                c = self.peopleFact.getPerson(p)
                if c.isPrivate():
                    continue
                bd = c.getBirthDate()
                if bd is None:
                    withoutBD.append(c)
                else:
                    withBD.append( (c, bd.date) )

        withBD.sort(key=lambda c: c[1])
        children = [c[0] for c in withBD]
        children.extend(withoutBD)
        return children
          
    def getVitalRecords(self):
        self.birthVr = ft_vital.Birth().find(self.path)
        self.deathVr = ft_vital.Death().find(self.path)

        # Only consider marriages VRs where we have a corresponding spouse link
        self.marriageVrs = [None for s in self.spouses()] # init
        for m in ft_vital.Marriage().find(self.path):
            if m.num < len(self.marriageVrs):
                self.marriageVrs[m.num] = m
        
        # For a female, any marriage VR is likely to be 'held' by the husband...

    def crossSearchMarriageVrs(self):
        marriagesVrs = []
        for s, mr in zip(self.spouses(), self.marriageVrs):
            if mr is None and (not s.fake):
                try:
                    idx = s.spouses().index(self)
                    mr = s.marriageVrs[idx]
                    #print("Found marriage VR for", self, "in spouse", s, "groom:", mr.groom, "bride:", mr.bride)
                except:
                    pass
            marriagesVrs.append(mr)
        self.marriageVrs = marriagesVrs

    def getSex(self):
        if self.sex is not None:
            return self.sex
        
        # Try for a birth record first
        if self.birthVr is not None:
            self.sex = self.birthVr.sex

        # Try from death
        if (self.sex is None) and (self.deathVr is not None):
            self.sex = self.deathVr.sex

        if (self.sex is None):
            self.spouses()

        return self.sex
        
    def getBirthDate(self):
        date = None
        
        # Try for a birth record first
        if self.birthVr is not None:
            date = self.birthVr.date
            if date is not None:
                return date

        # Try from marriage
        if (date is None) and (self.marriageVrs is not None):
            for m in self.marriageVrs:
                try:
                    if self.getSex() == 'M':
                        age = m.groom_age
                    else:
                        age = m.bride_age
                    if age is None: age = 25 # aproximation
                    date = m.date - age
                    date.approx = True
                except:
                    pass
        
        # Try from death
        if (date is None):
            try:
                date = self.deathVr.date - self.deathVr.age
                date.approx = True
            except:
                pass

        return date
    
    def getDeathDate(self):
        if self.deathVr is not None:
            return self.deathVr.date

    def getOtherNotes(self):
        p = os.path.join(self.path, "other_notes.htm")
        if os.path.exists(p):
            return p

    def getCensusSearches(self):
        p = os.path.join(self.path, "census_search.htm")
        if os.path.exists(p):
            return p
