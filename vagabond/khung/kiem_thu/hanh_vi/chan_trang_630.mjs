/* Ca kiểm HÀNH VI v630: chân trang trang đặt bánh bản Vue (mẫu 4 anh Việt
   duyệt 02/11/2026).

   MOUNT THẬT thành phần ChanTrang bằng Vue thật (bản ESM trong repo) qua một
   bộ dựng cây tối giản (createRenderer của chính Vue, nút là đối tượng JS),
   nên phản ứng, data(), sự kiện onClick đều là của Vue chứ không gọi render()
   tay. Kho là kho thật (taoKho) nạp cấu hình qua napCauHinh với mạng giả; nội
   dung web nạp bằng apNoiDung thật. Mỗi ca dựng đúng chuỗi khách thấy: dữ liệu
   tới, chân trang vẽ, khách bấm. Phần bố cục 1280/390 (không cuộn ngang, vùng
   bấm 44) đo trên Chromium thật, xem PR.

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/chan_trang_630.mjs */
import {readFileSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {createRenderer, h, nextTick} from '../../../public/web_vue/lib/vue.esm-browser.prod.js';
import {taoKho} from '../../../public/web_vue/banh/kho-banh.js';
import {ND, t, tMon, apNoiDung} from '../../../public/web_vue/kho/chu.js';
import {ChanTrang, locChinhSach} from '../../../public/web_vue/banh/chan-trang.js';

const GOC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..');

let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; } catch (e) { hong++; loi.push(ten + '\n      ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n      ') : e)); }
}
function la(ten, co, can) { const a = JSON.stringify(co), b = JSON.stringify(can); if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b); }
function dung(ten, x) { if (!x) throw new Error(ten); }

/* ---------- bộ dựng cây của Vue, nút là đối tượng thường ---------- */
const nut = (the) => ({the, props: {}, con: [], cha: null});
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
const lop = c => n => String(n.props.class || '').split(' ').includes(c);
const id = i => n => n.props.id === i;
const mot = (goc, dk, ten) => { const ds = tim(goc, dk); la('đúng một ' + ten, ds.length, 1); return ds[0]; };

/* ---------- kho thật, mạng giả ---------- */
const CAU_HINH = {
  mien_phi_tu: 1000000, pixel_id: '',
  lien_he: {dien_thoai: '0931 224 334', dien_thoai_so: '0931224334', email: 'hello@thevagabondpatisserie.com',
    zalo: 'https://zalo.me/0931224334', messenger: '', facebook: 'https://facebook.com/thevagabond.saigon', instagram: '', tiktok: ''},
  chinh_sach: [{duong: '/chinh-sach-bao-mat', ten: 'Chính sách bảo mật', khoa: 'chinh_sach_bao_mat'},
    {duong: 'javascript:alert(1)', ten: 'Bẩn'}, {duong: '/giao-hang', ten: 'Giao hàng và đổi trả'}]
};
function dungKho(cauHinh) {
  const vet = [];
  const kho = taoKho({t, tMon, doc: async (p) => { vet.push(p); return p === 'vagabond.don_web.cau_hinh_web' ? JSON.parse(JSON.stringify(cauHinh)) : {}; },
    ghi: async () => ({}), luuTru: null, suKien: () => {}, ngauNhien: () => null, xemThu: () => false, mxh: () => '', nd: ND,
    cookie: () => '', timKiem: () => '', bayGio: () => new Date('2026-11-02T09:00:00+07:00'), hen: () => 0, huyHen: () => {}});
  return {kho, vet};
}
const CUA_HANG = [
  {id: 'bep-tan-son-hoa', ten: 'Bếp Tân Sơn Hoà', dia_chi: '307/1 Nguyễn Văn Trỗi', gio_mo_cua: '', chi_duong: '', hien: false},
  {id: 'cua-hang-sai-gon', ten: 'The Vagabond District 1', dia_chi: '9 Trần Cao Vân, P. Sài Gòn', gio_mo_cua: 'Mở cửa 9:00 - 21:00 mỗi ngày',
    chi_duong: 'https://maps.app.goo.gl/abc', hien: true},
  {id: 'nha-van-hoa-thanh-nien', ten: 'Nhà Văn Hóa Thanh Niên', dia_chi: '21 Phạm Ngọc Thạch', gio_mo_cua: '', chi_duong: 'javascript:alert(1)', hien: true},
  {id: 'chua-dia-chi', ten: 'Điểm chưa có địa chỉ', dia_chi: '', hien: true}
];
function napNoiDung(lienHe, cuaHang = CUA_HANG, nhan = {}) {
  apNoiDung({nhan, san_pham: {}, lien_he: lienHe, khoi: [], thong_tin: {cua_hang: cuaHang}, ve: {}});
}
async function gan(kho, go) {
  const goc = nut('goc');
  const app = createApp({render: () => h(ChanTrang, {kho, go})});
  app.mount(goc);
  await nextTick();
  return {goc, app};
}

