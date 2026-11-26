/* Khuôn giao diện trang đặt bánh bản Vue. Thẻ, lớp, id CHÉP từ banh.html
   bản Rocca (a20e85054) để CSS đã duyệt áp y nguyên. Sửa giao diện thì sửa ở
   đây và so ảnh với bản cũ ở 390, 1440, 320 trước khi bàn giao. */
const GOI = 'M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2Z';

export const MAU = `
<header><div class="wrap hd">
  <div class="hd-left"><a :href="hm('#/')" @click.prevent="nav('#/')" :aria-label="t('dat_banh_86376d53a','Về trang chủ')"><img class="logo" :src="LOGO" :alt="t('dat_banh_913466c0d','The Vagabond Pâtisserie')"></a></div>
  <a class="hd-phone" :href="'tel:'+telSo()"><svg viewBox="0 0 24 24"><path d="${GOI}"/></svg>{{ telChu() }}</a>
  <nav class="dich-vu" :aria-label="t('dat_banh_2c5093996','Dịch vụ')"><a href="/dat-ban">{{ t('nut_dat_ban','Đặt bàn') }}</a><a href="/banh-si">{{ t('nut_khach_si','Khách sỉ') }}</a><a href="/thanh-vien">{{ t('nut_thanh_vien','Thành viên') }}</a></nav>
</div></header>

<div id="noi-dung-marketing" data-vgb-vi-tri="dau_trang" :aria-label="t('dat_banh_f4a541343','Lời chào từ chúng tôi')"><khoi-noi-dung vi-tri="dau_trang"/></div>
<div id="danh-muc-banh" tabindex="-1"></div>
<p class="ngay-ban" id="ngayBan">{{ ngayBan }}</p>
<vanh-nghieng :muc="mucVanh" :dang="tab" @chon="go"/>

<section class="wrap" id="uu_dai" :hidden="tab!=='uu_dai'"><header class="sec-head"><h1 class="h1">{{ t('tab_uu_dai','Ưu đãi') }}</h1></header><chuyen-muc v-if="tab==='uu_dai'" loai="uu_dai"/></section>
<section class="wrap" id="tiec" :hidden="tab!=='tiec'"><ve-su-kien v-if="tab==='tiec'"/></section>
<section class="wrap" id="dac_biet" :hidden="tab!=='dac_biet'"><dac-biet-tuan v-if="tab==='dac_biet'" :kho="kho" :mo="moBanh"/></section>
<section class="wrap" id="thiet_ke_rieng" :hidden="tab!=='thiet_ke_rieng'"><thiet-ke-rieng v-if="tab==='thiet_ke_rieng'"/></section>
<section class="wrap" id="tuyen_dung" :hidden="tab!=='tuyen_dung'"><header class="sec-head"><h1 class="h1">{{ t('tab_tuyen_dung','Tuyển dụng') }}</h1></header><chuyen-muc v-if="tab==='tuyen_dung'" loai="tuyen_dung"/></section>

<main id="season" :hidden="tab!=='season'">
  <div class="noi-dung-theo-tab" data-vgb-vi-tri="season"><khoi-noi-dung vi-tri="season"/></div>
  <section class="wrap">
    <div class="mua-hd">
      <div class="meta"><span class="num" id="muaSo"><span>{{ t('dat_banh_323acda9d','00 / In season') }}</span></span></div>
      <h1 class="h1" id="muaTen">{{ S.MUA.ten_mua || t('dat_banh_d7e8f3298','Hàng theo mùa') }}</h1>
      <div class="mua-han" id="muaHan">{{ kho.hanMua.value }}</div>
      <div class="mua-luat" id="muaLuat" v-if="kho.luatTabMua.value">{{ kho.luatTabMua.value }}</div>
    </div>
    <div class="grid" id="muaLuoi">
      <div class="card-o" v-for="x in monMua" :key="x.g.khoa">
        <button class="card mua" :class="{het: x.g.het}" :data-nhom="x.g.khoa" @click="moMua(x.g)">
          <div class="ph"><i class="tagline">{{ t('nhan_seasonal','Seasonal') }}</i><anh-mon :src="x.g.anh"/></div>
          <div class="c-body">
            <div class="c-name">{{ x.ten }}</div>
            <div class="c-price"><span v-if="x.tu" class="c-tu">{{ t('mv_gia_tu','từ') }}</span><b>{{ x.gia }}</b></div>
            <div class="ruot" v-if="x.moTa">{{ t('dat_banh_afcf62369','Gồm') }} {{ x.moTa }}</div>
            <div class="c-sizes"><i class="sz" v-for="c in x.chips" :key="c.ma" :class="{has: c.has}">{{ c.chu }}</i></div>
            <div class="c-go">{{ t('dat_banh_00b018c50','Xem chi tiết →') }}</div>
          </div>
        </button>
        <button v-if="x.nhanh" class="c-them" @click="kho.themHangMua(x.g.sizes[0].ma)" :aria-label="t('them_nhanh_mon','Thêm nhanh {ten} vào giỏ',{ten:x.ten})"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></button>
      </div>
    </div>
  </section>
</main>

<main id="store" :hidden="tab!=='store'">
  <div class="noi-dung-theo-tab" data-vgb-vi-tri="store"><khoi-noi-dung vi-tri="store"/></div>
  <section class="wrap">
    <div class="store-hd">
      <div class="meta"><span class="num"><span>{{ t('dat_banh_289234b8c','00 / Tại quầy') }}</span></span><span id="storeLuc">{{ S.STORE.cap_nhat ? t('dat_banh_8f92d9663','Cập nhật') + ' ' + String(S.STORE.cap_nhat).slice(11,16) : '' }}</span></div>
      <h1 class="h1"><tieu-de-muc vi-tri="store" :dong="['Bánh trên tủ','tại quầy']"/></h1>
    </div>
    <div id="storeBody">
      <div class="gb-dau" id="gbDau" v-if="gbDauHien">
        <b>{{ kho.goiBan.nhanBan.value }}</b>
        <span v-if="kho.goiBan.cheDo.value==='goi'">{{ t('goi_ban_huong_dan','Bấm + trên món để thêm vào giỏ, rồi bấm Gọi món. Thanh toán tại quầy khi dùng xong.') }}</span>
        <span v-else>{{ t('goi_ban_ngoai_gio','Quầy đang ngoài giờ mở cửa ({gio}). Quý khách xem món, quầy mở cửa thì gọi được.',{gio: kho.goiBan.G.ban.gio || ''}) }}</span>
      </div>
      <div class="gb-dau gb-nhac" id="gbNhacQr" v-else-if="nhacQrHien">
        <b>{{ t('goi_ban_nhac_qr','Đang ngồi tại quầy? Quét mã QR dán trên bàn để gọi món') }}</b>
        <span>{{ t('goi_ban_nhac_qr_phu','Trang này chỉ xem bánh còn trên tủ. Gọi món cần mã của đúng bàn để quầy mang ra đúng chỗ. Chưa có mã trên bàn thì nhắn nhân viên gần nhất.') }}</span>
      </div>
      <goi-tai-ban :kho="kho" :tab="tab"/>
      <template v-if="quayHien">
        <div class="quay-gat" id="quayGat" role="group" :aria-label="t('quay_chon_cua_hang','Chọn cửa hàng')" v-if="!kho.goiBan.cheDo.value || kho.goiBan.cheDo.value==='giao'" :style="{gridTemplateColumns: 'repeat(' + quayHien.quay.length + ',1fr)'}"><button v-for="q in quayHien.quay" :key="q.ma" type="button" :aria-pressed="String(q.ma===quayHien.chon.ma)" @click="S.quayChon=q.ma; S.nhomQuay=''; S.tangQuay=''">
          <span v-for="(d,i) in tenQuayHaiDong(q.ten)" :key="i">{{ d }}</span></button></div>
        <p class="quay-dong" id="quayDong"><b v-if="quayHien.chon.dia_chi">{{ quayHien.chon.dia_chi }}</b><span>{{ quayHien.tong ? (quayHien.chon.dia_chi ? ' · ' : '') + t('quay_dong_con','Còn {so} bánh',{so: quayHien.tong}) + ' · ' + t('quay_dong_loai','{loai} loại',{loai: quayHien.soBanh}) : (quayHien.chon.dia_chi ? ' · ' : '') + t('dat_banh_71fb5d32e','Hiện đã hết bánh trên tủ') }}</span></p>
        <div class="gb-tim" id="gbTim">
          <input id="gbTimO" type="search" autocomplete="off" :placeholder="t('goi_ban_tim','Tìm món, ví dụ trà lài, canelé')" :aria-label="t('goi_ban_tim','Tìm món, ví dụ trà lài, canelé')" v-model="S.timQuay">
          <button v-if="S.timQuay" type="button" class="gb-tim-xoa" :aria-label="t('goi_ban_tim_xoa','Xoá chữ tìm')" @click="S.timQuay=''">×</button>
          <button type="button" class="gb-tim-nut" :aria-label="t('goi_ban_tim_nut','Tìm món')" @click="$event.currentTarget.parentNode.querySelector('input').focus()"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg></button></div>
        <div class="gb-tang" id="storeTang"><button v-for="n in quayHien.tang" :key="n.n" type="button" :data-tang="n.n" :aria-pressed="String(n.n===quayHien.tangChon)" @click="S.tangQuay=n.n; S.nhomQuay=''"><b>{{ n.ten }}</b><span>{{ n.so }}</span></button></div>
        <div class="cm-chips gb-chips" id="storeChip" v-if="quayHien.nhom.length"><button v-for="n in quayHien.nhom" :key="n.n" :data-nhom="n.n" :aria-pressed="String(n.n===quayHien.chip)" @click="S.nhomQuay=n.n">{{ n.ten + ' · ' + n.so }}</button></div>
        <div v-if="quayHien.rong==='tim'" class="store-empty" id="gbTimRong">{{ t('goi_ban_tim_rong','Không có món nào khớp "{tim}". Quý khách thử chữ khác hoặc chọn nhóm.',{tim: quayHien.tim}) }}</div>
        <div v-else-if="quayHien.rong" class="store-empty" :id="kho.goiBan.cheDo.value==='giao' ? 'webGiaoRong' : null">{{ kho.goiBan.cheDo.value==='giao' ? t('web_giao_rong','Quầy này hiện chưa có món nào đặt giao được. Quý khách ghé quầy hoặc đặt qua ứng dụng giao hàng.') : t('dat_banh_a85783ffc','Quầy này đã bán hết bánh trong tủ. Bánh mới lên tủ theo từng đợt trong ngày.') }}</div>
        <div v-else-if="kho.goiBan.cheDo.value" class="gb-ds" id="storeLuoi">
          <div class="gb-mon" v-for="m in quayHien.mon" :key="m.loai + m.ma" :data-ma="m.ma">
            <div class="gb-mon-anh"><anh-mon :src="m.anh"/></div>
            <div class="gb-mon-chu">
              <b>{{ m.loai==='banh' ? tMon(m.ma,'ten',m.ten) : m.ten }}</b>
              <small class="gb-mon-mo" v-if="m.mo_ta">{{ m.mo_ta }}</small>
              <span class="gb-mon-gia"><b v-if="m.gia">{{ tienTom(m.gia) }}</b><s v-if="m.gocHien">{{ tienTom(m.gocHien) }}</s>
                <i v-if="m.loai==='combo'" class="gb-mon-combo">{{ t('goi_ban_chip_combo','Combo') }}</i>
                <i v-else-if="m.loai!=='nuoc'">{{ t('dat_banh_75f5cf26e','Còn') }} {{ m.con }}</i>
                <i v-else-if="m.bienThe.length > 1">{{ t('goi_ban_size','Size') }} {{ m.bienThe.map(b => b.size).join(' · ') }}</i>
                <i v-else-if="(m.tc||[]).length">{{ t('goi_ban_co_lua_chon','Chọn đá, đường') }}</i></span>
            </div>
            <button v-if="kho.goiBan.cheDo.value==='goi' || kho.goiBan.cheDo.value==='giao'" class="gb-cong" :class="{co: kho.goiBan.daChon(m)}" :data-them="m.ma" @click="kho.goiBan.bamThem(m)" :aria-label="t('goi_ban_them_mon','Thêm {ten} vào giỏ gọi món',{ten: m.ten})"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>
          </div>
        </div>
        <div v-else class="grid" id="storeLuoi">
          <div class="card-o" v-for="m in quayHien.mon" :key="m.loai + m.ma" :data-ma="m.ma"><div class="card">
            <div class="ph"><i class="tagline">{{ m.loai==='nuoc' ? t('quay_chip_nuoc','Đồ uống') : (quayHien.chon.ten_ngan || quayHien.chon.ten) }}</i><anh-mon :src="m.anh"/></div>
            <div class="c-body">
              <div class="c-name">{{ m.loai==='nuoc' ? m.ten : tMon(m.ma,'ten',m.ten) }}</div>
              <div class="c-price" v-if="m.gia"><b>{{ tienTom(m.gia) }}</b></div>
              <div class="c-sizes" v-if="m.loai!=='nuoc'"><i class="sz has">{{ t('dat_banh_75f5cf26e','Còn') }} {{ m.con }}</i></div>
              <div class="c-sizes" v-else-if="m.bienThe.length > 1"><i class="sz">{{ t('goi_ban_size','Size') }} {{ m.bienThe.map(b => b.size).join(' · ') }}</i></div>
            </div>
          </div></div>
        </div>
      </template>
      <template v-else-if="S.storeDaTai || S.storeLoi">{{ t('quay_rong','Chưa có dữ liệu tại điểm bán. Quý khách thử tải lại hoặc liên hệ chúng tôi.') }}<button class="cm-nut" @click="kho.napQuay()">{{ t('tai_lai_quay','Tải lại danh sách') }}</button></template>
    </div>
    <div class="store-note">{{ t('dat_banh_3e8df5af5','Số bánh cập nhật theo từng hoá đơn tại quầy. Muốn giữ bánh thì nhắn') }}
      <a v-if="mxh('messenger','https://m.me/thevagabond.saigon')" :href="mxh('messenger','https://m.me/thevagabond.saigon')" target="_blank">{{ t('dat_banh_68074b808','Messenger') }}</a> {{ t('dat_banh_bd0762c0f','hoặc gọi') }}
      <a :href="'tel:'+telSo()">{{ telChu() }}</a>{{ t('dat_banh_499d32a3f',', chúng tôi để riêng cho quý khách tới lấy.') }}</div>
  </section>
</main>

<main id="today" :hidden="tab!=='today'">
  <div class="noi-dung-theo-tab" data-vgb-vi-tri="today"><khoi-noi-dung vi-tri="today"/></div>
  <section class="wrap hero">
    <div class="meta"><span class="num"><span>{{ t('dat_banh_9360a53fc','01 / Có sẵn') }}</span></span><span id="dateline"></span></div>
    <h1 class="h1"><tieu-de-muc vi-tri="today" :dong="['Bánh','hôm nay']"/><em id="bigDate"></em></h1>
    <p class="dong-tt" id="dongTrangThai"><template v-for="(p,i) in kho.dongTrangThai.value.phan" :key="i"><dong-chu :phan="p"/> · </template><span class="live"><i class="dot"></i><span id="synced">{{ t('dat_banh_9c4a42cb2','cập nhật') }} {{ kho.dongTrangThai.value.gio }}</span></span></p>
  </section>
  <div class="wrap">
    <div v-if="S.tonLoi" class="note" id="tonLoi" role="status">{{ t('ton_tai_loi','Chưa cập nhật được số bánh. Quý khách tải lại hoặc liên hệ chúng tôi để xác nhận.') }} <button class="cm-nut" @click="kho.napTon()">{{ t('tai_lai_quay','Tải lại danh sách') }}</button></div>
    <div class="note" id="prepNote"><dong-chu :phan="kho.ghiChuHomNay.value"/></div>
    <div class="grid" id="grid-today" v-show="theHomNay.length">
      <div class="card-o" v-for="x in theHomNay" :key="x.c.k">
        <button class="card" @click="moBanh(x.c)">
          <div class="ph"><i v-if="x.nhanMua" class="tagline">{{ x.nhanMua }}</i><anh-mon :src="x.c.img"/></div>
          <div class="c-body">
            <div class="c-name" :class="{vi: x.vi}">{{ x.ten }}</div>
            <div class="c-price"><b>{{ x.gia }}</b></div>
            <div class="c-sizes"><i v-for="(z,j) in x.chips" :key="j" class="sz" :class="{has: z.co}">{{ z.chu }}</i></div>
            <div class="c-go">{{ t('dat_banh_00b018c50','Xem chi tiết →') }}</div>
          </div>
        </button>
        <button class="c-them" @click="themNhanh(x.c,'today')" :aria-label="t('them_nhanh_mon','Thêm nhanh {ten} vào giỏ',{ten:x.ten})"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></button>
      </div>
    </div>
    <div class="empty" id="empty-today" :style="{display: (theHomNay.length || !S.tonNapXong) ? 'none' : 'block'}">
      <div class="big">{{ t('dat_banh_b69d165f8','Hôm nay đã hết bánh') }}</div>
      <p>{{ t('dat_banh_2da45f7bd','Bánh ra lò mỗi sáng và thường hết trong ngày.') }}</p>
      <button class="btn" @click="go('order')">{{ t('dat_banh_5e7da44cb','Đặt bánh trước') }}</button>
    </div>
  </div>
</main>

<main id="order" :hidden="tab!=='order'">
  <div class="noi-dung-theo-tab" data-vgb-vi-tri="order"><khoi-noi-dung vi-tri="order"/></div>
  <section class="wrap hero">
    <div class="meta"><span class="num"><span>{{ t('dat_banh_d0d81dd57','02 / Đặt trước') }}</span></span><span><span>{{ t('dat_banh_0dc2a0248','Bếp làm theo đơn') }}</span></span></div>
    <h1 class="h1"><tieu-de-muc vi-tri="order" :dong="['Đặt','bánh trước']"/></h1>
  </section>
  <div class="wrap">
    <div class="sec"><span class="n"><span>{{ t('dat_banh_6dcd4ce23','A') }}</span></span><h3><span>{{ t('dat_banh_41d54a1aa','Ngày nhận bánh') }}</span></h3><i class="rule"></i></div>
    <div class="rail" id="rail"><button v-for="d in kho.ngayRailDatTruoc.value" :key="d.i" class="day" :class="{on: d.on, best: d.best, off: d.off}" @click="kho.pick(d.i)"><span>{{ d.ten }}</span><b>{{ d.ngay }}</b></button></div>
    <div class="note hom-nay-goi"><a :href="hm('#/')" @click.prevent="nav('#/')">{{ t('can_banh_hom_nay','Cần bánh hôm nay? Xem tab Có sẵn hôm nay') }} →</a></div>
    <div class="sec"><span class="n"><span>{{ t('dat_banh_ae4f281df','B') }}</span></span><h3><span>{{ t('dat_banh_722864cac','Khung giờ nhận') }}</span></h3><i class="rule"></i></div>
    <div class="rail" id="slots"><button v-for="k in kho.khungRail.value" :key="k.i" class="slot" :class="{on: k.on, off: k.off}" @click="kho.pickSlot(k.i)" :disabled="k.off" :aria-disabled="k.off ? 'true' : null">{{ k.t }}</button></div>
    <div class="note" id="orderNote"><dong-chu :phan="kho.ghiChuDatTruoc.value"/></div>
    <div class="sec"><span class="n"><span>{{ t('dat_banh_32096c2e0','C') }}</span></span><h3><span>{{ t('dat_banh_29bae8a2d','Bánh ổ sinh nhật') }}</span></h3><i class="rule"></i></div>
    <div class="grid" id="grid-cake">
      <div class="card-o" v-for="x in theDatTruoc" :key="x.c.k">
        <button class="card" @click="moBanh(x.c)">
          <div class="ph"><i v-if="x.nhanMua" class="tagline">{{ x.nhanMua }}</i><anh-mon :src="x.c.img"/></div>
          <div class="c-body">
            <div class="c-name" :class="{vi: x.vi}">{{ x.ten }}</div>
            <div class="c-price"><b>{{ x.gia }}</b></div>
            <div class="c-sizes"><i v-for="(z,j) in x.chips" :key="j" class="sz" :class="{has: z.co}">{{ z.chu }}</i></div>
            <div class="c-go">{{ t('dat_banh_00b018c50','Xem chi tiết →') }}</div>
          </div>
        </button>
        <button class="c-them" @click="themNhanh(x.c,'order')" :aria-label="t('them_nhanh_mon','Thêm nhanh {ten} vào giỏ',{ten:x.ten})"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></button>
      </div>
      <div v-if="!theDatTruoc.length" style="grid-column:1/-1;padding:28px 8px;text-align:center;color:#8a8f98">{{ t('dat_banh_685100bce','Danh mục đặt trước đang được bếp cập nhật, quý khách quay lại sau chút xíu') }}</div>
    </div>
  </div>
</main>

<div data-vgb-vi-tri="cuoi_trang" :aria-label="t('dat_banh_b69802262','Câu chuyện Vagabond')"><khoi-noi-dung vi-tri="cuoi_trang"/></div>
<chan-trang :kho="kho" :go="go"/>

<div class="bar" id="bar" :class="{on: S.CART.length > 0 && !gioMo}"><div class="wrap in">
  <span class="cnt" id="barTxt"><template v-if="S.CART.length"><b>{{ t('dat_banh_a2f8afb2e','{gia_tri_a} bánh · {gia_tri_b}',{gia_tri_a: kho.soBanh.value, gia_tri_b: tienTom(kho.tienBanh.value)}) }}</b><small>{{ kho.dongMienPhi.value }}</small></template></span>
  <button class="go" @click="moGio()"><span>{{ t('dat_banh_fb62c648d','Xem giỏ') }}</span><span class="vt-so" aria-hidden="true">{{ kho.soBanh.value }}</span></button>
</div></div>
<div class="toast" id="toast" :class="{on: S.toast.on}">{{ S.toast.chu }}</div>
<goi-tai-ban-noi v-if="kho.goiBan.cheDo.value" :kho="kho" :tab="tab"/>
<kenh-noi :chuong="chuongQuay" :nang="(kho.goiBan.barMo.value || kho.goiBan.barDon.value) ? 82 : 0"/>

<section class="co" id="checkout" :class="{open: gioMo}" role="dialog" aria-modal="true" aria-labelledby="co-title">
  <div class="co-top"><div class="wrap in">
    <button class="bk" type="button" :aria-label="t('quay_lai_chon_banh','Quay lại chọn bánh')" @click="navBack()"><svg viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg></button>
    <b id="co-title"><span>{{ t('dat_banh_74ed5c7f8','Thông tin đơn hàng') }}</span></b>
  </div></div>
  <div class="wrap" style="padding-bottom:140px" v-if="gioMo || S.guiXong">

    <div class="sec"><span class="n">01</span><h3><span>{{ t('dat_banh_f257f0ff4','Giỏ bánh') }}</span></h3><i class="rule"></i></div>
    <ul class="cart" id="cartList">
      <li v-if="!S.CART.length" class="cart-empty">{{ t('dat_banh_b5f223212','Giỏ chưa có bánh nào.') }}</li>
      <li v-for="d in kho.dongGio.value" :key="d.i + '|' + d.o.id" class="dg">
        <div class="dg-tren"><div class="im"><img :src="d.o.img" alt=""></div>
          <div class="bd"><div class="t">{{ d.ten }}</div>
            <div class="s">{{ d.phu }}</div><div class="ex" v-if="d.ex.length"><template v-for="(e,j) in d.ex" :key="j"><br v-if="j">
              <dong-chu :phan="e"/></template></div></div>
          <button v-if="d.o.cm" type="button" class="nut-tron nut-sua" :aria-label="t('sua_banh','Sửa bánh')" :title="t('sua_banh','Sửa bánh')" @click="suaDongGio(d.i)"><bieu-tuong loai="sua"/><span class="chi-may-doc">{{ t('sua_banh','Sửa bánh') }}</span></button>
          <span v-else class="nut-cho" aria-hidden="true"></span>
          <button type="button" class="nut-tron nut-bo" :aria-label="t('bo_khoi_gio','Bỏ khỏi giỏ')" :title="t('bo_khoi_gio','Bỏ khỏi giỏ')" @click="kho.cartRemove(d.i); if(!S.CART.length) nav('#/',true)"><bieu-tuong loai="bo"/><span class="chi-may-doc">{{ t('bo_khoi_gio','Bỏ khỏi giỏ') }}</span></button></div>
        <div class="dg-duoi"><div class="sl-vien" role="group" :aria-label="t('so_luong_cua','Số lượng {ten}',{ten:d.ten})">
            <button type="button" :disabled="d.o.qty<=1" :aria-label="t('sl_bot_1','Bớt 1')" @click="kho.cartQty(d.i,-1)"><bieu-tuong loai="tru"/></button>
            <output aria-live="polite">{{ d.o.qty }}</output><button type="button" :aria-label="t('sl_them_1','Thêm 1')" @click="kho.cartQty(d.i,1)"><bieu-tuong loai="cong"/></button></div>
          <div class="p">{{ d.tien }}</div></div></li>
    </ul>
    <button class="cart-add" @click="navBack()"><bieu-tuong loai="cong"/><span>{{ t('dat_banh_7ddb8bc3b','Chọn thêm bánh') }}</span></button>
    <div class="dc-don" id="c-dc" v-if="S.CART.length && kho.tranDc.value > 0">
      <div class="dc-tieu">{{ t('dc_don_tieu','Dụng cụ ăn tặng kèm') }}</div>
      <div class="dc-mo">{{ t('dc_don_mo','The Vagabond gửi kèm chỉ khi quý khách cần nhằm hạn chế dụng cụ ăn uống sử dụng một lần. Quý khách cần bao nhiêu vui lòng nhập số lượng.') }}</div>
      <div class="dc-mo dc-tran">{{ t('dc_don_tran','Tối đa {so} bộ cho giỏ hiện tại: bánh 12cm, 16cm được 10 bộ; bánh 18cm, 20cm được 15 bộ.',{so:kho.tranDc.value}) }}</div>
      <ul class="acc dc-ds"><li v-for="x in DUNG_CU_DON" :key="x.k" :id="'c-dc-' + x.k"><img :src="anhWeb(x.ka, x.i)" alt=""><span class="nm">{{ t(x.kt, x.n) }}<small>{{ t('dc_don_tang','tặng kèm, 0 đ') }}</small><small class="dc-het" v-if="S.DC[x.k] && S.DC[x.k]>=kho.tranDc.value" role="status">{{ t('dc_don_toi_da','Đã chọn tối đa số lượng cho phép') }}</small></span>
        <div class="sl-vien" role="group" :aria-label="t('so_luong_cua','Số lượng {ten}',{ten:t(x.kt, x.n)})"><button type="button" :disabled="!S.DC[x.k]" :aria-label="t('sl_bot_1','Bớt 1')" @click="kho.doiDc(x.k,-1)"><bieu-tuong loai="tru"/></button>
          <output aria-live="polite">{{ S.DC[x.k] }}</output><button type="button" :disabled="S.DC[x.k]>=kho.tranDc.value" :aria-label="t('sl_them_1','Thêm 1')" @click="kho.doiDc(x.k,1)"><bieu-tuong loai="cong"/></button></div></li></ul>
    </div>
    <goi-y-mua id-khoi="gyGio" :tieu="t('gy_tieu_gio','GIAO KÈM CÙNG CHUYẾN')" :ds="kho.goiYGio.value" :them="kho.themGoiY" :thanh="kho.thanhMienPhiGio.value"/>

    <!-- v681 (BẢN 2 mục 2.1): mỗi CHIẾC bánh một thẻ lời chúc và thiệp. -->
    <template v-if="kho.dsChiec.value.length">
    <div class="sec" id="c-loi-chuc"><span class="n">02</span><h3><span>{{ kho.coChiecCamCo.value ? t('lc_tieu_de','Lời chúc và thiệp') : t('mv_thiep_tieu_de','Thiệp') }}</span></h3><i class="rule"></i></div>
    <div class="lc-ds">
      <div class="lc-the" v-for="x in kho.dsChiec.value" :key="x.c.id" :id="'lc-' + x.c.id">
        <div class="lc-dau"><img :src="x.o.img" alt=""><div><b>{{ x.ten }}</b><small>{{ x.phu }}</small></div></div>
        <template v-if="x.coCo">
        <div class="lc-nhan" :id="'lcn-' + x.c.id">{{ t('lc_co_nhan','Cờ cắm lời chúc') }}</div>
        <div class="hai-nua" role="radiogroup" :aria-labelledby="'lcn-' + x.c.id">
          <button type="button" role="radio" :aria-checked="x.c.co !== false ? 'true' : 'false'" :class="{on: x.c.co !== false}" @click="kho.datCo(x.c.id, true)">{{ t('lc_can_co','Cần cờ') }}</button>
          <button type="button" role="radio" :aria-checked="x.c.co === false ? 'true' : 'false'" :class="{on: x.c.co === false}" @click="kho.datCo(x.c.id, false)">{{ t('lc_khong_co','Không cần cờ') }}</button>
        </div>
        </template>
        <div class="lc-co" v-if="x.coCo && x.c.co !== false">
          <div class="lc-o"><input :id="'lcw-' + x.c.id" maxlength="60" autocomplete="off" :aria-label="t('lc_o_chuc','Lời chúc in trên cờ')" :placeholder="t('dat_banh_ed04b0946','Happy Birthday...')" v-model="x.c.wish">
            <button type="button" class="lc-mau" :aria-label="t('lc_xem_mau','Xem mẫu cờ chúc')" @click="kho.moMauCo(x.c.id)"><img :src="anhWeb('anh_co_mau', ANH_CO)" alt=""><i aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/></svg></i></button></div>
          <div class="lc-dem"><span>{{ t('lc_bam_mau','Bấm hình cờ để xem mẫu') }}</span><span>{{ (x.c.wish || '').length }}/60</span></div>
        </div>
        <div class="lc-nhan" :id="'lctn-' + x.c.id">{{ x.mua ? t('mv_thiep_nhan','Thiệp (miễn phí)') : t('lc_thiep_nhan','Thiệp') }}</div>
        <div class="hai-nua" role="radiogroup" :aria-labelledby="'lctn-' + x.c.id">
          <button type="button" role="radio" :aria-checked="x.c.thiep === 'khong' ? 'true' : 'false'" :class="{on: x.c.thiep === 'khong'}" @click="kho.batThiep(x.c.id, false)">{{ t('lc_khong_thiep','Không cần thiệp') }}</button>
          <button type="button" role="radio" :aria-checked="x.c.thiep !== 'khong' ? 'true' : 'false'" :class="{on: x.c.thiep !== 'khong'}" @click="kho.batThiep(x.c.id, true)">{{ t('lc_can_thiep','Cần thiệp') }}</button>
        </div>
        <template v-if="x.c.thiep !== 'khong'">
          <!-- v693: bánh mùa vụ chỉ có thiệp miễn phí kèm trong hộp, không chọn loại. -->
          <div class="th-mua" v-if="x.mua" :data-thiep-mua="x.loai">
            <span class="th-anh"><img v-if="anhWeb(THIEP_MUA[x.loai].ka, '')" :src="anhWeb(THIEP_MUA[x.loai].ka, '')" alt=""><span v-else class="th-trong">{{ t(THIEP_MUA[x.loai].k, THIEP_MUA[x.loai].n) }}</span></span>
            <p><b>{{ t(THIEP_MUA[x.loai].k, THIEP_MUA[x.loai].n) }}</b><span>{{ t('mv_thiep_mo_ta','The Vagabond viết tay lời quý khách gửi lên thiệp. Để trống thì gửi thiệp trơn.') }}</span></p>
          </div>
          <div class="th-luoi" v-else role="radiogroup" :aria-label="t('lc_loai_thiep','Loại thiệp')">
            <button type="button" role="radio" class="th-the" data-thiep="nho" :class="{on: x.c.thiep === 'nho'}" :aria-checked="x.c.thiep === 'nho' ? 'true' : 'false'" @click="kho.datThiep(x.c.id, 'nho')">
              <span class="th-anh"><img v-if="anhWeb('anh_thiep_nho', '')" :src="anhWeb('anh_thiep_nho', '')" alt=""><span v-else class="th-trong">{{ t('lc_thiep_nho','Thiệp nhỏ') }}</span></span>
              <b>{{ t('lc_thiep_nho','Thiệp nhỏ') }}</b><span class="th-gia">{{ t('lc_mien_phi','miễn phí') }}</span><i class="th-chon" v-if="x.c.thiep === 'nho'" aria-hidden="true">✓</i></button>
            <button type="button" role="radio" class="th-the" data-thiep="ep_kim" :class="{on: x.c.thiep === 'ep_kim'}" :aria-checked="x.c.thiep === 'ep_kim' ? 'true' : 'false'" @click="kho.datThiep(x.c.id, 'ep_kim')">
              <span class="th-anh"><img :src="anhWeb(THIEP_EP_KIM.ka, THIEP_EP_KIM.img)" alt=""></span>
              <b>{{ t('thiep_ep_kim_ten','Thiệp sinh nhật ép kim') }}</b><span class="th-gia">{{ tienTom(kho.giaThiep.value) }}</span><i class="th-chon" v-if="x.c.thiep === 'ep_kim'" aria-hidden="true">✓</i></button>
          </div>
          <div class="fld lc-thiep-o"><label :for="'lct-' + x.c.id"><span>{{ t('lc_loi_thiep','Lời viết trên thiệp') }}</span></label>
            <input :id="'lct-' + x.c.id" maxlength="80" autocomplete="off" v-model="x.c.loi_thiep">
            <div class="lc-dem"><span>{{ t('lc_thiep_goi','Ngắn gọn, tối đa 80 ký tự') }}</span><span>{{ (x.c.loi_thiep || '').length }}/80</span></div></div>
        </template>
      </div>
    </div>
    </template>

    <div class="sec"><span class="n">03</span><h3><span>{{ t('dat_banh_73b0921c0','Ngày và giờ nhận') }}</span></h3><i class="rule"></i></div>
    <div class="tomtat" id="c-tomtat" v-if="kho.hienTomTat.value"><div class="tt-doc"><span>{{ t('dat_banh_9e6a654ba','Thời gian nhận') }}</span><b>{{ tomTatLich }}</b></div><button type="button" class="tt-doi" @click="kho.doiLich()">{{ t('dat_banh_2d141c148','Thay đổi') }}</button></div>
    <div id="c-chon" v-else>
      <div class="rail" id="c-days"><button v-for="d in kho.ngayRail.value" :key="d.i" class="day" :class="{on: d.on, best: d.best, off: d.off}" @click="kho.pick(d.i)"><span>{{ d.ten }}</span><b>{{ d.ngay }}</b></button></div>
      <div class="rail" id="c-slots"><button v-for="k in kho.khungRail.value" :key="k.i" class="slot" :class="{on: k.on, off: k.off}" @click="kho.pickSlot(k.i)" :disabled="k.off" :aria-disabled="k.off ? 'true' : null">{{ k.t }}</button></div>
    </div>
    <div class="note" id="c-prep"><dong-chu :phan="kho.ghiChuGio.value"/></div>

    <div class="sec"><span class="n">04</span><h3><span>{{ t('dat_banh_8e8a333b5','Nhận bánh bằng cách nào') }}</span></h3><i class="rule"></i></div>
    <div class="seg">
      <button id="m-ship" :class="{on: S.CO.mode==='ship'}" @click="kho.setMode('ship')"><b><span>{{ t('dat_banh_391958765','Giao tận nơi') }}</span></b><span><span>{{ t('dat_banh_456ce7b1c','Bếp gọi xe giao tới địa chỉ') }}</span></span></button>
      <button id="m-pick" :class="{on: S.CO.mode==='pick'}" :hidden="!S.PICKUPS.length" @click="kho.setMode('pick')"><b><span>{{ t('dat_banh_ba7ce36b2','Tự đến lấy') }}</span></b><span><span>{{ t('dat_banh_61aacce28','Lấy tại một trong hai địa điểm') }}</span></span></button>
    </div>
    <div id="pickList" :style="{display: S.CO.mode==='pick' ? 'block' : 'none', marginTop: '12px'}"><button v-for="x in S.PICKUPS" :key="x.id" class="pick" :class="{on: S.CO.pickupId===x.id}" @click="kho.setPickup(x.id)"><b>{{ x.n }}</b><span>{{ x.a }}</span></button></div>

    <div class="sec"><span class="n">05</span><h3><span>{{ t('dat_banh_bd76ef893','Người đặt') }}</span></h3><i class="rule"></i></div>
    <div class="fld"><label><span>{{ t('dat_banh_58f52301a','Số điện thoại') }}</span></label>
      <input id="f-phone" type="tel" inputmode="numeric" :placeholder="t('dat_banh_639307e29','09xx xxx xxx')" v-model="S.f.phone" @input="kho.lookupPhone()">
      <div class="hint" id="phoneHint" v-if="!kho.theThanhVien.value"><dong-chu v-if="S.goi.phone" :phan="S.goi.phone"/><template v-else>{{ t('dat_banh_4602d2995','Quý khách có thể nhập địa chỉ mới. Địa chỉ đã lưu chỉ hiện sau khi xác thực thành viên.') }}</template></div>
    </div>
    <!-- v682 (BẢN 2 mục 2.2): thẻ Thành viên ngay dưới ô số điện thoại. Ưu đãi đơn đầu và điểm chuyển từ mục Thanh toán lên đây; một lần xác thực Zalo dùng chung cho ưu đãi, điểm, địa chỉ đã lưu. -->
    <div class="tv-the" id="theTv" v-if="kho.theThanhVien.value" :class="'tv-' + kho.theThanhVien.value.kieu" role="group" :aria-label="t('tv682_nhan','Thành viên The Vagabond Club')">
      <div class="tv-dau"><span class="tv-dia" aria-hidden="true" v-if="kho.theThanhVien.value.dia">{{ kho.theThanhVien.value.dia }}</span>
        <div><b class="tv-tieu">{{ kho.theThanhVien.value.tieu }}</b><small class="tv-phu" v-if="kho.theThanhVien.value.phu">{{ kho.theThanhVien.value.phu }}</small></div></div>
      <template v-if="kho.theThanhVien.value.kieu === 'ma'">
        <div class="tv-o-ma" role="group" :aria-label="t('dat_banh_dd_o_ma','Mã 6 số trong tin nhắn Zalo')">
          <input v-for="i in 6" :key="i" :id="i === 1 ? 'ddMa' : 'ddMa' + i" class="tv-o" inputmode="numeric" :autocomplete="i === 1 ? 'one-time-code' : 'off'" maxlength="6"
            :aria-label="t('tv682_o_so','Số thứ {so} của mã',{so: i})" :value="(S.CO.dd.ma || '')[i - 1] || ''" @input="nhapOMa(i - 1, $event)" @keydown="phimOMa(i - 1, $event)"></div>
        <button type="button" class="tv-nut" id="ddXacNhan" :disabled="S.CO.dd.dangGui" @click="kho.xacThucDonDau()">{{ t('dat_banh_dd_xac_nhan','Xác nhận') }}</button>
        <div class="tv-duoi"><button type="button" class="tv-lai" id="ddGuiLai" :disabled="S.CO.dd.dangGui || S.CO.dd.cho > 0" @click="kho.guiMaDonDau()">{{ S.CO.dd.cho > 0 ? t('tv682_gui_lai_sau','Gửi lại sau {thoi}',{thoi: Math.floor(S.CO.dd.cho / 60) + ':' + String(S.CO.dd.cho % 60).padStart(2, '0')}) : t('dat_banh_dd_gui_lai','Gửi lại mã') }}</button>
          <button type="button" class="tv-doi" id="ddDoiSo" @click="doiSoDt()">{{ t('tv682_doi_so','Đổi số') }}</button></div>
      </template>
      <button v-else-if="kho.theThanhVien.value.nut" type="button" class="tv-nut" id="ddGuiMa" :disabled="S.CO.dd.dangGui" @click="kho.guiMaDonDau()">{{ S.CO.dd.dangGui ? t('dat_banh_dd_dang_gui','Đang gửi...') : t('tv682_gui_ma','Gửi mã qua Zalo') }}</button>
      <template v-if="kho.theThanhVien.value.kieu === 'xac'">
        <button v-if="kho.theThanhVien.value.diem" type="button" role="switch" class="tv-cong-tac" id="dvDung" :aria-checked="S.CO.dungDiem ? 'true' : 'false'" @click="kho.dungDiem(!S.CO.dungDiem)">
          <span class="tv-ct-chu"><b>{{ t('tv682_dung_diem','Dùng {diem} điểm cho đơn này',{diem: kho.theThanhVien.value.diem.so}) }}</b><small>{{ t('tv682_dung_diem_phu','Giảm {tien}. Dùng tối đa một nửa tiền bánh.',{tien: kho.theThanhVien.value.diem.tien}) }}</small></span>
          <span class="ct" aria-hidden="true"><i></i></span></button>
        <p class="tv-ghi" v-else-if="kho.theThanhVien.value.diemChu">{{ kho.theThanhVien.value.diemChu }}</p>
        <button v-if="kho.theThanhVien.value.soDc && S.CO.mode === 'ship'" type="button" class="tv-dc" id="tvDiaChi" @click="cuonToi('', '#savedAddr')">{{ t('tv682_dia_chi','Địa chỉ đã lưu: {so} địa chỉ',{so: kho.theThanhVien.value.soDc}) }}<span aria-hidden="true">›</span></button>
      </template>
      <p class="tv-loi" v-if="S.CO.dd.loi" role="alert">{{ S.CO.dd.loi }}</p>
    </div>
    <div class="two">
      <div class="fld"><label><span>{{ t('dat_banh_3da3c8c27','Họ tên') }}</span></label><input id="f-name" :placeholder="t('dat_banh_5bef63904','Họ và tên người đặt')" v-model="S.f.name"></div>
      <div class="fld"><label><span>{{ t('dat_banh_f2a1fc421','Email (không bắt buộc)') }}</span></label><input id="f-mail" type="email" :placeholder="t('dat_banh_b768618e5','email@...')" v-model="S.f.mail"></div>
    </div>

    <div id="addrBlock" :style="{display: S.CO.mode==='ship' ? 'block' : 'none'}">
      <div class="sec"><span class="n">06</span><h3><span>{{ t('dat_banh_19d05166b','Địa chỉ nhận') }}</span></h3><i class="rule"></i></div>
      <div id="savedAddr"><button v-for="a in kho.diaChiLuu.value" :key="a.i" class="pick" :class="{on: a.on}" @click="kho.selAddr(a.i)"><b>{{ a.dau }}</b><span>{{ a.duoi }}</span></button></div>
      <!-- v684 (BẢN 2 mục 2.3): ô gõ tìm phường mới thay ô chọn 20 khu vực. Gõ tên phường mới,
           tên quận cũ hay phường cũ, không dấu cũng tìm được. Không có phí dự kiến: phí tính theo địa chỉ. -->
      <div class="fld" id="phuongBlock" v-show="(S.cauHinh && S.cauHinh.phuong || []).length"><label for="f-phuong"><span>{{ t('ph684_nhan','Phường giao') }}</span></label>
        <div class="ph-o" :class="{mo: S.CO.phMo, da: !!kho.theoPhuong.value && !S.CO.phMo}">
          <svg class="ph-ghim" aria-hidden="true" viewBox="0 0 24 24"><path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/></svg>
          <input id="f-phuong" type="text" autocomplete="off" role="combobox" aria-autocomplete="list" aria-controls="phuongDs" :aria-expanded="S.CO.phMo ? 'true' : 'false'"
            :placeholder="t('ph684_goi','Gõ tên phường, quận cũ hoặc phường cũ')"
            :value="S.CO.phMo ? S.CO.phTim : (kho.theoPhuong.value ? kho.theoPhuong.value.chu : '')"
            @focus="kho.moPhuong()" @input="kho.goPhuong($event.target.value)" @keydown.esc="kho.dongPhuong()">
          <button v-if="!S.CO.phMo && kho.theoPhuong.value" type="button" class="ph-bo" :aria-label="t('ph684_bo','Bỏ phường đã chọn')" @click="kho.boPhuong()"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg></button>
        </div>
        <div class="ph-ds" id="phuongDs" role="listbox" v-if="S.CO.phMo && S.CO.phTim.trim()">
          <button v-for="p in kho.goiYPhuong.value" :key="p.ma" type="button" role="option" class="ph-dong" @mousedown.prevent @click="kho.chonPhuong(p.ma)">
            <span class="ph-chu"><b>{{ p.ten }}</b><small><template v-for="(m, i) in p.phu.split(p.khop || '\u0000')" :key="i"><template v-if="i"><em>{{ p.khop }}</em></template>{{ m }}</template></small></span>
            <span class="ph-tien" v-if="p.ngoai">{{ t('ph684_chua_tinh','chưa tính được') }}</span>
          </button>
          <p class="ph-rong" v-if="!kho.goiYPhuong.value.length">{{ t('ph684_rong','Không thấy phường này trong vùng giao. Quý khách gõ địa chỉ bên dưới hoặc gọi cho chúng tôi.') }}</p>
        </div>
      </div>
      <div class="fld"><label><span>{{ t('dat_banh_c67579097','Địa chỉ chi tiết') }}</span></label>
        <input id="f-addr" :placeholder="t('dat_banh_dd58bee7e','Gõ số nhà và tên đường, rồi chọn trong danh sách')" autocomplete="off" v-model="S.f.addr" @input="kho.goiYDiaChi()">
        <div id="addrGoiY"><div class="goiy" v-if="S.goiY.length"><div class="lbl">{{ t('dat_banh_3e7887810','Chọn đúng địa chỉ bên dưới') }}</div><button v-for="(g,i) in S.goiY" :key="i" type="button" @click="kho.chonGoiY(i)">{{ g.mo_ta }}</button></div></div>
        <div class="hint" id="shipHint"><dong-chu :phan="S.goi.ship || [thuong(t('ph684_goi_y_goc','Gõ địa chỉ, hệ thống báo phí giao.'))]"/><button v-if="S.goi.phiThuLai" class="cm-nut" @click="kho.quoteShip()">{{ t('thu_phi','Thử lại phí giao') }}</button></div>
      </div>
    </div>

    <div class="sec"><span class="n">07</span><h3><span>{{ t('dat_banh_449171c11','Người nhận') }}</span></h3><i class="rule"></i></div>
    <!-- v681 (BẢN 2 mục 2.4): chọn MỘT người nhận (nút tròn); Bánh tặng là ô vuông riêng. -->
    <div class="nhan-nho" id="nn-nhan">{{ t('nn_ai_nhan','AI NHẬN BÁNH') }}</div>
    <div role="radiogroup" aria-labelledby="nn-nhan">
      <button type="button" class="chon1" id="c-toi" role="radio" :class="{on: !S.CO.other}" :aria-checked="!S.CO.other ? 'true' : 'false'" @click="chonNguoiNhan(false)"><span class="tron" aria-hidden="true"></span>
        <span class="tx"><span>{{ t('nn_toi_nhan','Tôi là người nhận bánh') }}</span><small>{{ t('nn_toi_nhan_mo','Sử dụng số điện thoại đã nhập ở trên') }}</small></span></button>
      <button type="button" class="chon1" id="c-other" role="radio" :class="{on: S.CO.other}" :aria-checked="S.CO.other ? 'true' : 'false'" aria-controls="otherBlock" @click="chonNguoiNhan(true)"><span class="tron" aria-hidden="true"></span>
        <span class="tx"><span>{{ t('dat_banh_f9dae2775','Người khác nhận bánh') }}</span><small>{{ t('nn_khac_mo','Nhập thông tin người nhận thay') }}</small></span></button>
    </div>
    <div id="otherBlock" :style="{display: S.CO.other ? 'grid' : 'none'}" class="two">
      <div class="fld"><label><span>{{ t('dat_banh_c6a77e80c','Tên người nhận') }}</span></label><input id="f-rname" :placeholder="t('dat_banh_e2b6d704f','Họ và tên người nhận')" v-model="S.f.rname"></div>
      <div class="fld"><label><span>{{ t('dat_banh_d04237d6e','Số điện thoại người nhận') }}</span></label><input id="f-rphone" type="tel" inputmode="numeric" v-model="S.f.rphone"></div>
    </div>
    <div class="nhan-nho">{{ t('nn_gui_tang','GỬI TẶNG') }}</div>
    <button class="chk" id="c-gift" :class="{on: S.CO.gift}" role="checkbox" :aria-checked="S.CO.gift ? 'true' : 'false'" @click="tgl('gift')"><span class="bx">{{ S.CO.gift ? '✓' : '' }}</span>
      <span class="tx"><span>{{ t('dat_banh_6f5611da8','Bánh tặng, không gửi kèm hoá đơn') }}</span><small><span>{{ t('dat_banh_c5e99412b','Bếp sẽ bỏ hoá đơn ra khỏi hộp') }}</span></small></span></button>

    <div class="sec"><span class="n">08</span><h3><span>{{ t('gc_tieu_de','Ghi chú cho bếp và người giao') }}</span></h3><i class="rule"></i></div>
    <!-- v681 (BẢN 2 mục 2.5): viên chọn nhanh chạy theo MÃ, nhãn sửa ở trình biên tập. -->
    <div class="nhan-nho">{{ t('gc_chon_nhanh','CHỌN NHANH, CHỌN NHIỀU CŨNG ĐƯỢC') }}</div>
    <div class="gc-ds" id="gcDs"><button v-for="x in kho.gcHien.value" :key="x.ma" type="button" class="gc-vien" :data-gc="x.ma" :class="{on: S.CO.gc.includes(x.ma)}" :aria-pressed="S.CO.gc.includes(x.ma) ? 'true' : 'false'" @click="kho.doiGc(x.ma)"><i aria-hidden="true">{{ S.CO.gc.includes(x.ma) ? '✓' : '+' }}</i><span>{{ t(x.k, x.n) }}</span></button></div>
    <div class="gc-gio" id="gcGio" v-if="S.CO.gc.includes('gio_tre_nhat') && S.CO.mode !== 'pick'"><span class="gc-gio-nhan" id="gcGioNhan">{{ t('gc_gio_nhan','Giao trễ nhất lúc') }}</span>
      <div class="gc-gio-ds" role="radiogroup" aria-labelledby="gcGioNhan"><button v-for="g in kho.gioTreChon.value" :key="g" type="button" role="radio" class="gc-gio-nut" :class="{on: S.CO.gcGio === g}" :aria-checked="S.CO.gcGio === g ? 'true' : 'false'" @click="kho.chonGioTre(g)">{{ g }}</button></div></div>
    <p class="gc-bao" role="status" v-if="S.goi.gcGio">{{ S.goi.gcGio }}</p>
    <div class="fld"><label for="f-note"><span>{{ S.CO.gc.includes('di_ung') ? t('gc_khac_di_ung','GHI RÕ DỊ ỨNG VÀ GHI CHÚ KHÁC (BẮT BUỘC)') : t('gc_khac','GHI CHÚ KHÁC (KHÔNG BẮT BUỘC)') }}</span></label><textarea id="f-note" :placeholder="S.CO.gc.includes('di_ung') ? t('gc_goi_di_ung','Ghi rõ dị ứng với gì…') : t('gc_goi_khac','Yêu cầu khác cho bếp hoặc người giao...')" v-model="S.f.note"></textarea></div>

    <div class="sec"><span class="n">09</span><h3><span>{{ t('dat_banh_05ecd1510','Hoá đơn') }}</span></h3><i class="rule"></i></div>
    <button class="chk" id="c-vat" :class="{on: S.CO.vat}" role="checkbox" :aria-checked="S.CO.vat ? 'true' : 'false'" @click="tgl('vat')" :aria-expanded="S.CO.vat ? 'true' : 'false'" aria-controls="vatBlock"><span class="bx">{{ S.CO.vat ? '✓' : '' }}</span>
      <span class="tx"><span>{{ t('dat_banh_2b9cdf192','Xuất hoá đơn cho công ty') }}</span><small><span>{{ t('dat_banh_2f21d2762','Điền mã số thuế, hệ thống tự lấy tên và địa chỉ công ty') }}</span></small></span></button>
    <div id="vatBlock" :style="{display: S.CO.vat ? 'block' : 'none'}">
      <div class="fld"><label><span>{{ t('dat_banh_bf1686a9c','Mã số thuế') }}</span></label>
        <input id="f-mst" inputmode="numeric" maxlength="14" :placeholder="t('dat_banh_980763cf3','10 hoặc 13 số')" v-model="S.f.mst" @input="kho.lookupMst()">
        <div class="hint" id="mstHint"><dong-chu v-if="S.goi.mst" :phan="S.goi.mst"/><template v-else>{{ t('dat_banh_e90c92c6b','Gõ đủ mã số thuế, hệ thống sẽ tra tên công ty.') }}</template></div>
      </div>
      <div class="two">
        <div class="fld"><label><span>{{ t('dat_banh_24db39d3b','Tên công ty') }}</span></label><input id="f-cname" :placeholder="t('dat_banh_e22f738f9','Tự điền sau khi tra mã số thuế')" v-model="S.f.cname"></div>
        <div class="fld"><label><span>{{ t('dat_banh_36311276d','Email nhận hoá đơn') }}</span></label><input id="f-cmail" type="email" inputmode="email" :placeholder="t('dat_banh_0995a8a86','ketoan@congty.vn')" v-model="S.f.cmail"></div>
      </div>
      <div class="fld"><label><span>{{ t('dat_banh_8f0343ae6','Địa chỉ trên hoá đơn') }}</span></label><input id="f-caddr" :placeholder="t('dat_banh_e22f738f9','Tự điền sau khi tra mã số thuế')" v-model="S.f.caddr"></div>
      <div class="hint"><span>{{ t('dat_banh_f10e63e4f','Tên và địa chỉ lấy từ dữ liệu của Cục Thuế. Quý khách sửa lại được nếu công ty vừa đổi thông tin.') }}</span></div>
    </div>

    <div class="sec"><span class="n">10</span><h3><span>{{ t('dat_banh_9d5a6614c','Thanh toán') }}</span></h3><i class="rule"></i></div>
    <!-- v681 (BẢN 2 mục 2.7): mỗi cách trả một dòng: biểu tượng, tên, logo, nút tròn. Logo là tệp trong repo (logo-tt/), thay tệp là xong. -->
    <div id="payList" role="radiogroup" :aria-label="t('dat_banh_9d5a6614c','Thanh toán')"><button v-for="x in kho.paysHien.value" :key="x.k" type="button" role="radio" class="pt-dong" :class="{on: S.CO.pay===x.k}" :aria-checked="S.CO.pay===x.k ? 'true' : 'false'" :data-pt="x.k" @click="S.CO.pay=x.k; S.CO.payBao=false">
      <span class="pt-ic" aria-hidden="true"><svg viewBox="0 0 24 24"><template v-if="x.ic === 'landmark'"><path d="M3 21h18M5 18V10M9.5 18V10M14.5 18V10M19 18V10M12 3l8.5 4.5h-17z"/></template><template v-else-if="x.ic === 'credit-card'"><rect x="2.5" y="5" width="19" height="14" rx="2"/><path d="M2.5 10h19M6.5 15h4"/></template><template v-else><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9.5h4.5a2 2 0 0 1 1.6.8l.8 1a2.6 2.6 0 0 0 4.2 0l.8-1a2 2 0 0 1 1.6-.8H21M3 14h18"/></template></svg></span>
      <span class="pt-chu"><b>{{ t(x.kn, x.n) }}</b><small>{{ t(x.kd, x.d) }}</small>
        <span class="pt-logo"><img v-for="l in x.logo" :key="l" :src="LOGO_TT[l].src" :alt="LOGO_TT[l].ten"><em v-if="x.logoChu">{{ t('pt_ck_logo_chu','40+ ngân hàng') }}</em></span></span>
      <span class="tron" aria-hidden="true"></span></button></div>
    <p class="pay-bao" id="payBao" role="status" v-if="S.CO.payBao">{{ t('pay675_xem_lai','Cách thanh toán đã chọn trước đây không còn áp dụng. Quý khách xem lại cách thanh toán trước khi gửi đơn.') }}</p>

    <div class="fld"><label><span>{{ t('dat_banh_ma_uu_dai','Mã ưu đãi') }}</span></label>
      <div class="ma-hang"><input id="f-ma" autocomplete="off" autocapitalize="characters" maxlength="40" :aria-label="t('dat_banh_ma_uu_dai','Mã ưu đãi')" :placeholder="t('dat_banh_ma_uu_dai_goi','Ví dụ SINHNHAT10')" v-model="S.f.ma" @keydown.enter.prevent="kho.apMaUuDai()">
      <button class="nut-vien" id="btnMa" type="button" @click="kho.apMaUuDai()"><span>{{ t('dat_banh_ap_ma','Áp dụng') }}</span></button></div>
      <div class="hint" id="maHint"><dong-chu :phan="kho.goiYMa.value"/></div>
    </div>
    <div class="fld" id="gtKhoi" v-if="kho.coGioiThieu.value"><label for="f-gt"><span>{{ t('dat_banh_ma_gt','Mã giới thiệu (không bắt buộc)') }}</span></label>
      <input id="f-gt" inputmode="tel" autocomplete="off" maxlength="20" :placeholder="t('dat_banh_ma_gt_goi','Số điện thoại nhân viên giới thiệu')" v-model="S.f.gt" @blur="kho.kiemGioiThieu()" @keydown.enter.prevent="kho.kiemGioiThieu()">
      <div class="hint" id="gtHint"><dong-chu v-if="S.goi.gt" :phan="S.goi.gt"/></div>
    </div>

    <div class="noi-dung-gio" data-vgb-vi-tri="gio_hang" v-if="!S.guiXong"><khoi-noi-dung vi-tri="gio_hang"/></div>
    <!-- v681 (BẢN 2 mục 2.8): thẻ tóm tắt đơn. Số chỉ để xem, máy chủ chốt lúc gửi đơn. -->
    <div class="sum the-tt" id="sum">
      <div class="tt-banh" v-for="b in kho.theTomTat.value.banh" :key="b.k"><img v-if="b.img" :src="b.img" alt=""><span v-else class="tt-anh-trong" aria-hidden="true"></span>
        <div class="tt-ten"><b>{{ b.ten }}</b><small>{{ b.phu }}</small></div><span class="tt-gia">{{ b.gia }}</span></div>
      <div class="tt-them" v-for="x in kho.theTomTat.value.them" :key="x.k"><span>+ {{ x.ten }} × {{ x.sl }}</span><b>{{ x.gia }}</b></div>
      <div class="tt-dong" id="ttNhan"><svg aria-hidden="true" viewBox="0 0 24 24"><rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/></svg><span class="tt-nhan">{{ t('tt_nhan','Nhận') }}</span>
        <b v-if="kho.theTomTat.value.nhan">{{ kho.theTomTat.value.nhan }}</b><button v-else type="button" class="tt-thieu" @click="cuonToi('lich')">{{ t('tt_chon_gio','Chọn giờ') }}</button></div>
      <div class="tt-dong" id="ttGiao"><svg aria-hidden="true" viewBox="0 0 24 24"><template v-if="kho.theTomTat.value.tuLay"><path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/></template><template v-else><path d="M2.5 6h11v10h-11zM13.5 9.5h4l3 3.5V16h-7"/><circle cx="6.5" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/></template></svg>
        <span class="tt-nhan">{{ kho.theTomTat.value.tuLay ? t('tt_lay','Lấy') : t('tt_giao','Giao') }}</span>
        <b v-if="kho.theTomTat.value.giao" class="tt-dc">{{ kho.theTomTat.value.giao }}</b><button v-else type="button" class="tt-thieu" @click="cuonToi(kho.theTomTat.value.tuLay ? 'diem_nhan' : 'dia_chi')">{{ kho.theTomTat.value.tuLay ? t('tt_chon_diem','Chọn điểm nhận') : t('tt_nhap_dc','Nhập địa chỉ') }}</button>
        <em class="tt-phi" :class="'phi-' + kho.theTomTat.value.kieuPhi">{{ kho.theTomTat.value.phi }}</em></div>
      <div class="tt-dong tt-giam" v-if="kho.theTomTat.value.uuDai"><span class="tt-nhan">{{ t('dat_banh_dong_uu_dai','Ưu đãi') }}</span><b>−{{ kho.theTomTat.value.uuDai }}</b></div>
      <div class="tt-dong tt-giam" v-if="kho.theTomTat.value.diem"><span class="tt-nhan">{{ t('dat_banh_dong_diem','Điểm thành viên') }}</span><b>−{{ kho.theTomTat.value.diem }}</b></div>
      <div class="tt-day"><div><b>{{ kho.theTomTat.value.dayNhan }}</b><small v-if="kho.theTomTat.value.dayPhu">{{ kho.theTomTat.value.dayPhu }}</small></div><span class="tt-tong" id="ttTong">{{ kho.theTomTat.value.tong }}</span></div>
    </div>
    <div class="warn" id="warn"><p v-for="(c, i) in kho.cauThanhToan.value" :key="i" style="margin:0 0 4px">{{ c }}</p></div>

    <button class="chk dongy" id="c-dongy" :class="{on: S.CO.dongy}" @click="tgl('dongy')" role="checkbox" :aria-checked="S.CO.dongy ? 'true' : 'false'"><span class="bx">{{ S.CO.dongy ? '✓' : '' }}</span>
      <span class="tx"><span>{{ t('dat_banh_e12f05e93','Tôi đồng ý để The Vagabond Pâtisserie sử dụng họ tên, số điện thoại và địa chỉ để giao bánh và liên hệ về đơn này') }}</span><small><span v-if="baoMat || !S.cauHinh">{{ t('dat_banh_01f52284d','Theo chính sách bảo mật của chúng tôi.') }}</span><span v-else><a href="mailto:hello@thevagabondpatisserie.com?subject=Chinh%20sach%20bao%20mat">{{ t('chinh_sach_ho_tro','Quý khách liên hệ chúng tôi để được cung cấp thông tin bảo mật trước khi gửi.') }}</a></span></small></span></button>
    <p class="doc-cs" id="docChinhSach"><a v-if="baoMat" :href="baoMat.duong" target="_blank" rel="noopener">{{ t('doc_bao_mat','Đọc chính sách bảo mật') }}</a></p>
    <button class="chk" id="c-uudai" :class="{on: S.CO.uudai}" @click="tgl('uudai')" role="checkbox" :aria-checked="S.CO.uudai ? 'true' : 'false'"><span class="bx">{{ S.CO.uudai ? '✓' : '' }}</span>
      <span class="tx"><span>{{ t('uu_dai_nhan_tin','Tôi muốn nhận tin món mới và ưu đãi dịp lễ của The Vagabond Pâtisserie qua Zalo hoặc gọi điện. Tôi đổi ý lúc nào cũng được.') }}</span><small>{{ t('uu_dai_khong_bat_buoc','Không bắt buộc, không tích vẫn đặt bánh bình thường.') }}</small></span></button>

    <div class="cta">
      <button class="btn" id="btnSend" style="width:100%" v-show="!S.guiXong || S.dangGui" :disabled="S.dangGui" :style="{opacity: S.dangGui ? .55 : 1, pointerEvents: S.dangGui ? 'none' : 'auto'}" @click="guiDon()">{{ S.dangGui ? t('dat_banh_848d6282f','Đang gửi đơn...') : t('dat_banh_df2154067','Gửi yêu cầu đặt bánh') }}</button>
      <div id="sendHint" style="margin-top:12px;font-size:13px;line-height:1.6"><dong-chu v-if="S.goi.gui" :phan="S.goi.gui"/></div>
      <div class="noi-dung-dat-xong" data-vgb-vi-tri="dat_xong" v-if="S.guiXong && !S.dangGui"><khoi-noi-dung vi-tri="dat_xong"/></div>
    </div>
  </div>
</section>

<section class="sheet mua" id="sheetMua" :class="{open: S.trang==='mua'}" role="dialog" aria-modal="true" aria-labelledby="sm-name">
  <template v-if="muaXem">
  <div class="wrap"><div class="hero-img">
    <button class="close" type="button" :aria-label="t('dong_chi_tiet_banh','Đóng chi tiết bánh')" @click="nav('#/in-season')"><svg viewBox="0 0 24 24"><path d="M5 5l14 14M19 5L5 19"/></svg></button>
    <anh-mon id="sm-img" :src="muaXem.anh" :lazy="false"/>
  </div></div>
  <div class="wrap">
    <div class="s-head"><h2 id="sm-name">{{ muaXem.ten }}</h2><div id="sm-avail"><div class="avail">{{ muaXem.tinh }}</div></div></div>
    <!-- v693: mô tả, nguyên liệu, dị ứng, bảo quản Marketing nhập ở trình biên tập; ô để trống thì không hiện mục đó. -->
    <details class="tuy-chon" id="sm-thong-tin" v-if="muaXem.coNoiDung" :key="'ttm' + muaXem.g.khoa" open>
      <summary><span>{{ t('chi_tiet_huong_vi','Mô tả và hương vị') }}</span><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14M12 5v14"/></svg></summary>
      <div class="desc" id="sm-desc" v-if="muaXem.moTa">{{ muaXem.moTa }}</div>
      <div id="sm-layers" v-if="muaXem.tang.length"><h3 class="h-sec"><template v-if="muaXem.laBuche">{{ t('dat_banh_f84afdac6','Tầng hương') }} <em>{{ t('dat_banh_17a765496','lớp vị') }}</em></template><template v-else>{{ t('mv_nguyen_lieu','Nguyên liệu') }} <em>{{ t('mv_nguyen_lieu_chinh','chính') }}</em></template></h3>
        <div class="layers"><div class="layer" v-for="(l,i) in muaXem.tang" :key="i"><span class="i">{{ String(i+1).padStart(2,'0') }}</span><div><b>{{ l }}</b></div></div></div></div>
      <div class="them-tt" id="sm-di-ung" v-if="muaXem.diUng"><h3 class="h-sec">{{ t('ct675_di_ung','Thành phần dễ gây dị ứng') }}</h3><p>{{ muaXem.diUng }}</p></div>
      <div class="them-tt" id="sm-bao-quan" v-if="muaXem.baoQuan"><h3 class="h-sec">{{ t('ct675_bao_quan','Bảo quản và sử dụng') }}</h3><p>{{ muaXem.baoQuan }}</p></div>
    </details>

    <template v-if="muaXem.sizes.length > 1">
      <div class="sec"><span class="n">01</span><h3><span>{{ t('mv_chon_size','Chọn size bánh') }}</span></h3><i class="rule"></i></div>
      <div class="sizes" id="sm-sizes"><button v-for="z in muaXem.sizes" :key="z.s.ma" class="size" :class="{on: z.on}" :disabled="!!z.s.het" :data-ma="z.s.ma" @click="kho.setSizeMua(z.s.ma)"><b>{{ z.gia }}</b><span>{{ z.nhan }}</span><em>{{ z.em }}</em></button></div>
    </template>
    <template v-else>
      <div class="sec"><span class="n">01</span><h3><span>{{ t('dat_banh_71efef066','Giá') }}</span></h3><i class="rule"></i></div>
      <div id="sm-gia" style="font-size:22px;margin-top:14px"><b style="font-weight:400">{{ tienTom(muaXem.z.gia||0) }}</b></div>
    </template>
    <div class="fine"><span>{{ t('dat_banh_c02f89b47','Giá đã gồm thuế GTGT. Chưa gồm phí vận chuyển nếu có.') }}</span></div>
    <div class="fine mua-luat-ct" id="sm-luat" v-if="muaXem.luat"><span>{{ t('mv_luat_tieu','Lịch nhận bánh:') }} {{ muaXem.luat }}.</span></div>

    <div class="chon-so-luong" v-if="!muaXem.z.het"><span id="sm-qty-label">{{ t('so_luong_banh','Số lượng bánh') }}</span><div class="qty"><button type="button" id="sm-minus" :disabled="muaXem.sl<=1" @click="kho.doiSlMua(-1)" :aria-label="t('giam_so_luong','Giảm số lượng')"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14"/></svg></button><output id="sm-qty" aria-labelledby="sm-qty-label" aria-live="polite">{{ muaXem.sl }}</output><button type="button" id="sm-plus" @click="kho.doiSlMua(1)" :aria-label="t('tang_so_luong','Tăng số lượng')"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14M12 5v14"/></svg></button></div></div>

    <div id="sm-khoiruot" v-if="muaXem.ruot.length">
      <div class="sec"><span class="n">02</span><h3><span>{{ t('dat_banh_488b179ee','Trong hộp có gì') }}</span></h3><i class="rule"></i></div>
      <div class="mua-ruot" id="sm-ruot"><div v-for="(r,i) in muaXem.ruot" :key="i"><b>{{ r[0] }}</b><span>{{ r[1] }}</span></div></div>
    </div>
    <template v-if="muaXem.kem.length">
      <div class="sec"><span class="n">02</span><h3><span>{{ t('pk_co_san_tieu_de','Kèm theo mỗi bánh') }}</span></h3><i class="rule"></i></div>
      <div class="co-san">
        <div class="co-san-mo">{{ t('pk_co_san_mo_ta','Đã nằm trong giá bánh, quý khách không phải mua thêm.') }}</div>
        <ul class="acc" id="sm-acc"><li v-for="a in muaXem.kem" :key="a.k"><img v-if="anhWeb(a.ka, '')" :src="anhWeb(a.ka, '')" alt=""><span v-else class="acc-chu" aria-hidden="true">{{ t(a.k, a.n).split(' ')[0] }}</span><span class="nm">{{ t(a.k, a.n) }}<small v-if="t(a.ks, a.sub)">{{ t(a.ks, a.sub) }}</small></span></li></ul></div>
    </template>
    <!-- v693: sốt chấm bán kèm Panettone, tối đa 2 hũ mỗi bánh; mã sốt khai ở Mùa vụ, chưa khai thì không có mục này. -->
    <template v-if="muaXem.sot.length">
      <div class="sec"><span class="n">03</span><h3><span>{{ t('mv_sot_tieu_de','Sốt chấm đi kèm') }}</span></h3><i class="rule"></i></div>
      <div class="dc-don mua-sot" id="sm-sot">
        <div class="dc-mo">{{ t('mv_sot_mo_ta','Chọn tối đa {so} hũ cho mỗi bánh. Đặt nhiều bánh thì số hũ nhân theo số bánh.',{so:kho.sotMoiBanh.value}) }}</div>
        <ul class="acc dc-ds"><li v-for="x in muaXem.sot" :key="x.y.ma" :data-sot="x.y.ma"><img v-if="x.y.anh" :src="x.y.anh" alt=""><span v-else class="acc-chu" aria-hidden="true">{{ t('mv_sot_chu','Sốt') }}</span><span class="nm">{{ x.ten }}<small>{{ x.gia }}</small></span>
          <div class="sl-vien" role="group" :aria-label="t('so_luong_cua','Số lượng {ten}',{ten:x.ten})"><button type="button" :disabled="!x.so" :aria-label="t('sl_bot_1','Bớt 1')" @click="kho.doiSotMua(x.y.ma,-1)"><bieu-tuong loai="tru"/></button>
            <output aria-live="polite">{{ x.so }}</output><button type="button" :disabled="kho.soSotChon.value>=kho.sotMoiBanh.value" :aria-label="t('sl_them_1','Thêm 1')" @click="kho.doiSotMua(x.y.ma,1)"><bieu-tuong loai="cong"/></button></div></li></ul>
        <div class="dc-mo mua-sot-du" id="sm-sot-du" v-if="kho.soSotChon.value>=kho.sotMoiBanh.value" role="status">{{ t('mv_sot_du','Đã chọn đủ {so} hũ cho mỗi bánh.',{so:kho.sotMoiBanh.value}) }}</div>
      </div>
    </template>
    <!-- v693: Bûche mua thêm phụ kiện như bánh ổ sinh nhật (nến số, nón, sash, đồ dự phòng). -->
    <details class="tuy-chon mua-pk" id="sm-phu-kien" v-if="muaXem.laBuche" :key="'pkm' + muaXem.g.khoa">
      <summary><span class="mua-pk-chu"><b>{{ t('pk_mua_them_681','Mua thêm phụ kiện') }}</b><small>{{ t('pk_mua_them_phu_681','Nến số, nón và sash sinh nhật') }}</small></span><span class="mua-pk-nut" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 12h14M12 5v14"/></svg></span></summary>
    <div class="numlab"><span>{{ t('dat_banh_909dfa9ae','Nến số') }}</span> <b><span>{{ t('dat_banh_87aff9ee8','17.000 đ / số') }}</span></b></div>
    <div class="nums" id="sm-nums"><button v-for="x in NUMS" :key="x.n" class="numbtn" :class="{on: S.nums.includes(x.n)}" @click="kho.toggleNum(x.n)" :aria-label="t('nen_so','Nến số {so}',{so:x.n})"><img :src="anhWeb(x.ka, x.img)" :alt="t('nen_so','Nến số {so}',{so:x.n})"></button></div>
    <div class="numpick" id="sm-numpick">
      <template v-if="S.nums.length"><span>{{ t('dat_banh_21e08aca8','Số trên bánh') }}</span><span class="big">{{ S.nums.join('') }}</span>
        <button class="x" @click="kho.clearNums()"><bieu-tuong loai="bo"/>{{ t('dat_banh_82339c0a8','Xoá') }}</button></template>
      <span v-else style="color:var(--fog-2)">{{ t('dat_banh_16dd7180d','Bấm lần lượt từng số, ví dụ bấm 2 rồi 6 được số 26.') }}</span>
    </div>
    <ul class="addons" id="sm-addons"><li v-for="a in ADDONS.filter(x => !x.du_phong)" :key="a.id"><button :class="{on: S.adds.includes(a.id)}" @click="kho.toggleAdd(a.id)">
      <span class="bx"><bieu-tuong v-if="S.adds.includes(a.id)" loai="chon"/></span>
      <span class="ph"><img :src="anhWeb(a.ka, a.img)" alt=""></span>
      <span class="nm">{{ t(a.k, a.n) }}</span><span class="pr">{{ tienTom(a.p) }}</span></button></li></ul>
    <p class="hint" id="sm-mau-ngau-nhien">{{ t('pk_mau_ngau_nhien','Màu nón và sash giao ngẫu nhiên.') }}</p>
    <!-- Hộp, túi, nến dự phòng thu vào dòng gấp vì bánh đã có sẵn một bộ. Đã chọn món dự phòng (sửa dòng giỏ) thì mở sẵn. -->
    <details class="du-phong" id="sm-duphong" :key="'dpm' + muaXem.g.khoa" :open="ADDONS.some(x => x.du_phong && S.adds.includes(x.id))"><summary><span>{{ t('pk_du_phong_hoi','Cần thêm hộp, túi hay nến dự phòng?') }}</span> <small>{{ t('pk_du_phong_mo','Mỗi bánh đã có sẵn một bộ.') }}</small></summary>
    <ul class="addons" id="sm-addons-dp"><li v-for="a in ADDONS.filter(x => x.du_phong)" :key="a.id"><button :class="{on: S.adds.includes(a.id)}" @click="kho.toggleAdd(a.id)">
      <span class="bx"><bieu-tuong v-if="S.adds.includes(a.id)" loai="chon"/></span>
      <span class="ph"><img :src="anhWeb(a.ka, a.img)" alt=""></span>
      <span class="nm">{{ t(a.k, a.n) }}</span><span class="pr">{{ tienTom(a.p) }}</span></button></li></ul></details>
    </details>
    <div class="addsum" id="sm-addsum" aria-live="polite" v-if="kho.addsMuaXem.value.length">{{ t('dat_banh_fc2a93d57','Đã chọn thêm:') }} <b>{{ kho.T.tenAddsGop(kho.addsMuaXem.value) }}</b> {{ t('dat_banh_b6d0a562d','· cộng thêm') }} <b>{{ tienTom(kho.addsMuaXem.value.reduce((a,x)=>a+x.p,0)) }}</b></div>

    <div class="cta">
      <button class="btn" id="sm-cta" :disabled="!!muaXem.z.het" @click="themTuMua()">{{ muaXem.z.het ? t('dat_banh_a6001ad7a','Hết hàng') : t('dat_banh_34d469c70','Thêm vào giỏ · {gia_tri_a}',{gia_tri_a: tienTom(kho.tienNutMua.value)}) }}</button>
      <a class="tel" :aria-label="t('goi_ho_tro_dat_banh','Gọi hỗ trợ đặt bánh')" :href="'tel:'+telSo()"><svg viewBox="0 0 24 24"><path d="${GOI}"/></svg></a>
    </div>
  </div>
  </template>
</section>

<section class="sheet" id="sheet" :class="{open: S.trang==='banh'}" role="dialog" aria-modal="true" aria-labelledby="s-name">
  <template v-if="chiTiet">
  <div class="wrap"><div class="hero-img">
    <button class="close" type="button" :aria-label="t('dong_chi_tiet_banh','Đóng chi tiết bánh')" @click="navBack()"><svg viewBox="0 0 24 24"><path d="M5 5l14 14M19 5L5 19"/></svg></button>
    <anh-mon id="s-img" :src="chiTiet.anhs[anhChon] || chiTiet.c.img" :lazy="false"/>
  </div></div>
  <div class="wrap">
    <div class="thumbs" id="s-thumbs" v-if="chiTiet.anhs.length >= 2"><button v-for="(u,i) in chiTiet.anhs" :key="i" class="th" :class="{on: i===anhChon}" @click="anhChon=i" :aria-label="t('anh_thu_tu','Ảnh {so}',{so:i+1})"><img loading="lazy" :src="u" alt=""></button></div>
    <div class="s-head"><h2 id="s-name" :class="{vi: chiTiet.vi}">{{ chiTiet.ten }}</h2><div id="s-avail">
      <div class="avail" v-if="chiTiet.tinhTrang==='co'"><i class="dot"></i>{{ t('san_pham_co_san','Có sẵn hôm nay') }} · {{ chiTiet.tonChu }}</div>
      <div class="avail" v-else-if="chiTiet.tinhTrang==='dat'">{{ chiTiet.datChu }}</div>
      <div class="avail" v-else-if="chiTiet.tinhTrang==='mua'">{{ chiTiet.nhanMua }}</div>
      <div class="avail" v-else>{{ t('dat_banh_786f9ed52','Đặt trước · bếp làm theo đơn') }}</div></div></div>
    <details class="tuy-chon" id="s-thong-tin" :key="'tt' + chiTiet.c.k">
      <summary><span>{{ t('chi_tiet_huong_vi','Mô tả và hương vị') }}</span><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14M12 5v14"/></svg></summary>
      <div class="desc" id="s-desc">{{ chiTiet.moTa }}</div><div id="s-layers">
        <template v-if="chiTiet.tang"><h3 class="h-sec">{{ t('dat_banh_f84afdac6','Tầng hương') }} <em>{{ t('dat_banh_17a765496','lớp vị') }}</em></h3><div class="layers"><div class="layer" v-for="(l,i) in chiTiet.tang" :key="i"><span class="i">{{ String(i+1).padStart(2,'0') }}</span><div><b>{{ l[0] }}</b><i>{{ l[1] }}</i></div></div></div></template>
        <div v-else class="fine" style="margin-top:20px">{{ t('dat_banh_b96013446','Mô tả và tầng hương lớp vị của món này đang được cập nhật.') }}</div></div>
      <div class="them-tt" id="s-di-ung" v-if="chiTiet.diUng"><h3 class="h-sec">{{ t('ct675_di_ung','Thành phần dễ gây dị ứng') }}</h3><p>{{ chiTiet.diUng }}</p></div>
      <div class="them-tt" id="s-bao-quan" v-if="chiTiet.baoQuan"><h3 class="h-sec">{{ t('ct675_bao_quan','Bảo quản và sử dụng') }}</h3><p>{{ chiTiet.baoQuan }}</p></div>
    </details>

    <div class="sec"><span class="n">01</span><h3><span>{{ t('dat_banh_0e619c4c4','Giá bánh') }}</span></h3><i class="rule"></i><button type="button" class="huong-size" id="s-huongsize" @click="moHuongSize" aria-haspopup="dialog" aria-controls="huongSize"><i aria-hidden="true">?</i><span>{{ t('huong_size_nut','Chọn cỡ bánh') }}</span></button></div>
    <div class="sizes" id="s-sizes"><button v-for="z in kichThuocDong" :key="z.s.id" class="size" :class="{on: z.s.id===S.curSizeId}" @click="kho.setSize(z.s.id)"><b>{{ z.gia }}</b><span>{{ z.nhan }}</span><em v-if="z.em">{{ z.em }}</em></button></div>
    <div class="fine"><span>{{ t('dat_banh_c02f89b47','Giá đã gồm thuế GTGT. Chưa gồm phí vận chuyển nếu có.') }}</span></div>

    <div class="chon-so-luong"><span id="s-qty-label">{{ t('so_luong_banh','Số lượng bánh') }}</span><div class="qty"><button type="button" id="s-minus" :disabled="S.soLuong<=1" @click="kho.doiSoLuong(-1)" :aria-label="t('giam_so_luong','Giảm số lượng')"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14"/></svg></button><output id="s-qty" aria-labelledby="s-qty-label" aria-live="polite">{{ S.soLuong }}</output><button type="button" @click="kho.doiSoLuong(1)" :aria-label="t('tang_so_luong','Tăng số lượng')"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14M12 5v14"/></svg></button></div></div>
    <!-- v598 (port v597): khách tưởng phải mua thêm hộp, túi (Minh Vũ báo). Khung này luôn hiện, không gấp, nói rõ đồ đã có sẵn trong giá bánh. -->
    <div class="sec"><span class="n">02</span><h3><span>{{ t('pk_co_san_tieu_de','Kèm theo mỗi bánh') }}</span></h3><i class="rule"></i></div>
    <div class="co-san">
      <div class="co-san-mo">{{ t('pk_co_san_mo_ta','Đã nằm trong giá bánh, quý khách không phải mua thêm.') }}</div>
      <ul class="acc" id="s-acc"><li v-for="a in ACC" :key="a.k"><img :src="anhWeb(a.ka, a.i)" alt=""><span class="nm">{{ t(a.k, a.n) }}<small v-if="t(a.ks, a.sub)">{{ t(a.ks, a.sub) }}</small></span></li></ul></div>

    <!-- v681 (BẢN 2 mục 1.2): dòng Mua thêm phụ kiện, lấp lánh MỘT lần khi lần đầu lọt vào màn hình. -->
    <details class="tuy-chon mua-pk" id="s-phu-kien" :key="'pk' + chiTiet.c.k">
      <summary><span class="mua-pk-chu"><b>{{ t('pk_mua_them_681','Mua thêm phụ kiện') }}</b><small>{{ t('pk_mua_them_phu_681','Nến số, nón và sash sinh nhật') }}</small></span><span class="mua-pk-nut" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 12h14M12 5v14"/></svg></span></summary>
    <div class="numlab"><span>{{ t('dat_banh_909dfa9ae','Nến số') }}</span> <b><span>{{ t('dat_banh_87aff9ee8','17.000 đ / số') }}</span></b></div>
    <div class="nums" id="s-nums"><button v-for="x in NUMS" :key="x.n" class="numbtn" :class="{on: S.nums.includes(x.n)}" @click="kho.toggleNum(x.n)" :aria-label="t('nen_so','Nến số {so}',{so:x.n})"><img :src="anhWeb(x.ka, x.img)" :alt="t('nen_so','Nến số {so}',{so:x.n})"></button></div>
    <div class="numpick" id="s-numpick">
      <template v-if="S.nums.length"><span>{{ t('dat_banh_21e08aca8','Số trên bánh') }}</span><span class="big">{{ S.nums.join('') }}</span>
        <button class="x" @click="kho.clearNums()"><bieu-tuong loai="bo"/>{{ t('dat_banh_82339c0a8','Xoá') }}</button></template>
      <span v-else style="color:var(--fog-2)">{{ t('dat_banh_16dd7180d','Bấm lần lượt từng số, ví dụ bấm 2 rồi 6 được số 26.') }}</span>
    </div>
    <ul class="addons" id="s-addons"><li v-for="a in ADDONS.filter(x => !x.du_phong)" :key="a.id"><button :class="{on: S.adds.includes(a.id)}" @click="kho.toggleAdd(a.id)">
      <span class="bx"><bieu-tuong v-if="S.adds.includes(a.id)" loai="chon"/></span>
      <span class="ph"><img :src="anhWeb(a.ka, a.img)" alt=""></span>
      <span class="nm">{{ t(a.k, a.n) }}</span><span class="pr">{{ tienTom(a.p) }}</span></button></li></ul>
    <p class="hint" id="s-mau-ngau-nhien">{{ t('pk_mau_ngau_nhien','Màu nón và sash giao ngẫu nhiên.') }}</p>
    <!-- Hộp, túi, nến dự phòng thu vào dòng gấp vì bánh đã có sẵn một bộ. Đã chọn món dự phòng (sửa dòng giỏ) thì mở sẵn. -->
    <details class="du-phong" id="s-duphong" :key="'dp' + chiTiet.c.k" :open="ADDONS.some(x => x.du_phong && S.adds.includes(x.id))"><summary><span>{{ t('pk_du_phong_hoi','Cần thêm hộp, túi hay nến dự phòng?') }}</span> <small>{{ t('pk_du_phong_mo','Mỗi bánh đã có sẵn một bộ.') }}</small></summary>
    <ul class="addons" id="s-addons-dp"><li v-for="a in ADDONS.filter(x => x.du_phong)" :key="a.id"><button :class="{on: S.adds.includes(a.id)}" @click="kho.toggleAdd(a.id)">
      <span class="bx"><bieu-tuong v-if="S.adds.includes(a.id)" loai="chon"/></span>
      <span class="ph"><img :src="anhWeb(a.ka, a.img)" alt=""></span>
      <span class="nm">{{ t(a.k, a.n) }}</span><span class="pr">{{ tienTom(a.p) }}</span></button></li></ul></details>
    </details>
    <div class="addsum" id="s-addsum" aria-live="polite" :style="{display: kho.phuKienChon.value.length ? 'block' : 'none'}"><template v-if="kho.phuKienChon.value.length">{{ t('dat_banh_fc2a93d57','Đã chọn thêm:') }} <b>{{ kho.phuKienChon.value.map(x=>x.n).join(', ') }}</b> {{ t('dat_banh_b6d0a562d','· cộng thêm') }} <b>{{ tienTom(kho.phuKienChon.value.reduce((a,x)=>a+x.p,0)) }}</b></template></div>

    <div class="cta">
      <button class="btn" id="s-cta" @click="themVaoGio()">{{ S.dongDangSua >= 0 ? t('luu_banh','Lưu thay đổi') : t('dat_banh_34d469c70','Thêm vào giỏ · {gia_tri_a}',{gia_tri_a: tienTom(kho.tienNutThem.value)}) }}</button>
      <a class="tel" :aria-label="t('goi_ho_tro_dat_banh','Gọi hỗ trợ đặt bánh')" :href="'tel:'+telSo()"><svg viewBox="0 0 24 24"><path d="${GOI}"/></svg></a>
    </div>
  </div>
  </template>
</section>

<div class="hs-nen" id="huongSize" :hidden="!S.huongSize" @click.self="dongHuongSize">
  <div class="hs-hop" role="dialog" aria-modal="true" aria-labelledby="hs-tieu-de">
    <button type="button" class="hs-x" id="hs-dong" @click="dongHuongSize" :aria-label="t('huong_size_dong','Đóng')">×</button>
    <h3 class="hs-tieu-de" id="hs-tieu-de">{{ t('huong_size_tieu_de','Chọn cỡ bánh') }}</h3>
    <p class="hs-mo-ta">{{ t('huong_size_mo_ta','Mọi bánh cao 5 cm. Số miếng tính theo cách cắt thường, mỗi miếng vừa một người ăn tráng miệng.') }}</p>
    <div class="hs-luoi" id="hs-luoi"><div class="hs-o" v-for="(z, i) in HUONG_SIZE" :key="z.cm"><svg viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="44"/><line v-for="l in kho.T.duongCat(z.lat)" :key="l.x2 + ',' + l.y2" x1="50" y1="50" :x2="l.x2" :y2="l.y2"/></svg>
      <div class="hs-so">{{ t('huong_size_so','Size {so}',{so: i + 1}) }}</div><div class="hs-cm">Ø {{ z.cm }} cm</div>
      <div class="hs-mieng">{{ t('huong_size_mieng','{so} miếng',{so: z.mieng}) }}</div><div class="hs-nguoi">{{ t('huong_size_nguoi','{so} người',{so: z.nguoi}) }}</div></div></div>
    <p class="hs-meo">{{ t('huong_size_meo','Tiệc đông người hoặc ăn thay bữa thì chọn lớn hơn một size. Chưa chắc thì gọi 0931 224 334, chúng tôi tư vấn ngay.') }}</p>
    <button type="button" class="btn hs-ok" @click="dongHuongSize"><span>{{ t('huong_size_ok','Đã hiểu, chọn size') }}</span></button>
  </div>
</div>

<!-- v681: mẫu cờ chúc của một chiếc (BẢN 2 mục 2.1). -->
<div class="hs-nen" id="mauCo" :hidden="!kho.chiecMauCo.value" @click.self="kho.moMauCo('')">
  <div class="hs-hop mc-hop" role="dialog" aria-modal="true" aria-labelledby="mc-tieu-de">
    <button type="button" class="hs-x" id="mc-dong" @click="kho.moMauCo('')" :aria-label="t('huong_size_dong','Đóng')">✕</button>
    <img class="mc-anh" :src="anhWeb('anh_co_mau', ANH_CO)" alt="">
    <h3 class="hs-tieu-de" id="mc-tieu-de">{{ t('phu_kien_8034a0777','Cờ cắm in lời chúc') }}</h3>
    <p class="hs-mo-ta">{{ t('mc_mo_ta','Ảnh minh hoạ. Màu cờ có thể khác, lời chúc in đúng nội dung quý khách ghi.') }}</p>
    <div class="mc-in"><small>{{ t('mc_se_in','LỜI CHÚC SẼ IN') }}</small><b>{{ kho.chiecMauCo.value && kho.chiecMauCo.value.wish ? kho.chiecMauCo.value.wish : t('mc_chua_nhap','Chưa nhập lời chúc') }}</b></div>
  </div>
</div>
<!-- v681: hỏi lại trước khi bỏ một chiếc bánh đã có lời chúc hoặc thiệp (BẢN 2 mục 2.0). -->
<div class="hs-nen" id="hoiBo" :hidden="!S.hoiBo" @click.self="kho.giuLai()">
  <div class="hs-hop hb-hop" role="alertdialog" aria-modal="true" aria-labelledby="hb-chu">
    <p class="hs-mo-ta" id="hb-chu">{{ S.hoiBo ? S.hoiBo.chu : '' }}</p>
    <div class="hb-nut"><button type="button" class="hb-dong-y" id="hb-dong-y" @click="dongYBo()">{{ S.hoiBo ? S.hoiBo.nut : '' }}</button><button type="button" class="nut-vien" id="hb-giu" @click="kho.giuLai()">{{ t('hoi_bo_giu','Giữ lại') }}</button></div>
  </div>
</div>
`;
