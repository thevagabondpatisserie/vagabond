/* ---------- 5. Home ---------- */
async function scrHome() {
  frame(APPNAME, '<div class="emp"><div class="e1">⏳</div></div>');
  await loadMasters();
  var apRoles = hasRole('AP Kiểm soát (FIN)') || hasRole('AP Giám đốc') || hasRole('AP Officer');
  var q = [
    getList('Material Request', { fields: ['name'], filters: { material_request_type: 'Purchase', docstatus: ['<', 2], status: ['in', ['Draft', 'Pending', 'Partially Ordered']] }, limit_page_length: 0 }),
    getList('Material Request', { fields: ['name'], filters: { material_request_type: 'Material Transfer', docstatus: ['<', 2], status: ['in', ['Draft', 'Pending', 'Partially Ordered']] }, limit_page_length: 0 }),
    getList('Material Request', { fields: ['name'], filters: { material_request_type: 'Manufacture', docstatus: ['<', 2], status: ['in', ['Draft', 'Pending', 'Partially Ordered']] }, limit_page_length: 0 })
  ];
  if (apRoles) q.push(getList('Payment Entry', { fields: ['name'], filters: { workflow_state: ['in', myPayStates()] }, limit_page_length: 0 }));
  var c = await Promise.all(q.map(function (p) { return (p && p.catch) ? p.catch(function () { return []; }) : p; }));
  var n = c.map(function (x) { return x.length; });

  function card(icon, t1, t2, cnt, fn, green) {
    return '<div class="hub" data-go="' + fn + '"><div class="hi">' + icon + '</div>' +
      '<div class="ht"><div class="h1">' + h(t1) + '</div><div class="h2">' + h(t2) + '</div></div>' +
      (cnt ? '<span class="bdg' + (green ? ' g' : '') + '">' + cnt + '</span>' : '') +
      '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
  }
  var html = '<div class="sec">Đặt hàng</div><div class="card">' +
    card(TYPES.Purchase.icon, TYPES.Purchase.title, TYPES.Purchase.sub, n[0], 'Purchase') +
    card(TYPES.Transfer.icon, TYPES.Transfer.title, TYPES.Transfer.sub, n[1], 'Transfer') +
    card(TYPES.Manufacture.icon, TYPES.Manufacture.title, TYPES.Manufacture.sub, n[2], 'Manufacture') +
    /* Đề nghị chi: MỌI nhân viên đều thấy, không khoá theo quyền mua hàng
       (anh Việt 19/08/2026). Bạn bếp mua chai nước mắm, bạn quầy mua bình
       gas thì đều lập được ngay trên điện thoại, Uyên nhận và chạy tiếp
       chuỗi duyệt. Trước đó phiếu này chỉ lập được trên Desk. */
    card('🧾', 'Tạo yêu cầu thanh toán nội bộ', 'Ứng tiền mua đồ cho tiệm, hoặc xin trả thẳng cho người bán', 0, 'DNC') +
    /* Uyen theo doi don mua hang va cong no nha cung cap ngay tren app,
       khoi mo Desk (anh Viet 12/08/2026). Hai o nay chi hien voi ke toan,
       thu mua va giam doc - gia mua la thong tin nhay cam. */
    (coQuyenMua()
      ? card('✅', 'Duyệt yêu cầu mua', 'Duyệt từng dòng, kèm tồn kho và số đang chờ về để quyết ngay', 0, 'DUYETYC') +
        card('🧾', 'Đơn mua hàng', 'Đơn đã gửi nhà cung cấp, hàng về tới đâu', 0, 'PO') +
        card('💸', 'Công nợ phải trả', 'Còn nợ nhà cung cấp nào, khoản nào quá hạn', 0, 'CNPT') +
        card('🏭', 'Danh mục nhà cung cấp', 'Hồ sơ nhà cung cấp và gán nhà cung cấp cho mặt hàng', 0, 'NCC') +
        card('💰', 'Bảng giá mua', 'Giá mua theo đơn vị mua, máy tự quy ra giá mỗi đơn vị kho', 0, 'BGIA') +
        /* Hai o thu cua khuon danh sach dung chung (A2 + B3). Dat canh o
           cu de anh Viet mo hai ben doi chieu tung con so. Go di khi da
           chac hai duong khop nhau. */
        card('🧪', 'Đơn mua hàng (bản khung)', 'Bản dựng từ khuôn dùng chung, để đối chiếu số với bản cũ', 0, 'KHPO') +
        card('🧪', 'Hoá đơn mua vào (bản khung)', 'Bản dựng từ khuôn dùng chung, để đối chiếu số với bản cũ', 0, 'KHHDM')
      : '') +
    '</div>';
  if (apRoles) {
    html += '<div class="sec">Duyệt chi</div><div class="card">' +
      card('✍️', 'Duyệt phiếu chi', myPayRoleLabel(), n[3], 'PAY', false) + '</div>';
  }
  if (isBep()) {
    var kcn = 0;
    try {
      var kdd = await getList('Material Request', { fields: ['name', 'trang_thai_bep'], filters: { material_request_type: 'Manufacture', docstatus: 1, schedule_date: ['<=', today()] }, limit_page_length: 0 });
      kcn = kdd.filter(function (x) { return x.trang_thai_bep !== 'Đã xong'; }).length;
    } catch (e) { }
    var wcn = 0;
    try {
      var wdd = await getList('Work Order', { fields: ['name', 'status'], filters: { docstatus: 1 }, limit_page_length: 0 });
      wcn = wdd.filter(function (x) { return WODONE.indexOf(x.status) < 0; }).length;
    } catch (e) { }
    html += '<div class="sec">Bếp</div><div class="card">' +
      card('🧑‍🍳', 'Bảng bếp hôm nay', 'Tổng số bánh cần làm, gộp theo món', kcn, 'KIT') +
      card('🏭', 'Lệnh sản xuất', 'Tạo lệnh, trừ nguyên liệu, in tem', wcn, 'MFG') + '</div>';
  }
  html += '<div class="sec">Bán hàng</div><div class="card">' +
    card('\uD83C\uDF82', 'Kiểm bánh hôm nay', 'Tồn - bếp làm - đã đặt - bán được, đồng bộ Pancake', 0, 'KBD') +
    /* Kiem banh theo MUA dat ngay duoi kiem banh theo ngay (anh Viet
       17/08/2026). Hai bang tra loi hai cau hoi khac han: bang ngay hoi
       "hom nay con bao nhieu", bang mua hoi "ca mua con bao nhieu". */
    card('🌕', 'Kiểm bánh theo mùa', 'Bánh trung thu, Tết... hàng sản xuất một lô có số lượng giới hạn', 0, 'KBM') + '</div>';
  /* Cho san de chen chip canh bao han muc mua vu. Ve SAU khi man da dung
     xong (mvChipCanhBao), y het cach the Bao cao tong hop dien doanh thu
     hom nay: hong thi trang chu van nguyen ven. */
  html += '<div id="mvCanhBao"></div>';
  if (isKho()) {
    var rcn = 0;
    try { rcn = (await getList('Purchase Receipt', { fields: ['name'], filters: { docstatus: 0 }, limit_page_length: 0 })).length; } catch (e) { }
    html += '<div class="sec">Kho</div><div class="card">' +
      card('\ud83d\udce5', 'Nhập kho', 'Quét mã phiếu, đếm hàng rồi nhập máy', rcn, 'RCV') + '</div>';
  }
  if (isRnd()) {
    var rdn = 0;
    try { rdn = (await getList('RnD Purchase Request', { fields: ['name'], filters: { trang_thai: ['in', ['Mới tạo', 'Đang xử lý']] }, limit_page_length: 0 })).length; } catch (e) { }
    html += '<div class="sec">Mua hàng test (R&amp;D)</div><div class="card">' +
      card('🧪', 'Yêu cầu mua hàng test', 'Hàng test không tạo mã, không nhập kho', rdn, 'RND') + '</div>';
  }
  var kkn = 0;
  try { kkn = (await getList('Phieu Kiem Ke', { fields: ['name'], filters: { trang_thai: 'Đang kiểm' }, limit_page_length: 0 })).length; } catch (e) { }
  html += '<div class="sec">Kiểm kê</div><div class="card">' +
    card('\ud83d\udccb', 'Kiểm kê kho', 'Quét mã, đếm hàng thực tế trong kho', kkn, 'KK') + '</div>';
  if (isSales()) {
    var dsn = 0, dtn = 0;
    try { dsn = (await getList('Sales Invoice', { fields: ['name'], filters: { posting_date: today(), docstatus: 0, custom_pancake_id: ['!=', ''] }, limit_page_length: 0 })).length; } catch (e) { }
    try {
      dtn = (await getList('Sales Invoice', {
        fields: ['name'],
        filters: { posting_date: ['<', today()], docstatus: 0, custom_pancake_id: ['!=', ''], vgb_huy: 0, vgb_tam_tinh: 0 },
        limit_page_length: 0
      })).length;
    } catch (e) { }
    html += '<div class="sec">Bán hàng</div><div class="card">' +
      /* Ba diem ban gio nam chung mot cua: bam vao la chon D1, NVHTN hay
         Sales Online (anh Viet 10/08/2026). Truoc day Sales dung rieng mot
         nut o ngoai nen nhan vien hay vao nham. */
      card('🧾', 'Tính tiền - hoá đơn bán hàng', 'Chọn điểm bán: District 1, NVHTN, Sales Online', dsn, 'POS') +
        card('🔐', 'Mã OTP quản lý', 'Cấp mã cho nhân viên sửa hoặc xoá hoá đơn', 0, 'OTP') +
      card('🎫', 'Chương trình khuyến mãi - combo', 'Bảy cách thức khuyến mãi, combo rã món, mã voucher, báo cáo tiền đã giảm', 0, 'KM') +
      card('📒', 'Công nợ phải thu', 'Khách sỉ gom hoá đơn trả sau: gom phiếu, sinh QR, đối soát', 0, 'CN') +
      card('👥', 'Danh sách khách hàng', 'Tra cứu khách sỉ và lẻ, hạng khách, mức chi tiêu', 0, 'KH') +
      /* Don treo phai co mot cua rieng, khong nap trong man Doanh thu Sales:
         don treo cua NGAY CU khong ai mo lai ngay do de xem (anh Viet
         13/08/2026). So dem lay theo 14 ngay gan day. */
      card('⏳', 'Đơn còn treo', 'Hoá đơn chưa ghi sổ được và lý do vì sao', dtn, 'DTREO') + '</div>';
  }
  /* Anh Viet 14/08/2026: doi ten nut 'Hop dong event, catering' thanh
     'Quan ly hop dong mua ban' va mo cho Loan Anh (Sales), thu mua va ke
     toan. Nen tach han ra mot muc rieng, khong con nam trong khoi Sales. */
  if (isSales() || hasRole('Purchase User') || hasRole('Purchase Manager') || hasRole('Accounts User') || hasRole('Accounts Manager')) {
    html += '<div class="sec">Hợp đồng - báo giá</div><div class="card">' +
      card('📑', 'Quản lý hợp đồng mua bán', 'Báo giá khách doanh nghiệp xuất PDF theo branding, hợp đồng event - catering - B2B sỉ', 0, 'HDG') + '</div>';
  }
  if (isSales() || hasRole('Shipper') || hasRole('Accounts User') || hasRole('Purchase User')) {
    html += '<div class="sec">Giao hàng</div><div class="card">'
      + card('🛵', 'Vận đơn', 'Shipper giao bánh, book xe, gộp chuyến, đối soát COD', 0, 'VD')
      /* Chi phi xe truoc day lap trong chan man Van don. Chi Dung theo doi
         chi phi xe hang thang nen dua han ra ngoai (anh Viet 13/08/2026). */
      + card('⛽', 'Chi phí xăng xe - sửa xe', 'Khai chi phí, duyệt, hoàn ứng và xuất Excel theo dõi', 0, 'CPX')
      + card('💵', 'Đối soát COD', 'Tiền shipper thu hộ và nộp về cuối ngày, theo từng người', 0, 'DSCOD')
      + card('⚠️', 'Cảnh báo thanh toán', 'Hoá đơn thiếu hoặc sai phương thức, vận đơn treo COD nhầm', 0, 'CBTT')
      + '</div>';
  }
  if (isSales() || hasRole('Accounts User') || hasRole('Accounts Manager')) {
    /* Badge do so phieu hoan tien dang CHO CHI (anh Viet 18/08/2026): "chi
       Dung Ke toan truong de nhan biet".

       Hong thi bang 0 chu khong chan trang chu: mot phep dem hong khong
       duoc lam ca man hinh trang. Cung mot nep voi bcSoHomNay. */
    var htChoChi = 0;
    try { htChoChi = (await api('vagabond.hoan_tien.dem_cho_chi', {})).cho_chi || 0; } catch (e) { }
    /* Phan he Bao cao (anh Viet 12/08/2026): so lieu thoi gian thuc, gop
       ca ba diem ban, xem theo ngay - tuan - thang - quy - nam va xuat
       Excel cho ke toan. Mot cua vao, 12 bao cao ben trong. */
    html += '<div class="sec">Báo cáo</div><div class="card">' +
      card('📈', 'Báo cáo tổng hợp', 'Đang cộng sổ doanh thu hôm nay...', 0, 'BCHUB') +
      card('🛵', 'Doanh thu theo nguồn đơn', 'Tại chỗ, Sales Online, GrabFood, ShopeeFood...', 0, 'BC:BC03') +
      card('💳', 'Phương thức thanh toán', 'Tiền mặt, chuyển khoản, thẻ, ví, công nợ', 0, 'BC:BC04') +
      card('🧾', 'Đối soát hoá đơn điện tử', 'Chờ ký, đã ký, CQT chấp nhận, chưa xuất', 0, 'BC:BC05') +
      card('🍰', 'Món bán chạy', 'Xếp hạng theo số lượng bán ra', 0, 'BC:BC08') +
      card('✂️', 'Sửa và huỷ hoá đơn', 'Ai sửa, ai huỷ, làm gì trên hoá đơn nào', 0, 'BC:BC07') + '</div>';
    html += '<div class="sec">Kế toán</div><div class="card">' +
      card('🧾', 'Hoá đơn bán ra', 'Lọc theo điểm bán và trạng thái hoá đơn điện tử', 0, 'HDBAN') +
      card('🛒', 'Hoá đơn mua vào', 'Lọc theo nhà cung cấp, hạn trả, còn nợ', 0, 'HDMUA') +
      card('🔗', 'Đối chiếu hoá đơn mua', 'Nối hoá đơn nhà cung cấp với phiếu nhập kho rồi ghi sổ một nút', 0, 'DCM') +
      card('📒', 'Công nợ phải thu', 'Khách nào còn nợ mình', 0, 'CN') +
      card('💸', 'Công nợ phải trả', 'Mình còn nợ nhà cung cấp nào', 0, 'CNPT') +
      /* Hoan tien doi han tu khoi Ban hang sang day (anh Viet 18/08/2026).
         Ly do dung: nguoi QUYET CHI la ke toan chu khong phai Sales. Sales
         chi lap phieu, va van lap duoc tu nut Hoan tien tren man Chi tiet
         don nhu cu - duong do khong doi.

         So badge lay tu MAY CHU (dem_cho_chi), khong dem o day: man hinh
         chi duoc hien so, khong duoc tu tinh so. */
      card('↩️', 'Danh sách Phiếu hoàn tiền (Cash-back)', 'Phiếu chờ chi, ảnh bằng chứng, tài khoản khách, đối soát lệnh chi', htChoChi, 'HT') +
      /* Ho so thanh toan (APP): thu mua lap, ke toan duyet, giam doc duyet,
         chuyen tien roi may do SePay xoa cong no, xong gui thu bao nha cung
         cap. Anh Viet 13/08/2026: lam tren app cho do roi so voi desktop. */
      card('📁', 'Tạo APP - Hồ sơ thanh toán', 'Lập đề nghị trả tiền, duyệt hai cấp, khớp SePay và báo nhà cung cấp', 0, 'APPTT') +
      card('🏛️', 'Đối soát hoá đơn điện tử', 'Chờ ký, đã ký, CQT chấp nhận, chưa xuất', 0, 'BC:BC05') +
      /* Hai man cho chi Dung, anh Viet dat 14/08/2026. Truoc do so co 174
         tai khoan tieng Viet ma chi hai but toan go tay, va khong mot tai
         san nao duoc khai. */
      card('🏗️', 'Tài sản và công cụ dụng cụ', 'Khai tài sản, chạy khấu hao và phân bổ 242 hàng tháng', 0, 'TS') +
      card('📒', 'Bút toán tay', 'Trích lương, bảo hiểm, phân bổ, kết chuyển thuế theo định khoản mẫu', 0, 'BT') + '</div>';
  }
  html += '<div class="sec">Cài đặt</div><div class="card">' +
    (coQuyenMua() || hasRole('Accounts Manager') || hasRole('System Manager')
      ? card('🏪', 'Điểm bán', 'Chi nhánh, mã quầy, nguồn đơn - khai một nơi dùng cho cả hệ', 0, 'CDDB') +
        card('🔒', 'Khoá sổ', 'Chốt số liệu kỳ cũ, không ai sửa hay huỷ được nữa', 0, 'CDKS') +
        card('💳', 'Phương thức thanh toán', 'Máy cà thẻ, ví, công nợ - và mã gửi cơ quan thuế', 0, 'CDPT') +
        card('🏦', 'Tài khoản nhận tiền', 'Số tài khoản sinh mã QR, khai riêng được cho từng nguồn đơn', 0, 'CDTK') +
        card('🎂', 'Danh mục sản phẩm', 'Mở mã hàng mới trong bảy ô, máy tự đặt mã và cảnh báo trùng tên', 0, 'CDSP') +
        card('🖨', 'Máy in', 'Sổ máy in từng điểm bán và khổ giấy cho mỗi loại phiếu', 0, 'CDMI') +
        card('🙅', 'Quyền tại quầy', 'Thu ngân được bỏ món tới đâu, khi nào phải xin quản lý', 0, 'CDQQ') +
        card('🎖️', 'Hạng thành viên', 'Ngưỡng lên hạng, giảm giá, tích điểm và xét lại hàng loạt', 0, 'CDHT') +
        card('🌙', 'Cuối ngày: ghi sổ và xuất hoá đơn', 'Bật tắt từng điểm bán, chọn giờ chạy', 0, 'CDCN') +
        card('🏦', 'SePay: nhận giao dịch ngân hàng', 'Đường dẫn webhook, bản đồ tài khoản, nạp bù sao kê cũ', 0, 'CDSE')
      : '') +
    /* Quan ly nguoi dung: anh Viet, chi Dung va De. Bay theo goi chuc vu chu
       khong bay ma tran 40 vai tro cua Frappe ra man hinh dien thoai. */
    (hasRole('System Manager') || hasRole('Quản lý người dùng')
      ? card('👥', 'Quản lý người dùng', 'Mời tài khoản mới, xếp gói chức vụ, bật tắt nhân viên nghỉ', 0, 'QLND') +
        card('🗝', 'Quản lý quyền', 'Mười một gói chức vụ, gói nào làm được gì và ai đang giữ', 0, 'QLQ')
      : '') +
    card('📦', 'Tra tồn kho', 'Xem tồn hiện tại theo kho', 0, 'STOCK') +
    card('👤', 'Tài khoản', 'Thông tin tài khoản và đăng xuất', 0, 'ACC') +
    '</div>' +
    '<div style="text-align:center;color:#a0a6b4;font-size:12px;padding:14px 10px 4px;line-height:1.6">' +
    h(S.me.full_name || S.user) + ' &middot; ' + h(shortDep(S.me.bo_phan) || 'Chưa gắn bộ phận') +
    '<br>' + h(S.user) +
    '<br>Bấm chia sẻ trên trình duyệt rồi chọn "Thêm vào MH chính" để dùng như app</div>';

  var b = frame(APPNAME, html);
  b.onclick = function (e) {
    var r = e.target.closest('[data-go]'); if (!r) return;
    /* Goi thang vgbGo - MOT cho dinh tuyen duy nhat.

       Truoc 16/08/2026 cho nay chep lai gan nguyen si than cua vgbGo. Hai
       ban song song thi lech nhau luc nao khong hay: den hom nay ban o day
       co 'HT' ma thieu 'XKH','XKD'; con vgbGo co 'XKH','XKD' ma thieu 'HT'.
       Anh Viet bam the Hoan tien tu man phan he Ban hang - duong di qua
       vgbGo - nen khong co phan ung gi. Nay xoa han ban chep, con mot cho.
    */
    return vgbGo(r.dataset.go);
  };
  vgbGomNhom();
  bcSoHomNay();
  mvChipCanhBao();
  vgbNapKhungCo();
}

