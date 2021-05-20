import lxml.html
import glob
import os.path
import re
from ft_date import FtDate


class Vital:
    CERT_EXT = "(jpg|png|htm)"
    
    def __init__(self):
        self.properties = [ ("date", FtDate), ("where", str) ]
        self.filePattern = None
        self.certPattern = None
        self.file = None

    def __str__(self):
        props = [self.__class__.__name__]
        for attr, ty in self.properties:
            props.append("%s=%s" % (attr, getattr(self, attr) ))
        return ", ".join(props)
                      
    def parse(self, f):
        with open(f, "r") as fs:
            text = fs.read()
        doc = lxml.html.fromstring(text)
        for attr, ty in self.properties:   
            v = None
            try:
                v = doc.get_element_by_id(attr.upper()).text_content()
                v = v.strip()
                if len(v) == 0:
                    v = None
                else:
                    v = ty(v)
            except:
                pass

            setattr(self, attr, v)

    def find(self, d):
        files = glob.glob(os.path.join(d, self.filePattern))
        if len(files) == 0:
            return None
        elif len(files) > 1:
            Exception("Found multiple records")
        else:
            self.file = files[0]
            self.parse(self.file)
            return self

    def getFile(self):
        return self.file
    
    def getCert(self):
        if self.certRE is None:
            return None
        
        d = os.path.dirname(self.file)
        for f in os.listdir(d):
            match = self.certRE.match(f)
            if match is not None:
                return os.path.join(d, f)
            
class Birth(Vital):
    def __init__(self):
        Vital.__init__(self)
        self.filePattern = "birth_search.htm*"
        self.certRE = re.compile("birth\\.%s" % self.CERT_EXT)
        self.properties.extend([ ("sex", str), ("father", str), ("mother", str) ])

class Marriage(Vital): 
    def __init__(self):
        Vital.__init__(self)
        self.filePattern = re.compile(r"marriage([0-9]*?)_search.htm")
        self.properties.extend([ ("where", str),
                                 ("groom", str), ("groom_age", int), ("bride", int), ("bride_age", int),
                                 ("groom_father", str), ("groom_mother", str),
                                 ("bride_father", str), ("bride_mother", str) ])
        self.num = 1
        
    def getFather(self, sex):
        try:
            if (sex == 'M'):
                return self.groom_father
            elif (sex == 'F'):
                return self.bride_father
        except:
            pass

    def getMother(self, sex):
        try:
            if (sex == 'M'):
                return self.groom_mother
            elif (sex == 'F'):
                return self.bride_mother
        except:
            pass

    def find(self, d):
        marriages = []
        for f in os.listdir(d):
            match = self.filePattern.match(f)
            if match is None:
                continue

            m = Marriage()
            num = match.groups()[0]
            if num == '':
                num = '1'
            m.num = int(num) - 1   # store as zero based index

            m.file = os.path.join(d, f)
            m.parse(m.file)
            marriages.append(m)
        return marriages

    def getCert(self):
        if self.num == 0:
            t = '1*?'
        else:
            t = str(self.num + 1)
        self.certRE = re.compile("marriage%s\\.%s" % (t, self.CERT_EXT))
        return Vital.getCert(self)

class Death(Vital):
    def __init__(self):
        Vital.__init__(self)
        self.filePattern = "death_search.htm*"
        self.certRE = re.compile("death\\.%s" % (self.CERT_EXT))
        self.properties.extend([ ("sex", str), ("age", int), ("father", str), ("mother", str) ])
