/* v693 (sự cố 25/11/2026, site hết trần thời gian máy chủ): nhịp đọc số từ máy chủ
   cho trang đặt bánh. THUẦN, chỉ phụ thuộc document.hidden và Date.now (truyền vào
   được để kiểm).

   - chay(): đọc ngay; đang có lượt chưa xong thì trả đúng lượt đó, không gửi thêm.
   - nhip(): gọi từ một bộ hẹn giờ chung; chỉ đọc khi tab đang hiện VÀ số đã cũ từ
     chuKy trở lên.
   - hien(): gọi khi tab hiện lại; đọc ngay nếu số cũ từ MOI_HIEN trở lên (5 giây,
     để hai sự kiện liền nhau không gửi hai lượt). */
export const MOI_HIEN = 5000;

export function nhipDoc(doc, chuKy, mt) {
  const m = mt || {};
  const bay = m.bay || (() => Date.now());
  const an = m.an || (() => typeof document !== 'undefined' && !!document.hidden);
  let luc = -Infinity, dang = null;
  function chay() {
    if (dang) return dang;
    luc = bay();
    dang = Promise.resolve().then(doc).finally(() => { dang = null; });
    return dang;
  }
  return {
    chay,
    nhip() { if (!an() && !dang && bay() - luc >= chuKy) chay().catch(() => {}); },
    hien() { if (!an() && !dang && bay() - luc >= MOI_HIEN) chay().catch(() => {}); },
    get luc() { return luc; },
  };
}
