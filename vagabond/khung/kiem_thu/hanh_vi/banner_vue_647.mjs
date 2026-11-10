/* Ca kiểm HÀNH VI v647: banner ảnh trên trang đặt bánh và biên nhận (anh Việt
   10/11/2026, Minh Vũ thay ảnh ở thẻ Banner của trình biên tập).

   Dữ liệu banner đi qua ĐÚNG cửa máy chủ: python3 chạy noi_dung_web.chuan_hoa
   (Frappe giả) rồi banner_hien cho biên nhận; không chép tay khối đã lọc. Chạy
   THẬT KhoiNoiDung, BannerAnh của web_vue/banh/noi-dung.js và veBanner của
   web_vue/trang/app.js với Vue thật. Bấm trên trình duyệt thật kiểm ở
   cong_cu/kiem_web_vue_dom.cjs (F45).

   Chạy: node vagabond/khung/kiem_thu/hanh_vi/banner_vue_647.mjs */
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {ND} from '../../../public/web_vue/kho/chu.js';
import {KhoiNoiDung, khachThay, ngayVN} from '../../../public/web_vue/banh/noi-dung.js';
import {veBanner, taoTrang} from '../../../public/web_vue/trang/app.js';
import {createRenderer, nextTick} from '../../../public/web_vue/lib/vue.esm-browser.prod.js';

const GOC = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..');
const HN = ngayVN();
const MAY = JSON.parse(execFileSync('python3', ['-B', '-c', `
import copy, datetime, json, sys
sys.path.insert(0, sys.argv[1])
from vagabond.khung.kiem_thu import nen
nen.gia_lap()
from vagabond import noi_dung_web as nw
hn = datetime.date.fromisoformat(sys.argv[2])
d = lambda n: str(hn + datetime.timedelta(days=n))
def bn(i, vi, **k):
    m = {"id": i, "loai": "banner", "vi_tri": vi, "hien": True, "tieu_de": "Sinh nhật " + i, "anh": "/files/" + i + "-pc.png",
         "anh_dt": "/files/" + i + "-dt.png", "mo_ta_anh": "Cập nhật ngày sinh nhận quà", "lien_ket": "/thanh-vien", "bat_dau": "", "ket_thuc": ""}
    m.update(k)
    return m
nd = copy.deepcopy(nw.MAC_DINH)
nd["khoi"] = [bn("dau", "dau_trang"), bn("khong-dt", "dau_trang", anh_dt=""), bn("ngoai", "dau_trang", lien_ket="https://zalo.me/vagabond"),
    bn("khong-link", "dau_trang", lien_ket=""), bn("an", "dau_trang", hien=False), bn("sap", "dau_trang", bat_dau=d(1)),
    bn("het", "dau_trang", ket_thuc=d(-1)), bn("gio", "gio_hang"), bn("xong", "dat_xong"), bn("xong-het", "dat_xong", ket_thuc=d(-1))] + nd["khoi"]
nd = nw.chuan_hoa(nd)
print(json.dumps({"khoi": nd["khoi"], "xong": nw.banner_hien(nd, "dat_xong", str(hn))}, ensure_ascii=False))
`, GOC, HN]).toString());

