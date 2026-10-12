/* ---------- 5. Home ---------- */
async function scrHome() {
  frame(APPNAME, '<div class="emp"><div class="e1">⏳</div></div>');
  await loadMasters();
  var apRoles = hasRole('AP Kiểm soát (FIN)') || hasRole('AP Giám đốc') || hasRole('AP Officer');
  var q = [
    nenDemDanhSach('Material Request', { fields: ['name'], filters: { material_request_type: 'Purchase', docstatus: ['<', 2], status: ['in', ['Draft', 'Pending', 'Partially Ordered']] }, limit_page_length: 0 }),
    nenDemDanhSach('Material Request', { fields: ['name'], filters: { material_request_type: 'Material Transfer', docstatus: ['<', 2], status: ['in', ['Draft', 'Pending', 'Partially Ordered']] }, limit_page_length: 0 }),
    nenDemDanhSach('Material Request', { fields: ['name'], filters: { material_request_type: 'Manufacture', docstatus: ['<', 2], status: ['in', ['Draft', 'Pending', 'Partially Ordered']] }, limit_page_length: 0 })
  ];
  /* Con so tren the phai dem DUNG cai man hinh se bay ra.
     Workflow "Duyet phieu chi APP" dat tren CA doctype Payment Entry, nen
     Frappe dong dau "Nháp" len moi phieu tien moi - ke ca phieu THU tien
     khach do may tu tao luc doi soat sao ke, va phieu hoan tien cho khach.
     Man Duyet phieu chi da loc ca hai loai do ra tu lau; the o trang chu thi
     chua, nen the bao 12 ma vao thay 7. */
  if (apRoles) q.push(nenDemDanhSach('Payment Entry', { fields: ['name', 'party_type'], filters: { payment_type: 'Pay', workflow_state: ['in', myPayStates()] }, limit_page_length: 0 })
    .then(function (ds) { return ds.filter(function (d) { return (d.party_type || '') !== 'Customer'; }); }));
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
    card('🧾', 'Thanh toán nội bộ', 'Ứng tiền mua đồ cho tiệm, hoặc xin trả thẳng cho người bán. Lập phiếu và xem lại phiếu cũ', 0, 'DNC') +
    /* Uyen theo doi don mua hang va cong no nha cung cap ngay tren app,
       khoi mo Desk (anh Viet 12/08/2026). Hai o nay chi hien voi ke toan,
       thu mua va giam doc - gia mua la thong tin nhay cam. */
    (coQuyenMua()
      ? card('✅', 'Duyệt yêu cầu mua', 'Duyệt từng dòng, kèm tồn kho và số đang chờ về để quyết ngay', 0, 'DUYETYC') +
        card('🧾', 'Đơn mua hàng', 'Đơn đã gửi nhà cung cấp, hàng về tới đâu', 0, 'PO') +
        card('💸', 'Công nợ phải trả', 'Còn nợ nhà cung cấp nào, khoản nào quá hạn', 0, 'CNPT') +
        card('🏭', 'Danh mục nhà cung cấp', 'Hồ sơ nhà cung cấp và gán nhà cung cấp cho mặt hàng', 0, 'NCC') +
        card('💰', 'Bảng giá mua', 'Giá mua theo đơn vị mua, máy tự quy ra giá mỗi đơn vị kho', 0, 'BGIA')
        /* v565, anh Viet 03/10/2026: *"dong y an luon ban khung di"*.
           Hai o KHPO va KHHDM la ban dung tu khuon danh sach dung chung,
           dat canh o cu de doi chieu tung con so. So da khop tu lau, giu
           lai chi lam nhan vien thu mua bam nham vao ban doi chieu. Hai
           MAN van con trong vgbGo, ai co dia chi van mo duoc de soi; chi
           bo cai NUT tren man Thu mua. */
      : '') +
    '</div>';
  if (apRoles) {
    html += '<div class="sec">Duyệt chi</div><div class="card">' +
      card('✍️', 'Duyệt phiếu chi', myPayRoleLabel(), n[3], 'PAY', false) + '</div>';
  }
  if (isBep()) {
    var kcn = 0;
    try {
      var kdd = await nenDemDanhSach('Material Request', { fields: ['name', 'trang_thai_bep'], filters: { material_request_type: 'Manufacture', docstatus: 1, schedule_date: ['<=', today()] }, limit_page_length: 0 });
      kcn = kdd.filter(function (x) { return x.trang_thai_bep !== 'Đã xong'; }).length;
    } catch (e) { }
    var wcn = 0;
    try {
      var wdd = await nenDemDanhSach('Work Order', { fields: ['name', 'status'], filters: { docstatus: 1 }, limit_page_length: 0 });
      wcn = wdd.filter(function (x) { return WODONE.indexOf(x.status) < 0; }).length;
    } catch (e) { }
    html += '<div class="sec">Bếp</div><div class="card">' +
      card('🧑‍🍳', 'Bảng bếp hôm nay', 'Tổng số bánh cần làm, gộp theo món', kcn, 'KIT') +
      card('🏭', 'Lệnh sản xuất', 'Tạo lệnh, trừ nguyên liệu, in tem', wcn, 'MFG') +
      /* Ke hoach san xuat (anh Viet 28/08/2026). Dat ngay tren Lenh san
         xuat vi thu tu lam viec la doc ke hoach truoc, ra lenh sau. */
      card('📋', 'Lập kế hoạch sản xuất', 'Tính toán nguyên vật liệu, bán thành phẩm, thành phẩm sản xuất trong ngày', 0, 'KHSX') +
      /* Don tiec lam theo don, khong co BOM nen khong di qua Lenh san
         xuat. Van dat trong nhom San xuat vi day la viec cua bep. */
      card('🍽️', 'Đơn tiệc / B2B', 'Tiệc và đơn sỉ: xem thực đơn, xuất nguyên liệu theo hợp đồng', 0, 'TIEC') +
      /* Danh muc cong thuc cho bep truong (anh Viet 21/08/2026): xem, tao
         moi va dieu chinh BOM ngay tren dien thoai, khoi mo Desk. */
      card('📖', 'Danh mục công thức', 'Công thức ba khu: Pastry, Baker, Quầy Bar - tạo mới và điều chỉnh có phiên bản', 0, 'CTBOM') + '</div>';
  } else if (ctXemDuoc()) {
    /* Quay Bar va ke toan gia thanh KHONG phai bep: ho khong co viec gi voi
       Bang bep hay Lenh san xuat, chi can dung mot the Cong thuc. Nguoi bep
       van thay the do nam trong nhom Bep nhu cu, khong doi cho (anh Viet
       16/09/2026). */
    html += '<div class="sec">Công thức</div><div class="card">' +
      card('📖', 'Danh mục công thức', 'Công thức ba khu: Pastry, Baker, Quầy Bar - tạo mới và điều chỉnh có phiên bản', 0, 'CTBOM') + '</div>';
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
    try { rcn = (await nenDemDanhSach('Purchase Receipt', { fields: ['name'], filters: { docstatus: 0 }, limit_page_length: 0 })).length; } catch (e) { }
    html += '<div class="sec">Kho</div><div class="card">' +
      card('\ud83d\udce5', 'Nhập kho', 'Quét mã phiếu, đếm hàng rồi nhập máy', rcn, 'RCV') + '</div>';
  }
  /* So nhan banh (anh Viet 23/08/2026): thay cai bang Excel ma cua hang phai
     go tay roi chup gui vao nhom Zalo moi sang. Khong khoa theo quyen kho:
     ban quay nhan banh chu khong phai thu kho. */
  html += '<div class="sec">Cửa hàng</div><div class="card">' +
    card('🥐', 'Nhận bánh đầu ngày', 'Bếp giao bao nhiêu, quầy còn bao nhiêu. Thay bảng Excel gửi Zalo', 0, 'NBANH') + '</div>';
  if (isRnd()) {
    var rdn = 0;
    try { rdn = (await nenDemDanhSach('RnD Purchase Request', { fields: ['name'], filters: { trang_thai: ['in', ['Mới tạo', 'Đang xử lý']] }, limit_page_length: 0 })).length; } catch (e) { }
    html += '<div class="sec">Mua hàng phát sinh (R&amp;D)</div><div class="card">' +
      card('🧪', 'Yêu cầu mua hàng phát sinh', 'Hàng ngoài danh mục hoặc trên 500.000 một hoá đơn', rdn, 'RND') + '</div>';
  }
  var kkn = 0;
  try { kkn = (await nenDemDanhSach('Phieu Kiem Ke', { fields: ['name'], filters: { trang_thai: 'Đang kiểm' }, limit_page_length: 0 })).length; } catch (e) { }
  html += '<div class="sec">Kiểm kê</div><div class="card">' +
    card('\ud83d\udccb', 'Kiểm kê kho', 'Quét mã, đếm hàng thực tế trong kho', kkn, 'KK') + '</div>';
  if (isSales()) {
    var dsn = 0, dtn = 0, phCho = 0, phTreo = 0;
    /* So badge lay tu MAY CHU, khong dem o day: man hinh chi duoc HIEN so,
       khong duoc tu tinh so. Cung nguyen tac voi badge o Ke toan. */
    try {
      var pc = await api('vagabond.don_huy.dem_phieu_cho', {});
      phCho = pc.cho_chi || 0; phTreo = pc.treo || 0;
    } catch (e) { }
    try { dsn = (await nenDemDanhSach('Sales Invoice', { fields: ['name'], filters: { posting_date: today(), docstatus: 0, custom_pancake_id: ['!=', ''] }, limit_page_length: 0 })).length; } catch (e) { }
    try {
      /* Ba cho lech voi man Don con treo, sua cho khop het:
         1. Man hinh mac dinh nhin 14 ngay gan day, the thi khong co moc duoi
            nao ca - moi to nhap nam lai tu thang nao cung dem, nen the bao mot
            so ma vao man khong tim ra to nao ung voi no.
         2. Man hinh chi lay don CHUA vao quay (`vgb_quay` trong), the thi dem
            ca don da co quay. Nhung don do the dem ma man khong bao gio bay
            ra o bat ky chip nao.
         3. Man hinh co ca don HOM NAY, the thi cat hom nay di.
         Loi ghi chu ngay tren day tu truoc van noi "lay theo 14 ngay gan day",
         tuc y dinh ban dau la vay, chi la code khong lam. */
      var mocTreo = new Date(Date.now() - 14 * 864e5).toISOString().slice(0, 10);
      dtn = (await nenDemDanhSach('Sales Invoice', {
        fields: ['name'],
        filters: { posting_date: ['>=', mocTreo], docstatus: 0, custom_pancake_id: ['!=', ''], vgb_quay: ['in', ['', null]], vgb_huy: 0, vgb_tam_tinh: 0 },
        limit_page_length: 0
      })).length;
    } catch (e) { }
    html += '<div class="sec">Bán hàng</div><div class="card">' +
      /* Ba diem ban gio nam chung mot cua: bam vao la chon D1, NVHTN hay
         Sales Online (anh Viet 10/08/2026). Truoc day Sales dung rieng mot
         nut o ngoai nen nhan vien hay vao nham. */
      card('🧾', 'Tính tiền - hoá đơn bán hàng', 'Chọn điểm bán: District 1, NVHTN, Sales Online', dsn, 'POS') +
      /* CRM dat ngay DUOI nut Tinh tien (anh Viet chot 25/08/2026). Man
         nay thay bang tinh tang qua khach VIP cua chi Loan Anh. */
      card('💝', 'CRM - chăm sóc khách hàng', 'Tặng quà khách VIP: lên danh sách, chia việc, theo dõi đã tặng và đã liên hệ', 0, 'TQV') +
        card('🔐', 'Mã OTP quản lý', 'Cấp mã cho nhân viên sửa hoặc xoá hoá đơn', 0, 'OTP') +
      card('🎫', 'Chương trình khuyến mãi - combo', 'Bảy cách thức khuyến mãi, combo rã món, mã voucher, báo cáo tiền đã giảm', 0, 'KM') +
      /* v582: chi Sales that, QLCH, ke toan, giam doc (coQuyenCongNo). */
      (coQuyenCongNo() ? card('📒', 'Công nợ phải thu', 'Khách sỉ gom hoá đơn trả sau: gom phiếu, sinh QR, đối soát', 0, 'CN') : '') +
      /* Sổ hàng tặng cho Sales và quản lý cửa hàng (anh Việt 28/09/2026,
         issue #380): cùng màn Duyệt đơn hàng tặng bên Kế toán, mở sẵn chip
         Hoàn tất để tra lại bill đã tặng. Nút Duyệt vẫn chỉ hiện với giám
         đốc, chặn thật ở máy chủ (hang_tang.duoc_duyet). */
      card('🎁', 'Sổ hàng tặng', 'Đơn tặng đã xong và đang chờ duyệt, xem lại bill, xuất Excel', 0, 'SOTANG') +
      card('👥', 'Danh sách khách hàng', 'Tra cứu khách sỉ và lẻ, hạng khách, mức chi tiêu', 0, 'KH') +
      /* Don treo phai co mot cua rieng, khong nap trong man Doanh thu Sales:
         don treo cua NGAY CU khong ai mo lai ngay do de xem (anh Viet
         13/08/2026). So dem lay theo 14 ngay gan day. */
      card('⏳', 'Đơn còn treo', 'Hoá đơn chưa ghi sổ được và lý do vì sao', dtn, 'DTREO') +
      /* Phieu hoan don huy (anh Viet 31/08/2026). Sales lap phieu xong la
         mat dau, vi phan con lai nam ben Ke toan ma v355 da khoa phan he do
         lai. O nay la cua so CHI DOC mo ve phia Sales, kem nut tai uy nhiem
         chi de gui cho khach. */
      card('💸', 'Danh sách phiếu hoàn tiền',
        'Cập nhật danh sách phiếu hoàn đơn huỷ, phiếu hoàn tiền cho đơn hàng đã ghi sổ, tiền khách nộp thừa. Kế toán chi tới đâu hiện tới đó, uỷ nhiệm chi tải về gửi khách' +
        (phTreo ? ' ⚠️ ' + phTreo + ' phiếu treo quá lâu, tiền khách vẫn ở tiệm.' : ''),
        phCho, 'PHHUY') +
      /* Bien nhan nop tien mat (anh Viet 30/08/2026, theo mau ben Lark).
         Thu ngan ba diem ban dem so to, doi chieu doanh thu tien mat cua
         ngay, ky tay roi mang tien ve. O nay bay phieu CUA CHINH MINH;
         ke toan co o rieng ben phan he Ke toan bay tat ca. */
      card('💵', 'Biên nhận nộp tiền mặt', 'Đếm số tờ, đối chiếu doanh thu của ngày, ký giao nhận', 0, 'BNTM') + '</div>';
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
      /* Anh Viet 03/10/2026: tien tra cho app giao ngoai truoc day chi nam
         roi tren tung van don, khong ai cong duoc theo thang. */
      + card('🧾', 'Phí giao hàng book app', 'Tiền trả cho Ahamove, GreenSM, BE, Grab, Lalamove theo tháng', 0, 'PHIAPP')
      + card('⚠️', 'Cảnh báo thanh toán', 'Hoá đơn thiếu hoặc sai phương thức, vận đơn treo COD nhầm', 0, 'CBTT')
      + '</div>';
  }
  // Quyền báo cáo theo máy chủ; giữ điều kiện cũ nếu backend chưa có metadata.
  var xemBaoCao = S.quyenNen && typeof S.quyenNen.bao_cao === 'boolean'
    ? S.quyenNen.bao_cao : (isSales() || hasRole('Accounts User') || hasRole('Accounts Manager'));
  /* Viec hom nay (#351): quyen do may chu tra ve (phan_tich.QUYEN_BANG_SANG).
     Marketing hay quan ly bep co the co quyen nay ma khong co quyen xem bao
     cao doanh thu, nen o nay dung duoc ca khi khong co khoi Bao cao. */
  var xemBangSang = !!(S.quyenNen && S.quyenNen.bang_sang);
  var oBangSang = xemBangSang ? card('🧭', 'Việc hôm nay', 'Máy đọc số hôm qua, nháp sẵn việc để giao', 0, 'BCSANG') : '';
  if (!xemBaoCao && oBangSang) html += '<div class="sec">Việc hôm nay</div><div class="card">' + oBangSang + '</div>';
  if (xemBaoCao) {
    html += '<div class="sec">Báo cáo</div><div class="card">' + oBangSang +
      card('📈', 'Báo cáo tổng hợp', 'Đang cộng sổ doanh thu hôm nay...', 0, 'BCHUB') +
      card('🛵', 'Doanh thu theo nguồn đơn', 'Tại chỗ, Sales Online, GrabFood, ShopeeFood...', 0, 'BC:BC03') +
      card('💳', 'Phương thức thanh toán', 'Tiền mặt, chuyển khoản, thẻ, ví, công nợ', 0, 'BC:BC04') +
      card('🧾', 'Đối soát hoá đơn điện tử', 'Chờ ký, đã ký, CQT chấp nhận, chưa xuất', 0, 'BC:BC05') +
      card('🍰', 'Món bán chạy', 'Xếp hạng theo số lượng bán ra', 0, 'BC:BC08') +
      card('✂️', 'Sửa và huỷ hoá đơn', 'Ai sửa, ai huỷ, làm gì trên hoá đơn nào', 0, 'BC:BC07') + '</div>';
  }
  /* KHOI KE TOAN: chi ke toan, thu mua, giam doc. Anh Viet 30/08/2026 bat
     duoc lo hong nay - dieu kien cu la `isSales()` nen ca thu ngan cung
     nhin thay Cong no phai tra, Tai san va But toan tay. Xem
     `coQuyenKeToan` o 01-khung-app.js. */
  if (coQuyenKeToan()) {
    /* Badge do so phieu hoan tien dang CHO CHI (anh Viet 18/08/2026): "chi
       Dung Ke toan truong de nhan biet".

       Hong thi bang 0 chu khong chan trang chu: mot phep dem hong khong
       duoc lam ca man hinh trang. Cung mot nep voi bcSoHomNay. */
    var htChoChi = 0;
    try { if (nenCoQuyen('ban_hang')) htChoChi = (await api('vagabond.hoan_tien.dem_cho_chi', {})).cho_chi || 0; } catch (e) { }
    /* Don hang tang cho giam doc duyet. So lay tu MAY CHU, cung nguyen tac
       voi badge phieu hoan: man hinh chi duoc HIEN so, khong tu dem. */
    var tgCho = 0, tgQuaHan = 0;
    try {
      var tg = nenCoQuyen('ban_hang') ? await api('vagabond.hang_tang.dem_cho_duyet', {}) : {};
      tgCho = tg.cho || 0; tgQuaHan = tg.qua_han || 0;
    } catch (e) { }
    /* v550: so hoa don ghi so luc kho chua co hang, lay tu may chu. */
    var tkCho = 0;
    try { tkCho = (await api('vagabond.tru_kho_bu.dem_chua_tru_kho', {})).so || 0; } catch (e) { }
    html += '<div class="sec">Kế toán</div><div class="card">' +
      card('🧾', 'Hoá đơn bán ra', 'Lọc theo điểm bán và trạng thái hoá đơn điện tử', 0, 'HDBAN') +
      card('📦', 'Hoá đơn chưa trừ kho', 'Bán lúc kho điểm bán chưa có hàng, trừ bù khi hàng về', tkCho, 'TRUKHO') +
      card('🛒', 'Hoá đơn mua vào', 'Lọc theo nhà cung cấp, hạn trả, còn nợ', 0, 'HDMUA') +
      card('🔗', 'Đối chiếu hoá đơn mua', 'Nối hoá đơn nhà cung cấp với phiếu nhập kho rồi ghi sổ một nút', 0, 'DCM') +
      /* v579 (#420): đối soát báo cáo vendor, tách khỏi ô Đối soát hoá đơn
         điện tử (trạng thái phát hành HĐĐT) theo maquette anh duyệt 03/10. */
      card('⇄', 'Đối soát nhà cung cấp', 'Tiền bán qua sàn và cổng thẻ · Chuyến đi · Thẻ tín dụng', 0, 'DSVN') +
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
      (xemBaoCao ? card('🏛️', 'Đối soát hoá đơn điện tử', 'Chờ ký, đã ký, CQT chấp nhận, chưa xuất', 0, 'BC:BC05') : '') +
      /* Hai man cho chi Dung, anh Viet dat 14/08/2026. Truoc do so co 174
         tai khoan tieng Viet ma chi hai but toan go tay, va khong mot tai
         san nao duoc khai. */
      card('🏗️', 'Tài sản và công cụ dụng cụ', 'Khai tài sản, chạy khấu hao và phân bổ 242 hàng tháng', 0, 'TS') +
      /* Bien nhan nop tien mat, ban cua KE TOAN: bay phieu cua MOI nguoi,
         loc theo diem ban, xuat Excel. Nhan vien lap phieu o o cung ten
         ben phan he Ban hang. Cung mot bang du lieu, khac moi bo loc. */
      card('💵', 'Biên nhận nộp tiền mặt', 'Theo dõi phiếu của cả ba điểm bán, ký nhận tiền, xuất Excel', 0, 'NQ') +
      card('📒', 'Bút toán tay', 'Trích lương, bảo hiểm, phân bổ, kết chuyển thuế theo định khoản mẫu', 0, 'BT') +
      /* Duyet don hang tang (anh Viet 31/08/2026). Don tra bang phuong thuc
         Hang tang KHONG ghi so duoc cho toi khi giam doc bam duyet o day.
         Dat trong phan he Ke toan theo dung yeu cau cua anh Viet. */
      card('🎁', 'Duyệt đơn hàng tặng',
        'Đơn tặng không thu tiền đang chờ duyệt' +
        (tgQuaHan ? ' · ' + tgQuaHan + ' đơn chờ quá lâu' : '') +
        '. Duyệt rồi đơn mới ghi sổ được.', tgCho, 'DUYETTANG') + '</div>';
  }

  /* Nhan su. Anh Viet chot 01/09/2026: nut KPI chi cho quan ly, ke toan,
     giam doc thay. Chan that nam o may chu (kpi._kiem_quyen), day chi an o.

     O "KPI cua toi" nam NGOAI dieu kien do: ai cung phai xem duoc diem cua
     chinh minh. Cuoi ky moi cho biet thi KPI chi la bang cham diem, khong
     phai cong cu dieu hanh. */
  if (coQuyenHRM()) {
    html += '<div class="sec">Nhân sự</div><div class="card">' +
      card('📊', 'Duyệt KPI và hoa hồng',
        'Chấm điểm theo kỳ tháng, tính hoa hồng bậc thang, duyệt ba cấp rồi đẩy sang đề nghị chi',
        0, 'KPI') +
      card('🎯', 'Bảng chỉ tiêu và bậc hoa hồng',
        'Trọng số từng vai, sàn, mốc, trần và ô thử tính trước khi chốt', 0, 'KPICD') + '</div>';
  }
  html += '<div class="sec">KPI của tôi</div><div class="card">' +
    card('🙋', 'Điểm KPI của tôi',
      'Xem điểm từng tiêu chí của chính mình và nói lại nếu thấy chưa đúng', 0, 'KPITOI') + '</div>';

  html += '<div class="sec">Cài đặt</div><div class="card">' +
    (coQuyenMua() || hasRole('Accounts Manager') || hasRole('System Manager')
      ? card('🏪', 'Điểm bán', 'Chi nhánh, mã quầy, nguồn đơn - khai một nơi dùng cho cả hệ', 0, 'CDDB') +
        card('🔒', 'Khoá sổ', 'Chốt số liệu kỳ cũ, không ai sửa hay huỷ được nữa', 0, 'CDKS') +
        card('💳', 'Phương thức thanh toán', 'Máy cà thẻ, ví, công nợ - và mã gửi cơ quan thuế', 0, 'CDPT') +
        card('🏦', 'Tài khoản nhận tiền', 'Số tài khoản sinh mã QR, khai riêng được cho từng nguồn đơn', 0, 'CDTK') +
        card('🎂', 'Danh mục sản phẩm', 'Mở mã hàng mới trong bảy ô, máy tự đặt mã và cảnh báo trùng tên', 0, 'CDSP') +
        card('🖨', 'Máy in', 'Sổ máy in từng điểm bán và khổ giấy cho mỗi loại phiếu', 0, 'CDMI') +
        /* Mau in nam ngay duoi May in vi hai man hay bi lan: May in la
           "in o dau, to bao nhieu", Mau in la "tren to do in nhung gi". */
        card('🧾', 'Mẫu in ấn', 'Trên tờ hoá đơn và tem in những gì, chữ to hay nhỏ, in thử ngay tại quầy', 0, 'CDMU') +
        card('🙅', 'Quyền tại quầy', 'Thu ngân được bỏ món tới đâu, khi nào phải xin quản lý', 0, 'CDQQ') +
        card('🎖️', 'Hạng thành viên', 'Ngưỡng lên hạng, giảm giá, tích điểm và xét lại hàng loạt', 0, 'CDHT') +
        card('🌙', 'Cuối ngày: ghi sổ và xuất hoá đơn', 'Bật tắt từng điểm bán, chọn giờ chạy', 0, 'CDCN') +
        card('📦', 'Ngưỡng kho', 'Dung sai giao thừa giao thiếu, hạn dùng tối thiểu khi nhận', 0, 'CDKHO') +
        card('💬', 'Trợ lý hướng dẫn dùng app', 'Khoá API, hạn mức lượt hỏi và ai được dùng', 0, 'CDTL') +
        card('🏦', 'SePay: nhận giao dịch ngân hàng', 'Đường dẫn webhook, bản đồ tài khoản, nạp bù sao kê cũ', 0, 'CDSE') +
        /* Nhập tệp sao kê: bù những khoản SePay không đẩy về. OCB không có
           một khoản nào dưới 100k trong khi MB có sáu - chỗ mất nằm giữa
           NGÂN HÀNG và SePay, ngoài tầm sửa của tiệm. Đây là phần trong tầm. */
        card('📑', 'Nhập tệp sao kê ngân hàng', 'Tải tệp ngân hàng gửi, máy bù đúng những dòng còn thiếu', 0, 'NHAPSK')
      : '') +
    /* Trang dat banh web: Minh Vu doi anh ben Pancake xong bam mot nut la web
       doi theo, khong phai cho hay nho ai deploy (anh Viet 03/09/2026). Mo
       cho ca sales vi chinh sales la nguoi cam danh muc Pancake. */
    /* Cai dat loi va API (v570): trang Vagabond Settings tren app. Chi quan
       tri; may chu kiem lai quyen o tung cua vagabond.cai_dat_loi. */
    (hasRole('System Manager')
      ? card('🔑', 'Cài đặt lõi và API', 'Khoá kết nối, hoá đơn điện tử, ngân hàng, giao hàng, Zalo: điền ngay trên app', 0, 'CDLOI')
      : '') +
    (coQuyenMua() || hasRole('Sales User') || hasRole('Sales Manager') || hasRole('System Manager')
      ? card('🌐', 'Trang đặt bánh web', 'Đồng bộ ảnh và mô tả từ Pancake, xem tab nào đang lên bao nhiêu mã', 0, 'CDWEB')
      : '') +
    /* Quan ly nguoi dung: anh Viet, chi Dung va De. Bay theo goi chuc vu chu
       khong bay ma tran 40 vai tro cua Frappe ra man hinh dien thoai. */
    /* Bo chuyen BTP cap 1 sang Phantom. Chi giam doc va quan ly he thong,
       vi day la thao tac doi cau hinh kho cua ca tram ma hang. */
    (hasRole('System Manager') || hasRole('Giám đốc')
      ? card('🧹', 'Dọn chứng từ thử', 'Đóng nốt lệnh sản xuất treo trên bán thành phẩm trước khi chuyển Phantom', 0, 'PTDON') +
        card('👻', 'Chuyển bán thành phẩm sang Phantom', 'Bỏ ghi sổ kho cấp BTP, chạy thử xem trước rồi mới ghi thật', 0, 'PTCH')
      : '') +
    (hasRole('System Manager') || hasRole('Quản lý người dùng')
      ? card('👥', 'Quản lý người dùng', 'Mời tài khoản mới, xếp gói chức vụ, bật tắt nhân viên nghỉ', 0, 'QLND') +
        card('🗝', 'Quản lý quyền', 'Mười một gói chức vụ, gói nào làm được gì và ai đang giữ', 0, 'QLQ')
      : '') +
    /* Thông báo đẩy: MỌI vai đều thấy ô này, vì phiếu chờ ai thì báo người
       đó. Để trong Cài đặt chứ không hỏi ngay lúc mở app: trình duyệt chỉ
       cho hỏi một lần, bấm Chặn là chặn vĩnh viễn. */
    card('🔔', 'Thông báo trên điện thoại', 'Bật rung khi có phiếu chờ bạn duyệt, và kiểm thử một tin', 0, 'CDTB') +
    card('📦', 'Tra tồn kho', 'Xem tồn hiện tại theo kho', 0, 'STOCK') +
    card('🧭', 'Tồn kho theo chặng', 'Hàng của bếp đang đứng ở chặng nào: nguyên liệu, BTP sơ cấp, BTP sẵn sàng hay thành phẩm', 0, 'TONCHANG') +
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
  bsSoTrangChu();
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
  if (!nenCoQuyen('bao_cao')) return;
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

/* ---------- Gom nhom trong tung phan he (anh Viet 03/10/2026) ----------

   Anh noi: *"ben trong tat ca cac nut phan he em cho nhom lai dum anh cac
   nut tinh nang sao cho phu hop"*. Man Ke toan co 15 o xep thanh mot cot
   dai, Cai dat co 23 o, nen tim mot viec phai cuon va doc het tu dau.

   `nhom` chi la cach XEP CHO, KHONG phai cach chan quyen. Quyen van nam o
   `keys` va o may chu: o nao nguoi nay khong duoc xem thi khong co trong
   VGB_HUB, nhom chua no tu rong va khong hien. Them o moi ma quen xep vao
   nhom thi o do roi xuong nhom "Khac" o cuoi man chu KHONG bien mat - ca
   kiem thu_gom_nhom_565.py chot dung cho nay.

   Thu tu nhom theo tan suat dung: viec hang ngay len tren.

   Doi chieu SAP S/4HANA: ho gom theo LOAI CHUNG TU chu khong gom theo ten
   man, nen Xuat kho o day tach "Xuat noi bo" (Stock Transfer, hang van
   trong nha) khoi "Xuat ra ngoai" (Goods Issue, hang roi tiem) dung nhu ho
   chia Goods Movement. */
var VGB_NHOM = [
  /* Đặt hàng: ai cũng vào được, vì lập yêu cầu mua nguyên vật liệu là việc
     của mọi bộ phận. Các ô có giá mua và công nợ đã tách sang Thu mua. */
  {
    k: 'DH', ten: 'Đặt hàng', icon: '🛒', keys: ['Purchase', 'Transfer', 'RND', 'DNC'],
    nhom: [
      { t: 'Xin hàng', p: 'việc hàng ngày', keys: ['Purchase', 'Transfer'] },
      { t: 'Khác', p: '', keys: ['RND', 'DNC'] }
    ]
  },
  {
    k: 'SX', ten: 'Sản xuất', icon: '🧑‍🍳',
    keys: ['Manufacture', 'KIT', 'MFG', 'KHSX', 'BTPO', 'CTBOM', 'TIEC'],
    nhom: [
      { t: 'Việc bếp hôm nay', p: '', keys: ['KIT', 'Manufacture', 'MFG'] },
      { t: 'Kế hoạch', p: '', keys: ['KHSX', 'TIEC'] },
      { t: 'Công thức', p: '', keys: ['CTBOM', 'BTPO'] }
    ]
  },
  { k: 'NK', ten: 'Nhập kho', icon: '📥', keys: ['RCV', 'NHANDC', 'NBANH'] },
  {
    k: 'XK', ten: 'Xuất kho', icon: '📤',
    keys: ['XKH', 'XKNB', 'XKPV', 'XKD', 'XKTRA', 'XKSI'],
    nhom: [
      { t: 'Xuất nội bộ', p: 'trong nhà, không ra ngoài', keys: ['XKD', 'XKNB', 'XKPV'] },
      { t: 'Xuất ra ngoài', p: '', keys: ['XKSI', 'XKTRA'] },
      { t: 'Xuất bỏ', p: '', keys: ['XKH'] }
    ]
  },
  { k: 'KK', ten: 'Kiểm kê', icon: '🧮', keys: ['KK', 'STOCK', 'TONCHANG'] },
  {
    k: 'BH', ten: 'Bán hàng', icon: '🎂',
    keys: ['KBD', 'KBM', 'POS', 'TQV', 'HDG', 'OTP', 'KM', 'CN', 'SOTANG', 'KH', 'DTREO', 'PHHUY', 'BNTM'],
    nhom: [
      { t: 'Bán và thu tiền', p: 'việc của quầy', keys: ['POS', 'DTREO', 'BNTM'] },
      { t: 'Bánh và tồn', p: 'đầu ngày', keys: ['KBD', 'KBM'] },
      { t: 'Khách hàng', p: 'chăm sóc và công nợ', keys: ['TQV', 'KH', 'CN', 'SOTANG'] },
      { t: 'Chương trình và hợp đồng', p: '', keys: ['KM', 'HDG'] },
      { t: 'Quản lý', p: 'ít dùng', keys: ['OTP', 'PHHUY'] }
    ]
  },
  {
    k: 'GH', ten: 'Giao hàng', icon: '🚚', keys: ['VD', 'CPX', 'DSCOD', 'PHIAPP', 'CBTT'],
    nhom: [
      { t: 'Vận đơn', p: 'việc hàng ngày', keys: ['VD'] },
      { t: 'Tiền giao hàng', p: 'đối soát', keys: ['DSCOD', 'PHIAPP', 'CPX', 'CBTT'] }
    ]
  },
  {
    k: 'BC', ten: 'Báo cáo', icon: '📈',
    keys: ['BCSANG', 'BCHUB', 'BC:BC03', 'BC:BC04', 'BC:BC05', 'BC:BC08', 'BC:BC07'],
    nhom: [
      { t: 'Xem hàng ngày', p: '', keys: ['BCSANG', 'BCHUB'] },
      { t: 'Doanh thu', p: '', keys: ['BC:BC03', 'BC:BC04', 'BC:BC08'] },
      { t: 'Kiểm soát', p: '', keys: ['BC:BC05', 'BC:BC07'] }
    ]
  },
  /* Thu mua (anh Việt 18/08/2026): "các nút tính năng của luồng Mua hàng
     đang để chung chung khiến toàn bộ nhân viên đều nhìn thấy". Nhóm này
     nằm ngay trên Kế toán và chỉ hiện với Thu mua, Kế toán, Giám đốc.

     Không cần khoá riêng ở đây: các ô bên trong đều dựng có điều kiện
     coQuyenMua() trong scrHome, nên người không có quyền thì nhóm rỗng và
     vòng lặp dưới tự bỏ qua. Chặn thật nằm ở máy chủ, quyen_phan_he.py.

     v565: hai ô "bản khung" (KHPO, KHHDM) đã ẩn khỏi đây theo anh Việt
     03/10/2026. Hai ô đó dựng để đối chiếu số với bản cũ, số đã khớp từ
     lâu, giữ lại chỉ làm nhân viên thu mua bấm nhầm vào bản đối chiếu. */
  {
    k: 'TM', ten: 'Thu mua', icon: '🧾', keys: ['DUYETYC', 'PO', 'CNPT', 'NCC', 'BGIA'],
    nhom: [
      { t: 'Mua hàng', p: 'việc hàng ngày', keys: ['DUYETYC', 'PO'] },
      { t: 'Nhà cung cấp', p: '', keys: ['NCC', 'BGIA', 'CNPT'] }
    ]
  },
  {
    k: 'KT', ten: 'Kế toán', icon: '🧮',
    keys: ['HDBAN', 'TRUKHO', 'HDMUA', 'DCM', 'DSVN', 'CN', 'CNPT', 'HT', 'APPTT', 'DSTTNB', 'PAY', 'TS', 'NQ', 'BT', 'DUYETTANG', 'BC:BC05'],
    nhom: [
      { t: 'Hoá đơn', p: 'làm hàng ngày', keys: ['HDBAN', 'TRUKHO', 'HDMUA', 'DCM', 'DSVN', 'BC:BC05'] },
      { t: 'Công nợ', p: 'ai nợ ai', keys: ['CN', 'CNPT'] },
      { t: 'Chi tiền', p: 'duyệt và trả', keys: ['APPTT', 'DSTTNB', 'PAY', 'HT', 'NQ'] },
      { t: 'Tổng hợp và tài sản', p: 'cuối tháng', keys: ['BT', 'TS', 'DUYETTANG'] }
    ]
  },
  /* Nhan su (anh Viet chot 01/09/2026). Nhom nay CHI hien voi quan ly, ke
     toan va giam doc - dieu kien coQuyenHRM() dung o scrHome. O "KPI cua
     toi" thi nguoc lai, ai cung vao duoc, vi do la diem cua chinh ho. */
  { k: 'NS', ten: 'Nhân sự', icon: '👥', keys: ['KPI', 'KPICD', 'KPITOI'] },
  /* Danh mục nằm ngay trên Cài đặt (anh Việt chốt 18/08/2026). Khoá của
     các ô mang tiền tố DM: nên vgbGo bắt bằng MỘT nhánh tiền tố, không phải
     16 nhánh chép tay. */
  {
    k: 'DM', ten: 'Danh mục', icon: '📚',
    keys: VGB_DM.map(function (x) { return 'DM:' + x.m; }),
    nhom: [
      { t: 'Sản phẩm và kho', p: '', keys: ['DM:DMSP', 'DM:DMNSP', 'DM:DMDVT', 'DM:DMQD', 'DM:DMKHO', 'DM:DMBOM'] },
      { t: 'Nhà cung cấp và giá mua', p: '', keys: ['DM:DMNCC', 'DM:DMNNCC', 'DM:DMGIA'] },
      { t: 'Khách hàng', p: '', keys: ['DM:DMKH', 'DM:DMNKH'] },
      { t: 'Kế toán và thanh toán', p: '', keys: ['DM:DMPT', 'DM:DMNH', 'DM:DMTK', 'DM:DMTHUE', 'DM:DMTHUEM'] }
    ]
  },
  {
    k: 'KHAC', ten: 'Cài đặt', icon: '⚙️',
    keys: ['CDLOI', 'CDDB', 'CDKS', 'CDPT', 'CDTK', 'CDSP', 'CDMI', 'CDMU', 'CDQQ', 'CDHT', 'CDCN', 'CDKHO', 'CDTL', 'CDSE', 'NHAPSK', 'CDTB', 'CDWEB', 'PTDON', 'PTCH', 'QLND', 'QLQ', 'ACC', 'STOCK', 'TONCHANG'],
    nhom: [
      { t: 'Lõi hệ thống', p: '', keys: ['CDLOI'] },
      { t: 'Cửa hàng và bán hàng', p: '', keys: ['CDDB', 'CDPT', 'CDQQ', 'CDHT', 'CDCN', 'CDWEB'] },
      { t: 'Kho và sản phẩm', p: '', keys: ['CDSP', 'CDKHO', 'STOCK', 'TONCHANG', 'PTCH'] },
      { t: 'Kế toán và ngân hàng', p: '', keys: ['CDKS', 'CDTK', 'CDSE', 'NHAPSK', 'PTDON'] },
      { t: 'In ấn và nhắc việc', p: '', keys: ['CDMI', 'CDMU', 'CDTB', 'CDTL'] },
      { t: 'Người dùng', p: '', keys: ['QLND', 'QLQ', 'ACC'] }
    ]
  }
];

var VGB_HUB = {};

/* ---------- O tim nghiep vu, o ghim, va phep chia nhom (v565) ----------

   Anh Viet 03/10/2026: *"them o 'Tim kiem nghiep vu' de go la ra nut de truy
   cap luon"* va *"them tinh nang duoc pin 5 o hay truy cap nhat cho tung user
   duoc dung (ke toan pin gi cua ke toan hay xai)"*.

   Bon ham duoi day la PHEP THUAN: khong doc DOM, khong goi mang, khong doc
   bien toan cuc nao ngoai tham so. Lam vay de kiem thu chay that duoc trong
   node ma khong can trinh duyet - bai hoc dieu 16 cua CLAUDE.md: do chuoi
   trong ma nguon khong phai la kiem thu. */

/* Bo dau tieng Viet de go "cong no" van ra "Cong no", "kiem ke" ra "Kiem ke".

   Phai bo ca chu d gach: normalize('NFD') khong tach duoc d thanh d + dau,
   nen "don" se khong khop "don" neu thieu dong replace cuoi. */
function vgbBoDau(s) {
  return String(s == null ? '' : s).toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\u0111/g, 'd');
}

