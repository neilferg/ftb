#!/usr/bin/python3

import sys, os
import argparse

from ft_utils import getTreeRoot, TREE_NODE
from check_links import LinkAnalyser
from fix_links import Fixer
import ft_build
from ft_admin import cleanupfiles, init_new
from ft_bond import bond, PartnerLink
from convert_links import Converter
from update_html_head import UpdateVrs, FILES_ALL_FTLOADER, FILES_ALL_HTML, FILES_VRS_ONLY


linkTypes = ['url']
if os.name == 'posix':
    linkTypes.append('sym')
elif os.name == 'nt':
    linkTypes.append('scut')


def handle_init(args):
    init_new(allowNonEmpty=args.non_empty, addExample=args.example)

def handle_bld(args):
    treeRoot = args.treeroot
    if treeRoot is None:
        treeRoot = getTreeRoot()
    pf = ft_build.initAndScan(treeRoot)
    ft_build.MakeWeb(pf).make()
            
def handle_chk(args):
    treeRoot = args.treeroot
    if treeRoot is None:
        treeRoot = getTreeRoot()
        
    LinkAnalyser(treeRoot, args.findings).analyse(args.backlinks)

def handle_fix(args):
    Fixer(args.dryrun).tryToFix(args.findings_file[0])
    
def handle_clean(args):
    treeRoot = args.treeroot
    if treeRoot is None:
        treeRoot = getTreeRoot()
    cleanupfiles(treeRoot, args.dryrun)

def handle_convert(args):
    treeRoot = args.treeroot
    if treeRoot is None:
        treeRoot = getTreeRoot()
    
    incomingRootNode = args.root_node
    
    converter = Converter(args.dryrun, treeRoot, incomingRootNode, args.link_type, args.abs_links)
    converter.convert_links()

def handle_update(args):
    treeRoot = args.treeroot
    if treeRoot is None:
        treeRoot = getTreeRoot()
        
    if args.all and (not args.vronly):
        consider = FILES_ALL_HTML
    elif args.vronly and (not args.all):
        consider = FILES_VRS_ONLY
    elif (not args.vronly) and (not args.all):
        consider = FILES_ALL_FTLOADER
    else:
        raise Exception("Invalid args: -a=%s, -v=%s" % (args.all, args.vronly))

    UpdateVrs(treeRoot, consider).scan(args.dryrun)
    
def handle_bond(args):
    if args.relationship is None:
        args.relationship = PartnerLink.REL_PARTNER
        
    bond(args.partner[0], args.relationship, linkType=args.link_type, force=args.force)

 
