
//https://stackoverflow.com/questions/10787782/full-height-of-a-html-element-div-including-border-padding-and-margin
   function elementHeight(element) {
      var elmHeight = 0;
      var elmMargin = 0;
      if(document.all) {// IE
        elmHeight = element.currentStyle.height;
        if (!this.isNumeric(elmHeight)) {
          elmHeight = element.offsetHeight;
        }
        elmHeight = parseInt(elmHeight, 10);
        elmMargin = parseInt(element.currentStyle.marginTop, 10) + parseInt(element.currentStyle.marginBottom, 10);
      } else {// Mozilla
        elmHeight = parseInt(document.defaultView.getComputedStyle(element, '').getPropertyValue('height'), 10);
        elmMargin = parseInt(document.defaultView.getComputedStyle(element, '').getPropertyValue('margin-top'), 10) + parseInt(document.defaultView.getComputedStyle(element, '').getPropertyValue('margin-bottom'), 10);
      }
      return (elmHeight + elmMargin);
    }

   function elementWidth(element) {
      var elmWidth = 0;
      var elmMargin = 0;

      elmWidth = element.scrollWidth;

      if(document.all) {// IE
        elmMargin = parseInt(element.currentStyle.marginRight, 10);
      } else {// Mozilla
        elmMargin = parseInt(document.defaultView.getComputedStyle(element, '').getPropertyValue('margin-right'), 10);
      }

      //elmMargin = element.clientWidth - element.offsetWidth;

      return (elmWidth - elmMargin);
    }

  function reportResizeInfo(mode) {
    if (! document.body) {
      return;
    }
    var height = elementHeight(document.body);
    var width  = elementWidth(document.body);

    //console.log(document.URL+": sending msg: h="+height+", w="+width);

    let dto = {
        type: "resize",
        frameHeight: height,
        frameWidth: width
    };

    window.parent.postMessage(dto, '*');
  }

  function isResizeInfoMsg(msg) {
    return (msg.data.hasOwnProperty("type") && (msg.data.type === "resize"));
  }

  function handleResizeInfoMsg(msg) {
      let dto = msg.data;

      if (msg.source.window === this.window) { // reject messages from ourself
          return;
      }

      let child_width  = dto.frameWidth;
      let child_height = dto.frameHeight;

      console.log(document.URL+": msg rx: size: h="+child_height+" w="+child_width+": setting iframe");

      let iframe = document.getElementById("child_iframe")
      if (iframe) {
          iframe.height = child_height;
          iframe.width = child_width;
      } else {
          console.log("! No iframe node in DOM!");
      }
  }

