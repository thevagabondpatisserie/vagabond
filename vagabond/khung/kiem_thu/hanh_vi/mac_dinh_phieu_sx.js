/* #206: chạy handler thật, đổi mục đích không để PSX dính sang phiếu khác. */
const fs = require('fs'), vm = require('vm'), assert = require('assert');
let suKien;
vm.runInNewContext(fs.readFileSync('vagabond/public/js/san_xuat_phieu.js', 'utf8'), {
	frappe: {meta: {get_docfield: () => ({default: 'MAT-STE-.YYYY.-'})},
		ui: {form: {on: (dt, h) => {suKien = h;}}}}
});
function phieu(mucDich='Manufacture', mau='MAT-STE-.YYYY.-', moi=true) {
	return {doc: {name:'new-thu', purpose:mucDich, naming_series:mau},
		is_new: () => moi, async set_value(k, v) { this.doc[k]=v; suKien.naming_series(this); }};
}
(async () => {
	let p=phieu(); await suKien.onload(p);
	assert.equal(p.doc.naming_series,'PSX-.YYYY.-');
	p.doc.purpose='Material Transfer'; await suKien.purpose(p);
	assert.equal(p.doc.naming_series,'MAT-STE-.YYYY.-');
	p.doc.purpose='Manufacture'; await suKien.purpose(p);
	assert.equal(p.doc.naming_series,'PSX-.YYYY.-');
	for (const p of [phieu('Manufacture','MAU-RIENG'),phieu('Manufacture','MAT-STE-.YYYY.-',false),phieu('Material Receipt')]) {
		let cu=p.doc.naming_series; await suKien.onload(p); assert.equal(p.doc.naming_series,cu);
	}
	p=phieu(); await suKien.onload(p);
	p.doc.naming_series='CHON-TAY'; suKien.naming_series(p);
	p.doc.purpose='Material Receipt'; await suKien.purpose(p);
	assert.equal(p.doc.naming_series,'CHON-TAY');
	// Đổi mục đích lúc set_value còn chờ cũng phải rút gợi ý PSX.
	p=phieu(); let tiep;
	p.set_value=async function(k,v) {this.doc[k]=v; suKien.naming_series(this); if(v==='PSX-.YYYY.-') await new Promise(r=>tiep=r);};
	let cho=suKien.onload(p); p.doc.purpose='Material Receipt'; await suKien.purpose(p); tiep(); await cho;
	assert.equal(p.doc.naming_series,'MAT-STE-.YYYY.-');
	console.log('PASS: mẫu PSX mới, đổi mục đích, chọn tay, phiếu cũ và phản hồi muộn');
})().catch(e=>{console.error(e);process.exit(1);});
