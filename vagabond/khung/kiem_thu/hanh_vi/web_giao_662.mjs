/* v662 WEBORDER (anh Việt chốt 15/11/2026): tab Tại quầy trên trang chủ, không có
   link QR bàn, là đơn giao của quầy. Dựng ĐÚNG bộ mount thật của goi_mon_ban_638.mjs
   (Vue thật, kho thật, khuôn thật), mạng giả. Khách bấm đúng chuỗi: mở tab, bấm +,
   mở giỏ, chọn cách nhận, gõ tên, số, địa chỉ, chọn ô đồng ý, bấm Đặt và trả trước.

   Gốc chú thích của bộ mount (v638):

   MOUNT THẬT bằng Vue thật của repo qua bộ dựng cây tối giản (như
   thanh_toan_web_638.mjs): cắt ĐÚNG khối <main id="store"> của khuôn MAU, kho
   là kho thật (taoKho, kho-goi-ban), phần tab Tại quầy tính bằng đúng
   dungQuayHien mà app.js dùng, thành phần GoiTaiBan thật. Mạng giả. Khách bấm
   đúng chuỗi: mở link, bấm +, chọn đá đường, mở giỏ, gõ ghi chú, tên, mã giới
   thiệu, rời ô, bấm Gọi món; đọc đúng thân gửi máy chủ, rồi trạng thái đơn.
   Hai khối nội dung marketing (khoi-noi-dung, tieu-de-muc) thay bằng khối rỗng:
   chúng không dính gì tới gọi món.

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/goi_mon_ban_638.mjs */
import {createRenderer, nextTick, computed} from '../../../public/web_vue/lib/vue.esm-browser.prod.js';
import {MAU} from '../../../public/web_vue/banh/mau.js';
import {taoKho} from '../../../public/web_vue/banh/kho-banh.js';
import {dungQuayHien, tenQuayHaiDong} from '../../../public/web_vue/banh/kho-goi-ban.js';
import {GoiTaiBan, GoiTaiBanNoi} from '../../../public/web_vue/banh/goi-tai-ban.js';
import {KenhNoi} from '../../../public/web_vue/banh/noi-dung.js';
import {gomSize, tachSize, khopTim, chipNhom, LY_DO_GOI} from '../../../public/web_vue/banh/kho-goi-ban.js';
import {AnhMon} from '../../../public/web_vue/banh/thanh-phan.js';
import {t, tMon} from '../../../public/web_vue/kho/chu.js';
import * as T from '../../../public/web_vue/kho/thuan.js';

let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; console.log('  DAT   ' + ten); } catch (e) { hong++; loi.push(ten + '\n      ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n      ') : e)); }
}
function la(ten, co, can) { const a = JSON.stringify(co), b = JSON.stringify(can); if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b); }
function dung(ten, x) { if (!x) throw new Error(ten); }

const nut = the => ({the, props: {}, con: [], cha: null, nghe: {}, value: '',
  addEventListener(ev, f) { (this.nghe[ev] = this.nghe[ev] || []).push(f); },
  removeEventListener(ev, f) { this.nghe[ev] = (this.nghe[ev] || []).filter(x => x !== f); }});
