from ft_people import PersonFactory, Person
from ft_build import MakeSearch, MakeWeb
from osutils import fwdslash, islink, rm_rf
from ft_utils import HTML_IDX, MOTW, isPerson, TREE_NODE, PERSON_IDX_
import shutil
import os.path
import lxml.html
import urllib
import base64
from os.path import relpath
from subprocess import check_call
from ft_encrypt_utils import encryptBinary, encryptHtmlDOM


class Exporter:
    def __init__(self, srcInstallRoot, args):
        self.args = args
        self.srcInstallRoot = os.path.abspath(srcInstallRoot)
        self.srcTreeRoot = os.path.join(srcInstallRoot, TREE_NODE)
        self.pf = PersonFactory(self.srcTreeRoot)
        
        # If PASSPHRASE is None, then no encryption
        self.PASSPHRASE = args.passphrase
        
    def export(self, expInstallRoot):
        self.expInstallRoot = os.path.abspath(expInstallRoot)
        self.expTreeRoot = os.path.join(expInstallRoot, TREE_NODE)
        self.remapper = FileRemapper(self.pf, self.srcInstallRoot, self.expInstallRoot)
        
        rm_rf(self.expInstallRoot)
        os.makedirs(self.expTreeRoot)
        
        self.pf.scan()
        
        # export people
        for srcPath, p in self.pf.people.items():
            if p.fake or p.isPrivate():
                continue
            
            srcPath = p.path
            expPath = os.path.join(self.expTreeRoot, str(self.pf.getClanId(p.surname())), p.getIdStr())
            self.exportDir(srcPath, expPath)
                
        self.exportInfra()
        self.exportTrees()
        
        if (self.args.win32_installer):
            self.buildWin32Installer()
            
    def exportInfra(self):
        src = os.path.join(self.srcInstallRoot, 'ftb', 'dist')
        src = os.path.realpath(src)
        
        dst = os.path.join(self.expInstallRoot, 'ftb', 'dist')
        rm_rf(dst)
        shutil.copytree(src, dst)
        
        self.copyFile(os.path.join(self.srcTreeRoot, 'help.htm'),
                      os.path.join(self.expTreeRoot, 'help.htm'))
        
        # Re-build the search index
        MakeSearch(self.pf, self.expTreeRoot).makeSearchIndex(obsfuc = True)
        
        indexFile = os.path.join(self.expTreeRoot,"searchRecs.js")
        encryptBinary(indexFile, indexFile+'.json', self.PASSPHRASE)
        os.remove(indexFile)
        
        other = os.path.join(self.srcTreeRoot, "other")
        if os.path.isdir(other):  
            self.exportDir(other,
                           os.path.join(self.expTreeRoot, os.path.basename(other)))
        
    def exportTrees(self):
        self.copyFile(os.path.join(self.srcTreeRoot, HTML_IDX),
                      os.path.join(self.expTreeRoot, HTML_IDX))
        
        MakeWeb(self.pf).makeRoot(os.path.join(self.expTreeRoot, "families.html"), True)
        
        for clan in self.pf.getClans():
            expClanRoot = os.path.join(self.expTreeRoot, str(self.pf.getClanId(clan)))
            if not os.path.exists(expClanRoot):
                continue
            
            self.exportHtmlFile(os.path.join(self.srcTreeRoot, clan, "_clanTree.htm"),
                                os.path.join(expClanRoot, "_clanTree.htm"))
            
    def exportDir(self, srcPath, expPath):
        print(srcPath, "->", expPath)
        os.makedirs(expPath, exist_ok=True)
        
        for root, dirs, files in os.walk(srcPath):
            skip = []
            for d in dirs:
                # nested people are covered elsewhere
                # 'thumbs' will be converted to base64 & embedded
                if isPerson(d) or (d == 'thumbs'):
                    skip.append(d)
                    continue
                
                src = os.path.join(root, d)
                
                if islink(src):
                    skip.append(d)
                else:
                    dst = src[len(srcPath) + 1:]
                    dst = os.path.join(expPath, dst)
                    os.makedirs(dst, exist_ok=True)
                    
            for s in skip:
                dirs.remove(s)
            
            for f in files:
                src = os.path.join(root, f)
                
                if islink(src):
                    continue
                
                dummy, ext = os.path.splitext(f)
                if ext in ['.tif']:
                    continue
                
                dst, encrypt = self.remapper.getRemappedName(src)
                 
                #dst = src[len(srcPath) + 1:]
                #dst = os.path.join(expPath, dst)
                
                print("  ", src, "->", dst)
                self.copyFile(src, dst)
                    
    def copyFile(self, src, dst):
        dummy, ext = os.path.splitext(src)
        if ext in ['.htm', '.html']:
            self.exportHtmlFile(src, dst)
        else:
            encryptBinary(src, dst+'.json', self.PASSPHRASE)
         
    def exportHtmlFile(self, src, dst):
        with open(src, "rb") as fs:    
            text = fs.read()
        doc = lxml.html.fromstring(text)
        #   e,  src/href, url, 
        for el, attrib, lnk, pos in doc.iterlinks():
            lnk = urllib.parse.urlsplit(lnk)
            if (lnk.scheme == "file" or len(lnk.scheme) == 0) and len(lnk.path) > 0:
                srcPath = urllib.parse.unquote(lnk.path)
                if srcPath[0] == '/': # absolute
                    pass #srcPath = srcPath[1:] # why are we removing this?
                else: # relative
                    srcPath = os.path.join(os.path.dirname(src), srcPath)
                srcPath = os.path.normpath(srcPath)
                
                expPath, fileWillBeEncrypted = self.remapper.getRemappedName(srcPath)
                ext = os.path.splitext(srcPath)[1]
                if 0:
                    # Unless the file is under the '/dist/' dir it will be encrypted
                    fileWillBeEncrypted = (not srcPath.startswith(os.path.join(self.srcInstallRoot,'ftb','dist')))
                    ext = os.path.splitext(srcPath)[1]
                    fileWillBeEncrypted = fileWillBeEncrypted and (not ext in ['.css', '.htm', '.html', '.js'])
     
                    pPathItem = self.splitPersonPath(srcPath)
                    if pPathItem is not None:
                        # a person path: these get flattened to CLAN/personId/
                        p, pathSeg = pPathItem
                        if isinstance(p, Person):
                            expPath = os.path.join(self.expTreeRoot, str(self.pf.getClanId(p.surname())), p.getIdStr())
                        else: # clan
                            expPath = os.path.join(self.expTreeRoot, p)
                            
                        expPath = os.path.join(expPath, pathSeg)
                    else:
                        expPath = os.path.join(self.expInstallRoot, srcPath[len(self.srcInstallRoot) + 1:])
                    
                if (el.tag == 'img') and fileWillBeEncrypted:
                    # Hopefully this is just a small thumb file. We convert it to base64 and embed it
                    with open(srcPath, 'rb') as fs:
                        imgData = fs.read()
                    ext = os.path.splitext(srcPath)[1]
                    ext = ext[1:]
                
                    lnk = "data:image/"+ext+";base64,"
                    lnk += base64.b64encode(imgData).decode("utf8")
                else:             
                    expPath = fwdslash(relpath(expPath, os.path.dirname(dst)))
                            
                    fileWillBeEncrypted = fileWillBeEncrypted and (not ext in ['.htm', '.html'])
                    if fileWillBeEncrypted:
                        expPath += '.json'
                    
                    lnk = urllib.parse.urlunparse( ('', '', urllib.parse.quote(expPath), '', lnk.query, lnk.fragment) )
        
                el.attrib[attrib] = lnk

        encryptHtmlDOM(doc, self.PASSPHRASE)
                
        with open(dst, "wb") as fs:
            fs.write(MOTW.encode("utf8"))
            fs.write(lxml.html.tostring(doc, doctype='<!DOCTYPE HTML>'))
        
    def splitPersonPath(self, path):
        splitpath = path.split(os.sep)
        plen = len(splitpath)
        while (plen > 0):
            tryPerson = os.sep.join(splitpath)
            p = self.pf.people.get(tryPerson)
            if p is not None:
                return (p, path[len(tryPerson) + 1:])
            else:
                clan = splitpath[plen-1]
                clanid = self.pf.clans.get(clan) 
                if clanid is not None:
                    return (str(clanid), path[len(tryPerson) + 1:])
                
            del splitpath[plen-1]
            plen = len(splitpath)
        return None
    
    def buildWin32Installer(self):
        INSTALLER_NSI = 'nsis-installer.nsi'
        
        with open(os.path.join(os.path.dirname(__file__), INSTALLER_NSI), 'r') as fs:
            text = fs.read()
             
        version = self.pf.getVersion()
        text = text.replace('PRODUCT_VERSION "1.0.0"', 'PRODUCT_VERSION "%s"' % (version))
        text = text.replace('PRODUCT_PUBLISHER "Bob Bampot"', 'PRODUCT_PUBLISHER "%s"' % (self.args.author))
        
        installer = os.path.join(self.expInstallRoot, INSTALLER_NSI)
        with open(installer, 'w') as fs:
            fs.write(text)
            
        check_call(['makensis', installer])
        
        PRODUCT_INSTALLER_NAME = "FT-installer.exe"
        installerAutogenExe = os.path.join(self.expInstallRoot, PRODUCT_INSTALLER_NAME)
        installerExe = os.path.join(self.expInstallRoot, "Family-tree-installer-v%s.exe" % (version))
        os.rename(installerAutogenExe, installerExe)

        