/* Tim nghiep vu theo tu khoa. PHEP THUAN.

   Luat: MOI tu go vao deu phai khop o dau do (ten, ten phan he, hoac mo ta),
   nen go them tu la loc hep lai chu khong no ra. Khop trong TEN duoc diem cao
   hon khop trong mo ta, va khop tu dau ten duoc cao nhat - go "cong no" thi
   "Cong no phai thu" phai dung tren "Hoa don mua vao" (mo ta co chu "con no").

   Khi diem bang nhau thi giu DUNG thu tu danh ba dua vao, khong xep lai theo
   bang chu cai: thu tu danh ba la thu tu phan he tren trang chu, nguoi dung
   quen cai do. */
function vgbTimNghiepVu(tu, ds) {
  var t = vgbBoDau(tu).trim().replace(/\s+/g, ' ');
  if (t.length < 2) return [];
  var tus = t.split(' ');
  var ra = [];
  for (var i = 0; i < (ds || []).length; i++) {
    var x = ds[i];
    var ten = vgbBoDau(x.ten), mo = vgbBoDau(x.mo), ph = vgbBoDau(x.phanHe);
    var du = 1, diem = 0;
    for (var j = 0; j < tus.length; j++) {
      var w = tus[j];
      if (ten.indexOf(w) >= 0) diem += 10;
      else if (ph.indexOf(w) >= 0) diem += 4;
      else if (mo.indexOf(w) >= 0) diem += 2;
      else { du = 0; break; }
    }
    if (!du) continue;
    if (ten.indexOf(t) === 0) diem += 20;
    else if (ten.indexOf(t) > 0) diem += 8;
    ra.push({ k: x.k, ten: x.ten, mo: x.mo, phanHe: x.phanHe, diem: diem, tt: i });
  }
  ra.sort(function (a, b) { return b.diem - a.diem || a.tt - b.tt; });
  return ra;
}

