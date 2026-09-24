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

async function vgbTaiKhoanDichVu(frm) {
	var lan = frm._vgb_lan_tai_khoan_dich_vu = (frm._vgb_lan_tai_khoan_dich_vu || 0) + 1;
	if (frm.doc.docstatus !== 0 || frm.doc.vgb_loai_chung_tu !== 'Mua dịch vụ' || !frm.doc.vgb_tk_chi_phi) return;
	var phieu = frm.doc, tk = phieu.vgb_tk_chi_phi;
	var ds = (frm.doc.items || []).map(function (d) { return {name:d.name, item_code:d.item_code}; });
	function conDung() {
		return frm.doc === phieu && frm._vgb_lan_tai_khoan_dich_vu === lan &&
			phieu.docstatus === 0 && phieu.vgb_tk_chi_phi === tk && phieu.vgb_loai_chung_tu === 'Mua dịch vụ';
	}
	var cacMa = Array.from(new Set(ds.map(function (d) { return d.item_code; }).filter(Boolean)));
	var loaiMon = new Map();
	/* frappe/client.py:get_list có kiểm quyền và mặc định chỉ20 bản ghi.
	   Tra mỗi mã một lần, chia100 mã/POST để929 dòng không thành929 request
	   hoặc URL quá dài. Thiếu quyền/metadata thì giữ dòng cho máy chủ kiểm. */
	for (var i = 0; i < cacMa.length; i += 100) {
		var lo = cacMa.slice(i, i + 100);
		var kq = await frappe.call({method:'frappe.client.get_list', type:'POST', args:{
			doctype:'Item', fields:['name', 'is_stock_item'], filters:{name:['in', lo]},
			limit_page_length:lo.length
		}});
		if (!conDung() || !kq || !Array.isArray(kq.message)) return;
		kq.message.forEach(function (m) {
			if (lo.indexOf(m.name) !== -1 && (m.is_stock_item === 0 || m.is_stock_item === '0')) loaiMon.set(m.name, 0);
		});
	}
	for (var d of ds) {
		if (!conDung()) return;
		var dong = (frm.doc.items || []).find(function (r) { return r.name === d.name && r.item_code === d.item_code; });
		if (!dong || dong.purchase_receipt || (d.item_code && !loaiMon.has(d.item_code))) continue;
		await frappe.model.set_value(dong.doctype, dong.name, 'expense_account', tk);
	}
	if (conDung()) frm.refresh_field('items');
}