await ca('mạng xã hội: chỉ vẽ mạng có link https trong thẻ Liên hệ, đúng thứ tự IG, FB, Zalo, TikTok; link bẩn bị bỏ', async () => {
  const {kho} = dungKho(CAU_HINH);
  await kho.napCauHinh();
  napNoiDung({...CAU_HINH.lien_he, instagram: 'http://instagram.com/x', tiktok: 'https://www.tiktok.com/@thevagabond'});
  const {goc} = await gan(kho);
  const nuts = tim(goc, lop('ctr-mxh-nut'));
  la('các mạng hiện', nuts.map(n => n.props['data-mxh']), ['facebook', 'zalo', 'tiktok']);
  la('link', nuts.map(n => n.props.href), ['https://facebook.com/thevagabond.saigon', 'https://zalo.me/0931224334', 'https://www.tiktok.com/@thevagabond']);
  dung('có nhãn đọc màn hình', nuts.every(n => n.props['aria-label']));
  dung('mở tab mới an toàn', nuts.every(n => n.props.target === '_blank' && /noopener/.test(n.props.rel)));
  /* Marketing xoá hết link mạng xã hội: không còn hàng ô trống. */
  napNoiDung({dien_thoai: '0931 224 334', zalo: '', facebook: '', instagram: '', tiktok: ''});
  await nextTick();
  la('không còn ô mạng xã hội', tim(goc, lop('ctr-mxh-nut')).length, 0);
  la('không còn hàng mạng xã hội', tim(goc, id('ctrMxh')).length, 0);
});

await ca('cột Cửa hàng: chỉ cửa hàng đang hiện và có địa chỉ; Chỉ đường chỉ khi link https', async () => {
  const {kho} = dungKho(CAU_HINH);
  await kho.napCauHinh();
  napNoiDung(CAU_HINH.lien_he);
  const {goc} = await gan(kho);
  const ds = tim(goc, lop('ctr-ch'));
  la('cửa hàng hiện', ds.map(n => n.props['data-cua-hang']), ['cua-hang-sai-gon', 'nha-van-hoa-thanh-nien']);
  dung('có tên, địa chỉ, giờ', chu(ds[0]).includes('The Vagabond District 1') && chu(ds[0]).includes('9 Trần Cao Vân') && chu(ds[0]).includes('9:00 - 21:00'));
  const cd = tim(goc, lop('ctr-chi-duong'));
  la('chỉ một nút chỉ đường (link javascript bị bỏ)', cd.map(n => n.props.href), ['https://maps.app.goo.gl/abc']);
  la('chữ nút', chu(cd[0]), 'Chỉ đường ›');
  /* Marketing tắt hết cửa hàng: cột biến mất, không để tiêu đề trơ trọi. */
  napNoiDung(CAU_HINH.lien_he, CUA_HANG.map(c => ({...c, hien: false})));
  await nextTick();
  la('không còn mục Cửa hàng', tim(goc, n => n.props['data-muc'] === 'cua_hang').length, 0);
});