/* Tran so o ghim. Dat MOT cho, ca ben Python (vagabond/ghim.py) cung dat
   mot cho, va ca kiem doi chieu hai con so phai bang nhau. */
var VGB_GHIM_TOI_DA = 5;

/* Hai o KHONG thuoc phan he nao: Viec can lam va So tay. Chung ve rieng tren
   trang chu, bam mot lan la vao thang.

   Vi sao phai khai thanh BANG (Codex bat R2-F4 tren PR #426): truoc day hai o
   nay viet tay thang vao chuoi HTML cua luoi, nen chung khong co trong VGB_HUB
   va o tim khong thay. Go "so tay" ra 0 ket qua, do la mot trong hai loi vao
   nguoi ta bam nhieu nhat. Khai mot cho roi ca luoi, o tim va o ghim cung doc
   tu day (CLAUDE.md dieu 18).

   `rieng: 1` de vong gom "o chua xep nhom nao" KHONG keo chung vao Cai dat,
   khong thi trang chu moc them mot o So tay thu hai. */
var VGB_O_RIENG = [
  { k: 'VCL', ic: '\ud83d\udccc', ten: 'Vi\u1ec7c c\u1ea7n l\u00e0m',
    mo: 'Danh s\u00e1ch phi\u1ebfu \u0111ang ch\u1edd b\u1ea1n x\u1eed l\u00fd' },
  { k: 'SOTAY', ic: '\ud83d\udcd8', ten: 'S\u1ed5 tay',
    mo: 'H\u01b0\u1edbng d\u1eabn d\u00f9ng app theo t\u1eebng vi\u1ec7c' }
];

/* Chuan hoa danh sach ghim: bo rong, bo trung, bo o khong con quyen xem,
   cat con toi da nam. PHEP THUAN, `co` la mot ham hoi "o nay co dung duoc
   khong" chu khong doc VGB_HUB thang, de kiem thu truyen vao gi cung duoc.

   Giu DUNG thu tu nguoi dung xep, khong xep lai: thu tu ghim la thu tu ho
   muon thay tren trang chu. */
function vgbChuanGhim(ds, co) {
  var ra = [], da = {};
  for (var i = 0; i < (ds || []).length; i++) {
    var k = ds[i];
    if (!k || typeof k !== 'string' || da[k]) continue;
    if (co && !co(k)) continue;
    da[k] = 1;
    ra.push(k);
    if (ra.length >= VGB_GHIM_TOI_DA) break;
  }
  return ra;
}

