from ft_people import PersonFactory
from ft_build import MakeSearch
from osutils import fwdslash, islink, rm_rf
from ft_utils import HTML_IDX, MOTW, isPerson, TREE_NODE
import shutil
import os.path
import lxml.html
import urllib
from os.path import relpath

import binascii
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class Exporter:
    #SALT = os.urandom(16)
    SALT = bytes([13, 141, 85, 118, 69, 96, 89, 231, 199, 128, 94, 139, 14, 175, 242, 80])
    PASSPHRASE = 'z'
        
    def __init__(self, srcInstallRoot):
        self.srcInstallRoot = os.path.abspath(srcInstallRoot)
        self.srcTreeRoot = os.path.join(srcInstallRoot, TREE_NODE)
        self.pf = PersonFactory(self.srcTreeRoot)
        
    def export(self, expInstallRoot):
        self.expInstallRoot = os.path.abspath(expInstallRoot)
        self.expTreeRoot = os.path.join(expInstallRoot, TREE_NODE)
        
        rm_rf(self.expInstallRoot)
        os.makedirs(self.expTreeRoot)
        
        self.pf.scan()
        
        self.writeVersion()
        
        # export people
        for srcPath, p in self.pf.people.items():
            if p.fake or p.isPrivate():
                continue
            
            srcPath = p.path
            expPath = os.path.join(self.expTreeRoot, p.surname(), p.getIdStr())
            self.exportDir(srcPath, expPath)
                
        self.exportInfra()
        self.exportTrees()
        
    def writeVersion(self):
        version = self.pf.getVersion()
        version = "FT_" + version.replace(".", "_")
        with open(os.path.join(self.expTreeRoot, version), 'w') as fs:
            fs.write(version)
            
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
        
        ##self.exportDir(os.path.join(self.srcTreeRoot, "photo_albums"),
        ##               os.path.join(self.expTreeRoot, "photo_albums"))
        
    def exportTrees(self):
        self.copyFile(os.path.join(self.srcTreeRoot, HTML_IDX),
                      os.path.join(self.expTreeRoot, HTML_IDX))
        self.copyFile(os.path.join(self.srcTreeRoot, 'families.html'),
                      os.path.join(self.expTreeRoot, 'families.html'))
        
        for clan in self.pf.getClans():
            expClanRoot = os.path.join(self.expTreeRoot, clan)
            if not os.path.exists(expClanRoot):
                continue
            
            self.exportHtmlFile(os.path.join(self.srcTreeRoot, clan, "_clanTree.htm"),
                                os.path.join(expClanRoot, "_clanTree.htm"))
            # NF_DEBUG: TODO: CLANTREE PNG NEEDS TO BE A BASE64 IMG INSIDE HTML
            shutil.copy(os.path.join(self.srcTreeRoot, clan, "_clanTree.png"),
                        os.path.join(expClanRoot, "_clanTree.png"))
            ##self.copyFile(os.path.join(self.srcTreeRoot, clan, "_clanTree.png"),
            ##              os.path.join(expClanRoot, "_clanTree.png"))
            
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
            self.encryptBinary(src, dst+'.json')
         
    def exportHtmlFile(self, src, dst):
        with open(src, "r") as fs:    
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
                    path = os.path.join(self.expTreeRoot, p.surname(), p.getIdStr())
                    path = os.path.join(path, pathSeg)
                else:
                    path = os.path.join(self.expInstallRoot, path[len(self.srcInstallRoot) + 1:])
                    
                path = fwdslash(relpath(path, os.path.dirname(dst)))
                lnk = urllib.parse.urlunparse( ('', '', urllib.parse.quote(path), '', lnk.query, lnk.fragment) )

                # Encrypt any binaries (images etc) if under tree
                ext = os.path.splitext(lnk)[1]
                if pPathItem and (not ext in ['.css', '.htm', '.html', '.js']):
                    lnk += '.json'
                    
                el.attrib[attrib] = lnk

        self.encryptHtmlDOM(doc)
                
        with open(dst, "wb") as fs:
            fs.write(MOTW.encode("utf8"))
            fs.write(lxml.html.tostring(doc, doctype='<!DOCTYPE HTML>'))
                
    def encryptHtmlDOM(self, doc):
        title = doc.xpath('/html/head/title')[0]
        titleText = title.text
        doc.head.remove(title)
        
        txt = self.extractTxt(doc.body)
        doc.body.clear()
        txt += '<div hidden id="real_title">'+titleText+'</div>'
        
        hkdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=self.SALT, iterations=100000)
        key = hkdf.derive(self.PASSPHRASE.encode())
        
        iv = os.urandom(12)
        data = txt.encode("utf8")
        aesgcm = AESGCM(key)
        ct = aesgcm.encrypt(iv, data, None)
        
        iv_hex = binascii.b2a_hex(iv).decode("utf8")
        ct_hex = binascii.b2a_hex(ct).decode("utf8")
        
        content_div = lxml.etree.Element("div")
        content_div.set("id", 'encrypted_content')
        content_div.text = iv_hex+'-'+ct_hex
        doc.body.append(content_div)
        
    def extractTxt(self, node):
        txt = []
        for c in node.xpath("node()"):
            if type(c) == lxml.etree._ElementUnicodeResult:
                txt.append(str(c))
            else:
                txt.append(lxml.html.tostring(c, with_tail=False).decode())
        txt = "".join(txt)
        return txt
    
    def encryptBinary(self, fin, fout):        
        hkdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=self.SALT, iterations=100000)
        key = hkdf.derive(self.PASSPHRASE.encode())
        
        iv = os.urandom(12)

        with open(fin, 'rb') as fs:
            data = fs.read()

        aesgcm = AESGCM(key)
        ct = aesgcm.encrypt(iv, data, None)
        
        dictkey = os.path.basename(fout)
        
        with open(fout, 'wb') as fs:
            fs.write(b"gJSONP_objs.set('"+dictkey.encode('utf8')+b"', {\n");

            fs.write(b"iv: '")
            fs.write(base64.b64encode(iv))
            fs.write(b"',\n")

            fs.write(b"cipherdata: '")
            fs.write(base64.b64encode(ct))
            fs.write(b"'\n")
        
            fs.write(b"});\n");
        
    def splitPersonPath(self, path):
        splitpath = path.split(os.sep)
        plen = len(splitpath)
        while (plen > 0):
            tryPerson = os.sep.join(splitpath)
            p = self.pf.people.get(tryPerson)
            if p is not None:
                return (p, path[len(tryPerson) + 1:])
            del splitpath[plen-1]
            plen = len(splitpath)
        return None
