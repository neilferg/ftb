
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

function ftb_linkHandler_cb(e) {
    if (e.target.href.match('\.(jpg|png)')) {
        ftb_displayImage(this.href);
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

    return false;
}

function ftb_registerLinkHandlers(href_elements) {
    console.log(document.URL+": registering "+href_elements.length+" links");

    for(let i = 0, len = href_elements.length; i < len; i++) {
        if (href_elements[i].id == 'pbCloseBtn') { // picbox: leave alone (nasty hack)
            continue;
        }

        href_elements[i].onclick = ftb_linkHandler_cb;
    }
}

function loadJSScript(url) {
  return new Promise((resolve) => {
    let script_ele = document.createElement('script');
    script_ele.src = url;
    script_ele.onload = function() { resolve(); };
    document.head.appendChild(script_ele);
    document.head.removeChild(script_ele);
  });
}

