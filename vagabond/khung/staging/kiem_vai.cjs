// Quyen HTTP bang tai khoan tong hop; chua thay the UAT thao tac tung vai.
const fs = require('fs');
const path = require('path');
const {request} = require('playwright');
(async () => {
  if (process.env.GITHUB_ACTIONS !== 'true') throw new Error('Chi dung CI rieng.');
  const dich = process.env.VGB_ARTIFACTS;
  const f = JSON.parse(fs.readFileSync(path.join(dich, 'vai-fixture.json')));
  const hoSo = JSON.parse(fs.readFileSync(path.join(dich, 'thanh-toan-fixture.json'))).ho_so;
  const goc = 'http://127.0.0.1:8000';
  const ket = [];
  try {
    for (const [vai, profile] of Object.entries(f)) {
      const c = await request.newContext({baseURL: goc});
      try {
        const login = await c.post('/api/method/login', {form: {usr: profile.user, pwd: 'bench-only-roles-257'}});
        if (!login.ok()) throw new Error('Dang nhap that bai: ' + vai);
        const boot = await c.get('/api/method/vagabond.nhan_su.khoi_dong');
        const b = await boot.json();
        if (!boot.ok() || !Array.isArray(b.message?.vai) ||
            JSON.stringify([...b.message.vai].sort()) !== JSON.stringify(profile.roles)) {
          throw new Error('Vai HTTP khac fixture: ' + vai);
        }
        // Tai khoan kho/bep/sales khong duoc doc ho so tai chinh.
        const r = await c.get('/api/method/vagabond.ho_so_tt.danh_sach');
        const body = await r.json();
        const thongBao = JSON.parse(body._server_messages || '[]')
          .map(x => typeof x === 'string' ? JSON.parse(x).message : x.message).join('\n');
        if (vai === 'ke_toan') {
          if (!r.ok() || !Array.isArray(body.message?.rows) ||
              !body.message.rows.some(x => x.name === hoSo)) throw new Error('Ke toan khong doc duoc ho so thu');
        } else if (r.status() !== 417 || body.exc_type !== 'ValidationError' ||
            !thongBao.includes('không có quyền xem hồ sơ thanh toán') || body.message) {
          throw new Error('Cua tai chinh khong chan dung vai ' + vai);
        }
        ket.push({vai, dat: true, quyen_tai_chinh: vai === 'ke_toan' ? 'doc' : 'bi_chan'});
      } finally {await c.dispose();}
    }
  } finally {
    fs.writeFileSync(path.join(dich, 'vai-http.json'), JSON.stringify(ket, null, 2));
  }
  if (ket.length !== 4) throw new Error('Chua kiem du bon vai');
})().catch(e => {console.error(e); process.exitCode = 1;});
