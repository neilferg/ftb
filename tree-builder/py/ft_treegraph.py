import lxml.html
import os.path
import subprocess
from os.path import relpath
import glob

THIS_DIR = os.path.abspath(os.path.dirname(__file__))

from osutils import fwdslash, url2path, path2url
from ft_utils import FT_ROOT_subst_leader, FTB_ROOT_subst, TREE_ROOT_subst, CLANTREE, MOTW


def findDotExe():
    UXPATH = '/usr/bin/dot'
    if os.path.isfile(UXPATH):
        return UXPATH
    
    newest = 0
    newestExe = None
    for exe in glob.glob(r"C:\Program Files*\Graphviz*\bin\dot.exe"):
        if os.path.getmtime(exe) > newest:
            newestExe = exe
            newest = os.path.getmtime(exe)
    if newestExe is None:
        raise Exception("Cannot find dot executable")
    print("Using", newestExe)
    return newestExe

JOIN = '[shape=box, style=filled, label="", height=0.01, width=0.01]'
BR = '\n'
P = BR+BR


class TreeBuilder:
    FONT = "Times-Roman"
    FONT_SIZE = 14
    
    def __init__(self, peopleFact, opDir):
        self.peopleFact = peopleFact
        self.opDir = opDir
        self.interest = Interesting()
        self.isMultiClan = False
        self.templ = None

    def make(self, title = "", filebasename = CLANTREE):
        dotFile = os.path.join(self.opDir, filebasename+".dot")
        with open(dotFile, "w") as df:
            df.write('digraph "TREE" { node [shape=box fontname="%s" fontsize=%d]; bgcolor="transparent"\n' % \
                     (self.FONT, self.FONT_SIZE) )
        
            self.makeDot(df)
            df.write("}\n")

        self.makeHtml(title, dotFile)
        
    def makeDot(self, df):
        pass
            
    def getSexFill(self, sex):
        if sex == 'M':
            return 'style="filled" fillcolor="#ccffff"'
        elif sex == 'F':
            return 'style="filled" fillcolor="pink"'
        else:
            return ''
    
    def node(self, p, num):
        if p.getOtherNotes() is not None:
            shape = "note"
        else:
            shape = "box"
        txt = ['"%s" [shape=%s ' % (p.getIdStr(), shape)]
        txt.append(self.getSexFill(p.getSex()))
        if not p.fake:
            # NOTE: We're deliberately using absolute paths here - they're made relative later on            
            url = path2url(os.path.join(p.path, "www_index.htm"))
            txt.append(' URL="%s"' % url)
        txt.append('label=< <TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0">')
        
        flagImage = self.interest.getLocImage(p)
        if flagImage is not None:
            image = os.path.join(self.peopleFact.root,'..','ftb','dist','images','flags',flagImage)
            txt.append('<TR><TD></TD><TD ALIGN="RIGHT"><IMG SCALE="FALSE" SRC="%s"/></TD></TR>' % image)
        else:
            txt.append('<TR><TD></TD><TD ALIGN="RIGHT"></TD></TR>')
        
        if self.isMultiClan:
            name = p.name()
        else:
            name = p.forename()
            
        if num is None:
            txt.append('<TR><TD COLSPAN="2">%s</TD></TR>' % name)
        else:
            txt.append('<TR><TD COLSPAN="2">%d. %s</TD></TR>' % (num, name))
        txt.append('<TR><TD COLSPAN="2"><FONT POINT-SIZE="11">%s</FONT></TD></TR>' % self.dates(p))
        txt.append('</TABLE> >];')
        return '\n'.join(txt)
    
    def spouseNode(self, p, spouses, num):
        s = spouses[num]
        sCode = s.getIdStr()
        txt = ['"%s" [shape=ellipse ' % sCode]
        txt.append( self.getSexFill(s.getSex()) )
        if not s.fake:
            # NOTE: We're deliberately using absolute paths here - they're made relative later on
            url = path2url(os.path.join(s.path, "www_index.htm"))
            txt.append(' URL="%s" ' % url)
            
        if len(spouses) > 1:
            txt.append(' label="m%d.' % (num + 1))
        else:
            txt.append(' label="m.')
            
        # Get date info if present
        try:
            year = p.marriageVrs[num].date.toYearString()
            txt.append(' %s' % year)
        except:
            pass
            
        txt.append("\\n%s" % s) # name
        txt.append('"]\n')
        return ''.join(txt)

    def dates(self, p):
        birthDate = p.getBirthDate()
        deathDate = p.getDeathDate()
        if (birthDate is not None) and (deathDate is not None):
            return birthDate.toYearString() + " - " + deathDate.toYearString()
        elif (birthDate is not None):
            return "b. " + birthDate.toYearString()
        elif (deathDate is not None):
            return "d. " + deathDate.toYearString()
        else:
            return " "
        
    def makeHtml(self, title, dotFile):
        d = os.path.dirname(dotFile)
        bn = os.path.basename(dotFile)
        bn = os.path.splitext(bn)[0]
        
        # The bitmap file
        imageType = 'png'
        imageFile = bn + "." + imageType
        imageFilePath = os.path.join(d, imageFile)
        htmlFilePath = os.path.join(d, bn + ".htm")
        cmd = [findDotExe(), '-T', imageType, '-o', imageFilePath, '-Tcmapx', '-o', htmlFilePath, dotFile]
        subprocess.call(cmd)

        with open(htmlFilePath, "r") as fs:
            text = fs.read()
        origMapDoc = lxml.html.fromstring(text)

        with open(self.templ, "r") as fs:
            text = fs.read()
        
        text = text.replace("__TITLE__", title)

        replPath = FT_ROOT_subst_leader + fwdslash(relpath(os.path.join(self.peopleFact.root,'..','ftb','dist'), d)) + '/'
        text = text.replace(FTB_ROOT_subst, replPath)

        replPath = FT_ROOT_subst_leader + fwdslash(relpath(os.path.join(self.peopleFact.root), d)) + '/'
        text = text.replace(TREE_ROOT_subst, replPath)
        
        opDoc = lxml.html.fromstring(text)
        bitmap = opDoc.get_element_by_id("relationships")
        bitmap.attrib["src"] = imageFile
        eMapTempl = opDoc.get_element_by_id("TREEMAP")

        # Create new map element
        eMap = lxml.html.Element("map")
        eMap.attrib.update(iter(eMapTempl.attrib.items()))
        
        for c in origMapDoc:
            #c.attrib["onMouseOut"] = "clearFocus(this);"
            
            path = url2path(c.attrib["href"])
            c.attrib["href"] = fwdslash(relpath(path, self.opDir))
                
            if c.attrib["shape"] == "rect":
                #c.attrib["onMouseOver"] = "setFocus(this);"

                # Update id
                # Extract the person from the ABSOLUTE URL
                p = os.path.dirname(path)
                p = self.peopleFact.getPerson(p)
                c.attrib["id"] = p.getIdStr()
                c.attrib["title"] = self.getTitle(p)
            else:
                del c.attrib["title"]
                
            eMap.append(c)

        # Remove the template map & replace it with the 'real' one
        container = eMapTempl.getparent()
        container.remove(eMapTempl)
        container.append(eMap)

        with open(htmlFilePath, "wb") as fd:
            fd.write(MOTW.encode("utf8"))
            fd.write(lxml.html.tostring(opDoc, pretty_print=True))
        
    def getTitle(self, p):
        title = []
        for event in [self.personBirth, self.personMarriages, self.personDeath]:
            txt = event(p)
            if len(txt) > 0: 
                title.append(txt)
        return P.join(title)
    
    def personBirth(self, p):
        text = []
        date = p.getBirthDate()
        if date is not None:
            text.append('BIRTH: %s' % date)
            if (p.birthVr is not None) and (p.birthVr.where is not None):
                text.append(' in %s' % (p.birthVr.where))
            text.append('.')
        return ''.join(text)
        
    def personDeath(self, p):
        text = []
        if (p.deathVr is not None) and (p.deathVr.date is not None):
            text.append('DEATH: %s' % p.deathVr.date)
            if p.deathVr.age is not None:
                text.append(' (age %s)' % (p.deathVr.age))
            if p.deathVr.where is not None:
                text.append(' in %s' % (p.deathVr.where))
            text.append('.')
        return ''.join(text)

    def personMarriages(self, p):
        text = []  
        if (p.marriageVrs is not None):
            spouses = p.spouses()
            multipleMarriages = (len(spouses) > 1)

            num = 1
            for s, mr in zip(spouses, p.marriageVrs):
                if s.isPrivate():
                    continue
                
                if num > 1:
                    text.append(BR)
            
                if multipleMarriages:
                    text.append('MARRIAGE %d:' % (num) )
                else:
                    text.append('MARRIAGE:')

                if mr is not None and mr.date is not None:
                    text.append(' %s' % (mr.date))
                text.append(' to %s' % (s.name()))
                if mr is not None and mr.where is not None:
                    text.append(' in %s' % (mr.where))
                text.append('.')
                num += 1
        return ''.join(text)
        
