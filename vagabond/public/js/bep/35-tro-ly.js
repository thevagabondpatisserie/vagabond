/* Tro ly huong dan dung app: nut noi va khung hoi dap.
   ---------------------------------------------------
   Anh Viet chot 26/08/2026. Giai doan dau chi cap quan ly dung thu, tro ly
   chi giai thich cach dung app chu chua doc du lieu that cua tiem.

   VI SAO GAN VAO document.body CHU KHONG VAO #vgb
   `frame()` ghi de toan bo `root.innerHTML` moi lan doi man. Cai gi nam
   trong do se bien mat ngay man ke tiep. Nut noi phai song qua moi man nen
   gan thang vao body, dat z-index cao hon #vgb.

   VI SAO DAT BEN TRAI
   Goc phai duoi da co nut `.fab` dau cong cua nhieu man. Hai nut tron chong
   len nhau thi tren dien thoai bam nham la chuyen chac chan.

   XUNG HO
   Tro ly xung "He thong". Moi cau chu trong tep nay phai giu dung giong do,
   va tuyet doi khong duoc xung "em" - xem ca kiem thu_xung_ho.py. */

var TL_VAI = ['System Manager', 'Giám đốc', 'AP Giám đốc', 'Accounts Manager',
  'Manufacturing Manager', 'Purchase Manager', 'Sales Manager', 'Item Manager',
  'Quản lý cửa hàng'];

var tlMo = 0, tlBan = 0, tlNhatKy = '';

function tlDuocDung() {
  for (var i = 0; i < TL_VAI.length; i++) if (hasRole(TL_VAI[i])) return 1;
  return 0;
}

function tlCss() {
  if (document.getElementById('tlCss')) return;
  var s = document.createElement('style');
  s.id = 'tlCss';
  s.textContent =
    '#tlNut{position:fixed;left:16px;bottom:calc(env(safe-area-inset-bottom,0px) + 18px);' +
    'width:52px;height:52px;border-radius:26px;background:#05323C;color:#fff;border:0;' +
    'font-size:24px;line-height:1;box-shadow:0 6px 18px rgba(5,50,60,.42);cursor:pointer;' +
    'display:flex;align-items:center;justify-content:center;z-index:12}' +
    '#tlNen{position:fixed;inset:0;background:rgba(5,50,60,.42);z-index:13;display:none}' +
    '#tlKhung{position:fixed;left:0;right:0;bottom:0;max-height:82vh;background:#fff;' +
    'border-radius:18px 18px 0 0;z-index:14;display:none;flex-direction:column;' +
    'box-shadow:0 -8px 28px rgba(0,0,0,.22)}' +
    '#tlDau{flex:0 0 auto;padding:14px 16px 10px;border-bottom:1px solid #eef0f5;' +
    'display:flex;align-items:center;gap:10px}' +
    '#tlDau b{flex:1;font-size:16px;color:#05323C}' +
    '#tlDong{width:34px;height:34px;border:0;background:#f2f4f8;border-radius:10px;' +
    'font-size:19px;cursor:pointer;color:#5b6472}' +
    '#tlThan{flex:1;overflow-y:auto;padding:14px 16px;-webkit-overflow-scrolling:touch}' +
    '#tlChan{flex:0 0 auto;padding:10px 16px calc(env(safe-area-inset-bottom,0px) + 12px);' +
    'border-top:1px solid #eef0f5;display:flex;gap:8px}' +
    '#tlO{flex:1;padding:11px 12px;border:1.5px solid #e5e7eb;border-radius:10px;' +
    'font-size:15px;font-family:inherit;resize:none;height:44px;line-height:1.3}' +
    '#tlGui{flex:0 0 auto;padding:0 16px;border:0;border-radius:10px;background:#05323C;' +
    'color:#fff;font-size:15px;font-weight:600;cursor:pointer}' +
    '#tlGui:disabled{opacity:.5}' +
    '.tlH{background:#e8f7fb;color:#05323C;border-radius:12px;padding:10px 12px;' +
    'margin:0 0 10px auto;max-width:88%;font-size:14.5px;line-height:1.5;width:fit-content}' +
    '.tlT{background:#f7f8fa;border-radius:12px;padding:11px 13px;margin:0 0 6px;' +
    'font-size:14.5px;line-height:1.6;white-space:pre-wrap;color:#16181d}' +
    '.tlN{font-size:11.5px;color:#98a2b3;margin:0 0 14px;display:flex;gap:12px;' +
    'align-items:center;flex-wrap:wrap}' +
    '.tlBao{border:0;background:transparent;color:#b45309;font-size:11.5px;' +
    'cursor:pointer;padding:2px 0;text-decoration:underline}' +
    '.tlBao[disabled]{color:#98a2b3;text-decoration:none;cursor:default}' +
    '.tlGoi{font-size:13px;color:#6b7280;line-height:1.6;margin-bottom:12px}';
  document.head.appendChild(s);
}

