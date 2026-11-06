/* Bộ icon riêng của trang gọi món tại bàn (v640, anh Việt duyệt mẫu 05/11/2026).

   Thay emoji 🔔 🧾 🙋 🧊 🍴 💬 của iPhone (mỗi máy vẽ một kiểu, chung chung):
   nét mảnh 1,6, bo đầu nét, tô theo màu chữ (currentColor) nên tự ăn màu
   xanh ngọc, cam, tối theo chỗ đặt. Dựng bằng phần tử SVG thật qua render
   function, không v-html. */
import {h} from '../lib/vue.esm-browser.prod.js';

const N = {fill: 'none', stroke: 'currentColor', 'stroke-width': '1.6', 'stroke-linecap': 'round', 'stroke-linejoin': 'round'};

/* Mỗi icon: danh sách [thẻ, thuộc tính] trong khung 24 x 24. */
export const ICON = {
  chuong: [['path', {d: 'M6.5 16.5V11a5.5 5.5 0 0 1 11 0v5.5l1.5 1.6H5z'}], ['path', {d: 'M12 5.5V4'}],
    ['path', {d: 'M10.2 20.2a1.9 1.9 0 0 0 3.6 0'}], ['path', {d: 'M3.2 9.2a8.6 8.6 0 0 1 2.2-4.1M20.8 9.2a8.6 8.6 0 0 0-2.2-4.1'}]],
  hoaDon: [['path', {d: 'M6 3h12v18l-2-1.4-2 1.4-2-1.4-2 1.4-2-1.4L6 21z'}], ['path', {d: 'M9 8h6M9 11.5h6M9 15h3.5'}]],
  vayTay: [['circle', {cx: '9', cy: '7', r: '3'}], ['path', {d: 'M3.5 20v-1.8A4.7 4.7 0 0 1 8.2 13.5h1.6a4.7 4.7 0 0 1 4.7 4.7V20'}],
    ['path', {d: 'M17.5 4.5c1.6.7 2.6 2 3 3.6M16.8 7.4c.8.4 1.3 1 1.5 1.8'}]],
  lyDa: [['path', {d: 'M5.5 4h13l-1.6 15.2a2 2 0 0 1-2 1.8H9.1a2 2 0 0 1-2-1.8z'}], ['path', {d: 'M6.3 9.5h11.4'}],
    ['rect', {x: '8.6', y: '12', width: '3.2', height: '3.2', rx: '.6', transform: 'rotate(-10 10.2 13.6)'}],
    ['rect', {x: '12.4', y: '13.4', width: '3', height: '3', rx: '.6', transform: 'rotate(12 13.9 14.9)'}]],
  daoNia: [['path', {d: 'M7 3v5.5a2 2 0 0 0 4 0V3M9 3v18'}], ['path', {d: 'M16.5 21V3c-2 1.2-3 3.6-3 6.5 0 2.2 1 3.6 3 4'}]],
  chat: [['path', {d: 'M4 6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v8a2.5 2.5 0 0 1-2.5 2.5H10l-4.2 3.2V17H6.5A2.5 2.5 0 0 1 4 14.5z'}],
    ['circle', {cx: '8.6', cy: '10.5', r: '1', fill: 'currentColor', stroke: 'none'}], ['circle', {cx: '12', cy: '10.5', r: '1', fill: 'currentColor', stroke: 'none'}],
    ['circle', {cx: '15.4', cy: '10.5', r: '1', fill: 'currentColor', stroke: 'none'}]],
  cuaHang: [['path', {d: 'M4 9.5L5.5 4h13L20 9.5'}], ['path', {d: 'M4 9.5h16v1a2.7 2.7 0 0 1-5.3 0 2.7 2.7 0 0 1-5.4 0A2.7 2.7 0 0 1 4 10.5z'}],
    ['path', {d: 'M5.5 13v7h13v-7M10 20v-4.5h4V20'}]],
  cong: [['path', {d: 'M12 5v14M5 12h14'}]],
  tru: [['path', {d: 'M5 12h14'}]],
  dong: [['path', {d: 'M6 6l12 12M18 6L6 18'}]],
  tick: [['path', {d: 'M5 12.5l4.5 4.5L19 7.5', 'stroke-width': '2.6'}]],
};
/* Icon từng lý do gọi nhân viên, đúng thứ tự LY_DO_GOI. */
export const ICON_LY_DO = ['vayTay', 'hoaDon', 'lyDa', 'daoNia', 'chat'];

export const BieuTuong = {
  name: 'BieuTuong',
  props: {ten: {type: String, required: true}},
  render() {
    const ds = ICON[this.ten] || [];
    return h('svg', {class: 'bt', viewBox: '0 0 24 24', 'aria-hidden': 'true', focusable: 'false', ...N, 'data-bt': this.ten},
      ds.map(([the, tt]) => h(the, tt)));
  }
};
