/* ---------------- Danh sach Cong thuc tren Desk (ban Khai xin 25/08/2026)

   Ban Khai: *"Anh chinh keo rong cai nay giup em de em xem cai phien ban
   BOM"*. Cot dau cua danh sach dang cat mat duoi so cua ten BOM, ma duoi
   do CHINH LA so phien ban: `BOM-BTPB00007-002`.

   VI SAO KHONG CHI NOI CAI COT RA
   -------------------------------
   Be rong cot cua danh sach Frappe nam trong user settings cua TUNG NGUOI,
   sinh ra khi ho tu keo mep cot. Khong co API nao dat ho duoc, va ghi
   thang vao bang `__UserSettings` cua nguoi khac la thu ma quy tac 6 cua
   repo cam: dung vao ha tang cua Frappe.

   Nen cach o day la dat so phien ban vao CHIP trang thai. Chip la mot API
   co that cua Frappe (`get_indicator`), no nam ben phai va KHONG BAO GIO
   bi cat, du man hinh hep den may. Ban Khai doc duoc phien ban ma khong
   phai keo gi ca.

   Tien the co luon chip trang thai anh Viet xin: nhin mot cai la biet ban
   nao dang dung, ban nao la ban cu, ban nao con nhap.

   Con phan noi cot thi van lam, nhung bang CSS va coi la khuyen mai: neu
   Frappe doi cau truc HTML thi doan CSS do nam im chu khong lam hong gi.

   MOT CAI BAY DA TRANH
   --------------------
   ERPNext CO SAN mot `bom_list.js` cua rieng no. Gan de len
   `frappe.listview_settings['BOM']` la xoa trang phan cua ho, ke ca
   `add_fields` ma cac phan khac cua ERPNext dang dua vao. Nen o day GOP
   chu khong gan de. */

(function () {
	var CU = frappe.listview_settings['BOM'] || {};

	function duoiPhienBan(ten) {
		/* Giong het `cong_thuc.duoi_phien_ban` ben Python. Doi ben phai
		   ra cung mot ket qua, co ca kiem chot chuyen do. */
		var t = String(ten || '').trim();
		if (t.indexOf('-') < 0) return '';
		var duoi = t.split('-').pop();
		return /^[0-9]+$/.test(duoi) ? duoi : '';
	}

	function noiCot() {
		/* Khuyen mai, khong phai duong song. Frappe doi HTML thi doan nay
		   nam im. */
		if (document.getElementById('vgbBomCot')) return;
		var st = document.createElement('style');
		st.id = 'vgbBomCot';
		st.textContent =
			'[data-page-route="List/BOM/List"] .list-row-col:first-child,' +
			'[data-page-route="List/BOM/List"] .list-subject {' +
			'  flex: 2.2 1 0 !important; min-width: 260px !important; }' +
			'[data-page-route="List/BOM/List"] .list-subject .level-left {' +
			'  overflow: visible !important; }';
		document.head.appendChild(st);
	}

	frappe.listview_settings['BOM'] = Object.assign({}, CU, {
		add_fields: (CU.add_fields || []).concat([
			'item', 'item_name', 'is_active', 'is_default', 'docstatus',
		]),

		onload: function (lv) {
			noiCot();
			if (typeof CU.onload === 'function') CU.onload(lv);
		},

		refresh: function (lv) {
			noiCot();
			if (typeof CU.refresh === 'function') CU.refresh(lv);
		},

		get_indicator: function (doc) {
			var v = duoiPhienBan(doc.name);
			var dau = v ? 'v' + v + ' · ' : '';
			/* Thu tu nay quan trong: da huy va con nhap phai xet TRUOC
			   is_default, vi mot ban da huy van co the con giu co
			   is_default tu luc no con song. */
			if (cint(doc.docstatus) === 2) {
				return [dau + 'Đã huỷ', 'gray', 'docstatus,=,2'];
			}
			if (cint(doc.docstatus) === 0) {
				return [dau + 'Nháp', 'orange', 'docstatus,=,0'];
			}
			if (cint(doc.is_default) && cint(doc.is_active)) {
				return [dau + 'Đang dùng', 'green', 'is_default,=,1'];
			}
			if (cint(doc.is_active)) {
				return [dau + 'Còn hiệu lực', 'blue', 'is_active,=,1'];
			}
			return [dau + 'Bản cũ', 'gray', 'is_active,=,0'];
		},
	});
})();
