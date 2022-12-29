var canvas = null;
//var canvasHasDrawing = false;

function polyXcoords(coords) {
   var Xcoords = '';
   for (var z = 0; z < coords.length; z=z+2) {
      if (z > 0) { Xcoords += ', '; }
      Xcoords += parseInt(coords[z]);
   }
   return Xcoords;
}

function polyYcoords(coords) {
   var Ycoords = '';
   for (var z = 1; z<coords.length; z=z+2) {
      if (z > 1) { Ycoords += ', '; }
      Ycoords += parseInt(coords[z]);
   }
   return Ycoords;
}

function setFocusID(objid) {
   areaObj = document.getElementById(objid);
   setFocus(areaObj);
   return true;
}

function setFocus(objid) {
   canvas.clear();
   //if (canvasHasDrawing == true) canvas.clear();
   //return true;

   var coords = objid.coords.split(',');
   if ((objid.shape.toUpperCase() == 'POLY') || (objid.shape.toUpperCase() == 'POLYGON')) {
      var Xcoords = polyXcoords(coords);
      var Ycoords = polyYcoords(coords);
      var pgx = Xcoords.split(',');
      var pgy = Ycoords.split(',');
      for (var i=0 ; i < pgx.length ; i++ ) {
         pgx[i] = parseInt(pgx[i]);
         pgy[i] = parseInt(pgy[i]);
      }
      canvas.drawPolygon(pgx,pgy);
   } else if ((objid.shape.toUpperCase() == 'RECT') || (objid.shape.toUpperCase() == 'RECTANGLE')) {
      var width = coords[2] - coords[0];
      var height = coords[3] - coords[1];
      canvas.drawRect(parseInt(coords[0]),parseInt(coords[1]),parseInt(width),parseInt(height));
   } else {
      var topX = coords[0] - coords[2];
      var topY = coords[1] - coords[2];
      var diameter = coords[2] * 2;
      canvas.drawEllipse(parseInt(topX),parseInt(topY),parseInt(diameter),parseInt(diameter));
   }
   canvas.paint();
   //canvasHasDrawing = true;
   return true;
}

function clearFocus(objid) {
   //if (canvasHasDrawing)
   canvas.clear();
   canvasHasDrawing = false;
   return true;
}

function clearFocusID(objid) {
   areaObj = document.getElementById(objid);
   clearFocus(areaObj);
   return true;
}

function nav_and_set(id) {
   var obj = document.getElementById(id);
   var coords = obj.coords.split(',');
   var x = coords[0];
   var y = coords[1];
   window.scrollTo(x, y);

   if ($.browser.msie) {
      // for Firefox set strokeWidth = 3
      $('.map').maphilight( { strokeWidth: 2, neverOn: true, fillOpacity: 0 } );

      var data = $('#' + id).data('maphilight') || {};
      data.alwaysOn = true;
      $('#' + id).data('maphilight', data).trigger('alwaysOn.maphilight'); 
   } else  {
      setFocus(obj)
   }
}

