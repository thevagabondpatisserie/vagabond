/* ------------- Nut "Dong bo M-Invoice" tren man danh sach Desk

   Anh Viet xin 31/08/2026: *"Em thiet ke them nut nhan dong bo tren ban
   desktop o danh muc hoa don mua vao, hoa don ban ra de nhan thu cong
   duoc khong?"*

   BOI CANH, doc de dung go nut nay di
   -----------------------------------
   Ngay 26/08/2026 luc 16h28, buoc bien hoa don dien tu thanh chung tu bi
   tat. Buoc KEO hoa don ve van chay deu moi 15 phut, nen moi man hinh deu
   nhin nhu binh thuong. Nam ngay sau moi lo ra, va lo bang cach anh Viet
   ngoi so tay mot to cua Tac Khi Viet tren trang m-invoice voi man Hoa
   don mua hang. 69 to hoa don mua dung ngoai so suot thoi gian do.

   Nhip tu dong da duoc khai lai trong hooks.py, va co them chuong bao
   tac nhip. Nut nay la duong thu ba: khi ke toan nghi "hinh nhu thieu
   to nao do", ho bam mot cai va biet ngay trong ba muoi giay, thay vi
   phai nho toi nguoi viet ma.

   NUT TRA VE SO DEM CUA CA HAI BUOC, KHONG PHAI MOT
   -------------------------------------------------
   Trong dau moi nguoi "dong bo" la mot viec. That ra la hai: keo ve, roi
   dung chung tu. Chinh vi coi la mot ma vu 26/08 nam im duoc nam ngay -
   buoc mot van chay nen ai cung tuong ca day chuyen con song.

   Nen hop ket qua tach roi hai con so. Nhin mot cai la biet buoc nao dung.

   VI SAO GOP BA MAN VAO MOT TEP
   -----------------------------
   Hoa don mua vao, hoa don ban ra va bang hoa don dien tu deu hoi cung
   mot cau va bam cung mot cua. Chep ba ban la ba ban se lech nhau vao
   mot ngay khong ai doan truoc, dung cai bay quy tac 6 cua repo noi toi.

   MOT CAI BAY DA TRANH
   --------------------
   ERPNext co san listview_settings cho Purchase Invoice va Sales Invoice.
   Gan de len la xoa trang phan cua ho. Nen o day GOP chu khong gan de,
   giong het cach bom_list.js dang lam. */

