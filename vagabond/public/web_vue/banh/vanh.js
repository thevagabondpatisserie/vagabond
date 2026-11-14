/* v658 (anh Việt duyệt bản thử TkCJguMmbmYsWwimW3gGYF, 14/11/2026): thanh mục
   "Vành nghiêng" thay dải tab kéo ngang của trang đặt bánh.

   Các mục nằm trên một vành đai hành tinh nghiêng -11 độ, vẽ thẳng trên nền vũ
   trụ của trang, không khung, không nền riêng. Chữ mọi mục giữ CÙNG góc nghiêng
   của vành, không uốn theo đường cong (anh chê bản chữ uốn là "kịch cỡm").

   Thao tác: vuốt ngang để đổi mục, chạm thẳng vào một mục cũng chọn được, phím
   mũi tên và lăn chuột ngang trên máy tính. Anh Việt 14/11/2026 (bản v658 trên
   site): vành giật khi quẹt và kéo cả trang cuộn dọc theo. Nay vùng vành KHOÁ
   chỉ theo chiều ngang (touch-action: none, trình duyệt không tự cuộn khi ngón
   tay đặt trên vành), mỗi khung hình vẽ đúng một lần (requestAnimationFrame),
   không đọc lại kích thước mục giữa lúc vẽ (đo một lần, giữ trong bộ nhớ), và
   chỉ làm mờ chữ khi vành đã đứng yên (blur mỗi khung là việc nặng nhất trên
   iPhone). Danh sách mục do trang truyền vào (các tab đang hiện),
   thành phần này không ghi cứng mục nào.

   Phép tính hình học và luật vuốt là hàm THUẦN ở đầu tệp, ca kiểm node
   (hanh_vi/vanh_658.mjs) chạy thẳng các hàm này. Không innerHTML. */
import {h, ref, reactive, computed, watch, onMounted, onBeforeUnmount} from '../lib/vue.esm-browser.prod.js';
import {t} from '../kho/chu.js';

/* Thứ tự anh Việt duyệt; tab theo mùa (In season, Tiệc) chen cạnh nhóm mua bánh. */
/* Tab Vé sự kiện giữ mã nội bộ 'tiec' (tab Tiệc cũ nâng lên, anh Việt chọn A 14/11/2026). */
export const THU_TU_MUC = ['today', 'order', 'season', 'thiet_ke_rieng', 'tiec', 'store', 'uu_dai', 'tuyen_dung'];
export const HINH = {TILT: -11, RX: 150, RY: 44, H: 150, NGUONG: 7, VUOT_NGAN: 140, PX_MOT_MUC: 80, AN_DUOI: 0.2};

/* Xếp mục theo thứ tự đã duyệt; mục lạ (chưa có trong danh sách) đứng cuối, giữ thứ tự gốc. */
export function xepMuc(ds) {
  const vt = m => { const i = THU_TU_MUC.indexOf(m.tab); return i < 0 ? THU_TU_MUC.length : i; };
  return (ds || []).map((m, i) => ({m, i})).sort((a, b) => vt(a.m) - vt(b.m) || a.i - b.i).map(x => x.m);
}
export const vongQuanh = (x, n) => ((x % n) + n) % n;
/* Độ lệch của mục i so với vị trí quay pos, đưa về khoảng (-n/2, n/2]. */
export function lech(i, pos, n) { let d = vongQuanh(i - pos, n); if (d > n / 2) d -= n; return d; }
/* Màn rộng: vành lớn theo chiều ngang, có trần. */
export function coGian(w) { return Math.max(1, Math.min(1.45, (Number(w) || 390) / 390)); }

/* Vị trí một mục trên vành. Góc giãn th + 0.5 sin th để mục phía trước thưa,
   phía sau không chồng; k là độ gần (1 là ngay trước mặt). Mục k dưới AN_DUOI
   ẩn hẳn và không cho chạm (anh Việt: nửa sau đang sát và đè nhau). */
