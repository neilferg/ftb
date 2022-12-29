
async function ftb_tree_postdom_main() {
    let encrypted_content = document.getElementById("encrypted_content");
    let key_hex = null;
    if (encrypted_content) {
      key_hex = await getKey_hex();
      await ftb_decryptDocument(key_hex, encrypted_content);
    }

   let loc = window.location.hash.toString();
   if (loc.length > 0) {
      canvas = new jsGraphics("canvasOverlay");
      canvas.setColor("#ff0000");
      canvas.setStroke(3);

      id = loc.substring(1);

      if ($.browser.msie) {
         setTimeout('nav_and_set("' + id + '")', 200);
      } else {
         nav_and_set(id);
      }
   }
    
    ftb_registerLinkHandlers(document.getElementsByTagName('a'));
    ftb_registerLinkHandlers(document.getElementsByTagName('area'));
}

ftb_tree_postdom_main();