def cli(cliargs = None):
    parser = argparse.ArgumentParser()

    subparser = parser.add_subparsers(title='These are common ftb commands used in various situations',
                                      metavar='command')
    
    # init command
    #-------------
    init_parser = subparser.add_parser('init', help="Initialise new tree")
    
    init_parser.add_argument('-z', '--non-empty', action="store_true", default=False,
                            help='Create even if directory is not empty')
    init_parser.add_argument('-x', '--example', action="store_true", default=False,
                            help="Add an example tree")
    
    init_parser.set_defaults(handle=handle_init)
     
    # build command
    #--------------
    bld_parser = subparser.add_parser('build', help="Build")
    
    # Optional parameters
    
    # The positional parameter optionally specifies the tree-root
    bld_parser.add_argument('treeroot', metavar='treeroot', type=str, nargs='?',
                            help='Tree Root (default search cwd)')
    
    bld_parser.set_defaults(handle=handle_bld)
    
    # chklinks command
    # ----------------
    chk_parser = subparser.add_parser('chklinks', help="Check links")
    
    # Optional parameters
    chk_parser.add_argument('-f', '--findings', type=str, default='findings',
                            help='Filename where findings will be written')
    chk_parser.add_argument('-b', '--backlinks', action="store_true", default=False,
                            help='Check for missing backlinks (ensure all bad links have been fixed first')
    
    # The positional parameter optionally specifies the tree-root
    chk_parser.add_argument('treeroot', metavar='treeroot', type=str, nargs='?',
                            help='Tree Root (default search cwd)')
    
    chk_parser.set_defaults(handle=handle_chk)
    
    # fixlinks command
    # ----------------
    fix_parser = subparser.add_parser('fixlinks', help="Fix links")
    # Optional parameters
    fix_parser.add_argument('-d', '--dryrun', action="store_true", default=False,
                            help='Not for real')
    
    # The positional parameter specifies the findings file
    fix_parser.add_argument('findings_file', metavar='findings_file', type=str, nargs=1,
                            help='Findings file (from previous check)')
    fix_parser.set_defaults(handle=handle_fix)
    
    # clean command
    #--------------
    clean_parser = subparser.add_parser('clean', help="Clean")
    
    # Optional parameters
    clean_parser.add_argument('-d', '--dryrun', action="store_true", default=False,
                            help='Not for real')
    
    # The positional parameter optionally specifies the tree-root
    clean_parser.add_argument('treeroot', metavar='treeroot', type=str, nargs='?',
                              help='Tree Root (default search cwd)')
    
    clean_parser.set_defaults(handle=handle_clean)
    
    # convert command
    #----------------
    convert_parser = subparser.add_parser('convert', help="Convert links")
    
    # Optional parameters
    convert_parser.add_argument('-l', '--link_type', type=str, default='url', choices=linkTypes,
                                help='Link type to be used')
    convert_parser.add_argument('-a', '--abs_links', action="store_true", default=False,
                                help='Use absolute paths in sym links')
    convert_parser.add_argument('-r', '--root_node', type=str, default=TREE_NODE,
                                help='Alternative tree root node (for incoming targets)')
    convert_parser.add_argument('-d', '--dryrun', action="store_true", default=False,
                                help='Not for real')

    # The positional parameter optionally specifies the tree-root
    convert_parser.add_argument('treeroot', metavar='treeroot', type=str, nargs='?',
                                help='Tree Root (default search cwd)')
    
    convert_parser.set_defaults(handle=handle_convert)
    
    # update command
    #---------------
    update_parser = subparser.add_parser('update', help="Update")
    
    # Optional parameters
    update_parser.add_argument('-d', '--dryrun', action="store_true", default=False,
                               help='Not for real')
    update_parser.add_argument('-a', '--all', action="store_true", default=False,
                               help='Consider all html files (not just ftLoader)')
    update_parser.add_argument('-v', '--vronly', action="store_true", default=False,
                               help='Vital Record html files only')

    # The positional parameter optionally specifies the tree-root
    update_parser.add_argument('treeroot', metavar='treeroot', type=str, nargs='?',
                               help='Tree Root (default search cwd)')
    
    update_parser.set_defaults(handle=handle_update)
    
    # bond command
    # ------------
    bond_parser = subparser.add_parser('bond', formatter_class=argparse.RawTextHelpFormatter,
                                       description="Create partner link(s) (bond)")
    
    bond_parser.add_argument('-m', '--my-path', type=str, default=None,
                             help='My Path (default: current directory)')
    bond_parser.add_argument('-l', '--link-type', type=str, default=None, choices=linkTypes,
                             help='Link type to be used')
    bond_parser.add_argument('-f', '--force', action="store_true", default=False,
                             help='Force: any existing links will be overwritten')
    
    # The positional parameter specifies the path to the partner & the relationship
    bond_parser.add_argument('partner', metavar='partner', type=str, nargs=1,
                             help='''Partner path. There are two forms:
1) A tree directory path to the person:
    The path may be absolute or relative to <MY_PATH>
    Two links are created:
    - <MY_PATH>/'<relationship>. <partner>'
    - <partner>/'{h|w|p}. <MY_PATH>'
2) A name of the form 'CLAN/Forename':
    This will create a one sided null link:
    - <MY_PATH>/'<relationship>. <partner>''')
    bond_parser.add_argument('relationship', metavar='relationship', type=str, nargs='?', choices=['h','w','p'], default='p',
                             help='Partner relationship {%(choices)s}. Default p')
    
    bond_parser.set_defaults(handle=handle_bond)
    
    # =====================================================
    
    
    args = parser.parse_args(cliargs)
    
    if hasattr(args, 'handle'):
        args.handle(args)
    else:
        parser.print_help()
    
##

if __name__ == '__main__':
    try:
        cli()
    except Exception as e:
        print('ERROR: '+str(e))
        sys.exit(1)

    sys.exit(0)
    
