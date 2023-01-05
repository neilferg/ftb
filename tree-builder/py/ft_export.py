from ft_people import PersonFactory
from ft_build import MakeSearch, MakeWeb
from osutils import fwdslash, islink, rm_rf
from ft_utils import HTML_IDX, MOTW, isPerson, TREE_NODE, PERSON_IDX_, isClan
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
                
                if (el.tag == 'img') and fileWillBeEncrypted:
                    # Hopefully this is just a small thumb file. We convert it to base64 and embed it
                    with open(srcPath, 'rb') as fs:
                        imgData = fs.read()
                    
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
    TREEROOT_FILES = ['families.html', 'help.htm', 'index.html', 'searchRecs.js']
    
    def __init__(self, pf, srcInstallRoot, expInstallRoot):
        self.pf = pf
        self.srcInstallRoot = srcInstallRoot
        self.srcInstallRoot_len = len(self.srcInstallRoot)
        self.srcTreeRoot = os.path.join(self.srcInstallRoot, TREE_NODE)
        self.srcTreeRoot_len = len(self.srcTreeRoot)
        
        self.expInstallRoot = expInstallRoot
        
        self.lookup = {}
        self.fileId = 1000
          
    def tryExtractPerson(self, srcPath):
        srcPathBase = srcPath[self.srcTreeRoot_len + 1:]
        srcPathBase_split = srcPathBase.split(os.sep)
        
        clan = srcPathBase_split[0]
        if not isClan(clan):
            return (None, None)
  
        plen = len(srcPathBase_split)
        while (plen > 0):
            tryPerson = os.path.join(self.srcTreeRoot, *srcPathBase_split)
            p = self.pf.people.get(tryPerson)
            if p is not None:
                return (clan, p)
                
            del srcPathBase_split[plen-1]
            plen = len(srcPathBase_split)
            
        return (clan, None)
    
    def getFileId(self, srcPath):
        fid = self.lookup.get(srcPath, None)
        if fid is None:
            fid = str(self.fileId)
            self.fileId += 1
            
            ext = os.path.splitext(srcPath)[1]
            fid += ext
            
            self.lookup[srcPath] = fid
        return fid
                   
    # TODO: 3rd party html documents may contain link references that we don't have locally
    def getRemappedName(self, srcPath):        
        encrypt = True
        rename = True
        
        if srcPath.startswith(self.srcTreeRoot):
            bn = os.path.basename(srcPath)
            clan, person = self.tryExtractPerson(srcPath)
            if person:
                expPath = os.path.join(self.expInstallRoot, TREE_NODE, str(self.pf.getClanId(clan)), person.getIdStr())
                rename = not (bn in [PERSON_IDX_])
            elif clan: # _clanTree.htm
                expPath = os.path.join(self.expInstallRoot, TREE_NODE, str(self.pf.getClanId(clan)))
                rename = not (bn in ["_clanTree.htm"])
            else:
                srcPathBase = srcPath[self.srcTreeRoot_len + 1:]
                
                if srcPathBase in self.TREEROOT_FILES: # @ tree root: keep there
                    rename = False
                    expPath = os.path.join(self.expInstallRoot, TREE_NODE)
                else: # other directories: flatten to other
                    expPath = os.path.join(self.expInstallRoot, TREE_NODE, 'other')
                
            if rename:
                expPath = os.path.join(expPath, self.getFileId(srcPath))
            else:
                expPath = os.path.join(expPath, bn)
        else: # Non 'tree'
            encrypt = False
            
            if srcPath.startswith(self.srcInstallRoot):
                # Just rebase
                srcPathBase = srcPath[self.srcInstallRoot_len + 1:]
                expPath = os.path.join(self.expInstallRoot, srcPathBase)
            elif srcPath == '/opt/ftb/tree-builder/css/ftb.css':
                # The user html files have the css hard coded to make it easier to
                # edit them standalone
                expPath = os.path.join(self.expInstallRoot,'ftb','dist','css','ftb.css')
            else:
                expPath = None
                
        return (expPath, encrypt)
    