const {createApp} = createRenderer({
  createElement: the => nut(the),
  createText: chu => ({chu, cha: null}),
  createComment: chu => ({ghiChu: chu, cha: null}),
  setText: (n, chu) => { n.chu = chu; },
  setElementText: (n, chu) => { n.con = chu ? [{chu, cha: n}] : []; },
  insert: (con, cha, moc) => {
    if (con.cha) con.cha.con.splice(con.cha.con.indexOf(con), 1);
    const i = moc ? cha.con.indexOf(moc) : -1;
    if (i >= 0) cha.con.splice(i, 0, con); else cha.con.push(con);
    con.cha = cha;
  },
  remove: con => { if (con.cha) { con.cha.con.splice(con.cha.con.indexOf(con), 1); con.cha = null; } },
  parentNode: n => n.cha,
  nextSibling: n => (n.cha ? n.cha.con[n.cha.con.indexOf(n) + 1] || null : null),
  patchProp: (n, k, cu, moi) => { if (moi == null) delete n.props[k]; else n.props[k] = moi; },
  setScopeId: () => {}, insertStaticContent: () => { throw new Error('không dùng'); }
});
const chu = n => (n == null ? '' : n.chu != null ? n.chu : (n.con || []).map(chu).join(''));
function tim(n, dk, ra = []) { if (!n || !n.con) return ra; if (n.the && dk(n)) ra.push(n); n.con.forEach(x => tim(x, dk, ra)); return ra; }
const theoId = (goc, i) => tim(goc, n => n.props.id === i)[0];
const cho = async () => { for (let i = 0; i < 5; i++) { await nextTick(); await new Promise(r => setTimeout(r, 0)); } };
function go(n, gt) { n.value = gt; (n.nghe.input || []).forEach(f => f({target: n})); }
const bam = async n => { dung('có nút để bấm', n); n.props.onClick(); await cho(); };

/* v-model của Vue hỏi document.activeElement lúc cập nhật ô; trình duyệt nào
   cũng có, node thì không. Chỉ cấp đúng ô đó, không dựng DOM giả. */
globalThis.document = globalThis.document || {activeElement: null};

/* v639: phần nổi (thanh giỏ, bảng chọn, giỏ, chuông) nằm NGOÀI main để không bị
   dải tab đè; cắt cả hai khối của khuôn thật. */
const KHOI = MAU.match(/<main id="store"[\s\S]*?<\/main>/)[0] + MAU.match(/<goi-tai-ban-noi[^>]*>/)[0];
dung('cắt được khối Tại quầy', KHOI.includes('storeBody') && KHOI.includes('<goi-tai-ban ') && KHOI.includes('<goi-tai-ban-noi'));
const Rong = {template: '<span></span>', props: ['viTri', 'dong']};


const STORE = {ngay: '2026-11-15', cap_nhat: '2026-11-15 10:00', quay: [
  {ma: 'TCV', ten: 'The Vagabond District 1', ten_ngan: 'District 1', dia_chi: '9 Trần Cao Vân',
    mon: [{ma: 'BAWC00115', ten: 'Mousse Chanh Dây', gia: 95000, anh: '', con: 2, nhom: 'Bánh lạnh', tai_ban: 1, giao: 1},
      {ma: 'BKMN00099', ten: 'Mille-feuille', gia: 85000, anh: '', con: 3, nhom: 'Bánh lạnh', tai_ban: 1, giao: 0}],
    do_uong: [
      {ma: 'NUIC00002', ten: 'Kem Vani', gia: 30000, anh: '', nhom: 'Đồ uống', tc: [], tai_ban: 0, giao: 1},
      {ma: 'NUTR00021', ten: 'Trà Hoa Lài', gia: 45000, anh: '', nhom: 'Đồ uống', tc: [], tai_ban: 1, giao: 0}]},
  {ma: 'NVHTN', ten: 'Nhà Văn Hóa Thanh Niên', ten_ngan: 'NVHTN', dia_chi: '21 Phạm Ngọc Thạch', mon: [], do_uong: []}]};

function moiTruong({xemGia = th => ({ok: 1, tien_hang: 125000, giam: 0, phi: 22000, trang_thai_phi: 'chinh_xac', nguong: 500000}),
  tao = () => ({ok: 1, ma_yeu_cau: 'DW-2026-00001', duong_dan: '/banh/xong/' + 'a'.repeat(40)}), store = STORE} = {}) {
  const vet = [], hen = [];
  const mang = {
    'vagabond.kiem_kho.con_tren_quay_web': () => JSON.parse(JSON.stringify(store)),
    'vagabond.don_quay.xem_gia': th => xemGia(th),
    'vagabond.don_quay.tao_don': th => tao(th),
  };
  const mt = {
    t, tMon, bayGio: () => new Date('2026-11-15T10:00:00'),
    hen: (f, ms) => { hen.push({f, ms}); return hen.length; }, huyHen: () => {},
    doc: async (p, th) => { vet.push(['GET', p, th]); return mang[p] ? mang[p](th) : {}; },
    ghi: async (p, th) => { vet.push(['POST', p, th]); return mang[p] ? mang[p](th) : {ok: true}; },
    luuTru: null, suKien: () => {}, nd: {nhan: {}}, timKiem: () => '',
    ngauNhien: n => Array.from({length: n}, () => 7)
  };
  const chayHen = async () => { await nextTick(); const ds = hen.splice(0); for (const x of ds) await x.f(); await cho(); };
  return {mt, vet, chayHen, mang};
}

