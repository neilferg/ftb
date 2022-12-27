// deferred setup (called after DOM has loaded)

// DEPENDENCIES:
// - jquery.js
// - picbox.js
// - iframe-resizer.js


async function ftb_displayImage(imgURL) {
    // We display all images in the top level window. This allows picbox to display
    // over the whole browser window rather than just that occupied by an iframe
    let key_hex = null;
    if (imgURL.endsWith('.json')) { // encrypted
        key_hex = await getKey_hex();
    }

    if (self.window === window.top) {
        ftb_displayImage_impl(imgURL, key_hex);
    } else {
        // Send to top window to handle
        sendImageViewerMsg(imgURL, key_hex);
    }
}

async function ftb_displayImage_impl(imgURL, key_hex) {
    if (key_hex) { // imgURL is json with encrypted base64
        imgURL = await fetchAndDecryptJSONPFile(imgURL, key_hex);
        // NF_DEBUG: SHOULD PROBABLY REPLACE THE MIME PREFIX WITH THE CORRECT ONE FOR THE IMG. BUT IT SEEMS TO WORK...
    }
    $.picbox(imgURL);
}

async function ftb_clickHandler(e) {
  if ((e.target.nodeName === 'A') || (e.target.nodeName === 'AREA')) {
    e.preventDefault();
    if (e.target.href.match('\.(jpg|png)')) {
      ftb_displayImage(e.target.href);
    } else {
      let lnk = e.target.href;
      if (gkey_hex) {
        let url = new URL(lnk);
        url.search = '?ftb_key='+gkey_hex;
        lnk = url.toString();
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
    let encrypted_content = document.getElementById("encrypted_content");
    let key_hex = null;
    if (encrypted_content) {
      key_hex = await getKey_hex();
      await ftb_decryptDocument(key_hex, encrypted_content);
    }

    // Set the iframe's source page. We do this here so we can send the
    // encryption key
    let iframe = document.getElementById("child_iframe")
    if (iframe) {
      let lnk = gftb_childIframeSrc;
      if (key_hex) {
        lnk += '?ftb_key='+key_hex;
      }
      iframe.src = lnk;
    }
    
    document.addEventListener("click", ftb_clickHandler);
}

ftb_main();
