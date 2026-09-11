// #262: duyệt một lần căn cứ, sau đó máy tự bù khi hoá đơn được ghi sổ.
frappe.ui.form.on('Vagabond Can Tru San', {
  async refresh(frm) {
    const kq = await frappe.call('vagabond.can_tru_san.diem_ban');
    frm.set_df_property('diem_ban', 'options', [''].concat((kq.message || []).map(d => d.ma)).join('\n'));
    frm.set_query('hoa_don', 'phi', () => ({filters: {company: frm.doc.company, supplier: frm.doc.nha_cung_cap, docstatus: ['<', 2]}}));
    frm.set_query('hoa_don', 'ban', () => ({filters: {company: frm.doc.company, customer: frm.doc.khach_hang, custom_nguon: frm.doc.san, vgb_quay: frm.doc.diem_ban === 'SALES' ? ['in', ['', 'SALES']] : frm.doc.diem_ban, docstatus: ['<', 2]}}));
    if (frm.doc.docstatus === 1 && !frm.doc.but_toan) {
      frm.add_custom_button('Kiểm lại đối soát', async () => {
        await frappe.call({method: 'vagabond.can_tru_san.thu_lai', args: {ten: frm.doc.name}, freeze: true});
        await frm.reload_doc();
      });
    }
    if (!frm.is_new()) frm.add_custom_button('Xem công nợ sàn', async () => {
      const r = (await frappe.call('vagabond.can_tru_san.doi_chieu', {ten: frm.doc.name})).message;
      const esc = frappe.utils.escape_html;
      const tien = n => Number(n || 0).toLocaleString('vi-VN') + ' đ';
      frappe.msgprint({title: r.trang_thai, message: '<table class="table">' + [
        ['Đầu kỳ', r.dau_ky], ['Doanh thu ghi công nợ', r.doanh_thu], ['Tiền đã nhận và phân bổ', r.da_nhan],
        ['Phí đã cấn trừ', r.phi_da_bu], ['Điều chỉnh khác', r.dieu_chinh], ['Cuối kỳ', r.du_cuoi],
        ['Trong dư cuối kỳ: hóa đơn đã hủy mềm', r.du_huy_mem]
      ].map(x => '<tr><td>' + esc(x[0]) + '</td><td>' + tien(x[1]) + '</td></tr>').join('') + '</table><p>' + esc(r.ghi_chu) + '</p>'});
    });
  }
});