class FileRemapper:
    def __init__(self, pf, srcInstallRoot, expInstallRoot):
        self.pf = pf
        self.srcInstallRoot = srcInstallRoot
        self.srcInstallRoot_len = len(self.srcInstallRoot)
        self.srcTreeRoot = os.path.join(self.srcInstallRoot, TREE_NODE)
        self.srcTreeRoot_len = len(self.srcTreeRoot)
        
        self.expInstallRoot = expInstallRoot
        self.expInstallRoot_len = len(self.expInstallRoot)
        self.expTreeRoot = os.path.join(self.expInstallRoot, TREE_NODE)
        
        self.lookup = {}
        self.fileId = 1000
        
    def splitPersonPath(self, path):
        splitpath = path.split(os.sep)
        plen = len(splitpath)
        while (plen > 0):
            tryPerson = os.sep.join(splitpath)
            p = self.pf.people.get(tryPerson)
            if p is not None:
                return (p, path[len(tryPerson) + 1:])
            else:
                clan = splitpath[plen-1]
                clanid = self.pf.clans.get(clan) 
                if clanid is not None:
                    return (str(clanid), path[len(tryPerson) + 1:])
                
            del splitpath[plen-1]
            plen = len(splitpath)
        return None
        
    def getRemappedName(self, srcPath):
        srcPathBase = srcPath[self.srcInstallRoot_len + 1:]
        encrypt = True
        
        if srcPath.startswith(os.path.join(self.srcInstallRoot,'ftb','dist')):
            # non-encrypted  
            expPath = os.path.join(self.expInstallRoot, srcPathBase)
            encrypt = False
        elif srcPath == '/opt/ftb/tree-builder/css/ftb.css':
            # The user html files have the css hard coded to make it easier to
            # edit them standalone
            expPath = os.path.join(self.expInstallRoot,'ftb','dist','css','ftb.css')
            encrypt = False
        else: # /tree/
            # encrypted
            expPath = self.lookup.get(srcPath, None)
            if expPath is None:
                expPath = self.createRemap(srcPath)
                self.lookup[srcPath] = expPath
                
        return (expPath, encrypt)
    
    def makeFileId(self, ext):
        fileId = str(self.fileId)
        self.fileId += 1
        fileId += ext
        return fileId
                
    def createRemap(self, srcPath):
        ext = os.path.splitext(srcPath)[1]
        pPathItem = self.splitPersonPath(srcPath)
        if pPathItem is not None: # a person path
            # these get flattened to CLAN_ID/personId/fileId.ext
            # pathSeg is the portion of the filepath under the person
            p, pathSeg = pPathItem
            if isinstance(p, Person):
                expPath = os.path.join(self.expTreeRoot, str(self.pf.getClanId(p.surname())), p.getIdStr())
            else: # clan id str
                expPath = os.path.join(self.expTreeRoot, p)
                
            if pathSeg.endswith(PERSON_IDX_):
                # we can't obsfuscate this as it is in javascript
                expPath = os.path.join(expPath, pathSeg)
            else:
                expPath = os.path.join(expPath, self.makeFileId(ext))
        elif srcPath.startswith(self.srcTreeRoot):
            # anything else (i.e /other/), flatten to 1st dir only
        
            srcPathBase = srcPath[self.srcTreeRoot_len + 1:]
            splitpath = srcPathBase.split(os.sep)
            expPath = os.path.join(self.expInstallRoot, splitpath[0])
            expPath = os.path.join(expPath, self.makeFileId(ext))
        else:
            #print("No mapping for path: %s" % (srcPath))
            #expPath = self.expInstallRoot
            raise Exception("No mapping for path: %s" % (srcPath))
       
        return expPath
    