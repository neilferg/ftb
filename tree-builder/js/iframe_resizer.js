
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
    var height = elementHeight(document.body);
    var width  = elementWidth(document.body);

    let url = new URL(document.URL);

    console.log(document.URL+": sending msg: h="+height+", w="+width);

    let dto = {
        type: "resize",
        url: url.href,
        frameHeight: height,
        frameWidth: width
    };

    window.parent.postMessage(dto, '*');
  }