/* Chia cac o cua mot phan he thanh nhom de ve. PHEP THUAN.

   Hai viec quan trong hon ve ngoai cua no:

   1. O khai trong `nhom` ma khong co trong `keys` thi KHONG ve - khong duoc
      lam cho mot o lot vao man nay chi vi ai danh may sai mot khoa.
   2. O co trong `keys` ma chua xep vao nhom nao thi roi xuong nhom "Khac" o
      cuoi, KHONG bien mat. Day la cho de mat nut nhat: them nghiep vu moi
      la viec xay ra hang tuan, con nho sua bang nhom thi khong. */
function vgbChiaNhom(nh, co) {
  var coKey = {}, i, k;
  for (i = 0; i < nh.keys.length; i++) coKey[nh.keys[i]] = 1;
  var da = {}, ra = [], dsn = nh.nhom || [];
  for (i = 0; i < dsn.length; i++) {
    var g = dsn[i], ks = [];
    for (var j = 0; j < g.keys.length; j++) {
      k = g.keys[j];
      if (da[k] || !coKey[k]) continue;
      da[k] = 1;
      if (co(k)) ks.push(k);
    }
    if (ks.length) ra.push({ t: g.t, p: g.p || '', keys: ks });
  }
  var le = [];
  for (i = 0; i < nh.keys.length; i++) {
    k = nh.keys[i];
    if (da[k]) continue;
    da[k] = 1;
    if (co(k)) le.push(k);
  }
  if (le.length) ra.push({ t: ra.length ? 'Kh\u00e1c' : '', p: '', keys: le });
  return ra;
}

/* Danh ba phang moi nghiep vu dang dung duoc, de o tim doc mot cho.

   Ten phan he lay tu VGB_NHOM, cung mot nguon voi luoi o lon, nen khong co
   chuyen o tim noi "Cong no phai tra" thuoc Thu mua ma luoi lai xep cho khac.
   O nao thuoc hai phan he (Cong no phai tra o ca Thu mua va Ke toan) thi lay
   phan he DAU TIEN tim thay, va chi hien mot dong trong ket qua. */
function vgbDanhBaNghiepVu() {
  var ra = [], da = {};
  /* Hai o rieng dung dau danh ba: chung la loi vao dung nhieu nhat tren trang
     chu nen go ra phai thay ngay (Codex R2-F4). */
  for (var r = 0; r < VGB_O_RIENG.length; r++) {
    var rk = VGB_O_RIENG[r].k, ro = VGB_HUB[rk];
    if (!ro || da[rk]) continue;
    da[rk] = 1;
    ra.push({ k: rk, ten: ro.ten, mo: ro.mo || '', phanHe: 'Trang ch\u1ee7' });
  }
  for (var i = 0; i < VGB_NHOM.length; i++) {
    var nh = VGB_NHOM[i];
    for (var j = 0; j < nh.keys.length; j++) {
      var k = nh.keys[j];
      if (da[k]) continue;
      var o = VGB_HUB[k];
      if (!o || !o.ten) continue;
      da[k] = 1;
      ra.push({ k: k, ten: o.ten, mo: o.mo || '', phanHe: nh.ten });
    }
  }
  return ra;
}

/* Doc ten, mo ta va bieu tuong tu doan HTML da dung san cua tung o.

   Vi sao doc lai tu HTML chu khong bat moi cho dung o phai khai them ten:
   cac o duoc dung o BON cho khac nhau (card() trong scrHome, vgbODong(),
   vong lap VGB_DM, va o Thanh toan noi bo gan co dieu kien). Bat bon cho khai
   them la bon cho se lech nhau. Doc lai tu ban da dung thi o tim thay dung
   cai chu nguoi dung dang nhin. */
function vgbDocNhanHub() {
  var tam = document.createElement('div');
  for (var k in VGB_HUB) {
    var o = VGB_HUB[k];
    if (!o || o.ten !== undefined) continue;
    tam.innerHTML = o.html;
    var e1 = tam.querySelector('.h1'), e2 = tam.querySelector('.h2'), ei = tam.querySelector('.hi');
    o.ten = e1 ? (e1.textContent || '').trim() : '';
    o.mo = e2 ? (e2.textContent || '').trim() : '';
    o.ic = ei ? (ei.textContent || '').trim() : '';
  }
}

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
    /* KHUNG NHAP KIEU THE (anh Viet 27/08/2026: *"visual dang bi xau...
       nhin no bi tho so"*).

       Man Lap phieu xuat huy truoc day la mot cot nhan xam va o nhap tran,
       khong co the, khong co vien, khong co biểu tuong - nhin nhu mot to
       khai chua lam xong, trong khi moi man khac trong app deu la the trang
       bo goc co do do. Chenh lech do lam nguoi dung tuong man nay chua
       xong, va hoi lai.

       Cac lop duoi day dung chung cho MOI man co bieu mau, khong rieng
       xuat huy - dat ten `vf` (vagabond form) chu khong dat ten theo mot
       man cu the. */
    '.vf{background:#fff;border-radius:14px;padding:2px 14px 14px;margin-bottom:12px;' +
    'box-shadow:0 1px 2px rgba(16,24,40,.06)}' +
    '.vf .vfh{display:flex;align-items:center;gap:9px;padding:13px 0 3px}' +
    '.vf .vfh .ic{font-size:17px;line-height:1;flex:none}' +
    '.vf .vfh b{font-size:14px;color:#101828;font-weight:700;flex:1}' +
    '.vf .vfh .bat{font-size:11px;font-weight:700;color:#b42318;background:#fef3f2;' +
    'border-radius:999px;padding:2px 8px;flex:none}' +
    '.vf .vfm{font-size:12px;color:#98a2b3;line-height:1.5;margin:0 0 8px}' +
    /* O chon: bo mui ten mac dinh cua trinh duyet roi tu ve mot cai, de ba
       he dieu hanh nhin giong nhau. */
    '.vfs{width:100%;box-sizing:border-box;border:1.5px solid #d0d5dd;border-radius:11px;' +
    'padding:13px 40px 13px 13px;font-size:16px;background:#fff;color:#101828;' +
    'appearance:none;-webkit-appearance:none;cursor:pointer;' +
    "background-image:url(\"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' fill='none' stroke='%23667085' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 8l4 4 4-4'/%3E%3C/svg%3E\");" +
    'background-repeat:no-repeat;background-position:right 12px center}' +
    '.vfi{width:100%;box-sizing:border-box;border:1.5px solid #d0d5dd;border-radius:11px;' +
    'padding:13px;font-size:16px;background:#fff;color:#101828}' +
    '.vfs:focus,.vfi:focus{outline:0;border-color:#50DBF2;box-shadow:0 0 0 3px rgba(80,219,242,.25)}' +
    '.vfs.thieu,.vfi.thieu{border-color:#fda29b;background:#fffbfa}' +
    /* O tai anh: giau input that di, ve mot vung bam de nhin ra la cho tai
       anh. Input that van nam do va van bam duoc, chi la trong suot. */
    '.vfa{position:relative;border:1.5px dashed #d0d5dd;border-radius:11px;background:#fcfcfd;' +
    'padding:16px 13px;text-align:center;cursor:pointer}' +
    '.vfa.thieu{border-color:#fda29b;background:#fffbfa}' +
    '.vfa.xong{border-style:solid;border-color:#a6f4c5;background:#f6fef9}' +
    '.vfa input[type=file]{position:absolute;inset:0;width:100%;height:100%;opacity:0;cursor:pointer}' +
    '.vfa .i{font-size:24px;line-height:1}' +
    '.vfa .t{font-size:14px;font-weight:600;color:#344054;margin-top:5px}' +
    '.vfa .p{font-size:12px;color:#98a2b3;margin-top:2px}' +
    '.vfa.xong .t{color:#027a48}' +
    '.vfanh{max-width:100%;border-radius:9px;margin-top:9px;display:block}' +
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
    /* O tim nghiep vu va o ghim (v565). */
    '.vgbtimw{padding:12px 12px 0}' +
    '.vgbtim{width:100%;box-sizing:border-box;border:1.5px solid #bfe9f6;border-radius:14px;' +
    'padding:13px 14px;font-size:16px;background:#fff;color:#101828;' +
    '-webkit-appearance:none;appearance:none}' +
    '.vgbtim:focus{outline:0;border-color:#50DBF2;box-shadow:0 0 0 3px rgba(80,219,242,.25)}' +
    '.vgbkq{padding:10px 12px 0}' +
    '.vgbkq .hub{background:#fff;border-radius:12px;margin-bottom:8px}' +
    '.vgbtrong{padding:18px 4px;font-size:14px;color:#98a2b3;text-align:center}' +
    /* Nut ghim trong ket qua tim: vung bam rong 40px de ngon tay khong
       cham vao dong ben canh roi mo nham man. */
    /* Vung bam 44 diem, dung AGENTS.md dieu 13 ("nut, chip, dong cao it nhat
       44 diem"). Ban dau dat 40 va Codex bat tren PR #426.

       `display:inline-flex` o day la lop PHONG THU, khong phai lop duy nhat.

       DINH CHINH mot con so em bao sai o vong truoc: em tung bao nut nay do
       that chi 21x19. So do lay tren trang thu CHUA nap CSS nen cua app, nen
       luc do `.hub` khong co `display:flex` va cai span bi tinh la inline
       that. Tren app that, `.hub{display:flex}` lam no thanh flex item va
       trinh duyet tu blockify, nen no van du 44x44 ngay ca khi bo dong nay -
       da do lai de chung minh. Giu dong nay de o nay khong phai dua vao viec
       cha no tinh co la mot flex container.

       Bai hoc that nam o cho khac va van dung: phep do nao chay tren mot
       trang thieu CSS thi no do mot thu khong co that. */
    '.vgbgb{flex:none;display:inline-flex;align-items:center;justify-content:center;' +
    'width:44px;height:44px;text-align:center;' +
    'border-radius:999px;background:#f2f4f7;font-size:17px;opacity:.45;cursor:pointer}' +
    '.vgbgb.on{background:#e4f6fc;opacity:1}' +
    '.vgbghim{background:#fff;border-radius:16px;margin:12px 12px 0;padding:12px 12px 14px;' +
    'box-shadow:0 1px 3px rgba(16,24,40,.08)}' +
    '.vgbgh{display:flex;align-items:center;gap:8px;margin-bottom:10px}' +
    '.vgbgh b{flex:1;font-size:15px;color:#101828}' +
    /* Nut "Sua ghim" / "Xong" cung phai du 44 diem (AGENTS.md dieu 13).
       Codex bat R3-F2 tren PR #429: do that ra 82x28 va 56x28. Lan truoc em
       chi do nut ghim va dau X nen khong thay no - phep do nao bo sot mot nut
       thi no khong chung minh duoc gi ve nut do. Da them ca hai vao
       do_vung_bam_566.js. */
    '.vgbgs{flex:none;display:inline-flex;align-items:center;justify-content:center;' +
    'min-height:44px;font-size:13px;font-weight:700;color:#667085;background:#f2f4f7;' +
    'border-radius:9px;padding:6px 13px;cursor:pointer}' +
    '.vgbgl{display:flex;gap:8px;overflow-x:auto;-webkit-overflow-scrolling:touch}' +
    '.vgbgo{position:relative;flex:0 0 auto;width:88px;background:#f9fafb;border:1px solid #eef0f4;' +
    'border-radius:13px;padding:11px 6px 9px;text-align:center;cursor:pointer}' +
    '.vgbgo:active{transform:scale(.97)}' +
    '.vgbgi{font-size:24px;line-height:1}' +
    /* O "+ Them" cuoi dai ghim va dai moi ghim khi chua ghim gi (v571). */
    '.vgbgthem{flex:0 0 auto;width:88px;min-height:72px;border:1.5px dashed #c7d0dd;' +
    'border-radius:13px;padding:11px 6px 9px;text-align:center;cursor:pointer;color:#667085}' +
    '.vgbgtrong{cursor:pointer}.vgbgtrong .vgbgh{margin-bottom:4px}' +
    '.vgbgthemn{color:#0f766e;background:#e6f6f4}' +
    '.vgbgm{font-size:13px;line-height:1.5;color:#667085}' +
    /* 13 diem la san AGENTS.md dieu 13 ("chu toi thieu 13 diem"); ban dau
       dat 11.5 cho gon o. Hai dong van vua trong o rong 88. */
    '.vgbgn{font-size:13px;font-weight:600;color:#344054;margin-top:6px;line-height:1.25;' +
    'max-height:34px;overflow:hidden}' +
    /* Dau X ve nho cho khoi che mat o, nhung VUNG BAM phai du 44 diem
       (AGENTS.md dieu 13). Noi rong bang mot lop phu trong suot: bam vao lop
       do la trinh duyet tinh nhu bam vao chinh dau X, nen closest() van tim
       ra data-ghim.

       Dau X nam HAN TRONG o chu khong treo ra ngoai mep. Ly do do duoc tren
       Chromium: dai o ghim cuon ngang (`overflow-x:auto`), ma trinh duyet
       bien luon truc doc thanh `overflow-y:auto`, nen phan tran ra ngoai mep
       o bi CAT. Khai 44x44 nhung vung bam do duoc chi 44 ngang va 29 doc.
       Dat top/right 10px thi lop phu trai tu 0 toi 44 trong long o (o rong
       102, cao 86), khong cham mep nao nen khong bi cat. */
    '.vgbgx{position:absolute;top:10px;right:10px;width:24px;height:24px;line-height:24px;' +
    'text-align:center;' +
    'border-radius:999px;background:#d92d20;color:#fff;font-size:13px;font-weight:700;z-index:2}' +
    '.vgbgx::after{content:"";position:absolute;top:-10px;left:-10px;width:44px;height:44px}' +
    /* Ghi chu nho canh ten nhom trong man phan he, kieu "lam hang ngay". */
    '.sec i{font-style:normal;font-weight:600;color:#c3c8d4;text-transform:none;' +
    'letter-spacing:0;margin-left:7px}' +
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
  /* Trang chu chia hai tang: o tim nam ngoai, phan thay doi nam trong #vgbDuoi.

     Vi sao phai tach (Codex bat R2-F3 tren PR #426): danh ba quyen ve muon thi
     ham nay chay lan hai va ghi de ca body, keo theo o nhap. Do duoc: dang go
     "cong no" ra 3 ket qua, danh ba ve xong thi o trong va 0 ket qua - mat
     nguyen thao tac dang lam. Tach ra thi luot sau khong dung toi o nhap, nen
     khong mat chu, khong mat con tro, khong tat ban phim.

     CHI doc dong nguon khi trang chu CHUA duoc gom lan nao.
     Codex bat tren PR #426: tu v565 trang chu con co o ghim va ket qua tim,
     ca hai deu mang [data-go]. Luot gom thu hai (vgbNapKhungCo ve muon) doc
     phai chung va nhan nham lam dong goc, VGB_DONG_GOC tu 23 o con 1 o va
     gan het phan he bien mat. Do duoc tren DOM gia dung mot o ghim: 23 -> 1.
     Co .gwrap nghia la lan gom truoc da ghi de body bang luoi, nen moi
     [data-go] dang co deu la do minh sinh ra, khong phai nguon. */
  var daGom = !!document.getElementById('vgbDuoi');
  var rows = daGom ? [] : body.querySelectorAll('[data-go]');
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
  /* Ba ô còn lại của phân hệ Xuất kho (anh Việt chốt 02/09/2026).

     Trước hôm nay phân hệ chỉ có Xuất huỷ và Điều chuyển, nên bánh cho
     Marketing chụp ảnh phải đi đường Xuất huỷ, và hàng trả nhà cung cấp
     thì không có đường nào cả. Ba ô này để mỗi việc thật đi đúng một
     đường, thay vì mượn tạm cái nút gần giống nhất. */
  VGB_HUB.XKNB = {
    cnt: 0,
    html: vgbODong('XKNB', '🏷️', 'Xuất dùng nội bộ', 'Chụp ảnh, mẫu thử, mời khách, ăn ca')
  };
  /* Chot kho diem ban (anh Viet 16/09/2026). Do tren site that hom do:
     trong mot thang, hang ra khoi hai kho diem ban chi co 18 dong va ca 18
     deu la dieu chuyen. Bao bi, cong cu dung cu, nguyen lieu deu khong co
     duong ra, nen khoang 320 trieu treo lai trong ton kho. */
  VGB_HUB.XKPV = {
    cnt: 0,
    html: vgbODong('XKPV', '🧾', 'Xuất kho phục vụ bán hàng', 'Chốt bao bì, dụng cụ, nguyên liệu đã dùng')
  };
  VGB_HUB.XKTRA = {
    cnt: 0,
    html: vgbODong('XKTRA', '↩️', 'Xuất trả nhà cung cấp', 'Hàng lỗi trả về, giảm luôn công nợ')
  };
  /* Loi tat sang danh sach Thanh toan noi bo ngay trong phan he Ke toan
     (anh Viet 17/09/2026). O 'Thanh toan noi bo' van nam o Dat hang cho
     nguoi lap phieu; ke toan duyet va chi thi mo tu day cho gan tay, khong
     phai vong sang phan he khac. Cung mot man scrTTNB, chi them cua vao.
     Codex bat tren PR #345: gan o nay vo dieu kien la nhom Ke toan hien
     ca voi thu ngan (scrHome co y giau nhom do bang coQuyenKeToan), nen
     chi gan khi dung nguoi. */
  if (coQuyenKeToan()) {
    VGB_HUB.DSTTNB = {
      cnt: 0,
      html: vgbODong('DSTTNB', '🧾', 'Danh sách thanh toán nội bộ', 'Mọi phiếu ứng tiền và đề nghị chi, lọc theo trạng thái')
    };
  }
  VGB_HUB.XKSI = {
    cnt: 0,
    html: vgbODong('XKSI', '🚚', 'Xuất bán sỉ', 'Phiếu giao hàng cho khách sỉ và doanh nghiệp')
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

  /* Hai o rieng vao VGB_HUB de o tim va o ghim thay chung. Danh dau `rieng`
     de vong gom ben duoi khong keo chung vao phan he Cai dat. */
  for (var ri = 0; ri < VGB_O_RIENG.length; ri++) {
    var rx = VGB_O_RIENG[ri];
    VGB_HUB[rx.k] = {
      cnt: 0, rieng: 1, ten: rx.ten, mo: rx.mo, ic: rx.ic,
      html: vgbODong(rx.k, rx.ic, rx.ten, rx.mo)
    };
  }

  var daXep = {};
  for (var a = 0; a < VGB_NHOM.length; a++) {
    for (var c = 0; c < VGB_NHOM[a].keys.length; c++) daXep[VGB_NHOM[a].keys[c]] = 1;
  }
  var khac = VGB_NHOM[VGB_NHOM.length - 1];
  for (var kk in VGB_HUB) {
    if (VGB_HUB[kk] && VGB_HUB[kk].rieng) continue;
    if (!daXep[kk] && khac.keys.indexOf(kk) < 0) khac.keys.push(kk);
  }

  /* O "Viec can lam" PHAI deo con so, y het moi o khac.

     Anh Viet 27/08/2026: ke toan gui ba ho so thanh toan len cho giam doc
     duyet, tren app cua anh "chang co gi de duyet ca". Ba ho so nam dung
     buoc, quyen dung, may chu tra ve du. Nhung o nay la o DUY NHAT tren
     trang chu khong co con so, nen nhin vao tuong la khong co viec, va
     nguoi ta di sang man "Duyet phieu chi" - man do doc mot loai chung tu
     khac han nen no rong that.

     Con so lay tu may chu, GOM SAU khi ve xong luoi, de trang chu khong
     phai cho. Chua ve xong thi o van bam duoc nhu cu. */
  /* Doc ten tung o NGAY TRUOC khi ve: o tim doc danh ba tu day, va danh ba
     phai co du moi o ma nguoi nay dung duoc, ke ca cac o may chu vua tra
     quyen o luot gom thu hai. */
  vgbDocNhanHub();

  var g = '<div id="vgbKQ" class="vgbkq" style="display:none"></div>' +
    '<div id="vgbGhimW"></div>' +
    '<div class="gwrap">' +
    '<div class="gt vcl" data-nhom="VCL">' +
    '<span class="gb" id="vgbSoVCL" style="display:none"></span>' +
    '<div class="gi">' + VGB_O_RIENG[0].ic + '</div>' +
    '<div><div class="gn">' + h(VGB_O_RIENG[0].ten) + '</div>' +
    '<div class="gs">' + h(VGB_O_RIENG[0].mo) + '</div></div></div>';
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
  /* O So tay (v554, anh Viet 02/10/2026: "lam nut so tay trong app"). Dung
     rieng nhu o Viec can lam, KHONG thuoc phan he nao, de ai mo app cung
     thay va bam mot lan la vao thang, khong qua man phan he trung gian. */
  g += '<div class="gt" data-nhom="SOTAY">' +
    '<div class="gi">' + VGB_O_RIENG[1].ic + '</div>' +
    '<div><div class="gn">' + h(VGB_O_RIENG[1].ten) + '</div>' +
    '<div class="gs">' + h(VGB_O_RIENG[1].mo) + '</div></div></div>';
  g += '</div>';
  if (daGom) {
    /* Chi thay phan duoi. O nhap va moi thu dinh toi no giu nguyen. */
    document.getElementById('vgbDuoi').innerHTML = g;
  } else {
    body.innerHTML = '<div class="vgbtimw">' +
      '<input id="vgbTim" class="vgbtim" type="search" autocomplete="off" ' +
      'placeholder="T\u00ecm nghi\u1ec7p v\u1ee5: c\u00f4ng n\u1ee3, ki\u1ec3m k\u00ea, ph\u00ed app...">' +
      '</div><div id="vgbDuoi">' + g + '</div>';
    var oTim = document.getElementById('vgbTim');
    if (oTim) {
      oTim.oninput = function () { vgbVeTim(oTim.value); };
      /* Ban su kien 'search' la luc nguoi dung bam dau X trong o type=search.
         Khong nghe cai nay thi bam X xoa chu ma ket qua cu van dinh tren man. */
      oTim.onsearch = function () { vgbVeTim(oTim.value); };
    }
  }
  vgbVeGhim();
  /* Dang go do thi ve lai ket qua theo danh ba MOI, chu khong de ket qua cu
     nam do. Khong dung toi o nhap.

     CO MOT LOP THU HAI lam cung viec nay: vgbNapGhim goi vgbVeLaiGhim, ma ham
     do cung ve lai ket qua tim. Dot bien chi go mot trong hai thi bo kiem van
     xanh (CLAUDE.md dieu 17c), go het ca hai thi do. Giu ca hai la co y:
     duong trong vgbNapGhim chay sau mot nhip (bat dong bo), nen co mot
     khoanh khac ket qua trong neu chi dua vao no. */
  var oDangGo = document.getElementById('vgbTim');
  if (oDangGo && oDangGo.value) vgbVeTim(oDangGo.value);
  body.onclick = function (e) {
    /* Nut ghim va bo ghim phai doc TRUOC data-go: o ghim nam trong mot the
       co data-go, bam vao dau X ma doc data-go truoc thi no mo man thay vi
       bo ghim. */
    var gh = e.target.closest('[data-ghim]');
    if (gh) return vgbBatGhim(gh.dataset.ghim);
    var sg = e.target.closest('[data-suaghim]');
    if (sg) { VGB_SUA_GHIM = !VGB_SUA_GHIM; return vgbVeGhim(); }
    if (e.target.closest('[data-themghim]')) return vgbChonGhim();
    var r = e.target.closest('[data-go]');
    if (r) return vgbGo(r.dataset.go);
    var t = e.target.closest('[data-nhom]');
    if (!t) return;
    var nh = null;
    for (var i = 0; i < VGB_NHOM.length; i++) if (VGB_NHOM[i].k === t.dataset.nhom) nh = VGB_NHOM[i];
    /* Di qua vgbGo chu khong go() thang: vgbGo la CUA DUY NHAT dat dia
       chi. Bo qua cua nay dung mot lan la o lon mat dia chi, va do dung la
       loi anh Viet bao ngay 24/08 voi phan he Ke toan. */
    if (t.dataset.nhom === 'VCL') return vgbGo('VCL');
    if (t.dataset.nhom === 'SOTAY') return vgbGo('SOTAY');
    if (nh) vgbGo('PH:' + nh.k);
  };
  vgbDemVCL();
  /* Don ghim NGAY SAU khi doc xong: danh ba quyen vua ve co the da bo mot vai
     o ma nguoi ta tung ghim. */
  vgbNapGhim().then(vgbDonGhim);
}

