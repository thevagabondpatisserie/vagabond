/* v667 (anh Việt duyệt 17/11/2026 qua ảnh chụp trang thật): tab "Đặc biệt tuần này",
   mục 05 trên vành nghiêng, sau Vé sự kiện, trước Tại quầy.

   Mọi chữ và ngày ở đầu tab lấy từ đợt Marketing nhập ở trình biên tập (thẻ Cuối
   tuần), không viết cứng. Giá, size, tầng hương lấy từ danh mục bánh như mọi bánh.
   Đợt 1 món: một thẻ lớn rộng hết hàng, nút chính "Đặt món này". Đợt 2 món trở
   lên: băng chuyền thẻ 292 x 440 vuốt ngang có điểm dừng, nút + tròn, hàng chấm
   vị trí. Không có dạng lưới. Bấm thẻ hay nút mở khung chọn bánh sẵn có.
   Luật nút (dbt-thuan.js): chưa tới giờ mở đơn khoá và ghi "Mở đơn" + ngày;
   qua giờ chốt hay hết số lượng khoá và ghi "Đã chốt đơn tuần này". */
import {h, reactive} from '../lib/vue.esm-browser.prod.js';
import {ND, t, tMon} from '../kho/chu.js';
import {anToan, dong as dongChu} from './noi-dung.js';
import * as D from './dbt-thuan.js';

const TT = reactive({dang: 0});

/* Dữ liệu một thẻ món: bánh trong danh mục, giá từ size nhỏ nhất đang nhận. */
export function theMon(kho, dot, m, luc) {
  const c = (kho.S.CAKES || []).find(x => D.khoaBanh(x.k) === m.khoa);
  if (!c) return null;
  const sz = kho.kichThuocDangBan(c, 'dac_biet').slice().sort((a, b) => (a.cm || 0) - (b.cm || 0) || a.p - b.p);
  const nho = sz[0] || c.sizes[0];
  const ma = c.sizes[0].id;
  const anh = (m.anh && anToan(m.anh) ? m.anh : '') || (c.anhs && c.anhs[0]) || c.img || '';
  const tang = (c.layers || []).map(x => (Array.isArray(x) ? x[0] : x)).filter(Boolean);
  return {m, c, ten: tMon(ma, 'ten', c.k), anh, tang, gia: nho ? nho.p : 0, cm: nho ? nho.cm : '',
    tt: D.trangThaiMon(dot, m, luc, ND.dac_biet_da_dat)};
}

function nhanKhoa(dot, tt) {
  if (tt === 'chua_mo') {
    const mo = D.mocMoDon(dot);
    return t('dbt_mo_don', 'Mở đơn') + (mo && mo.chu_ngay ? ' ' + mo.chu_ngay : '');
  }
  return t('dbt_da_chot', 'Đã chốt đơn tuần này');
}

function DauTab(dot, luc) {
  const dong = dongChu(dot.tieu_de);
  const hien = D.mocHienTai(dot, luc);
  const dn = dot.dem_nguoc === '1' ? D.demNguoc(dot, luc) : null;
  return h('header', {class: 'dbt-dau'}, [
    h('div', {class: 'meta dbt-meta'}, [h('span', {class: 'num'}, [h('span', null, t('dbt_meta', '05 / Đặc biệt tuần này'))]),
      h('span', {class: 'dbt-nhan-phai'}, dot.nhan || t('dbt_nhan_mac_dinh', 'Chỉ cuối tuần'))]),
    h('h1', {class: 'dbt-tieu'}, dong.flatMap((d, i) => (i ? [h('br'), d] : [d]))),
    dot.noi_dung ? h('p', {class: 'dbt-mo-ta'}, dot.noi_dung) : null,
    h('ol', {class: 'dbt-moc', 'aria-label': t('dbt_lich', 'Lịch đợt')}, (dot.moc || []).map((m, i) =>
      h('li', {class: i === hien ? 'on' : (i < hien ? 'qua' : ''), 'aria-current': i === hien ? 'step' : undefined},
        [h('i', {'aria-hidden': 'true'}), h('b', null, m.nhan), h('span', null, m.chu_ngay)]))),
    dn ? h('div', {class: 'dbt-dem', role: 'timer'}, [
      h('b', null, dn.don_vi === 'ngay' ? t('dbt_dem_ngay', '{so} ngày', {so: dn.so}) : t('dbt_dem_gio', '{so} giờ', {so: dn.so})),
      h('span', null, [h('span', null, dot.dem_chu_1 || ''), h('span', null, dot.dem_chu_2 || '')])]) : null
  ]);
}

