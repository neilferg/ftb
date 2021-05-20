import os
import ntpath
import urllib, urllib.request
import struct
from configparser import RawConfigParser
from subprocess import check_call
import shutil


# These are intended to be used as suffixes to temporary/backup files
BCKf = '__bck_'
TMPf = '__tmp_'

def rm_rf(path):
    if os.name == 'nt':
        # Don't trust rmtree on windows: with junctions it recurses into the junction
        # deleting!
        if os.path.exists(path):
            check_call('rmdir /s /q "%s"' % (path), shell=True)
    else:
        shutil.rmtree(path, ignore_errors=True)

def fwdslash(fp):
    return fp.replace('\\', '/')

def stripKnownSuffixes(f, suffixes):
    # This was intended as an alternative to os.path.splitext. If that were to be
    # used on a symlink spouse link ('w. ' etc) then it would split wrongly:
    # 'w. My Name.lnk'
    #   |_ The split would be ('w', ' My Name.lnk') not what we want!
    # So instead strip off KNOWN suffixes
    for suffix in suffixes:
        if f.endswith(suffix):
            pos = len(f) - len(suffix)
            return f[0:pos]
    return f

# from linux: path2url('/etc/passwd') -> 'file:///etc/passwd'
# urllib.url2pathname(urlparse.urlsplit('file:///etc/passwd').path) -> '/etc/passwd'

# from win:   path2url("C:\gitco"))   -> 'file:///C:/gitco'
# urllib.url2pathname(urlparse.urlsplit('file:///C:/gitco').path) -> r'C:\gitco'
# from linux:                                                     -> r'/C:/gitco'

def path2url(path):
    # path MUST BE ABSOLUTE!
    return urllib.parse.urljoin('file:', urllib.request.pathname2url(path))

def url2path(url):
    return urllib.request.url2pathname(urllib.parse.urlsplit(url).path)


# Links. We follow the python convention used in os.symlink(src, dst)
# src: this what the link will be pointing TO (the target)
# dst: this is the filename that the link will be created as

INTERNET_SCUT_SUFFIX = '.url'
WINDOWS_SCUT_SUFFIX  = '.lnk'

# Code here modified from:
# https://stackoverflow.com/questions/397125/reading-the-target-of-a-lnk-file-in-python

#                     00021401-0000-0000-C000-000000000046
msShortcutCLSID   = b'\x01\x14\x02\x00\x00\x00\x00\x00\xC0\x00\x00\x00\x00\x00\x00\x46'

# flags (uint32)
HasLinkTargetIDList = 0x00000001
HasLinkInfo         = 0x00000002
HasName             = 0x00000004
HasRelativePath     = 0x00000008
HasWorkingDir       = 0x00000010
HasArguments        = 0x00000020
HasIconLocation     = 0x00000040
IsUnicode           = 0x00000080
ForceNoLinkInfo     = 0x00000100
HasExpString        = 0x00000200

def _readStringObj(scContent, pos, isUnicode):
    """returns: tuple: (newPosition, string)"""
    strg = ''
    size = struct.unpack('H', scContent[pos:pos+2])[0] # num characters 
    
    if isUnicode:
        size *= 2
        strg = struct.unpack(str(size)+'s', scContent[pos+2:pos+2+size])[0]
        strg = strg.decode('utf-16')               
    else:
        strg = struct.unpack(str(size)+'s', scContent[pos+2:pos+2+size])[0]
        strg = strg.decode('cp1252')

    pos += size + 2 # +2 for the num chars prefix

    return (pos, strg)

def _extractUtf8ZBytes(buf):
    '''Extract a null terminated char string (utf-8)'''       
    pos = buf.find(b'\x00')
    return buf[0:pos]
        
def _extractUtf16ZBytes(buf):
    '''Extract a null terminated wchar string (utf-16)'''
    for i in range(0, len(buf), 2):
        if buf[i:i+2] == b'\x00\x00':
            return buf[0:i]
    return b''


