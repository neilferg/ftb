// Define global variables
var profiles = null;

var F_URL = 0;
var F_TITLE = 1;
var F_TEXT = 2;
var F_MATCH = 3;

var numMatches = 0;
var docObj      = null;
var searchText  = "";
var resHtml = "";


function getProjRoot() {
    var i = location.href.lastIndexOf("/tree/");
    return (i != -1) ? location.href.substring(0, i) : "";
}

function getTreeRoot() {
    return getProjRoot() + "/tree";
}

async function doSearchBtn() {
    if (profiles === null) {
        let lookupTable = getTreeRoot() +'/searchRecs.js';
        let encrypted_content = document.getElementById("encrypted_content");
        if (encrypted_content) {
            lookupTable += '.json';
            let key_hex = await getKey_hex();
            let b64url = await fetchAndDecryptJSONPFile(lookupTable, key_hex)
            await loadJSScript(b64url);
        } else {
            await loadJSScript(lookupTable);
        }
    }

    var tb = document.getElementById("search-entry");
    searchText = tb.value.trim();
    tb.value = "";

    docObj = document.getElementById('docContent');
    convertString(searchText);
}

function doSearch(e) {
    if (e.which == 13 || e.keyCode == 13) {
        doSearchBtn();
        return false;
    }
    return true;
}

function convertString(reentry) {
   var searchArray = reentry.split(" ");
   
   markupMatches(searchArray);
   if (numMatches == 0) 
   {
      noMatch();
   } else {
      displayResults();
   }
}

function markupMatches(searchItems) {
   numMatches = 0;
   for (var i = 0; i < profiles.length; i++) {
      var tryStr = profiles[i][F_TITLE].toUpperCase();
      var numItemMatches = 0;
      for (j = 0; j < searchItems.length; j++) {
         var searchStr = searchItems[j].toUpperCase();
         var matchAt = tryStr.indexOf(searchStr);
         if (matchAt != -1) numItemMatches++;
      }
      
      if (numItemMatches == searchItems.length) {
         profiles[i][F_MATCH] = 1;
         numMatches++;
      } else {
         profiles[i][F_MATCH] = 0;
      }
   }
}

function noMatch() {
    resHtml = '<P><TABLE WIDTH=90% ALIGN=CENTER style="border:0;"><TR><TD VALIGN=TOP><FONT FACE=Arial><B><DL>' +
        //'<HR NOSHADE WIDTH=100%>' +
        'Search for person "' + searchText + '" returned no results.' +
        //'<HR NOSHADE WIDTH=100%>' +
        '</TD></TR></TABLE></P>';

    docObj.innerHTML = resHtml;
}

function displayResults() {
    resHtml = '<P><TABLE WIDTH=90% ALIGN=CENTER CELLPADDING=3 style="border:0;"><TR><TD>' +
        //'<HR NOSHADE WIDTH=100%>' +
        '</TD></TR><TR><TD VALIGN=TOP><FONT FACE=Arial><B>' +
        'Search Query: <I>' + searchText + '</I><BR>\n' +
        '<BR><BR></FONT>' +
        '<FONT FACE=Arial SIZE=-1><B>' + '\n\n<!-- Begin result set //-->\n\n\t<DL>';
 
    for (var i = 0; i < profiles.length; i++) {
       if (profiles[i][F_MATCH] > 0) {
          var url = getTreeRoot()  + '/' + profiles[i][F_URL]
          resHtml += '\n\n\t<DT>' + '<A HREF="' + url + '">' + profiles[i][F_TITLE] + '</A>' +
            '\t<DD>' + '<I>' + profiles[i][F_TEXT] + '</I>';
       }
    }
    resHtml += '\n\t</DL>\n\n<!-- End result set //-->\n\n';
    resHtml += //'<HR NOSHADE WIDTH=100%>' +
        '</TD>\n</TR>\n</TABLE></P>\n';

    docObj.innerHTML = resHtml;

    ftb_registerLinkHandlers(document.getElementsByTagName('a'));
}
