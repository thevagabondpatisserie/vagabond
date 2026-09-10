/* Phieu thu/chi tren Desk tu dien so va ngay tham chieu khi chuyen khoan.

   Core kiem `mandatory_depends_on` o TRINH DUYET sau nhịp validate, truoc
   khi request toi may chu. Hook Python truoc day dung nhung khong bao gio
   duoc goi trong ca Dung va Uyen chup ngay 10/09/2026. Do do can dien ngay
   trong validate cua dung Payment Entry. Co ma FT/so sec that thi giu.

   Chi dung cho Payment Entry, khong gan hook rong tren moi form. */

(function () {
	function trong(x) {
		return !String(x || '').trim();
	}

	function chamNganHang(doc) {
		return String(doc.paid_from || '').trim().indexOf('112') === 0
			|| String(doc.paid_to || '').trim().indexOf('112') === 0
			|| doc.paid_from_account_type === 'Bank'
			|| doc.paid_to_account_type === 'Bank';
	}

	function dien(doc) {
		if (!chamNganHang(doc)) return [];
		var ngay = doc.posting_date || frappe.datetime.get_today();
		var daDien = [];
		if (trong(doc.reference_no)) {
			doc.reference_no = 'CK-' + String(ngay).replace(/[^0-9]/g, '');
			daDien.push('reference_no');
		}
		if (!doc.reference_date) {
			doc.reference_date = ngay;
			daDien.push('reference_date');
		}
		return daDien;
	}

	frappe.ui.form.on('Payment Entry', {
		validate: function (frm) {
			var daDien = dien(frm.doc);
			daDien.forEach(function (o) { frm.refresh_field(o); });
		}
	});

	// Chi mo cho bo kiem hanh vi Node, khong tao bien toan cuc tren Desk.
	if (typeof module !== 'undefined') module.exports = { dien: dien };
})();
