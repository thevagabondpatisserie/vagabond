/* ----------- Hoa don mua sinh tu hoa don dien tu: bo nut pha dong hang

   ANH VIET HOI 31/08/2026
   -----------------------
   *"Day la hoa don day ve sao lai phai lay mat hang tu? No noi phieu vao
   thoi roi anh xa chu nhi?"*

   Dung. Va do la ly do to hoa don cua Kamereo va cua Pha Che Viet cu hien
   ra sai tren man hinh.

   HAI NUT DUNG CANH NHAU, MOT NUT PHA
   -----------------------------------
   Tren thanh cong cu cua Hoa don mua co hai nut nhin gan giong nhau:

     "Noi phieu nhap kho"  - nut cua tiem. GAN dong hoa don vao dong phieu
                             nhap. Khong dung toi so luong, khong dung toi
                             don gia.
     "Lay mat hang tu"     - nut co san cua ERPNext. CHEP dong hang cua
                             phieu nhap DE LEN dong hang cua hoa don.

   Bam nut thu hai tren mot to hoa don day ve tu m-invoice la mat trang
   dong hang goc.

   CA THAT, KAMEREO 271846 NGAY 27/08/2026
   ---------------------------------------
   Hoa don dien tu co 6 dong, tong 417.400 d. Trong so co mot dong "Phi
   dich vu" 30.000 d va mot dong ca chua 2 Kg.

   Sau khi co nguoi bam "Lay mat hang tu" va chon bon phieu nhap kho cua
   ngay hom do, man hinh thanh:

     - ca chua tach lam HAI dong 1 Kg, vi hang ve lam hai chuyen nen co
       hai phieu nhap rieng (PNK-2026-00181 va PNK-2026-00246);
     - mat han dong Phi dich vu, vi phi dich vu khong di qua kho nen
       khong co phieu nhap nao;
     - tong tut tu 417.400 xuong 385.000.

   Ba trieu chung Uyen bao deu tu mot cai bam nut. Du lieu trong so KHONG
   he sai: to HDM-26-08-00216 van du 6 dong va van 417.400 d, vi ho chua
   bam Luu.

   VI SAO KHONG DE NGUYEN ROI DAN NGUOI TA DUNG BAM
   ------------------------------------------------
   Vi da dan roi va van xay ra. Ngay 17/08 mat 135.720 d cua Thanh An
   Eggpack cung vi nut nay; ban v318 chi CANH BAO luc luu, tuc va bang loi
   dan; ban v319 them hook dung lai dong hang moi lan luu, tuc va bang
   luoi do.

   Luoi do cuu duoc SO SACH nhung khong cuu duoc NGUOI. Uyen van thay man
   hinh sai, van tuong he thong hong, van bao len, va moi lan nhu vay la
   mot buoi lam viec cua ca ba nguoi. Ngay 31/08 la lan thu ba trong hai
   tuan.

   Nen ban nay bo han cai nut do di, va chi bo tren dung nhung to sinh tu
   hoa don dien tu. To go tay van con nut nhu cu, vi to go tay khong co
   ban goc nao de pha. */

/* THU TU CHAY, va day la cho ban dau lam sai (31/08/2026)
   -------------------------------------------------------
   Ban dau go nut ngay trong `refresh`. Deploy xong mo to Kamereo ra thi
   nut VAN CON: `refresh` cua tep nay chay TRUOC luc bo dieu khien cua
   ERPNext gan nut vao thanh cong cu, nen go xong ho gan lai.

   Do bang tay tren Desk: goi remove_custom_button luc trang da dung han
   thi so cum nut tut tu 2 xuong 1, tuc phep go dung, chi sai thoi diem.

   Nen goi lam nhieu nhip: ngay lap tuc de bat truong hop ho gan som, roi
   0ms va 400ms de bat truong hop ho gan sau. Goi thua khong sao, vi go
   mot cai nut khong con o do la khong lam gi ca. */

function vgbGoNutLayMatHang(frm) {
	var tu_hddt = (frm.doc.custom_minvoice_id || '').trim();
	if (!tu_hddt) return;
	if (frm.doc.docstatus !== 0) return;

	/* Nhom nut duoc ERPNext them bang add_custom_button(label, fn,
	   __("Get Items From")), tuc TEN NHOM DA DICH khi site chay tieng
	   Viet. Nen go bang ca hai ten, ai dung ten nao thi trung ten do. */
	var nhom = ['Get Items From', 'Lấy mặt hàng từ'];
	var nut = ['Purchase Order', 'Purchase Receipt', 'Đơn mua hàng', 'Phiếu nhập kho'];
	nhom.forEach(function (g) {
		nut.forEach(function (b) {
			try {
				frm.remove_custom_button(b, g);
			} catch (e) {
				/* Khong co nut do thi thoi. */
			}
		});
	});

	/* LUOI DO CUOI: neu ERPNext doi ten nut o ban sau thi vong tren go
	   truot, va nut lai hien ra. Nen an luon ca cum theo nhan. Chi AN
	   bang CSS chu khong xoa phan tu: xoa nham mot cum khac la hong nut
	   cua nguoi khac, con an nham thi chi mat mot nut. */
	try {
		frm.page.wrapper.find('.inner-group-button').each(function () {
			var t = ($(this).text() || '').trim();
			if (t.indexOf('Lấy mặt hàng từ') === 0 || t.indexOf('Get Items From') === 0) {
				$(this).hide();
			}
		});
	} catch (e) {
		/* Phan nay la khuyen mai, hong cung khong duoc keo do man hinh. */
	}
}

frappe.ui.form.on('Purchase Invoice', {
	refresh: function (frm) {
		var tu_hddt = (frm.doc.custom_minvoice_id || '').trim();
		if (!tu_hddt) return;
		if (frm.doc.docstatus !== 0) return;

		vgbGoNutLayMatHang(frm);
		setTimeout(function () { vgbGoNutLayMatHang(frm); }, 0);
		setTimeout(function () { vgbGoNutLayMatHang(frm); }, 400);

		/* Noi ro cho nguoi dung biet vi sao khong con nut, va bam nut nao
		   thay the. Khong noi thi ho di tim, va di tim thi lai mo Desk goc
		   ra bam. */
		frm.dashboard.add_comment(
			'Tờ này dựng từ hoá đơn điện tử nên dòng hàng khoá theo bản gốc. ' +
			'Muốn gắn phiếu nhập kho thì bấm <b>Nối phiếu nhập kho</b>, nút đó ' +
			'chỉ gắn chứ không sửa số lượng và đơn giá. Nút <b>Lấy mặt hàng từ</b> ' +
			'của ERPNext đã được gỡ khỏi tờ này vì nó chép đè dòng hàng, làm mất ' +
			'những dòng không đi qua kho như phí dịch vụ và phí giao hàng.',
			'blue',
			true
		);
	},
});