/* ---------- Ve o tim va o ghim (v565) ----------

   Ba ham duoi day chi lo viec VE. Phan quyet dinh (tim gi, ghim duoc khong)
   nam o bon ham thuan phia tren, de kiem thu chot luat o day ma khong phai
   dung ca man hinh. */

/* Danh sach ghim cua nguoi dang dang nhap. null nghia la CHUA hoi may chu
   lan nao; mang rong nghia la da hoi va nguoi nay chua ghim gi. Phan biet hai
   cai de khong hoi lai may chu moi lan ve lai trang chu. */
var VGB_GHIM = null;
var VGB_SUA_GHIM = false;
/* Loi hua doc ghim, dung chung cho moi luot gom: hai luot gom chong nhau cung
   chi hoi may chu MOT lan. */
var VGB_GHIM_NAP = null;
/* Loc ghim theo quyen, nhung CHI khi danh ba quyen da biet.

   Codex bat R2-F2 tren PR #426: danh ba chua ve thi cac o Danh muc tam co
   trong VGB_HUB. Loc luc do la dung; nhung neu danh ba HONG (mang loi) ma van
   loc thi la xoa ghim cua nguoi ta chi vi mang cham. VGB_KHUNG_CO con null
   nghia la CHUA BIET, khac han voi biet va tra ve rong. */
function vgbLocGhim(ds) {
  return vgbChuanGhim(ds, VGB_KHUNG_CO ? function (k) { return !!VGB_HUB[k]; } : null);
}

/* Bo khoi danh sach ghim nhung o nguoi nay THAT SU khong con quyen xem.

   Do duoc tren DOM gia: ghim 5 o Danh muc roi danh ba tra ve rong thi 5 o do
   bien mat khoi man nhung van chiem du 5 cho, bam ghim o moi chi nhan duoc
   cau "Chi ghim duoc 5 nghiep vu, bo mot o cu roi ghim lai" trong khi khong
   con o cu nao de bo. */
function vgbDonGhim() {
  if (!VGB_GHIM || !VGB_KHUNG_CO) return;
  var con = vgbLocGhim(VGB_GHIM);
  if (con.length === VGB_GHIM.length) return;
  VGB_GHIM = con;
  vgbVeLaiGhim();
  vgbCatGhim(VGB_GHIM);
}

function vgbVeTim(tu) {
  var kq = document.getElementById('vgbKQ');
  if (!kq) return;
  var luoi = document.querySelector('.gwrap');
  var gw = document.getElementById('vgbGhimW');
  var co = vgbBoDau(tu).trim().length >= 2;
  /* Dang go thi an luoi o lon va khoi ghim di, de ket qua nam ngay duoi o
     go chu khong phai cuon qua het trang chu moi thay. */
  kq.style.display = co ? '' : 'none';
  if (luoi) luoi.style.display = co ? 'none' : '';
  if (gw) gw.style.display = co ? 'none' : '';
  if (!co) { kq.innerHTML = ''; return; }
  var ds = vgbTimNghiepVu(tu, vgbDanhBaNghiepVu());
  if (!ds.length) {
    kq.innerHTML = '<div class="vgbtrong">Kh\u00f4ng c\u00f3 nghi\u1ec7p v\u1ee5 n\u00e0o kh\u1edbp v\u1edbi t\u1eeb n\u00e0y.</div>';
    return;
  }
  var r = '', gh = VGB_GHIM || [];
  for (var i = 0; i < ds.length && i < 30; i++) {
    var x = ds[i];
    var da = gh.indexOf(x.k) >= 0;
    /* data-go dat o CA DONG chu khong rieng khoi chu: bam vao bieu tuong
       cung phai mo man, khong thi nguoi dung bam trung vao bieu tuong roi
       tuong nut chet. Nut ghim nam ngoai, va duoc doc truoc trong onclick. */
    r += '<div class="hub vgbkqd" data-go="' + h(x.k) + '">' +
      '<div class="hi">' + ((VGB_HUB[x.k] && VGB_HUB[x.k].ic) || '\u25b8') + '</div>' +
      '<div class="ht">' +
      '<div class="h1">' + h(x.ten) + '</div>' +
      '<div class="h2">' + h(x.phanHe) + (x.mo ? ' \u00b7 ' + h(x.mo) : '') + '</div></div>' +
      '<span class="vgbgb' + (da ? ' on' : '') + '" data-ghim="' + h(x.k) + '">\ud83d\udccc</span>' +
      '</div>';
  }
  kq.innerHTML = r;
}

/* Ve lai MOI cho co nut ghim: khoi ghim va ca ket qua tim dang mo.

   Mot ham duy nhat chu khong di goi tung cho (CLAUDE.md dieu 18). Codex bat
   tren PR #426: vgbNapGhim truoc day chi ve lai khoi ghim, nen ai go o tim
   TRUOC khi may chu tra ve se thay nut ghim o trang thai tat du da ghim, bam
   vao la BO ghim. Do duoc tren DOM gia: ghim ['CNPT'], go "cong no", bam nut
   -> VGB_GHIM thanh []. */
function vgbVeLaiGhim() {
  vgbVeGhim();
  var oTim = document.getElementById('vgbTim');
  if (oTim && oTim.value) vgbVeTim(oTim.value);
}