await ca('điện thoại: mục Cửa hàng mở sẵn, Liên hệ/Mua bánh/Chính sách gấp; bấm là mở, bấm lại là gấp', async () => {
  const {kho} = dungKho(CAU_HINH);
  await kho.napCauHinh();
  napNoiDung(CAU_HINH.lien_he);
  const {goc} = await gan(kho);
  const trangThai = () => Object.fromEntries(tim(goc, lop('ctr-muc')).map(m => [m.props['data-muc'],
    [lop('mo')(m), mot(m, lop('ctr-mo'), 'nút mở').props['aria-expanded']]]));
  la('ban đầu', trangThai(), {cua_hang: [true, 'true'], lien_he: [false, 'false'], mua: [false, 'false'], chinh_sach: [false, 'false']});
  const nutLh = mot(tim(goc, n => n.props['data-muc'] === 'lien_he')[0], lop('ctr-mo'), 'nút Liên hệ');
  la('nút trỏ đúng vùng', nutLh.props['aria-controls'], 'ctrLienHe');
  mot(goc, id('ctrLienHe'), 'vùng Liên hệ');
  nutLh.props.onClick({});
  await nextTick();
  la('mở Liên hệ', trangThai().lien_he, [true, 'true']);
  la('Cửa hàng vẫn mở', trangThai().cua_hang, [true, 'true']);
  nutLh.props.onClick({});
  await nextTick();
  la('gấp lại', trangThai().lien_he, [false, 'false']);
  const nutCh = mot(tim(goc, n => n.props['data-muc'] === 'cua_hang')[0], lop('ctr-mo'), 'nút Cửa hàng');
  nutCh.props.onClick({});
  await nextTick();
  la('gấp Cửa hàng', trangThai().cua_hang, [false, 'false']);
});

await ca('dòng miễn phí giao chỉ hiện khi ngưỡng > 0; ngưỡng 0 thì nói chưa gồm phí vận chuyển', async () => {
  const {kho} = dungKho(CAU_HINH);
  napNoiDung(CAU_HINH.lien_he);
  const {goc} = await gan(kho);
  /* Chưa nạp cấu hình: ngưỡng 0. */
  la('trước khi nạp', chu(mot(goc, id('fNotePhi'), 'dòng phí')), '✓Giá đã gồm thuế GTGT, chưa gồm phí vận chuyển');
  await kho.napCauHinh();
  await nextTick();
  const camKet = tim(goc, id('ctrCamKet'))[0];
  const dong = camKet.con.map(chu);
  la('các dòng cam kết', dong, ['✓Giá đã gồm thuế GTGT', '✓Miễn phí giao cho đơn từ 1.000.000 đ', '✓Xuất hoá đơn điện tử theo yêu cầu',
    '✓Giá và tồn kho thay đổi theo mùa và nguyên liệu nhập khẩu']);
  /* Marketing sửa câu nhưng giữ chỗ điền {tien}: máy vẫn điền đúng số. */
  napNoiDung(CAU_HINH.lien_he, CUA_HANG, {ct630_mien_phi: 'Freeship đơn từ {tien}'});
  await nextTick();
  la('câu đã sửa', chu(mot(goc, id('fNotePhi'), 'dòng phí')), '✓Freeship đơn từ 1.000.000 đ');
  const {kho: kho0} = dungKho({...CAU_HINH, mien_phi_tu: 0});
  await kho0.napCauHinh();
  const {goc: goc0} = await gan(kho0);
  dung('ngưỡng 0 không nói miễn phí', !chu(goc0).includes('Miễn phí giao') && !chu(goc0).includes('Freeship'));
  la('ngưỡng 0', chu(mot(goc0, id('fNotePhi'), 'dòng phí')), '✓Giá đã gồm thuế GTGT, chưa gồm phí vận chuyển');
});

