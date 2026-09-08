/* #225: Cloud không có console Python. Xem đúng phương án năm dòng rồi
 * thực hiện qua POST, giữ hash để không áp lên chứng từ đã đổi. */
frappe.ui.form.on('Sales Invoice', {
  refresh(frm) {
    if (frm.doc.name !== 'HDB-26-09-00710' || frm.doc.docstatus !== 1 ||
        frm.doc.vgb_but_toan_tang !== 'PKT-2026-00012' ||
        !['Accounts Manager', 'System Manager'].some(r => frappe.user.has_role(r))) return;
    frm.add_custom_button(__('Sửa PKT hàng tặng'), async () => {
      const r = await frappe.call({method: 'vagabond.cong_cu_tang_cu.xem', freeze: true});
      const p = r.message;
      if (!p || !p.ma_xac_nhan) return;
      const esc = frappe.utils.escape_html;
      const tien = v => Number(v).toLocaleString('vi-VN', {maximumFractionDigits: 2});
      const dong = p.pkt_moi_chi_dung_chot.map(d => '<tr><td>' + esc(d.account_number) +
        '</td><td>' + tien(d.debit) + '</td><td>' + tien(d.credit) + '</td></tr>').join('');
      const html = '<p>Thay ' + esc(p.pkt_cu) + ' cho ' + esc(p.hoa_don) +
        '. Giữ nguyên hoá đơn điện tử ' + esc(String(p.so_hddt || '')) + '.</p>' +
        '<table class="table table-bordered"><thead><tr><th>Tài khoản</th><th>Nợ</th><th>Có</th></tr></thead><tbody>' +
        dong + '</tbody></table><p>Tổng Nợ = Có: 10.420.000,15 đ. Đây là một PKT gồm năm dòng chị Dung đã chốt.</p>';
      frappe.confirm(html, async () => {
        const tra = await frappe.call({method: 'vagabond.cong_cu_tang_cu.thay', type: 'POST',
          args: {ma_xac_nhan: p.ma_xac_nhan}, freeze: true, freeze_message: __('Đang thay PKT và kiểm công nợ...')});
        const kq = tra.message;
        if (!kq || kq.ok !== 1 || kq.hoa_don !== p.hoa_don || kq.pkt_cu !== p.pkt_cu ||
            !kq.pkt_moi || Number(kq.con_no) !== 0) {
          frappe.msgprint(__('Chưa xác minh được kết quả. Tải lại phiếu để đối chiếu PKT, không bấm thay lặp lại.'));
          return;
        }
        await frm.reload_doc();
        if (frm.doc.vgb_but_toan_tang !== kq.pkt_moi || Number(frm.doc.outstanding_amount) !== 0) {
          frappe.msgprint(__('Phiếu vừa tải chưa khớp kết quả. Kế toán đối chiếu liên kết PKT và công nợ.'));
          return;
        }
        frappe.show_alert({message: __('Đã thay PKT và tất toán công nợ. Mở liên kết PKT để kiểm lại.'), indicator: 'green'});
      });
    });
  }
});