function vgbVeGhim() {
  var w = document.getElementById('vgbGhimW');
  if (!w) return;
  /* CHUA doc duoc danh sach (null: dang hoi hoac may chu hong) thi khong ve
     gi: khong biet nguoi nay ghim gi thi khong moi ho ghim them. */
  if (!VGB_GHIM) { w.innerHTML = ''; return; }
  var ds = VGB_GHIM;
  /* Da doc va CHUA ghim gi: hien mot dai mong moi ghim, KHONG an han.

     Ban v565 an han khoi nay cho gon (mockup 03/10/2026). Do tren site that
     04/10/2026: khong mot tai khoan nao ghim duoc o nao, vi loi ghim duy
     nhat nam trong ket qua o tim, ma o tim thi khong ai biet la co nut ghim.
     Anh Viet hoi lai "sao khong thay bang ghim app hay dung?". Nen giu mot
     dai mot dong, bam vao la mo hop chon nghiep vu de ghim. */
  if (!ds.length) {
    VGB_SUA_GHIM = false;
    w.innerHTML = '<div class="vgbghim vgbgtrong" data-themghim="1">' +
      '<div class="vgbgh"><b>\ud83d\udccc Ghim nghi\u1ec7p v\u1ee5 hay d\u00f9ng</b>' +
      '<span class="vgbgs vgbgthemn">+ Ch\u1ecdn \u00f4 \u0111\u1ec3 ghim</span></div>' +
      '<div class="vgbgm">Ghim t\u1ed1i \u0111a ' + VGB_GHIM_TOI_DA +
      ' \u00f4 b\u1ea1n hay m\u1edf l\u00ean \u0111\u1ea7u trang ch\u1ee7. ' +
      'C\u0169ng ghim \u0111\u01b0\u1ee3c b\u1eb1ng n\u00fat \ud83d\udccc trong k\u1ebft qu\u1ea3 \u00f4 t\u00ecm.</div></div>';
    return;
  }
  var o = '';
  for (var i = 0; i < ds.length; i++) {
    var x = VGB_HUB[ds[i]];
    if (!x) continue;
    o += '<div class="vgbgo"' + (VGB_SUA_GHIM ? '' : ' data-go="' + h(ds[i]) + '"') + '>' +
      (VGB_SUA_GHIM ? '<span class="vgbgx" data-ghim="' + h(ds[i]) + '">\u2715</span>' : '') +
      '<div class="vgbgi">' + (x.ic || '\ud83d\udccc') + '</div>' +
      '<div class="vgbgn">' + h(x.ten) + '</div></div>';
  }
  /* Con cho trong thi de mot o "+ Them" cuoi dai, de ghim them khong phai
     di vong qua o tim. Dang sua ghim thi an di cho khoi bam nham. */
  /* Codex #437 vong 10: dem theo o CON QUYEN khi danh ba da biet, de mot o
     mat quyen chua kip go khong an mat o "+ Them". */
  if (!VGB_SUA_GHIM && (VGB_KHUNG_CO ? vgbLocGhim(ds).length : ds.length) < VGB_GHIM_TOI_DA) {
    o += '<div class="vgbgthem" data-themghim="1"><div class="vgbgi">\uff0b</div>' +
      '<div class="vgbgn">Th\u00eam</div></div>';
  }
  w.innerHTML = '<div class="vgbghim"><div class="vgbgh">' +
    '<b>\ud83d\udccc Ghim nghi\u1ec7p v\u1ee5 hay d\u00f9ng</b>' +
    '<span class="vgbgs" data-suaghim="1">' +
    (VGB_SUA_GHIM ? 'Xong' : 'S\u1eeda ghim') + '</span></div>' +
    '<div class="vgbgl">' + o + '</div></div>';
}

/* Hoi may chu danh sach ghim. Hong thi IM LANG: mot loi doc o ghim khong
   duoc lam vo trang chu cua ca quan, va trang chu khong co o ghim van dung
   duoc het. */
function vgbNapGhim() {
  if (VGB_GHIM) { vgbVeLaiGhim(); return Promise.resolve(VGB_GHIM); }
  if (!VGB_GHIM_NAP) {
    VGB_GHIM_NAP = api('vagabond.ghim.lay', {}).then(function (kq) {
      VGB_GHIM = vgbLocGhim((kq && kq.ghim) || []);
      return VGB_GHIM;
    }, function () {
      /* Doc hong thi BO loi hua di, khong giu lai.
         Codex bat R3-F1 tren PR #429: ban cu giu lai loi hua da hong, nen moi
         lan mo lai trang chu va moi lan bam ghim deu dung lai dung ket qua
         hong do ma khong he hoi may chu nua. Do duoc: lan doc dau reject,
         sau do mang da tot tro lai nhung van readCalls=1, pins=null,
         saves=[]. Nghia la cau "Mo lai trang chu roi thu lai" ma chinh minh
         hien ra cho nguoi dung LA LOI NOI SUONG - khong co duong nao hoi lai
         tru khi tai lai ca app.
         Bo di thi lan sau hoi lai; con trong LUC dang hoi, loi hua van nam
         day nen nhieu luot gom chong nhau van chi hoi mot lan. */
      VGB_GHIM_NAP = null;
      return null;
    });
  }
  return VGB_GHIM_NAP.then(function (ds) {
    if (ds && S.stack[S.stack.length - 1] === scrHome) vgbVeLaiGhim();
    return ds;
  });
}

/* Cat ghim len may chu, NOI TIEP nhau chu khong song song.

   Codex bat tren PR #426: moi lan bam truoc day goi api ngay, nen bam hai o
   lien tiep la hai loi goi chay song song va co the ve nguoc thu tu. Do duoc
   tren DOM gia voi lan dau cham 60ms, lan sau 10ms: may chu giu lai ["POS"]
   trong khi man hien ["POS","CNPT"], mo app lan sau la mat o vua ghim.

   Cach gom: moi lan cat lay mot so thu tu. Lan nao da bi lan sau vuot mat thi
   KHONG gui nua - trang thai sau cung la cai duy nhat dang gui, va no luon
   duoc gui sau cung vi ca day noi tiep nhau. */
var VGB_GHIM_LUOT = 0;
var VGB_GHIM_DAY = null;

function vgbCatGhim(ds) {
  var luot = ++VGB_GHIM_LUOT;
  var chuoi = (VGB_GHIM_DAY || Promise.resolve()).then(function () {
    if (luot !== VGB_GHIM_LUOT) return;
    return api('vagabond.ghim.luu', { ghim: JSON.stringify(ds) }).catch(function () {
      toast('Ch\u01b0a c\u1ea5t \u0111\u01b0\u1ee3c ghim l\u00ean m\u00e1y ch\u1ee7. ' +
        'L\u1ea7n sau m\u1edf app s\u1ebd v\u1ec1 nh\u01b0 c\u0169.', 3800);
    });
  });
  VGB_GHIM_DAY = chuoi;
  return chuoi;
}

/* Bat tat ghim mot nghiep vu.

   Ve TRUOC roi cat sau: nguoi dung bam phai thay ngay, khong doi mang. Cat
   hong thi noi ro la lan sau mo app se ve nhu cu, chu khong im lang de ho
   tuong da ghim xong. */
async function vgbBatGhim(k) {
  /* CHUA doc xong danh sach cu thi CHO doc xong da.

     Codex bat R2-F1 tren PR #426: truoc day `(VGB_GHIM || [])` coi "chua doc"
     la "chua ghim gi", nen bam mot o luc dang cho se cat len may chu dung mot
     o do va XOA sach ghim cu. Do duoc: ghim san ["CNPT"], bam POS truoc khi
     doc ve -> may chu giu ["POS"] con man hien ["CNPT"].

     Doc hong thi KHONG ghi gi ca. Ghi de bang mot danh sach minh khong biet
     la cach mat du lieu nhanh nhat.

     Buoc cho nay la lop DUY NHAT giu viec do, khong co lop thu hai do phia
     sau. Ban dau con mot co "nguoi dung da sua" trong vgbNapGhim, nhung do
     dot bien thay no khong lam do ca nao va truy ra thi khong con duong nao
     chay vao no: ai bam ghim cung phai qua buoc cho nay truoc. Da go di cho
     khoi de lai mot nhanh chet (CLAUDE.md dieu 17c). */
  if (!VGB_GHIM) {
    await vgbNapGhim();
    if (!VGB_GHIM) {
      return toast('Ch\u01b0a \u0111\u1ecdc \u0111\u01b0\u1ee3c danh s\u00e1ch ghim ' +
        't\u1eeb m\u00e1y ch\u1ee7. M\u1edf l\u1ea1i trang ch\u1ee7 r\u1ed3i th\u1eed l\u1ea1i.', 3600);
    }
  }
  /* Don truoc khi tinh tran: o da mat quyen khong duoc chiem cho vo hinh. */
  vgbDonGhim();
  var ds = (VGB_GHIM || []).slice();
  var i = ds.indexOf(k);
  if (i >= 0) ds.splice(i, 1);
  else if (ds.length >= VGB_GHIM_TOI_DA) {
    return toast('Ch\u1ec9 ghim \u0111\u01b0\u1ee3c ' + VGB_GHIM_TOI_DA +
      ' nghi\u1ec7p v\u1ee5. B\u1ecf m\u1ed9t \u00f4 c\u0169 r\u1ed3i ghim l\u1ea1i.', 3400);
  } else ds.push(k);
  VGB_GHIM = vgbLocGhim(ds);
  vgbVeLaiGhim();
  await vgbCatGhim(VGB_GHIM);
}

/* Mo hop chon de ghim them mot nghiep vu (v571).

   Lay DUNG danh ba ma o tim dang dung (vgbDanhBaNghiepVu), nen o nao nguoi
   nay khong co quyen thi cung khong hien de ghim. Bo nhung o da ghim roi.
   Chon xong di qua vgbBatGhim, cua duy nhat doi danh sach ghim, de moi luat
   (cho doc xong, tran 5 o, cat noi tiep) chi nam o mot cho. */
async function vgbChonGhim() {
  if (!VGB_GHIM) {
    await vgbNapGhim();
    if (!VGB_GHIM) {
      return toast('Ch\u01b0a \u0111\u1ecdc \u0111\u01b0\u1ee3c danh s\u00e1ch ghim ' +
        't\u1eeb m\u00e1y ch\u1ee7. M\u1edf l\u1ea1i trang ch\u1ee7 r\u1ed3i th\u1eed l\u1ea1i.', 3600);
    }
  }
  /* Go o mat quyen TRUOC khi tinh cho trong (Codex #437 vong 10), cung mot
     phep voi vgbBatGhim. */
  vgbDonGhim();
  var con = VGB_GHIM_TOI_DA - VGB_GHIM.length;
  if (con <= 0) {
    return toast('Ch\u1ec9 ghim \u0111\u01b0\u1ee3c ' + VGB_GHIM_TOI_DA +
      ' nghi\u1ec7p v\u1ee5. B\u1ecf m\u1ed9t \u00f4 c\u0169 r\u1ed3i ghim l\u1ea1i.', 3400);
  }
  var ds = vgbDanhBaNghiepVu().filter(function (x) { return VGB_GHIM.indexOf(x.k) < 0; });
  var k = await hoiChon('Ghim nghi\u1ec7p v\u1ee5 hay d\u00f9ng',
    'Ch\u1ecdn m\u1ed9t \u00f4 \u0111\u1ec3 ghim l\u00ean \u0111\u1ea7u trang ch\u1ee7. C\u00f2n ghim \u0111\u01b0\u1ee3c ' + con + ' \u00f4.',
    ds.map(function (x) {
      return { k: x.k, nhan: x.ten, mo_ta: x.phanHe + (x.mo ? ' \u00b7 ' + x.mo : ''),
        icon: (VGB_HUB[x.k] && VGB_HUB[x.k].ic) || '' };
    }), null);
  if (!k) return;
  return vgbBatGhim(k);
}

/* Hoi may chu xem nguoi nay con bao nhieu viec, roi deo len o.

   Hong thi IM LANG. O khong deo so van dung nhu truoc, con hien mot loi do
   giua trang chu vi mot con so phu thi lam ca man xau di. */
async function vgbDemVCL() {
  /* #398 vong 4: Viec can lam di cong chung (bep, kho, thu mua cung co), nen
     hoi co cong_chung, khong hoi co ban_hang da thu hep. */
  if (!nenCoQuyen('cong_chung')) return;
  var o = document.getElementById('vgbSoVCL');
  if (!o) return;
  try {
    var kq = await api('vagabond.viec_can_lam.dem', {});
    var n = (kq && kq.tong) || 0;
    if (!n) return;
    o.textContent = n > 99 ? '99+' : String(n);
    o.style.display = '';
  } catch (e) { }
}

/* ---------- Việc cần làm ----------

Anh Việt 20/08/2026: *"Hiện tại màn hình này đang hiển thị sai đối tượng (Kế
toán đang phải nhìn thấy cả Phiếu nhập kho của Bếp/Kho)."*

Bản cũ gom việc ngay tại đây bằng một loạt lời gọi getList, và dòng lấy Phiếu
nhập kho không có một điều kiện vai nào cả. Nay toàn bộ việc gom và lọc nằm ở
máy chủ trong `vagabond/viec_can_lam.py`, màn này chỉ vẽ lại: lọc theo vai mà
đặt ở máy khách thì sửa vài dòng trong trình duyệt là xem được việc người
khác. */
var vclLoc = { loai: '', trang_thai: '' };

async function scrVclList() {
  vgbCss();
  frame('Việc cần làm', '<div class="emp"><div class="e1">⏳</div><div class="e2">Đang gom việc của bạn...</div></div>');
  var kq;
  try { kq = await api('vagabond.viec_can_lam.danh_sach', vclLoc); }
  catch (e) {
    frame('Việc cần làm', '<div class="emp"><div class="e1">⚠️</div><div class="e2">' +
      h((e && e.message) || 'Không gom được việc') + '</div></div>');
    return;
  }
  vclVe(kq);
}

