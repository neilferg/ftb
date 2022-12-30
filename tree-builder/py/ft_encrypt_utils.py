import os
import base64
import binascii
import lxml.html
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
  
#SALT = os.urandom(16)
SALT = bytes([13, 141, 85, 118, 69, 96, 89, 231, 199, 128, 94, 139, 14, 175, 242, 80])
   
def encryptBinary(fin, fout, passphrase):        
    hkdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=100000)
    key = hkdf.derive(passphrase.encode())
    
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

def encryptHtmlDOM(doc, passphrase):
    titleText = None
    title = doc.xpath('/html/head/title')
    if len(title) > 0:
        title = title[0]
        titleText = title.text
        doc.head.remove(title)
    
    txt = _extractTxt(doc.body)
    doc.body.clear()
    if titleText is not None:
        txt += '<div hidden id="real_title">'+titleText+'</div>'
    
    hkdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=100000)
    key = hkdf.derive(passphrase.encode())
    
    iv = os.urandom(12)
    data = txt.encode("utf8")
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(iv, data, None)
    
    iv_hex = binascii.b2a_hex(iv).decode("utf8")
    ct_hex = binascii.b2a_hex(ct).decode("utf8")
    
    content_div = lxml.etree.Element("div")
    content_div.set("hidden", '')
    content_div.set("id", 'encrypted_content')
    content_div.text = iv_hex+'-'+ct_hex
    doc.body.append(content_div)
            
def _extractTxt(node):
    txt = []
    for c in node.xpath("node()"):
        if type(c) == lxml.etree._ElementUnicodeResult:
            txt.append(str(c))
        else:
            txt.append(lxml.html.tostring(c, with_tail=False).decode())
    txt = "".join(txt)
    return txt
