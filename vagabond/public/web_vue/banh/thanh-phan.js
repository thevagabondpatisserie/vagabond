/* Thành phần nhỏ dùng chung cho trang đặt bánh bản Vue. */
import {h} from '../lib/vue.esm-browser.prod.js';
import {ANH_NEN} from './du-lieu.js';

/* Một câu nhiều mảnh (chu-giau.js). KHÔNG có v-html: chữ marketing luôn là chữ. */
export const DongChu = {
  name: 'DongChu',
  props: {phan: {type: Array, default: () => []}},
  render() {
    return (this.phan || []).map(p => {
      if (!p) return null;
      const style = p.mau === 'cyan' ? 'color:var(--cyan)' : p.mau === 'do' ? 'color:#FF7A6B' : undefined;
      if (p.href) return h('a', {href: p.href, target: p.moi ? '_blank' : undefined, rel: p.moi ? 'noopener' : undefined, style: 'color:var(--cyan)'}, p.chu);
      if (p.dam) return h('b', {style}, p.chu);
      if (p.nghieng) return h('em', null, p.chu);
      if (style) return h('span', {style}, p.chu);
      return p.chu;
    });
  }
};

/* Biểu tượng nút cùng lưới 24, nét 1.5 (#460). */
const DUONG = {cong: 'M5 12h14M12 5v14', tru: 'M5 12h14', sua: 'm15 5 4 4M4 20l4-1L20 7l-4-4L4 15v5Z',
  bo: 'M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 10v7M14 10v7', chon: 'm5 12 4 4 10-10',
  lui: 'M15 5l-7 7 7 7', dong: 'M5 5l14 14M19 5L5 19',
  goi: 'M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2Z'};
export const BieuTuong = {
  name: 'BieuTuong',
  props: {loai: String, an: {type: Boolean, default: true}},
  render() { return h('svg', {'aria-hidden': this.an ? 'true' : undefined, viewBox: '0 0 24 24'}, [h('path', {d: DUONG[this.loai]})]); }
};

/* Ảnh món: hỏng thì thay ảnh nền thương hiệu, chỉ một lần (anhHong cũ). */
export const AnhMon = {
  name: 'AnhMon',
  props: {src: String, alt: {type: String, default: ''}, lazy: {type: Boolean, default: true}},
  data() { return {hong: false}; },
  watch: {src() { this.hong = false; }},
  render() {
    return h('img', {loading: this.lazy ? 'lazy' : undefined, src: this.hong ? ANH_NEN : (this.src || ANH_NEN), alt: this.alt,
      onError: () => { if (!this.hong) this.hong = true; }});
  }
};