function tlThemHoi(t) {
  var d = document.createElement('div');
  d.className = 'tlH';
  d.textContent = t;
  document.getElementById('tlThan').appendChild(d);
}

/* Moi cau tra loi keo theo dung mot nut bao. Nut do cam co vao DUNG dong
   nhat ky cua cau tra loi day, khong phai vao cau gan nhat. */
function tlThemTra(t, maNhatKy, nguon) {
  var than = document.getElementById('tlThan');
  var d = document.createElement('div');
  d.className = 'tlT';
  d.textContent = t;
  than.appendChild(d);
  var c = document.createElement('div');
  c.className = 'tlN';
  var nut = document.createElement('button');
  nut.className = 'tlBao';
  nut.textContent = 'Báo cáo lỗi / Không hữu ích';
  if (!maNhatKy) nut.disabled = true;
  nut.onclick = async function () {
    nut.disabled = true;
    nut.textContent = 'Đang gửi...';
    try {
      await api('vagabond.tro_ly.bao_loi', { nhat_ky: maNhatKy });
      nut.textContent = 'Đã ghi nhận, quản lý sẽ xem lại';
    } catch (e) {
      nut.disabled = false;
      nut.textContent = 'Báo cáo lỗi / Không hữu ích';
      toast(errMsg(e), 4000);
    }
  };
  c.appendChild(nut);
  if (nguon && nguon.length) {
    var n = document.createElement('span');
    n.textContent = 'Tra theo: ' + nguon.slice(0, 3).join(', ');
    c.appendChild(n);
  }
  than.appendChild(c);
  than.scrollTop = than.scrollHeight;
}

async function tlGui() {
  if (tlBan) return;
  var o = document.getElementById('tlO');
  var cau = (o.value || '').trim();
  if (!cau) return;
  tlBan = 1;
  o.value = '';
  document.getElementById('tlGui').disabled = true;
  tlThemHoi(cau);
  var cho = document.createElement('div');
  cho.className = 'tlT';
  cho.textContent = 'Đang tra sổ tay...';
  document.getElementById('tlThan').appendChild(cho);
  document.getElementById('tlThan').scrollTop = 9e9;
  try {
    var r = await api('vagabond.tro_ly.hoi', { cau_hoi: cau, man: VGB_TD || '' });
    cho.remove();
    tlThemTra((r && r.tra_loi) || '', (r && r.nhat_ky) || '', (r && r.nguon) || []);
  } catch (e) {
    cho.remove();
    tlThemTra(errMsg(e), '', []);
  }
  tlBan = 0;
  document.getElementById('tlGui').disabled = false;
}

function tlDong() {
  tlMo = 0;
  document.getElementById('tlNen').style.display = 'none';
  document.getElementById('tlKhung').style.display = 'none';
}

function tlBat() {
  tlMo = 1;
  document.getElementById('tlNen').style.display = 'block';
  document.getElementById('tlKhung').style.display = 'flex';
  var o = document.getElementById('tlO');
  if (o) o.focus();
}

