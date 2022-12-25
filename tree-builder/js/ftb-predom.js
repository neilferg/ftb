
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

clearUrlQuery();

document.addEventListener('DOMSubtreeModified', (e) => {
  // window 'load' event was not enough to fully detect the sizing
  console.log(document.URL+":", e); 
  reportResizeInfo("dom change");
})

// Handle posted iframe size DTOs from child
window.onmessage = (e) => {
  let dto = e.data;

  if (dto.hasOwnProperty("type") && (dto.type === "resize")) { // resize DTO
    let url = new URL(document.URL);
    if (dto.url === url.href) { // reject messages from ourself
        return;
    }

    let child_width  = dto.frameWidth;
    let child_height = dto.frameHeight;

    console.log(document.URL+": msg rx: size: h="+child_height+" w="+child_width+": setting iframe");

    let iframe = document.getElementById("child_iframe")
    if (iframe) {
        iframe.height=child_height;
        iframe.width=child_width;
    } else {
        console.log("! No iframe node in DOM!");
    }
  }
}

