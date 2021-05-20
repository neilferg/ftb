#!/usr/bin/python3

from ft_utils import makelink_withbck, getLinkMaker


class Fixer:
    def __init__(self, dryrun):
        self.dryrun = dryrun
                
    def tryToFix(self, findings_file):
        cmdmap = {
            'CantRead': self.CantRead,
            'Auto': self.Auto,
            'Man': self.Man,
            'Backlink': self.Backlink
        }
        
        exec(compile(open(findings_file, "rb").read(), findings_file, 'exec'), cmdmap)
     
    def CantRead(self, tgt):
        pass
    
    def Man(self, link, link_origTgt, link_revisedTgt, status):
        pass
        
    def Auto(self, link, link_origTgt, link_revisedTgt, status):
        mklnk = getLinkMaker(link)
        makelink_withbck(link_revisedTgt, link, mklnk, dryrun=self.dryrun)

    def Backlink(self, link1, linkTgt1, link2, linkTgt2):
        mklnk = getLinkMaker(link1)
        makelink_withbck(linkTgt2, link2, mklnk, dryrun=self.dryrun)
