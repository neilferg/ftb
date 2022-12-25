
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


// PARENT DOC

// This gets called by the parent. It intercepts the message that the
// child sends and resizes the iframe 

 function attachIFrameResizer() {
    // receive message from child iframe
    window.onmessage = (e) => {
      if (e.data.hasOwnProperty("frameHeight")) {
        var iframe = document.getElementById("child_iframe");

        var minHeight = 0;
        //minHeight = document.documentElement.clientHeight - 100;
        minHeight = window.innerHeight - 100;

        if (e.data.frameHeight < minHeight) {
            e.data.frameHeight = minHeight;
        }
	console.log("resize: h(min)="+e.data.frameHeight+"("+minHeight+") w="+e.data.frameWidth);

        iframe.style.width  = e.data.frameWidth;
        iframe.style.height = e.data.frameHeight;
      }
    };
 }


 // CHILD IFRAME

  const postIframeInfo = (mode) => {
    var height = elementHeight(document.body);
    var width  = elementWidth(document.body);

    console.log("report ("+mode
                 +"): h="+height
                 +" o="+document.body.offsetHeight
                 +" c="+document.body.clientHeight
                 +" s="+document.body.scrollHeight
                 +" w="+window.outerHeight);

      window.parent.postMessage({
        frameHeight: height,
        frameWidth: width
      }, '*');
  }