/* Danh bạ các màn danh sách mà TÀI KHOẢN NÀY được xem, do máy chủ trả về.

   Vì sao hỏi máy chủ chứ không tự đoán theo vai ở màn: danh sách quyền chỉ
   được khai MỘT nơi, ở Python. Đoán lại ở đây là đẻ ra bản sao thứ hai, và
   hai bản sẽ lệch nhau vào một ngày không ai đoán trước.

   Chạy SAU khi trang chủ đã dựng xong, và hỏng thì im lặng bỏ qua: một lỗi
   đọc danh bạ không được làm vỡ trang chủ của cả quán. Lần đầu vào chưa có
   danh bạ thì nhóm Danh mục chưa hiện, xong lượt hỏi thì tự hiện ra. */
var VGB_KHUNG_CO = null;

async function vgbNapKhungCo() {
  if (VGB_KHUNG_CO) return;
  var ds;
  try { ds = await api('vagabond.khung.ds.danh_ba', {}); } catch (e) { return; }
  var m = {};
  (ds || []).forEach(function (x) { if (x && x.ma) m[x.ma] = x.ten || x.ma; });
  VGB_KHUNG_CO = m;
  /* Chỉ vẽ lại khi vẫn đang đứng ở trang chủ. Người ta bấm đi màn khác
     trong lúc chờ mà mình vẽ đè lên là cướp màn của họ. */
  if (S.stack[S.stack.length - 1] === scrHome) vgbGomNhom();
}

