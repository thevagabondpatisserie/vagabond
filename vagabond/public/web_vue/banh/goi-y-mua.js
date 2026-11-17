/* v668 Gợi ý mua thêm (anh Việt duyệt 17/11/2026, phần F prompt /banh).

   Một khối thẻ ảnh vuốt ngang, dùng ở hai chỗ:
     - giỏ đặt trước, ngay dưới nút "Chọn thêm bánh", trước mục 02 Ngày và giờ nhận;
     - khung Đặt giao của tab Tại quầy, ngay dưới danh sách món, trước lựa chọn
       Giao tận nơi / Tự lấy tại quầy.
   Không bật khung chen ngang, không đặt sát nút gửi. Bấm + là thêm NGAY một cái
   (món gợi ý không cần chọn size hay tuỳ chọn); thêm xong thẻ đó nhường chỗ cho
   món kế tiếp. Không còn món thì ẩn cả khối.
   Thanh miễn phí giao: chỉ khi giao tận nơi và chưa đủ mốc; mốc lấy từ cấu hình
   miễn phí giao đang chạy, không viết cứng. */
import {h} from '../lib/vue.esm-browser.prod.js';
import {t} from '../kho/chu.js';
import * as T from '../kho/thuan.js';

const TIENG_ANH = () => typeof document !== 'undefined' && /^en/i.test(document.documentElement.lang || '');
export const lyDo = u => (TIENG_ANH() && u.ly_do_en) || u.ly_do_vn || '';

/* THUẦN: thanh miễn phí giao. null khi không hiện. */
export function thanhMienPhi(tien, nguong, giaoTanNoi, bat = true) {
  const g = Number(nguong) || 0, x = Number(tien) || 0;
  if (!bat || !giaoTanNoi || g <= 0 || x <= 0 || x >= g) return null;
  return {con: g - x, phan: Math.max(4, Math.min(100, Math.round(x * 100 / g)))};
}

/* THUẦN: món bày ra = món máy chủ gợi ý chưa có trong giỏ, tối đa toi_da. */
export function monBay(ds, maTrongGio, toiDa) {
  const co = new Set(maTrongGio || []);
  return (ds || []).filter(u => u && u.ma && !co.has(u.ma)).slice(0, Math.max(0, Number(toiDa) || 0));
}

const dungGhim = (c, ngay) => {
  const tu = String(c.ghim_tu || '').slice(0, 10), den = String(c.ghim_den || '').slice(0, 10);
  return !!(tu || den) && (!tu || tu <= ngay) && (!den || ngay <= den);
};

/* THUẦN: gợi ý cho khung Đặt giao của Tại quầy, từ món của ĐÚNG cửa hàng đang chọn.
   gio: [{ma, loai}] (loai 'banh' | 'nuoc' | 'combo'); menu: danh sách món của quầy
   (dungQuayHien: bánh có "con", đồ uống có bienThe); cfg: kết quả goi_y_mua.cap_quay.
   Giỏ có bánh: đồ uống (cặp đã duyệt theo món hoặc nhóm món gốc, chưa có cặp thì
   đồ uống không cần chọn, câu chung). Giỏ chỉ có đồ uống: bánh còn trên tủ từ
   ngưỡng tồn trở lên. Trả {loai: 'uong'|'an', ds: [{ma, ten, anh, gia, ly_do_vn,
   ly_do_en, m, bt}]} (m, bt để thêm bằng hàm thêm sẵn có của quầy). */