export function viTri(d, n, s = 1, giamMo = false) {
  const th0 = d * 2 * Math.PI / n, th = th0 + 0.5 * Math.sin(th0), tl = HINH.TILT * Math.PI / 180;
  const x = Math.sin(th) * HINH.RX * s, y = Math.cos(th) * HINH.RY * s;
  const k = (Math.cos(th) + 1) / 2;
  return {
    x: x * Math.cos(tl) - y * Math.sin(tl), y: x * Math.sin(tl) + y * Math.cos(tl), k,
    co: 0.45 + 0.6 * k * k, mo: giamMo ? 0 : Math.min(6, (1 - k) * 4), dTrong: 0.08 + 0.92 * k * k,
    an: k < HINH.AN_DUOI, truoc: k > 0.97, lop: Math.round(k * 10),
  };
}
/* Nhận kiểu vuốt: 'h' ngang (đổi mục), 'v' dọc (để trình duyệt cuộn), null chưa đủ ngưỡng. */
export function kieuVuot(dx, dy, nguong = HINH.NGUONG) {
  if (Math.abs(dx) > nguong && Math.abs(dx) > Math.abs(dy)) return 'h';
  if (Math.abs(dy) > nguong) return 'v';
  return null;
}
/* Đang kéo: vị trí theo ngón tay. Vuốt sang trái (dx âm) là sang mục sau. */
export const viTriKeo = (p0, dx) => p0 - dx / HINH.PX_MOT_MUC;
/* Buông tay: vuốt ngắn luôn qua đúng một mục, kéo dài thì dừng ở mục gần nhất. */
export function dichBuong(p0, pos, dx) {
  if (!dx) return Math.round(p0);
  return Math.abs(dx) < HINH.VUOT_NGAN ? Math.round(p0) + (dx < 0 ? 1 : -1) : Math.round(pos);
}
/* Đường quay ngắn nhất từ pos tới mục i, cộng thêm vòng (mở màn). */
export function dichToi(i, pos, n, themVong = 0) {
  let d = i - vongQuanh(Math.round(pos), n);
  if (d > n / 2) d -= n; if (d < -n / 2) d += n;
  return Math.round(pos) + d + themVong;
}
const em = x => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

function luu(loai) { try { const s = window[loai]; s.getItem('x'); return s; } catch (e) { return null; } }
const KHOA_MO = 'vgb_vanh_mo', KHOA_GOI_Y = 'vgb_vanh_goi_y';

/* Nửa elip của một vành ('b' nửa sau vẽ dưới chữ, 'f' nửa trước vẽ trên chữ). */
function veVanh(cx, cy, rx, ry, nua) {
  const sw = nua === 'b' ? 1 : 0, sau = nua === 'b';
  const d = (a, b) => `M${cx - a},${cy} A${a},${b} 0 0 ${sw} ${cx + a},${cy}`;
  const net = [
    [rx * 1.14, ry * 1.18, {stroke: 'rgba(255,255,255,.10)', 'stroke-dasharray': '1 5'}],
    [rx * 0.86, ry * 0.8, {stroke: `rgba(41,189,179,${sau ? 0.09 : 0.15})`, 'stroke-width': 7}],
    [rx, ry, {stroke: `rgba(41,189,179,${sau ? 0.42 : 0.72})`, 'stroke-width': 1.2}],
    [rx * 0.93, ry * 0.9, {stroke: `rgba(41,189,179,${sau ? 0.16 : 0.26})`, 'stroke-width': 0.8}],
  ];
  return h('g', {transform: `rotate(${HINH.TILT} ${cx} ${cy})`}, net.map(([a, b, kieu]) => h('path', Object.assign({d: d(a, b), fill: 'none'}, kieu))));
}