function tlGan() {
  if (document.getElementById('tlNut') || !tlDuocDung()) return;
  tlCss();

  var nut = document.createElement('button');
  nut.id = 'tlNut';
  nut.setAttribute('aria-label', 'Tro ly huong dan');
  nut.innerHTML = '&#128172;';
  nut.onclick = function () { tlMo ? tlDong() : tlBat(); };
  document.body.appendChild(nut);

  var nen = document.createElement('div');
  nen.id = 'tlNen';
  nen.onclick = tlDong;
  document.body.appendChild(nen);

  var k = document.createElement('div');
  k.id = 'tlKhung';
  k.innerHTML =
    '<div id="tlDau"><b>Trợ lý hướng dẫn</b>' +
    '<button id="tlDong" aria-label="Dong">&#10005;</button></div>' +
    '<div id="tlThan"><div class="tlGoi">Hệ thống trả lời dựa trên tài liệu ' +
    'của chính phần mềm này, về cách dùng từng màn hình và ý nghĩa các câu ' +
    'chặn.<br><br>Hệ thống chưa đọc dữ liệu thật của tiệm, nên không trả lời ' +
    'được tồn kho hay tình trạng đơn. Việc cần quyết thì hỏi anh Việt.</div></div>' +
    '<div id="tlChan">' +
    '<textarea id="tlO" placeholder="Nhập câu hỏi về cách dùng app"></textarea>' +
    '<button id="tlGui">Gửi</button></div>';
  document.body.appendChild(k);

  document.getElementById('tlDong').onclick = tlDong;
  document.getElementById('tlGui').onclick = tlGui;
  document.getElementById('tlO').addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); tlGui(); }
  });
}

/* ===== Man Cai dat > Tro ly ==========================================
   Anh Viet 26/08/2026: "Anh khong thay cho anthropic key de nhap vao?"
   Dung, ban truoc chi them o do vao Cai dat ben Desk chu khong co duong
   nao trong app. Man nay la duong do.

   O khoa KHONG BAO GIO hien lai gia tri da luu, ke ca voi giam doc. De
   trong la giu nguyen khoa cu; muon go han thi go chu xoa. */

var tlcD = null;

