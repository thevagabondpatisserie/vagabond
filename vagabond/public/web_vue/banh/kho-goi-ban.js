/* KHO gọi món tại bàn (v638, anh Việt duyệt 04/11/2026).

   Khách quét QR dán bàn: /banh?diem=TCV&ban=5&k=<16 hex>#/in-store. Link đúng
   (máy chủ kiểm khoá HMAC, goi_mon_ban.mo_ban) thì tab Tại quầy chuyển sang
   chế độ gọi món của ĐÚNG quầy đó: nút "+" trên từng món, đồ uống mở bảng
   chọn đá đường, thanh giỏ dưới cùng, giỏ có ghi chú, tên để quầy gọi, mã
   giới thiệu, nút Gọi món. Link sai hay không có thì tab giữ chế độ xem.

   Giỏ này TÁCH khỏi giỏ đặt bánh (S.CART): đơn tại bàn trả tại quầy khi dùng
   xong, không đi Pancake. Mọi số trên màn là computed từ kho này; giá chỉ để
   hiện, máy chủ tính lại (QT-19). Phụ thuộc bên ngoài tiêm vào để bộ kiểm chạy
   được trong node với Vue thật. */
import {reactive, computed} from '../lib/vue.esm-browser.prod.js';
import * as T from '../kho/thuan.js';

export const NHIP_TRANG_THAI = 10000;
export const SL_TOI_DA = 20;

/* ?diem=TCV&ban=5&k=... -> {diem, ban, k} hoặc null. THUẦN. */
export function docLinkBan(timKiem) {
  let q;
  try { q = new URLSearchParams(String(timKiem || '')); } catch (e) { return null; }
  const diem = String(q.get('diem') || '').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 20);
  const ban = String(q.get('ban') || '').trim();
  const k = String(q.get('k') || '').trim().toLowerCase();
  if (!diem || !/^\d{1,3}$/.test(ban) || !/^[0-9a-f]{16}$/.test(k)) return null;
  return {diem, ban: Number(ban), k};
}

/* Khoá một dòng giỏ: cùng món cùng lựa chọn thì gộp. THUẦN. */
export function khoaDong(ma, tc) {
  const p = Object.keys(tc || {}).sort().filter(k => tc[k]).map(k => k + '=' + tc[k]);
  return ma + '|' + p.join(';');
}

/* Số đã có trong giỏ của một mã (mọi lựa chọn). THUẦN. */
export function daCo(gio, ma) { return (gio || []).filter(x => x.ma === ma).reduce((a, x) => a + x.sl, 0); }

/* Chuỗi lựa chọn hiện trên dòng giỏ, đúng thứ tự nhóm của món. THUẦN. */
export function chuTuyChon(tc, nhom) {
  return (nhom || []).map(n => (tc || {})[n.nhom]).filter(Boolean).join(', ');
}

/* Phần tab Tại quầy đang bày: quầy chọn, món theo chip, tổng bánh còn. THUẦN
   theo S và G. Bánh trên tủ (đếm "còn") và đồ uống (không đếm) chung một lưới;
   chip cố định Tất cả, Bánh trên tủ, Đồ uống (chip Đồ uống chỉ có khi quầy có
   đồ uống). Mở từ QR một bàn thì chỉ còn đúng quầy của bàn đó. */
export function dungQuayHien(S, G, t) {
  let quay = (S.STORE && S.STORE.quay) || [];
  if (G && G.ban && G.ban.ok) quay = quay.filter(q => q.ma === G.ban.diem);
  if (!quay.length) return null;
  const chon = quay.find(q => q.ma === S.quayChon) || quay[0];
  const banh = (chon.mon || []).map(m => ({...m, loai: 'banh'}));
  const nuoc = (chon.do_uong || []).map(m => ({...m, loai: 'nuoc'}));
  const ds = banh.concat(nuoc);
  const mon = ds.filter(m => !S.nhomQuay || m.loai === S.nhomQuay);
  const nhom = [{n: '', ten: t('tat_ca_muc', 'Tất cả'), so: ds.length}, {n: 'banh', ten: t('quay_chip_banh', 'Bánh trên tủ'), so: banh.length}];
  if (nuoc.length) nhom.push({n: 'nuoc', ten: t('quay_chip_nuoc', 'Đồ uống'), so: nuoc.length});
  return {quay, chon, mon, tong: banh.reduce((a, m) => a + (m.con || 0), 0), soBanh: banh.length, nhom};
}

