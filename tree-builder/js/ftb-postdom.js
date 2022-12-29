// deferred setup (called after DOM has loaded)

// DEPENDENCIES:
// - jquery.js
// - picbox.js
// - iframe-resizer.js

async function ftb_postdom_main() {
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
    
    ftb_registerLinkHandlers(document.getElementsByTagName('a'));
}

ftb_postdom_main();
