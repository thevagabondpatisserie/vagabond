/* Phần giao diện gọi món tại bàn (v638, v639 vòng 2 theo mẫu anh Việt duyệt
   05/11/2026) của tab Tại quầy. Hai thành phần:

   - GoiTaiBan: phần NẰM TRONG DÒNG của tab (các đơn đã gọi kèm trạng thái,
     nút Gọi thêm), đặt ngay dưới nhãn bàn để khách thấy trước danh sách món.
   - GoiTaiBanNoi: phần NỔI (thanh giỏ dưới cùng, bảng chọn một món, giỏ,
     bảng chuông gọi nhân viên). Phải đặt NGOÀI <main>: main có z-index riêng
     nên bảng nằm trong main bị dải tab (sticky) và nút nổi đè lên (ảnh anh
     Việt chụp 05/11/2026).

   Mọi số đọc từ kho-goi-ban.js; không v-html. */
import {t} from '../kho/chu.js';
import {computed, ref, watch} from '../lib/vue.esm-browser.prod.js';
import * as T from '../kho/thuan.js';
import {AnhMon} from './thanh-phan.js';
import {giaDong, LY_DO_GOI, CACH_TRA, TT_KHONG_TINH, moTaCombo} from './kho-goi-ban.js';
import {BieuTuong, ICON_LY_DO} from './bieu-tuong.js';


/* Khối "đã gọi" là khối CHỈ ĐỂ ĐỌC, không được lấn chỗ khối để bấm (AGENTS.md
   2b.17, Codex PR #542 vòng 1): thu về MỘT dòng đếm số đơn kèm trạng thái đơn
   mới nhất, bấm mới mở chi tiết; nút Gọi thêm món đứng cùng dòng, trong màn
   đầu. Đơn bị từ chối hoặc hết hạn thì tự mở chi tiết vì khách phải xử lý.
   Dòng món của một đơn: hai món đầu rồi "và N nữa", không nối cả danh sách. */
export const MON_HIEN_TOI_DA = 2;

export const MAU_GOI_BAN = `
<section class="wrap gb-don" id="gbDon" v-if="hien">
  <div class="gb-tom">
    <button type="button" class="gb-tom-chu" id="gbDonXem" :aria-expanded="hienChiTiet ? 'true' : 'false'" @click="bat()">
      <b>{{ t('goi_ban_da_goi_n','Đã gọi {n} đơn', {n: G.don.length}) }}</b>
      <small>{{ ttMoi }}</small>
      <span class="gb-tom-mo">{{ hienChiTiet ? t('goi_ban_thu_gon','Thu gọn') : t('goi_ban_xem_chi_tiet','Xem chi tiết') }}</span>
    </button>
    <button class="btn gb-them" id="gbGoiThem" v-if="gb.cheDo.value==='goi'" @click="goiThem()">{{ t('goi_ban_goi_them','Gọi thêm món') }}</button>
  </div>
  <div class="gb-chi-tiet" id="gbDonChiTiet" v-if="hienChiTiet">
    <div class="gb-the" v-for="d in donHien" :key="d.ma" :data-don="d.ma" :data-tt="d.trangThai">
      <b>{{ d.cau }}</b>
      <span v-if="d.mon">{{ d.mon }}</span>
    </div>
  </div>
</section>`;

const TT_CAN_XU_LY = ['Từ chối', 'Hết hạn'];

/* Phép thuần: dòng món của một đơn, tối đa MON_HIEN_TOI_DA món rồi "và N nữa". */
export function dongMonNgan(mon, tVa) {
  const ds = (mon || []).map(x => x.sl + ' ' + x.ten + ((x.tc || []).length ? ' (' + x.tc.join(', ') + ')' : ''));
  if (ds.length <= MON_HIEN_TOI_DA) return ds.join(', ');
  return ds.slice(0, MON_HIEN_TOI_DA).join(', ') + ' ' + tVa(ds.length - MON_HIEN_TOI_DA);
}

