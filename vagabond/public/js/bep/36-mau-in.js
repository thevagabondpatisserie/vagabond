/* ---------- Cai dat - Mau in an tai quay (anh Viet 26/08/2026) ----------

   *"Anh thay em can lam them phan he Cau hinh mau in an trong nut cai dat
   tren app, trong do co cau hinh mau in hoa don, cau hinh mau in tem,... de
   nhan vien chinh duoc giong nhu ben ipos."*

   RANH GIOI VOI MAN MAY IN - hai man, hai cau hoi khac nhau:

     May in    in o DAU va ra TO TO BAO NHIEU. So may, manh ten may in tren
               Windows, kho giay, can tem lech may mi li met.
     Mau in    tren to giay do IN NHUNG GI. Co logo khong, chu to hay nho,
               co in khoi diem thanh vien khong, dong cam on viet gi.

   Khong o nao duoc khai o ca hai man.

   VI SAO NUT "IN THU" IN THAT CHU KHONG XEM TREN MAN HINH
   -------------------------------------------------------
   Cai can kiem o day la TO GIAY: chu co vua khong, ten mon dai co bi cat
   khong, tem co lech mep khong. Nhung thu do man hinh khong tra loi duoc,
   chi to giay cam tren tay moi tra loi duoc. Va quan trong hon: in thu di
   dung duong in that, dung khuon that, nen no chung minh duoc cai that su
   se ra - mot ban xem truoc ve rieng thi chi chung minh duoc chinh no.

   Cung mot ly do da viet trong posInTemThu tu truoc. */

var muData = null, muDiem = '', muBan = null, muSuaDuoc = 0;

async function scrMauIn() {
  frame('Mẫu in ấn', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try { muData = await api('vagabond.mau_in_quay.danh_sach', {}); }
  catch (e) {
    frame('Mẫu in ấn', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  S.chuaLuu = '';
  muSuaDuoc = muData.sua_duoc ? 1 : 0;
  /* Mo ra la dung ngay o diem ban dang lam viec, khong bat nguoi dung tim.
     Chua chon quay nao thi dung ban chung. */
  var ma = (typeof posQuay !== 'undefined' && posQuay && posQuay.ma) ? posQuay.ma : '';
  muDiem = muCoDiem(ma) ? ma : '';
  muNapBan();
  muVe();
}

function scrMauIn0() { muVe(); }

function muCoDiem(ma) {
  var ds = (muData && muData.diem) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].ma === ma) return 1;
  return 0;
}

function muTenDiem(ma) {
  var ds = (muData && muData.diem) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].ma === ma) return ds[i].ten;
  return ma;
}

/* Ban dang sua = ban rieng cua diem neu co, khong thi CHEP tu ban chung.

   Chep chu khong tro thang vao ban chung: dang sua ban cua mot diem ma lai
   go vao ban chung thi sua mot diem hoa ra doi ca ba. */
function muNapBan() {
  var mau = (muData && muData.mau) || {};
  var goc = muDiem ? ((mau.diem || {})[muDiem] || mau.chung) : mau.chung;
  muBan = JSON.parse(JSON.stringify(goc || {}));
}

function muRieng() {
  return !!(muDiem && ((muData.mau || {}).diem || {})[muDiem]);
}