await ca('chính sách: vẽ đúng link nội bộ đang hiện, bỏ link bẩn; trang /web_moi giữ khách trong bản đang xem', async () => {
  const {kho} = dungKho(CAU_HINH);
  await kho.napCauHinh();
  napNoiDung(CAU_HINH.lien_he);
  globalThis.location = {pathname: '/banh'};
  const {goc} = await gan(kho);
  const a = tim(mot(goc, id('fChinhSach'), 'hàng chính sách'), n => n.the === 'a');
  la('link', a.map(n => [n.props.href, chu(n)]), [['/chinh-sach-bao-mat', 'Chính sách bảo mật'], ['/giao-hang', 'Giao hàng và đổi trả']]);
  la('bản /web_moi', locChinhSach(CAU_HINH.chinh_sach, '/web_moi/banh').map(c => c.duong), ['/web_moi/chinh-sach-bao-mat', '/web_moi/giao-hang']);
  delete globalThis.location;
  const {kho: kho0} = dungKho({...CAU_HINH, chinh_sach: []});
  await kho0.napCauHinh();
  const {goc: goc0} = await gan(kho0);
  la('không có chính sách thì không có mục', tim(goc0, n => n.props['data-muc'] === 'chinh_sach').length, 0);
});

await ca('pháp lý và liên hệ giữ đủ: tên công ty, mã số thuế, hai địa chỉ, điện thoại tel:, email mailto:, Zalo', async () => {
  const {kho} = dungKho(CAU_HINH);
  await kho.napCauHinh();
  napNoiDung(CAU_HINH.lien_he);
  const {goc} = await gan(kho);
  const tat = chu(goc);
  for (const x of ['Công ty TNHH Patisserie Vagabond', 'Mã số thuế 0318561568', '9 Trần Cao Vân, Phường Sài Gòn (Quận 1 cũ)', '307/1 Nguyễn Văn Trỗi, Phường Tân Sơn Hoà']) dung('có ' + x, tat.includes(x));
  dung('có năm', /© 20\d\d Công ty/.test(chu(mot(goc, id('fPhapNhan'), 'khối pháp lý'))));
  const lh = mot(goc, id('fLienHe'), 'khối liên hệ');
  la('link liên hệ', tim(lh, n => n.the === 'a').map(n => n.props.href), ['tel:0931224334', 'mailto:hello@thevagabondpatisserie.com', 'https://zalo.me/0931224334']);
  /* Email điền sai dạng: không thành mailto; chưa điền số: về số gốc. */
  napNoiDung({email: 'hello at vagabond', zalo: ''});
  await nextTick();
  la('chỉ còn số gốc', tim(tim(goc, id('fLienHe'))[0], n => n.the === 'a').map(n => n.props.href), ['tel:0931224334']);
});

await ca('nút Chọn bánh về đúng danh sách bánh đang xem (mặc định Có sẵn hôm nay); Đặt bàn tới /dat-ban; Mua bánh gọi đúng tab', async () => {
  const {kho} = dungKho(CAU_HINH);
  await kho.napCauHinh();
  napNoiDung(CAU_HINH.lien_he);
  const di = [];
  const {goc} = await gan(kho, tab => di.push(tab));
  const chon = mot(goc, id('ctrChonBanh'), 'nút Chọn bánh');
  kho.S.tab = 'uu_dai'; chon.props.onClick({}); kho.S.tab = 'order'; chon.props.onClick({});
  la('chọn bánh', di, ['today', 'order']);
  la('đặt bàn', mot(goc, id('ctrDatBan'), 'nút Đặt bàn').props.href, '/dat-ban');
  const a = tim(tim(goc, n => n.props['data-muc'] === 'mua')[0], n => n.the === 'a');
  la('các mục', a.map(n => chu(n)), ['Có sẵn hôm nay', 'Đặt bánh trước', 'Ưu đãi', 'Thành viên', 'Bánh sỉ cho quán', 'Tuyển dụng']);
  di.length = 0; let chan = 0;
  a[1].props.onClick({preventDefault: () => { chan++; }});
  la('bấm Đặt bánh trước', [di, chan], [['order'], 1]);
  la('Thành viên là trang riêng, không có tab', [a[3].props.href, a[3].props.onClick], ['/thanh-vien', undefined]);
  /* v630: Bánh sỉ là trang riêng /banh-si, không phải tab của trang đặt bánh. */
  la('Bánh sỉ là trang riêng, không có tab', [a[4].props.href, a[4].props.onClick], ['/banh-si', undefined]);
});