/* Chip do canh bao han muc mua vu (anh Viet chot 18/08/2026).

   Chay SAU khi ve xong trang chu, va hong thi im lang bo qua - mot loi doc
   bang mua vu khong duoc lam vo trang chu cua ca quan.

   Ban lo hien rieng va hien truoc: con so am nghia la da co don khong giao
   duoc, va do la viec phai goi khach ngay hom nay. */
async function mvChipCanhBao() {
  var o = document.getElementById('mvCanhBao');
  if (!o) return;
  var kq;
  try { kq = await api('vagabond.mua_vu.canh_bao', {}); } catch (e) { return; }
  if (!kq || !kq.so) return;
  var lo = (kq.ds || []).filter(function (x) { return x.ban_lo; });
  var it = (kq.ds || []).filter(function (x) { return !x.ban_lo; });
  var chip = function (x) {
    var mau = x.ban_lo ? '#b3261e' : '#b45309';
    var nen = x.ban_lo ? '#fef2f2' : '#fffbeb';
    return '<div style="display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid ' +
      (x.ban_lo ? '#fee2e2' : '#fef3c7') + '">' +
      '<div style="flex:1;min-width:0;font-size:12.5px;color:#374151">' + h(String(x.ten).slice(0, 40)) + '</div>' +
      '<b style="font-size:12.5px;color:' + mau + ';white-space:nowrap">' +
      (x.ban_lo ? 'BÁN LỐ ' + money(-x.con) : 'còn ' + money(x.con) + '/' + money(x.san_xuat)) + '</b></div>';
  };
  o.innerHTML = '<div class="sec">Cảnh báo hàng mùa vụ</div>' +
    '<div class="card" data-go="KBM" style="cursor:pointer;background:' +
    (lo.length ? '#fef2f2' : '#fffbeb') + ';border:1.5px solid ' + (lo.length ? '#fecaca' : '#fde68a') + '">' +
    (lo.length ? '<div style="padding:9px 12px;font-size:12px;font-weight:800;color:#b3261e">' +
      money(lo.length) + ' mã đã bán lố, phải gọi khách ngay</div>' : '') +
    lo.slice(0, 5).map(chip).join('') +
    (it.length ? '<div style="padding:9px 12px;font-size:12px;font-weight:700;color:#b45309">' +
      money(it.length) + ' mã còn dưới ' + money(kq.nguong) + '% hạn mức</div>' : '') +
    it.slice(0, 5).map(chip).join('') +
    '<div style="padding:8px 12px;font-size:11px;color:#98a2b3">Bấm để mở bảng Kiểm bánh theo mùa</div></div>';
}