export const GoiTaiBan = {
  name: 'GoiTaiBan',
  props: {kho: {type: Object, required: true}, tab: {type: String, default: ''}},
  template: MAU_GOI_BAN,
  setup(props) {
    const gb = props.kho.goiBan;
    const G = gb.G;
    const mo = ref(null); /* null: tự theo trạng thái; true/false: khách đã bấm */
    function goiThem() {
      try { const n = document.getElementById('gbTim'); if (n && n.scrollIntoView) n.scrollIntoView({block: 'start', behavior: 'smooth'}); } catch (e) { /* node */ }
    }
    function bat() { mo.value = !hienChiTiet.value; }
    /* Biểu thức có && để ngoài khuôn: bộ dịch khuôn của Vue giải mã thực thể
       HTML khi gặp dấu & và cần DOM, bộ kiểm node không có. */
    const hien = computed(() => props.tab === 'store' && G.don.length > 0);
    const canXuLy = computed(() => G.don.some(d => TT_CAN_XU_LY.includes((d.tt && d.tt.trang_thai) || '')));
    const hienChiTiet = computed(() => (mo.value === null ? canXuLy.value : mo.value));
    /* Có đơn mới bị từ chối hoặc hết hạn sau khi khách đã gập: mở lại cho khách thấy. */
    watch(canXuLy, (moi, cu) => { if (moi && !cu) mo.value = null; });
    const ttMoi = computed(() => (G.don.length ? gb.cauDon(G.don[G.don.length - 1]) : ''));
    const donHien = computed(() => G.don.slice().reverse().map(d => ({
      ma: d.ma, cau: gb.cauDon(d), trangThai: (d.tt && d.tt.trang_thai) || 'Chờ nhận',
      mon: dongMonNgan((d.tt && d.tt.mon) || [], n => t('goi_ban_va_nua', 'và {n} nữa', {n}))})));
    return {gb, G, t, goiThem, bat, donHien, hien, hienChiTiet, ttMoi};
  }
};