function vclVe(kq) {
  var ds = kq.ds || [], dl = kq.dem_loai || {}, dt = kq.dem_trang_thai || {};
  var body = '';

  body += '<div style="padding:13px 14px 4px;font-size:13px;color:#8a90a0">' +
    (kq.tong ? 'Đang chờ bạn xử lý <b>' + kq.tong + '</b> việc' : 'Không có việc nào đang chờ bạn') +
    (kq.so_dich_danh ? ', trong đó <b>' + kq.so_dich_danh + '</b> giao đích danh cho bạn' : '') +
    ' · vai <b>' + h(kq.vai_chinh || '') + '</b></div>';

  /* Chip loại phiếu. Chỉ bày loại người này ĐƯỢC THẤY và ĐANG CÓ việc: bày
     ra chip rồi bấm vào không có gì là một cách nói dối nhẹ nhàng. */
  var cl = kq.chip_loai || [];
  if (cl.length) {
    body += '<div style="display:flex;gap:7px;overflow-x:auto;padding:6px 12px 8px">' +
      '<button class="vclL" data-l="" style="flex:none;border:1.5px solid ' +
      (!vclLoc.loai ? '#0f766e' : '#e5e7eb') + ';background:' + (!vclLoc.loai ? '#ccfbf1' : '#fff') +
      ';color:' + (!vclLoc.loai ? '#0f766e' : '#374151') + ';border-radius:999px;padding:6px 13px;' +
      'font-size:12.5px;font-weight:' + (!vclLoc.loai ? '800' : '600') + ';white-space:nowrap">Tất cả · ' +
      (kq.tong || 0) + '</button>' +
      cl.map(function (c) {
        var on = vclLoc.loai === c.k;
        return '<button class="vclL" data-l="' + h(c.k) + '" style="flex:none;border:1.5px solid ' +
          (on ? '#0f766e' : '#e5e7eb') + ';background:' + (on ? '#ccfbf1' : '#fff') + ';color:' +
          (on ? '#0f766e' : '#374151') + ';border-radius:999px;padding:6px 13px;font-size:12.5px;' +
          'font-weight:' + (on ? '800' : '600') + ';white-space:nowrap">' + c.ic + ' ' + h(c.ten) +
          ' · ' + (dl[c.k] || 0) + '</button>';
      }).join('') + '</div>';
  }

  /* Chip trạng thái, đúng theo loại đang chọn. */
  var ct = kq.chip_trang_thai || [];
  if (ct.length > 1) {
    body += '<div style="display:flex;gap:7px;overflow-x:auto;padding:0 12px 8px">' +
      '<button class="vclT" data-t="" style="flex:none;border:1px solid ' +
      (!vclLoc.trang_thai ? '#0f766e' : '#e5e7eb') + ';background:' +
      (!vclLoc.trang_thai ? '#f0fdfa' : '#fff') + ';color:' +
      (!vclLoc.trang_thai ? '#0f766e' : '#6b7280') + ';border-radius:999px;padding:5px 12px;' +
      'font-size:12px;font-weight:' + (!vclLoc.trang_thai ? '800' : '600') + ';white-space:nowrap">Mọi trạng thái</button>' +
      ct.map(function (c) {
        var on = vclLoc.trang_thai === c.k;
        return '<button class="vclT" data-t="' + h(c.k) + '" style="flex:none;border:1px solid ' +
          (on ? '#0f766e' : '#e5e7eb') + ';background:' + (on ? '#f0fdfa' : '#fff') + ';color:' +
          (on ? '#0f766e' : '#6b7280') + ';border-radius:999px;padding:5px 12px;font-size:12px;' +
          'font-weight:' + (on ? '800' : '600') + ';white-space:nowrap">' + h(c.ten) +
          ' · ' + (dt[c.k] || 0) + '</button>';
      }).join('') + '</div>';
  }

  if (!ds.length) {
    body += '<div class="emp"><div class="e1">🎉</div><div class="e2">' +
      (vclLoc.loai || vclLoc.trang_thai ? 'Không có việc nào trong nhóm đang lọc' : 'Không có việc nào đang chờ bạn') +
      '</div></div>';
  } else {
    var nhoms = [];
    ds.forEach(function (x) { if (nhoms.indexOf(x.nhom) < 0) nhoms.push(x.nhom); });
    nhoms.forEach(function (n) {
      body += '<div class="sec">' + h(n) + '</div>';
      ds.forEach(function (x, i) {
        if (x.nhom !== n) return;
        body += '<div data-v="' + i + '" style="background:#fff;border-radius:16px;margin:8px 12px;padding:13px 15px;' +
          'display:flex;align-items:center;gap:12px;box-shadow:0 1px 3px rgba(16,24,40,.07)">' +
          '<div style="font-size:22px">' + (vclIcon(x.loai) || '📄') + '</div>' +
          '<div style="flex:1;min-width:0"><div style="font-weight:700;font-size:15px">' + h(x.ma) +
          /* Dấu này chỉ hiện khi máy đã GIAO đích danh phiếu cho người đang
             xem. Việc của bộ phận và việc giao cho mình là hai chuyện, và
             lẫn hai chuyện đó là cách một phiếu nằm ba ngày không ai nhận. */
          (x.cua_toi ? ' <span style="background:#0f766e;color:#fff;font-size:10.5px;font-weight:800;' +
            'border-radius:6px;padding:2px 6px;vertical-align:2px">GIAO BẠN</span>' : '') + '</div>' +
          '<div style="font-size:12.5px;color:#8a90a0;margin-top:2px">' + h(x.phu || '') +
          (x.ngay ? ' · ' + dmy(x.ngay) : '') +
          (x.tien ? ' · ' + money(x.tien) + ' đ' : '') + '</div></div>' +
          '<span style="padding:3px 10px;border-radius:11px;font-size:11.5px;font-weight:700;color:#fff;' +
          'white-space:nowrap;background:' + x.mau + '">' + h(x.nhan_tt) + '</span></div>';
      });
    });
  }

  var b = frame('Việc cần làm', body);
  b.querySelectorAll('.vclL').forEach(function (n) {
    n.onclick = function () {
      vclLoc.loai = n.getAttribute('data-l');
      vclLoc.trang_thai = '';
      go(scrVclList, true);
    };
  });
  b.querySelectorAll('.vclT').forEach(function (n) {
    n.onclick = function () { vclLoc.trang_thai = n.getAttribute('data-t'); go(scrVclList, true); };
  });
  b.onclick = function (e) {
    var el = e.target.closest('[data-v]');
    if (!el) return;
    vclMo(ds[+el.dataset.v]);
  };
}

function vclIcon(l) {
  return {
    chuyen_kho: '📦', san_xuat: '🎂', nhap_kho: '📥', xuat_kho: '📤',
    kiem_ke: '🧮', sai_kho: '⚠️', ycmh: '🛒', de_nghi_chi: '🧾', hoan_tien: '💸',
    ho_so_tt: '🏦', don_mua: '⚠️', tang_qua: '🎁',
    nop_quy: '💵', hang_tang: '🎁', goi_y: '📌'
  }[l] || '';
}

/* Dong viec nay la phieu chi (Payment Entry) hay ho so thanh toan? THUAN.

   Doc o `phieu_chi` may chu gui xuong truoc. Neu vi ly do gi do o ay khong
   co, van con duong nhan dang thu hai: ma Ho so TT luon dung dau CHAM
   (APP.26.08.027) vi doctype do tu sinh ma, con Payment Entry di theo bo ma
   cua ERPNext nen dung dau GACH (APP-26-08-534). Hai duong doc lap nhau, mat
   mot van con mot, de khong bao gio quay lai canh bam vao thi bao khong tim
   thay. */
function vclLaPhieuChi(x) {
  if (!x) return false;
  if (x.phieu_chi) return true;
  var ma = String(x.ma || '');
  return ma.indexOf('-') >= 0 && ma.indexOf('.') < 0;
}

/* Bấm vào một việc thì mở đúng màn của loại đó. */
function vclMo(x) {
  if (!x) return;
  var l = x.loai;
  if (l === 'chuyen_kho') return go(function () { scrMRView(x.ma, typeOf('Material Transfer')); });
  if (l === 'san_xuat') return go(function () { scrMRView(x.ma, typeOf('Manufacture')); });
  if (l === 'nhap_kho') return go(function () { scrRecvDoc(x.ma); });
  if (l === 'xuat_kho') return go(function () { scrXkView(x.ma); });
  if (l === 'kiem_ke') return go(scrKkList);
  /* v512 y 4: hang nam sai kho mo thang man Ton kho theo chang, loc chip Sai kho. */
  if (l === 'sai_kho') return go(function () { tch.chang = 'sai_kho'; tch.tim = x.ma || ''; tch.d = null; return scrTonChang(); });
  if (l === 'de_nghi_chi') return ttnbCt(x.ma);
  if (l === 'hoan_tien') return htChiTiet(x.ma);
  /* Ba nhanh them 25/08/2026, deu la viec DA CO man tren app ma man Viec
     can lam van day nguoi ta sang may tinh:
       tang_qua   may chu da sinh viec tu v305 nhung chua co duong mo
       ycmh       da co scrDuyetYcXem tu lau
       ho_so_tt   da co scrHoSoTTView tu lau
     Mo phieu tang qua theo dung cach man CRM tu mo: dat tq.form roi go. */
  if (l === 'tang_qua') return go(function () { tq.form = { ma: x.ma }; return scrTqSua(); });
  if (l === 'ycmh') return go(function () { scrDuyetYcXem(x.ma); });
  /* Hai duong khac nhau duoi cung mot nhan.
     Dong co co phieu_chi la mot PAYMENT ENTRY tra truoc NCC (ten dang
     APP-26-08-534, dau gach), khong phai mot Ho so TT (APP.26.08.027, dau
     cham). Mo bang man Ho so TT thi may chu bao "Khong tim thay Vagabond Ho
     So TT ...". Man Ho so thanh toan da chia dung tu v408 bang o data-hspc,
     man nay tra no not. */
  if (l === 'ho_so_tt') return go(function () { vclLaPhieuChi(x) ? scrPayView(x.ma) : scrHoSoTTView(x.ma); });
  /* Hai nhanh them 31/08/2026 cho che do giam doc: hai anh chi con thay ba
     loai viec he trong, nen ba loai do bat buoc phai bam mo duoc ngay tren
     app. Man Viec can lam ma day nguoi ta sang may tinh thi coi nhu khong
     co man. */
  if (l === 'nop_quy') return go(function () { nqXem = x.ma; return scrNopQuyXem(); });
  /* Chi loc san o tim ve dung don do, KHONG mo san phan chi tiet: phan do
     doc chi tiet bang mot loi goi rieng luc nguoi ta bam vao, mo san ma
     chua goi thi no dung mai o cau "Dang doc tung mon". */
  if (l === 'hang_tang') return go(function () {
    dtgChang = ''; dtgKy = ''; dtgDiem = ''; dtgLoai = ''; dtgTim = x.ma; return scrDuyetTang();
  });
  /* Viec giao tu man Viec hom nay (#351): mo man chi tiet, co nut bao xong. */
  if (l === 'goi_y') return go(function () { return scrViecGoiY(x.ma); });
  toast('Phiếu ' + x.ma + ' cần xử lý trên máy tính.', 4200);
}

function vgbODong(k, icon, t1, t2) {
  return '<div class="hub" data-go="' + k + '"><div class="hi">' + icon + '</div>' +
    '<div class="ht"><div class="h1">' + h(t1) + '</div><div class="h2">' + h(t2) + '</div></div>' +
    '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
}

/* Tra ve mo ta phan he theo khoa. Mot cho duy nhat do bang VGB_NHOM, de
   khong cho nao chep lai vong lap tim nhom roi lech nhau. */
function vgbNhomTheoKhoa(k) {
  for (var i = 0; i < VGB_NHOM.length; i++) if (VGB_NHOM[i].k === k) return VGB_NHOM[i];
  return null;
}

function scrNhom(nh) {
  vgbCss();
  /* v565: ve theo nhom. vgbChiaNhom lo phan quyet dinh, cho nay chi ve.
     Phan he khong khai nhom (Nhap kho, Kiem ke, Nhan su - ba o mot man) thi
     tra ve dung mot nhom khong ten, va ve ra y het ban truoc v565. */
  var nhom = vgbChiaNhom(nh, function (k) { return !!VGB_HUB[k]; });
  var html = '';
  for (var i = 0; i < nhom.length; i++) {
    var g = nhom[i], rows = '';
    for (var j = 0; j < g.keys.length; j++) rows += VGB_HUB[g.keys[j]].html;
    if (g.t) {
      html += '<div class="sec">' + h(g.t) +
        (g.p ? '<i>' + h(g.p) + '</i>' : '') + '</div>';
    }
    html += '<div class="card">' + rows + '</div>';
  }
  var body = frame(nh.ten, html);
  root.onclick = null;
  body.onclick = function (e) {
    var r = e.target.closest('[data-go]');
    if (r) vgbGo(r.dataset.go);
  };
}

/* ---------- Dia chi that cho tung man (23/08/2026) ----------

   Anh Viet: *"click vao bat ky menu nao URL cung dung im, F5 la bi vang ve
   trang chu"*.

   App nay KHONG dung Vue nen khong co Vue Router de bat sang History Mode.
   Cach lam o day la tu tay: doi dia chi khi mo man, va doc dia chi luc khoi
   dong.

   TU v288 BANG DUOI DO MAY VIET. Nguon that la bang MAN trong
   vagabond/duong_app.py, va slug do slugify() sinh ra tu chinh TEN man hinh.
   Sua o day la vo ich: chay lai sinh_duong.py la mat, ma khong chay lai thi
   ca kiem thu_duong_app.py do.

   Vi sao phai may sinh: ban cu co hai bang go tay va mot ca kiem doi chieu
   chung. Ca kiem do chi bat duoc luc hai bang LECH, khong bat duoc luc ca
   hai cung SAI - va ngay 23/08 ca hai cung gan `don-da-huy` cho khoa DTREO
   la man "Don con treo". Ca kiem xanh, nguoi dung bam ra nham man. */
/* === BANG DUONG DAN: MAY SINH RA, DUNG SUA TAY === */
/* Nguon that: vagabond/duong_app.py, bang MAN va DANH_MUC.
   Sua ben do roi chay: python3 sinh_duong.py
   Sua tay o day thi ca kiem thu_duong_app.py do ngay. */