if os.name == 'nt':
    try:
        import win32api
        import pywintypes
        import win32com.client
    except ImportError:
        print("pywin32 package not available")
        pass
    
    wscriptShell = []
    def getWscriptShell():
        shell = None
        if len(wscriptShell) == 0:
            shell = win32com.client.Dispatch("WScript.Shell")
            wscriptShell.append(shell)
        else:
            shell = wscriptShell[0]
        return shell
    
    def makelink_scut(tgt, linkName):
        if not linkName.endswith(WINDOWS_SCUT_SUFFIX):
            raise Exception("linkName must have '%s' extension" % (WINDOWS_SCUT_SUFFIX))

        # CreateShortCut embeds both a absolute and relative path to the tgt 
        if not os.path.isabs(tgt):
            tgt = os.path.join(os.path.dirname(linkName), tgt)

        linkName = os.path.normpath(linkName)
        shortcut = getWscriptShell().CreateShortCut(linkName)
        shortcut.TargetPath = os.path.normpath(tgt)
        shortcut.save()
        
else: # linux
      
    def makelink_scut(tgt, linkName):
        raise NotImplementedError()


def readlink_url(linkName):
    config = RawConfigParser()
    config.read(linkName)
    url = config.get('InternetShortcut', 'URL')

    if not url.startswith("file:"):
        raise Exception("Malformed URL %s" % (url))
    return url2path(url)

# same footprint as os.symlink(src, dst)
def makelink_url(tgt, linkName):
    '''Create an InternetShortcut link pointing to tgt named linkName.
    '''
    if not linkName.endswith(INTERNET_SCUT_SUFFIX):
        raise Exception("linkName must have '%s' extension" % (INTERNET_SCUT_SUFFIX))
    
    if os.path.isdir(linkName):
        linkName = os.path.join(linkName, os.path.basename(tgt))
    
    if not os.path.isabs(tgt):
        tgt = os.path.join(os.path.dirname(linkName), tgt)
        
    tgt = os.path.normpath(tgt)
    
    url = path2url(tgt)
    dat = '''[InternetShortcut]
URL=%s
IDList=
HotKey=0
IconFile=C:\\windows\\system32\\SHELL32.dll
IconIndex=4
''' % (url)

    with open(linkName, 'w') as fs:
        fs.write(dat)
        
# Code here modified from:
# https://stackoverflow.com/questions/397125/reading-the-target-of-a-lnk-file-in-python

def readlink_scut(linkName):
    with open(linkName, 'rb') as fs:
        content = fs.read()
    
    localBasePath = None
    commonPathSuffix = None
    relativePath = None

    # verify header size
    hdrSize = struct.unpack('I', content[0x00:0x04])[0]
    expHdr_sz = 76
    if hdrSize != expHdr_sz:
        raise Exception("MS Shortcut HeaderSize Error")

    # verify LinkCLSID id (16 bytes)            
    _clsid = bytes(struct.unpack('B'*16, content[0x04:0x14]))
    if _clsid != msShortcutCLSID:
        raise Exception("MS Shortcut ClassID Error")        

    # read the LinkFlags structure (4 bytes)
    flags = struct.unpack('I', content[0x14:0x18])[0]
    
    isUnicode = ((flags & IsUnicode) > 0)
    
    pos = expHdr_sz # Skip past the header

    # if HasLinkTargetIDList bit, then pos to skip the stored IDList structure and header
    if (flags & HasLinkTargetIDList):
        idListSize = struct.unpack('H', content[pos:pos+0x02])[0]
        pos += 2
        pos += idListSize

    # if HasLinkInfo, then process the linkinfo structure  
    if (flags & HasLinkInfo):
        (linkInfoSize, linkInfoHdrSize, _linkInfoFlags, 
         volIdOffset, localBasePathOffset, 
         cmnNetRelativeLinkOffset, cmnPathSuffixOffset) = struct.unpack('IIIIIII', content[pos:pos+28])

        # check for optional offsets
        localBasePathOffsetUnicode = None
        cmnPathSuffixOffsetUnicode = None
        
        if linkInfoHdrSize >= 0x24:
            (localBasePathOffsetUnicode, cmnPathSuffixOffsetUnicode) = struct.unpack('II', content[pos+28:pos+36])

        # if info has a localBasePath
        if (_linkInfoFlags & 0x01):     
            if localBasePathOffsetUnicode:
                bpPosition = pos + localBasePathOffsetUnicode
                localBasePath = _extractUtf16ZBytes(content[bpPosition:])
                localBasePath = localBasePath.decode('utf-16')
            else:
                bpPosition = pos + localBasePathOffset
                localBasePath = _extractUtf8ZBytes(content[bpPosition:])
                localBasePath = localBasePath.decode('cp1252')

        # get common Path Suffix    
        if cmnPathSuffixOffsetUnicode:
            cmnSuffixPosition = pos + cmnPathSuffixOffsetUnicode
            commonPathSuffix = _extractUtf16ZBytes(content[cmnSuffixPosition:])
            commonPathSuffix = commonPathSuffix.decode('utf-16')
        else:
            cmnSuffixPosition = pos + cmnPathSuffixOffset               
            commonPathSuffix = _extractUtf8ZBytes(content[cmnSuffixPosition:])
            commonPathSuffix = commonPathSuffix.decode('cp1252')

        pos += linkInfoSize 

    if (flags & HasName):
        (pos, _name) = _readStringObj(content, pos, isUnicode)  

    if (flags & HasRelativePath):
        (pos, relativePath) = _readStringObj(content, pos, isUnicode)
    
    #if (flags & HasWorkingDir):
    #    (pos, _workingDir) = _readStringObj(content, pos, isUnicode)
    #    print(_workingDir)
    
    #print(relativePath)
    #print(localBasePath, commonPathSuffix)
    
    if relativePath:
        return relativePath
    
    if localBasePath and commonPathSuffix:
        return ntpath.join(localBasePath, commonPathSuffix)
    
    raise Exception("Unable to retrieve target path from MS Shortcut: shortcut = %s" % (linkName))

