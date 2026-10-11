/* Khuôn giao diện trang đặt bánh bản Vue. Thẻ, lớp, id CHÉP từ banh.html
   bản Rocca (a20e85054) để CSS đã duyệt áp y nguyên. Sửa giao diện thì sửa ở
   đây và so ảnh với bản cũ ở 390, 1440, 320 trước khi bàn giao. */
const GOI = 'M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2Z';

export const MAU = `
<header><div class="wrap hd">
  <div class="hd-left"><a href="#/" @click.prevent="nav('#/')" :aria-label="t('dat_banh_86376d53a','Về trang chủ')"><img class="logo" :src="LOGO" :alt="t('dat_banh_913466c0d','The Vagabond Pâtisserie')"></a></div>
  <a class="hd-phone" :href="'tel:'+telSo()"><svg viewBox="0 0 24 24"><path d="${GOI}"/></svg>{{ telChu() }}</a>
  <nav class="dich-vu" :aria-label="t('dat_banh_2c5093996','Dịch vụ')"><a href="/dat-ban">{{ t('nut_dat_ban','Đặt bàn') }}</a><a href="/thanh-vien">{{ t('nut_thanh_vien','Thành viên') }}</a></nav>
</div></header>

<div id="noi-dung-marketing" data-vgb-vi-tri="dau_trang" :aria-label="t('dat_banh_f4a541343','Lời chào từ chúng tôi')"><khoi-noi-dung vi-tri="dau_trang"/></div>
<div id="danh-muc-banh" tabindex="-1"></div>
<p class="ngay-ban" id="ngayBan">{{ ngayBan }}</p>
<nav class="tabs">
  <button class="tab mua" :class="{on: tab==='season'}" data-tab="season" id="tabMua" :hidden="!kho.coMua.value" @click="go('season')">{{ t('tab_season','In season') }}</button>
  <button class="tab store" :class="{on: tab==='store'}" data-tab="store" id="tabStore" :hidden="!S.storeDaTai" @click="go('store')">{{ t('tab_store','In store') }}</button>
  <button class="tab" :class="{on: tab==='uu_dai'}" data-tab="uu_dai" @click="go('uu_dai')">{{ t('tab_uu_dai','Ưu đãi') }}</button>
  <button class="tab" :class="{on: tab==='tiec'}" data-tab="tiec" :hidden="!coTiec" @click="go('tiec')">{{ t('tab_tiec','Tiệc') }}</button>
  <button class="tab" :class="{on: tab==='tuyen_dung'}" data-tab="tuyen_dung" @click="go('tuyen_dung')">{{ t('tab_tuyen_dung','Tuyển dụng') }}</button>
  <button class="tab" :class="{on: tab==='today'}" data-tab="today" @click="go('today')">{{ t('tab_today','Có sẵn hôm nay') }}</button>
  <button class="tab" :class="{on: tab==='order'}" data-tab="order" @click="go('order')">{{ t('tab_order','Đặt bánh trước') }}</button>
</nav>

<section class="wrap" id="uu_dai" :hidden="tab!=='uu_dai'"><header class="sec-head"><h1 class="h1">{{ t('tab_uu_dai','Ưu đãi') }}</h1></header><chuyen-muc v-if="tab==='uu_dai'" loai="uu_dai"/></section>
<section class="wrap" id="tiec" :hidden="tab!=='tiec'"><header class="sec-head"><h1 class="h1">{{ t('tab_tiec','Tiệc') }}</h1></header><chuyen-muc v-if="tab==='tiec'" loai="tiec"/></section>
<section class="wrap" id="tuyen_dung" :hidden="tab!=='tuyen_dung'"><header class="sec-head"><h1 class="h1">{{ t('tab_tuyen_dung','Tuyển dụng') }}</h1></header><chuyen-muc v-if="tab==='tuyen_dung'" loai="tuyen_dung"/></section>

<main id="season" :hidden="tab!=='season'">
  <div class="noi-dung-theo-tab" data-vgb-vi-tri="season"><khoi-noi-dung vi-tri="season"/></div>
  <section class="wrap">
    <div class="mua-hd">
      <div class="meta"><span class="num" id="muaSo"><span>{{ t('dat_banh_323acda9d','00 / In season') }}</span></span></div>
      <h1 class="h1" id="muaTen">{{ S.MUA.ten_mua || t('dat_banh_d7e8f3298','Hàng theo mùa') }}</h1>
      <div class="mua-han" id="muaHan">{{ kho.hanMua.value }}</div>
    </div>
    <div class="grid" id="muaLuoi">
      <div class="card-o" v-for="x in monMua" :key="x.m.ma">
        <button class="card mua" :class="{het: x.m.het}" @click="moMua(x.m)">
          <div class="ph"><i class="tagline">{{ t('nhan_seasonal','Seasonal') }}</i><anh-mon :src="x.m.anh"/></div>
          <div class="c-body">
            <div class="c-name">{{ x.ten }}</div>
            <div class="c-price"><b>{{ tienTom(x.m.gia||0) }}</b></div>
            <div class="ruot" v-if="x.moTa">{{ t('dat_banh_afcf62369','Gồm') }} {{ x.moTa }}</div>
            <div class="c-sizes"><i class="sz" :class="{has: !x.m.het}">{{ x.chip }}</i></div>
            <div class="c-go">{{ t('dat_banh_00b018c50','Xem chi tiết →') }}</div>
          </div>
        </button>
        <button v-if="!x.m.het" class="c-them" @click="kho.themHangMua(x.m.ma)" :aria-label="t('them_nhanh_mon','Thêm nhanh {ten} vào giỏ',{ten:x.ten})"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></button>
      </div>
    </div>
  </section>
</main>

<main id="store" :hidden="tab!=='store'">
  <div class="noi-dung-theo-tab" data-vgb-vi-tri="store"><khoi-noi-dung vi-tri="store"/></div>
  <section class="wrap">
    <div class="store-hd">
      <div class="meta"><span class="num"><span>{{ t('dat_banh_289234b8c','00 / In store') }}</span></span><span id="storeLuc">{{ S.STORE.cap_nhat ? t('dat_banh_8f92d9663','Cập nhật') + ' ' + String(S.STORE.cap_nhat).slice(11,16) : '' }}</span></div>
      <h1 class="h1"><tieu-de-muc vi-tri="store" :dong="['Bánh trên tủ','tại quầy']"/></h1>
    </div>
    <div id="storeBody">
      <template v-if="quayHien">
        <div class="quay-chon"><button v-for="q in quayHien.quay" :key="q.ma" :aria-pressed="String(q.ma===quayHien.chon.ma)" @click="S.quayChon=q.ma; S.nhomQuay=''">
          <b>{{ q.ten }}</b><span>{{ q.dia_chi || '' }}</span><span>{{ (q.mon||[]).reduce((a,m)=>a+(m.con||0),0) }} {{ t('dat_banh_3556aabb5','bánh') }} · {{ (q.mon||[]).length }} {{ t('so_loai','loại') }}</span></button></div>
        <div class="cm-chips"><button v-for="n in quayHien.nhom" :key="n.n" :aria-pressed="String(n.n===S.nhomQuay)" @click="S.nhomQuay=n.n">{{ (n.n || t('tat_ca_muc','Tất cả')) + ' · ' + n.so }}</button></div>
        <div class="quay">
          <div class="q-ten">{{ quayHien.chon.ten }}</div>
          <div class="q-dc" v-if="quayHien.chon.dia_chi">{{ quayHien.chon.dia_chi }}</div>
          <div class="q-con">{{ quayHien.tong ? t('dat_banh_75f5cf26e','Còn') + ' ' + quayHien.tong + ' ' + t('dat_banh_9ce7e8d31','bánh ·') + ' ' + quayHien.mon.length + ' ' + t('dat_banh_97a16dfdf','loại') : t('dat_banh_71fb5d32e','Hiện đã hết bánh trên tủ') }}</div>
        </div>
        <div v-if="!quayHien.mon.length" class="store-empty">{{ t('dat_banh_a85783ffc','Quầy này đã bán hết bánh trong tủ. Bánh mới lên tủ theo từng đợt trong ngày.') }}</div>
        <div v-else class="grid">
          <div class="card" v-for="m in quayHien.mon" :key="m.ma">
            <div class="ph"><i class="tagline">{{ quayHien.chon.ten_ngan || quayHien.chon.ten }}</i><anh-mon :src="m.anh"/></div>
            <div class="c-body">
              <div class="c-name">{{ tMon(m.ma,'ten',m.ten) }}</div>
              <div class="c-price" v-if="m.gia"><b>{{ tienTom(m.gia) }}</b></div>
              <div class="c-sizes"><i class="sz has">{{ t('dat_banh_75f5cf26e','Còn') }} {{ m.con }}</i></div>
            </div>
          </div>
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
    <div class="rail" id="rail"><button v-for="d in kho.ngayRail.value" :key="d.i" class="day" :class="{on: d.on, best: d.best}" @click="kho.pick(d.i)"><span>{{ d.ten }}</span><b>{{ d.ngay }}</b></button></div>
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

<cua-hang/>
<div data-vgb-vi-tri="cuoi_trang" :aria-label="t('dat_banh_b69802262','Câu chuyện Vagabond')"><khoi-noi-dung vi-tri="cuoi_trang"/></div>
<footer><div class="wrap">
  <div class="f-note"><span id="fNotePhi">{{ S.mienPhiTu > 0 ? t('dat_banh_a6738ef6d','Giá đã gồm thuế GTGT. Miễn phí giao cho đơn từ') + ' ' + tienTom(S.mienPhiTu) : t('dat_banh_8b550092a','Giá đã gồm thuế GTGT, chưa gồm phí vận chuyển') }}</span><br>{{ t('dat_banh_4c203e5ec','Giá và tồn kho thay đổi theo mùa và nguyên liệu nhập khẩu') }}</div>
  <div class="f-phap-nhan" id="fPhapNhan">
    <b>{{ t('dat_banh_15f2c7f29','Công ty TNHH Patisserie Vagabond') }}</b><br>
    {{ t('dat_banh_2085c9658','Mã số thuế 0318561568') }}<br>
    {{ t('dat_banh_2f7b911ea','Cửa hàng Sài Gòn: 9 Trần Cao Vân, Phường Sài Gòn (Quận 1 cũ), TP. Hồ Chí Minh') }}<br>
    {{ t('dat_banh_cc4a76159','Bếp Tân Sơn Hoà: 307/1 Nguyễn Văn Trỗi, Phường Tân Sơn Hoà (Tân Bình cũ), TP. Hồ Chí Minh') }}<br>
    <span id="fLienHe"><template v-if="lienHe.dien_thoai || lienHe.email"><template v-if="lienHe.dien_thoai">{{ t('dien_thoai','Điện thoại') }} <a :href="'tel:'+String(lienHe.dien_thoai_so||'')">{{ lienHe.dien_thoai }}</a></template><template v-if="lienHe.dien_thoai && lienHe.email"> · </template><template v-if="lienHe.email">Email <a :href="'mailto:'+lienHe.email">{{ lienHe.email }}</a></template></template><template v-else>{{ t('dat_banh_08fc3ada4','Điện thoại') }} <a :href="'tel:'+telSo()">{{ telChu() }}</a></template></span>
  </div>
  <nav class="f-cs" id="fChinhSach" :aria-label="t('dat_banh_e9ba7dd58','Chính sách')"><a v-for="c in chinhSach" :key="c.duong" :href="c.duong">{{ c.ten }}</a></nav>
</div></footer>

<div class="bar" id="bar" :class="{on: S.CART.length > 0 && !gioMo}"><div class="wrap in">
  <span class="cnt" id="barTxt"><template v-if="S.CART.length"><b>{{ t('dat_banh_a2f8afb2e','{gia_tri_a} bánh · {gia_tri_b}',{gia_tri_a: kho.soBanh.value, gia_tri_b: tienTom(kho.tienBanh.value)}) }}</b><small>{{ kho.dongMienPhi.value }}</small></template></span>
  <button class="go" @click="moGio()">{{ t('dat_banh_fb62c648d','Xem giỏ') }}</button>
</div></div>
<div class="toast" id="toast" :class="{on: S.toast.on}">{{ S.toast.chu }}</div>
<kenh-noi/>

<section class="co" id="checkout" :class="{open: gioMo}" role="dialog" aria-modal="true" aria-labelledby="co-title">
  <div class="co-top"><div class="wrap in">
    <button class="bk" type="button" :aria-label="t('quay_lai_chon_banh','Quay lại chọn bánh')" @click="navBack()"><svg viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg></button>
    <b id="co-title"><span>{{ t('dat_banh_74ed5c7f8','Thông tin đơn hàng') }}</span></b>
  </div></div>
  <div class="wrap" style="padding-bottom:40px" v-if="gioMo || S.guiXong">

    <div class="sec"><span class="n">01</span><h3><span>{{ t('dat_banh_f257f0ff4','Giỏ bánh') }}</span></h3><i class="rule"></i></div>
    <ul class="cart" id="cartList">
      <li v-if="!S.CART.length" class="cart-empty">{{ t('dat_banh_b5f223212','Giỏ chưa có bánh nào.') }}</li>
      <li v-for="d in kho.dongGio.value" :key="d.i + '|' + d.o.id"><div class="im"><img :src="d.o.img" alt=""></div>
        <div class="bd"><div class="t">{{ d.ten }}</div>
          <div class="s">{{ d.phu }}</div><div class="ex" v-if="d.ex.length"><template v-for="(e,j) in d.ex" :key="j"><br v-if="j">
            <dong-chu :phan="e"/></template></div></div>
        <div class="rt"><button v-if="d.o.cm" class="sua-gio" @click="suaDongGio(d.i)"><bieu-tuong loai="sua"/>{{ t('sua_banh','Sửa bánh') }}</button>
          <div class="p">{{ d.tien }}</div><div class="qty">
            <button :disabled="d.o.qty<=1" :aria-label="t('giam_so_luong','Giảm số lượng')" @click="kho.cartQty(d.i,-1)"><bieu-tuong loai="tru"/></button>
            <span>{{ d.o.qty }}</span><button :aria-label="t('tang_so_luong','Tăng số lượng')" @click="kho.cartQty(d.i,1)"><bieu-tuong loai="cong"/></button></div>
          <button class="rm" @click="kho.cartRemove(d.i); if(!S.CART.length) nav('#/',true)"><bieu-tuong loai="bo"/>{{ t('bo_khoi_gio','Bỏ khỏi giỏ') }}</button></div></li>
    </ul>
    <button class="cart-add" @click="navBack()"><bieu-tuong loai="cong"/><span>{{ t('dat_banh_7ddb8bc3b','Chọn thêm bánh') }}</span></button>

    <div class="sec"><span class="n">02</span><h3><span>{{ t('dat_banh_73b0921c0','Ngày và giờ nhận') }}</span></h3><i class="rule"></i></div>
    <div class="tomtat" id="c-tomtat" v-if="kho.hienTomTat.value"><div class="tt-doc"><span>{{ t('dat_banh_9e6a654ba','Thời gian nhận') }}</span><b>{{ tomTatLich }}</b></div><button type="button" class="tt-doi" @click="kho.doiLich()">{{ t('dat_banh_2d141c148','Thay đổi') }}</button></div>
    <div id="c-chon" v-else>
      <div class="rail" id="c-days"><button v-for="d in kho.ngayRail.value" :key="d.i" class="day" :class="{on: d.on, best: d.best}" @click="kho.pick(d.i)"><span>{{ d.ten }}</span><b>{{ d.ngay }}</b></button></div>
      <div class="rail" id="c-slots"><button v-for="k in kho.khungRail.value" :key="k.i" class="slot" :class="{on: k.on, off: k.off}" @click="kho.pickSlot(k.i)" :disabled="k.off" :aria-disabled="k.off ? 'true' : null">{{ k.t }}</button></div>
    </div>
    <div class="note" id="c-prep"><dong-chu :phan="kho.ghiChuGio.value"/></div>

    <div class="sec"><span class="n">03</span><h3><span>{{ t('dat_banh_8e8a333b5','Nhận bánh bằng cách nào') }}</span></h3><i class="rule"></i></div>
    <div class="seg">
      <button id="m-ship" :class="{on: S.CO.mode==='ship'}" @click="kho.setMode('ship')"><b><span>{{ t('dat_banh_391958765','Giao tận nơi') }}</span></b><span><span>{{ t('dat_banh_456ce7b1c','Bếp gọi xe giao tới địa chỉ') }}</span></span></button>
      <button id="m-pick" :class="{on: S.CO.mode==='pick'}" :hidden="!S.PICKUPS.length" @click="kho.setMode('pick')"><b><span>{{ t('dat_banh_ba7ce36b2','Tự đến lấy') }}</span></b><span><span>{{ t('dat_banh_61aacce28','Lấy tại một trong hai địa điểm') }}</span></span></button>
    </div>
    <div id="pickList" :style="{display: S.CO.mode==='pick' ? 'block' : 'none', marginTop: '12px'}"><button v-for="x in S.PICKUPS" :key="x.id" class="pick" :class="{on: S.CO.pickupId===x.id}" @click="kho.setPickup(x.id)"><b>{{ x.n }}</b><span>{{ x.a }}</span></button></div>

    <div class="sec"><span class="n">04</span><h3><span>{{ t('dat_banh_bd76ef893','Người đặt') }}</span></h3><i class="rule"></i></div>
    <div class="fld"><label><span>{{ t('dat_banh_58f52301a','Số điện thoại') }}</span></label>
      <input id="f-phone" type="tel" inputmode="numeric" :placeholder="t('dat_banh_639307e29','09xx xxx xxx')" v-model="S.f.phone" @input="kho.lookupPhone()">
      <div class="hint" id="phoneHint"><dong-chu v-if="S.goi.phone" :phan="S.goi.phone"/><template v-else>{{ t('dat_banh_4602d2995','Quý khách có thể nhập địa chỉ mới. Địa chỉ đã lưu chỉ hiện sau khi xác thực thành viên.') }}</template></div>
    </div>
    <div class="two">
      <div class="fld"><label><span>{{ t('dat_banh_3da3c8c27','Họ tên') }}</span></label><input id="f-name" :placeholder="t('dat_banh_5bef63904','Họ và tên người đặt')" v-model="S.f.name"></div>
      <div class="fld"><label><span>{{ t('dat_banh_f2a1fc421','Email (không bắt buộc)') }}</span></label><input id="f-mail" type="email" :placeholder="t('dat_banh_b768618e5','email@...')" v-model="S.f.mail"></div>
    </div>

    <div id="addrBlock" :style="{display: S.CO.mode==='ship' ? 'block' : 'none'}">
      <div class="sec"><span class="n">05</span><h3><span>{{ t('dat_banh_19d05166b','Địa chỉ nhận') }}</span></h3><i class="rule"></i></div>
      <div id="savedAddr"><button v-for="a in kho.diaChiLuu.value" :key="a.i" class="pick" :class="{on: a.on}" @click="kho.selAddr(a.i)"><b>{{ a.dau }}</b><span>{{ a.duoi }}</span></button></div>
      <div class="fld" id="quanBlock" v-show="(S.cauHinh && S.cauHinh.quan || []).length"><label for="f-quan"><span>{{ t('dat_banh_d754706bf','Khu vực giao') }}</span></label>
        <select id="f-quan" :value="S.CO.quan" @change="kho.chonQuan($event.target.value)"><option value="">{{ t('dat_banh_cda7716cd','Chọn khu vực để xem phí giao dự kiến') }}</option><option v-for="q in (S.cauHinh && S.cauHinh.quan) || []" :key="q.ma" :value="q.ma">{{ q.ten }}</option></select>
      </div>
      <div class="fld"><label><span>{{ t('dat_banh_c67579097','Địa chỉ chi tiết') }}</span></label>
        <input id="f-addr" :placeholder="t('dat_banh_dd58bee7e','Gõ số nhà và tên đường, rồi chọn trong danh sách')" autocomplete="off" v-model="S.f.addr" @input="kho.goiYDiaChi()">
        <div id="addrGoiY"><div class="goiy" v-if="S.goiY.length"><div class="lbl">{{ t('dat_banh_3e7887810','Chọn đúng địa chỉ bên dưới') }}</div><button v-for="(g,i) in S.goiY" :key="i" type="button" @click="kho.chonGoiY(i)">{{ g.mo_ta }}</button></div></div>
        <div class="hint" id="shipHint"><dong-chu :phan="S.goi.ship || [thuong(t('dat_banh_e347a8e6c','Chọn khu vực hoặc gõ địa chỉ, hệ thống báo phí giao dự kiến.'))]"/><button v-if="S.goi.phiThuLai" class="cm-nut" @click="kho.quoteShip()">{{ t('thu_phi','Thử lại phí giao') }}</button></div>
      </div>
    </div>

    <div class="sec"><span class="n">06</span><h3><span>{{ t('dat_banh_449171c11','Người nhận') }}</span></h3><i class="rule"></i></div>
    <button class="chk" id="c-other" :class="{on: S.CO.other}" @click="tgl('other')" :aria-expanded="S.CO.other ? 'true' : 'false'" aria-controls="otherBlock"><span class="bx">{{ S.CO.other ? '✓' : '' }}</span>
      <span class="tx"><span>{{ t('dat_banh_f9dae2775','Người khác nhận bánh') }}</span><small><span>{{ t('dat_banh_aec4fcb77','Nhận thay, hoặc gửi tặng') }}</span></small></span></button>
    <div id="otherBlock" :style="{display: S.CO.other ? 'grid' : 'none'}" class="two">
      <div class="fld"><label><span>{{ t('dat_banh_c6a77e80c','Tên người nhận') }}</span></label><input id="f-rname" :placeholder="t('dat_banh_e2b6d704f','Họ và tên người nhận')" v-model="S.f.rname"></div>
      <div class="fld"><label><span>{{ t('dat_banh_d04237d6e','Số điện thoại người nhận') }}</span></label><input id="f-rphone" type="tel" inputmode="numeric" v-model="S.f.rphone"></div>
    </div>
    <button class="chk" id="c-gift" :class="{on: S.CO.gift}" @click="tgl('gift')"><span class="bx">{{ S.CO.gift ? '✓' : '' }}</span>
      <span class="tx"><span>{{ t('dat_banh_6f5611da8','Bánh tặng, không gửi kèm hoá đơn') }}</span><small><span>{{ t('dat_banh_c5e99412b','Bếp sẽ bỏ hoá đơn ra khỏi hộp') }}</span></small></span></button>

    <div class="sec"><span class="n">07</span><h3><span>{{ t('dat_banh_d3f481f07','Ghi chú cho bếp') }}</span></h3><i class="rule"></i></div>
    <div class="fld"><label><span>{{ t('dat_banh_251c930aa','Ghi chú chung cho cả đơn') }}</span></label><textarea id="f-note" :placeholder="t('dat_banh_e2f0d554c','Dị ứng, yêu cầu riêng, hướng dẫn giao...')" v-model="S.f.note"></textarea>
      <div class="hint"><span>{{ t('dat_banh_99aa833e4','Lời chúc in trên cờ cắm bánh thì điền ở trang chọn bánh, mỗi bánh một lời chúc riêng.') }}</span></div>
    </div>

    <div class="sec"><span class="n">08</span><h3><span>{{ t('dat_banh_05ecd1510','Hoá đơn') }}</span></h3><i class="rule"></i></div>
    <button class="chk" id="c-vat" :class="{on: S.CO.vat}" @click="tgl('vat')" :aria-expanded="S.CO.vat ? 'true' : 'false'" aria-controls="vatBlock"><span class="bx">{{ S.CO.vat ? '✓' : '' }}</span>
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

    <div class="sec"><span class="n">09</span><h3><span>{{ t('dat_banh_9d5a6614c','Thanh toán') }}</span></h3><i class="rule"></i></div>
    <div id="payList"><button v-for="x in PAYS" :key="x.k" class="pick" :class="{on: S.CO.pay===x.k}" @click="S.CO.pay=x.k"><b>{{ t(x.kn, x.n) }}</b><span>{{ t(x.kd, x.d) }}</span></button></div>

    <div class="fld"><label><span>{{ t('dat_banh_ma_uu_dai','Mã ưu đãi') }}</span></label>
      <div class="two"><input id="f-ma" autocomplete="off" autocapitalize="characters" maxlength="40" :placeholder="t('dat_banh_ma_uu_dai_goi','Ví dụ SINHNHAT10')" v-model="S.f.ma" @keydown.enter.prevent="kho.apMaUuDai()">
      <button class="pick" id="btnMa" type="button" @click="kho.apMaUuDai()" style="min-height:44px"><b><span>{{ t('dat_banh_ap_ma','Áp dụng') }}</span></b></button></div>
      <div class="hint" id="maHint"><dong-chu :phan="kho.goiYMa.value"/></div>
    </div>

    <div class="sum" id="sum">
      <div class="row" v-for="r in hangTomTat" :key="r.k"><span>{{ r.nhan }}</span><b>{{ r.gia }}</b></div>
      <div class="row"><span>{{ t('gio_hang_nhan_ngay','Nhận ngày') }}</span><b>{{ kho.T.dmy(kho.ngayDangChon.value) }} · {{ kho.gioHopLe.value && S.daChonGio ? kho.slotDangChon.value.t : t('chon_lai_gio','Vui lòng chọn khung giờ còn nhận') }}</b></div>
      <div class="row" v-if="S.CO.mode==='pick'"><span>{{ t('dat_banh_f738100e0','Tự lấy tại') }}</span><b>{{ kho.diemNhanChon.value ? kho.diemNhanChon.value.n : t('dat_banh_chua_chon_diem','Chưa chọn điểm nhận') }}</b></div>
      <div class="row"><span>{{ t('gio_hang_tien_banh','Tiền bánh') }}</span><b>{{ tienTom(kho.tong.value.items) }}</b></div>
      <div class="row" v-if="kho.tong.value.giam > 0"><span>{{ t('dat_banh_dong_uu_dai','Ưu đãi') }}</span><b>- {{ tienTom(kho.tong.value.giam) }}</b></div>
      <div class="row"><span>{{ kho.tong.value.tt.nhan }}</span><b>{{ kho.tong.value.tt.gia_tri }}</b></div>
      <div class="row tot"><span>{{ kho.tong.value.tt.tong_nhan }}</span><b>{{ tienTom(kho.tong.value.total) }}</b></div>
    </div>
    <div class="warn" id="warn">
      <template v-if="S.CO.pay==='card'">{{ t('dat_banh_a3fb251a8','Sau khi xác nhận đơn, chúng tôi sẽ gửi quý khách') }} <b>{{ t('dat_banh_0a8b2618a','link thanh toán OnePay') }}</b> {{ t('dat_banh_96cfeea73','để nhập thẻ.') }}
        <b style="color:var(--cyan)">{{ t('dat_banh_3f1b2677e','Link có hiệu lực 15 phút') }}</b>{{ t('dat_banh_03b6a741d',', quá hạn mà chưa thanh toán thì đơn tự huỷ\\n và bánh được mở lại cho khách khác, hệ thống sẽ nhắn báo quý khách.') }}</template>
      <template v-else>{{ t('dat_banh_a3fb251a8','Sau khi xác nhận đơn, chúng tôi sẽ gửi quý khách') }} <b>{{ t('dat_banh_73816524a','mã VietQR') }}</b> {{ t('dat_banh_d0dc8fa4d','để chuyển khoản.') }}
        <b style="color:var(--cyan)">{{ t('dat_banh_9b84e7f46','Mã có hiệu lực 15 phút') }}</b>{{ t('dat_banh_03b6a741d',', quá hạn mà chưa thanh toán thì đơn tự huỷ\\n và bánh được mở lại cho khách khác, hệ thống sẽ nhắn báo quý khách.') }}</template>
    </div>

    <button class="chk dongy" id="c-dongy" :class="{on: S.CO.dongy}" @click="tgl('dongy')" role="checkbox" :aria-checked="S.CO.dongy ? 'true' : 'false'"><span class="bx">{{ S.CO.dongy ? '✓' : '' }}</span>
      <span class="tx"><span>{{ t('dat_banh_e12f05e93','Tôi đồng ý để The Vagabond Pâtisserie sử dụng họ tên, số điện thoại và địa chỉ để giao bánh và liên hệ về đơn này') }}</span><small><span v-if="baoMat || !S.cauHinh">{{ t('dat_banh_01f52284d','Theo chính sách bảo mật của chúng tôi.') }}</span><span v-else><a href="mailto:hello@thevagabondpatisserie.com?subject=Chinh%20sach%20bao%20mat">{{ t('chinh_sach_ho_tro','Quý khách liên hệ chúng tôi để được cung cấp thông tin bảo mật trước khi gửi.') }}</a></span></small></span></button>
    <p class="doc-cs" id="docChinhSach"><a v-if="baoMat" :href="baoMat.duong" target="_blank" rel="noopener">{{ t('doc_bao_mat','Đọc chính sách bảo mật') }}</a></p>

    <div class="cta">
      <button class="btn" id="btnSend" style="width:100%" v-show="!S.guiXong || S.dangGui" :disabled="S.dangGui" :style="{opacity: S.dangGui ? .55 : 1, pointerEvents: S.dangGui ? 'none' : 'auto'}" @click="guiDon()">{{ S.dangGui ? t('dat_banh_848d6282f','Đang gửi đơn...') : t('dat_banh_df2154067','Gửi yêu cầu đặt bánh') }}</button>
      <div id="sendHint" style="margin-top:12px;font-size:13px;line-height:1.6"><dong-chu v-if="S.goi.gui" :phan="S.goi.gui"/></div>
    </div>
  </div>
</section>

<section class="sheet mua" id="sheetMua" :class="{open: S.trang==='mua'}" role="dialog" aria-modal="true" aria-labelledby="sm-name">
  <template v-if="muaXem">
  <div class="wrap"><div class="hero-img">
    <button class="close" type="button" :aria-label="t('dong_chi_tiet_banh','Đóng chi tiết bánh')" @click="nav('#/in-season')"><svg viewBox="0 0 24 24"><path d="M5 5l14 14M19 5L5 19"/></svg></button>
    <anh-mon id="sm-img" :src="muaXem.m.anh" :lazy="false"/>
  </div></div>
  <div class="wrap">
    <div class="s-head"><h2 id="sm-name">{{ muaXem.ten }}</h2><div id="sm-avail"><div class="avail">{{ muaXem.tinh }}</div></div></div>
    <div class="sec"><span class="n">01</span><h3><span>{{ t('dat_banh_71efef066','Giá') }}</span></h3><i class="rule"></i></div>
    <div id="sm-gia" style="font-size:22px;margin-top:14px"><b style="font-weight:400">{{ tienTom(muaXem.m.gia||0) }}</b></div>
    <div class="fine"><span>{{ t('dat_banh_c02f89b47','Giá đã gồm thuế GTGT. Chưa gồm phí vận chuyển nếu có.') }}</span></div>
    <div id="sm-khoiruot" v-if="muaXem.ruot.length">
      <div class="sec"><span class="n">02</span><h3><span>{{ t('dat_banh_488b179ee','Trong hộp có gì') }}</span></h3><i class="rule"></i></div>
      <div class="mua-ruot" id="sm-ruot"><div v-for="(r,i) in muaXem.ruot" :key="i"><b>{{ r[0] }}</b><span>{{ r[1] }}</span></div></div>
    </div>
    <div class="cta">
      <button class="btn" id="sm-cta" :disabled="!!muaXem.m.het" @click="themTuMua()">{{ muaXem.m.het ? t('dat_banh_a6001ad7a','Hết hàng') : t('dat_banh_b742ca205','Thêm vào giỏ') }}</button>
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
      <div class="avail" v-else-if="chiTiet.tinhTrang==='mua'">{{ chiTiet.nhanMua }}</div>
      <div class="avail" v-else>{{ t('dat_banh_786f9ed52','Đặt trước · bếp làm theo đơn') }}</div></div></div>
    <details class="tuy-chon" id="s-thong-tin" :key="'tt' + chiTiet.c.k">
      <summary><span>{{ t('chi_tiet_huong_vi','Mô tả và hương vị') }}</span><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14M12 5v14"/></svg></summary>
      <div class="desc" id="s-desc">{{ chiTiet.moTa }}</div><div id="s-layers">
        <template v-if="chiTiet.tang"><h3 class="h-sec">{{ t('dat_banh_f84afdac6','Tầng hương') }}<em>{{ t('dat_banh_17a765496','lớp vị') }}</em></h3><div class="layers"><div class="layer" v-for="(l,i) in chiTiet.tang" :key="i"><span class="i">{{ String(i+1).padStart(2,'0') }}</span><div><b>{{ l[0] }}</b><i>{{ l[1] }}</i></div></div></div></template>
        <div v-else class="fine" style="margin-top:20px">{{ t('dat_banh_b96013446','Mô tả và tầng hương lớp vị của món này đang được cập nhật.') }}</div></div>
    </details>

    <div class="sec"><span class="n">01</span><h3><span>{{ t('dat_banh_0e619c4c4','Giá bánh') }}</span></h3><i class="rule"></i></div>
    <div class="sizes" id="s-sizes"><button v-for="z in kichThuocDong" :key="z.s.id" class="size" :class="{on: z.s.id===S.curSizeId}" @click="kho.setSize(z.s.id)"><b>{{ z.gia }}</b><span>{{ z.nhan }}</span><em v-if="z.em">{{ z.em }}</em></button></div>
    <div class="fine"><span>{{ t('dat_banh_c02f89b47','Giá đã gồm thuế GTGT. Chưa gồm phí vận chuyển nếu có.') }}</span></div>

    <div class="chon-so-luong"><span id="s-qty-label">{{ t('so_luong_banh','Số lượng bánh') }}</span><div class="qty"><button type="button" id="s-minus" :disabled="S.soLuong<=1" @click="kho.doiSoLuong(-1)" :aria-label="t('giam_so_luong','Giảm số lượng')"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14"/></svg></button><output id="s-qty" aria-labelledby="s-qty-label" aria-live="polite">{{ S.soLuong }}</output><button type="button" @click="kho.doiSoLuong(1)" :aria-label="t('tang_so_luong','Tăng số lượng')"><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14M12 5v14"/></svg></button></div></div>
    <div class="sec"><span class="n">02</span><h3 id="s-wish-label"><span>{{ t('dat_banh_970e693a8','Lời chúc in trên cờ') }}</span></h3><i class="rule"></i></div>
    <div class="fld"><input id="s-wish" aria-labelledby="s-wish-label" maxlength="60" :placeholder="t('dat_banh_ed04b0946','Happy Birthday...')" v-model="S.wish">
      <div class="hint"><span id="s-wishN">{{ (S.wish||'').length }}</span><span>{{ t('dat_banh_05faf7b4b','/60 ký tự. Nội dung sẽ được in thành cờ, khi vào tiệc thì cắm lên bánh.') }}</span></div>
    </div>

    <details class="tuy-chon" id="s-phu-kien" :key="'pk' + chiTiet.c.k">
      <summary><span>{{ t('phu_kien_cho_banh','Phụ kiện cho bánh') }}</span><svg aria-hidden="true" viewBox="0 0 24 24"><path d="M5 12h14M12 5v14"/></svg></summary>
    <div class="sec"><span class="n">03</span><h3><span>{{ t('dat_banh_2320148b6','Phụ kiện tặng kèm') }}</span></h3><i class="rule"></i></div>
    <ul class="acc" id="s-acc"><li v-for="a in ACC" :key="a.k"><img :src="a.i" alt=""><span class="nm">{{ t(a.k, a.n) }}<small v-if="t(a.ks, a.sub)">{{ t(a.ks, a.sub) }}</small></span></li></ul>
    <h4>{{ t('yeu_cau_dung_cu','Dụng cụ tặng kèm theo yêu cầu') }}</h4><div class="dung-cu"><label><span>{{ t('so_nia','Số nĩa gỗ') }}</span><input id="s-nia" type="number" min="0" max="30" v-model.number="S.nia"></label><label><span>{{ t('so_dia','Số dĩa giấy') }}</span><input id="s-dia" type="number" min="0" max="30" v-model.number="S.dia"></label></div>

    <div class="sec"><span class="n">04</span><h3><span>{{ t('dat_banh_b009ad199','Phụ kiện mua thêm') }}</span></h3><i class="rule"></i></div>
    <div class="addon-lead"><span>{{ t('dat_banh_16c989c4d','Quý khách chọn thêm phụ kiện cần dùng. Chúng tôi sẽ ghi nhận cùng đơn bánh.') }}</span></div>
    <div class="numlab"><span>{{ t('dat_banh_909dfa9ae','Nến số') }}</span> <b><span>{{ t('dat_banh_87aff9ee8','17.000 đ / số') }}</span></b></div>
    <div class="nums" id="s-nums"><button v-for="x in NUMS" :key="x.n" class="numbtn" :class="{on: S.nums.includes(x.n)}" @click="kho.toggleNum(x.n)" :aria-label="t('nen_so','Nến số {so}',{so:x.n})"><img :src="x.img" :alt="t('nen_so','Nến số {so}',{so:x.n})"></button></div>
    <div class="numpick" id="s-numpick">
      <template v-if="S.nums.length"><span>{{ t('dat_banh_21e08aca8','Số trên bánh') }}</span><span class="big">{{ S.nums.join('') }}</span>
        <button class="x" @click="kho.clearNums()"><bieu-tuong loai="bo"/>{{ t('dat_banh_82339c0a8','Xoá') }}</button></template>
      <span v-else style="color:var(--fog-2)">{{ t('dat_banh_16dd7180d','Bấm lần lượt từng số, ví dụ bấm 2 rồi 6 được số 26.') }}</span>
    </div>
    <ul class="addons" id="s-addons"><li v-for="a in ADDONS" :key="a.id"><button :class="{on: S.adds.includes(a.id)}" @click="kho.toggleAdd(a.id)">
      <span class="bx"><bieu-tuong v-if="S.adds.includes(a.id)" loai="chon"/></span>
      <span class="ph"><img :src="a.img" alt=""></span>
      <span class="nm">{{ t(a.k, a.n) }}</span><span class="pr">{{ tienTom(a.p) }}</span></button></li></ul>
    </details>
    <div class="addsum" id="s-addsum" aria-live="polite" :style="{display: kho.phuKienChon.value.length ? 'block' : 'none'}"><template v-if="kho.phuKienChon.value.length">{{ t('dat_banh_fc2a93d57','Đã chọn thêm:') }} <b>{{ kho.phuKienChon.value.map(x=>x.n).join(', ') }}</b> {{ t('dat_banh_b6d0a562d','· cộng thêm') }} <b>{{ tienTom(kho.phuKienChon.value.reduce((a,x)=>a+x.p,0)) }}</b></template></div>

    <div class="cta">
      <button class="btn" id="s-cta" @click="themVaoGio()">{{ S.dongDangSua >= 0 ? t('luu_banh','Lưu thay đổi') : t('dat_banh_34d469c70','Thêm vào giỏ · {gia_tri_a}',{gia_tri_a: tienTom(kho.tienNutThem.value)}) }}</button>
      <a class="tel" :aria-label="t('goi_ho_tro_dat_banh','Gọi hỗ trợ đặt bánh')" :href="'tel:'+telSo()"><svg viewBox="0 0 24 24"><path d="${GOI}"/></svg></a>
    </div>
  </div>
  </template>
</section>
`;
