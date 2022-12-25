// deferred setup (called after DOM has loaded)

// DEPENDENCIES:
// - jquery.js
// - picbox.js
// - iframe-resizer.js


async function displayJsImage(imgURL) {
    let imgB64 = await fetchAndDecryptJSONPFile(imgURL);
    // NF_DEBUG: SHOULD PROBABLY REPLACE THE MIME PREFIX WITH THE CORRECT ONE FOR THE IMG. BUT IT SEEMS TO WORK...
    $.picbox(imgB64);
}

function ftb_registerLinkHandlers() {
    let elements = document.getElementsByTagName('a');
    console.log(document.URL+": registering "+elements.length+" <a> (links)");
    for(let i = 0, len = elements.length; i < len; i++) {
        elements[i].onclick = function () {
            if (this.href.match('\.(jpg\.json|png\.json)')) {
                console.log("encrypted image (json)");
                displayJsImage(this.href);
            } else if (this.href.match('\.(jpg|png)')) {
                console.log("normal image");
                $.picbox(this.href);
            } else {
                console.log("other link (may or may not be encrypted)");
                let lnk = this.href;
                if (gkey_hex) {
                  lnk += '?ftb_key='+gkey_hex;
                }
                if (this.target && (this.target === '_top')) {
                  top.location.href = lnk;
                } else {
                  window.location = lnk;
                }
            }

            return false;
        }
    }
}

function ftb_clickHandler(e) {
  if ((e.target.nodeName === 'A') || (e.target.nodeName === 'AREA')) {
    e.preventDefault();
    if (e.target.href.match('\.(jpg\.json|png\.json)')) {
      console.log("encrypted image (json)");
      displayJsImage(e.target.href);
    } else if (e.target.href.match('\.(jpg|png)')) {
      console.log("normal image");
      $.picbox(e.target.href);
    } else {
      console.log("other link (may or may not be encrypted)");
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