def readlink_f(linkName): # resolve links and return absolute path
    '''Read link target. This returns an absolute path'''
    if linkName.endswith(INTERNET_SCUT_SUFFIX):
        return readlink_url(linkName) # always absolute
    elif linkName.endswith(WINDOWS_SCUT_SUFFIX):
        tgt = readlink_scut(linkName)
        if not ntpath.isabs(tgt):
            linkName = os.path.abspath(linkName)      
            pth = os.path.join(os.path.dirname(linkName), tgt)
        return pth
    elif os.path.islink(linkName):
        return os.path.realpath(linkName) # realpath ensures an absolute path
    raise ValueError("Can't read link target")

def getLinkSuffix(mklnk_func):
    if mklnk_func == makelink_url:
        return INTERNET_SCUT_SUFFIX
    elif mklnk_func == makelink_scut:
        return WINDOWS_SCUT_SUFFIX
    else: # assume symlink
        return ''

def islink(fullpath):
    return os.path.islink(fullpath) or fullpath.endswith(INTERNET_SCUT_SUFFIX) or fullpath.endswith(WINDOWS_SCUT_SUFFIX) 

# This makelink creates links in windows and linux that can be used
# for direct file access.
def makelink(src, lnk):
    if os.name == 'posix':
        os.symlink(src, lnk)
    else:
        if os.path.isfile(src):
            _ln_file(src, lnk)
        elif os.path.isdir(src):
            _ln_dir(src, lnk)
        else:
            raise Exception("Unknown src type")

def _ln_dir(srcDir, lnkDir):
    '''Create <lnkDir> as a windows junction'''
    if os.path.exists(lnkDir):
        os.rmdir(lnkDir)
    lnkDir = os.path.abspath(lnkDir)
    srcDir = os.path.normpath(srcDir) # may be relative
    if not os.path.isabs(srcDir): # relative
        srcDir = os.path.join(os.path.dirname(lnkDir), srcDir)
        srcDir = os.path.normpath(srcDir)
        
    check_call(['cmd', '/c', 'mklink', '/j', lnkDir, srcDir])   
    
def _ln_file(srcFile, lnkFile):
    if os.path.isdir(lnkFile):
        lnkFile = os.path.join(lnkFile, os.path.basename(srcFile)) 
        if os.path.exists(lnkFile):
            os.remove(lnkFile)        
    CreateHardLink(lnkFile, srcFile)
    
# n.b this won't work in the pydebugger
try:
    import msvcrt
    getch = msvcrt.getch
except:
    import sys, tty, termios
    def _unix_getch():
        """Get a single character from stdin, Unix version"""

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())          # Raw read
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    getch = _unix_getch
    
def oktodo(prompt):
    print(prompt+" [Y/n]")
    c = getch()
    return c in ['y', 'Y', '\r']

def getFileVersion(f): 
    if not os.path.exists(f):
        return "0.0.0.0"
    
    info = GetFileVersionInfo(f, "\\")
    ms = info['FileVersionMS']
    ls = info['FileVersionLS']
    return ".".join ([str (i) for i in [HIWORD(ms), LOWORD(ms), HIWORD(ls), LOWORD(ls)] ])