/* Doanh thu hom nay hien thang tren the "Bao cao tong hop" o trang chu, de
   mo app phat la thay so - anh Viet 12/08/2026. Chay SAU khi ve xong man,
   hong thi de nguyen dong chu cu chu khong lam vo trang chu. */
async function bcSoHomNay() {
  var el = document.querySelector('[data-go="BCHUB"] .h2');
  var el2 = document.querySelector('[data-nhom="BC"] .gs');
  if (!el && !el2) return;
  try {
    var kq = await api('vagabond.bao_cao.danh_sach', { ky: 'ngay' });
    var chu = 'Hôm nay ' + money(kq.tong_doanh_thu) + ' đ · ' + money(kq.so_hoa_don) + ' hoá đơn';
    if (el) el.textContent = chu;
    if (el2) el2.textContent = money(kq.tong_doanh_thu) + ' đ hôm nay';
  } catch (e) {
    if (el) el.textContent = 'Doanh thu, nguồn đơn, thanh toán, hoá đơn điện tử';
  }
}

/* ---------- 5b. Nhom nghiep vu: o lon o trang chu, bam vao moi hien o nho ----------

Anh Viet dat ngay 03/08/2026: nghiep vu nhieu qua roi, trang chu cuon dai
khong nhin het. Gom thanh 8 o lon kieu iPOS, bam o lon moi ra danh sach o nho.

Cach lam co y: KHONG dung lai phan dem so cua scrHome. scrHome van dung so
lieu va van dung ham card() cu de dung tung dong; xong roi vgbGomNhom() moi
doc lai cac dong da dung duoc, xep vao nhom rong. Them nghiep vu moi chi can
them key vao VGB_NHOM, khong phai sua cho nao khac.
*/
/* ---------- Phân hệ DANH MỤC (anh Việt 18/08/2026) ----------

Anh nói: "để đảm bảo mọi phân hệ hoạt động trơn tru mà không bị rác dữ liệu,
anh muốn quy hoạch lại toàn bộ dữ liệu nền tảng".

Không màn hình nào ở đây được viết tay. Cả 16 danh mục đi qua tầng khung
danh sách: khai báo cột và bộ lọc bên Python, giao diện tự hiện, và bộ lọc
chạy ở MÁY CHỦ. Điều cuối là bắt buộc chứ không phải cho đẹp - doctype
Customer của tiệm đang có 43.220 dòng, kéo hết về điện thoại là treo máy.

Ô nào người dùng không đủ quyền thì máy chủ không trả về trong danh bạ, nên
ô đó không hiện. Chặn thật nằm ở vagabond/danh_muc_nen.py. */
var VGB_DM = [
  { m: 'DMSP', ic: '🎂', ten: 'Danh mục sản phẩm', mo: 'Toàn bộ mặt hàng, lọc theo nhóm và đơn vị tính' },
  { m: 'DMNSP', ic: '🗂️', ten: 'Nhóm sản phẩm', mo: 'Cây nhóm hàng của tiệm' },
  { m: 'DMDVT', ic: '📏', ten: 'Đơn vị tính', mo: 'Kg, gram, cái, hộp...' },
  { m: 'DMQD', ic: '🔄', ten: 'Quy đổi đơn vị tính', mo: 'Một kg bằng bao nhiêu gram' },
  { m: 'DMKHO', ic: '🏬', ten: 'Kho hàng', mo: 'Cây kho, kho cha và kho chứa hàng' },
  { m: 'DMBOM', ic: '🧪', ten: 'Công thức định mức', mo: 'Một món ăn hết bao nhiêu nguyên liệu' },
  { m: 'DMNCC', ic: '🏭', ten: 'Nhà cung cấp', mo: 'Hồ sơ nhà cung cấp' },
  { m: 'DMNNCC', ic: '📁', ten: 'Nhóm nhà cung cấp', mo: 'Cây nhóm nhà cung cấp' },
  { m: 'DMGIA', ic: '💰', ten: 'Bảng giá mua vào', mo: 'Giá mua theo món và nhà cung cấp' },
  { m: 'DMKH', ic: '👥', ten: 'Danh mục khách hàng', mo: 'Lọc khách sỉ B2B và khách lẻ B2C' },
  { m: 'DMNKH', ic: '📁', ten: 'Nhóm khách hàng', mo: 'Cây nhóm khách hàng' },
  { m: 'DMPT', ic: '💳', ten: 'Phương thức thanh toán', mo: 'Tiền mặt, chuyển khoản, thẻ, ví' },
  { m: 'DMNH', ic: '🏦', ten: 'Danh mục ngân hàng', mo: '581 ngân hàng NAPAS, dùng chung với tệp MB Biz' },
  { m: 'DMTK', ic: '🧮', ten: 'Tài khoản kế toán', mo: 'Lọc sẵn nhóm hay dùng: tiền, công nợ, doanh thu' },
  { m: 'DMTHUE', ic: '🧾', ten: 'Thuế bán ra', mo: 'Mẫu thuế áp cho hoá đơn bán' },
  { m: 'DMTHUEM', ic: '🧾', ten: 'Thuế mua vào', mo: 'Mẫu thuế áp cho hoá đơn mua' }
];