export function taoGoiBan(moiTruong, S) {
  const {t, doc, ghi, luuTru = null, ngauNhien = null, hen = (f, ms) => setTimeout(f, ms), huyHen = id => clearTimeout(id),
    timKiem = () => '', toast = () => {}} = moiTruong;

  const G = reactive({
    link: docLinkBan(timKiem()),
    ban: null, daKiem: false,
    gio: [],
    chon: null,          // đồ uống đang chọn đá đường: {m, tc}
    moGio: false,
    ghiChu: '', ten: '', gt: '', gtHien: '',
    nonce: '', dangGui: false, loi: '',
    don: [],             // [{ma, token, tt}]
  });

  const khoaLuu = () => (G.link ? 'vgb-goi-ban-' + G.link.diem + '-' + G.link.ban : '');
  function luuDon() {
    if (!luuTru || !khoaLuu()) return;
    try { luuTru.setItem(khoaLuu(), JSON.stringify(G.don.slice(-10).map(d => ({ma: d.ma, token: d.token})))); } catch (e) { /* bỏ qua */ }
  }
  function docDonLuu() {
    if (!luuTru || !khoaLuu()) return [];
    try {
      const v = JSON.parse(luuTru.getItem(khoaLuu()) || '[]');
      return Array.isArray(v) ? v.filter(d => d && /^[A-Za-z0-9-]{3,40}$/.test(d.ma || '') && /^[0-9a-f]{32}$/.test(d.token || '')).slice(-10) : [];
    } catch (e) { return []; }
  }

  /* Đang ở chế độ gọi món (link đúng) và quầy đang mở cửa. */
  const cheDo = computed(() => (!G.ban || !G.ban.ok) ? '' : (G.ban.mo_cua ? 'goi' : 'dong'));
  const nhanBan = computed(() => (G.ban && G.ban.ok) ? (G.ban.ten + ' · ' + t('goi_ban_ban', 'Bàn') + ' ' + G.ban.ban) : '');
  const soMon = computed(() => G.gio.reduce((a, x) => a + x.sl, 0));
  const tong = computed(() => G.gio.reduce((a, x) => a + x.gia * x.sl, 0));
  const quayCua = () => ((S.STORE && S.STORE.quay) || []).find(q => G.ban && q.ma === G.ban.diem) || null;

  async function kiemLink() {
    if (!G.link) { G.daKiem = true; return null; }
    let m = null;
    try { m = await doc('vagabond.goi_mon_ban.mo_ban', {diem: G.link.diem, ban: G.link.ban, k: G.link.k}); } catch (e) { m = null; }
    G.ban = m && m.ok ? m : {ok: 0};
    G.daKiem = true;
    if (G.ban.ok) {
      S.quayChon = G.ban.diem; S.nhomQuay = '';
      G.don = docDonLuu().map(d => ({ma: d.ma, token: d.token, tt: null}));
      if (G.don.length) void hoiTrangThai();
    }
    return G.ban;
  }

  /* Món còn thêm được bao nhiêu: bánh theo số "còn", đồ uống theo trần dòng. */
  function conThem(m) {
    const da = daCo(G.gio, m.ma);
    return m.loai === 'nuoc' ? SL_TOI_DA - da : Math.min(SL_TOI_DA, Number(m.con) || 0) - da;
  }
  /* Bấm "+" trên thẻ: đồ uống có lựa chọn thì mở bảng chọn, còn lại thêm luôn. */
  function bamThem(m) {
    if (cheDo.value !== 'goi') return false;
    if (conThem(m) <= 0) {
      toast(m.loai === 'nuoc' ? t('goi_ban_qua_nhieu', 'Mỗi lần gọi tối đa 20 ly một món.')
        : t('goi_ban_het_con', 'Món này trên tủ chỉ còn {so}.', {so: Number(m.con) || 0}));
      return false;
    }
    if (m.loai === 'nuoc' && (m.tc || []).length) { G.chon = {m, tc: {}}; return 'chon'; }
    them(m, {});
    return true;
  }
  function chonTc(nhom, lc) {
    if (!G.chon) return;
    G.chon.tc[nhom] = G.chon.tc[nhom] === lc ? '' : lc;
  }
  function xongChon() {
    if (!G.chon) return;
    them(G.chon.m, G.chon.tc);
    G.chon = null;
  }
  function them(m, tc) {
    const sach = {};
    (m.tc || []).forEach(n => { if (tc && tc[n.nhom] && n.lua_chon.includes(tc[n.nhom])) sach[n.nhom] = tc[n.nhom]; });
    const k = khoaDong(m.ma, sach);
    const cu = G.gio.find(x => x.khoa === k);
    if (cu) cu.sl += 1;
    else G.gio.push({khoa: k, ma: m.ma, ten: m.ten, gia: Number(m.gia) || 0, sl: 1, tc: sach, nhom: m.tc || [], loai: m.loai, con: m.con});
    if (!G.nonce) G.nonce = T.taoNonce(ngauNhien);
    G.loi = '';
    toast(t('goi_ban_da_them', 'Đã thêm {ten}', {ten: m.ten}));
  }
  function doiSl(i, d) {
    const x = G.gio[i]; if (!x) return;
    if (d > 0) {
      const m = {ma: x.ma, loai: x.loai, con: x.con};
      if (conThem(m) <= 0) return;
    }
    x.sl += d;
    if (x.sl <= 0) G.gio.splice(i, 1);
    if (!G.gio.length) G.moGio = false;
  }

  /* Mã giới thiệu: số điện thoại nhân viên. Rời ô thì hỏi tên nhân viên qua
     cửa vagabond.gioi_thieu.kiem; lỗi hay cửa chưa có thì im lặng, không bao
     giờ chặn gọi món. Cùng luật ô Mã giới thiệu của bước đặt bánh. */
  const soGt = () => { const so = String(G.gt || '').replace(/\D/g, ''); return so.length >= 8 && so.length <= 12 ? so : ''; };
  let luotGt = 0;
  async function kiemGt() {
    const so = soGt(), luot = ++luotGt;
    G.gtHien = '';
    if (!so) return;
    let m = null;
    try { m = await ghi('vagabond.gioi_thieu.kiem', {sdt: so}, {choXemThu: true}); } catch (e) { return; }
    if (luot !== luotGt || so !== soGt() || !m || typeof m !== 'object') return;
    const ten = String(m.ten || '').trim();
    G.gtHien = ten ? t('goi_ban_gt_co', 'Nhân viên giới thiệu: {ten}', {ten}) : '';
  }

  async function goiMon() {
    if (G.dangGui || cheDo.value !== 'goi' || !G.gio.length) return null;
    if (!G.nonce) G.nonce = T.taoNonce(ngauNhien);
    G.dangGui = true; G.loi = '';
    const than = {diem: G.ban.diem, ban: G.ban.ban, k: G.link.k, nonce: G.nonce,
      mon: JSON.stringify(G.gio.map(x => ({ma: x.ma, sl: x.sl, tc: x.tc}))),
      ghi_chu: String(G.ghiChu || '').trim().slice(0, 300), ten: String(G.ten || '').trim().slice(0, 40), sdt_gioi_thieu: soGt()};
    let m = null;
    try { m = await ghi('vagabond.goi_mon_ban.goi', than); } catch (e) { m = null; }
    G.dangGui = false;
    if (!m || !m.ok) {
      G.loi = (m && m.cau) || t('goi_ban_loi', 'Chưa gửi được. Quý khách thử lại hoặc nhắn nhân viên gần nhất.');
      if (m && m.tai_lai && moiTruong.napQuay) void moiTruong.napQuay();
      return m;
    }
    if (!G.don.some(d => d.ma === m.ma)) G.don.push({ma: m.ma, token: m.token, tt: {trang_thai: 'Chờ nhận', mon: [], ban: G.ban.ban}});
    luuDon();
    G.gio.splice(0); G.ghiChu = ''; G.nonce = ''; G.moGio = false;
    hen(hoiTrangThai, 1500);
    return m;
  }

  let henTt = null;
  async function hoiTrangThai() {
    huyHen(henTt); henTt = null;
    for (const d of G.don) {
      if (d.tt && ['Đã nhận', 'Từ chối', 'Hết hạn'].includes(d.tt.trang_thai) && d.xong) continue;
      let m = null;
      try { m = await doc('vagabond.goi_mon_ban.trang_thai', {ma: d.ma, token: d.token}); } catch (e) { m = null; }
      if (m && m.ok) { d.tt = m; d.xong = m.trang_thai !== 'Chờ nhận'; }
    }
    if (G.don.some(d => !d.tt || d.tt.trang_thai === 'Chờ nhận')) henTt = hen(hoiTrangThai, NHIP_TRANG_THAI);
  }
  /* Câu trạng thái một đơn cho khách. THUẦN theo đơn. */
  function cauDon(d) {
    const tt = (d.tt && d.tt.trang_thai) || 'Chờ nhận';
    if (tt === 'Đã nhận') return t('goi_ban_tt_nhan', 'Đã nhận lúc {gio}, đang pha chế', {gio: (d.tt && d.tt.nhan_luc) || ''});
    if (tt === 'Từ chối') return t('goi_ban_tt_tu_choi', 'Quầy từ chối: {ly_do}', {ly_do: (d.tt && d.tt.ly_do) || ''});
    if (tt === 'Hết hạn') return t('goi_ban_tt_het_han', 'Quầy đang bận, quý khách nhắn nhân viên gần nhất');
    return t('goi_ban_tt_cho', 'Chờ quầy nhận');
  }

  return {G, cheDo, nhanBan, soMon, tong, quayCua, kiemLink, conThem, bamThem, chonTc, xongChon, them, doiSl,
    kiemGt, goiMon, hoiTrangThai, cauDon, chuTuyChon};
}
