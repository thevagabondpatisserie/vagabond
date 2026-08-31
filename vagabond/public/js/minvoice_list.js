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

	MAN.forEach(gan);
})();
