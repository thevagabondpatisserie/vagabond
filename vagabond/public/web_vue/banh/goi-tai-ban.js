/* Phần giao diện gọi món tại bàn (v638) của tab Tại quầy: thanh giỏ dưới cùng,
   bảng chọn đá đường, giỏ (ghi chú, tên, mã giới thiệu, nút Gọi món) và các
   đơn đã gọi kèm trạng thái. Mọi số đọc từ kho-goi-ban.js; không v-html. */
import {t} from '../kho/chu.js';
import {computed} from '../lib/vue.esm-browser.prod.js';
import * as T from '../kho/thuan.js';

export const MAU_GOI_BAN = `
<div class="gb" v-if="tab==='store'">
  <section class="wrap gb-don" id="gbDon" v-if="G.don.length">
    <h2 class="gb-tieu">{{ t('goi_ban_don_da_goi','Món đã gọi') }}</h2>
    <div class="gb-the" v-for="d in donHien" :key="d.ma" :data-don="d.ma" :data-tt="d.trangThai">
      <b>{{ d.cau }}</b>
      <span v-if="d.mon">{{ d.mon }}</span>
    </div>
    <button class="btn gb-them" id="gbGoiThem" v-if="gb.cheDo.value==='goi'" @click="goiThem()">{{ t('goi_ban_goi_them','Gọi thêm món') }}</button>
  </section>

  <div class="bar gb-bar" id="gbBar" :class="{on: barMo}"><div class="wrap in">
    <span class="cnt"><b>{{ t('goi_ban_728f6901b','{so} món · {tien}',{so: gb.soMon.value, tien: tien(gb.tong.value)}) }}</b></span>
    <button class="go" id="gbXemGio" @click="G.moGio=true">{{ t('dat_banh_fb62c648d','Xem giỏ') }}</button>
  </div></div>

  <section class="sheet gb-sheet" id="gbChon" :class="{open: !!G.chon}" role="dialog" aria-modal="true" aria-labelledby="gb-chon-ten">
    <div class="wrap" v-if="G.chon">
      <div class="gb-sheet-dau"><h2 id="gb-chon-ten">{{ G.chon.m.ten }}</h2>
        <button class="close" type="button" :aria-label="t('goi_ban_dong','Đóng')" @click="G.chon=null"><svg viewBox="0 0 24 24"><path d="M5 5l14 14M19 5L5 19"/></svg></button></div>
      <div class="gb-gia">{{ tien(G.chon.m.gia) }}</div>
      <div class="gb-nhom" v-for="n in G.chon.m.tc" :key="n.nhom">
        <h3>{{ n.nhom }}</h3>
        <p class="gb-phu">{{ t('goi_ban_mac_dinh','Không chọn là pha chuẩn của quầy.') }}</p>
        <div class="sizes"><button v-for="lc in n.lua_chon" :key="lc" class="size" :class="{on: G.chon.tc[n.nhom]===lc}" :data-tc="n.nhom + '=' + lc" :aria-pressed="String(G.chon.tc[n.nhom]===lc)" @click="gb.chonTc(n.nhom, lc)"><b>{{ lc }}</b></button></div>
      </div>
      <button class="btn gb-nut" id="gbThemLy" @click="gb.xongChon()">{{ t('dat_banh_b742ca205','Thêm vào giỏ') }}</button>
    </div>
  </section>

  <section class="sheet gb-sheet" id="gbGio" :class="{open: G.moGio}" role="dialog" aria-modal="true" aria-labelledby="gb-gio-tieu">
    <div class="wrap">
      <div class="gb-sheet-dau"><h2 id="gb-gio-tieu">{{ t('goi_ban_3de60aa70','Gọi món · {ban}',{ban: gb.nhanBan.value}) }}</h2>
        <button class="close" type="button" :aria-label="t('goi_ban_dong','Đóng')" @click="G.moGio=false"><svg viewBox="0 0 24 24"><path d="M5 5l14 14M19 5L5 19"/></svg></button></div>
      <div class="gb-dong" v-for="(x,i) in G.gio" :key="x.khoa" :data-dong="x.ma">
        <div class="gb-dong-ten"><b>{{ x.ten }}</b><small v-if="gb.chuTuyChon(x.tc, x.nhom)">{{ gb.chuTuyChon(x.tc, x.nhom) }}</small><small>{{ tien(x.gia) }}</small></div>
        <div class="qty"><button type="button" :aria-label="t('goi_ban_bot','Bớt một')" @click="gb.doiSl(i,-1)">−</button><span>{{ x.sl }}</span><button type="button" :aria-label="t('goi_ban_them','Thêm một')" @click="gb.doiSl(i,1)">+</button></div>
      </div>
      <div class="fld"><label for="gb-ghi"><span>{{ t('goi_ban_ghi_chu','Ghi chú cho quầy') }}</span></label>
        <textarea id="gb-ghi" rows="2" maxlength="300" :placeholder="t('goi_ban_ghi_chu_goi','Ví dụ: mang trà ra trước, bánh để sau')" v-model="G.ghiChu"></textarea></div>
      <div class="fld"><label for="gb-ten"><span>{{ t('goi_ban_ten','Tên để quầy gọi (không bắt buộc)') }}</span></label>
        <input id="gb-ten" maxlength="40" autocomplete="off" v-model="G.ten"></div>
      <div class="fld" v-if="!G.ban || Number(G.ban.gioi_thieu) !== 0"><label for="gb-gt"><span>{{ t('goi_ban_ma_gt','Mã giới thiệu (không bắt buộc)') }}</span></label>
        <input id="gb-gt" inputmode="tel" maxlength="20" autocomplete="off" :placeholder="t('dat_banh_ma_gt_goi','Số điện thoại nhân viên giới thiệu')" v-model="G.gt" @blur="gb.kiemGt()">
        <div class="hint" id="gbGtHint">{{ G.gtHien }}</div></div>
      <p class="gb-loi" id="gbLoi" role="status" v-if="G.loi">{{ G.loi }}</p>
      <button class="btn gb-nut" id="gbGoi" :disabled="G.dangGui || !G.gio.length" @click="gb.goiMon()">{{ G.dangGui ? t('goi_ban_dang_gui','Đang gửi...') : t('goi_ban_6a9970661','Gọi món · {tien}',{tien: tien(gb.tong.value)}) }}</button>
      <p class="gb-phu" id="gbCuoi">{{ t('goi_ban_thanh_toan','Thanh toán tại quầy khi dùng xong. Nhân viên mang món ra bàn {ban}.',{ban: soBan}) }}</p>
    </div>
  </section>
</div>`;

