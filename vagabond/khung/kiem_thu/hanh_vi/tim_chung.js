/* v583: nguon JS cua phep tim chung (vgbChuan, vgbKhop) cat THANG tu
 * 00-nen.js, de cac bo kiem hanh vi chi nap mot vai tep van co phep tim.
 * Khong chep lai than ham o day: doi phep tim trong 00-nen.js la ca kiem
 * chay theo ban moi ngay.
 */
'use strict';
var fs = require('fs');
var path = require('path');

function layHam(src, ten) {
  var dau = src.indexOf('function ' + ten + '(');
  if (dau < 0) throw new Error('Khong thay ham ' + ten);
  var i = src.indexOf('{', dau), sau = 0;
  for (var j = i; j < src.length; j++) {
    if (src[j] === '{') sau++;
    else if (src[j] === '}') { sau--; if (!sau) return src.slice(dau, j + 1); }
  }
  throw new Error('Ham ' + ten + ' khong dong ngoac');
}

var NEN = fs.readFileSync(path.resolve(__dirname, '..', '..', '..', 'public', 'js', 'bep', '00-nen.js'), 'utf8');
module.exports = layHam(NEN, 'vgbChuan') + '\n' + layHam(NEN, 'vgbKhop') + '\n';