export const VanhNghieng = {
  name: 'VanhNghieng',
  props: {muc: {type: Array, default: () => []}, dang: {type: String, default: ''}},
  emits: ['chon'],
  setup(props, {emit}) {
    const RM = (() => { try { return window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { return false; } })();
    const goc = ref(null), gon = ref(null);
    const G = reactive({w: 390, goiY: false, gonHien: false, phim: false});
    const s = computed(() => coGian(G.w));
    const cao = computed(() => Math.round(HINH.H * s.value));
    const n = () => props.muc.length;
    const viTriDang = () => Math.max(0, props.muc.findIndex(m => m.tab === props.dang));
    let pos = viTriDang(), dich = pos, keo = false, quay = false, nguoiDoi = false, daDiChuyen = false;
    const oMuc = [], oGon = [];
    /* Kích thước từng mục đo MỘT lần (mở trang, đổi bề rộng, đổi danh sách),
       không đọc offsetWidth trong lúc vẽ: đọc ngay sau khi vừa ghi transform
       bắt trình duyệt tính lại bố cục mỗi mục mỗi khung, nguồn giật chính. */
    const kt = [];
    function doMuc() { oMuc.forEach((o, i) => { if (o) kt[i] = [o.offsetWidth, o.offsetHeight]; }); }

    let gonTruoc = -2, moDangCo = null;
    function ve(yen = false) {
      const N = n(); if (!N || !goc.value) return;
      const cx = G.w / 2, cy = cao.value / 2 - 12 * s.value;
      /* Mờ chữ chỉ vẽ khi vành đứng yên; đang quay thì bỏ (blur mỗi khung rất nặng). */
      const lamMo = yen && !RM;
      let truoc = -1, kMax = -1;
      oMuc.forEach((o, i) => {
        if (!o) return;
        const v = viTri(lech(i, pos, N), N, s.value, RM);
        if (!kt[i]) kt[i] = [o.offsetWidth, o.offsetHeight];
        const [w, hh] = kt[i];
        o.style.transform = `translate3d(${(cx + v.x - w / 2).toFixed(1)}px,${(cy + v.y - hh / 2).toFixed(1)}px,0) rotate(${HINH.TILT}deg)`;
        const chu = o.firstElementChild;
        if (chu) {
          chu.style.transform = `scale(${v.co.toFixed(3)})`;
          if (lamMo !== moDangCo || lamMo) chu.style.filter = lamMo && v.mo ? `blur(${v.mo.toFixed(2)}px)` : 'none';
        }
        o.style.opacity = v.an ? '0' : v.dTrong.toFixed(2);
        o.style.visibility = v.an ? 'hidden' : 'visible';
        o.style.pointerEvents = v.an ? 'none' : 'auto';
        o.style.zIndex = String(v.lop);
        o.classList.toggle('truoc', v.truoc);
        if (v.k > kMax) { kMax = v.k; truoc = i; }
      });
      moDangCo = lamMo;
      if (truoc !== gonTruoc) { gonTruoc = truoc; veGon(truoc); }
      return truoc;
    }
    /* Thanh gọn: mục đang chọn ở giữa một cung mảnh, hai mục kề mờ hai bên.
       Chỉ ghi lại chữ khi mục ở giữa đổi. */
    function veGon(truoc) {
      const N = n();
      oGon.forEach((o, j) => {
        if (!o) return;
        const i = vongQuanh(truoc + j - 1, N);
        o.dataset.i = String(i);
        o.firstElementChild.textContent = (props.muc[i] || {}).nhan || '';
      });
    }
    let khung = 0;
    function chay() {
      if (khung) return;
      const buoc = () => {
        khung = 0;
        if (!keo && !quay) pos = RM ? dich : pos + (dich - pos) * 0.18;
        if (!keo && !quay && Math.abs(dich - pos) < 0.002) pos = dich;
        const yen = !keo && !quay && pos === dich;
        const truoc = ve(yen);
        if (yen && nguoiDoi && truoc >= 0) {
          nguoiDoi = false;
          const m = props.muc[truoc];
          if (m && m.tab !== props.dang) emit('chon', m.tab);
        }
        if (!yen) khung = window.requestAnimationFrame(buoc);
      };
      khung = window.requestAnimationFrame(buoc);
    }
    /* Mỗi lần quay mới huỷ lần quay đang chạy (mở màn, chạm liên tiếp) để hai
       vòng hình không giành nhau vị trí. */
    let luot = 0;
    function quayToi(i, ms, themVong = 0, doiTuNguoi = true) {
      const N = n(); if (!N) return;
      const tu = pos, toi = dichToi(i, pos, N, themVong), cua = ++luot;
      nguoiDoi = doiTuNguoi;
      if (RM || !ms) { quay = false; pos = dich = toi; chay(); return; }
      const t0 = performance.now(); quay = true;
      const f = now => {
        if (cua !== luot) return;
        const k = Math.min(1, (now - t0) / ms);
        pos = tu + (toi - tu) * em(k);
        ve();
        if (k < 1) window.requestAnimationFrame(f); else { dich = toi; quay = false; chay(); }
      };
      window.requestAnimationFrame(f);
    }
    function buocMot(chieu) { tatGoiY(); nguoiDoi = true; dich = Math.round(dich) + chieu; chay(); }

    /* Mục đang xem đổi từ ngoài (link mở thẳng, nút quay lại): quay vành tới đó, không báo ngược. */
    watch(() => props.dang, () => {
      if (keo) return;
      const i = viTriDang();
      if (vongQuanh(Math.round(dich), n()) !== i) quayToi(i, 700, 0, false);
    });
    /* Danh sách đổi (tab theo mùa hiện, tắt): giữ đúng mục đang xem, không quay. */
    watch(() => props.muc.map(m => m.tab).join(','), () => {
      pos = dich = viTriDang(); kt.length = 0; gonTruoc = -2;
      window.requestAnimationFrame(() => { doMuc(); ve(true); chay(); });
    });

    /* ---- vuốt, chạm ---- */
    /* Vùng vành khoá chiều ngang (CSS touch-action: none): ngón tay đặt trên
       vành thì trình duyệt không cuộn trang, nên không còn cảnh vừa quẹt ngang
       vừa bị kéo xuống. Vuốt dọc trên vành không làm gì; cuộn trang ở ngoài vành.
       Mỗi lần ngón tay di chuyển chỉ ghi lại vị trí, vẽ gom vào một khung hình. */
    let sx = null, sy = 0, p0 = 0, kieu = null, dx0 = 0, tl = 1, henVe = 0;
    function xuong(e) {
      sx = e.clientX; sy = e.clientY; p0 = pos; kieu = null; dx0 = 0; daDiChuyen = false;
      const el = e.currentTarget, r = el.getBoundingClientRect(); tl = (r.width / el.offsetWidth) || 1;
    }
    function di(e) {
      if (sx === null) return;
      const el = e.currentTarget, dx = (e.clientX - sx) / tl, dy = (e.clientY - sy) / tl;
      if (!kieu) {
        kieu = kieuVuot(dx, dy);
        if (kieu === 'h') { keo = true; quay = false; daDiChuyen = true; tatGoiY(); try { el.setPointerCapture(e.pointerId); } catch (x) { /* trình duyệt cũ */ } }
        if (kieu === 'v') daDiChuyen = true;
      }
      if (kieu === 'h') {
        if (e.cancelable) e.preventDefault();
        pos = viTriKeo(p0, dx); dx0 = dx;
        if (!henVe) henVe = window.requestAnimationFrame(() => { henVe = 0; if (keo) ve(); });
      }
    }
    function len() {
      if (sx === null) return;
      sx = null;
      if (kieu === 'h') { keo = false; nguoiDoi = true; dich = dichBuong(p0, pos, dx0); if (henVe) { window.cancelAnimationFrame(henVe); henVe = 0; } chay(); }
      kieu = null;
      setTimeout(() => { daDiChuyen = false; }, 0);
    }
    /* Chạm một mục: chọn ngay như bấm tab cũ, vành quay tới mục đó theo props.dang. */
    function chon(i) { const m = props.muc[i]; if (m && m.tab !== props.dang) emit('chon', m.tab); else quayToi(i, 500, 0, false); }
    function cham(i) { if (daDiChuyen) return; tatGoiY(); chon(i); }
    function lan(e) {
      if (Math.abs(e.deltaX) <= Math.abs(e.deltaY) || Math.abs(e.deltaX) < 4) return;
      e.preventDefault();
      if (lan.cho) return;
      lan.cho = setTimeout(() => { lan.cho = 0; }, 220);
      buocMot(Math.sign(e.deltaX));
    }
    const suKien = {onPointerdown: xuong, onPointermove: di, onPointerup: len, onPointercancel: len};

    /* ---- gợi ý vuốt: một lần trên mỗi máy ---- */
    let henGoiY = 0;
    function hienGoiY() {
      const l = luu('localStorage');
      if (l) { if (l.getItem(KHOA_GOI_Y)) return; try { l.setItem(KHOA_GOI_Y, '1'); } catch (e) { /* đầy bộ nhớ */ } }
      G.goiY = true; henGoiY = setTimeout(tatGoiY, 4000);
    }
    function tatGoiY() { G.goiY = false; clearTimeout(henGoiY); }

    let theoDoi = null, coDo = null;
    function doRong() { if (goc.value) { G.w = goc.value.offsetWidth || 390; kt.length = 0; doMuc(); ve(true); } }
    onMounted(() => {
      doRong();
      try { coDo = new ResizeObserver(doRong); coDo.observe(goc.value); } catch (e) { window.addEventListener('resize', doRong); }
      /* Thanh gọn hiện khi vành đã cuộn qua khỏi đầu màn. */
      try {
        theoDoi = new IntersectionObserver(([m]) => { G.gonHien = !m.isIntersecting && m.boundingClientRect.top < 0; }, {threshold: 0});
        theoDoi.observe(goc.value);
      } catch (e) { /* trình duyệt cũ: không có thanh gọn */ }
      goc.value.addEventListener('wheel', lan, {passive: false});
      /* Vòng quay mở màn: một lần mỗi phiên trình duyệt, không khi khách giảm chuyển động. */
      const ss = luu('sessionStorage');
      const daMo = ss ? ss.getItem(KHOA_MO) : '1';
      if (!RM && !daMo && n() > 1) {
        try { ss.setItem(KHOA_MO, '1'); } catch (e) { /* bỏ qua */ }
        const i = viTriDang(); pos = dich = i - 1.2; ve(false);
        setTimeout(() => { if (!keo) quayToi(viTriDang(), 2600, n(), false); }, 400);
        setTimeout(hienGoiY, 3200);
      } else { ve(true); if (!RM) setTimeout(hienGoiY, 600); else hienGoiY(); }
    });
    onBeforeUnmount(() => {
      if (theoDoi) theoDoi.disconnect(); if (coDo) coDo.disconnect();
      if (goc.value) goc.value.removeEventListener('wheel', lan);
      if (khung) window.cancelAnimationFrame(khung);
      if (henVe) window.cancelAnimationFrame(henVe);
      clearTimeout(henGoiY);
    });

    /* Phím mũi tên trên danh sách mục cho bàn phím và trình đọc màn hình. */
    function phim(e, i) {
      const N = n();
      const den = e.key === 'ArrowRight' ? i + 1 : e.key === 'ArrowLeft' ? i - 1 : e.key === 'Home' ? 0 : e.key === 'End' ? N - 1 : null;
      if (den === null) return;
      e.preventDefault();
      const j = vongQuanh(den, N);
      chon(j);
      const nut = e.currentTarget.parentNode.children[j]; if (nut && nut.focus) nut.focus();
    }

    return () => {
      const N = n(), cx = G.w / 2, cy = cao.value / 2 - 12 * s.value, vb = `${-G.w * 0.3} -40 ${G.w * 1.6} ${cao.value + 80}`;
      const vanh = nua => [veVanh(cx, cy, (HINH.RX + 12) * s.value, (HINH.RY + 10) * s.value, nua), veVanh(cx, cy, HINH.RX * 1.55 * s.value, HINH.RY * 1.45 * s.value, nua)];
      oMuc.length = N;
      const dangI = viTriDang();
      return h('div', {class: 'vanh-khung'}, [
        /* Danh sách mục cho trình đọc màn hình và bàn phím: role tablist, aria-selected. */
        h('nav', {class: 'tabs vanh-ds' + (G.phim ? ' co-phim' : ''), role: 'tablist', 'aria-label': t('vanh_nhan', 'Các mục của trang'),
          onFocusin: () => { G.phim = true; }, onFocusout: () => { G.phim = false; }},
        props.muc.map((m, i) => h('button', {key: m.tab, type: 'button', role: 'tab', class: 'tab' + (m.lop ? ' ' + m.lop : '') + (m.tab === props.dang ? ' on' : ''),
          'data-tab': m.tab, 'aria-selected': m.tab === props.dang ? 'true' : 'false', tabindex: i === dangI ? 0 : -1,
          onClick: () => chon(i), onKeydown: e => phim(e, i)}, m.nhan))),
        h('div', Object.assign({ref: goc, class: 'vanh' + (G.phim ? ' co-phim' : ''), 'aria-hidden': 'true', style: {height: cao.value + 'px'}}, suKien), [
          h('svg', {class: 'vanh-sau', viewBox: vb, preserveAspectRatio: 'none'}, vanh('b')),
          h('div', {class: 'vanh-san'}, props.muc.map((m, i) => h('div', {key: m.tab, class: 'vanh-muc', 'data-tab': m.tab, ref: el => { oMuc[i] = el; }, onClick: () => cham(i)},
            [h('span', {class: 'vanh-chu' + (m.lop ? ' ' + m.lop : '')}, [m.nhan, m.moi ? h('i', {class: 'vanh-moi'}, t('vanh_moi', 'Mới')) : null])]))),
          h('svg', {class: 'vanh-truoc', viewBox: vb, preserveAspectRatio: 'none'}, vanh('f')),
          h('div', {class: 'vanh-goi-y' + (G.goiY ? ' on' : '')}, [h('b', null, ['← ', t('vanh_goi_y_vuot', 'vuốt ngang'), ' →']), ' ', t('vanh_goi_y', 'để đổi mục'), ' · ', t('vanh_goi_y_cham', 'chạm mục để chọn')]),
        ]),
        /* Thanh gọn dính đầu màn khi đã cuộn qua vành (đề xuất, chờ anh Việt duyệt ảnh). */
        h('div', Object.assign({ref: gon, class: 'vanh-gon' + (G.gonHien ? ' on' : ''), 'aria-hidden': 'true'}, suKien), [
          h('svg', {class: 'vanh-gon-cung', viewBox: '0 0 390 56', preserveAspectRatio: 'none'}, [
            h('path', {d: 'M-10,50 Q195,8 400,50', fill: 'none', stroke: 'rgba(41,189,179,.55)', 'stroke-width': 1}),
            h('path', {d: 'M-10,54 Q195,14 400,54', fill: 'none', stroke: 'rgba(41,189,179,.14)', 'stroke-width': 5}),
          ]),
          ...[0, 1, 2].map(j => h('button', {type: 'button', tabindex: -1, class: 'vanh-gon-muc vanh-gon-' + j, ref: el => { oGon[j] = el; },
            onClick: e => { if (daDiChuyen) return; const i = Number(e.currentTarget.dataset.i); if (j !== 1 && i >= 0) chon(i); }}, [h('span')])),
        ]),
      ]);
    };
  },
};
