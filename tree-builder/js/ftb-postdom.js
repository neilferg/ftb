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

async function ftb_main() {
    await decrypt(); // need to wait for this to complete before we can register

    let elements = document.getElementsByTagName('a');
    console.log("registering "+elements.length);
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

ftb_main();