export const GoiTaiBan = {
  name: 'GoiTaiBan',
  props: {kho: {type: Object, required: true}, tab: {type: String, default: ''}},
  template: MAU_GOI_BAN,
  setup(props) {
    const gb = props.kho.goiBan;
    const tien = n => T.tienVN(n);
    function goiThem() {
      try { window.scrollTo({top: 0, behavior: 'smooth'}); } catch (e) { /* node */ }
    }
    const G = gb.G;
    /* Biểu thức có && để ngoài khuôn: bộ dịch khuôn của Vue giải mã thực thể
       HTML khi gặp dấu & và cần DOM, bộ kiểm node không có. */
    const barMo = computed(() => G.gio.length > 0 && !G.moGio && !G.chon);
    const soBan = computed(() => (G.ban && G.ban.ban) || '');
    const donHien = computed(() => G.don.slice().reverse().map(d => ({
      ma: d.ma, cau: gb.cauDon(d), trangThai: (d.tt && d.tt.trang_thai) || 'Chờ nhận',
      mon: ((d.tt && d.tt.mon) || []).map(x => x.sl + ' ' + x.ten + ((x.tc || []).length ? ' (' + x.tc.join(', ') + ')' : '')).join(' · ')})));
    return {gb, G, t, tien, goiThem, barMo, soBan, donHien};
  }
};