var VGB_NHOM = [
  /* Đặt hàng: ai cũng vào được, vì lập yêu cầu mua nguyên vật liệu là việc
     của mọi bộ phận. Các ô có giá mua và công nợ đã tách sang Thu mua. */
  { k: 'DH', ten: 'Đặt hàng', icon: '🛒', keys: ['Purchase', 'Transfer', 'RND', 'DNC'] },
  { k: 'SX', ten: 'Sản xuất', icon: '🧑‍🍳', keys: ['Manufacture', 'KIT', 'MFG', 'BTPO'] },
  { k: 'NK', ten: 'Nhập kho', icon: '📥', keys: ['RCV', 'NHANDC'] },
  { k: 'XK', ten: 'Xuất kho', icon: '📤', keys: ['XKH', 'XKD'] },
  { k: 'KK', ten: 'Kiểm kê', icon: '🧮', keys: ['KK', 'STOCK'] },
  { k: 'BH', ten: 'Bán hàng', icon: '🎂', keys: ['KBD', 'KBM', 'POS', 'HDG', 'OTP', 'KM', 'CN', 'KH', 'DTREO'] },
  { k: 'GH', ten: 'Giao hàng', icon: '🚚', keys: ['VD', 'CPX', 'DSCOD', 'CBTT'] },
  { k: 'BC', ten: 'Báo cáo', icon: '📈', keys: ['BCHUB', 'BC:BC03', 'BC:BC04', 'BC:BC05', 'BC:BC08', 'BC:BC07'] },
  /* Thu mua (anh Việt 18/08/2026): "các nút tính năng của luồng Mua hàng
     đang để chung chung khiến toàn bộ nhân viên đều nhìn thấy". Nhóm này
     nằm ngay trên Kế toán và chỉ hiện với Thu mua, Kế toán, Giám đốc.

     Không cần khoá riêng ở đây: các ô bên trong đều dựng có điều kiện
     coQuyenMua() trong scrHome, nên người không có quyền thì nhóm rỗng và
     vòng lặp dưới tự bỏ qua. Chặn thật nằm ở máy chủ, quyen_phan_he.py. */
  { k: 'TM', ten: 'Thu mua', icon: '🧾', keys: ['DUYETYC', 'PO', 'CNPT', 'NCC', 'BGIA', 'KHPO', 'KHHDM'] },
  { k: 'KT', ten: 'Kế toán', icon: '🧮', keys: ['HDBAN', 'HDMUA', 'DCM', 'CN', 'CNPT', 'HT', 'APPTT', 'PAY', 'TS', 'BT', 'BC:BC05'] },
  /* Danh mục nằm ngay trên Cài đặt (anh Việt chốt 18/08/2026). Khoá của
     các ô mang tiền tố DM: nên vgbGo bắt bằng MỘT nhánh tiền tố, không phải
     16 nhánh chép tay. */
  { k: 'DM', ten: 'Danh mục', icon: '📚', keys: VGB_DM.map(function (x) { return 'DM:' + x.m; }) },
  { k: 'KHAC', ten: 'Cài đặt', icon: '⚙️', keys: ['CDDB', 'CDKS', 'CDPT', 'CDTK', 'CDSP', 'CDMI', 'CDQQ', 'CDHT', 'CDCN', 'CDSE', 'QLND', 'QLQ', 'ACC', 'STOCK'] }
];

var VGB_HUB = {};

