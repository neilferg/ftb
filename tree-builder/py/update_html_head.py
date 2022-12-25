#!/usr/bin/python3

import sys, os
import fnmatch
import lxml.html

THIS_DIR = os.path.abspath(os.path.dirname(__file__))

from osutils import BCKf, TMPf

# filename globs of the files that we'll uppdate
VREC_HTML_FILES = [ 'birth_search.htm*', 'death_search.htm*', 'marriage*_search.htm*',
                    'census_search.htm*', 'other_notes.htm*'
                  ]
HTML_FILES = [ '*.htm', '*.html' ]

FILES_ALL_FTLOADER = 0
FILES_ALL_HTML     = 1
FILES_VRS_ONLY     = 2


class UpdateVrs:
    def __init__(self, root, consider):
        self.root = os.path.abspath(root)
        # Use the NewPerson/birth_search.htm as the template
        self.templateFile = os.path.abspath(os.path.join(THIS_DIR,'..','..','templates','NewPerson','birth_search.htm'))
        self.consider = consider   
        if self.consider == FILES_VRS_ONLY:
            self.filesglob = VREC_HTML_FILES
        else: # FILES_ALL_HTML & FILES_ALL_FTLOADER (with script id check)
            self.filesglob = HTML_FILES

    def loadHeadTemplate(self, templateFile):   
        with open(templateFile, "rb") as fs:
            text = fs.read()
        htmlDoc = lxml.html.fromstring(text)
        newHead = htmlDoc.xpath('/html/head')[0]    
        return newHead
    
    def candidateFile(self, f):
        for e in self.filesglob:
            if fnmatch.fnmatch(f, e):
                return True
        return False 

    def scan(self, dryRun):
        newHead = self.loadHeadTemplate(self.templateFile)
                   
        for root, dirs, files in os.walk(self.root):
            for f in files:
                if not self.candidateFile(f):
                    continue
                
                fp = os.path.join(root, f)
                
                if fp == self.templateFile: # not the template
                    continue
                
                tmpfp = os.path.join(root, TMPf+f)
                bckfp = os.path.join(root, BCKf+f)
                
                sys.stdout.write("%s" % (fp)) # ...
                
                with open(fp, "rb") as fs:
                    text = fs.read()
                doc = lxml.html.fromstring(text)
                
                if (self.consider != FILES_ALL_HTML):
                    ftLoader = doc.xpath("/html/head/script[@id='ftLoader']")
                    if len(ftLoader) != 1:
                        sys.stdout.write(" NOT a ftLoader script - SKIPPING\n")
                        continue
                
                oldhead = doc.xpath('/html/head')[0]
                bdy = oldhead.getparent()
                
                # We'll delete the entire <head> element, but before we do
                # grab its <title> if it has one
                
                docTitle = doc.xpath('/html/head/title')
                if len(docTitle) != 0:
                    docTitle = docTitle[0].text
                else:
                    docTitle = ""
                
                sys.stdout.write(" ('%s') -> %s\n" % (docTitle, tmpfp))
                
                bdy.insert(bdy.index(oldhead)+1, newHead)
                bdy.remove(oldhead)
                
                title = doc.xpath('/html/head/title')[0]
                title.text = docTitle
                
                if dryRun:
                    print("rename(%s,\n" \
                          "       %s)" % (fp, bckfp))
                    print("rename(%s,\n" \
                          "       %s)" % (tmpfp, fp))
                else:                    
                    # Write to temp file first
                    with open(tmpfp, "wb") as fs:
                        fs.write( lxml.html.tostring(doc, doctype='<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">') )
                    
                    # Backup existing  
                    if os.path.exists(bckfp):
                        os.remove(bckfp)
                    os.rename(fp, bckfp)
                    
                    # Move new file into place
                    os.rename(tmpfp, fp)
                    
                    #os.remove(bckfp)
                