export const MAU_GOI_BAN_NOI = `
<div class="gb" v-if="tab==='store'">
  <div class="bar gb-bar" id="gbBar" :class="{on: gb.barMo.value}"><div class="wrap in">
    <span class="cnt"><b>{{ t('goi_ban_728f6901b','{so} món · {tien}',{so: gb.soMon.value, tien: tien(gb.tong.value)}) }}</b></span>
    <button class="go" id="gbXemGio" @click="G.moGio=true">{{ t('dat_banh_fb62c648d','Xem giỏ') }}</button>
  </div></div>

  <div class="bar gb-bar gb-bar-don" id="gbBarDon" :class="{on: gb.barDon.value}"><div class="wrap in">
    <button type="button" class="gb-bar-chu" id="gbBarDonChu" @click="gb.moDon()"><b>{{ t('goi_ban_0dc232137','Bàn {ban} · Đã gọi {n} lượt',{ban: soBan, n: G.don.length}) }}</b>
      <small>{{ t('goi_ban_bar_tam','Tạm tính {tien}',{tien: tien(gb.tom.value.tamTinh)}) }}<template v-if="gb.tom.value.choNhan"> · {{ t('goi_ban_bar_cho','{n} lượt chờ quầy nhận',{n: gb.tom.value.choNhan}) }}</template></small></button>
    <button class="go" id="gbXemDon" type="button" @click="gb.moDon()">{{ t('goi_ban_xem_don','Xem đơn') }}</button>
  </div></div>

  <section class="sheet gb-sheet" id="gbChon" :class="{open: !!G.chon}" role="dialog" aria-modal="true" aria-labelledby="gb-chon-ten">
    <div class="gb-khung" v-if="G.chon">
      <header class="gb-dau-bang"><div class="gb-dau-chu"><small v-if="G.chon.m.nhomTen">{{ G.chon.m.nhomTen }}</small><h2 id="gb-chon-ten">{{ G.chon.m.ten }}</h2></div>
        <button class="gb-x" type="button" :aria-label="t('goi_ban_dong','Đóng')" @click="G.chon=null"><bieu-tuong ten="dong"/></button></header>
      <div class="gb-than">
        <div class="gb-anh" v-if="G.chon.m.anh"><anh-mon :src="G.chon.m.anh"/></div>
        <div class="gb-gia" id="gbGiaChon">{{ tien(gb.giaChon.value) }}</div>
        <p class="gb-mo-ta" v-if="G.chon.m.mo_ta">{{ G.chon.m.mo_ta }}</p>
        <div class="gb-nhom" id="gbSize" v-if="G.chon.m.bienThe.length > 1">
          <div class="gb-nhom-dau"><h3>{{ t('goi_ban_size','Size') }}</h3><i>{{ t('goi_ban_chon_mot','chọn một') }}</i></div>
          <div class="gb-vien-ds"><button v-for="bt in G.chon.m.bienThe" :key="bt.ma" type="button" class="gb-vien" :class="{on: G.chon.bt.ma===bt.ma}" :data-size="bt.ma" :aria-pressed="String(G.chon.bt.ma===bt.ma)" @click="gb.chonBienThe(bt)">{{ bt.size || bt.ten }}<small>{{ tien(bt.gia) }}</small></button></div>
        </div>
        <div class="gb-nhom" v-for="n in G.chon.nhomTc" :key="n.nhom">
          <div class="gb-nhom-dau"><h3>{{ n.nhom }}</h3><i>{{ t('goi_ban_chon_mot','chọn một') }}</i></div>
          <div class="gb-vien-ds"><button v-for="lc in n.lua_chon" :key="lc" type="button" class="gb-vien" :class="{on: G.chon.tc[n.nhom]===lc}" :data-tc="n.nhom + '=' + lc" :aria-pressed="String(G.chon.tc[n.nhom]===lc)" @click="gb.chonTc(n.nhom, lc)">{{ lc }}</button></div>
        </div>
        <div class="gb-nhom" id="gbTopping" v-if="G.chon.topping.length">
          <div class="gb-nhom-dau"><h3>{{ t('goi_ban_topping','Thêm topping') }}</h3><i>{{ t('goi_ban_chon_nhieu','chọn nhiều') }}</i></div>
          <button v-for="x in G.chon.topping" :key="x.ma" type="button" class="gb-tp" :class="{on: !!G.chon.tp[x.ma]}" :data-tp="x.ma" role="checkbox" :aria-checked="String(!!G.chon.tp[x.ma])" @click="gb.chonTp(x.ma)">
            <i class="gb-cb" aria-hidden="true"><bieu-tuong ten="tick"/></i><span>{{ x.ten }}</span><b>+{{ tien(x.gia) }}</b></button>
        </div>
      </div>
      <footer class="gb-day">
        <div class="gb-step"><button type="button" :aria-label="t('goi_ban_bot','Bớt một')" @click="gb.doiSlChon(-1)"><bieu-tuong ten="tru"/></button><span id="gbSlChon">{{ G.chon.sl }}</span><button type="button" :aria-label="t('goi_ban_them','Thêm một')" @click="gb.doiSlChon(1)"><bieu-tuong ten="cong"/></button></div>
        <button type="button" class="gb-cta" id="gbThemLy" @click="gb.xongChon()">{{ t('goi_ban_c7d1e2f3a','Thêm · {tien}',{tien: tien(gb.tongChon.value)}) }}</button>
      </footer>
    </div>
  </section>

  <section class="sheet gb-sheet" id="gbGio" :class="{open: G.moGio}" role="dialog" aria-modal="true" aria-labelledby="gb-gio-tieu">
    <div class="gb-khung">
      <header class="gb-dau-bang"><div class="gb-dau-chu"><small>{{ gb.nhanBan.value }}</small><h2 id="gb-gio-tieu">{{ G.don.length ? t('goi_ban_goi_them','Gọi thêm món') : t('goi_ban_goi_mon','Gọi món') }}</h2></div>
        <button class="gb-x" type="button" :aria-label="t('goi_ban_dong','Đóng')" @click="G.moGio=false"><bieu-tuong ten="dong"/></button></header>
      <div class="gb-than">
        <div class="gb-dong" v-for="(x,i) in G.gio" :key="x.khoa" :data-dong="x.ma">
          <span class="gb-dong-anh"><anh-mon :src="x.anh"/></span>
          <div class="gb-dong-ten"><b>{{ x.ten }}</b><small v-if="chuDong(x)">{{ chuDong(x) }}</small>
            <div class="gb-dong-duoi"><em>{{ tien(giaDong(x) * x.sl) }}</em>
              <div class="gb-step gb-step-nho"><button type="button" :aria-label="t('goi_ban_bot','Bớt một')" @click="gb.doiSl(i,-1)"><bieu-tuong ten="tru"/></button><span>{{ x.sl }}</span><button type="button" :aria-label="t('goi_ban_them','Thêm một')" @click="gb.doiSl(i,1)"><bieu-tuong ten="cong"/></button></div></div>
          </div>
        </div>
        <div class="fld"><label for="gb-ghi"><span>{{ t('goi_ban_ghi_chu','Ghi chú cho quầy') }}</span></label>
          <textarea id="gb-ghi" rows="2" maxlength="300" :placeholder="t('goi_ban_ghi_chu_goi','Ví dụ: mang trà ra trước, bánh để sau')" v-model="G.ghiChu"></textarea></div>
        <div class="fld"><label for="gb-ten"><span>{{ t('goi_ban_ten','Tên để quầy gọi (không bắt buộc)') }}</span></label>
          <input id="gb-ten" maxlength="40" autocomplete="off" v-model="G.ten"></div>
        <div class="fld" v-if="!G.ban || Number(G.ban.gioi_thieu) !== 0"><label for="gb-gt"><span>{{ t('goi_ban_ma_gt','Mã giới thiệu (không bắt buộc)') }}</span></label>
          <input id="gb-gt" inputmode="tel" maxlength="20" autocomplete="off" :placeholder="t('dat_banh_ma_gt_goi','Số điện thoại nhân viên giới thiệu')" v-model="G.gt" @blur="gb.kiemGt()">
          <div class="hint" id="gbGtHint">{{ G.gtHien }}</div></div>
        <p class="gb-phu" id="gbCuoi">{{ G.don.length ? t('goi_ban_cung_bill','Gọi thêm sẽ cộng vào cùng bill của bàn {ban}. Thanh toán tại quầy khi dùng xong, hoặc bấm Xin tính tiền để nhân viên mang bill ra bàn.',{ban: soBan}) : t('goi_ban_thanh_toan','Thanh toán tại quầy khi dùng xong. Nhân viên mang món ra bàn {ban}.',{ban: soBan}) }}</p>
        <div class="gb-hai">
          <button class="gb-ghost" id="gbGioChuong" type="button" @click="moChuong('')"><bieu-tuong ten="chuong"/>{{ t('goi_ban_chuong_nut','Gọi nhân viên') }}</button>
          <button class="gb-ghost" id="gbGioTinhTien" type="button" @click="moChuong(LY_DO_GOI[1])"><bieu-tuong ten="hoaDon"/>{{ t('goi_ban_xin_tinh_tien','Xin tính tiền') }}</button>
        </div>
      </div>
      <footer class="gb-day gb-day-doc">
        <p class="gb-loi" id="gbLoi" role="status" v-if="G.loi">{{ G.loi }}</p>
        <div class="gb-tong"><span>{{ t('goi_ban_so_mon','{so} món',{so: gb.soMon.value}) }}</span><b>{{ tien(gb.tong.value) }}</b></div>
        <button type="button" class="gb-cta" id="gbGoi" :disabled="G.dangGui || !G.gio.length" @click="gb.goiMon()">{{ G.dangGui ? t('goi_ban_dang_gui','Đang gửi...') : (G.don.length ? t('goi_ban_d8e2f3a4b','Gọi thêm · {tien}',{tien: tien(gb.tong.value)}) : t('goi_ban_6a9970661','Gọi món · {tien}',{tien: tien(gb.tong.value)})) }}</button>
      </footer>
    </div>
  </section>

  <section class="sheet gb-sheet" id="gbDonBan" :class="{open: G.moDon}" role="dialog" aria-modal="true" aria-labelledby="gb-don-tieu">
    <div class="gb-khung">
      <header class="gb-dau-bang"><div class="gb-dau-chu"><small>{{ gb.nhanBan.value }}</small><h2 id="gb-don-tieu">{{ t('goi_ban_don_ban','Đơn của bàn') }}</h2></div>
        <button class="gb-x" type="button" :aria-label="t('goi_ban_dong','Đóng')" @click="gb.dongDon()"><bieu-tuong ten="dong"/></button></header>
      <div class="gb-than">
        <div class="gb-luot" v-for="l in luot" :key="l.ma" :data-luot="l.ma" :data-tt="l.trangThai" :class="{tat: l.khongTinh}">
          <div class="gb-luot-dau"><b>{{ l.tieuDe }}</b><span class="gb-tt" :class="l.lop">{{ l.cau }}</span></div>
          <div class="gb-luot-dong" v-for="(x, i) in l.mon" :key="i"><span>{{ x.sl }} × {{ x.ten }}<small v-if="(x.tc || []).length">{{ x.tc.join(' · ') }}</small></span><em>{{ tien(x.tien) }}</em></div>
        </div>
        <div class="gb-tong-ban" id="gbTongBan">
          <div><span>{{ t('goi_ban_tam_tinh_n','Tạm tính ({n} món)',{n: gb.tom.value.soMon}) }}</span><span>{{ tien(gb.tom.value.tamTinh) }}</span></div>
          <div class="lon"><span>{{ t('goi_ban_can_tra','Cần thanh toán') }}</span><b>{{ tien(gb.tom.value.tamTinh) }}</b></div>
          <p class="gb-phu">{{ t('goi_ban_chot_khi_in','Số tiền chốt khi quầy in bill. Lượt chờ quầy nhận chưa tính chắc; lượt quầy từ chối không tính.') }}</p>
        </div>
        <div class="gb-hai">
          <button class="gb-ghost" id="gbDonGoiThem" type="button" @click="goiThem()"><bieu-tuong ten="cong"/>{{ t('goi_ban_goi_them','Gọi thêm món') }}</button>
          <button class="gb-ghost" id="gbDonChuong" type="button" @click="moChuong('')"><bieu-tuong ten="chuong"/>{{ t('goi_ban_chuong_nut','Gọi nhân viên') }}</button>
        </div>
      </div>
      <footer class="gb-day gb-day-doc">
        <button type="button" class="gb-cta" id="gbDonTra" :disabled="!gb.tom.value.soLuot" @click="gb.moTra()">{{ t('goi_ban_cd6cd79ce','Thanh toán · {tien}',{tien: tien(gb.tom.value.tamTinh)}) }}</button>
      </footer>
    </div>
  </section>

  <section class="sheet gb-sheet" id="gbTra" :class="{open: G.tra.mo}" role="dialog" aria-modal="true" aria-labelledby="gb-tra-tieu">
    <div class="gb-khung">
      <header class="gb-dau-bang"><div class="gb-dau-chu"><small>{{ gb.nhanBan.value }}</small><h2 id="gb-tra-tieu">{{ t('goi_ban_thanh_toan_tieu','Thanh toán') }}</h2></div>
        <button class="gb-x" type="button" :aria-label="t('goi_ban_dong','Đóng')" @click="gb.dongTra()"><bieu-tuong ten="dong"/></button></header>
      <div class="gb-than">
        <template v-if="G.tra.xong">
          <div class="gb-xong" id="gbTraXong"><b>{{ G.tra.xong.cach==='ban' ? t('goi_ban_tra_xong_ban','Đã báo quầy lúc {gio}. Nhân viên mang bill ra bàn {ban} trong giây lát.',{gio: G.tra.xong.luc, ban: soBan}) : t('goi_ban_tra_xong_quay','Đã báo quầy lúc {gio}. Quý khách ra quầy, báo bàn {ban} với thu ngân.',{gio: G.tra.xong.luc, ban: soBan}) }}</b>
            <span>{{ t('goi_ban_tra_bill_moi','Gọi thêm món sau khi đã thanh toán sẽ thành một bill mới.') }}</span></div>
        </template>
        <template v-else>
          <div class="gb-tong-ban"><div class="lon"><span>{{ t('goi_ban_can_tra','Cần thanh toán') }}</span><b>{{ tien(gb.tom.value.tamTinh) }}</b></div></div>
          <button v-for="c in CACH_TRA" :key="c.ma" type="button" class="gb-ly" :class="{on: G.tra.cach===c.ma}" :data-cach="c.ma" :aria-pressed="String(G.tra.cach===c.ma)" @click="G.tra.cach=c.ma">
            <i class="gb-ly-ic" aria-hidden="true"><bieu-tuong :ten="c.ma==='ban' ? 'hoaDon' : 'cuaHang'"/></i><span><b>{{ c.ten }}</b><small>{{ c.phu }}</small></span><i class="gb-ly-chon" aria-hidden="true"></i></button>
          <div class="fld"><label for="gb-tra-hd"><span>{{ t('goi_ban_tra_hd','Xuất hoá đơn điện tử (không bắt buộc)') }}</span></label>
            <input id="gb-tra-hd" maxlength="80" autocomplete="off" :placeholder="t('goi_ban_tra_hd_goi','Mã số thuế hoặc email nhận hoá đơn')" v-model="G.tra.hd">
            <div class="hint">{{ t('goi_ban_tra_hd_phu','Có mã số thuế thì thu ngân hỏi thêm tên công ty khi in bill.') }}</div></div>
          <p class="gb-phu">{{ t('goi_ban_tra_chua_online','Thanh toán online ngay tại bàn sẽ mở sau. Gọi thêm món sau khi đã thanh toán sẽ thành một bill mới.') }}</p>
        </template>
      </div>
      <footer class="gb-day gb-day-doc">
        <p class="gb-loi" id="gbTraLoi" role="status" v-if="G.tra.loi">{{ G.tra.loi }}</p>
        <button v-if="G.tra.xong" type="button" class="gb-cta" @click="gb.dongTra()">{{ t('goi_ban_dong','Đóng') }}</button>
        <button v-else type="button" class="gb-cta" id="gbTraGui" :disabled="G.tra.dangGui || !G.tra.cach" @click="gb.guiTra()">{{ G.tra.dangGui ? t('goi_ban_dang_gui','Đang gửi...') : t('goi_ban_tra_gui','Báo quầy tính tiền') }}</button>
      </footer>
    </div>
  </section>

  <section class="sheet gb-sheet" id="gbChuong" :class="{open: G.chuong.mo}" role="dialog" aria-modal="true" aria-labelledby="gb-chuong-tieu">
    <div class="gb-khung">
      <header class="gb-dau-bang"><div class="gb-dau-chu"><small>{{ gb.nhanBan.value }}</small><h2 id="gb-chuong-tieu">{{ t('goi_ban_chuong_nut','Gọi nhân viên') }}</h2></div>
        <button class="gb-x" type="button" :aria-label="t('goi_ban_dong','Đóng')" @click="gb.dongChuong()"><bieu-tuong ten="dong"/></button></header>
      <div class="gb-than">
        <template v-if="G.chuong.xong">
          <div class="gb-xong" id="gbChuongXong"><b>{{ t('goi_ban_chuong_da_bao','Đã báo quầy lúc {gio}. Nhân viên tới bàn {ban} trong giây lát.',{gio: G.chuong.xong.luc, ban: soBan}) }}</b>
            <span>{{ G.chuong.xong.lyDo }}</span>
            <span>{{ t('goi_ban_chuong_qua_lau','Quá 3 phút chưa thấy, quý khách bấm lại hoặc nhắn Zalo.') }}</span></div>
        </template>
        <template v-else>
          <p class="gb-phu gb-chuong-dau">{{ t('goi_ban_chuong_hoi','Quý khách cần gì? Nhân viên tới ngay.') }}</p>
          <button v-for="(ly, i) in LY_DO_GOI" :key="ly" type="button" class="gb-ly" :class="{on: G.chuong.lyDo===ly}" :data-lydo="ly" :aria-pressed="String(G.chuong.lyDo===ly)" @click="G.chuong.lyDo=ly">
            <i class="gb-ly-ic" aria-hidden="true"><bieu-tuong :ten="ICON_LY_DO[i]"/></i><span><b>{{ ly }}</b><small>{{ phuLyDo[i] }}</small></span><i class="gb-ly-chon" aria-hidden="true"></i></button>
          <div class="fld" v-if="G.chuong.lyDo===LY_DO_GOI[4]"><label for="gb-chuong-chi-tiet"><span>{{ t('goi_ban_chuong_chi_tiet','Gõ vài chữ cho quầy') }}</span></label>
            <input id="gb-chuong-chi-tiet" maxlength="120" autocomplete="off" v-model="G.chuong.chiTiet"></div>
          <p class="gb-phu">{{ t('goi_ban_chuong_gioi_han','Mỗi bàn bấm được tối đa 3 lần trong 10 phút để tránh bấm nhầm.') }}</p>
        </template>
      </div>
      <footer class="gb-day gb-day-doc">
        <p class="gb-loi" id="gbChuongLoi" role="status" v-if="G.chuong.loi">{{ G.chuong.loi }}</p>
        <button v-if="G.chuong.xong" type="button" class="gb-cta" @click="gb.dongChuong()">{{ t('goi_ban_dong','Đóng') }}</button>
        <button v-else type="button" class="gb-cta" id="gbChuongGui" :disabled="G.chuong.dangGui || !G.chuong.lyDo" @click="gb.goiNhanVien()">{{ G.chuong.dangGui ? t('goi_ban_dang_gui','Đang gửi...') : t('goi_ban_chuong_gui','Báo quầy') }}</button>
      </footer>
    </div>
  </section>
</div>`;