function vgbCss() {
  if (document.getElementById('vgbHubCss')) return;
  var st = document.createElement('style');
  st.id = 'vgbHubCss';
  st.textContent =
    '.gwrap{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:12px}' +
    '.gt{position:relative;background:#fff;border-radius:16px;padding:16px 14px 14px;' +
    'box-shadow:0 1px 3px rgba(16,24,40,.08);min-height:104px;display:flex;' +
    'flex-direction:column;justify-content:space-between;cursor:pointer;' +
    '-webkit-tap-highlight-color:transparent}' +
    '.gt:active{transform:scale(.98)}' +
    '.gt .gi{font-size:30px;line-height:1}' +
    '.gt .gn{font-size:17px;font-weight:700;color:#101828}' +
    '.gt .gs{font-size:12px;color:#98a2b3;margin-top:2px}' +
    '.gt .gb{position:absolute;top:12px;right:12px;background:#fee4e2;color:#d92d20;' +
    'font-size:13px;font-weight:700;border-radius:999px;padding:2px 9px}' +
    '.vxf{padding:12px}' +
    '.vxl{font-size:13px;color:#667085;margin:14px 2px 6px;font-weight:600}' +
    '.vxi,.vxs{width:100%;box-sizing:border-box;border:1px solid #d0d5dd;border-radius:10px;' +
    'padding:11px 12px;font-size:16px;background:#fff;color:#101828}' +
    '.vxb{width:100%;box-sizing:border-box;border:0;border-radius:12px;padding:14px;' +
    'font-size:16px;font-weight:700;background:#101828;color:#fff;margin-top:16px}' +
    '.vxb.o{background:#fff;color:#101828;border:1px solid #d0d5dd;margin-top:8px}' +
    '.vxb.r{background:#d92d20;color:#fff}' +
    '.vxb[disabled]{opacity:.45}' +
    '.vxr{display:flex;align-items:center;gap:10px;background:#fff;border-radius:12px;' +
    'padding:10px 12px;margin-bottom:8px;box-shadow:0 1px 2px rgba(16,24,40,.06)}' +
    '.vxr .t{flex:1;min-width:0}' +
    '.vxr .t b{display:block;font-size:15px;color:#101828;font-weight:600;' +
    'white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '.vxr .t i{font-style:normal;font-size:12px;color:#98a2b3}' +
    '.vxq{width:78px;text-align:right;border:1px solid #d0d5dd;border-radius:8px;' +
    'padding:8px;font-size:15px}' +
    '.vxx{border:0;background:transparent;color:#d92d20;font-size:20px;padding:0 4px}' +
    '.vxtag{display:inline-block;font-size:12px;font-weight:600;border-radius:999px;' +
    'padding:2px 9px}' +
    '.vxtag.c{background:#fef0c7;color:#b54708}' +
    '.vxtag.d{background:#d1fadf;color:#027a48}' +
    '.vxtag.x{background:#fee4e2;color:#912018}' +
    '.vxtag.c2{background:#eceff2;color:#5c6670}' +
    '.vtb{display:flex;gap:8px;padding:12px 12px 2px;overflow-x:auto}' +
    '.vt{flex:0 0 auto;padding:8px 14px;border-radius:20px;background:#fff;border:1px solid #dfe4ea;font-size:14px;font-weight:600;color:#5c6670;cursor:pointer;-webkit-tap-highlight-color:transparent}' +
    '.vt.on{background:#101828;color:#fff;border-color:#101828}' +
    '.vt b{font-weight:700;margin-left:4px}' +
    '.vxg{display:grid;grid-template-columns:1fr 1fr;gap:10px}' +
    '.vxgi{background:#fff;border-radius:12px;padding:10px;box-shadow:0 1px 2px rgba(16,24,40,.06);cursor:pointer}' +
    '.vxgi:active{transform:scale(.97)}' +
    '.vxga{width:100%;height:84px;object-fit:cover;border-radius:8px;display:block}' +
    '.vxga.t{display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:700;color:#475467}' +
    '.vxgn{font-size:13.5px;font-weight:600;color:#101828;margin-top:6px;line-height:1.3;max-height:36px;overflow:hidden}' +
    '.vxgm{font-size:11px;color:#98a2b3;margin-top:2px}' +
    '.vxgt{font-size:12px;font-weight:700;color:#027a48;margin-top:3px}' +
    '.vxgt.r{color:#d92d20}' +
    '.gt.vcl{grid-column:1/-1;min-height:0;flex-direction:row;align-items:center;justify-content:flex-start;gap:12px;padding-right:56px}' +
    '.gt.vcl .gi{font-size:26px}' +
    '.rcvths{display:flex;gap:10px;padding:0 12px 8px;flex-wrap:wrap}' +
    '.rcvth{width:110px;text-decoration:none;color:#475467;font-size:12px;text-align:center}' +
    '.rcvthi{width:110px;height:110px;object-fit:cover;border-radius:10px;border:1px solid #e4e7ec;display:block;background:#fff}' +
    '.rcvthf{width:110px;height:110px;display:flex;align-items:center;justify-content:center;font-size:40px;background:#fff;border:1px solid #e4e7ec;border-radius:10px}' +
    '.rcvth span{display:block;margin-top:4px}';
  document.head.appendChild(st);
}

function vgbSoNhom(nh) {
  var t = 0;
  for (var i = 0; i < nh.keys.length; i++) {
    var o = VGB_HUB[nh.keys[i]];
    if (o && o.cnt) t += o.cnt;
  }
  return t;
}

/* Bản chụp các dòng đọc được từ scrHome ở lượt gom ĐẦU TIÊN.

   Vì sao phải giữ: hàm này đọc các dòng [data-go] rồi GHI ĐÈ body bằng lưới
   ô lớn. Nên từ lượt gom thứ hai trở đi, [data-go] không còn dòng nào và
   lưới sẽ trống trơn. Bắt được lúc dựng phân hệ Danh mục 18/08/2026, khi
   danh bạ máy chủ về muộn và cần gom lại lượt hai. */
var VGB_DONG_GOC = null;

function vgbGomNhom() {
  vgbCss();
  VGB_HUB = {};
  var body = document.getElementById('vgbBody');
  if (!body) return;
  var rows = body.querySelectorAll('[data-go]');
  if (rows.length) {
    VGB_DONG_GOC = {};
    for (var i = 0; i < rows.length; i++) {
      var el = rows[i];
      var b = el.querySelector('.bdg');
      var n = b ? parseInt((b.textContent || '').replace(/\D/g, ''), 10) : 0;
      VGB_DONG_GOC[el.dataset.go] = { html: el.outerHTML, cnt: n || 0 };
    }
  } else if (!VGB_DONG_GOC) {
    /* Chưa gom lần nào mà cũng không đọc được dòng nào: không có gì để vẽ,
       và vẽ đè một lưới trống lên màn đang có là làm hỏng màn. */
    return;
  }
  for (var gk in VGB_DONG_GOC) VGB_HUB[gk] = VGB_DONG_GOC[gk];

  /* Hai o nho cua Xuat kho - dung o day de khong phai dong vao scrHome. */
  VGB_HUB.XKH = {
    cnt: 0,
    html: vgbODong('XKH', '🗑️', 'Xuất huỷ', 'Hàng hỏng, hết hạn, không đạt')
  };
  VGB_HUB.XKD = {
    cnt: 0,
    html: vgbODong('XKD', '🔁', 'Xuất điều chuyển nội bộ', 'Chuyển hàng sang kho khác')
  };
  /* Phân hệ Danh mục. VGB_KHUNG_CO là danh bạ máy chủ trả về, chỉ gồm các
     màn tài khoản này đủ quyền xem. Ô nào không có trong đó thì không dựng,
     nên người không đủ quyền không nhìn thấy ô. */
  for (var dmi = 0; dmi < VGB_DM.length; dmi++) {
    var dmx = VGB_DM[dmi];
    if (VGB_KHUNG_CO && !VGB_KHUNG_CO[dmx.m]) continue;
    VGB_HUB['DM:' + dmx.m] = {
      cnt: 0,
      html: vgbODong('DM:' + dmx.m, dmx.ic, dmx.ten, dmx.mo)
    };
  }

  /* Ô cho bộ phận Bếp (anh Việt 18/08/2026: "các bạn nhân sự Bếp đang bị
     nghẽn ở khâu nhận hàng"). Không khoá theo vai: ai có khai Kho phụ trách
     thì thấy hàng về kho mình, ai chưa khai thì màn tự nói phải làm gì. */
  VGB_HUB.NHANDC = {
    cnt: 0,
    html: vgbODong('NHANDC', '📦', 'Hàng chuyển về kho tôi', 'Kho khác vừa chuyển gì sang bộ phận mình')
  };

  var daXep = {};
  for (var a = 0; a < VGB_NHOM.length; a++) {
    for (var c = 0; c < VGB_NHOM[a].keys.length; c++) daXep[VGB_NHOM[a].keys[c]] = 1;
  }
  var khac = VGB_NHOM[VGB_NHOM.length - 1];
  for (var kk in VGB_HUB) {
    if (!daXep[kk] && khac.keys.indexOf(kk) < 0) khac.keys.push(kk);
  }

  var tongViec = 0;
  for (var vk in VGB_HUB) if (VGB_HUB[vk].cnt) tongViec += VGB_HUB[vk].cnt;
  var g = '<div class="gwrap">' +
    '<div class="gt vcl" data-nhom="VCL">' +
    '<div class="gi">📌</div>' +
    '<div><div class="gn">Việc cần làm</div>' +
    '<div class="gs">' + 'Danh sách phiếu đang chờ bạn xử lý' + '</div></div></div>';
  for (var j = 0; j < VGB_NHOM.length; j++) {
    var nh = VGB_NHOM[j];
    var co = 0;
    for (var m = 0; m < nh.keys.length; m++) if (VGB_HUB[nh.keys[m]]) co++;
    if (!co) continue;
    var so = vgbSoNhom(nh);
    g +=
      '<div class="gt" data-nhom="' + nh.k + '">' +
      (so ? '<span class="gb">' + so + '</span>' : '') +
      '<div class="gi">' + nh.icon + '</div>' +
      '<div><div class="gn">' + h(nh.ten) + '</div>' +
      '<div class="gs">' + co + ' nghiệp vụ</div></div></div>';
  }
  g += '</div>';
  body.innerHTML = g;
  body.onclick = function (e) {
    var t = e.target.closest('[data-nhom]');
    if (!t) return;
    var nh = null;
    for (var i = 0; i < VGB_NHOM.length; i++) if (VGB_NHOM[i].k === t.dataset.nhom) nh = VGB_NHOM[i];
    if (t.dataset.nhom === 'VCL') return go(scrVclList);
    if (nh) go(function () { scrNhom(nh); });
  };
}

async function scrVclList() {
  vgbCss();
  frame('Việc cần làm', '<div class="emp"><div class="e1">⏳</div><div class="e2">Đang gom việc của bạn...</div></div>');
  var td = today();
  var giu = khoGiuCuaToi();
  var khoNhan = giu.length ? giu : S.wh;
  var TT = typeOf('Material Transfer');
  var TM = typeOf('Manufacture');
  var R = [], daCo = {};
  function them(o) { R.push(o); }
  function tre(n) { return !!(n && String(n) < td); }
  async function lay(fn) { try { await fn(); } catch (e) { } }

  await lay(async function () {
    var ds = await getList('Purchase Receipt', { fields: ['name', 'supplier_name', 'posting_date'], filters: { docstatus: 0 }, limit_page_length: 60, order_by: 'posting_date asc' });
    (ds || []).forEach(function (x) {
      them({ nhom: 'Phiếu nhập kho chờ đếm hàng', icon: '📥', t: x.name, s: (x.supplier_name || '') + ' · ' + dmy(x.posting_date), chip: 'chờ nhận', mau: '#1a73c7', mo: function () { go(function () { scrRecvDoc(x.name); }); } });
    });
  });

  await lay(async function () {
    var f = { material_request_type: 'Material Transfer', docstatus: 1, status: ['in', ['Pending', 'Partially Ordered']] };
    if (giu.length) f.set_from_warehouse = ['in', giu];
    var ds = await getList('Material Request', { fields: ['name', 'set_from_warehouse', 'set_warehouse', 'schedule_date'], filters: f, limit_page_length: 60, order_by: 'schedule_date asc' });
    (ds || []).forEach(function (x) {
      daCo[x.name] = 1;
      them({ nhom: 'Kho bạn giữ phải soạn hàng', icon: '🧺', t: x.name, s: shortWh(x.set_from_warehouse) + ' → ' + shortWh(x.set_warehouse) + ' · cần ' + dmy(x.schedule_date), chip: tre(x.schedule_date) ? 'trễ hẹn' : 'chờ soạn', mau: tre(x.schedule_date) ? '#c0392b' : '#c77700', mo: function () { go(function () { scrMRView(x.name, TT); }); } });
    });
  });

  await lay(async function () {
    var f = { material_request_type: 'Material Transfer', docstatus: 1, status: ['in', ['Pending', 'Partially Ordered']] };
    if (khoNhan && khoNhan.length) f.set_warehouse = ['in', khoNhan];
    var ds = await getList('Material Request', { fields: ['name', 'set_from_warehouse', 'set_warehouse', 'schedule_date', 'per_ordered'], filters: f, limit_page_length: 60, order_by: 'schedule_date asc' });
    (ds || []).forEach(function (x) {
      if (daCo[x.name]) return;
      if (!((x.per_ordered || 0) > 0)) return;
      daCo[x.name] = 1;
      them({ nhom: 'Hàng đã chuyển, chờ bạn xác nhận nhận', icon: '📦', t: x.name, s: shortWh(x.set_from_warehouse) + ' → ' + shortWh(x.set_warehouse) + ' · cần ' + dmy(x.schedule_date), chip: 'chờ nhận', mau: '#0a8f9e', mo: function () { go(function () { scrMRView(x.name, TT); }); } });
    });
  });

  var bep = shortDep(S.me.bo_phan || '');
  if (bep && bep.indexOf('Bếp') === 0) {
    await lay(async function () {
      var ds = await getList('Material Request', { fields: ['name', 'set_warehouse', 'schedule_date', 'bo_phan_yeu_cau'], filters: { material_request_type: 'Manufacture', docstatus: 1, status: ['in', ['Pending', 'Partially Ordered']], custom_bep_nhan: bep }, limit_page_length: 60, order_by: 'schedule_date asc' });
      (ds || []).forEach(function (x) {
        them({ nhom: 'Bếp bạn phải làm', icon: '🎂', t: x.name, s: (x.bo_phan_yeu_cau || '') + ' · cần ' + dmy(x.schedule_date), chip: tre(x.schedule_date) ? 'trễ hẹn' : 'chờ làm', mau: tre(x.schedule_date) ? '#c0392b' : '#7a4bbf', mo: function () { go(function () { scrMRView(x.name, TM); }); } });
      });
    });
  }

  await lay(async function () {
    var ds = await getList('Stock Entry', { fields: ['name', 'purpose', 'from_warehouse', 'to_warehouse', 'posting_date', 'owner'], filters: { docstatus: 0, purpose: ['in', ['Material Transfer', 'Material Issue']] }, limit_page_length: 60, order_by: 'creation desc' });
    (ds || []).forEach(function (x) {
      var cuaToi = (x.owner === S.user) || (giu.length && giu.indexOf(x.from_warehouse) >= 0);
      if (!cuaToi) return;
      them({ nhom: 'Phiếu xuất nháp chờ ghi sổ', icon: '📤', t: x.name, s: shortWh(x.from_warehouse) + (x.to_warehouse ? ' → ' + shortWh(x.to_warehouse) : '') + ' · ' + dmy(x.posting_date), chip: 'bản nháp', mau: '#8a8f98', mo: function () { go(function () { scrXkView(x.name); }); } });
    });
  });

  if (kkCanPost()) {
    await lay(async function () {
      var ds = await getList('Phieu Kiem Ke', { fields: ['name', 'kho', 'ngay_kiem'], filters: { trang_thai: 'Chờ duyệt' }, limit_page_length: 40, order_by: 'ngay_kiem asc' });
      (ds || []).forEach(function (x) {
        them({ nhom: 'Phiếu kiểm kê chờ bạn chốt sổ', icon: '🧮', t: x.name, s: shortWh(x.kho) + ' · kiểm ' + dmy(x.ngay_kiem), chip: 'chờ chốt', mau: '#c77700', mo: function () { go(scrKkList); } });
      });
    });
  }

  if (hasRole('Purchase User') || hasRole('Stock Manager') || hasRole('System Manager')) {
    await lay(async function () {
      var ds = await getList('Purchase Order', { fields: ['name', 'supplier_name', 'schedule_date', 'trang_thai_pnk'], filters: { docstatus: 1, status: ['not in', ['Closed', 'Completed']], schedule_date: ['<', td] }, limit_page_length: 30, order_by: 'schedule_date asc' });
      (ds || []).forEach(function (x) {
        if ((x.trang_thai_pnk || '') === 'Đã nhập đủ') return;
        them({ nhom: 'Cảnh báo: đơn mua quá hẹn chưa nhập đủ', icon: '⚠️', t: x.name, s: (x.supplier_name || '') + ' · hẹn ' + dmy(x.schedule_date) + ' · ' + (x.trang_thai_pnk || 'Chưa tạo phiếu'), chip: 'quá hẹn', mau: '#c0392b', mo: function () { toast('Đơn ' + x.name + ' cần xử lý trên máy tính.', 4200); } });
      });
    });
  }

  var nhoms = [];
  R.forEach(function (x) { if (nhoms.indexOf(x.nhom) < 0) nhoms.push(x.nhom); });
  var body = '';
  if (!R.length) {
    body = '<div class="emp"><div class="e1">🎉</div><div class="e2">Không có việc nào đang chờ bạn</div></div>';
  } else {
    body = '<div style="padding:14px 14px 0;font-size:13px;color:#8a90a0">Đang chờ bạn xử lý <b>' + R.length + '</b> việc</div>';
    nhoms.forEach(function (n) {
      body += '<div class="sec">' + h(n) + '</div>';
      R.forEach(function (x, i) {
        if (x.nhom !== n) return;
        body += '<div data-v="' + i + '" style="background:#fff;border-radius:16px;margin:8px 12px;padding:13px 15px;display:flex;align-items:center;gap:12px;box-shadow:0 1px 3px rgba(16,24,40,.07)">' +
          '<div style="font-size:22px">' + x.icon + '</div>' +
          '<div style="flex:1;min-width:0"><div style="font-weight:700;font-size:15px">' + h(x.t) + '</div>' +
          '<div style="font-size:12.5px;color:#8a90a0;margin-top:2px">' + h(x.s) + '</div></div>' +
          '<span style="padding:3px 10px;border-radius:11px;font-size:11.5px;font-weight:700;color:#fff;white-space:nowrap;background:' + x.mau + '">' + h(x.chip) + '</span></div>';
      });
    });
  }
  var b = frame('Việc cần làm', body);
  b.onclick = function (e) {
    var el = e.target.closest('[data-v]');
    if (!el) return;
    var x = R[+el.dataset.v];
    if (x && x.mo) x.mo();
  };
}
function vgbODong(k, icon, t1, t2) {
  return '<div class="hub" data-go="' + k + '"><div class="hi">' + icon + '</div>' +
    '<div class="ht"><div class="h1">' + h(t1) + '</div><div class="h2">' + h(t2) + '</div></div>' +
    '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
}

function scrNhom(nh) {
  vgbCss();
  var rows = '';
  for (var i = 0; i < nh.keys.length; i++) {
    var o = VGB_HUB[nh.keys[i]];
    if (o) rows += o.html;
  }
  var body = frame(nh.ten, '<div class="card">' + rows + '</div>');
  root.onclick = null;
  body.onclick = function (e) {
    var r = e.target.closest('[data-go]');
    if (r) vgbGo(r.dataset.go);
  };
}

/* Mot cho duy nhat dinh tuyen tu o nho sang man hinh. */
function vgbGo(k) {
  if (k === 'KBD') { location.href = '/kiem-banh'; return; }
  if (k === 'KBM') return go(scrMuaVuDs);
  if (k === 'BTPO') { location.href = '/btp'; return; }
  if (k === 'PAY') return go(scrPayList);
  if (k === 'BGIA') return go(scrBangGia);
  if (k === 'NCC') return go(scrNcc);
  if (k === 'STOCK') return go(scrStock);
  if (k === 'KIT') return go(scrKitchen);
  if (k === 'MFG') return go(scrMfgList);
  if (k === 'RCV') return go(scrRecvList);
  if (k === 'KK') return go(scrKkList);
  if (k === 'DS') return go(scrDoanhSo);
  if (k === 'DTREO') return go(scrDonTreo);
  if (k === 'POS') return go(scrPosChonQuay);
  if (k === 'HDG') return go(scrHopDongHub);
  if (k === 'BC3') return go(function () { kmThe = 'bc'; scrKhuyenMai(); });
  if (k === 'KT1') return go(scrDoanhSo);
  if (k === 'BCHUB') return go(scrBaoCao);
  if (k === 'DUYETYC') return go(scrDuyetYc);
  if (k === 'PO') return go(scrDonMua);
  if (k === 'KHPO') return kgMo('PO');
  if (k === 'KHHDM') return kgMo('HDM');
  if (k === 'CNPT') return go(scrNoPhaiTra);
  if (k === 'HDBAN') return go(scrHdBan);
  if (k === 'APPTT') return go(scrHoSoTT);
  if (k === 'HDMUA') return go(scrHdMua);
  if (k === 'DCM') return go(scrDoiChieuMua);
  if (k && k.indexOf('BC:') === 0) { bcMa = k.slice(3); return go(scrBaoCaoXem); }
  if (k && k.indexOf('BC') === 0) return toast('Báo cáo này chưa dựng. Anh Việt chốt nội dung rồi em điền vào.', 4200);
  if (k && k.indexOf('KT') === 0) return toast('Mục kế toán này chưa dựng. Anh Việt chốt nội dung rồi em điền vào.', 4200);
  if (k === 'OTP') return go(scrOtp);
  if (k === 'KM') return go(scrKhuyenMai);
  if (k === 'CN') return go(scrCongNo);
  if (k === 'HT') return go(scrHoanTien);
  if (k === 'KH') return go(scrKhachHang);
  if (k === 'VD') return go(scrVanDon);
  if (k === 'CPX') return go(scrVdChiPhi);
  if (k === 'DSCOD') return go(scrVdCod);
  if (k === 'CBTT') return go(scrCanhBaoTT);
  if (k === 'RND') return go(scrRndList);
  if (k === 'NHANDC') return go(scrHangVeKho);
  /* Một nhánh tiền tố cho cả 16 danh mục. Chép 16 nhánh tay là 16 cơ hội
     gõ nhầm một mã, và đó đúng là lỗi dead link ngày 16/08. */
  if (k.indexOf('DM:') === 0) return kgMo(k.slice(3));
  if (k === 'DNC') return go(scrDeNghiChi);
  if (k === 'CDDB') return go(scrDiemBan);
  if (k === 'CDKS') return go(scrKhoaSo);
  if (k === 'CDPT') return go(scrPtThanhToan);
  if (k === 'CDTK') return go(scrTaiKhoan);
  if (k === 'CDSP') return go(scrDanhMuc);
  if (k === 'CDMI') return go(scrMayIn);
  if (k === 'CDQQ') return go(scrQuyenQuay);
  if (k === 'CDHT') return go(scrHangKhach);
  if (k === 'CDCN') return go(scrCaiDatCuoiNgay);
  if (k === 'CDSE') return go(scrSePay);
  if (k === 'TS') return go(scrTaiSan);
  if (k === 'BT') return go(scrButToan);
  if (k === 'QLND') return go(scrNguoiDung);
  if (k === 'QLQ') return go(scrQuyen);
  if (k === 'ACC') return go(scrAccount);
  if (k === 'XKH') return go(scrXkHuyList);
  if (k === 'XKD') return go(scrXkCkList);
  go(function () { scrMRList(TYPES[k]); });
}