var VGB_DUONG = {
  'ban-tai-quay': 'POS',
  'bang-bep-hom-nay': 'KIT',
  'bang-gia': 'BGIA',
  'bao-cao': 'BCHUB',
  'bien-nhan-nop-tien-mat': 'BNTM',
  'but-toan': 'BT',
  'cai-dat-cuoi-ngay': 'CDCN',
  'cai-dat-loi-va-api': 'CDLOI',
  'canh-bao-thanh-toan': 'CBTT',
  'chi-phi-van-don': 'CPX',
  'chuyen-phantom': 'PTCH',
  'cong-no': 'CN',
  'cong-no-phai-tra': 'CNPT',
  'cong-thuc': 'CTBOM',
  'danh-muc-san-pham': 'CDSP',
  'danh-sach-thanh-toan-noi-bo': 'DSTTNB',
  'diem-ban': 'CDDB',
  'doanh-so': 'DS',
  'doi-chieu-mua': 'DCM',
  'doi-soat-cod': 'DSCOD',
  'doi-soat-nha-cung-cap': 'DSVN',
  'don-chung-tu-thu': 'PTDON',
  'don-con-treo': 'DTREO',
  'don-da-huy': 'DHUY',
  'don-mua-hang': 'PO',
  'don-tiec': 'TIEC',
  'duyet-don-hang-tang': 'DUYETTANG',
  'duyet-yeu-cau': 'DUYETYC',
  'hang-chuyen-ve-kho-toi': 'NHANDC',
  'hang-khach': 'CDHT',
  'ho-so-thanh-toan': 'APPTT',
  'hoa-don-ban': 'HDBAN',
  'hoa-don-chua-tru-kho': 'TRUKHO',
  'hoa-don-mua': 'HDMUA',
  'hoan-tien': 'HT',
  'hop-dong': 'HDG',
  'huong-dan-che-bien': 'HDCB',
  'khach-hang': 'KH',
  'khoa-so': 'CDKS',
  'khuyen-mai': 'KM',
  'kiem-banh-theo-mua': 'KBM',
  'kiem-ke': 'KK',
  'kpi': 'KPI',
  'kpi-bang-chi-tieu': 'KPICD',
  'kpi-cua-toi': 'KPITOI',
  'lap-ke-hoach-san-xuat': 'KHSX',
  'ma-otp': 'OTP',
  'mau-in': 'CDMU',
  'may-in': 'CDMI',
  'nghien-cuu-phat-trien': 'RND',
  'nguoi-dung': 'QLND',
  'nha-cung-cap': 'NCC',
  'nhap-kho': 'RCV',
  'nhap-sao-ke': 'NHAPSK',
  'nop-quy': 'NQ',
  'phan-he-ban-hang': 'PH:BH',
  'phan-he-bao-cao': 'PH:BC',
  'phan-he-cai-dat': 'PH:KHAC',
  'phan-he-danh-muc': 'PH:DM',
  'phan-he-dat-hang': 'PH:DH',
  'phan-he-giao-hang': 'PH:GH',
  'phan-he-ke-toan': 'PH:KT',
  'phan-he-kiem-ke': 'PH:KK',
  'phan-he-nhan-su': 'PH:NS',
  'phan-he-nhap-kho': 'PH:NK',
  'phan-he-san-xuat': 'PH:SX',
  'phan-he-thu-mua': 'PH:TM',
  'phan-he-xuat-kho': 'PH:XK',
  'phan-quyen': 'QLQ',
  'phi-book-app': 'PHIAPP',
  'phieu-hoan-tien': 'PHHUY',
  'phuong-thuc-thanh-toan': 'CDPT',
  'quyen-quay': 'CDQQ',
  'san-xuat': 'MFG',
  'sepay': 'CDSE',
  'so-tay': 'SOTAY',
  'tai-khoan-cua-toi': 'ACC',
  'tai-khoan-ke-toan': 'CDTK',
  'tai-san': 'TS',
  'tang-qua-khach-vip': 'TQV',
  'tao-nha-cung-cap': 'NCCTAO',
  'thanh-toan': 'PAY',
  'thanh-toan-noi-bo': 'DNC',
  'thong-bao': 'CDTB',
  'ton-kho': 'STOCK',
  'ton-kho-theo-chang': 'TONCHANG',
  'tra-cuu-bang-gia-mua-vao': 'DM:DMGIA',
  'tra-cuu-cong-thuc-dinh-muc': 'DM:DMBOM',
  'tra-cuu-danh-muc-khach-hang': 'DM:DMKH',
  'tra-cuu-danh-muc-ngan-hang': 'DM:DMNH',
  'tra-cuu-danh-muc-san-pham': 'DM:DMSP',
  'tra-cuu-don-vi-tinh': 'DM:DMDVT',
  'tra-cuu-kho-hang': 'DM:DMKHO',
  'tra-cuu-nha-cung-cap': 'DM:DMNCC',
  'tra-cuu-nhom-khach-hang': 'DM:DMNKH',
  'tra-cuu-nhom-nha-cung-cap': 'DM:DMNNCC',
  'tra-cuu-nhom-san-pham': 'DM:DMNSP',
  'tra-cuu-phuong-thuc-thanh-toan': 'DM:DMPT',
  'tra-cuu-quy-doi-don-vi-tinh': 'DM:DMQD',
  'tra-cuu-tai-khoan-ke-toan': 'DM:DMTK',
  'tra-cuu-thue-ban-ra': 'DM:DMTHUE',
  'tra-cuu-thue-mua-vao': 'DM:DMTHUEM',
  'trang-dat-banh-web': 'CDWEB',
  'tro-ly': 'CDTL',
  'van-don': 'VD',
  'viec-can-lam': 'VCL',
  'viec-hom-nay': 'BCSANG',
  'xuat-ban-si': 'XKSI',
  'xuat-dieu-chuyen': 'XKD',
  'xuat-dung-noi-bo': 'XKNB',
  'xuat-huy': 'XKH',
  'xuat-kho-phuc-vu-ban-hang': 'XKPV',
  'xuat-tra-nha-cung-cap': 'XKTRA'
};
/* === HET BANG DUONG DAN === */

function vgbSlugTheoKhoa(k) {
  for (var s in VGB_DUONG) { if (VGB_DUONG[s] === k) return s; }
  return '';
}

/* DIA CHI LUC NAP TRANG, chup ngay khi tep duoc doc chu khong doi den luc
   goi. Tu v292 `reset()` co doi dia chi, va __boot goi reset(scrHome) TRUOC
   khi goi vgbMoTheoDiaChi - nen neu doc location.pathname luc do thi no da
   bi ghi de mat roi, va F5 tai /hoa-don-mua se ra trang chu. */
var VGB_DIA_NAP = String(location.pathname || '');

/* Dia chi cua man chu. Thuong la /bep, tru khi app duoc nap tu mot duong
   dan la nao do thi giu nguyen duong dan do de khong nem nguoi dung di. */
var VGB_GOC = '';
function vgbGocApp() {
  if (VGB_GOC) return VGB_GOC;
  var p = String(VGB_DIA_NAP || '').replace(/\/+$/, '');
  var d = p.replace(/^\/+/, '');
  VGB_GOC = (!d || VGB_DUONG[d]) ? '/bep' : p;
  return VGB_GOC;
}

/* Ap dia chi cua nac dang dung len thanh dia chi. Khung app goi ham nay o
   MOI cho lam chong doi: go, back, reset, va popstate.

   replaceState chu khong pushState: moc lich su do go() day, o day chi dan
   dung dia chi vao moc vua day. Day them mot moc nua thi nut Back phai bam
   hai lan moi lui duoc mot man. */
function vgbApDiaChi(slug) {
  var dia = slug ? '/' + slug : vgbGocApp();
  try {
    if (location.pathname !== dia) history.replaceState(history.state, '', dia);
  } catch (e) { }
}
window.vgbApDiaChi = vgbApDiaChi;

/* Khoa man sap mo. vgbGo dat truoc khi goi go(), go() doc mot lan roi xoa.

   Vi sao khong truyen thang khoa vao go(): go() duoc goi tu hang tram cho
   trong app, phan lon la man chi tiet khong co khoa rieng. Them mot doi so
   la sua hang tram cho goi, va cho nao quen sua thi lang le mat dia chi. */
var VGB_KHOA_MO = '';
function vgbSlugSapMo() {
  var k = VGB_KHOA_MO;
  VGB_KHOA_MO = '';
  return k ? vgbSlugTheoKhoa(k) : '';
}
window.vgbSlugSapMo = vgbSlugSapMo;

/* Luc khoi dong: dia chi dang la mot slug thi mo thang man do.
   Van de scrHome o duoi cung chong, de nut Back tu man do ve duoc trang chu
   thay vi thoat han khoi app. */
function vgbMoTheoDiaChi() {
  var d = String(VGB_DIA_NAP || '').replace(/^\/+|\/+$/g, '');
  var k = VGB_DUONG[d];
  if (!k) return false;
  try { vgbGo(k); return true; } catch (e) { return false; }
}

/* Mot cho duy nhat dinh tuyen tu o nho sang man hinh.

   Boc quanh vgbDinhTuyen de KHOA LUON DUOC XOA. Nhanh nao khong goi go(),
   vi du nhanh toast bao man chua dung, thi khoa con dinh lai se nhay sang
   lan go() ke tiep va dat sai dia chi cho mot man khac han. */
function vgbGo(k) {
  VGB_KHOA_MO = k;
  try {
  /* O LON tren trang chu, tuc phan he. Mot nhanh tien to cho ca muoi hai,
     y het cach ho DM: di chung mot nhanh. */
  if (k && k.indexOf('PH:') === 0) {
    var nhx = vgbNhomTheoKhoa(k.slice(3));
    if (!nhx) return;
    return go(function () { scrNhom(nhx); });
  }
  if (k === 'VCL') return go(scrVclList);
  if (k === 'SOTAY') return go(scrSoTay);
  if (k === 'KBD') { location.href = '/kiem-banh'; return; }
  if (k === 'KBM') return go(scrMuaVuDs);
  if (k === 'BTPO') { location.href = '/btp'; return; }
  if (k === 'PAY') return go(scrPayList);
  if (k === 'BGIA') return go(scrBangGia);
  if (k === 'NCC') return go(scrNcc);
  if (k === 'NCCTAO') return go(scrNccTao);
  if (k === 'STOCK') return go(scrStock);
  if (k === 'TONCHANG') return go(scrTonChang);
  if (k === 'KIT') return go(scrKitchen);
  if (k === 'MFG') return go(scrMfgList);
  if (k === 'CTBOM') return go(scrCongThuc);
  if (k === 'KHSX') return go(scrKeHoachSX);
  if (k === 'TIEC') return go(scrDonTiec);
  if (k === 'HDCB') return go(scrHuongDan);
  if (k === 'RCV') return go(scrRecvList);
  if (k === 'NBANH') return go(scrNhanBanh);
  if (k === 'KK') return go(scrKkList);
  if (k === 'DS') return go(scrDoanhSo);
  if (k === 'DTREO') return go(scrDonTreo);
  /* Man "Don da huy cho hoan" truoc gio chi mo duoc tu man khac, khong co
     khoa rieng. Them khoa o day de no co DIA CHI that, con o nho tren trang
     chu thi giu nguyen nhu cu, khong them the moi. */
  if (k === 'DHUY') return go(scrDonHuy);
  if (k === 'PHHUY') return go(scrPhieuHoanHuy);
  if (k === 'POS') return go(scrPosChonQuay);
  if (k === 'TQV') return go(scrTqDot);
  if (k === 'HDG') return go(scrHopDongHub);
  if (k === 'BC3') return go(function () { kmThe = 'bc'; scrKhuyenMai(); });
  if (k === 'KT1') return go(scrDoanhSo);
  if (k === 'BCHUB') return go(scrBaoCao);
  if (k === 'BCSANG') return go(scrBangSang);
  if (k === 'DUYETYC') return go(scrDuyetYc);
  if (k === 'PO') return go(scrDonMua);
  if (k === 'KHPO') return kgMo('PO');
  if (k === 'KHHDM') return kgMo('HDM');
  if (k === 'CNPT') return go(scrNoPhaiTra);
  if (k === 'HDBAN') return go(scrHdBan);
  if (k === 'TRUKHO') { tkDiem = ''; tkLocChon = 'cho'; return go(scrTruKho); }
  if (k === 'APPTT') return go(scrHoSoTT);
  if (k === 'DSTTNB') return go(scrTTNB);
  if (k === 'DUYETTANG') { dtgChang = ''; return go(scrDuyetTang); }
  if (k === 'SOTANG') { dtgChang = 'hoan_tat'; return go(scrDuyetTang); }
  if (k === 'HDMUA') return go(scrHdMua);
  if (k === 'DCM') return go(scrDoiChieuMua);
  if (k && k.indexOf('BC:') === 0) { bcMa = k.slice(3); return go(scrBaoCaoXem); }
  if (k && k.indexOf('BC') === 0) return toast('Báo cáo này chưa dựng. Anh Việt chốt nội dung rồi hệ thống điền vào.', 4200);
  if (k && k.indexOf('KT') === 0) return toast('Mục kế toán này chưa dựng. Anh Việt chốt nội dung rồi hệ thống điền vào.', 4200);
  if (k === 'OTP') return go(scrOtp);
  if (k === 'KM') return go(scrKhuyenMai);
  if (k === 'CN') return go(scrCongNo);
  if (k === 'HT') return go(scrHoanTien);
  /* Hai o, mot man. Khac nhau dung mot bien: o ben Ban hang chi bay
     phieu cua chinh minh, o ben Ke toan bay tat ca. */
  if (k === 'BNTM') { BNT_TOI = 1; return go(scrBntDs); }
  if (k === 'NQ') { BNT_TOI = 0; return go(scrBntDs); }
  if (k === 'KH') return go(scrKhachHang);
  if (k === 'VD') return go(scrVanDon);
  if (k === 'CPX') return go(scrVdChiPhi);
  if (k === 'PHIAPP') return go(scrVdPhiApp);
  if (k === 'DSCOD') return go(scrVdCod);
  if (k === 'CBTT') return go(scrCanhBaoTT);
  if (k === 'RND') return go(scrRndList);
  if (k === 'NHANDC') return go(scrHangVeKho);
  /* Một nhánh tiền tố cho cả 16 danh mục. Chép 16 nhánh tay là 16 cơ hội
     gõ nhầm một mã, và đó đúng là lỗi dead link ngày 16/08. */
  if (k.indexOf('DM:') === 0) return kgMo(k.slice(3));
  if (k === 'DNC') return go(scrTTNB);
  if (k === 'KPI') return go(scrKPI);
  if (k === 'KPICD') return go(scrKPICau);
  if (k === 'KPITOI') return go(scrKPIToi);
  if (k === 'CDDB') return go(scrDiemBan);
  if (k === 'CDKS') return go(scrKhoaSo);
  if (k === 'CDPT') return go(scrPtThanhToan);
  if (k === 'CDTK') return go(scrTaiKhoan);
  if (k === 'CDSP') return go(scrDanhMuc);
  if (k === 'CDMI') return go(scrMayIn);
  if (k === 'CDMU') return go(scrMauIn);
  if (k === 'CDQQ') return go(scrQuyenQuay);
  if (k === 'CDHT') return go(scrHangKhach);
  if (k === 'CDCN') return go(scrCaiDatCuoiNgay);
  if (k === 'CDKHO') return go(scrCaiDatKho);
  if (k === 'CDSE') return go(scrSePay);
  if (k === 'CDTL') return go(scrTroLyCaiDat);
  if (k === 'CDTB') return go(scrThongBao);
  if (k === 'CDWEB') return go(scrCaiDatWeb);
  if (k === 'CDLOI') return go(scrCaiDatLoi);
  if (k === 'DSVN') return go(scrDsvn);
  if (k === 'PTDON') return go(scrDonChungTuThu);
  if (k === 'PTCH') return go(scrChuyenPhantom);
  if (k === 'NHAPSK') return go(scrNhapSaoKe);
  if (k === 'TS') return go(scrTaiSan);
  if (k === 'BT') return go(scrButToan);
  if (k === 'QLND') return go(scrNguoiDung);
  if (k === 'QLQ') return go(scrQuyen);
  if (k === 'ACC') return go(scrAccount);
  if (k === 'XKH') return go(scrXkHuyList);
  if (k === 'XKNB') return go(scrXkNbList);
  if (k === 'XKPV') return go(scrXkPvList);
  if (k === 'XKD') return go(scrXkCkList);
  if (k === 'XKTRA') return go(scrXkTraList);
  if (k === 'XKSI') return go(scrXkSiList);
  go(function () { scrMRList(TYPES[k]); });
  } finally {
    /* XOA KHOA DU NHANH NAO CHAY. Nhanh nao khong goi go() - vi du nhanh
       toast bao man chua dung - thi khoa con nguyen, va lan go() ke tiep,
       du la cua man nao, cung nhan dung khoa do va dat sai dia chi. */
    VGB_KHOA_MO = '';
  }
}

