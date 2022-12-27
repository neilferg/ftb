
// non-deferred setup (called prior to reading the DOM)

// DEPENDENCIES:
// - iframe-resizer


var gOriginalUrl = null;

function clearUrlQuery() {
    let uri = window.location.toString();
    gOriginalUrl = uri;

    if (uri.indexOf("?") > 0) {
        let clean_uri = uri.substring(0, uri.indexOf("?"));
        window.history.replaceState({}, document.title, clean_uri);
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

function handleImageViewerMsg(msg) {
  let dto = msg.data;
  $.picbox(dto.url);
}

function sendImageViewerMsg(url) {
    let dto = {
        type: "image-viewer",
        url: url,
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

