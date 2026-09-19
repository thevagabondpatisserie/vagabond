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

frappe.ui.form.on('Purchase Invoice', {
	refresh:async function(frm) {
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
	}
});