await ca('mọi khoá chữ chân trang gọi lúc vẽ đều có trong sổ nhãn, chữ mặc định trùng sổ nhãn', async () => {
  const so = JSON.parse(readFileSync(path.join(GOC, 'vagabond/public/web_order/chu-mac-dinh.json'), 'utf8'));
  const nhanPy = JSON.parse(execFileSync('python3', ['-B', '-c', `
import ast, json, sys
cay = ast.parse(open(sys.argv[1] + '/vagabond/noi_dung_web.py').read())
for n in cay.body:
    if isinstance(n, ast.Assign) and any(getattr(x, 'id', '') == 'NHAN' for x in n.targets):
        print(json.dumps({k: v['mac_dinh'] for k, v in ast.literal_eval(n.value).items()}))
`, GOC]).toString());
  const macDinh = k => (so[k] ? so[k].mac_dinh : nhanPy[k]);
  /* Ghi lại mọi khoá t() thật sự đọc khi vẽ, kể cả mục ẩn hiện theo dữ liệu. */
  const doc = new Set();
  const {kho} = dungKho(CAU_HINH);
  await kho.napCauHinh();
  napNoiDung(CAU_HINH.lien_he);
  ND.nhan = new Proxy({}, {get: (o, k) => { if (typeof k === 'string' && /^[a-z][a-z0-9_]*$/.test(k)) doc.add(k); return undefined; }});
  const {goc} = await gan(kho);
  dung('vẽ ra chữ', chu(goc).length > 200);
  /* Vẽ thêm các nhánh ẩn hiện theo dữ liệu: ngưỡng 0, có hàng mùa, có tiệc. */
  const {kho: kho0} = dungKho({...CAU_HINH, mien_phi_tu: 0});
  await kho0.napCauHinh();
  kho0.S.MUA = {co: 1, ten_mua: 'Mùa thử', mon: [{ma: 'M1', ten: 'Hộp', gia: 1, con: 1, het: 0}]};
  ND.khoi = [{id: 'tiec1', loai: 'tiec', hien: true, tieu_de: 'Tiệc thử', bat_dau: '2099-01-01'}];
  const {goc: goc0} = await gan(kho0);
  la('mục khi có mùa và tiệc', tim(tim(goc0, n => n.props['data-muc'] === 'mua')[0], n => n.the === 'a').map(n => n.props.href),
    ['#/', '#/dat-truoc', '#/in-season', '#/uu-dai', '#/tiec', '/thanh-vien', '/banh-si', '#/tuyen-dung']);
  ND.khoi = [];
  const thieu = [...doc].filter(k => macDinh(k) == null);
  la('khoá thiếu trong sổ nhãn', thieu, []);
  dung('đọc đủ khoá mới', ['ct630_moi_tieu_de', 'ct630_chon_banh', 'ct630_mien_phi', 'ct630_hoa_don', 'ct630_cua_hang'].every(k => doc.has(k)));
  const nguon = readFileSync(path.join(GOC, 'vagabond/public/web_vue/banh/chan-trang.js'), 'utf8');
  const cap = [...nguon.matchAll(/\bt\(\s*'([a-z0-9_]+)'\s*,\s*'((?:[^'\\]|\\.)*)'/g)];
  dung('dò được khoá trong nguồn', cap.length >= 20);
  for (const [, k, d] of cap) la('mặc định ' + k, d, macDinh(k));
  for (const [k] of cap.map(m => [m[1]])) dung('khoá nguồn ' + k + ' được đọc khi vẽ', doc.has(k));
  for (const k of Object.keys(so).filter(k => k.startsWith('ct630_'))) {
    dung(k + ' không có đại từ cũ', !/(^|[^\p{L}])(tiệm|mình|anh chị|em)([^\p{L}]|$)/iu.test(so[k].mac_dinh));
    dung(k + ' không có markup', !/[<>]/.test(so[k].mac_dinh));
    dung(k + ' không dấu gạch dài', !/[\u2013\u2014]/.test(so[k].mac_dinh + so[k].ten));
  }
  ND.nhan = {};
});

console.log(`chan_trang_630: ${dat} ca dat, ${hong} ca hong`);
if (hong) { console.log('  ' + loi.join('\n  ')); process.exit(1); }