class Interesting:
    PLACES = {
        'USA': 'usa.gif',
        'Ireland': 'ireland.gif',
        'Wales': 'wales.gif',
        'England': 'england.gif',
        'Australia': 'australia.gif',
        'Canada': 'canada.gif',
        'France': 'france.gif'
    }
    
    def getLocImage(self, p):
        flagImage = None
        for vr in [ p.deathVr, p.birthVr ]:
            if vr is None or vr.where is None:
                continue
            
            loc = vr.where.split(',')[-1].strip()
            flagImage = self.PLACES.get(loc)
            if flagImage is not None:
                break
        return flagImage
    
    
class ClanTree(TreeBuilder):
    def __init__(self, clan, peopleFact, opDir = None):  
        if not clan in peopleFact.getClans():
            raise Exception("No such clan " + clan)
        
        if opDir is None:
            opDir = os.path.join(peopleFact.root, clan)
            
        TreeBuilder.__init__(self, peopleFact, opDir)
        self.clan = clan
        self.templ = os.path.join(THIS_DIR,'..','html','tree_templ.htm')
        
    def makeDot(self, df):
        print("Drawing %s tree" % (self.clan))
        gen = [(None, p) for p in self.peopleFact.getClanGeneration(self.clan, 0)]
        while len(gen) > 0:
            df.write('graph [splines = polyline]\n')
            df.write('subgraph { rank = same\n')
            prevPer = None
            for num, p in gen:
                if p.fake or p.isPrivate():
                    continue
                
                # Write out this person
                df.write( self.node(p, num) )
                if prevPer is not None:
                    df.write('"%s" -> "%s" [style = invis]\n' % \
                             (prevPer.getIdStr(), p.getIdStr()))
                prevPer =  p
                    
                # write out and link spouses
                prevSpouse = p
                spouses = p.spouses()
                for i, s in enumerate(spouses):
                    df.write( self.spouseNode(p, spouses, i) )
                    df.write('"%s" -> "%s" [dir = none, weight=10000]\n' % \
                             (prevSpouse.getIdStr(), s.getIdStr()))
                    prevSpouse = s    
            df.write('}\n\n') # end subgraph
            
            nextGen = []
            for num, p in gen:
                if p.fake or p.isPrivate():
                    continue
                
                for i, c in enumerate(p.children()):
                    parent = c.parent()
                    df.write('"%s" -> "%s" [dir = none]\n' % \
                             (p.getIdStr(), c.getIdStr() ))
                    if c.getBirthDate() is None:
                        i = None
                    else:
                        i += 1
                    nextGen.append( (i, c) )
                    
            gen = nextGen


