// #257: chọn/ghi nhận, huỷ PE qua Desk, bỏ đối chiếu và ghi nhận lại qua app.
const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');
(async () => {
  if (process.env.GITHUB_ACTIONS !== 'true') throw new Error('Chỉ dùng CI riêng.');
  const dich = process.env.VGB_ARTIFACTS;
  const f = JSON.parse(fs.readFileSync(path.join(dich, 'thanh-toan-fixture.json')));
  const goc = 'http://127.0.0.1:8000';
  const browser = await chromium.launch({headless: true});
  const c = await browser.newContext({viewport: {width: 390, height: 900}, serviceWorkers: 'block'});
  const ket = {dat: false, pham_vi: 'chọn/ghi nhận, huỷ PE Desk, bỏ đối chiếu và ghi nhận lại'};
  try {
    await c.route('**/*', r => new URL(r.request().url()).origin === goc ? r.continue() : r.abort());
    const dn = await c.request.post(goc + '/api/method/login', {form: {usr: 'Administrator', pwd: 'bench-only-admin'}});
    if (!dn.ok()) throw new Error('Đăng nhập thất bại');
    await c.tracing.start({screenshots: true, snapshots: true});
    const p = await c.newPage();
    const loi = [];
    p.on('pageerror', e => loi.push(e.message));
    async function mo() {
      const html = await p.goto(goc + '/ho-so-thanh-toan');
      if (!html?.ok()) throw new Error('Không mở được trang hồ sơ');
      await p.locator('[data-hs="' + f.ho_so + '"]').click();
    }
    async function xacNhan(method, tuChoi) {
      // Gắn catch ngay để lỗi click không để lại promise reject ngoài luồng.
      const doi = p.waitForResponse(r => new URL(r.url()).pathname === '/api/method/' + method,
        {timeout: 60000}).then(r => ({r}), e => ({e}));
      await p.locator('[data-hkok]').click();
      const k = await doi;
      if (k.e) throw k.e;
      const body = await k.r.json();
      if (tuChoi) {
        if (k.r.ok() || body.exc_type !== 'ValidationError' || !JSON.stringify(body).includes(tuChoi)) {
          throw new Error('Không chặn đúng lý do nghiệp vụ: ' + JSON.stringify(body));
        }
        return body;
      }
      if (!k.r.ok() || body.exc_type || !body.message) throw new Error('API thất bại: ' + method + ' ' + JSON.stringify(body));
      return body.message;
    }
    await mo();
    await p.locator('[data-hsv="khoptay"]').click();
    await p.locator('[data-tgd="' + f.giao_dich + '"]').click();
    await xacNhan('vagabond.doi_chieu_app.gan');
    // Tải lại để đọc trạng thái đã lưu, tránh bấm vào DOM cũ trong lúc go().
    await mo();
    await p.locator('[data-hsv="datra"]').click();
    const ghi = await xacNhan('vagabond.ho_so_tt.danh_dau_da_tra');
    ket.phan_hoi = {but_toan: ghi.but_toan || null, da_lam_roi: ghi.da_lam_roi || 0};
    await mo();
    await p.locator('[data-hsv="bodoichieu"]').waitFor();
    if (await p.locator('[data-hsv="datra"]').count()) throw new Error('Hồ sơ đã trả vẫn có nút ghi nhận');
    // Không được tháo sao kê khi bút toán vẫn đang ghi sổ.
    await p.locator('[data-hsv="bodoichieu"]').click();
    await xacNhan('vagabond.doi_chieu_app.bo', 'Sao kê còn liên kết bút toán');
    await p.locator('[data-hbok]').waitFor();
    await p.locator('[data-hbok]').click();
    await mo();
    await p.locator('[data-hsv="bodoichieu"]').waitFor();
    if (await p.locator('[data-hsv="datra"]').count()) throw new Error('Thao tác bị từ chối đã mở lại hồ sơ');
    ket.chan_bo_khi_con_but_toan = true;
    if (!ghi.but_toan || ghi.but_toan.includes(',')) throw new Error('Ca NCC phải trả đúng một Payment Entry');
    ket.but_toan_cu = ghi.but_toan;
    // Desk thật: chỉ huỷ riêng PE thử, không xác nhận Cancel All.
    await p.goto(goc + '/desk/payment-entry/' + encodeURIComponent(ghi.but_toan));
    const lienKet = p.waitForResponse(r => new URL(r.url()).pathname === '/api/method/frappe.desk.form.linked_with.get_submitted_linked_docs')
      .then(r => ({r}), e => ({e}));
    await p.locator('.page-head .btn-secondary').filter({hasText: /^(Cancel|Hủy|Huỷ)$/}).click();
    const lk = await lienKet;
    if (lk.e) throw lk.e;
    const lkBody = await lk.r.json();
    if (!lk.r.ok() || !lkBody.message || (lkBody.message.docs || []).length) {
      throw new Error('Không huỷ chuỗi chứng từ trong ca thử: ' + JSON.stringify(lkBody));
    }
    // ERPNext before_cancel hỏi riêng việc gỡ đối chiếu ngân hàng.
    const nganHang = p.waitForResponse(r => new URL(r.url()).pathname === '/api/method/erpnext.accounts.doctype.payment_entry.payment_entry.get_linked_bank_transactions')
      .then(r => ({r}), e => ({e}));
    await p.locator('.modal.show .modal-footer .btn-primary').click();
    const nh = await nganHang;
    if (nh.e) throw nh.e;
    const nhBody = await nh.r.json();
    if (!nh.r.ok() || JSON.stringify(nhBody.message) !== JSON.stringify([f.giao_dich])) {
      throw new Error('Desk phải xác nhận đúng một sao kê thử: ' + JSON.stringify(nhBody));
    }
    const hoiNganHang = p.locator('.modal.show').filter({hasText: 'Cancelling will automatically unreconcile it.'});
    await hoiNganHang.waitFor();
    if (!(await hoiNganHang.innerText()).includes(f.giao_dich)) throw new Error('Hộp xác nhận thiếu sao kê thử');
    const huy = p.waitForResponse(r => new URL(r.url()).pathname === '/api/method/frappe.desk.form.save.cancel')
      .then(r => ({r}), e => ({e}));
    await hoiNganHang.locator('.modal-footer .btn-primary').click();
    const hu = await huy;
    if (hu.e) throw hu.e;
    const huBody = await hu.r.json();
    if (!hu.r.ok() || huBody.exc_type || !huBody.docs?.some(d => d.name === ghi.but_toan && d.docstatus === 2)) {
      throw new Error('Desk chưa huỷ đúng bút toán: ' + JSON.stringify(huBody));
    }
    await mo();
    await p.locator('[data-hsv="bodoichieu"]').click();
    await xacNhan('vagabond.doi_chieu_app.bo');
    await mo();
    await p.locator('[data-hsv="datra"]').waitFor();
    // Đọc qua HTTP sau bước mở lại, không chỉ suy trạng thái từ nút hiện ra.
    async function docThat(doctype, name) {
      const r = await c.request.get(goc + '/api/method/frappe.client.get', {params: {doctype, name}});
      const b = await r.json();
      if (!r.ok() || !b.message) throw new Error('Không đọc được chứng từ trung gian');
      return b.message;
    }
    const moLai = await docThat('Vagabond Ho So TT', f.ho_so);
    const saoKe = await docThat('Bank Transaction', f.giao_dich);
    if (moLai.trang_thai !== 'Da duyet' || Number(moLai.da_tra) !== 0 || moLai.ngay_thanh_toan || moLai.ma_giao_dich) {
      throw new Error('Bỏ đối chiếu chưa đưa trạng thái/số tiền/ngày về đúng');
    }
    if (saoKe.payment_entries.length || Number(saoKe.unallocated_amount) !== f.tien) {
      throw new Error('Sao kê chưa sẵn sàng để dùng lại');
    }
    ket.mo_lai = {trang_thai: moLai.trang_thai, da_tra: moLai.da_tra,
      ngay_thanh_toan: moLai.ngay_thanh_toan, chua_phan_bo: saoKe.unallocated_amount};
    // Dùng lại đúng sao kê, ghi nhận kế toán lại; không chuyển tiền mới.
    await p.locator('[data-hsv="khoptay"]').click();
    await p.locator('[data-tgd="' + f.giao_dich + '"]').click();
    await xacNhan('vagabond.doi_chieu_app.gan');
    await mo();
    await p.locator('[data-hsv="datra"]').click();
    const ghiLai = await xacNhan('vagabond.ho_so_tt.danh_dau_da_tra');
    if (!ghiLai.but_toan || ghiLai.but_toan === ghi.but_toan) throw new Error('Chưa tạo bút toán thay thế');
    ket.but_toan_moi = ghiLai.but_toan;
    await mo();
    await p.locator('[data-hsv="bodoichieu"]').waitFor();
    if (await p.locator('[data-hsv="datra"]').count()) throw new Error('Ghi nhận lại chưa xong');
    if (loi.length) throw new Error(loi.join('\n'));
    await p.screenshot({path: path.join(dich, 'thanh-toan-da-tra.png'), fullPage: true});
    ket.dat = true;
  } catch (e) {ket.loi = e.stack; throw e;}
  finally {
    await c.tracing.stop({path: path.join(dich, 'thanh-toan.zip')}).catch(() => {});
    await browser.close();
    fs.writeFileSync(path.join(dich, 'thanh-toan-browser.json'), JSON.stringify(ket, null, 2));
  }
})().catch(e => {console.error(e); process.exitCode = 1;});