async function moTrang(o = {}) {
  const m = moiTruong(o);
  const kho = taoKho(m.mt);
  kho.S.tab = 'store';
  await kho.napQuay();
  await kho.goiBan.kiemLink();
  const goc = nut('goc');
  createApp({
    template: '<div>' + KHOI + '</div>',
    components: {AnhMon, GoiTaiBan, GoiTaiBanNoi, KhoiNoiDung: Rong, TieuDeMuc: Rong},
    setup: () => {
      const quayHien = computed(() => dungQuayHien(kho.S, kho.goiBan.G, t));
      return {S: kho.S, kho, t, tMon, tab: computed(() => 'store'), quayHien, nhacQr: computed(() => kho.goiBan.G.daKiem && !!quayHien.value), tenQuayHaiDong,
        gbDauHien: computed(() => !!kho.goiBan.cheDo.value && kho.goiBan.cheDo.value !== 'giao'),
        nhacQrHien: computed(() => kho.goiBan.G.daKiem && !!quayHien.value && !kho.goiBan.cheDo.value),
        tienTom: n => T.tienVN(n), mxh: (k, d) => d, telSo: () => '0931224334', telChu: () => '0931 224 334'};
    }
  }).mount(goc);
  await cho();
  return {...m, kho, goc};
}
const nutThem = goc => tim(goc, n => n.props['data-them']);

await ca('Tab Tại quầy không có QR là đơn giao: chỉ món đã tick Giao (bánh mong manh, món chỉ tick Tại bàn không hiện), có nút +, nhãn cách nhận', async () => {
  const {goc, kho} = await moTrang();
  la('chế độ', kho.goiBan.cheDo.value, 'giao');
  la('chỉ món tick Giao', nutThem(goc).map(n => n.props['data-them']), ['BAWC00115', 'NUIC00002']);
  /* v667 (anh Việt 17/11/2026): bỏ khung chú thích đầu tab; chọn quầy bằng thanh gạt, một dòng nhãn. */
  dung('không còn khung chú thích đầu tab', !theoId(goc, 'gbDau') && !theoId(goc, 'gbNhacQr'));
  dung('có thanh gạt chọn quầy và dòng nhãn', !!theoId(goc, 'quayGat') && !!theoId(goc, 'quayDong'));
});

await ca('Đặt giao: + hai món, mở giỏ hỏi giá máy chủ, gõ tên số địa chỉ, chọn đồng ý, Đặt và trả trước gửi đúng quầy, món, cách nhận, số giảm và phí đã xem; xong thì giỏ trống', async () => {
  const {goc, kho, vet, chayHen} = await moTrang();
  const G = kho.goiBan.G;
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'BAWC00115'));
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'NUIC00002'));
  await bam(theoId(goc, 'gbXemGio'));
  dung('giỏ mở', String(theoId(goc, 'gbGio').props.class).includes('open'));
  la('tiêu đề', chu(theoId(goc, 'gb-gio-tieu')), 'Đặt giao');
  go(theoId(goc, 'gb-web-ten'), 'Lan'); go(theoId(goc, 'gb-web-sdt'), '0909 123 456'); go(theoId(goc, 'gb-web-dc'), '12 Lê Lợi, Quận 1');
  await cho();
  await kho.goiBan.xemGiaWeb(true); await cho();
  dung('dòng phí giao', chu(theoId(goc, 'gbGio')).includes('22.000'));
  await bam(tim(theoId(goc, 'gbGio'), n => n.the === 'button' && n.props.role === 'checkbox')[0]);
  await bam(theoId(goc, 'gbDatWeb'));
  const gui = vet.filter(x => x[1] === 'vagabond.don_quay.tao_don');
  la('gửi một lần', gui.length, 1);
  const don = JSON.parse(gui[0][2].don);
  // Codex #573: gửi đủ ba số khách đã xem (tiền món, giảm, phí giao) để máy chủ đối chiếu cả tiền món.
  la('thân gửi', [don.diem, don.tu_lay, don.ho_ten, don.dien_thoai, don.dia_chi, don.mon.map(x => [x.ma, x.sl]), don.tien_hang_da_xem, don.giam_da_xem, don.phi_da_xem, don.thanh_toan, don.dong_y],
    ['TCV', false, 'Lan', '0909123456', '12 Lê Lợi, Quận 1', [['BAWC00115', 1], ['NUIC00002', 1]], 125000, 0, 22000, 'bank', true]);
  la('giỏ trống sau khi đặt', G.gio.length, 0);
});

