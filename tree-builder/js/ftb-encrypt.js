  // look up tables
  var to_hex_array = [];
  var to_byte_map = {};
  for (var ord=0; ord<=0xff; ord++) {
      var s = ord.toString(16);
      if (s.length < 2) {
          s = "0" + s;
      }
      to_hex_array.push(s);
      to_byte_map[s] = ord;
  }

  // converter using lookups
  function bufferToHex2(buffer) {
      var hex_array = [];
      //(new Uint8Array(buffer)).forEach((v) => { hex_array.push(to_hex_array[v]) });
      for (var i=0; i<buffer.length; i++) {
          hex_array.push(to_hex_array[buffer[i]]);
      }
      return hex_array.join('')
  }

  // reverse conversion using lookups
  function hexToBuffer(s) {
      var length2 = s.length;
      if ((length2 % 2) != 0) {
          throw "hex string must have length a multiple of 2";
      }
      var length = length2 / 2;
      var result = new Uint8Array(length);
      for (var i=0; i<length; i++) {
          var i2 = i * 2;
          var b = s.substring(i2, i2 + 2);
          result[i] = to_byte_map[b];
      }
      return result;
  }

  function arrayBufferToBase64URL(buffer) {
    let blob = new Blob([buffer], {type:'application/octet-binary'});
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.readAsDataURL(blob);
    });
  }

  function base64ToArrayBuffer(base64) {
    let raw = window.atob(base64);
    let rawLength = raw.length;
    let buf = new ArrayBuffer(rawLength);
    let array = new Uint8Array(buf);

    for(let i = 0; i < rawLength; i++) {
      array[i] = raw.charCodeAt(i);
    }
    return buf;
  }

  gJSONP_objs = new Map();

  function loadJSONPFile(jsonpFile) {
    return new Promise((resolve) => {
      let script_ele = document.createElement('script');
      script_ele.src = jsonpFile;
      script_ele.onload = function() {
          let i = script_ele.src.lastIndexOf("/"); // NF_DEBUG: TODO PUT FULL PATH W.R.T TREE ROOT
          let key = script_ele.src.substring(i+1);
          let obj = gJSONP_objs.get(key);
          resolve(obj);
          gJSONP_objs.delete(key);
      };
      document.head.appendChild(script_ele);
      document.head.removeChild(script_ele);
    });
  }

  async function exportCryptoKey(key) {
    const exported = await window.crypto.subtle.exportKey("raw", key);
    const exportedKeyBuffer = new Uint8Array(exported);
    return bufferToHex2(exportedKeyBuffer);
  }

  const SALT = new Uint8Array([13, 141, 85, 118, 69, 96, 89, 231, 199, 128, 94, 139, 14, 175, 242, 80]);

  async function getKey_hex() {
    //gkey_hex = null; window.sessionStorage.removeItem('ftb_key');

    if (! gkey_hex) {
      gkey_hex = window.sessionStorage.getItem('ftb_key');

      if (! gkey_hex) {
        let passphrase = promptForPassphrase();

        const enc = new TextEncoder();
        let pbkdfHash = await window.crypto.subtle.importKey(
                              "raw", enc.encode(passphrase),
                              {name: "PBKDF2"}, false,
                              ["deriveBits", "deriveKey"]);

        let key = await window.crypto.subtle.deriveKey(
                        {"name": "PBKDF2", salt: SALT, "iterations": 100000, "hash": "SHA-256"},
                        pbkdfHash, {"name": "AES-GCM", "length": 256}, true,
                        ["encrypt", "decrypt"]);
        gkey_hex = await exportCryptoKey(key);
        window.sessionStorage.setItem('ftb_key', gkey_hex);
      }
    }

    return gkey_hex;
  }

  async function getKey(key_hex) {
    return window.crypto.subtle.importKey("raw", hexToBuffer(key_hex), "AES-GCM", true, ["encrypt", "decrypt"]);
  }

  function clearKey() {
      window.sessionStorage.removeItem('ftb_key');
      gkey_hex = null;
  }

  // --------------------------------------------------------------------------

  function promptForPassphrase() {
    return window.prompt("Enter your password");
  }

  async function ftb_decryptDocument(key_hex, content) {
    console.log("decrypting "+document.URL );

    // An encrypted document consists of a <body> with one <div id=content> element.
    // This div contains hex bytes of the form <iv>-<ciphertext>
    // We extract these params, decrypt the ciphertext & use it to replace the div's text

    let [iv, ciphertext] = content.innerHTML.split("-")

    ciphertext = hexToBuffer(ciphertext);
    iv = hexToBuffer(iv);

    let key = await getKey(key_hex);

    try {
      let decrypted = await window.crypto.subtle.decrypt({name: "AES-GCM", iv: iv}, key, ciphertext);
      let dec = new TextDecoder();
      console.log("setting text "+document.URL );
      content.innerHTML = dec.decode(decrypted);
      console.log("set text "+document.URL );
      
      // There may be a hidden <div> in the decrypted body id=real_title. If so copy its
      // text to the <head><title>      
      let real_title = document.getElementById("real_title");
      if (real_title) {
        let title = document.createElement('title');
        title.innerHTML = real_title.innerHTML;
        document.head.appendChild(title);
      }
    } catch (e) {
      document.body.innerHTML = "*** Decryption error ***";
      clearKey();
    }
  }

  async function fetchAndDecryptJSONPFile(url, key_hex) {
    let encryptedImjObj = await loadJSONPFile(url);

    let iv = base64ToArrayBuffer(encryptedImjObj.iv);
    let cipherdata = base64ToArrayBuffer(encryptedImjObj.cipherdata);
    let key = await getKey(key_hex);

    try {
      let decrypted = await window.crypto.subtle.decrypt({name: "AES-GCM", iv: iv}, key, cipherdata);
      return arrayBufferToBase64URL(decrypted);
    } catch (e) {
      clearKey();
    }
  }