let dat = 0, hong = 0;
const loi = [];
async function ca(ten, ham) {
  try { await ham(); dat++; } catch (e) { hong++; loi.push(ten + '\n      ' + (e && e.stack ? e.stack.split('\n').slice(0, 3).join('\n      ') : e)); }
}
function la(ten, co, can) { const a = JSON.stringify(co), b = JSON.stringify(can); if (a !== b) throw new Error(ten + ': được ' + a + ', cần ' + b); }
function dung(ten, x) { if (!x) throw new Error(ten); }
function dung_cay(v) {
  if (v == null || v === false) return null;
  if (Array.isArray(v)) return v.map(dung_cay).filter(Boolean);
  if (typeof v !== 'object') return String(v);
  if (typeof v.type === 'object' && v.type.render) return dung_cay(v.type.render.call(Object.assign({}, v.props || {})));
  const con = typeof v.children === 'string' ? [v.children] : dung_cay(v.children || []);
  return {the: typeof v.type === 'string' ? v.type : '', props: v.props || {}, con};
}
function tim(n, dk, ra = []) {
  if (!n || typeof n === 'string') return ra;
  if (Array.isArray(n)) { n.forEach(x => tim(x, dk, ra)); return ra; }
  if (dk(n)) ra.push(n);
  tim(n.con, dk, ra);
  return ra;
}
const ve = viTri => dung_cay(KhoiNoiDung.render.call({viTri}));
const banner = c => tim(c, n => String(n.props.class || '').split(' ').includes('web-banner'));
function nap(xemThu) { ND.khoi = JSON.parse(JSON.stringify(MAY.khoi)); ND.xemThu = !!xemThu; }

await ca('Đầu trang: chỉ banner đang bật, có ảnh, trong khoảng ngày, đúng thứ tự', async () => {
  nap();
  la('đúng bốn banner', banner(ve('dau_trang')).map(n => n.props['data-khoi']), ['dau', 'khong-dt', 'ngoai', 'khong-link']);
});

await ca('Banner có link là thẻ a mở đúng link; không link là khối không bấm được', async () => {
  nap();
  const ds = banner(ve('dau_trang'));
  la('thẻ và link', ds.map(n => [n.the, n.props.href || '']), [['a', '/thanh-vien'], ['a', '/thanh-vien'], ['a', 'https://zalo.me/vagabond'], ['div', '']]);
});

await ca('Có ảnh điện thoại thì màn hẹp dùng ảnh đó; không có thì một ảnh cho mọi màn; alt là mô tả ảnh', async () => {
  nap();
  const [mot, hai] = banner(ve('dau_trang'));
  la('nguồn ảnh điện thoại', tim(mot, n => n.the === 'source').map(n => [n.props.media, n.props.srcset]), [['(max-width: 640px)', '/files/dau-dt.png']]);
  la('ảnh máy tính', tim(mot, n => n.the === 'img').map(n => [n.props.src, n.props.alt]), [['/files/dau-pc.png', 'Cập nhật ngày sinh nhận quà']]);
  la('không ảnh điện thoại thì không có source', tim(hai, n => n.the === 'source').length, 0);
});

await ca('Giỏ hàng và Đặt xong chỉ ra ở đúng chỗ của mình', async () => {
  nap();
  la('giỏ hàng', banner(ve('gio_hang')).map(n => n.props['data-khoi']), ['gio']);
  la('đặt xong', banner(ve('dat_xong')).map(n => n.props['data-khoi']), ['xong']);
  la('cuối trang không có banner', banner(ve('cuoi_trang')).length, 0);
});

await ca('Link hay ảnh lọt qua mà không an toàn thì không vẽ link, không vẽ ảnh', async () => {
  nap();
  ND.khoi.unshift({id: 'xau', loai: 'banner', vi_tri: 'dau_trang', hien: true, tieu_de: 'x', anh: '/files/a.png', anh_dt: 'javascript:alert(1)', lien_ket: 'javascript:alert(1)'},
    {id: 'xau-anh', loai: 'banner', vi_tri: 'dau_trang', hien: true, tieu_de: 'y', anh: 'http://x.vn/a.png', lien_ket: '/thanh-vien'});
  const ds = banner(ve('dau_trang'));
  la('banner ảnh xấu không ra', ds.some(n => n.props['data-khoi'] === 'xau-anh'), false);
  const xau = ds.find(n => n.props['data-khoi'] === 'xau');
  la('link xấu thành khối không bấm', [xau.the, xau.props.href], ['div', undefined]);
  la('ảnh điện thoại xấu bị bỏ', tim(xau, n => n.the === 'source').length, 0);
});