function The(x, mot, dang, mo) {
  const mo_duoc = x.tt === 'mo';
  const bam = mo_duoc ? () => mo(x.c) : undefined;
  const gia = h('p', {class: 'dbt-gia'}, [h('span', null, t('dbt_tu', 'Từ') + (x.cm ? ' · Ø ' + x.cm + 'cm' : '')),
    h('b', null, String(x.gia || 0).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' đ')]);
  const chu = [h('h2', {class: 'dbt-ten'}, x.ten), x.m.mo_ta ? h('p', {class: 'dbt-mo'}, x.m.mo_ta) : null, gia];
  if (mot && x.tang.length) chu.push(h('p', {class: 'dbt-tang'}, [h('b', null, t('dbt_tang_huong', 'Tầng hương')), h('span', null, x.tang.join(' · '))]));
  if (!mo_duoc) chu.push(h('p', {class: 'dbt-khoa', role: 'status'}, nhanKhoa(x.dot, x.tt)));
  if (mot) {
    chu.push(h('button', {class: 'btn dbt-dat', type: 'button', disabled: !mo_duoc, onClick: bam},
      [h('span', null, mo_duoc ? t('dbt_dat_mon', 'Đặt món này') : nhanKhoa(x.dot, x.tt))]));
  }
  return h('article', {class: 'dbt-the' + (mot ? ' dbt-mot' : '') + (dang ? ' dang' : '') + (mo_duoc ? '' : ' khoa'),
    'data-khoa': x.m.khoa}, [
    h('div', {class: 'dbt-anh', onClick: bam, role: mo_duoc && !mot ? 'button' : undefined, tabindex: mo_duoc && !mot ? 0 : undefined,
      'aria-label': mo_duoc && !mot ? t('dbt_xem_mon', 'Xem {ten}', {ten: x.ten}) : undefined},
      x.anh ? [h('img', {src: x.anh, alt: '', loading: 'lazy', decoding: 'async', onError: e => { e.target.style.display = 'none'; }})] : []),
    h('span', {class: 'dbt-goc'}, x.m.nhan_goc || t('dbt_nhan_mac_dinh', 'Chỉ cuối tuần')),
    h('div', {class: 'dbt-chu'}, chu),
    !mot && mo_duoc ? h('button', {class: 'dbt-cong', type: 'button', onClick: bam, 'aria-label': t('dbt_them', 'Chọn size {ten}', {ten: x.ten})},
      [h('svg', {viewBox: '0 0 24 24', 'aria-hidden': 'true'}, [h('path', {d: 'M12 5v14M5 12h14', fill: 'none', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round'})])]) : null
  ]);
}

export const DacBietTuan = {
  name: 'DacBietTuan',
  props: {kho: Object, mo: Function},
  render() {
    const kho = this.kho, dot = kho.dotDbt.value;
    if (!dot) return h('p', {class: 'cm-rong', id: 'dbtRong'}, t('dbt_rong', 'Tuần này chưa có món đặc biệt. Quý khách xem các bánh đặt trước nhé.'));
    const luc = kho.lucDbt();
    const ds = (dot.mon_dt || []).map(m => theMon(kho, dot, m, luc)).filter(Boolean).map(x => Object.assign(x, {dot}));
    const mot = ds.length === 1;
    const mo = c => this.mo && this.mo(c);
    const dang = Math.min(TT.dang, Math.max(ds.length - 1, 0));
    const bang = mot ? [The(ds[0], true, true, mo)]
      : [h('div', {class: 'dbt-bang', id: 'dbtBang', onScroll: e => {
        const el = e.currentTarget, the = el.querySelector('.dbt-the');
        if (!the) return;
        TT.dang = Math.max(0, Math.min(ds.length - 1, Math.round(el.scrollLeft / (the.offsetWidth + 14))));
      }}, ds.map((x, i) => The(x, false, i === dang, mo))),
      h('div', {class: 'dbt-cham', 'aria-hidden': 'true'}, ds.map((_, i) => h('i', {class: i === dang ? 'on' : ''})))];
    return h('div', {class: 'dbt', id: 'dacBietTuan', 'data-so-mon': ds.length}, [
      DauTab(dot, luc),
      ds.length ? h('div', {class: 'dbt-ds' + (mot ? ' mot' : '')}, bang)
        : h('p', {class: 'cm-rong'}, t('dbt_chua_co_mon', 'Món của tuần này đang được cập nhật. Quý khách quay lại sau ít phút.'))
    ]);
  }
};
