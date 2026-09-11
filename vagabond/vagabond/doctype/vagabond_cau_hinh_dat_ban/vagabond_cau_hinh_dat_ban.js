// Danh mục lấy từ cùng cấu hình điểm bán của app.
frappe.ui.form.on('Vagabond Cau Hinh Dat Ban', {onload(frm) {
  frappe.call('vagabond.diem_ban.danh_sach').then(r => {
    const ds = r.message || []; const cacDiem = Array.isArray(ds) ? ds : (ds.diem || []);
    frm.set_df_property('co_so','options',cacDiem.filter(d => d.bat && d.quay).map(d => ({value:d.ma,label:d.ten})));
  });
}});