await ca('Bấm Đặt hai lần liền chỉ gửi một đơn (H8 loại 4); lần hỏi giá cũ trả lời muộn không ghi đè giá mới (H8 loại 8)', async () => {
  let treo = null, lan = 0;
  const {goc, kho, vet} = await moTrang({xemGia: () => { lan++; if (lan === 1) return new Promise(r => { treo = r; }); return {ok: 1, tien_hang: 95000, giam: 0, phi: 30000, trang_thai_phi: 'chinh_xac'}; },
    tao: () => new Promise(r => setTimeout(() => r({ok: 1, duong_dan: '/banh/xong/' + 'b'.repeat(40)}), 5))});
  const G = kho.goiBan.G;
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'BAWC00115'));
  const cu = kho.goiBan.xemGiaWeb(true);
  await kho.goiBan.xemGiaWeb(true);
  treo({ok: 1, tien_hang: 95000, giam: 0, phi: 11000, trang_thai_phi: 'chinh_xac'}); await cu; await cho();
  la('giá mới giữ nguyên', G.web.gia.phi, 30000);
  G.web.ten = 'Lan'; G.web.sdt = '0909123456'; G.web.diaChi = '12 Lê Lợi, Quận 1'; G.web.dongY = true;
  const a = kho.goiBan.datWeb(), b = kho.goiBan.datWeb();
  await a; await b; await cho();
  la('chỉ một lần gửi', vet.filter(x => x[1] === 'vagabond.don_quay.tao_don').length, 1);
});

await ca('Máy chủ báo tổng đổi: không xoá giỏ, hiện câu, giữ số mới để khách bấm lại', async () => {
  const {goc, kho} = await moTrang({tao: () => ({ok: 0, ly_do: 'gia_doi', tien_hang: 125000, giam: 10000, phi: 22000, cau: 'Tổng tiền vừa cập nhật. Quý khách xem lại rồi bấm gửi.'})});
  const G = kho.goiBan.G;
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'BAWC00115'));
  G.web.ten = 'Lan'; G.web.sdt = '0909123456'; G.web.tuLay = true; G.web.dongY = true;
  await kho.goiBan.xemGiaWeb(true);
  await kho.goiBan.datWeb(); await cho();
  la('giỏ còn', G.gio.length, 1);
  la('câu', G.web.loi, 'Tổng tiền vừa cập nhật. Quý khách xem lại rồi bấm gửi.');
  la('số giảm mới', G.web.gia.giam, 10000);
});