await ca('Xem thử trong trình biên tập: vẫn vẽ cả banner đang ẩn ngày, bấm là chọn để sửa, không mở link', async () => {
  nap(true);
  const ds = banner(ve('dau_trang'));
  dung('có banner chưa tới ngày', ds.some(n => n.props['data-khoi'] === 'sap'));
  la('không thẻ a khi xem thử', ds.filter(n => n.the === 'a').length, 0);
  ND.xemThu = false;
});

await ca('Luật ngày trùng máy chủ: từ ngày bắt đầu tới hết ngày kết thúc', async () => {
  const k = {loai: 'banner', hien: true};
  la('trong khoảng', khachThay(Object.assign({bat_dau: HN, ket_thuc: HN}, k), HN), true);
  la('chưa tới', khachThay(Object.assign({bat_dau: '2999-01-01'}, k), HN), false);
  la('đã hết', khachThay(Object.assign({ket_thuc: '2000-01-01'}, k), HN), false);
  la('đang ẩn', khachThay({loai: 'banner', hien: false}, HN), false);
});

await ca('Biên nhận: máy chủ chỉ gửi banner Đặt xong còn hạn, trang vẽ ảnh, ảnh điện thoại và link', async () => {
  la('máy chủ lọc', MAY.xong.map(b => b.id), ['xong']);
  const ds = dung_cay(veBanner(MAY.xong));
  la('một banner, thẻ a tới trang thành viên', ds.map(n => [n.the, n.props.href, n.props['data-banner']]), [['a', '/thanh-vien', 'dat_xong']]);
  la('ảnh và ảnh điện thoại', [tim(ds, n => n.the === 'img').map(n => n.props.src), tim(ds, n => n.the === 'source').map(n => n.props.srcset)],
    [['/files/xong-pc.png'], ['/files/xong-dt.png']]);
  la('không có gì thì không vẽ', dung_cay(veBanner(undefined)), []);
  la('link xấu không thành a', dung_cay(veBanner([{anh: '/files/a.png', lien_ket: 'javascript:x'}])).map(n => n.the), ['div']);
});

/* Mutation B8 (bỏ veBanner khỏi biên nhận) chỉ bị ca mã băm bắt: ca này MOUNT
   THẬT trang biên nhận taoTrang bằng Vue thật, dữ liệu banner từ máy chủ. */
const nutR = the => ({the, props: {}, con: [], cha: null, addEventListener() {}, removeEventListener() {}});
const {createApp: taoApp} = createRenderer({
  createElement: the => nutR(the), createText: chu => ({chu, cha: null}), createComment: chu => ({ghiChu: chu, cha: null}),
  setText: (n, chu) => { n.chu = chu; }, setElementText: (n, chu) => { n.con = chu ? [{chu, cha: n}] : []; },
  insert: (con, cha, moc) => {
    if (con.cha) con.cha.con.splice(con.cha.con.indexOf(con), 1);
    const i = moc ? cha.con.indexOf(moc) : -1;
    if (i >= 0) cha.con.splice(i, 0, con); else cha.con.push(con);
    con.cha = cha;
  },
  remove: con => { if (con.cha) { con.cha.con.splice(con.cha.con.indexOf(con), 1); con.cha = null; } },
  parentNode: n => n.cha, nextSibling: n => (n.cha ? n.cha.con[n.cha.con.indexOf(n) + 1] || null : null),
  patchProp: (n, k, cu, moi) => { if (moi == null) delete n.props[k]; else n.props[k] = moi; },
  setScopeId: () => {}, insertStaticContent: () => { throw new Error('không dùng'); }
});
const timR = (n, dk, ra = []) => { if (!n || !n.con) return ra; if (n.the && dk(n)) ra.push(n); n.con.forEach(x => timR(x, dk, ra)); return ra; };
async function moBienNhan(banner, kho = new Map(), taiLai = false) {
  const win = {location: {pathname: taiLai ? '/banh/xong' : '/banh/xong/' + 'T'.repeat(43), replace() {}}, document: {title: ''},
    history: {replaceState(a, b, p) { win.location.pathname = p; }},
    sessionStorage: {getItem: k => (kho.has(k) ? kho.get(k) : null), setItem: (k, v) => kho.set(k, v)}};
  const D = taiLai ? {loai: 'bien_nhan', khong_token: 1, nhan: {}, bang: {gia_tri: {}, tien_to: []}, lien_he: [], banner}
    : {loai: 'bien_nhan', nhan: {}, bang: {gia_tri: {}, tien_to: []}, lien_he: [], banner,
    bien_nhan: {ma: 'DW-2611-00123', mon: [], tien_banh: '900.000 đ', phi_giao: '36.000 đ', tong: '936.000 đ', thanh_toan: 'Tiền mặt'}};
  const goc = nutR('goc');
  taoApp(taoTrang(D, {win, hen: () => {}, ghi: async () => ({}), dieuHuong: () => {}, chep: async () => {}})).mount(goc);
  for (let i = 0; i < 3; i++) { await nextTick(); await new Promise(r => setTimeout(r, 0)); }
  return goc;
}