export const GoiTaiBanNoi = {
  name: 'GoiTaiBanNoi',
  props: {kho: {type: Object, required: true}, tab: {type: String, default: ''}},
  components: {AnhMon, BieuTuong},
  template: MAU_GOI_BAN_NOI,
  setup(props) {
    const gb = props.kho.goiBan;
    const G = gb.G;
    const tien = n => T.tienVN(n);
    const soBan = computed(() => (G.ban && G.ban.ban) || '');
    const phuLyDo = [
      t('goi_ban_ly_1', 'Có việc cần hỏi, cần hỗ trợ tại bàn'),
      t('goi_ban_ly_2', 'Nhân viên mang bill ra, trả tại bàn hoặc tại quầy'),
      t('goi_ban_ly_3', 'Miễn phí'),
      t('goi_ban_ly_4', 'Nhân viên mang ra bàn'),
      t('goi_ban_ly_5', 'Gõ vài chữ cho quầy')];
    function moChuong(lyDo) { G.moGio = false; gb.moChuong(lyDo); }
    /* v642 màn Đơn của bàn: lượt mới nhất trên cùng; lượt bị từ chối, hết hạn
       vẫn hiện (khách biết món nào không lên) nhưng mờ và không vào tổng. */
    const luot = computed(() => G.don.map((d, i) => ({d, so: i + 1})).reverse().map(({d, so}) => {
      const tt = (d.tt && d.tt.trang_thai) || 'Chờ nhận';
      const luc = (d.tt && d.tt.luc) || '';
      return {ma: d.ma, trangThai: tt, khongTinh: TT_KHONG_TINH.includes(tt), cau: gb.cauDon(d),
        lop: tt === 'Đã nhận' ? 'ok' : (TT_KHONG_TINH.includes(tt) ? 'tat' : 'cho'),
        tieuDe: t('goi_ban_luot','Lượt {so}',{so}) + (luc ? ' · ' + luc : ''), mon: (d.tt && d.tt.mon) || []};
    }));
    /* Gọi thêm từ màn Đơn của bàn: đóng màn, đưa khách về ô tìm món. */
    function goiThem() {
      gb.dongDon();
      try { const n = document.getElementById('gbTim'); if (n && n.scrollIntoView) n.scrollIntoView({block: 'start', behavior: 'smooth'}); } catch (e) { /* node */ }
    }
    /* Dòng phụ của một món trong giỏ: tuỳ chọn rồi topping, gọn một dòng. */
    const chuDong = x => [x.thanhPhan ? moTaCombo(x.thanhPhan) : gb.chuTuyChon(x.tc, x.nhom), (x.tp || []).length ? '+ ' + x.tp.map(y => y.ten).join(', ') : '']
      .filter(Boolean).join(' · ');
    return {gb, G, t, tien, soBan, giaDong, LY_DO_GOI, ICON_LY_DO, phuLyDo, moChuong, chuDong, luot, goiThem, CACH_TRA};
  }
};
