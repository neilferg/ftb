Packages

python-dateutil
python-lxml
graphviz

User Project file system layout
-------------------------------

.../[project]/                <- PROJ_ROOT (one level above 'tree' dir)
              ft/             <- FTBUILDER_ROOT - the FT builder (git checkout; also one level above 'tree' dir) 
              tree/           <- TREE_ROOT - family tree root 'tree' name is mandatory
                   index.htm  <- web brower entry point
                   help.htm   <- help pages entry point
                   BAMPOT/    <- clan (surname) must be in BLOCK CAPITALS
                          Bob <- person (forename) must be captialised lowercase
                          
If the tree is being hosted on a windows host, be aware of the 260 file path
length restriction. It may be prudent to place the project root in C:\ (e.g C:\ft)
              