await ca('Biên nhận mount thật: banner Đặt xong máy chủ gửi hiện trên trang, nằm trước nút Đặt thêm bánh; không có banner thì không vẽ', async () => {
  const goc = await moBienNhan(MAY.xong);
  const bn = timR(goc, n => n.props['data-banner'] === 'dat_xong');
  la('một banner, link trang thành viên', bn.map(n => [n.the, n.props.href]), [['a', '/thanh-vien']]);
  la('ảnh máy tính', timR(bn[0], n => n.the === 'img').map(n => n.props.src), ['/files/xong-pc.png']);
  const vo = timR(goc, n => String(n.props.class || '') === 'bn-in')[0];
  const i = vo.con.indexOf(bn[0]), j = vo.con.findIndex(n => String(n.props && n.props.class || '') === 'bn-nut');
  dung('banner trước hàng nút', i >= 0 && j > i);
  la('rỗng thì không vẽ', timR(await moBienNhan([]), n => n.props['data-banner']).length, 0);
});

/* Codex PR #550: khách tải lại biên nhận. Lần đầu trang gỡ token khỏi đường dẫn
   và lưu biên nhận vào phiên; lần tải lại máy chủ không biết biên nhận nào
   (khong_token) nhưng vẫn gửi banner công khai, trang khôi phục biên nhận từ
   phiên và vẽ banner. Không có biên nhận trong phiên thì không vẽ banner. */
await ca('Tải lại biên nhận (không còn token): biên nhận khôi phục từ phiên vẫn có banner Đặt xong', async () => {
  const kho = new Map();
  await moBienNhan(MAY.xong, kho);
  const lai = await moBienNhan(MAY.xong, kho, true);
  dung('khôi phục đúng biên nhận', JSON.stringify(timR(lai, n => n.the === 'b').map(n => n.con.map(x => x.chu).join(''))).includes('DW-2611-00123'));
  la('banner vẫn hiện', timR(lai, n => n.props['data-banner'] === 'dat_xong').map(n => n.props.href), ['/thanh-vien']);
  const trong = await moBienNhan(MAY.xong, new Map(), true);
  la('không có biên nhận trong phiên: không vẽ banner', timR(trong, n => n.props['data-banner']).length, 0);
});

console.log('Bộ ca kiểm HÀNH VI v647: banner trên trang đặt bánh và biên nhận');
loi.forEach(d => console.log('  HỎNG  ' + d));
console.log(dat + ' ca đạt, ' + hong + ' ca hỏng, tổng ' + (dat + hong) + ' ca.');
process.exit(hong ? 1 : 0);
