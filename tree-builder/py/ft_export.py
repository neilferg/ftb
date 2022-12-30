from ft_people import PersonFactory, Person
from ft_build import MakeSearch, MakeWeb
from osutils import fwdslash, islink, rm_rf
from ft_utils import HTML_IDX, MOTW, isPerson, TREE_NODE
import shutil
import os.path
import lxml.html
import urllib
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
        
        photo_albums = os.path.join(self.srcTreeRoot, "photo_albums")
        if os.path.isdir(photo_albums):  
            self.exportDir(photo_albums,
                           os.path.join(self.expTreeRoot, os.path.basename(photo_albums)))
        
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
                if isPerson(d):
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
                 
                dst = src[len(srcPath) + 1:]
                dst = os.path.join(expPath, dst)
                
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
                path = urllib.parse.unquote(lnk.path)
                if path[0] == '/': # absolute
                    path = path[1:]
                else: # relative
                    path = os.path.join(os.path.dirname(src), path)
                path = os.path.normpath(path)
                
                pPathItem = self.splitPersonPath(path)
                if pPathItem is not None:
                    p, pathSeg = pPathItem
                    if isinstance(p, Person):
                        path = os.path.join(self.expTreeRoot, str(self.pf.getClanId(p.surname())), p.getIdStr())
                    else: # clan
                        path = os.path.join(self.expTreeRoot, p)
                        
                    path = os.path.join(path, pathSeg)
                else:
                    path = os.path.join(self.expInstallRoot, path[len(self.srcInstallRoot) + 1:])
                    
                path = fwdslash(relpath(path, os.path.dirname(dst)))
                
                # Non-html files that are under the tree will be encrypted as jsonp
                ext = os.path.splitext(path)[1]
                if pPathItem and (not ext in ['.css', '.htm', '.html', '.js']):
                    path += '.json'
                
                lnk = urllib.parse.urlunparse( ('', '', urllib.parse.quote(path), '', lnk.query, lnk.fragment) )
    
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
        