function muVe() {
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">MẪU IN ẤN</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Chỉnh nội dung in trên tờ hoá đơn, phiếu làm món và tem - có in logo không, chữ to hay nhỏ, ' +
    'dòng cảm ơn viết gì. Còn máy nào in và khổ giấy bao nhiêu thì khai bên màn ' +
    '<b>Máy in</b>, không khai hai nơi.</div></div>';

  /* Chon pham vi. Ban chung dat truoc vi phan lon thoi gian chi can no. */
  html += '<div class="sec">Áp dụng cho</div><div class="card" style="padding:11px 12px">' +
    '<div style="display:flex;flex-wrap:wrap;gap:7px">' +
    muChip('', 'Dùng chung') +
    ((muData.diem || []).map(function (d) { return muChip(d.ma, d.ten); }).join('')) +
    '</div>' +
    '<div style="font-size:12px;color:#98a2b3;margin-top:9px;line-height:1.55">' +
    (muDiem
      ? (muRieng()
        ? 'Điểm ' + h(muTenDiem(muDiem)) + ' đang có mẫu riêng.'
        : 'Điểm ' + h(muTenDiem(muDiem)) + ' đang theo mẫu dùng chung. Sửa rồi bấm Lưu thì nó tách ra thành mẫu riêng.')
      : 'Điểm bán nào chưa có mẫu riêng thì in theo mẫu này.') +
    '</div></div>';

  (muData.vai_tro || []).forEach(function (v) {
    html += '<div class="sec">' + (v.ic || '🖨') + ' ' + h(v.ten) + '</div>' +
      '<div class="card">' +
      '<div style="padding:10px 14px;font-size:12.5px;color:#98a2b3;border-bottom:1px solid #f2f4f7">' + h(v.mo || '') + '</div>' +
      (((muData.o || {})[v.k] || []).map(function (o) { return muDong(v.k, o); }).join('')) +
      '<div style="padding:11px 14px">' +
      '<button class="btn gh" data-inthu="' + v.k + '" style="margin:0;width:auto;padding:8px 14px">🖨 In thử ' + h(v.ten.toLowerCase()) + '</button>' +
      '</div></div>';
  });

  if (muSuaDuoc) {
    html += '<div style="padding:14px">' +
      '<button class="btn" id="muLuu">Lưu mẫu in</button>' +
      '<button class="btn gh" id="muTra" style="margin-top:9px">' +
      (muDiem ? 'Bỏ mẫu riêng, theo lại mẫu dùng chung' : 'Trả mọi ô về mặc định') + '</button></div>';
  } else {
    html += '<div class="card" style="padding:12px 14px;font-size:13px;color:#b45309">' +
      'Bạn đang xem thôi. Chỉ quản lý cửa hàng hoặc kế toán mới sửa được mẫu in.</div>';
  }

  frame('Mẫu in ấn', html);
  muGan();
}

function muChip(ma, ten) {
  var chon = (muDiem === ma);
  return '<button class="btn gh" data-diem="' + h(ma) + '" style="margin:0;width:auto;padding:7px 13px;font-size:13px;' +
    (chon ? 'background:#50DBF2;color:#05323C;border-color:#50DBF2;font-weight:700' : '') + '">' + h(ten) + '</button>';
}

/* Mot o cau hinh. Kieu o do may chu quyet dinh (mau_in_quay.O), man hinh
   chi dung ra - them mot o moi thi khong phai sua tep nay. */