/* ---------- v670 (Minh Vũ 17/11, anh Việt đồng ý): nhóm món như O2O và combo cho đơn giao ---------- */
function storeV670() {
  const st = JSON.parse(JSON.stringify(STORE));
  const q = st.quay[0];
  q.mon.push({ma: 'BKNU00010', ten: 'Canelé', gia: 45000, anh: '', con: 5, nhom: 'Bánh nướng', tai_ban: 1, giao: 1});
  q.do_uong.push({ma: 'NUTR00030', ten: 'Trà Lài Đào', gia: 55000, anh: '', nhom: 'Đồ uống', nhom_goc: 'Trà', tc: [], tai_ban: 1, giao: 1});
  q.combo = [
    {ma: 'KMCB0001', ten: 'Combo Trà và Canelé', gia: 89000, goc: 100000, con: 5, tai_ban: 1, giao: 1, con_giao: 1,
      thanh_phan: [{ma: 'NUTR00030', ten: 'Trà Lài Đào', sl: 1, loai: 'nuoc'}, {ma: 'BKNU00010', ten: 'Canelé', sl: 1, loai: 'banh'}]},
    {ma: 'KMCB0002', ten: 'Combo chỉ bán tại bàn', gia: 70000, goc: 80000, con: 3, tai_ban: 1, giao: 0, thanh_phan: [{ma: 'NUTR00021', ten: 'Trà Hoa Lài', sl: 1}]},
    /* Máy chủ cũ không gửi cờ: Giao coi như KHÔNG bán. */
    {ma: 'KMCB0003', ten: 'Combo bản cũ', gia: 60000, goc: 70000, con: 3, thanh_phan: [{ma: 'BAWC00115', ten: 'Mousse Chanh Dây', sl: 1}]}];
  return st;
}
const chipNho = goc => tim(theoId(goc, 'storeChip'), n => n.the === 'button');

await ca('v670 Tại quầy đặt giao: ở Tất cả bày luôn nhóm món (bánh theo nhóm, đồ uống theo nhóm), chạm nhóm Bánh nướng chỉ còn món nhóm đó', async () => {
  const {goc} = await moTrang({store: storeV670()});
  const ten = chipNho(goc).map(b => chu(b));
  dung('có Mọi nhóm, Bánh lạnh, Bánh nướng và nhóm đồ uống: ' + JSON.stringify(ten),
    ten[0].startsWith('Mọi nhóm') && ten.some(x => x.startsWith('Bánh lạnh')) && ten.some(x => x.startsWith('Bánh nướng')) && ten.some(x => x.startsWith('Trà')));
  dung('Bánh lạnh đứng trước Bánh nướng', ten.findIndex(x => x.startsWith('Bánh lạnh')) < ten.findIndex(x => x.startsWith('Bánh nướng')));
  await bam(chipNho(goc).find(b => chu(b).startsWith('Bánh nướng')));
  la('chỉ món Bánh nướng', nutThem(goc).map(n => n.props['data-them']), ['BKNU00010']);
});

await ca('v670 combo cho đơn giao: chỉ combo máy chủ cho bán Giao (cờ giao), số bộ theo con_giao; thêm vào giỏ rồi Đặt gửi đúng mã combo', async () => {
  const {goc, kho, vet} = await moTrang({store: storeV670()});
  const G = kho.goiBan.G;
  const ma = nutThem(goc).map(n => n.props['data-them']);
  dung('combo bán Giao có nút +', ma.includes('KMCB0001'));
  dung('combo chỉ bán tại bàn và combo bản cũ không bày', !ma.includes('KMCB0002') && !ma.includes('KMCB0003'));
  dung('có tầng Combo', tim(theoId(goc, 'storeTang'), n => n.the === 'button').some(b => b.props['data-tang'] === 'combo'));
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'KMCB0001'));
  await bam(nutThem(goc).find(n => n.props['data-them'] === 'KMCB0001'));
  la('con_giao 1 bộ: bấm lần hai không thêm', G.gio.map(x => [x.ma, x.sl]), [['KMCB0001', 1]]);
  G.web.ten = 'Lan'; G.web.sdt = '0909123456'; G.web.tuLay = true; G.web.dongY = true;
  await kho.goiBan.xemGiaWeb(true);
  await kho.goiBan.datWeb(); await cho();
  const gui = vet.filter(x => x[1] === 'vagabond.don_quay.tao_don');
  la('gửi đúng mã combo', JSON.parse(gui[0][2].don).mon.map(x => [x.ma, x.sl]), [['KMCB0001', 1]]);
});

console.log('\n' + dat + ' ca dat, ' + hong + ' ca hong');
if (hong) { console.log(loi.join('\n')); process.exit(1); }
