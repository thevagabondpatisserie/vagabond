/* Câu có chữ đậm, chữ màu hoặc liên kết, KHÔNG dùng v-html.

   Trang cũ ghép HTML bằng tay rồi gán innerHTML, phải nhớ esc() từng mảnh
   (bài học #367: nhãn CMS phải escape cả nhánh lỗi). Ở đây một câu là một
   mảng mảnh {chu, dam, mau, href}; thành phần DongChu vẽ từng mảnh bằng chữ
   thường của Vue, nên chữ marketing không bao giờ thành thẻ HTML. */

export const thuong = chu => ({chu: String(chu ?? '')});
export const dam = (chu, mau) => ({chu: String(chu ?? ''), dam: true, mau: mau || ''});
export const mau = (chu, m) => ({chu: String(chu ?? ''), mau: m});
export const lienKet = (chu, href, moi) => ({chu: String(chu ?? ''), href, moi: !!moi});

/* "Nhận {so} bánh" + {so: 3} -> [thuong('Nhận '), dam('3'), thuong(' bánh')].
   Chỗ điền thiếu trong `thay` thì bỏ trống, không để lại ngoặc (cauNhan cũ). */
export function cauCoSo(mau0, thay) {
  const ra = [];
  let i = 0;
  String(mau0 || '').replace(/\{([a-z_]+)\}/g, (g, k, vt) => {
    if (vt > i) ra.push(thuong(mau0.slice(i, vt)));
    if (thay && k in thay) ra.push(dam(thay[k]));
    i = vt + g.length;
    return g;
  });
  if (i < String(mau0 || '').length) ra.push(thuong(String(mau0).slice(i)));
  return ra;
}

export function noi(...cac) {
  /* Nối nhiều câu/mảnh thành một mảng phẳng. */
  const ra = [];
  cac.forEach(x => { if (!x) return; if (Array.isArray(x)) ra.push(...x.filter(Boolean)); else ra.push(x); });
  return ra;
}

export function chuPhang(phan) { return (phan || []).map(x => x.chu).join(''); }
