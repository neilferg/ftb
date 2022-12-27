// deferred setup (called after DOM has loaded)

// DEPENDENCIES:
// - jquery.js
// - picbox.js
// - iframe-resizer.js


async function ftb_displayImage(imgURL) {
    // We display all images in the top level window. This allows picbox to display
    // over the whole browser window rather than just that occupied by an iframe
    if (self.window === window.top) {
        if (imgURL.endsWith('.json')) { // encrypted
            imgURL = await fetchAndDecryptJSONPFile(imgURL);
            // NF_DEBUG: SHOULD PROBABLY REPLACE THE MIME PREFIX WITH THE CORRECT ONE FOR THE IMG. BUT IT SEEMS TO WORK...
        }
        $.picbox(imgURL);
    } else {
        // Send to top window to handle
        sendImageViewerMsg(imgURL);
    }
}

function ftb_clickHandler(e) {
  if ((e.target.nodeName === 'A') || (e.target.nodeName === 'AREA')) {
    e.preventDefault();
    if (e.target.href.match('\.(jpg|png)')) {
      ftb_displayImage(e.target.href);
    } else {
      let lnk = e.target.href;
      if (gkey_hex) {
        lnk += '?ftb_key='+gkey_hex;
      }
      if (e.target.target && (e.target.target === '_top')) {
        top.location.href = lnk;
      } else {
        window.location = lnk;
      }
    }
  }
} 

async function ftb_main() {
    await decrypt(); // need to wait for this to complete before we can register
    //ftb_registerLinkHandlers();
    document.addEventListener("click", ftb_clickHandler);
}

ftb_main();