export function goiYQuay(gio, menu, cfg) {
  const ra = {loai: '', ds: []};
  if (!cfg || !Number(cfg.bat) || !(gio || []).length) return ra;
  const maGio = new Set(gio.map(x => x.ma));
  const coBanh = gio.some(x => x.loai === 'banh' || x.loai === 'combo');
  const lyNhom = cfg.ly_do_nhom || {};
  const ghim = new Set(cfg.ghim || []);
  const toiDa = Number(cfg.toi_da) || 4;
  if (coBanh) {
    ra.loai = 'uong';
    const nuoc = (menu || []).filter(m => m.loai === 'nuoc');
    const timBt = ma => { for (const m of nuoc) { const bt = (m.bienThe || [{ma: m.ma, gia: m.gia, ten: m.ten}]).find(b => b.ma === ma); if (bt) return {m, bt}; } return null; };
    const nhomGio = new Set((menu || []).filter(m => maGio.has(m.ma)).map(m => m.nhom || m.nhom_goc).filter(Boolean));
    const keyGio = new Set([...maGio].map(x => String(x).toLowerCase()));
    const theoCap = [], coCap = new Set();
    (cfg.cap || []).forEach(c => {
      const goc = String(c.mon_goc || '').toLowerCase();
      if (!(goc ? keyGio.has(goc) : nhomGio.has(c.nhom_goc))) return;
      if (goc) coCap.add(goc);
      const x = timBt(c.mon_goi_y);
      if (!x || maGio.has(x.bt.ma) || theoCap.some(y => y.ma === x.bt.ma)) return;
      theoCap.push({ma: x.bt.ma, ten: x.bt.ten || x.m.ten, anh: x.m.anh || '', gia: Number(x.bt.gia) || 0, ly_do_vn: c.ly_do_vn || '',
        ly_do_en: c.ly_do_en || '', m: x.m, bt: x.bt, _g: ghim.has(c.mon_goi_y) ? 0 : 1, _u: Number(c.uu_tien) || 10});
    });
    theoCap.sort((a, b) => a._g - b._g || a._u - b._u);
    let ds = theoCap;
    if (!ds.length) {
      const [vn, en] = lyNhom['Đồ uống'] || ['', ''];
      ds = nuoc.filter(m => (m.bienThe || []).length <= 1 && !(m.tc || []).length && !maGio.has(m.ma))
        .map(m => ({ma: m.ma, ten: m.ten, anh: m.anh || '', gia: Number(m.gia) || 0, ly_do_vn: vn, ly_do_en: en, m, bt: (m.bienThe || [])[0]}));
    }
    ra.ds = ds.filter(u => u.anh && u.gia > 0).slice(0, toiDa * 3).map(({_g, _u, ...u}) => u);
    return ra;
  }
  ra.loai = 'an';
  const [vn, en] = lyNhom['Bánh trên tủ'] || ['', ''];
  const nguong = Number(cfg.nguong);
  ra.ds = (menu || []).filter(m => m.loai === 'banh' && !maGio.has(m.ma) && (Number(m.con) || 0) >= (isNaN(nguong) ? 3 : Math.max(1, nguong)))
    .sort((a, b) => (Number(b.con) || 0) - (Number(a.con) || 0))
    .filter(m => m.anh && Number(m.gia) > 0)
    .map(m => ({ma: m.ma, ten: m.ten, anh: m.anh, gia: Number(m.gia) || 0, ly_do_vn: vn, ly_do_en: en, m, bt: (m.bienThe || [])[0]}))
    .slice(0, toiDa * 3);
  return ra;
}

export const GoiYMua = {
  name: 'GoiYMua',
  props: {tieu: String, ds: Array, them: Function, nho: Boolean, thanh: Object, idKhoi: String},
  render() {
    const ds = this.ds || [];
    const thanh = this.thanh;
    if (!ds.length && !thanh) return null;
    const the = u => h('article', {class: 'gy-the', 'data-ma': u.ma}, [
      h('div', {class: 'gy-anh'}, [
        h('img', {src: u.anh, alt: '', loading: 'lazy', decoding: 'async', onError: e => { e.target.style.display = 'none'; }}),
        h('button', {class: 'gy-cong', type: 'button', 'aria-label': t('gy_them', 'Thêm {ten} vào giỏ', {ten: u.ten}), onClick: () => this.them && this.them(u)},
          [h('svg', {viewBox: '0 0 24 24', 'aria-hidden': 'true'}, [h('path', {d: 'M12 5v14M5 12h14', fill: 'none', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round'})])])]),
      h('p', {class: 'gy-ten'}, u.ten),
      lyDo(u) ? h('p', {class: 'gy-ly'}, lyDo(u)) : null,
      h('p', {class: 'gy-gia'}, T.tienVN(u.gia))]);
    return h('div', {class: 'gy' + (this.nho ? ' gy-nho' : ''), id: this.idKhoi || null}, [
      thanh ? h('div', {class: 'gy-mp', role: 'status'}, [
        h('p', null, t('gy_mien_phi', 'Thêm {tien} nữa được miễn phí giao', {tien: T.tienVN(thanh.con)})),
        h('div', {class: 'gy-vach', 'aria-hidden': 'true'}, [h('i', {style: {width: thanh.phan + '%'}})])]) : null,
      ds.length ? h('p', {class: 'gy-tieu'}, this.tieu) : null,
      ds.length ? h('div', {class: 'gy-bang'}, ds.map(the)) : null]);
  }
};
