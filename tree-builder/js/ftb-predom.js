
// non-deferred setup (called prior to reading the DOM)

// DEPENDENCIES:
// - iframe-resizer


var gkey_hex = null;

function clearUrlQuery() {
    let url = new URL(window.location);
    let key_hex = url.searchParams.get('ftb_key');
    if (key_hex !== null) {
        gkey_hex = key_hex;
        url.searchParams.delete('ftb_key');
        window.history.replaceState({}, document.title, url.toString());

        // This ensures that back-navigate will always have the key
        //window.sessionStorage.setItem('ftb_key', gkey_hex);
        window.name = gkey_hex;
    }
}

// ============================================================================

clearUrlQuery();

document.addEventListener('DOMSubtreeModified', (e) => {
  // window 'load' event was not enough to fully detect the sizing
  //console.log(document.URL+":", e); 
  reportResizeInfo("dom change");
});

/*
const observer = new MutationObserver((mutations, observer) => {
  //console.log(document.URL+":", mutations); 
  reportResizeInfo("dom change");
});

observer.observe(document, {
  subtree: true,
  attributes: true,
  childList: true
});
*/

function isImageViewerMsg(msg) {
  return (msg.data.hasOwnProperty("type") && (msg.data.type === "image-viewer"));
}

async function handleImageViewerMsg(msg) {
  let dto = msg.data;
  ftb_displayImage_impl(dto.url, dto.key_hex);
}

function sendImageViewerMsg(url, key_hex) {
    let dto = {
        type: "image-viewer",
        url: url,
        key_hex: key_hex,
    };

    window.parent.postMessage(dto, '*');
}


// Handle posted iframe size DTOs from child
window.onmessage = (msg) => {
  if (isResizeInfoMsg(msg)) {
    handleResizeInfoMsg(msg);
  } else if (isImageViewerMsg(msg)) {
    handleImageViewerMsg(msg);
  }
}