(function () {
	var MAN = ['Purchase Invoice', 'Sales Invoice', 'MInvoice Invoice'];

	function so(n) {
		var x = Number(n || 0);
		return isNaN(x) ? '0' : x.toLocaleString('vi-VN');
	}

	function bangKetQua(kq) {
		var keo = (kq && kq.keo) || {};
		var dung = (kq && kq.dung) || {};
		var loi = (keo.loi_o_loai || []).join(', ');
		var h = '';

		h += '<p style="margin:0 0 10px">Đồng bộ chạy làm <b>hai bước</b>. ';
		h += 'Bước một kéo hoá đơn từ M-Invoice về, bước hai biến chúng thành ';
		h += 'chứng từ trong sổ. Xem cả hai để biết bước nào đứng.</p>';

		h += '<table class="table table-bordered" style="margin-bottom:12px">';
		h += '<tr><td colspan="2" style="background:#f4f5f6"><b>Bước 1 &mdash; Kéo về từ M-Invoice</b></td></tr>';
		h += '<tr><td>Tờ quét qua</td><td style="text-align:right">' + so(keo.da_quet) + '</td></tr>';
		h += '<tr><td>Tờ mới kéo về</td><td style="text-align:right"><b>' + so(keo.moi) + '</b></td></tr>';
		h += '<tr><td>Tờ vỏ ruột đã lành</td><td style="text-align:right">' + so(keo.chua_lanh) + '</td></tr>';
		if (loi) {
			h += '<tr><td colspan="2" style="color:#b71c1c">Đứt giữa chừng ở: ' + frappe.utils.escape_html(loi) + '</td></tr>';
		}
		h += '</table>';

		h += '<table class="table table-bordered" style="margin-bottom:12px">';
		h += '<tr><td colspan="2" style="background:#f4f5f6"><b>Bước 2 &mdash; Dựng chứng từ</b></td></tr>';
		h += '<tr><td>Tờ đầu vào xét tới</td><td style="text-align:right">' + so(dung.quet) + '</td></tr>';
		h += '<tr><td>Chứng từ dựng được</td><td style="text-align:right"><b>' + so(dung.da_dung) + '</b></td></tr>';
		h += '<tr><td>Bỏ qua hợp lệ</td><td style="text-align:right">' + so(dung.bo_qua_hop_le) + '</td></tr>';
		h += '<tr><td>Đầu ra đóng dấu (Fabi xuất)</td><td style="text-align:right">' + so(dung.dau_ra_dong_dau) + '</td></tr>';
		h += '<tr><td>Còn hỏng, cần soi</td><td style="text-align:right">' + so(dung.con_hong) + '</td></tr>';
		h += '</table>';

		var hong = dung.vi_du_hong || [];
		if (hong.length) {
			h += '<p style="margin:0 0 6px"><b>Vài tờ hỏng để soi:</b></p>';
			h += '<table class="table table-bordered">';
			h += '<tr><th>Loại</th><th>Số HĐ</th><th>Lý do</th></tr>';
			hong.forEach(function (r) {
				h += '<tr><td>' + frappe.utils.escape_html(String(r[0] || '')) + '</td>';
				h += '<td>' + frappe.utils.escape_html(String(r[1] || '')) + '</td>';
				h += '<td>' + frappe.utils.escape_html(String(r[2] || '')) + '</td></tr>';
			});
			h += '</table>';
		}

		h += '<p style="margin:10px 0 0;color:#6b7280">Chứng từ dựng ra nằm ở ';
		h += 'dạng <b>nháp</b>, kế toán soi rồi ghi sổ. Hệ không tự ghi sổ tờ nào.</p>';
		return h;
	}

	function bamDongBo() {
		var d = new frappe.ui.Dialog({
			title: 'Đồng bộ M-Invoice',
			fields: [
				{
					fieldtype: 'HTML',
					options:
						'<p>Kéo hoá đơn điện tử từ M-Invoice về rồi dựng chứng từ ' +
						'cho những tờ còn thiếu.</p>' +
						'<p style="color:#6b7280">Chạy lại nhiều lần không sinh ' +
						'trùng: tờ nào đã có chứng từ thì hệ bỏ qua.</p>',
				},
				{
					fieldname: 'so_ngay',
					fieldtype: 'Int',
					label: 'Lùi lại bao nhiêu ngày',
					default: 30,
					description:
						'Để trống thì lấy theo cài đặt (mặc định 7 ngày). ' +
						'Nghi sót lâu thì để 60 hoặc 90.',
				},
			],
			primary_action_label: 'Đồng bộ ngay',
			primary_action: function (v) {
				d.hide();
				frappe.dom.freeze('Đang đồng bộ với M-Invoice, chờ chút...');
				frappe.call({
					method: 'vagabond.minvoice_chung_tu.dong_bo_ngay',
					args: { so_ngay: v.so_ngay || 0 },
					callback: function (r) {
						frappe.dom.unfreeze();
						if (!r || !r.message) return;
						frappe.msgprint({
							title: 'Đồng bộ xong',
							indicator: (r.message.dung || {}).con_hong ? 'orange' : 'green',
							message: bangKetQua(r.message),
							wide: true,
						});
						if (cur_list) cur_list.refresh();
					},
					error: function () {
						frappe.dom.unfreeze();
					},
				});
			},
		});
		d.show();
	}

	/* ---------- Cot trang thai cua man Hoa don mua hang ----------

	   Anh Viet 04/09/2026: ghi so xong ra danh sach van chi thay "Qua han",
	   va "cai trang thai nay cung it xai nua".

	   Dem that hom do noi ro vi sao:

	     * 63 to da ghi so thi 62 to co han tra TRUNG ngay hach toan, vi
	       525 nha cung cap khong ai duoc khai dieu khoan thanh toan. To
	       vua ghi so xong la qua han ngay. Mot cot luc nao cung do thi
	       nguoi ta thoi nhin no.
	     * 3.170 to con nhap deu hien dung mot chu "Nhap", trong khi 2.487
	       to con thieu ma hang, 508 to cho noi phieu nhap, va chi 5 to la
	       sach. Ba viec cua ba nguoi doi chung mot cai nhan.

	   Nen cot nay khong doi ten "Qua han" thanh "Da ghi so" cho xong, ma
	   noi ra to dang o BUOC nao. Phan buoc do may chu tinh va ghi san vao
	   o `vgb_buoc` moi lan luu, ben nay chi to mau - MOT CHO TINH, MOT CHO
	   HIEN (QT-19), de man Desk va app khong bao gio noi khac nhau. */

	var MAU_BUOC = {
		'Thiếu mã hàng': 'red',
		'Lệch hoá đơn điện tử': 'red',
		'Chờ nối phiếu nhập': 'orange',
		'Chờ ghi sổ': 'blue',
	};

	/* ---------- TRANG THAI THANH TOAN, dung chung mua vao va ban ra

	   Anh Viet xin 05/09/2026: them chip "trang thai thanh toan" (da thanh
	   toan, con mot phan...) cho ca man hoa don mua lan man hoa don ban.

	   Truoc ban nay hai man do noi hai giong khac nhau. Man mua chi chia
	   duoc hai muc la da tra het hay con no. Man ban thi khong co gi ca,
	   dung nhan mac dinh cua ERPNext. Cung mot cau hoi "to nay tra toi
	   dau roi" ma hai man tra loi hai kieu.

	   VI SAO TACH RIENG "TRA MOT PHAN": gop no vao chung voi chua tra la
	   mat dung thong tin dang gia nhat. To chua tra dong nao va to da tra
	   tam phan muoi la hai tinh huong khac han nhau khi di doi no hay khi
	   xep lich chi. Nhap chung lai thi ke toan phai mo tung to ra xem,
	   tuc la cai chip khong tiet kiem duoc gi.

	   PHEP TINH NAY CHEP TU vagabond/trang_thai_tra.py, ban thuan o may
	   chu la ban goc va co bo kiem thu giu. Sua ben nao phai sua ben kia.
	   Chep sang day vi man danh sach khong goi duoc may chu cho tung dong,
	   goi tung dong la mot man 100 dong thanh 100 luot goi. */

	var LE = 1;

	function quaHan(ngayLap, hanTra, homNay) {
		/* Hai dieu kien, phai du ca hai. Mot: co han tra THAT, tuc han dat
		   SAU ngay hach toan. Han bang dung ngay lap nghia la chua ai khai
		   dieu khoan thanh toan cho doi tac do, goi la qua han la vu oan.
		   Hai: han do da troi qua. Thieu ngay nao thi khong ket luan. */
		var a = String(ngayLap || '').trim();
		var b = String(hanTra || '').trim();
		var n = String(homNay || '').trim();
		if (!a || !b || !n) return false;
		if (!(b > a)) return false;
		return b < n;
	}

	function trangThaiTra(tong, conLai, ghiSo, ngayLap, hanTra, homNay) {
		if (!ghiSo) return 'Chưa ghi sổ';
		var t = Number(tong || 0);
		var c = Number(conLai || 0);
		if (c < -LE) return 'Trả thừa';
		if (Math.abs(c) < LE) return 'Đã thanh toán';
		if (quaHan(ngayLap, hanTra, homNay)) return 'Quá hạn thanh toán';
		if (t > 0 && Math.abs(c - t) < LE) return 'Chưa thanh toán';
		if (t <= 0) return 'Chưa thanh toán';
		return 'Trả một phần';
	}

	var MAU_TRA = {
		'Chưa ghi sổ': 'gray',
		'Đã thanh toán': 'green',
		'Trả một phần': 'blue',
		'Chưa thanh toán': 'orange',
		'Quá hạn thanh toán': 'red',
		'Trả thừa': 'purple',
	};

	function phanTramDaTra(tong, conLai) {
		var t = Number(tong || 0);
		if (t <= 0) return 0;
		var da = t - Number(conLai || 0);
		if (da <= 0) return 0;
		if (da >= t) return 100;
		return Math.round((da * 100) / t);
	}

	function chipTra(doc) {
		/* Tra ve mang ba phan dung khuon get_indicator cua Frappe: nhan,
		   mau, va bo loc bam vao thi loc theo. */
		var tt = trangThaiTra(
			doc.grand_total, doc.outstanding_amount,
			parseInt(doc.docstatus, 10) === 1,
			doc.posting_date, doc.due_date,
			frappe.datetime.get_today()
		);
		var nhan = tt;
		if (tt === 'Trả một phần') {
			nhan = 'Trả một phần ' + phanTramDaTra(doc.grand_total, doc.outstanding_amount) + '%';
		}
		var loc = 'outstanding_amount,>,0';
		if (tt === 'Đã thanh toán') loc = 'outstanding_amount,=,0';
		else if (tt === 'Quá hạn thanh toán') loc = 'due_date,<,' + frappe.datetime.get_today();
		return [nhan, MAU_TRA[tt] || 'gray', loc];
	}

	function ganTrangThaiMuaHang() {
		var dt = 'Purchase Invoice';
		var CU = frappe.listview_settings[dt] || {};
		var ind_cu = CU.get_indicator;

		/* HAI CO NAY LA DIEU KIEN DE HAM DUOI DUOC GOI (04/09/2026).

		   Frappe chan truoc: voi doctype co ghi so, to o trang thai nhap
		   tra thang ve "Nhap" va to da huy tra ve "Da huy", KHONG he goi
		   `get_indicator` cua minh - tru khi bat dung hai co nay. Thieu
		   chung thi to da ghi so hien dung nhan moi, con 3.170 to nhap
		   van tro tro mot chu "Nhap", tuc la dung cai dong nguoi ta can
		   phan biet nhat. Da dinh dung the o ban v420, chi lo ra khi mo
		   danh sach that tren site. */
		CU.has_indicator_for_draft = 1;
		CU.has_indicator_for_cancelled = 1;

		CU.add_fields = (CU.add_fields || []).concat([
			'docstatus', 'status', 'outstanding_amount', 'grand_total',
			'posting_date', 'due_date', 'vgb_buoc', 'vgb_huy',
		]);

		CU.get_indicator = function (doc) {
			var ds = parseInt(doc.docstatus, 10) || 0;

			if (ds === 2 || parseInt(doc.vgb_huy, 10) === 1) {
				return ['Đã huỷ', 'gray', 'docstatus,=,2'];
			}

			if (ds === 0) {
				var b = String(doc.vgb_buoc || '').trim();
				/* To cu luu truoc ban nay chua co o `vgb_buoc`. Dung bia
				   ra mot buoc: noi that la chua tinh, luu lai mot lan la
				   co. */
				if (!b) return ['Nháp, chưa xét', 'gray', 'vgb_buoc,=,'];
				return [b, MAU_BUOC[b] || 'gray', 'vgb_buoc,=,' + b];
			}

			/* DA GHI SO thi chuyen sang noi chuyen TIEN. O `vgb_buoc`
			   khong duoc dung o day: to da ghi so thi khong luu lai nua
			   nen o do dung yen, ma cong no thi van chay.

			   Tu ban v425 phan nay dung chung phep tinh voi man hoa don
			   ban, nen hai man tra loi cung mot giong. Truoc do man nay
			   chi chia duoc hai muc la da tra het hay con no, gop mat
			   nhom tra mot phan vao chung voi nhom chua tra dong nao. */
			return chipTra(doc);
		};

		/* Phan cua ERPNext van duoc goi neu minh khong xu ly duoc. */
		CU._vgb_ind_cu = ind_cu;
		frappe.listview_settings[dt] = CU;
	}

	function gan(dt) {
		var CU = frappe.listview_settings[dt] || {};
		var onload_cu = CU.onload;
		CU.onload = function (lv) {
			/* GOI PHAN CUA ERPNext TRUOC. Ho co the dang them cot, them
			   bo loc, them nut cua rieng ho. */
			if (onload_cu) {
				try {
					onload_cu(lv);
				} catch (e) {
					/* Phan cua ho hong thi nut cua minh van phai moc len. */
				}
			}
			/* Chi ke toan va quan ly moi thay nut. Cua o may chu van chan
			   mot lan nua, day chi la cho do roi mat (QT-19: mot cho tinh,
			   mot cho kiem - o day may chu la cho kiem). */
			var vai = frappe.user_roles || [];
			var duoc =
				vai.indexOf('System Manager') >= 0 ||
				vai.indexOf('Accounts Manager') >= 0 ||
				vai.indexOf('Accounts User') >= 0;
			if (!duoc) return;
			lv.page.add_inner_button('Đồng bộ M-Invoice', bamDongBo);
		};
		frappe.listview_settings[dt] = CU;
	}

	function ganTrangThaiBanHang() {
		/* Man hoa don BAN ra. Truoc ban nay man nay khong co tuy bien nao
		   ca, dung nhan mac dinh cua ERPNext, nen nhin vao khong biet
		   khach da tra toi dau tru khi mo tung to.

		   Vi sao khong dung thang o `status` cua ERPNext: chu "Overdue"
		   cua ho doc thang han tra, ma phan lon doi tac chua duoc khai
		   dieu khoan thanh toan nen han tra bang luon ngay lap, khien to
		   vua ghi so xong da thanh qua han. Bai hoc nay da ghi o ban v420.

		   Man nay khong co o buoc xu ly nhu man mua, vi to ban ra khong
		   phai di qua day chuyen noi phieu nhap. To nhap o day chi la to
		   chua chot, noi dung mot chu la du. */
		var dt = 'Sales Invoice';
		var CU = frappe.listview_settings[dt] || {};
		var ind_cu = CU.get_indicator;

		/* Hai co nay la dieu kien de ham duoi duoc goi. Thieu chung thi
		   Frappe chan truoc, to nhap tra thang ve "Nhap" va to da huy tra
		   ve "Da huy". Da dinh dung the o ban v420 ben man mua. */
		CU.has_indicator_for_draft = 1;
		CU.has_indicator_for_cancelled = 1;

		CU.add_fields = (CU.add_fields || []).concat([
			'docstatus', 'status', 'outstanding_amount', 'grand_total',
			'posting_date', 'due_date', 'vgb_huy', 'is_return',
		]);

		CU.get_indicator = function (doc) {
			var ds = parseInt(doc.docstatus, 10) || 0;

			if (ds === 2 || parseInt(doc.vgb_huy, 10) === 1) {
				return ['Đã huỷ', 'gray', 'docstatus,=,2'];
			}
			if (ds === 0) {
				return ['Nháp, chưa chốt', 'gray', 'docstatus,=,0'];
			}
			/* To tra hang mang tong tien AM, nen phep tinh chung se doc ra
			   "tra thua". Noi thang no la to tra hang thi dung hon. */
			if (parseInt(doc.is_return, 10) === 1) {
				return ['Trả hàng', 'purple', 'is_return,=,1'];
			}
			return chipTra(doc);
		};

		CU._vgb_ind_cu = ind_cu;
		frappe.listview_settings[dt] = CU;
	}

	MAN.forEach(gan);
	ganTrangThaiMuaHang();
	ganTrangThaiBanHang();
})();
