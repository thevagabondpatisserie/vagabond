/* ------------- Man danh sach Phieu thu / Phieu chi

   Anh Viet noi 05/09/2026, nguyen van: *"Phieu thu/chi ve ban chat la
   tien mat thi anh thay van lung tung khach o trong phieu thu/chi. No
   chang phai la APP gi ca."*

   Anh noi dung. Co SAU nghiep vu hoan toan khac nhau, cua sau nguoi khac
   nhau, dang do chung vao dung mot man nay:

     1. Thu tien khach tra hoa don ban
     2. Tra cong no nha cung cap
     3. Tra truoc cho nha cung cap, tuc dat coc khi chua co hoa don
     4. Hoan ung cho nhan vien, di qua mot ban ghi Supplier doi lot
     5. Hoan tien cho khach khi don bi huy hoac khach nop thua
     6. Chuyen tien noi bo giua hai tai khoan cua chinh cong ty

   Ba trong sau cai do deu la "Phieu chi" gui toi mot "Supplier", nen mat
   phai tu loc. Do chinh la cho lung tung anh nhin thay.

   O `vgb_loai_ct` san co KHONG giai quyet duoc, vi o do chi doc so hieu
   tai khoan de goi ten chung tu cho dung luat ke toan: 111 thi goi Phieu
   thu hay Phieu chi, 112 thi goi Uy nhiem chi hay Giay bao Co. No noi
   tien di qua dau, khong noi viec do la viec gi.

   MOT CHO TINH, MOT CHO HIEN (QT-19)
   ----------------------------------
   Phan xep nghiep vu do MAY CHU tinh va ghi san vao o `vgb_nghiep_vu`
   moi lan luu phieu, ben nay chi to mau. Doc dau tep
   vagabond/nghiep_vu_tien.py de biet vi sao xep nhu the.

   O do con duoc bat `in_standard_filter`, nen ngoai chip mau con co san
   mot o loc ngay tren dau man: bam mot cai la ra rieng nhom phieu hoan
   ung, hoac rieng nhom tra truoc.

   MOT CAI BAY DA TRANH
   --------------------
   ERPNext co san listview_settings cho Payment Entry. Gan de len la xoa
   trang phan cua ho. Nen o day GOP chu khong gan de, giong het cach
   bom_list.js va minvoice_list.js dang lam. */

(function () {

	var MAU_NGHIEP_VU = {
		/* Xanh la cho tien VAO. Cam va tim cho tien RA co doi tac ro.
		   Xam cho chuyen noi bo vi no khong lam doi tong tien cua tiem.
		   Do danh rieng cho hai nhom "khac", vi do la phieu may CHUA XEP
		   DUOC, can nguoi ngo toi - chu khong phai phieu sai. */
		'Thu tiền khách': 'green',
		'Hoàn tiền khách': 'orange',
		'Trả nhà cung cấp': 'blue',
		'Trả trước nhà cung cấp': 'purple',
		'Hoàn ứng nhân viên': 'yellow',
		'Chuyển nội bộ': 'gray',
		'Thu khác': 'red',
		'Chi khác': 'red',
	};

	var dt = 'Payment Entry';
	var CU = frappe.listview_settings[dt] || {};
	var ind_cu = CU.get_indicator;

	/* Thieu hai co nay thi Frappe chan truoc, to nhap tra thang ve "Nhap"
	   va to da huy tra ve "Da huy", khong he goi ham duoi. Da dinh dung
	   the o ban v420 ben man hoa don mua, chi lo ra khi mo man that. */
	CU.has_indicator_for_draft = 1;
	CU.has_indicator_for_cancelled = 1;

	CU.add_fields = (CU.add_fields || []).concat([
		'docstatus', 'payment_type', 'party_type',
		'vgb_nghiep_vu', 'vgb_loai_ct', 'vgb_huy',
	]);

	CU.get_indicator = function (doc) {
		var ds = parseInt(doc.docstatus, 10) || 0;

		if (ds === 2 || parseInt(doc.vgb_huy, 10) === 1) {
			return ['Đã huỷ', 'gray', 'docstatus,=,2'];
		}

		var nv = String(doc.vgb_nghiep_vu || '').trim();

		/* Phieu lap truoc ban nay chua co o do. Dung bia ra mot nghiep vu:
		   noi that la chua xep, luu lai mot lan la co. Ban nay co kem mot
		   luot nap lai cho phieu cu nen so nay se rat it. */
		if (!nv) {
			return ['Chưa xếp nghiệp vụ', 'gray', 'vgb_nghiep_vu,=,'];
		}

		var mau = MAU_NGHIEP_VU[nv] || 'gray';
		var nhan = nv;

		/* Phieu con nhap thi noi ro ra, keo ke toan tuong da chi roi. Van
		   giu ten nghiep vu vi do moi la thu nguoi ta tim. */
		if (ds === 0) {
			nhan = nv + ' (nháp)';
			mau = 'gray';
		}

		return [nhan, mau, 'vgb_nghiep_vu,=,' + nv];
	};

	/* Phan cua ERPNext van duoc goi neu minh khong xu ly duoc. */
	CU._vgb_ind_cu = ind_cu;
	frappe.listview_settings[dt] = CU;
})();
