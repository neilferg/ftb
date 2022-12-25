import os.path
from osutils import fwdslash
from os.path import relpath
import urllib

THIS_DIR = os.path.abspath(os.path.dirname(__file__))

from ft_people import PersonFactory
from ft_utils import MOTW, PERSON_IDX, PERSON_IDX_, FT_ROOT_subst_leader, FTB_ROOT_subst, TREE_ROOT_subst
import ft_otherfiles
from ft_treegraph import ClanTree


def initAndScan(root):
    root = os.path.abspath(root)
    pf = PersonFactory(root)
    pf.scan()
    print("Found %d people" % len(pf.people))
    print("Clans:", pf.getClans())
    return pf


class MakeWeb:
    def __init__(self, pf):
        self.pf = pf

    def make(self):
        self.makeRoot()
        self.makeIndividuals()
        self.makeClanTreegraphs()
        MakeSearch(self.pf).makeSearchIndex()

    def makeRoot(self):
        NUM_COLS = 4

        html = []
        html.append("<!DOCTYPE HTML>")
        html.append(MOTW)
        html.append('<html><head><title>Family Tree</title>')
        html.append("<meta HTTP-EQUIV='Content-Type' CONTENT='text/html; charset=ISO-8859-1'>")
        ftBuilderRoot = os.path.join('..','ftb','dist')
        html.append('<script type="text/javascript" src="%s/js/ftb-predom.js"></script>\n' % (ftBuilderRoot))
        html.append('<script defer type="text/javascript" src="%s/js/ftb-postdom.js"></script>\n' % (ftBuilderRoot))
        html.append('</head><body>')
        
        html.append('<span style="font-style: italic;">FamilyTree Version:</span> %s<br>' % self.pf.getVersion())
        html.append('<h2>Families</h2>')

        ALL_CLANS = []
        for clan in self.pf.getClans():
            numPublic = 0
            for p in self.pf.getClanPeople(clan):
                if not p.isPrivate(): numPublic += 1
            if numPublic > 0:
                ALL_CLANS.append(clan)
        ALL_CLANS.sort()
        numClans = len(ALL_CLANS)
        numPerCol = (numClans // NUM_COLS) + 1
        html.append('<table style="width: 90%;" border="0" cellpadding="0" cellspacing="0"><tr>')
        NEW_COL = '<td style="vertical-align: top; width: 25%;"><ul>'
        END_COL = '</ul></td>'
        for n, c in enumerate(ALL_CLANS):
            if n % numPerCol == 0:
                if n > 0:
                    html.append(END_COL)
                html.append(NEW_COL)
            html.append('<li><a href="%s" target="_top">%s</a></li>' % (c + "/_clanTree.htm", c))
            
        if numClans > 0:
            html.append(END_COL)
        html.append('</tr></table></body></html>')

        with open(os.path.join(self.pf.root, "families.html"), "w") as fs:
            fs.write('\n'.join(html))

    def makeClanTreegraphs(self):
        for c in self.pf.getClans():
            tb = ClanTree(c, self.pf)
            tb.make(c)

    def makeIndividuals(self):
        personIndexTempl = os.path.join(THIS_DIR,'..','html','person_index_templ.htm')
        with open(personIndexTempl, "r") as fs:
            personIndexTempl = fs.read()
        
        for path, p in self.pf.people.items():
            if p.fake or p.isPrivate():
                continue

            # Navigator Bar
            clanTree = os.path.join(self.pf.root, p.surname(), "_clanTree.htm")

            person_index = personIndexTempl
            
            parent = p.parent()
            if parent is None:
                parent = clanTree
                parentTxt = 'top'
            else:
                sex = parent.getSex()
                parent = os.path.join(parent.path, PERSON_IDX)
                if sex is None:
                    parentTxt = 'parent'
                elif sex == 'M':
                    parentTxt = 'Father'
                elif sex == 'F':
                    parentTxt = 'Mother'
                    
            person_index = person_index.replace("__PATH_TO_PERSON__", fwdslash(path[len(self.pf.root) + 1:]))
            
            replPath = FT_ROOT_subst_leader + fwdslash(relpath(os.path.join(self.pf.root,'..','ftb','dist'), path)) + '/'
            person_index = person_index.replace(FTB_ROOT_subst, replPath)
            
            replPath = FT_ROOT_subst_leader + fwdslash(relpath(os.path.join(self.pf.root), path)) + '/'
            person_index = person_index.replace(TREE_ROOT_subst, replPath)
            
            person_index = person_index.replace("__P_TY__", parentTxt)
            person_index = person_index.replace("__GOTO_P__", fwdslash(relpath(parent, path)))
                
            person_index = person_index.replace("__GOTO_ME_IN_TREE__", fwdslash(relpath(clanTree + "#" + p.getIdStr(), path)))
            person_index = person_index.replace("__CLAN_NAME__", p.surname())
            person_index = person_index.replace("__MY_NAME__", p.name())

            print("write", PERSON_IDX, path)
            with open(os.path.join(path, PERSON_IDX), "w") as fs:
                fs.write(person_index)

            self.makePersonIndex(p, path)

    def personName(self, p, htmlText):
        htmlText.append('<tr><td style="font-style: italic;">Name:</td>')
        htmlText.append('<td>%s</td>' % (p.name()))
        htmlText.append('<td></td>') # blank
        htmlText.append('</tr>')

    def personBirth(self, p, htmlText):
        date = p.getBirthDate()
        if date is None:
            return

        if p.birthVr is None:
            htmlText.append('<tr><td style=" font-style: italic;">Birth:</td>')
            htmlText.append('<td>%s</td>' % (date))
        else:
            searchDoc = fwdslash(relpath(p.birthVr.getFile(), p.path))
            url = '<a href="%s">Birth</a>:' % (searchDoc)
            htmlText.append('<tr><td style=" font-style: italic;">%s</td>' % (url))
            htmlText.append('<td>%s' % (date))
            if p.birthVr.where is not None:
                htmlText.append(' in %s' % (p.birthVr.where))
            htmlText.append('</td>')
            cert = p.birthVr.getCert()
            if cert is not None:
                url = '<a href="%s">certificate</a>' % (fwdslash(relpath(cert, p.path)))
                htmlText.append('<td>%s</td>' % url)
                htmlText.append('</tr>')

    def personDeath(self, p, htmlText):
        if p.deathVr is None:
            return

        searchDoc = fwdslash(relpath(p.deathVr.getFile(), p.path))
        url = '<a href="%s">Death</a>:' % (searchDoc)
        htmlText.append('<tr><td style=" font-style: italic;">%s</td><td>' % (url))
       
        if p.deathVr.date is not None:
            htmlText.append('%s ' % (p.deathVr.date))
        if p.deathVr.age is not None:
            htmlText.append('(age %s) ' % (p.deathVr.age))
        if p.deathVr.where is not None:
            htmlText.append('in %s' % (p.deathVr.where))
        htmlText.append('</td>')
        cert = p.deathVr.getCert()
        if cert is not None:
            url = '<a href="%s">certificate</a>' % (fwdslash(relpath(cert, p.path)))
            htmlText.append('<td>%s</td>' % url)
        htmlText.append('</tr>')

    def personMarriages(self, p, htmlText):
        if (p.marriageVrs is None):
            return
        
        spouses = p.spouses()
        
        if len(spouses) > 0:
            htmlText.append('<tr><td><br></td></tr>')
        multipleMarriages = (len(spouses) > 1)

        num = 1
        for s, mr in zip(spouses, p.marriageVrs):
            if s.isPrivate():
                continue
            
            if multipleMarriages:
                t = "Marriage %d" % (num)
            else:
                t = "Marriage"
            if mr is None:
                url = t + ":"
            else:
                searchDoc = fwdslash(relpath(mr.getFile(), p.path))
                url = '<a href="%s">%s</a>:' % (searchDoc, t)
            
            htmlText.append('<tr><td style=" font-style: italic;">%s</td>' % (url))
            
            htmlText.append('<td>')
            if mr is not None and mr.date is not None:
                htmlText.append('%s ' % (mr.date))

            if s.fake:
                url = s.name()
            else:
                sidx = os.path.join(s.path, PERSON_IDX)
                sidx = urllib.parse.quote(fwdslash(relpath(sidx, p.path)))
                url = '<a href="%s" target="_top">%s</a>' % (sidx, s.name())
            
            htmlText.append('to %s' % url)
            if mr is not None and mr.where is not None:
                htmlText.append(' in %s' % (mr.where))
            htmlText.append('</td>')

            if mr is not None:
                cert = mr.getCert()
                if cert is not None:
                    url = '<a href="%s">certificate</a>' % (fwdslash(relpath(cert, p.path)))
                    htmlText.append('<td>%s</td>' % url)
                    
            htmlText.append('</tr>')
            num += 1

    def personMf(self, p, parentType, htmlText):
        if (parentType.upper() == 'FATHER'):
            parent = p.getFather()
        else:
            parent = p.getMother()

        if parent is None:
            return

        htmlText.append('<tr><td style=" font-style: italic;">%s:</td>' % (parentType))

        if parent.fake:
            url = parent.name()
        else:
            pidx = os.path.join(parent.path, PERSON_IDX)
            pidx = urllib.parse.quote(fwdslash(relpath(pidx, p.path)))
            url = '<a href="%s" target="_top">%s</a>' % (pidx, parent.name())
            
        htmlText.append('<td>%s</td>' % (url))
        htmlText.append('<td></td>') # blank
        htmlText.append('</tr>')

    def personChildren(self, p, htmlText):
        withBD = []
        withoutBD = []
        for c in p.children():
            bd = c.getBirthDate()
            if bd is None:
                withoutBD.append(c)
            else:
                withBD.append( (c, bd.date) )
                
        # Now check spouses
        for s in p.spouses(): 
            for c in s.children():
                if p.isMother():
                    parent = c.getMother()
                elif p.isFather():
                    parent = c.getFather()
                else:
                    continue
                if parent is not None and p.nameMatch(parent.name()):
                    bd = c.getBirthDate()
                    if bd is None:
                        withoutBD.append(c)
                    else:
                        withBD.append( (c, bd.date) )
                        
        if len(withBD) == 0 and len(withoutBD) == 0:
            return
        
        withBD.sort(key=lambda c: c[1])
        children = [c[0] for c in withBD]
        children.extend(withoutBD)
        
        htmlText.append('<h2>Children</h2><table class="children">')
        idx = 1
        for c in children:
            bd = c.getBirthDate()
            if bd is None:
                htmlText.append('<tr><td class="children-ra"><br></td>')
            else:
                htmlText.append('<tr><td class="children-ra">%d.</td>' % (idx))
                idx += 1
                
            cidx = os.path.join(c.path, PERSON_IDX)
            cidx = urllib.parse.quote(fwdslash(relpath(cidx, p.path)))
            url = '<a href="%s" target="_top">%s</a>' % (cidx, c.name())
            if bd is not None:
                url += ' b. %s' % (bd)
            if c.birthVr is not None and c.birthVr.where is not None:
                url += ' in %s' % (c.birthVr.where)
            htmlText.append('<td class="children">%s</td></tr>' % (url))
        htmlText.append('</table>')
            
    def makePersonIndex(self, p, path):
        dc = ft_otherfiles.DirCat(self.pf.root)

        htmlText = [ '<!DOCTYPE HTML>',
                     MOTW,
                     '<html><head>\n',
                     '<meta content="text/html; charset=ISO-8859-1" http-equiv="Content-Type">\n'
                   ]
        ftBuilderRoot = fwdslash(relpath(os.path.join(self.pf.root,'..','ftb','dist'), path))
        htmlText.append('<link rel="stylesheet" href="%s/css/ftb.css" type="text/css" />\n' % (ftBuilderRoot))
        htmlText.append('<script type="text/javascript" src="%s/js/ftb-predom.js"></script>\n' % (ftBuilderRoot))
        htmlText.append('<script defer type="text/javascript" src="%s/js/ftb-postdom.js"></script>\n' % (ftBuilderRoot))
        htmlText.append('<title>%s</title></head><body>\n' % (p.name()))

        htmlText.append("<h2>Vital Records</h2>\n")

        htmlText.append('<table style="text-align: left; width: 700px;" border="0" cellpadding="2" cellspacing="2"><tbody>\n')

        self.personName(p, htmlText)
        self.personBirth(p, htmlText)
        self.personDeath(p, htmlText)
        self.personMf(p, 'Father', htmlText)
        self.personMf(p, 'Mother', htmlText)

        self.personMarriages(p, htmlText)

        htmlText.append('</tbody></table>\n')

        self.personChildren(p, htmlText)

        census = p.getCensusSearches()
        other = p.getOtherNotes()

        if census or other:
            htmlText.append("<h2>Secondary Records</h2><ul>\n")

            if census:
                htmlText.append('<li><a href="%s">Census Searches</a></li>\n' % (fwdslash(relpath(census, p.path))))
                
            if other:
                htmlText.append('<li><a href="%s">Other Notes</a><br></li>\n' % (fwdslash(relpath(other, p.path))))

            htmlText.append('</ul>\n')

        numOtherFiles, otherFilesHtml = dc.cat(path)
        if (numOtherFiles > 0):
            htmlText.append("<h3>Other Files</h3>\n")
            htmlText.append(otherFilesHtml)
            #htmlText.append('<br><br>\n')
            
        htmlText.append('</body></html>\n')
        
        with open(os.path.join(path, PERSON_IDX_), "w") as fs:
            fs.write("".join(htmlText))
        
class MakeSearch:
    def __init__(self, pf, root = None):
        self.pf = pf
        self.root = root if root is not None else self.pf.root
        
    def makeSearchIndex(self, obsfuc = False):
        indexFile = os.path.join(self.root,"searchRecs.js")
        with open(indexFile, "w") as fh:
            fh.write("profiles = new Array();\n")
            idx = 0
            for path, p in self.pf.people.items():
                if p.fake or p.isPrivate():
                    continue
    
                path = path[len(self.pf.root)+1:]
                if obsfuc:
                    url = os.path.join(p.surname(), p.getIdStr(), PERSON_IDX)
                else:
                    url = os.path.join(path, PERSON_IDX)
                url = fwdslash(url)
                path = fwdslash(path)
                fh.write('profiles[%d] = ["%s", "%s", "Path: %s"]\n' % (idx, url, p.name(), path))
                idx += 1