class AncestorTree(TreeBuilder):
    def __init__(self, person, peopleFact, opDir = None):
        if opDir is None:
            opDir = person.path
            
        TreeBuilder.__init__(self, peopleFact, opDir)
        
        self.p = person
        self.templ = os.path.join(THIS_DIR,'..','html','ancestor_tree_templ.htm')
        self.isMultiClan = True
        self.part = 0
        
    def makeDot(self, df):
        df.write('graph [splines = polyline, rankdir = LR]\n')
        
        df.write( self.node(self.p, None) )
        
        for part, parent in enumerate([ self.p.getFather(), self.p.getMother() ]):
            self.part = part
            self.linkGeneration(df, self.p.getIdStr(), parent.getIdStr())
            generation = [ parent ]
            while len(generation) > 0:
                generation = self.drawGeneration(df, generation)
                 
    def marriageNode(self, father):
        return father.getIdStr() + "_m"
    
    def linkGeneration(self, df, node1, node2):
        if self.part == 0:
            pair = (node2, node1)
        else:
            pair = (node1, node2)
        df.write('"%s" -> "%s" [dir = none]\n' % pair)
    
    def drawGeneration(self, df, generation):
        df.write('subgraph { rank = same\n')
        
        nextGen = []
        prevPer = None
        for p in generation:
            df.write( self.node(p, None) )
            if prevPer is not None:
                if p in prevPer.spouses():
                    # Create link node
                    marriageNode = self.marriageNode(prevPer)
                    df.write('"%s" ' % marriageNode)
                    df.write(JOIN)
                    df.write('\n')
                    
                    df.write('"%s" -> "%s" -> "%s" [dir = none]\n' % \
                             (prevPer.getIdStr(), marriageNode, p.getIdStr()))
                else:
                    df.write('"%s" -> "%s" [style = invis]\n' % \
                             (prevPer.getIdStr(), p.getIdStr()))
            prevPer =  p
            
        df.write('}\n\n') # end subgraph
            
        # Link to next generation
        for p in generation:
            father = p.getFather()
            mother = p.getMother()
            connect = None
            if (father is not None) and (mother is not None):
                connect = self.marriageNode(father)
            elif (father is not None):
                connect = father.getIdStr()
            elif (mother is not None):
                connect = mother.getIdStr()
                
            if connect is not None:
                self.linkGeneration(df, p.getIdStr(), connect)
            
            if father is not None:
                nextGen.append(father)
            if mother is not None:
                nextGen.append(mother)
                
        return nextGen