function muDong(vai, o) {
  var gt = ((muBan || {})[vai] || {})[o.k];
  var id = 'mu_' + vai + '_' + o.k;
  var phai;
  if (o.loai === 'bat') {
    phai = '<input type="checkbox" id="' + id + '"' + (gt ? ' checked' : '') +
      (muSuaDuoc ? '' : ' disabled') +
      ' style="flex:none;width:22px;height:22px;accent-color:#0f766e">';
  } else if (o.loai === 'so') {
    phai = '<input type="number" id="' + id + '" value="' + h(String(gt)) + '"' +
      ' min="' + o.min + '" max="' + o.max + '" step="' + (o.buoc || 1) + '"' +
      (muSuaDuoc ? '' : ' disabled') +
      ' style="flex:none;width:88px;text-align:right;padding:8px 10px;border:1px solid #d0d5dd;border-radius:9px;font-size:14px">';
  } else {
    phai = '';
  }
  var tren = '<div style="display:flex;align-items:center;gap:12px;padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
    '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(o.ten) + '</b>' +
    (o.mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:2px;line-height:1.45">' + h(o.mo) + '</div>' : '') +
    '</div>' + phai + '</div>';
  if (o.loai !== 'chu') return tren;
  /* O chu dai thi cho xuong dong rieng, khong nhet vao ben phai cho chat. */
  return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
    '<b style="font-size:14px">' + h(o.ten) + '</b>' +
    (o.mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:2px">' + h(o.mo) + '</div>' : '') +
    '<input type="text" id="' + id + '" value="' + h(String(gt || '')) + '" maxlength="' + (o.dai || 80) + '"' +
    (muSuaDuoc ? '' : ' disabled') +
    ' style="width:100%;margin-top:7px;padding:9px 11px;border:1px solid #d0d5dd;border-radius:9px;font-size:14px"></div>';
}

/* Doc man hinh vao muBan. Goi TRUOC moi lan doi pham vi hay bam Luu, de
   nhung o vua go khong bay mat. */
function muDoc() {
  (muData.vai_tro || []).forEach(function (v) {
    var ban = (muBan[v.k] = muBan[v.k] || {});
    (((muData.o || {})[v.k]) || []).forEach(function (o) {
      var e = document.getElementById('mu_' + v.k + '_' + o.k);
      if (!e) return;
      if (o.loai === 'bat') ban[o.k] = e.checked ? 1 : 0;
      else if (o.loai === 'so') {
        var x = parseFloat(e.value);
        /* Go bay so ngoai khoang thi giu nguyen o cu chu khong ghi bua:
           may chu cung go lai lan nua, nhung nguoi dung phai thay ngay. */
        if (!isNaN(x) && x >= o.min && x <= o.max) ban[o.k] = x;
      } else ban[o.k] = String(e.value || '').trim();
    });
  });
}

function muGan() {
  var g = document.getElementById('vgbBody') || document;
  g.querySelectorAll('[data-diem]').forEach(function (n) {
    n.onclick = function () {
      var ma = n.getAttribute('data-diem') || '';
      if (ma === muDiem) return;
      muDoc();
      /* Doi pham vi la BO nhung gi vua go cho pham vi cu, vi hai pham vi la
         hai ban khac nhau. Hoi mot cau chu khong lang le vut di. */
      if (S.chuaLuu) {
        xacNhan('Bỏ những ô vừa sửa và chuyển sang mẫu khác?', 'Chưa lưu', 'Bỏ')
          .then(function (ok) {
            if (!ok) return;
            S.chuaLuu = '';
            muDiem = ma;
            muNapBan();
            muVe();
          });
        return;
      }
      muDiem = ma;
      muNapBan();
      muVe();
    };
  });
  g.querySelectorAll('[data-inthu]').forEach(function (n) {
    n.onclick = function () {
      muDoc();
      muInThu(n.getAttribute('data-inthu'));
    };
  });
  ['input', 'change'].forEach(function (bc) {
    g.addEventListener(bc, function () { S.chuaLuu = 'Mẫu in'; }, { once: false });
  });
  var l = document.getElementById('muLuu');
  if (l) l.onclick = muLuu;
  var t = document.getElementById('muTra');
  if (t) t.onclick = muTraMacDinh;
}

async function muLuu() {
  muDoc();
  busy(true);
  try {
    muData = await api('vagabond.mau_in_quay.luu', {
      diem: muDiem, mau: JSON.stringify(muBan)
    });
    muSuaDuoc = muData.sua_duoc ? 1 : 0;
    S.chuaLuu = '';
    /* Cau hinh ban hang cu con trong bo nho thi ban in tiep theo van ra mau
       cu. Xoa di de lan in sau doc lai - y het cach man May in lam. */
    CFGBH = null;
    busy(false);
    toast('Đã lưu mẫu in');
    muNapBan();
    muVe();
  } catch (e) {
    busy(false);
    baoTin((e && e.message) || 'Không lưu được');
  }
}

async function muTraMacDinh() {
  var ok = await xacNhan(muDiem
    ? 'Bỏ mẫu riêng của điểm ' + muTenDiem(muDiem) + ', cho nó in theo mẫu dùng chung?'
    : 'Trả mọi ô của mẫu dùng chung về mặc định?', 'Trả về mặc định', 'Trả về');
  if (!ok) return;
  busy(true);
  try {
    muData = await api('vagabond.mau_in_quay.tra_mac_dinh', { diem: muDiem });
    muSuaDuoc = muData.sua_duoc ? 1 : 0;
    S.chuaLuu = '';
    CFGBH = null;
    busy(false);
    toast('Đã trả về mặc định');
    muNapBan();
    muVe();
  } catch (e) {
    busy(false);
    baoTin((e && e.message) || 'Không đổi được');
  }
}

/* ---------- In thu ----------

   Don mau co du cac tinh huong de nhin mot to giay la biet het: mon co tuy
   chon pha che, mon khong co, mon gia 0 dong, co giam gia, co ghi chu, co
   khoi diem thanh vien.

   `name` de RONG va `diem` dien san la co y: hai o do la dieu kien de
   posInBill di hoi may chu ma hoa don that va ten thu ngan that. Don mau
   thi khong co gi de hoi, hoi la ra loi ngay giua luc dang can tem. */
function muDonMau() {
  return {
    bill: 'IN-THU', name: '', tam_tinh: 0, huy: 0,
    thu_ngan: 'Bản in thử', so_ban: '12',
    quay: (typeof posQuay !== 'undefined' && posQuay && posQuay.ma) || '',
    nguon: '', pt: 'Chuyển khoản',
    mon: [
      { ten: 'Americano Dừa Xiêm Xanh', item_code: 'NUCF001', qty: 2, rate: 85000, tc: ['ít đá', '70% đường'] },
      { ten: 'Croissant bơ Pháp', item_code: 'BAVN001', qty: 1, rate: 45000, tc: [] },
      { ten: 'Bánh tặng khách quen', item_code: 'BAVN002', qty: 1, rate: 0, tc: [], gc: 'Gói riêng' }
    ],
    tong: 215000, thu: 205000, giamTay: 10000, kmAp: [],
    ghi_chu: 'Bản in thử để căn mẫu, không phải đơn thật.',
    xhd_url: '/xuat-hoa-don/in-thu',
    diem: { hang: 'Hạng Bạc', ten: 'Khách in thử', dung: 0, tich: 205, ty_le: 1, du_sau: 1250 }
  };
}

/* Ap ban DANG SUA tren man hinh vao truoc khi in, chu khong doi bam Luu.

   Neu bat in thu doc tu may chu thi phai luu roi moi thu duoc, tuc la moi
   lan can chu to len nua lai ghi mot ban vao so cai. Nen o day nhet tam
   ban dang sua vao CFGBH, in xong tra lai y cu. */
async function muInThu(vai) {
  if (!CFGBH) {
    try { CFGBH = await api('vagabond.ban_hang.cfg', {}); }
    catch (e) { return baoTin('Chưa đọc được cấu hình bán hàng, thử lại.'); }
  }
  var giuChung = CFGBH.mau_in, giuDiem = CFGBH.mau_in_diem;
  var ma = (typeof posQuay !== 'undefined' && posQuay && posQuay.ma) ? posQuay.ma : '';
  CFGBH.mau_in = muBan;
  CFGBH.mau_in_diem = {};
  if (ma) CFGBH.mau_in_diem[ma] = muBan;
  try {
    var d = muDonMau();
    if (vai === 'tem') await posInTemLy(d);
    else if (vai === 'phieu_mon') await posInPhieuMon(d);
    else await posInBill(d);
  } catch (e) {
    baoTin((e && e.message) || 'Không in thử được');
  } finally {
    CFGBH.mau_in = giuChung;
    CFGBH.mau_in_diem = giuDiem;
  }
}
