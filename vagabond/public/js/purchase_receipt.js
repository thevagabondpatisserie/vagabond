/* ----------- Phieu nhap kho: thu kho khong phai nhin gia

   ANH VIET HOI 31/08/2026
   -----------------------
   *"Anh cung khong hieu sao lai co gia tren phieu nhap kho? PNK anh tuong
   chi quan so luong, HSD?"*

   CAU TRA LOI NGAN: phieu nhap BAT BUOC phai co gia, nhung thu kho KHONG
   phai la nguoi go gia do.

   Trong ERPNext, don gia tren phieu nhap chinh la GIA VON NHAP KHO. No di
   thang vao So kho va So cai. Khong co con so do thi khong ghi so kho
   duoc. Nen khong bo o gia di duoc.

   Nhung con so do khong can thu kho nghi ra. No chay ngam:

     Bang gia nhap  ->  Don mua hang  ->  Phieu nhap kho  ->  hoa don nan lai

   Chang cuoi la cai it nguoi biet: thiet lap mua hang dang bat "lay gia
   von theo don gia tren hoa don mua". Nghia la khi ke toan ghi so to hoa
   don co noi phieu nhap, ERPNext tu dieu chinh gia von cua phieu nhap do
   theo dung don gia tren hoa don. Gia tren hoa don MOI LA GIA CUOI CUNG.

   Vay nen o gia tren man phieu nhap chi lam duoc mot viec: khien thu kho
   tuong minh phai go gi do vao do, roi go mot con so tu doan. Ban nay an
   no di voi nguoi lam kho, va noi ro cho ho biet gia von lay o dau.

   AN CHU KHONG XOA, VA AN THEO VAI
   --------------------------------
   Ke toan, thu mua, quan tri van thay nguyen o gia: ho la nguoi doi chieu
   voi hoa don, cat gia di la ho lam viec bang mat. Chi nguoi thuan lam kho
   moi duoc man hinh gon.

   Va day la AN TREN MAN HINH chu khong phai chan o may chu. Ai co quyen
   sua phieu nhap thi van sua duoc gia bang duong khac. Muc dich la bo mot
   o gay hieu nham khoi tam mat, khong phai lap mot hang rao. Noi ro ra de
   sau khong ai tuong day la khoa an toan. */

function vgbLaNguoiThuanKho() {
	var vai = frappe.user_roles || [];
	function co(x) { return vai.indexOf(x) >= 0; }

	/* Ai trong nhom nay cung PHAI thay gia. Nho hon mot chut la ke toan mat
	   duong doi chieu. */
	if (co('System Manager') || co('Accounts Manager') || co('Accounts User') ||
		co('Purchase Manager') || co('Purchase User') || co('Auditor')) {
		return false;
	}
	return co('Stock User') || co('Stock Manager');
}

function vgbAnCotGia(frm) {
	var luoi = frm.fields_dict && frm.fields_dict.items && frm.fields_dict.items.grid;
	if (!luoi) return;
	['rate', 'amount', 'price_list_rate', 'base_rate', 'base_amount',
		'discount_percentage', 'discount_amount', 'net_rate', 'net_amount'
	].forEach(function (o) {
		try { luoi.update_docfield_property(o, 'hidden', 1); } catch (e) {}
	});
	try { luoi.refresh(); } catch (e) {}
}

frappe.ui.form.on('Purchase Receipt', {
	refresh: function (frm) {
		/* Dong chu nay hien cho MOI NGUOI, ke ca ke toan. No tra loi dung cai
		   cau anh Viet hoi, va cau do chac chan khong chi mot minh anh hoi. */
		if (frm.doc.docstatus === 0) {
			frm.dashboard.add_comment(
				'Đơn giá trên phiếu nhập là <b>giá vốn tạm</b>, chảy xuống từ đơn ' +
				'mua hàng chứ không phải do thủ kho gõ. Khi kế toán ghi sổ hoá đơn ' +
				'mua có nối phiếu này, hệ tự nắn lại giá vốn theo <b>đơn giá trên ' +
				'hoá đơn</b>. Thủ kho chỉ cần đúng số lượng thực nhận, hạn sử dụng ' +
				'và kho nhận.',
				'blue', true);
		}

		if (!vgbLaNguoiThuanKho()) return;

		/* ERPNext dung o gia vao luoi kha muon. Goi nhieu nhip, cung bai hoc
		   cua ban v361: mot lan trong refresh la go truot. */
		vgbAnCotGia(frm);
		setTimeout(function () { vgbAnCotGia(frm); }, 0);
		setTimeout(function () { vgbAnCotGia(frm); }, 400);
	},
});
