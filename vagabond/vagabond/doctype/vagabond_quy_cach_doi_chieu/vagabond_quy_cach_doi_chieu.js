// Chỉ chọn hai chứng từ; mã dòng và hệ số do máy chủ xác định. Chặn
// phản hồi muộn để đổi phiếu nhanh không bị gán lại căn cứ vừa bỏ chọn.
frappe.ui.form.on('Vagabond Quy Cach Doi Chieu', {
  setup(frm) {
    frm.set_query('phieu_nhap', () => ({filters: {docstatus: 1, is_return: 0}}));
    frm.set_query('phieu_kiem_ke', () => ({filters: {docstatus: 1}}));
  },
  phieu_nhap: qcdcDienCanCu,
  phieu_kiem_ke: qcdcDienCanCu
});

async function qcdcDienCanCu(frm) {
  if (frm.doc.docstatus) return;
  const phieu_nhap = frm.doc.phieu_nhap;
  const phieu_kiem_ke = frm.doc.phieu_kiem_ke;
  await frm.set_value({dong_nhap: '', dong_kiem_ke: '', he_so_cu: 0, he_so_moi: 0});
  if (!phieu_nhap || !phieu_kiem_ke) return;
  const r = await frappe.call({method: 'vagabond.quy_cach_doi_chieu.goi_y_dong',
    args: {phieu_nhap, phieu_kiem_ke}, freeze: true,
    freeze_message: __('Đang xác định dòng điều chỉnh...')});
  if (frm.doc.docstatus || frm.doc.phieu_nhap !== phieu_nhap || frm.doc.phieu_kiem_ke !== phieu_kiem_ke) return;
  await frm.set_value(r.message);
}