frappe.ui.form.on('Purchase Invoice', {
	vgb_tk_chi_phi: vgbTaiKhoanDichVu,
	vgb_loai_chung_tu: vgbTaiKhoanDichVu,
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

// #332: chọn mã thay thế trên chính dòng nguồn, không xóa/thêm dòng và
// không để bảng giá của mã mới quyết định số tiền nhà cung cấp đã xuất.
async function vgbSuaMaTheoNguon(frm) {
	if (frm.is_dirty()) {
		frappe.msgprint('Lưu các thay đổi đang có rồi mở lại Sửa mã theo hóa đơn gốc.');
		return;
	}
	var kq = await frappe.call({method:'vagabond.sua_ma_hoa_don.lua_chon', args:{name:frm.doc.name}});
	var du = kq.message;
	if (!du.co_nguon) {frappe.msgprint('Hồ sơ không còn liên kết nguồn. Tải lại để kiểm tra.'); return;}
	var dong = du.dong.map(function(d) {return {label:frappe.utils.escape_html(d.nhan), value:d.name};});
	var nguon = du.nguon.map(function(d) {
		return {label:frappe.utils.escape_html((d.vi_tri+1)+'. '+d.ten+' | '+d.sl+' '+(d.dvt || '')+' x '+format_currency(d.gia, 'VND')), value:String(d.vi_tri)};
	});
	var hop = new frappe.ui.Dialog({title:'Sửa mã theo hóa đơn gốc', fields:[
		{fieldtype:'HTML', options:'Chọn đúng dòng nguồn và quy cách của mã mới. Số lượng, đơn giá lấy từ hóa đơn gốc. Lựa chọn mã và đơn vị sẽ được ghi nhớ cho lần đồng bộ sau.'},
		{fieldname:'dong', label:'Dòng trên hồ sơ đang sửa', fieldtype:'Autocomplete', options:dong, reqd:1},
		{fieldname:'vi_tri', label:'Dòng tương ứng trên hóa đơn gốc', fieldtype:'Autocomplete', options:nguon, reqd:1},
		{fieldname:'item_code', label:'Món thay thế', fieldtype:'Link', options:'Item', reqd:1,
			get_query:function(){return {filters:{disabled:0, is_purchase_item:1}};}},
		{fieldname:'uom', label:'Đơn vị đã đối chiếu', fieldtype:'Link', options:'UOM', reqd:1,
			description:'Chọn đúng quy cách đã khai trong Món. Ví dụ Chai 700 ml, không suy từ tên Chai.'}
	], primary_action_label:'Sửa dòng và ghi nhớ', primary_action:async function(v) {
		hop.disable_primary_action();
		try {
			/* F4: gửi kèm DẤU VÂN dòng nguồn đã thấy lúc chọn, máy chủ đối chiếu với vị trí. */
			var goc = du.nguon.find(function(d){return String(d.vi_tri) === String(v.vi_tri);});
			await frappe.call({method:'vagabond.sua_ma_hoa_don.sua', args:Object.assign({}, v,
				{name:frm.doc.name, modified:du.modified, dau_nguon:goc ? goc.dau : ''}), freeze:true});
			hop.hide();
			await frm.reload_doc();
			frappe.show_alert({message:'Đã sửa mã, quy cách và giữ giá theo hóa đơn gốc.', indicator:'green'});
		} finally {hop.enable_primary_action();}
	}});
	hop.show();
}

// #358 (anh Việt 22/09/2026): máy gợi ý, người chốt. Dòng trống mã (máy
// không đoán ra, hoặc đoán ra Món mà chưa biết quy đổi đơn vị) thì kế toán
// chọn Món ngay trên phiếu nháp; Món chưa khai đơn vị nhà cung cấp ghi thì
// gõ hệ số, máy ghi luôn vào bảng quy đổi của Món để lần sau tự hiểu.
async function vgbGanMonDesk(frm) {
	if (frm.is_dirty()) {
		frappe.msgprint('Lưu các thay đổi đang có rồi mở lại Gắn Món cho dòng trống mã.');
		return;
	}
	/* Dòng còn dấu "máy đoán" vẫn là dòng chờ chốt, dù người đã gõ mã thẳng
	   vào lưới: hệ số lúc đó còn là 1 (Codex #358). */
	var choChot = function (d) { return !(d.item_code || '').trim() || (d.vgb_mon_may_doan || '').trim(); };
	var trong = (frm.doc.items || []).filter(choChot);
	if (!trong.length) { frappe.msgprint('Phiếu này không còn dòng nào trống mã.'); return; }
	var nhan = function (d) {
		return d.idx + '. ' + (d.ten_hang_ncc || d.item_name || '') + ' | ' + d.qty + ' x ' + format_currency(d.rate, 'VND');
	};
	var hop = new frappe.ui.Dialog({title: 'Gắn Món cho dòng trống mã', fields: [
		{fieldtype: 'HTML', fieldname: 'gt', options: 'Máy gợi ý sẵn Món, bạn chọn lại nếu sai. Số lượng và đơn giá giữ đúng hoá đơn gốc. Lựa chọn được ghi nhớ cho lần sau.'},
		/* Codex #358 P2: tờ nhiều dòng trống mã thì phải tìm được theo tên
		   hoặc số dòng (AGENTS.md: chọn là tìm), như hộp Sửa mã theo hóa đơn gốc. */
		{fieldname: 'dong', label: 'Dòng trên phiếu', fieldtype: 'Autocomplete', reqd: 1,
			options: trong.map(function (d) { return {label: frappe.utils.escape_html(nhan(d)), value: String(d.idx)}; })},
		{fieldtype: 'HTML', fieldname: 'goi_y'},
		{fieldname: 'item_code', label: 'Món', fieldtype: 'Link', options: 'Item', reqd: 1,
			get_query: function () { return {filters: {disabled: 0, is_purchase_item: 1}}; }},
		/* Codex #358 vòng 19: tờ trả hàng không đi được cửa "Sửa mã theo hóa
		   đơn gốc", nên hoá đơn gốc không ghi đơn vị thì hỏi ngay tại đây. */
		/* Codex #358 vòng 20: CHỌN trong danh mục Đơn vị tính, không gõ tự do.
		   Gõ nhầm một chữ là danh mục dùng chung mang một đơn vị rác vĩnh viễn. */
		{fieldname: 'dvt_khai', label: 'Đơn vị nhà cung cấp ghi', fieldtype: 'Link', options: 'UOM', hidden: 1},
		{fieldname: 'he_so', label: 'Hệ số quy đổi', fieldtype: 'Float', hidden: 1}
	], primary_action_label: 'Gắn và ghi nhớ', primary_action: async function (v) {
		hop.disable_primary_action();
		try {
			var args = {name: frm.doc.name, dong: v.dong, item_code: v.item_code, nho: 1};
			if (hop._can_he_so) {
				if (!(parseFloat(v.he_so) > 0)) { frappe.msgprint('Gõ hệ số lớn hơn 0.'); return; }
				args.he_so = v.he_so;
				/* Codex #358: hệ số gửi kèm đúng Món máy chủ đã hỏi. Máy chủ
				   thấy lệch Món thì bỏ hệ số và hỏi lại, không ghi nhầm Món. */
				args.he_so_cho = hop._he_so_cho;
				if (hop._can_dvt) {
					if (!(v.dvt_khai || '').trim()) { frappe.msgprint('Gõ đơn vị nhà cung cấp ghi trên hoá đơn giấy.'); return; }
					args.dvt_khai = (v.dvt_khai || '').trim();
				}
			}
			var r = await frappe.call({method: 'vagabond.doi_chieu_mua.gan_ma_hang', args: args, freeze: true});
			var kq = r.message || {};
			if (kq.can_nguon) {
				/* #358 vòng 8: dòng hàng tồn kho mà hoá đơn gốc không ghi đơn vị.
				   Đường đi tiếp là nút "Sửa mã theo hóa đơn gốc" ngay trên phiếu. */
				frappe.msgprint({message: frappe.utils.escape_html(kq.loi_nhan) +
					'<br><br>Đóng hộp này rồi bấm <b>Sửa mã theo hóa đơn gốc</b> trên phiếu.',
					title: 'Cần chọn quy cách theo hoá đơn gốc', indicator: 'orange'});
				return;
			}
			if (kq.can_dvt) {
				/* Codex #358 vòng 19: hoá đơn gốc không ghi đơn vị mà tờ này
				   không đi được cửa nguồn. Hỏi luôn đơn vị và hệ số ở đây. */
				hop._can_he_so = 1;
				hop._can_dvt = 1;
				hop._he_so_cho = kq.item_code || v.item_code;
				var fd = hop.get_field('dvt_khai');
				fd.df.hidden = 0;
				fd.df.description = frappe.utils.escape_html(kq.loi_nhan || '');
				fd.refresh();
				var fh = hop.get_field('he_so');
				fh.df.hidden = 0;
				fh.df.label = '1 đơn vị đó bằng bao nhiêu ' + kq.dvt_kho + '?';
				fh.df.description = 'Số bạn gõ được ghi vào Món, lần sau máy tự hiểu.';
				fh.refresh();
				return;
			}
			if (kq.can_he_so) {
				hop._can_he_so = 1;
				hop._he_so_cho = kq.item_code || v.item_code;
				var f = hop.get_field('he_so');
				f.df.hidden = 0;
				f.df.label = '1 ' + kq.dvt_ncc + ' bằng bao nhiêu ' + kq.dvt_kho + '?';
				f.df.description = 'Món này chưa khai đơn vị "' + frappe.utils.escape_html(kq.dvt_ncc) + '". Số bạn gõ được ghi vào Món, lần sau máy tự hiểu.';
				f.refresh();
				if (kq.de_xuat && !hop.get_value('he_so')) hop.set_value('he_so', kq.de_xuat);
				return;
			}
			hop.hide();
			await frm.reload_doc();
			frappe.show_alert({message: kq.loi_nhan || 'Đã gắn Món.', indicator: 'green'});
		} finally { hop.enable_primary_action(); }
	}});
	/* Codex #358 P1: hệ số đang hỏi là của MỘT Món. Người đổi Món thì bỏ
	   hẳn câu hỏi cũ và số cũ, bấm Gắn lại để máy chủ hỏi cho Món mới. Giữ
	   lại thì "1 Lần = 1 Set" của Món cũ bị ghi vĩnh viễn vào Món mới. */
	function boHoiHeSo() {
		hop._can_he_so = 0;
		hop._can_dvt = 0;
		hop._he_so_cho = null;
		var f = hop.get_field('he_so'); f.df.hidden = 1; f.refresh();
		if (hop.get_value('he_so')) hop.set_value('he_so', null);
		var fd = hop.get_field('dvt_khai'); fd.df.hidden = 1; fd.refresh();
		if (hop.get_value('dvt_khai')) hop.set_value('dvt_khai', null);
	}
	async function napGoiY() {
		boHoiHeSo();
		var dong = hop.get_value('dong');
		/* Dòng đã mang Món kế toán tự gõ thì giữ nguyên lựa chọn đó, gợi ý
		   chỉ để tham khảo (Codex #358). */
		var d0 = (frm.doc.items || []).filter(function (d) { return String(d.idx) === String(dong); })[0];
		hop.set_value('item_code', (d0 && (d0.item_code || '').trim()) || '');
		if (!dong) return;
		try {
			var r = await frappe.call({method: 'vagabond.doi_chieu_mua.goi_y_mon', args: {name: frm.doc.name, dong: dong}});
			/* Codex #358 P1: người đã chọn dòng khác trong lúc chờ thì bỏ gợi ý
			   của dòng cũ, không thì Món của dòng này bị gắn sang dòng kia. */
			if (String(hop.get_value('dong')) !== String(dong)) return;
			var gy = (r.message && r.message.goi_y) || [];
			hop.get_field('goi_y').$wrapper.html(gy.length
				? '<div style="margin-bottom:8px;font-size:12px">Gợi ý: ' + gy.slice(0, 5).map(function (x) {
					return '<b>' + frappe.utils.escape_html(x.item_code) + '</b> ' + frappe.utils.escape_html(x.item_name) +
						' <span style="color:#6b7280">(' + frappe.utils.escape_html(x.vi_sao) + ')</span>';
				}).join('<br>') + '</div>'
				: '<div style="margin-bottom:8px;font-size:12px;color:#6b7280">Máy chưa có gợi ý, tìm Món trong ô dưới.</div>');
			/* Codex #358 P1 vòng 3: người đã tự chọn Món trong lúc chờ thì giữ
			   lựa chọn của người, gợi ý chỉ hiện ra để tham khảo. */
			if (gy.length && !hop.get_value('item_code')) hop.set_value('item_code', gy[0].item_code);
		} catch (e) { /* Gợi ý hỏng thì vẫn chọn tay được. */ }
	}
	hop.fields_dict.dong.df.onchange = napGoiY;
	hop.fields_dict.item_code.df.onchange = function () {
		if (hop._he_so_cho && hop.get_value('item_code') !== hop._he_so_cho) boHoiHeSo();
	};
	hop.show();
	hop.set_value('dong', String(trong[0].idx));
	napGoiY();
}

/* v526 (anh Viet chot 23/09/2026): noi HOA DON DEN SAU ngay tu to hoa don.

   Khoan chi tu TK cong ty danh dau "Hoa don den sau" da ghi chi phi luc
   chuyen tien. Hoa don ve tu m-invoice thanh mot to nhap o day; nut nay
   noi to do vao dung khoan cho cua cung nha cung cap. To da noi chi la
   chung tu: he chan ghi so (chi phi hai lan), nen bao ro tren dau to. */
var VGB_VAI_NOI_HD_SAU = ['System Manager', 'Accounts Manager', 'Accounts User', 'AP Kiểm soát (FIN)', 'AP Giám đốc'];

async function vgbHoaDonDenSau(frm) {
	if (frm.is_new() || frm.doc.docstatus !== 0) return;
	if (!VGB_VAI_NOI_HD_SAU.some(function (v) { return frappe.user.has_role(v); })) return;
	var phieu = frm.doc, kq;
	try {
		kq = (await frappe.call({ method: 'vagabond.ho_so_bo_sung.khoan_cho_hoa_don', args: { hoa_don: phieu.name } })).message || {};
	} catch (e) { return; }
	if (frm.doc !== phieu) return;
	if (kq.da_noi) {
		frm.dashboard.add_comment('Tờ này đã nối làm hoá đơn đến sau của hồ sơ ' +
			frappe.utils.escape_html(kq.da_noi) + '. Khoản chi đã ghi chi phí qua hồ sơ đó, nên tờ này chỉ là chứng từ, không ghi sổ.', 'blue', true);
		return;
	}
	var ds = kq.khoan || [];
	if (!ds.length) return;
	/* Codex #368 vong 3: may chu tra toi 50 khoan, nhieu khoan cung noi dung
	   va so tien. O chon phai TIM DUOC (go so ho so, noi dung, so tien), va
	   gia tri chon chinh la dinh danh "ho so · khoan N" chu khong phai so thu
	   tu trong danh sach, de khong the noi nham dong. Khong chon san khoan
	   nao: nguoi chon phai chu dong chon. */
	var theo_gia_tri = {};
	var lua_chon = ds.map(function (d) {
		var gt = d.ho_so + ' · khoản ' + d.dong + ' · ' + (d.noi_dung || '') + ' · ' + format_currency(d.so_tien) +
			(d.ngay ? ' · ' + d.ngay : '');
		theo_gia_tri[gt] = d;
		return gt;
	});
	frm.add_custom_button('Nối vào hồ sơ chi (hoá đơn đến sau)', function () {
		var hop = new frappe.ui.Dialog({
			title: 'Nối hoá đơn đến sau',
			fields: [
				{ fieldtype: 'HTML', fieldname: 'ghi_chu', options: '<p class="text-muted">Có ' + ds.length + ' khoản chi đang chờ hoá đơn của nhà cung cấp này. ' +
					'Gõ số hồ sơ, nội dung hoặc số tiền để tìm. Nối xong, tờ hoá đơn này chỉ là chứng từ và không ghi sổ nữa, vì chi phí đã ghi qua hồ sơ.</p>' },
				{ fieldtype: 'Autocomplete', fieldname: 'khoan', label: 'Khoản chi', reqd: 1, options: lua_chon }
			],
			primary_action_label: 'Nối',
			primary_action: async function (v) {
				var d = theo_gia_tri[v.khoan];
				if (!d) {
					frappe.msgprint('Chọn đúng một khoản trong danh sách gợi ý (gõ để tìm rồi bấm chọn).');
					return;
				}
				try {
					var r = (await frappe.call({ method: 'vagabond.ho_so_bo_sung.noi_hoa_don',
						args: { name: d.ho_so, dong: d.dong, hoa_don: phieu.name }, freeze: true })).message || {};
					hop.hide();
					frappe.show_alert({ message: 'Đã nối vào ' + d.ho_so + (r.hop_le ? '. Hồ sơ chuyển sang Hợp lệ tính thuế.' : '.'), indicator: 'green' }, 7);
					if ((r.lech || []).length) {
						frappe.msgprint({ title: 'Chưa chuyển Hợp lệ tính thuế', indicator: 'orange',
							message: 'Tiền lệch:<br>' + r.lech.map(function (x) { return frappe.utils.escape_html(x); }).join('<br>') });
					}
					frm.reload_doc();
				} catch (e) { /* frappe.call da bao loi cua may chu */ }
			}
		});
		hop.show();
	});
}

frappe.ui.form.on('Purchase Invoice', {
	refresh:async function(frm) {
		vgbHoaDonDenSau(frm);
		if (!frm.is_new() && !frm.doc.custom_minvoice_id && frm.doc.bill_no) {
			var phieu = frm.doc;
			try {
				var kq = await frappe.call({method:'vagabond.sua_ma_hoa_don.lien_quan', args:{name:phieu.name}});
				if (frm.doc === phieu && (kq.message || []).length) {
					frm.dashboard.add_comment('Chưa liên kết hóa đơn nguồn. Có hồ sơ cùng số/NCC/công ty: '+
						kq.message.map(function(d){return frappe.utils.get_form_link('Purchase Invoice', d.name, true, frappe.utils.escape_html(d.name));}).join(', ')+
						'. Mở kiểm tiền và trạng thái trước khi ghi sổ, tránh ghi hai lần.', 'orange', true);
				}
			} catch(e) { /* Cảnh báo lỗi không ngăn mở/sửa hồ sơ. */ }
		}
		if (!frm.is_new() && frm.doc.docstatus === 0 && frm.doc.custom_minvoice_id && !frm.doc.is_return &&
			['System Manager','Accounts Manager','Accounts User','Purchase Manager'].some(function(v){return frappe.user.has_role(v);})) {
			frm.add_custom_button('Sửa mã theo hóa đơn gốc', function(){return vgbSuaMaTheoNguon(frm);});
		}
		if (!frm.is_new() && frm.doc.docstatus === 0 && frm.doc.custom_minvoice_id &&
			(frm.doc.items || []).some(function (d) { return !(d.item_code || '').trim() || (d.vgb_mon_may_doan || '').trim(); }) &&
			['System Manager','Accounts Manager','Accounts User','Purchase Manager'].some(function(v){return frappe.user.has_role(v);})) {
			frm.add_custom_button('Gắn Món cho dòng trống mã', function(){return vgbGanMonDesk(frm);});
		}
	}
});
