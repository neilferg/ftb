import os.path
import lxml.html
import urllib
from os.path import relpath
import fnmatch
from ft_people import isPerson
from osutils import fwdslash, islink
from ft_utils import PRIVATE


VREC_HTML_FILES = [ 'birth_search.htm*', 'death_search.htm*', 'marriage*search.htm*',
                    'birth.*', 'death.*', 'marriage.*',
                    'birth_cert.htm*', 'death_cert.htm*', 'marriage*cert.htm*',
                    'census_search.htm*',
                    'other_notes.htm*',
                  ]

AUTOGEN_FILES = [ 'www_*.htm*' ]
JUNK_FILES = [ '*.tif', PRIVATE ]

EXCLUDE = VREC_HTML_FILES[:]
EXCLUDE.extend(AUTOGEN_FILES)
EXCLUDE.extend(JUNK_FILES)

def exclude(item, excludeList):
    for e in excludeList:
        if fnmatch.fnmatch(item, e):
            return True
    return False

class FindLocalLinks:
    HTML_EXT = [ ".HTM", ".HTML" ]
    
    def __init__(self, localDir):
        self.localDir = localDir
        self.scanHtmlFiles()

    def scanHtmlFiles(self):
        self.files = []
        for f in os.listdir(self.localDir):
            if exclude(f, AUTOGEN_FILES):
                continue
            dummy, ext = os.path.splitext(f)
            if not ext.upper() in self.HTML_EXT:
                continue
            self.findAll(os.path.join(self.localDir, f))

    def selectFile(self, f):
        comps = urllib.parse.urlparse(f)
        f = comps[2]
        if comps[0] == '':
            pass
        elif comps[0] == 'file':
            f = fwdslash(relpath(f, self.localDir))
        else:
            f = None
        return f
    
    def findAll(self, f):
        with open(f, "r") as fs:
            text = fs.read()
        doc = lxml.html.fromstring(text)

        # look for links and images
        for tag, attrib in [ (".//a", "href"), (".//img", "src") ]:
            for i in doc.findall(tag):
                try: # not all <a> anchors have hrefs
                    f = self.selectFile(i.attrib[attrib])
                except:
                    f = None
                if f is not None: self.files.append(f)

    def isFileReferenced(self, f):
        return f in self.files

class DirCat: 
    def __init__(self, root):
        self.root = root
        self.FOLDER_ICON = os.path.join(self.root,'..','ftb','dist','images','folder.png')
        
    def cat(self, path, excludes = None):
        lclLinks = FindLocalLinks(path)
        if excludes is None:
            excludes = EXCLUDE
        htmlText = [ '<table style="border:0; margin-left: 40px;"><thead><tr><td><br></td><th>Name</th></tr></thead><tbody>' ]
        files = []
        dirs = []
        for i in os.listdir(path):
            i_fullpath = os.path.join(path, i)
            
            if exclude(i, excludes) or lclLinks.isFileReferenced(i) or isPerson(i) or islink(i_fullpath):
                continue
            
            if os.path.isdir(i_fullpath):
                dirs.append(i)
            else:
                files.append(i)

        for f in files:
            htmlText.extend(self.row(path, f, False))
            
        for d in dirs:
            htmlText.extend(self.row(path, d, True))
            
        htmlText.append('</tbody></table>')
        return (len(files) + len(dirs)), "".join(htmlText)
        
    def row(self, path, item, isDir):
        rowText = [ '<tr>' ]
        if isDir:
            rowText.append('<td><img src="%s" alt="Dir:" border="0"></td>' % (fwdslash(relpath(self.FOLDER_ICON, path))))
        else:
            rowText.append('<td><br></td>')

        rowText.append('<td><a href="%s">%s</a></td>' % (urllib.parse.quote(item), item))
        rowText.append("</tr>")
        return rowText