async function scrTroLyCaiDat() {
  frame('Trợ lý', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try { tlcD = await api('vagabond.tro_ly.cai_dat', {}); }
  catch (e) {
    frame('Trợ lý', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  tlcVe();
}

function tlcVe() {
  var d = tlcD;
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">TRỢ LÝ HƯỚNG DẪN DÙNG APP</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Nút tròn góc dưới bên trái màn hình. Trợ lý chỉ giải thích <b>cách dùng app</b> ' +
    'dựa trên tài liệu của chính phần mềm, <b>chưa đọc dữ liệu thật</b> của tiệm và ' +
    'không thay ai quyết việc. Câu hỏi nào sổ tay không có thì trợ lý nói thẳng là ' +
    'chưa có tài liệu, không đoán.</div></div>';

  html += '<div class="card" style="padding:11px 12px">' + kmHangChip(
    posChipNut('data-tlcbat="1"', d.bat ? '● Đang bật' : '○ Đang tắt', !!d.bat)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px">Tắt thì nút trợ lý vẫn hiện nhưng không trả lời.</div></div>';

  html += '<div class="sec">Khoá API</div><div class="card" style="padding:12px 14px">' +
    (d.co_khoa
      ? '<div style="font-size:13px;color:#15803d;font-weight:600">✅ Đã khai khoá</div>' +
        '<div style="font-size:12px;color:#6b7280;line-height:1.6;margin-top:3px">' +
        'Khoá đã lưu thì không xem lại được từ đây, kể cả giám đốc. Muốn thay thì gõ khoá mới vào ô dưới. ' +
        'Gõ chữ <b>xoá</b> rồi lưu là gỡ hẳn khoá.</div>'
      : '<div style="font-size:13px;color:#b3261e;font-weight:600">⚠️ Chưa có khoá, trợ lý chưa trả lời được</div>' +
        '<div style="font-size:12px;color:#6b7280;line-height:1.6;margin-top:3px">' +
        'Lấy khoá trong trang quản trị tài khoản Anthropic rồi dán vào ô dưới.</div>') +
    '<input class="tin" id="tlcKhoa" type="password" autocomplete="new-password" ' +
    'placeholder="' + (d.co_khoa ? 'Để trống là giữ nguyên khoá cũ' : 'Dán khoá API vào đây') + '" ' +
    'style="width:100%;margin-top:9px"></div>';

  html += '<div class="sec">Hạn mức dùng</div><div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;gap:10px;align-items:center">' +
    '<span style="font-size:13px;color:#374151;flex:1">Mỗi người một ngày</span>' +
    '<input class="tin" id="tlcNgay" type="number" min="1" value="' + h(String(d.luot_ngay)) + '" style="width:110px"></div>' +
    '<div style="display:flex;gap:10px;align-items:center;margin-top:9px">' +
    '<span style="font-size:13px;color:#374151;flex:1">Cả tiệm một tháng</span>' +
    '<input class="tin" id="tlcThang" type="number" min="1" value="' + h(String(d.luot_thang)) + '" style="width:110px"></div>' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:9px;line-height:1.6">' +
    'Hết hạn mức thì máy chặn trước khi gọi, nên không phát sinh thêm chi phí. ' +
    'Tháng này đã hỏi ' + num(d.da_hoi_thang_nay) + ' lượt, hôm nay ' + num(d.da_hoi_hom_nay) + ' lượt.' +
    (d.bao_loi_thang_nay ? ' Có ' + num(d.bao_loi_thang_nay) + ' câu bị báo là chưa hữu ích.' : '') +
    '</div></div>';

  html += '<div class="sec">Mô hình</div><div class="card" style="padding:12px 14px">' +
    '<input class="tin" id="tlcMoHinh" value="' + h(d.mo_hinh || '') + '" placeholder="' + h(d.mo_hinh_mac_dinh) + '" style="width:100%">' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    'Để trống thì dùng ' + h(d.mo_hinh_mac_dinh) + '. Chỉ đổi khi bộ phận kỹ thuật dặn.</div></div>';

  html += '<div class="sec">Ai được hỏi</div>' +
    '<div class="card" style="padding:12px 14px;font-size:13px;color:#374151;line-height:1.7">' +
    (d.vai_duoc_hoi || []).map(function (v) { return '· ' + h(v); }).join('<br>') +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px">Đang mở cho cấp quản lý dùng thử. Mở rộng thì báo bộ phận kỹ thuật.</div></div>';

  var b = frame('Trợ lý', html, {
    footer: '<button class="btn" id="tlcLuu" style="margin:0;width:100%">Lưu cấu hình</button>'
  });

  b.onclick = function (e) {
    var t = e.target.closest('[data-tlcbat]');
    if (t) { tlcD.bat = tlcD.bat ? 0 : 1; return tlcVe(); }
  };
  document.getElementById('tlcLuu').onclick = tlcLuu;
}

async function tlcLuu() {
  var khoa = (document.getElementById('tlcKhoa') || {}).value || '';
  busy(true);
  try {
    tlcD = await api('vagabond.tro_ly.luu_cai_dat', {
      bat: tlcD.bat ? 1 : 0,
      khoa: khoa,
      mo_hinh: (document.getElementById('tlcMoHinh') || {}).value || '',
      luot_ngay: (document.getElementById('tlcNgay') || {}).value || 0,
      luot_thang: (document.getElementById('tlcThang') || {}).value || 0
    });
    busy(false);
    toast(tlcD.co_khoa ? 'Đã lưu. Trợ lý sẵn sàng trả lời.' : 'Đã lưu. Vẫn chưa có khoá API.', 3500);
    tlcVe();
  } catch (e) { busy(false); baoTin((e && e.message) || 'Không lưu được'); }
}
