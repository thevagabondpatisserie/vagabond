/* The Vagabond Patisserie - App nghiep vu (mobile). Built for ERPNext v16 portal. */

(function () {
'use strict';

/* App nghiep vu chi song tren ten mien app.*. Ten mien erp.* danh RIENG
   cho ban desktop (Desk cua ERPNext) - anh Viet chot 10/08/2026. Ai lo mo
   app bang erp.* thi day sang dung ten mien, giu nguyen duong dan va tham
   so de khong mat viec dang lam. */
try {
  var vgbHost = (location.hostname || '').toLowerCase();
  if (vgbHost.indexOf('erp.') === 0) {
    var vgbP = location.pathname || '/';
    /* erp.* vao trang goc thi vao thang ban desktop; con ai da go duong
       dan /bep thi day sang dung ten mien app.*, giu nguyen viec dang lam. */
    location.replace(
      (vgbP === '/' || vgbP === '')
        ? '/app'
        : 'https://' + vgbHost.replace(/^erp\./, 'app.') + vgbP + location.search + location.hash
    );
    return;
  }
} catch (eDom) { }

/* ---------- 1. CSS ---------- */
var CSS = `
.navbar,.web-footer,footer,.footer-logo-extension,#navbar-collapse,.page-header,.breadcrumb-container{display:none!important}
html,body{background:#eef0f5!important;margin:0!important;padding:0!important}
body{-webkit-text-size-adjust:100%;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;color:#16181d}
.page_content,.container,main,section,article,#page-index{padding:0!important;margin:0!important;max-width:none!important;width:auto!important}
#vgb *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
#vgb{position:fixed;inset:0;display:flex;flex-direction:column;background:#eef0f5;overflow:hidden;z-index:9}
.vh{flex:0 0 auto;background:#50DBF2;color:#05323C;padding:calc(env(safe-area-inset-top,0px) + 10px) 8px 12px;display:flex;align-items:center;gap:4px;box-shadow:0 2px 8px rgba(0,0,0,.12)}
.vh b{flex:1;font-size:17px;font-weight:600;text-align:center;line-height:1.25;padding:0 4px}
.vh .ic{width:40px;height:40px;flex:0 0 40px;display:flex;align-items:center;justify-content:center;font-size:22px;border-radius:12px;cursor:pointer;background:transparent;border:0;color:#05323C}
.vh .ic:active{background:rgba(5,50,60,.10)}
.lgw{flex:1;background:#50DBF2;display:flex;align-items:center;justify-content:center;padding:24px 20px;overflow-y:auto}
.lgb{width:100%;max-width:360px;text-align:center}
.lgt{font-size:29px;font-weight:700;color:#05323C;line-height:1.15}
.lgs{font-size:14px;color:#05323C;opacity:.72;margin:4px 0 22px;letter-spacing:4px;text-transform:uppercase}
.lgo{width:78%;max-width:280px;display:block;margin:0 auto 26px;mix-blend-mode:multiply}
.lgc{background:#fff;border-radius:18px;padding:18px 16px 16px;box-shadow:0 10px 30px rgba(5,50,60,.20);text-align:left}
.lgl{font-size:12px;color:#0B7C93;font-weight:600;margin:0 0 6px}
.lgi{width:100%;border:1.5px solid #dfe3ea;border-radius:12px;padding:13px 12px;font-size:16px;outline:0;margin:0 0 14px;background:#fff;color:#16181d}
.lgi:focus{border-color:#0FB5CE;background:#E4F9FD}
.lge{color:#c0392b;font-size:13px;min-height:17px;margin:0 0 8px;line-height:1.35}
.lgf{color:#05323C;opacity:.7;font-size:12.5px;margin-top:18px;line-height:1.5}
.lgfp{text-align:center;font-size:13.5px;color:#0B7C93;font-weight:600;padding:12px 8px 2px;cursor:pointer;user-select:none}
.lgfp:active{color:#05323C}
.vb{flex:1;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:12px 12px 24px}
.vf{flex:0 0 auto;padding:10px 12px calc(env(safe-area-inset-bottom,8px) + 14px);background:#fff;border-top:1px solid #e3e6ee;box-shadow:0 -2px 10px rgba(0,0,0,.05)}
.btn{display:block;width:100%;border:0;border-radius:14px;padding:16px;font-size:17px;font-weight:600;background:#50DBF2;color:#05323C;cursor:pointer}
.btn:active{background:#2FC9E6}
.btn[disabled]{background:#c3c8d4;color:#fff}
.btn.gh{background:#fff;color:#0B7C93;border:1.5px solid #7FE5F6}
.btn.dg{background:#e04b4b}
.btn.gr{background:#12a150}
.row2{display:flex;gap:10px}.row2>*{flex:1}
/* Trinh soan Huong dan che bien (v302). O nhap co NHAN nam tren, vi bep
   truong go tren dien thoai va placeholder bien mat ngay khi go chu dau
   tien, luc do khong con biet o do la o gi nua. */
.hd-form{padding:12px 14px}
.hd-o{display:block;margin-bottom:10px}
.hd-o>span{display:block;font-size:12px;color:#8a8f9c;margin-bottom:4px;font-weight:600}
.hd-o .tin{width:100%;text-align:left;font-size:15px;padding:0 12px}
.hd-o .nt{width:100%;font-size:15px}
.hd-dong{padding:12px 14px;margin-bottom:9px}
.hd-so{font-size:12.5px;font-weight:700;color:#0b6bcb;margin-bottom:9px;display:flex;justify-content:space-between;align-items:center}
.hd-xoa{border:0;background:#fdeaea;color:#b3261e;border-radius:7px;width:28px;height:28px;font-size:15px;cursor:pointer;line-height:1}
.hd-bang{margin-bottom:0}
/* Nut mo Huong dan che bien tren the cong thuc. Doc them o 26-cong-thuc.js */
.ct-hd{border:0;background:#eef7ff;color:#0b6bcb;border-radius:8px;padding:6px 10px;font-size:12.5px;font-weight:600;cursor:pointer;white-space:nowrap;line-height:1}
.ct-hd.chua{background:#fff4e5;color:#8a5a00}
.ct-hd.lech{background:#fdeaea;color:#b3261e}
/* Nut huy mot phieu xuat NVL cua tiec (v303). Do vi no dao nguoc but
   toan da vao so cai, khong phai mot thao tac nhe. */
.tc-huy{border:0;background:#fdeaea;color:#b3261e;border-radius:7px;padding:5px 9px;font-size:12px;font-weight:600;cursor:pointer;margin-top:6px;line-height:1}
/* display:block la CO Y, dung xoa. Bootstrap cua Frappe dat
   .card{display:flex;flex-direction:column} tren TOAN BO trang. Hau qua:
   moi the inline nam truc tiep trong .card (<b>, <i>, <span>) bi trinh
   duyet BLOCKIFY thanh flex item, tuc chiem tron mot dong.

   Do la ly do that cua loi "chu dam bi xuong dong" anh Viet bao ngay
   24/08/2026. Bon quy tac .kq b / .nbs b / .nbc b / .vxr .t b deu KHONG
   dinh gi toi cac man do - di tim o day la di lac.

   Va vi sao khong sua bang ".card > b{display:inline}": khong an. Blockify
   doi gia tri TINH TOAN cua display tren flex item, ghi de moi thu minh
   khai. Phai chan tu goc, tuc dung de .card la flex container nua.

   An toan: ung dung chua bao gio dua vao .card la flex. 17 cho that su
   can flex hay grid deu khai bang inline style, ma inline style thang
   quy tac lop, nen chung khong he suy suyen. Xem them ham kmHangChip trong
   13-khuyen-mai.js: hai phien truoc da gap dung cai bay nay va tung
   nguoi tu boc mot lop div rieng de tranh. Nay chan mot lan cho tat ca. */
.card{display:block;background:#fff;border-radius:16px;margin-bottom:12px;overflow:hidden;box-shadow:0 1px 3px rgba(20,25,40,.07)}
.fld{display:flex;align-items:center;gap:12px;padding:14px 14px;border-bottom:1px solid #f0f2f6;cursor:pointer;background:#fff}
.fld:last-child{border-bottom:0}
.fld:active{background:#f6f8fc}
.fld .fi{width:38px;height:38px;flex:0 0 38px;border-radius:11px;background:#E4F9FD;display:flex;align-items:center;justify-content:center;font-size:19px}
.fld .ft{flex:1;min-width:0}
.fld .fl{font-size:12px;color:#8a8f9c;margin-bottom:3px}
.fld .fv{font-size:16px;font-weight:600;color:#16181d;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fld .fv.ph{color:#b3b8c4;font-weight:400}
.fld .fc{color:#c3c8d4;font-size:20px;flex:0 0 auto}
.hub{display:flex;align-items:center;gap:13px;padding:16px 14px;border-bottom:1px solid #f0f2f6;cursor:pointer;background:#fff;text-decoration:none;color:inherit}
.hub:last-child{border-bottom:0}.hub:active{background:#f6f8fc}
.hub .hi{width:44px;height:44px;flex:0 0 44px;border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:23px;background:#E4F9FD}
.hub .ht{flex:1;min-width:0}
.hub .h1{font-size:16px;font-weight:600;margin-bottom:2px}
.hub .h2{font-size:12.5px;color:#8a8f9c;line-height:1.35}
.bdg{background:#e04b4b;color:#fff;font-size:12px;font-weight:700;min-width:22px;height:22px;border-radius:11px;padding:0 7px;display:flex;align-items:center;justify-content:center}
.bdg.g{background:#12a150}
.chips{display:flex;gap:8px;overflow-x:auto;padding:2px 0 10px;-webkit-overflow-scrolling:touch}
.chips::-webkit-scrollbar{display:none}
.chip{flex:0 0 auto;border:1px solid #dfe3ec;background:#fff;color:#4a5061;border-radius:999px;padding:9px 15px;font-size:14px;white-space:nowrap;cursor:pointer;font-weight:500}
.chip.on{background:#50DBF2;border-color:#50DBF2;color:#05323C}
.srch{display:flex;align-items:center;gap:9px;background:#fff;border-radius:14px;padding:12px 14px;margin-bottom:12px;box-shadow:0 1px 3px rgba(20,25,40,.07)}
.srch input{flex:1;border:0;outline:0;font-size:16px;background:transparent;min-width:0}
.lst{background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 1px 3px rgba(20,25,40,.07)}
.li{display:flex;align-items:center;gap:12px;padding:14px;border-bottom:1px solid #f0f2f6;cursor:pointer}
.li:last-child{border-bottom:0}.li:active{background:#f6f8fc}
.li .lt{flex:1;min-width:0}
.li .l1{font-size:15.5px;font-weight:600;margin-bottom:3px;line-height:1.3}
.li .l2{font-size:12.5px;color:#8a8f9c}
.ck{width:26px;height:26px;flex:0 0 26px;border-radius:8px;border:2px solid #cfd4e0;display:flex;align-items:center;justify-content:center;color:#fff;font-size:15px;font-weight:700}
.ck.on{background:#50DBF2;border-color:#50DBF2;color:#05323C}
.emp{text-align:center;padding:56px 20px;color:#a0a6b4}
.emp .e1{font-size:52px;margin-bottom:12px;opacity:.5}
.emp .e2{font-size:14.5px}
.fab{position:absolute;right:16px;bottom:calc(env(safe-area-inset-bottom,0px) + 18px);width:58px;height:58px;border-radius:29px;background:#50DBF2;color:#05323C;border:0;font-size:32px;line-height:1;box-shadow:0 6px 18px rgba(11,124,147,.45);cursor:pointer;display:flex;align-items:center;justify-content:center}
.sh{position:fixed;inset:0;background:rgba(15,18,28,.45);z-index:99;display:flex;flex-direction:column;justify-content:flex-end}
.shb{background:#fff;border-radius:20px 20px 0 0;max-height:88%;display:flex;flex-direction:column;overflow:hidden}
.shh{padding:14px 16px;border-bottom:1px solid #eef0f5;display:flex;flex-direction:row;align-items:center;gap:10px}
.shh b{flex:1;font-size:16.5px}
.shh .x{font-size:26px;color:#9aa0ae;cursor:pointer;line-height:1;padding:0 4px}
.shl{overflow-y:auto;-webkit-overflow-scrolling:touch;padding-bottom:calc(env(safe-area-inset-bottom,0px) + 8px)}
.shi{padding:15px 16px;border-bottom:1px solid #f4f6fa;font-size:16px;cursor:pointer;display:flex;flex-direction:row;align-items:center;gap:10px}
.shi:active{background:#f6f8fc}
.shi.on{color:#0B7C93;font-weight:600}
.ic1{background:#fff;border-radius:16px;margin-bottom:12px;box-shadow:0 1px 3px rgba(20,25,40,.07);overflow:hidden}
.ic1 .ih{display:flex;align-items:flex-start;gap:10px;padding:13px 12px 11px 14px}
.ic1 .n{width:24px;height:24px;flex:0 0 24px;border-radius:8px;background:#0B7C93;color:#fff;font-size:12.5px;font-weight:700;display:flex;align-items:center;justify-content:center;margin-top:1px}
.ic1 .in{flex:1;min-width:0;font-size:15.5px;font-weight:600;line-height:1.35}
.ic1 .ig{font-size:12px;color:#8a8f9c;margin-top:3px}
.ic1 .im3{width:44px;height:44px;flex:0 0 44px;border-radius:11px;object-fit:cover;background:#E4F9FD}
.ic1 .im3p{display:flex;align-items:center;justify-content:center;font-size:19px;color:#0B7C93}
/* Anh mon dung duoc o moi khung, khong rieng trong the .ic1. Anh Viet
   29/08/2026: danh muc lenh san xuat va ke hoach san xuat phai co anh mon
   di kem ten mon cho de nhan dang. */
.imm{width:40px;height:40px;flex:0 0 40px;border-radius:10px;object-fit:cover;background:#E4F9FD}
.immp{display:flex;align-items:center;justify-content:center;font-size:18px;color:#0B7C93}
.ic1 .del{width:30px;height:30px;flex:0 0 30px;border-radius:50%;background:#fdecec;color:#e0342f;font-size:18px;font-weight:700;line-height:1;display:flex;align-items:center;justify-content:center;cursor:pointer;margin-top:-1px}
.ic1 .del:active{background:#f7cfcf}
.stk{display:flex;background:#f6f8fc;border-top:1px solid #eef1f7;border-bottom:1px solid #eef1f7}
.stk>div{flex:1 1 0;min-width:0;padding:8px;text-align:center;border-right:1px solid #e6eaf3}
.stk>div:last-child{border-right:0}
.stk .s1{font-size:10.5px;color:#8a8f9c;margin-bottom:2px}
.stk .s2{font-size:13.5px;font-weight:600;line-height:1.3;word-break:break-word}
.qw{display:flex;flex-direction:row;align-items:center;gap:10px;padding:12px 14px}
.qw .lb{font-size:12px;color:#8a8f9c;margin-bottom:6px}
.qr{display:flex;gap:9px;align-items:center}
.stp{display:flex;align-items:center;border:1.5px solid #dfe3ec;border-radius:12px;background:#fff;flex:1 1 auto;min-width:0}
.stp button{width:44px;height:50px;border:0;background:#f6f8fc;font-size:24px;line-height:1;color:#0B7C93;cursor:pointer;flex:0 0 44px;padding:0}
.stp button:first-child{border-radius:10px 0 0 10px}
.stp button:last-child{border-radius:0 10px 10px 0}
.stp button:active{background:#DBF6FB}
.stp input{flex:1 1 auto;width:100%;min-width:0;border:0;outline:0;text-align:center;font-size:21px;font-weight:700;height:50px;background:#fff;margin:0;-webkit-appearance:none;appearance:none}
.stp input::-webkit-outer-spin-button,.stp input::-webkit-inner-spin-button{-webkit-appearance:none;margin:0}
.uom{border:1.5px solid #dfe3ec;border-radius:12px;height:53px;padding:0 17px;font-size:15px;font-weight:600;background-color:#fff;background-image:linear-gradient(45deg,transparent 50%,#0B7C93 50%),linear-gradient(135deg,#0B7C93 50%,transparent 50%);background-position:calc(100% - 14px) 25px,calc(100% - 10px) 25px;background-size:4px 4px,4px 4px;background-repeat:no-repeat;flex:0 0 96px;width:96px;color:#16181d;text-align:center;text-align-last:center;-webkit-appearance:none;appearance:none}
.tw{padding:0 14px 12px}
.tw .lb{font-size:12px;color:#8a8f9c;margin-bottom:6px}
.tin{width:100%;border:1.5px solid #dfe3ec;border-radius:12px;height:52px;font-size:20px;font-weight:700;text-align:center;background:#fff;color:#16181d;outline:0;font-family:inherit}
.tin:focus{border-color:#0FB5CE}
.tch{display:flex;gap:7px;overflow-x:auto;padding-top:9px}
.tch::-webkit-scrollbar{display:none}
.tch span{flex:0 0 auto;border:1px solid #dfe3ec;border-radius:9px;padding:8px 13px;font-size:14px;background:#fff;cursor:pointer;font-weight:600;color:#4a5061}
.tch span.on{background:#50DBF2;color:#05323C;border-color:#50DBF2}
.nt{width:100%;border:1.5px solid #dfe3ec;border-radius:12px;padding:12px;font-size:15px;font-family:inherit;outline:0;resize:none;background:#fff}
.nt:focus{border-color:#0FB5CE}
.sec{font-size:12.5px;font-weight:700;color:#8a8f9c;text-transform:uppercase;letter-spacing:.4px;margin:4px 2px 8px}
.kv{display:flex;justify-content:space-between;gap:14px;padding:12px 14px;border-bottom:1px solid #f2f4f8;font-size:15px}
.kv:last-child{border-bottom:0}
.kv b{font-weight:600;text-align:right;flex:1}
.kv span{color:#8a8f9c;flex:0 0 auto}
.tot{display:flex;justify-content:space-between;padding:15px 14px;background:#E4F9FD;font-size:17px;font-weight:700;color:#0B7C93}
.att{display:flex;gap:10px;flex-wrap:wrap;padding:12px 14px}
.att .ph,.att img{width:76px;height:76px;border-radius:12px;object-fit:cover}
.att .ph{border:2px dashed #cfd6e4;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#8a8f9c;font-size:11px;gap:2px;cursor:pointer;background:#fafbfe}
/* O tep dinh kem dung chung. Anh Viet 24/08/2026: *"moi thumbnail cua file
   dinh kem bat buoc phai co mot nut 'X' o goc"*. Truoc do co man phai cham
   vao chinh o anh moi go duoc, khong ai doan ra; co man khong go duoc gi ca
   nen dinh nham mot to la phai huy ca phieu lam lai. */
.otp{position:relative;display:inline-block;flex:0 0 auto}
.otp img,.otp .tt{display:block;border-radius:10px;object-fit:cover;border:1.5px solid #d1d5db;background:#f9fafb}
.otp .tt{display:flex;align-items:center;justify-content:center;color:#6b7280}
.otp .xo{position:absolute;top:-7px;right:-7px;width:22px;height:22px;border-radius:50%;background:#c0392b;color:#fff;border:2px solid #fff;font-size:13px;line-height:1;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 1px 4px rgba(0,0,0,.28);z-index:2;font-weight:700}
.otp .xo:active{background:#8f2a20}
.otp .nh{margin-top:3px;font-size:10.5px;color:#6b7280;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:center}
.amt{font-size:19px;font-weight:700;color:#16181d}
.st{font-size:11.5px;font-weight:700;padding:4px 9px;border-radius:7px;display:inline-block}
.st.w{background:#fff4e0;color:#c07800}.st.b{background:#E4F9FD;color:#0B7C93}
.st.g{background:#e4f7ec;color:#0d8a45}.st.r{background:#fdeaea;color:#c93a3a}
.st.n{background:#eef0f3;color:#6b7280}
.tst{position:fixed;left:50%;transform:translateX(-50%);bottom:96px;background:#23262f;color:#fff;padding:13px 20px;border-radius:12px;font-size:14.5px;z-index:200;max-width:88%;text-align:center;box-shadow:0 6px 20px rgba(0,0,0,.3)}
.ld{position:fixed;inset:0;background:rgba(238,240,245,.75);z-index:150;display:flex;align-items:center;justify-content:center}
.ld i{width:38px;height:38px;border:3.5px solid #cdd5e6;border-top-color:#0FB5CE;border-radius:50%;animation:sp .8s linear infinite;display:block}
.li .im{width:46px;height:46px;flex:0 0 46px;border-radius:11px;object-fit:cover;background:#E4F9FD}

/* ---------- O tick tron cho cac man co chon nhieu dong ----------

   Anh Viet review giao dien 30/08/2026: nut tick cu "nhin rat tho, lech
   truc doc so voi hinh anh va text, dang lam vo layout cua the mon".
   Dung ca ba diem: no von la mot the .chip, tuc mot vien thuoc bo goc deo
   chu ☐, nen cao thap tuy kieu chu cua may va khong bao gio thang hang
   voi anh mon.

   Nay dung <input type=checkbox> THAT roi ghi de appearance. Input that
   thi vung bam dung chuan cua he dieu hanh, trinh doc man hinh doc duoc,
   va khong an theo co chu. flex:0 0 24px de ten mon dai may dong cung
   khong bop meo duoc no.

   Mau khi tich lay #0B7C93 chu KHONG lay #50DBF2 cua thanh tieu de: dau
   tick mau trang tren nen #50DBF2 gan nhu khong doc duoc. #0B7C93 la mau
   dam cua chinh bang mau app, dang dung cho o anh va bieu tuong. */
.tik{appearance:none;-webkit-appearance:none;-moz-appearance:none;
  width:24px;height:24px;flex:0 0 24px;margin:0;border-radius:50%;
  border:2px solid #cbd5e1;background-color:#fff;cursor:pointer;
  transition:background-color .18s ease,border-color .18s ease,transform .12s ease}
.tik:checked{background-color:#0B7C93;border-color:#0B7C93;
  background-image:url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='3.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4.5 12.6l5.2 5.2L19.5 7.2'/%3E%3C/svg%3E");
  background-size:66%;background-position:center;background-repeat:no-repeat}
.tik:active{transform:scale(.92)}

/* O go so nam ngay trong bang bon cot cua man Ke hoach san xuat. */
.khsx-o{width:100%;height:30px;line-height:30px;text-align:center;font-size:14.5px;
  font-weight:600;padding:0 4px;border:1px solid #cfd6e4;border-radius:7px;
  background:#fff;color:#1b2030}
.khsx-o:focus{outline:none;border-color:#0B7C93;box-shadow:0 0 0 2px rgba(11,124,147,.14)}

/* Phan xo ra duoi mot the: nam NGOAI hang flex cua .li de hang do giu
   duoc luat cua he thong thiet ke, khong phai boc them mot lop flex tay
   roi tu dat lai align-items. */
.khsx-the{background:#fff;border-bottom:1px solid #f0f2f6}
.khsx-the .li{border-bottom:0}
.khsx-than{padding:0 14px 12px}

/* Chip NOI cua mot lenh san xuat: phieu YCSX nao, can ngay nao, giao ve
   dau. Anh Viet 30/08/2026: "nhin vao thi khong ro lenh nao voi lenh nao
   la dung cho phieu YCSX, ngay can banh".

   Khong dung .chip san co vi .chip la nut BAM DUOC, cao 38px, nam trong
   hang cuon ngang. Cai o day chi de DOC, nam duoi ten mon, nen nho hon va
   xuong dong duoc. Dat mau nhat de khong tranh mat voi ten mon. */
.noi{display:flex;flex-wrap:wrap;gap:5px;margin-top:5px}
.noi i{font-style:normal;font-size:11.5px;font-weight:600;line-height:1;
  padding:4px 8px;border-radius:999px;background:#eef2f7;color:#4a5061;
  border:1px solid #e2e8f0;max-width:100%;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.noi i.d{background:#fff4e0;color:#9a6200;border-color:#f4e0b8}
.noi i.q{background:#fdeaea;color:#b3261e;border-color:#f5c2c0}

/* The GOP nhieu lenh cung mot mon. Hang cha van la .li nguyen ban, phan
   xo ra nam ngoai hang do y nhu .khsx-the. */
.lgop{background:#fff;border-bottom:1px solid #f0f2f6}
.lgop .li{border-bottom:0}
.lgop .lcon{padding:0 14px 10px}
.lgop .lcon .li{border:1px solid #eef0f4;border-radius:12px;margin-bottom:8px;
  padding:11px 12px;background:#fbfcfe}
.lgop .lcon .li:last-child{margin-bottom:0}
.lsl{flex:0 0 auto;font-size:11.5px;font-weight:700;color:#0B7C93;
  background:#E4F9FD;border-radius:999px;padding:4px 9px;line-height:1}

/* Nut hoan thanh nam ngay tren hang danh sach: bep bam mot phat la ra o
   nhap so, khong phai mo phieu ra roi moi bam. Anh Viet 30/08/2026, mot
   ngay bep nhap 40-50 phieu. */
.lok{flex:0 0 auto;width:40px;height:40px;border-radius:12px;border:0;
  background:#e4f7ec;color:#0d8a45;font-size:19px;cursor:pointer;
  display:flex;align-items:center;justify-content:center}
.lok:active{transform:scale(.93)}
.lok[disabled]{background:#f2f4f7;color:#c3c8d1;cursor:default}
.li .imp{display:flex;align-items:center;justify-content:center;font-size:20px;color:#0B7C93}
.sbtn{flex:0 0 auto;width:38px;height:38px;border-radius:11px;border:0;background:#E4F9FD;color:#0B7C93;font-size:19px;cursor:pointer;display:flex;align-items:center;justify-content:center}
.scan{position:fixed;inset:0;background:#000;z-index:300;display:flex;flex-direction:column}
.scan video{flex:1;width:100%;height:100%;object-fit:cover}
.scw{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:78%;max-width:330px;height:150px;border:3px solid #50DBF2;border-radius:16px;box-shadow:0 0 0 2000px rgba(0,0,0,.45)}
.sct{position:absolute;left:0;right:0;top:calc(50% + 96px);text-align:center;color:#fff;font-size:15px;text-shadow:0 1px 3px #000}
.scx{position:absolute;left:16px;right:16px;bottom:calc(env(safe-area-inset-bottom,0px) + 18px);height:52px;border:0;border-radius:14px;background:#fff;color:#16181d;font-size:16px;font-weight:600;z-index:2}
.scl{position:absolute;left:16px;right:16px;bottom:calc(env(safe-area-inset-bottom,0px) + 84px);text-align:center;color:#fff;font-size:15px;font-weight:600;line-height:1.35;text-shadow:0 1px 3px #000;z-index:2}
.selw{background:#E4F9FD;border:1px solid #7FE5F6;border-radius:13px;padding:10px 12px;margin-bottom:12px}
.selh{font-size:12px;font-weight:700;color:#0B7C93;letter-spacing:.6px;text-transform:uppercase;margin-bottom:8px}
.sell{display:flex;flex-wrap:wrap;gap:6px}
.selc{background:#fff;border:1px solid #7FE5F6;border-radius:999px;padding:6px 9px 6px 11px;font-size:13px;color:#05323C;display:flex;align-items:center;gap:7px;max-width:100%}
.selc span{color:#0B7C93;font-size:17px;font-weight:700;line-height:1}
.kbar{display:flex;gap:8px;padding:10px 14px 2px;overflow-x:auto;-webkit-overflow-scrolling:touch}
.kbar::-webkit-scrollbar{display:none}
.kpg{padding:12px 14px 14px}
.kpt{font-size:12.5px;color:#0B7C93;font-weight:700;margin-bottom:7px}
.kpb{height:9px;border-radius:5px;background:#E4F9FD;overflow:hidden}
.kpb i{display:block;height:100%;background:#0FB5CE;border-radius:5px;transition:width .25s}
.kc{display:flex;align-items:center;gap:12px;padding:13px 14px;border-bottom:1px solid #f0f2f6;background:#fff;cursor:pointer}
.kc:last-child{border-bottom:0}
.kc:active{background:#f6f8fc}
.ktk{width:36px;height:36px;flex:0 0 36px;border-radius:11px;border:2px solid #cfd6e4;color:transparent;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:700;background:#fff}
.kc.on .ktk{background:#12a150;border-color:#12a150;color:#fff}
.kc.on .kn{text-decoration:line-through;color:#9aa0ad}
.kb{flex:1;min-width:0}
.kn{font-size:15.5px;font-weight:600;line-height:1.3}
.kd{font-size:12.5px;color:#8a8f9c;margin-top:4px;line-height:1.5}
.kq{text-align:right;flex:0 0 auto;min-width:52px}
.kq b{font-size:22px;font-weight:800;color:#05323C;display:block;line-height:1}
.kq small{font-size:11.5px;color:#8a8f9c}
.kwn{margin:10px 14px 0;background:#fff4e0;border:1px solid #f0d4a0;border-radius:12px;padding:11px 13px;font-size:13px;color:#8a5a00;line-height:1.45}
.rcvh{background:#E4F9FD;border:1px solid #7FE5F6;border-radius:13px;padding:11px 13px;margin-bottom:12px;font-size:13px;color:#0B7C93;line-height:1.5}
/* So nhan banh dau ngay (v289). Mot dong mot mon: hinh, ten, day o so
   (ton dau + tung dot), va cot tong dang co ben phai. */
.nbs{display:flex;gap:9px;margin:0 14px 12px}
.nbs>div{flex:1;background:#f6f8fc;border:1.5px solid #dfe3ec;border-radius:13px;padding:11px 8px;text-align:center}
.nbs b{display:block;font-size:21px;font-weight:800;color:#05323C;line-height:1.1}
.nbs i{display:block;font-style:normal;font-size:11.5px;color:#8a8f9c;margin-top:3px}
.nbw{margin:0 14px 12px;background:#fff4e0;border:1px solid #f0d4a0;border-radius:12px;padding:11px 13px;font-size:12.5px;color:#8a5a00;line-height:1.5}
.nbw.ok{background:#E4F9FD;border-color:#7FE5F6;color:#0B7C93}
.nbb{margin:0 14px}
.nbr{display:flex;gap:11px;align-items:flex-start;background:#fff;border:1.5px solid #eceff5;border-radius:14px;padding:11px 12px;margin-bottom:9px}
.nbr img{width:42px;height:42px;object-fit:cover;border-radius:10px;flex:none;border:1px solid #e5e7eb}
.nbi{width:42px;height:42px;flex:none;border-radius:10px;background:#f6f8fc;display:flex;align-items:center;justify-content:center;font-size:20px}
.nbt{flex:1;min-width:0}
.nbt .n1{font-size:14.5px;font-weight:600;color:#05323C;line-height:1.35}
.nbt .n2{font-size:11.5px;color:#a0a6b4;margin-top:2px}
.nbl{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.nbd{display:inline-flex;flex-direction:column;align-items:center;background:#f6f8fc;border:1.5px solid #dfe3ec;border-radius:10px;padding:5px 9px;cursor:pointer;min-width:52px}
.nbd.t{background:#E4F9FD;border-color:#7FE5F6}
.nbd i{font-style:normal;font-size:10.5px;color:#8a8f9c;line-height:1}
.nbd b{font-size:16px;font-weight:800;color:#05323C;line-height:1.25;margin-top:2px}
.nbd.t b{color:#0B7C93}
.nbg{display:inline-flex;align-items:center;font-size:11.5px;color:#a0a6b4;background:#fafbfd;border:1px dashed #dfe3ec;border-radius:10px;padding:0 9px;cursor:pointer}
.nbc{flex:0 0 auto;text-align:right;min-width:56px;position:relative}
.nbc b{display:block;font-size:22px;font-weight:800;color:#05323C;line-height:1}
.nbc i{display:block;font-style:normal;font-size:10.5px;color:#8a8f9c;margin-top:3px}
.nbx{display:inline-block;margin-top:7px;font-size:13px;color:#c3c8d4;cursor:pointer;padding:2px 6px}
.uml{flex:0 0 78px;height:50px;border:1.5px solid #dfe3ec;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:600;color:#4a5061;background:#f6f8fc;text-align:center;line-height:1.15;padding:0 4px;word-break:break-word}
.kku{margin-bottom:11px}
.kkuf{font-size:11.5px;color:#8a8f9c;margin-top:4px;padding-left:2px}
.kkuh{font-size:12.5px;color:#0B7C93;background:#E4F9FD;border:1px solid #7FE5F6;border-radius:12px;padding:10px 12px;margin-bottom:13px;line-height:1.5}
.kkut{display:flex;align-items:center;justify-content:space-between;background:#f6f8fc;border:1.5px solid #dfe3ec;border-radius:12px;padding:11px 13px;font-size:14px;font-weight:600;color:#4a5061;margin-top:2px}
.kkut b{font-size:20px;font-weight:800;color:#05323C;margin-left:auto;margin-right:6px}
.kkpk{color:#0B7C93;font-weight:600;cursor:pointer;line-height:1.45}
.kkpk b{color:#05323C;font-weight:800}
.rok{width:32px;height:32px;flex:0 0 32px;border-radius:50%;border:2px solid #cfd6e4;color:transparent;display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:700;background:#fff;cursor:pointer;margin-top:-1px}
.ic1.ok .rok{background:#12a150;border-color:#12a150;color:#fff}
.ic1.ok{box-shadow:0 0 0 2px #12a150}
.ic1.zero .in{color:#9aa0ad;text-decoration:line-through}
.lbw{color:#c07800}.hw{padding:0 14px 12px}.hl{font-size:12px;color:#8a8f9c;margin-bottom:6px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;line-height:1.35}.hbd{font-size:11px;font-weight:700;color:#0B7C93;background:#E4F9FD;border-radius:6px;padding:2px 7px;white-space:nowrap}.hin{display:flex;align-items:center;justify-content:space-between;width:100%;max-width:100%;min-width:0;-webkit-appearance:none;appearance:none;border:1.5px solid #dfe3ec;border-radius:12px;height:48px;padding:0 12px;font-size:16px;font-weight:600;text-align:left;background:#fff;color:#16181d;outline:0;font-family:inherit}.hin::-webkit-date-and-time-value{text-align:left;margin:0;padding:0;min-width:0;flex:1 1 auto}.hin::-webkit-calendar-picker-indicator{opacity:.85;margin:0;padding:0;flex:0 0 auto;cursor:pointer;width:22px;height:22px}input.hin[type="date"]{cursor:pointer;height:48px;min-height:48px;box-sizing:border-box}input.hin[type="date"]:hover{border-color:#0FB5CE}.hin.ed{border-color:#0FB5CE;background:#f4fdff}.hn{font-size:11px;color:#9aa0ad;margin-top:5px;line-height:1.4}.hn.ed{color:#0B7C93;font-weight:600}
.mno{display:inline-block;background:#fff4e0;color:#c07800;font-size:11px;font-weight:700;padding:3px 8px;border-radius:8px}
.mtem{border:1px solid #dfe3ea;border-radius:12px;padding:12px 12px 10px;background:#fff;margin:2px 0 6px}
.mtem .t1{font-size:16px;font-weight:800;color:#05323C;line-height:1.25;margin-bottom:6px}
.mtem .t2{font-size:12px;color:#4a5261;line-height:1.6}
.mtem .bq{display:inline-block;border:1.5px solid #05323C;border-radius:6px;font-size:11px;font-weight:800;color:#05323C;padding:2px 8px;margin-top:7px}
.mtem .bcd{margin-top:9px;text-align:center;font-size:13px;font-weight:700;letter-spacing:2px;color:#05323C;border-top:1px dashed #dfe3ea;padding-top:8px}
@keyframes sp{to{transform:rotate(360deg)}}
.kkl{margin:8px 0 2px;border-radius:10px;padding:8px 11px;font-size:12.5px;font-weight:700;line-height:1.4}
.kkl.up{background:#e4f7ec;color:#0d8a45}
.kkl.dn{background:#fdeaea;color:#c93a3a}
.kkl.eq{background:#eef0f3;color:#6b7280}
.kkq{font-size:12px;color:#8a8f9c;padding:2px 2px 10px;line-height:1.45;text-align:center}
.kkq b{color:#05323C}
.kkcx{display:block;width:100%;background:0;border:0;font-size:12.5px;color:#c93a3a;font-weight:700;padding:10px 0 2px;cursor:pointer}
.kkbig{display:block;width:100%;border:0;border-radius:14px;padding:15px;font-size:17px;font-weight:800;background:#05323C;color:#fff;margin:0 0 12px;cursor:pointer}
.kkbig:active{background:#0B7C93}
`;
var st = document.createElement('style'); st.id = 'vgbcss'; st.textContent = CSS; document.head.appendChild(st);
function keepCss() { if (st.parentNode !== document.head || document.head.lastElementChild !== st) document.head.appendChild(st); }
window.addEventListener('load', keepCss); setTimeout(keepCss, 800); setTimeout(keepCss, 2500);
var mt = document.querySelector('meta[name=viewport]');
if (!mt) { mt = document.createElement('meta'); mt.name = 'viewport'; document.head.appendChild(mt); }
mt.content = 'width=device-width,initial-scale=1,maximum-scale=1,viewport-fit=cover,user-scalable=no';

/* ---------- 2. Helpers ---------- */
var COMPANY = 'CÔNG TY TNHH PATISSERIE VAGABOND';
var root = document.getElementById('vgb');
if (!root) { root = document.createElement('div'); root.id = 'vgb'; document.body.appendChild(root); }

function h(s) { return (s == null ? '' : String(s)).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
var VN = { 'Draft': 'Nháp', 'Pending': 'Chờ xử lý', 'Partially Ordered': 'Xử lý một phần', 'Ordered': 'Đã đặt', 'Received': 'Đã nhận', 'Cancelled': 'Đã huỷ', 'Stopped': 'Đã dừng', 'Issued': 'Đã xuất', 'Transferred': 'Đã chuyển', 'Manufactured': 'Đã sản xuất' };
function vnSt(x) { return VN[x] || x || ''; }
function money(n) { return (Math.round(n || 0)).toLocaleString('vi-VN'); }
function num(n) { var v = Math.round((n || 0) * 1000) / 1000; return v.toLocaleString('vi-VN'); }

/* ---------- So can dong, viet sao cho bep khong doc nham ----------

   num() dung dau phay lam dau thap phan theo loi Viet Nam, nen 242.486
   gram hien ra thanh "242,486". Ngay 29/08/2026 bep doc con so do thanh
   242 nghin gram, tuc 242 ky ca phe nuoc, va bao la may tinh sai. So thi
   dung, chi cach viet la bay.

   Nen o day KHONG bao gio de dau thap phan cho don vi can dong:
     duoi 1000    lam tron so nguyen   -> "242 g"
     tu 1000 tro len  doi sang kg/lit  -> "9,34 kg"
   Don vi dem duoc (Mon, Cai, Chiec) khong doi gi, van dung num().

   DUNG go lai ham nay thanh num(): khong con dau thap phan thi ca so
   "9.336" moi doc duoc dut khoat la chin nghin ba tram, chu khong con
   lan sang chin phay ba. */
/* Khung anh mon. Mon chua co anh thi ve o banh cho khoi lech hang. */
function anhMon(url) {
  return url ? '<img class="imm" src="' + h(url) + '" loading="lazy" alt="">'
    : '<div class="imm immp">🍰</div>';
}

function kl(v, dvt) {
  var d = String(dvt || '').trim().toLowerCase();
  var doi = { 'gram': 'kg', 'g': 'kg', 'gam': 'kg', 'gr': 'kg', 'kilogram': null,
    'ml': 'lít', 'millilitre': 'lít', 'milliliter': 'lít', 'mililit': 'lít' };
  var n = Number(v) || 0;
  if (!(d in doi) || !doi[d]) return num(n) + (dvt ? ' ' + dvt : '');
  if (Math.abs(n) >= 1000) {
    return (Math.round(n / 10) / 100).toLocaleString('vi-VN') + ' ' + doi[d];
  }
  return Math.round(n).toLocaleString('vi-VN') + ' ' + (doi[d] === 'lít' ? 'ml' : 'g');
}

/* ---------- Ô nhập tiền: dấu chấm hàng nghìn khi đang gõ ----------

Anh Việt 20/08/2026: *"khi user gõ số phải tự động có dấu phân cách hàng
nghìn (dấu chấm). Không chỉ làm ở màn này, hãy viết một hàm format dùng
chung để áp dụng cho mọi ô input số tiền trên App."*

Ba điều phải cẩn thận, và điều thứ ba là chỗ nguy nhất:

MỘT. Ô có dấu chấm thì KHÔNG dùng được type="number" nữa: trình duyệt coi
"2.000.000" là chuỗi không hợp lệ và trả về value rỗng. Nên ô tiền chuyển
sang type="text" cộng inputmode="numeric" - bàn phím số vẫn bật lên trên
điện thoại, mà giá trị thì đọc được.

HAI. Không đụng tới ô SỐ LƯỢNG, ô mm căn tem, ô phần trăm. Những ô đó có số
lẻ và có số âm, chấm vào là hỏng. Vì vậy hàm này chỉ áp cho ô nào TỰ KHAI
lớp `tien`, chứ không quét tất cả input số trên trang.

BA. Mọi chỗ ĐỌC ô tiền phải đọc qua `soTien()`. Đọc thẳng bằng Number() thì
"2.000.000" ra NaN, và một ô tiền ra NaN thì phiếu lưu xuống số 0 mà không
báo gì cả. Bộ kiểm có một ca soi đúng chuyện này. */

function soTien(v) {
  /* Nhận cả phần tử DOM lẫn chuỗi. Bỏ mọi thứ không phải chữ số, kể cả
     dấu chấm mình vừa chèn vào, dấu cách, và chữ "đ" người ta gõ thêm. */
  if (v && v.nodeType === 1) v = v.value;
  var s = String(v == null ? '' : v).replace(/[^0-9-]/g, '');
  if (s === '' || s === '-') return 0;
  return Number(s) || 0;
}

function tienChuoi(v) {
  var n = soTien(v);
  return n ? n.toLocaleString('vi-VN') : '';
}

/* Đặt lại giá trị đã chấm, GIỮ NGUYÊN vị trí con trỏ.

   Không giữ con trỏ thì mỗi lần gõ một chữ số con trỏ nhảy về cuối, và
   người ta không sửa được chữ số ở giữa. Cách giữ: đếm xem bên trái con trỏ
   có bao nhiêu CHỮ SỐ, rồi sau khi chấm lại thì đặt con trỏ sau đúng chừng
   ấy chữ số. Đếm chữ số chứ không đếm ký tự, vì số dấu chấm đã đổi. */
function tienGo(el) {
  if (!el) return;
  var cu = el.value || '';
  var vt = el.selectionStart == null ? cu.length : el.selectionStart;
  var soTruoc = (cu.slice(0, vt).match(/[0-9]/g) || []).length;
  var moi = tienChuoi(cu);
  if (moi === cu) return;
  el.value = moi;
  if (el.selectionStart == null) return;
  var dem = 0, i = 0;
  for (; i < moi.length && dem < soTruoc; i++) {
    if (moi[i] >= '0' && moi[i] <= '9') dem++;
  }
  try { el.setSelectionRange(i, i); } catch (e) { }
}

/* Một lần gắn cho cả app. Bắt ở tầng document nên màn nào vẽ ra sau cũng
   được hưởng, không phải nhớ gắn lại sau mỗi lần vẽ lại. */
document.addEventListener('input', function (e) {
  var t = e.target;
  if (!t || !t.getAttribute) return;
  /* Nhận CẢ HAI cách khai. `class="tien"` là cách mới. `data-tien="1"` là
     cách màn Báo giá đã tự làm từ trước; gom vào đây để cả app chỉ còn một
     hành vi duy nhất, thay vì mỗi màn một kiểu chấm. */
  if ((t.classList && t.classList.contains('tien')) || t.getAttribute('data-tien') === '1') {
    tienGo(t);
  }
}, true);
function today() { var d = new Date(); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
function addDays(iso, n) { var d = new Date(iso + 'T00:00:00'); d.setDate(d.getDate() + n); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
/* Input ngay cua trinh duyet hien theo locale may (iOS ra 01 Aug 2026).
   Phu mot lop chu dd/mm/yyyy cua minh len tren, van bam mo lich duoc. */
function dSkin(sc) {
  var ins = (sc || document).querySelectorAll('input[type="date"]');
  for (var i = 0; i < ins.length; i++) (function (inp) {
    if (inp.getAttribute('data-dsk')) return;
    inp.setAttribute('data-dsk', '1');
    var w = document.createElement('div');
    w.className = inp.className;
    w.style.cssText = inp.getAttribute('style') || '';
    w.style.position = 'relative';
    w.style.display = 'flex';
    w.style.alignItems = 'center';
    inp.parentNode.insertBefore(w, inp);
    w.appendChild(inp);
    inp.className = '';
    inp.setAttribute('style', 'position:absolute;left:0;top:0;width:100%;height:100%;opacity:0;margin:0;padding:0;border:0;background:none;cursor:pointer');
    w.style.cursor = 'pointer';
    var ov = document.createElement('span');
    ov.style.cssText = 'pointer-events:none;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis';
    w.appendChild(ov);
    var ic = document.createElement('span');
    ic.textContent = '📅';
    ic.style.cssText = 'pointer-events:none;margin-left:6px;font-size:13px;opacity:.7';
    w.appendChild(ic);
    var ve = function () { ov.textContent = inp.value ? dmy(inp.value) : 'dd/mm/yyyy'; };
    ve();
    inp.addEventListener('input', ve);
    inp.addEventListener('change', ve);
    /* Tren may tinh: o ngay that bi phu opacity 0 nen nut mo lich cua trinh
       duyet (::-webkit-calendar-picker-indicator) an theo, bam vao chi focus
       chu khong mo lich duoc. Bam dau cung mo lich, giong nhu tren dien thoai. */
    w.addEventListener('click', function () {
      if (inp.disabled || inp.readOnly) return;
      try { inp.focus(); } catch (e1) { }
      try { if (inp.showPicker) inp.showPicker(); } catch (e2) { }
    });
  })(ins[i]);
}
function dmy(iso) { if (!iso) return ''; var p = String(iso).slice(0, 10).split('-'); return p[2] + '/' + p[1] + '/' + p[0]; }
function hm(t) { var m = String(t == null ? '' : t).match(/^(\d{1,2}):(\d{2})/); return m ? ('0' + m[1]).slice(-2) + ':' + m[2] : ''; }
function shortWh(w) { return String(w || '').replace(/ - TVD?$/, ''); }

/* ---------- O tep dinh kem dung chung cho MOI man ----------

   Anh Viet 24/08/2026: *"moi thumbnail cua file dinh kem bat buoc phai co
   mot nut 'X' o goc. Khi user click vao, he thong se go bo file do khoi
   phieu (ho tro cho truong hop dinh kem nham)"*.

   Vi sao gom vao mot cho: truoc do moi man tu ve lay mot kieu. Man Hoan
   ung phai cham vao chinh o anh moi go duoc, khong ai doan ra. Man Phieu
   hoan tien va man ban the hien khong go duoc gi ca, dinh nham mot to la
   phai huy ca phieu lam lai. Man Chi tu TK cong ty thi chi hien ten tep
   dang chu, nhin khong biet la to nao.

   o = {
     url    duong dan anh, de trong thi ve o giay
     ten    ten tep, hien duoi o neu nhan = 1
     anh    1 la anh, 0 la tep khac (pdf, doc)
     co     canh o vuong tinh bang px, mac dinh 76
     cho    1 = chua co byte anh, ve o cho
     mo     chuoi thuoc tinh gan vao o de bat su kien bam xem
     go     chuoi thuoc tinh gan vao nut X. DE TRONG THI KHONG CO NUT X,
            dung cho phieu da chot - chi xem chu khong sua duoc.
     nhan   1 = hien ten tep duoi o
     lop    ten lop CSS them vao o, cho man nao can tu tim lai o de nap anh
   }

   Ham chi sinh chuoi HTML, khong tu gan su kien: moi man co cach ve lai
   rieng, ep chung mot co che bat su kien se pha cach lam cua man khac. */
function oTep(o) {
  o = o || {};
  var co = o.co || 76;
  var vien = 'width:' + co + 'px;height:' + co + 'px';
  var ruot;
  if (o.cho) {
    ruot = '<span class="tt" style="' + vien + ';font-size:' + Math.round(co / 4) + 'px">⏳</span>';
  } else if (o.anh && o.url) {
    ruot = '<img src="' + h(o.url) + '" style="' + vien + '">';
  } else {
    ruot = '<span class="tt" style="' + vien + ';font-size:' + Math.round(co / 3.4) + 'px">📄</span>';
  }
  return '<span class="otp' + (o.lop ? ' ' + h(o.lop) : '') + '" style="max-width:' + co + 'px"' +
    (o.mo ? ' ' + o.mo : '') + ' title="' + h(o.ten || '') + '">' +
    ruot +
    (o.go ? '<span class="xo" ' + o.go + ' title="Gỡ tệp này">✕</span>' : '') +
    (o.nhan && o.ten ? '<span class="nh">' + h(o.ten) + '</span>' : '') +
    '</span>';
}

var loadEl = null;
function busy(on) {
  if (on) { if (!loadEl) { loadEl = document.createElement('div'); loadEl.className = 'ld'; loadEl.innerHTML = '<i></i>'; document.body.appendChild(loadEl); } }
  else if (loadEl) { loadEl.remove(); loadEl = null; }
}
function toast(msg, ms) {
  var t = document.createElement('div'); t.className = 'tst'; t.textContent = msg; document.body.appendChild(t);
  setTimeout(function () { t.remove(); }, ms || 2600);
}
var CSRFT = '';
function csrfTok() {
  if (CSRFT) return CSRFT;
  try { if (window.frappe && frappe.csrf_token) return frappe.csrf_token; } catch (e) { }
  return '';
}
var csrfJob = null;
function refreshCsrf() {
  if (csrfJob) return csrfJob;
  csrfJob = (async function () {
    try {
      var r = await fetch(location.pathname + '?nc=' + (new Date()).getTime(), { credentials: 'same-origin', cache: 'no-store', headers: { 'Accept': 'text/html' } });
      var t = await r.text();
      var m = t.match(/csrf_token[^a-zA-Z0-9]{1,8}["']([a-zA-Z0-9]{16,})["']/);
      if (m && m[1]) {
        CSRFT = m[1];
        try { if (window.frappe) frappe.csrf_token = CSRFT; } catch (e) { }
        return 1;
      }
    } catch (e) { }
    return 0;
  })();
  csrfJob.then(function () { setTimeout(function () { csrfJob = null; }, 1500); }, function () { csrfJob = null; });
  return csrfJob;
}
var goneOnce = 0;
function sessionGone() {
  if (goneOnce) return;
  goneOnce = 1;
  setTimeout(function () { try { busy(0); reset(scrLogin); } catch (e) { } }, 60);
}
function srvErr(status, body) {
  var msg = '', exc = '';
  try {
    var j = JSON.parse(body);
    exc = j.exc_type || '';
    if (j._server_messages) { try { msg = JSON.parse(JSON.parse(j._server_messages)[0]).message || ''; } catch (x) { } }
    if (!msg) msg = j.message || j._error_message || '';
  } catch (x) { }
  msg = (msg + '').replace(/<[^>]*>/g, '');
  if (!msg) {
    msg = status === 401 ? 'Phiên đăng nhập đã hết hạn'
      : status === 403 ? 'Không đủ quyền thao tác'
      : status === 417 ? 'Dữ liệu chưa hợp lệ'
      : status === 502 || status === 503 || status === 504 ? 'Máy chủ đang bận, thử lại sau'
      : 'Lỗi máy chủ (mã ' + status + ')';
  }
  var e = new Error(msg.slice(0, 200));
  e.status = status; e.exc_type = exc;
  return e;
}
/* Hạn giờ cho MỌI lời gọi máy chủ (anh Việt báo 18/08/2026).

   Triệu chứng: bấm Đồng bộ Pancake thì màn đứng im ở khung chờ, mãi mãi.
   Đọc bản ghi thì thấy máy chủ chạy xong cả ba lần anh bấm, mà màn vẫn nằm
   ở khung chờ. Nguyên nhân: fetch KHÔNG có hạn giờ mặc định, nên một lần
   mạng chập giữa chừng là lời hứa treo vĩnh viễn, không thành công cũng
   không thất bại - và mọi màn hình chờ nó đều kẹt theo, không có đường ra.

   60 giây: đủ dài cho việc nặng thật như xuất hoá đơn hàng loạt, đủ ngắn
   để người dùng không ngồi nhìn đồng hồ cát không biết chuyện gì. */
var API_HAN_GIO = 60000;

async function rawCall(method, args) {
  var ctl = window.AbortController ? new AbortController() : null;
  var hen = ctl ? setTimeout(function () { try { ctl.abort(); } catch (e) { } }, API_HAN_GIO) : null;
  var r, txt;
  try {
    r = await fetch('/api/method/' + method, {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', 'X-Frappe-CSRF-Token': csrfTok() },
      body: JSON.stringify(args || {}),
      signal: ctl ? ctl.signal : undefined
    });
    /* Đọc thân trả lời cũng nằm trong hạn giờ: máy chủ trả đầu mà nghẽn
       giữa thân thì vẫn là treo. */
    txt = await r.text();
  } catch (ne) {
    if (ctl && ctl.signal.aborted) {
      throw new Error('Máy chủ chưa trả lời sau ' + Math.round(API_HAN_GIO / 1000) +
        ' giây. Kiểm tra mạng rồi bấm lại; vẫn vậy thì báo bộ phận kỹ thuật kiểm tra máy chủ.');
    }
    throw new Error('Mất kết nối mạng, kiểm tra rồi thử lại');
  } finally {
    if (hen) clearTimeout(hen);
  }
  if (!r.ok) throw srvErr(r.status, txt);
  var j = {};
  try { j = JSON.parse(txt); } catch (x) { }
  return j.message;
}
async function api(method, args) {
  try { return await rawCall(method, args); }
  catch (e) {
    if (e && e.exc_type === 'CSRFTokenError') {
      if (await refreshCsrf()) return await rawCall(method, args);
      sessionGone();
      throw new Error('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại');
    }
    if (e && (e.status === 401 || (e.exc_type || '').indexOf('AuthenticationError') >= 0)) sessionGone();
    throw e;
  }
}
function getList(dt, o) { o = o || {}; o.doctype = dt; if (o.limit_page_length === undefined || o.limit_page_length === null) o.limit_page_length = 100; return api('frappe.client.get_list', o); }

/* ---- o tim kiem dung chung (co nut quet ma vach) ---- */
function srchBox(id, ph, val, withScan) {
  return '<div class="srch"><span>&#128269;</span>' +
    '<input id="' + id + '" placeholder="' + h(ph) + '" value="' + h(val || '') + '">' +
    (withScan ? '<button class="sbtn" id="' + id + 'scan" title="Quét mã vạch">&#128247;</button>' : '') +
    '</div>';
}

/* ---- nap thu vien ZXing khi trinh duyet khong co BarcodeDetector ---- */
var zxReady = null;
function loadZX() {
  if (zxReady) return zxReady;
  zxReady = new Promise(function (res, rej) {
    if (window.ZXing) return res(window.ZXing);
    var sc = document.createElement('script');
    sc.src = 'https://cdn.jsdelivr.net/npm/@zxing/library@0.21.3/umd/index.min.js';
    sc.onload = function () { res(window.ZXing); };
    sc.onerror = function () { rej(new Error('Không tải được thư viện quét mã')); };
    document.head.appendChild(sc);
  });
  return zxReady;
}

/* ---- mo camera quet ma vach, tra ve chuoi ma hoac null ---- */
function scanBarcode(onHit) {
  return new Promise(function (resolve) {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      toast('Thiết bị không hỗ trợ camera'); return resolve(null);
    }
    var ov = document.createElement('div'); ov.className = 'scan';
    ov.innerHTML = '<video playsinline muted autoplay></video><div class="scw"></div>' +
      '<div class="sct">Đưa mã vạch vào khung</div>' +
      (onHit ? '<div class="scl"></div>' : '') +
      '<button class="scx">' + (onHit ? 'Xong' : 'Đóng') + '</button>';
    document.body.appendChild(ov);
    var vd = ov.querySelector('video'), stream = null, stop = 0, zxr = null;
    function done(code) {
      if (stop) return; stop = 1;
      try { if (zxr && zxr.reset) zxr.reset(); } catch (e) { }
      try { if (stream) stream.getTracks().forEach(function (t) { t.stop(); }); } catch (e) { }
      ov.remove(); resolve(code || null);
    }
    var hLast = '', hAt = 0, hBusy = 0;
    function hit(code) {
      if (stop || !code) return;
      if (!onHit) return done(code);
      if (hBusy) return;
      var now = (new Date()).getTime();
      if (code === hLast && now - hAt < 2500) return;
      hLast = code; hAt = now; hBusy = 1;
      var gd = setTimeout(function () { hBusy = 0; }, 9000);
      var lb = ov.querySelector('.scl');
      Promise.resolve(onHit(code)).then(function (msg) {
        if (lb) lb.textContent = msg || code;
        try { if (navigator.vibrate) navigator.vibrate(60); } catch (e) { }
      }).catch(function (e) {
        if (lb) lb.textContent = 'Lỗi: ' + String(e && e.message || e);
      }).then(function () { clearTimeout(gd); hBusy = 0; });
    }
    ov.querySelector('.scx').onclick = function () { done(null); };
    navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 } }, audio: false })
      .then(function (st) {
        stream = st; vd.srcObject = st; vd.play();
        if (window.BarcodeDetector) {
          var det = new window.BarcodeDetector({ formats: ['ean_13', 'ean_8', 'code_128', 'code_39', 'upc_a', 'upc_e', 'itf', 'qr_code', 'codabar'] });
          var loop = function () {
            if (stop) return;
            det.detect(vd).then(function (r) {
              if (r && r.length && r[0].rawValue) { hit(String(r[0].rawValue).trim()); if (stop) return; }
              setTimeout(loop, 220);
            }).catch(function () { setTimeout(loop, 350); });
          };
          setTimeout(loop, 500);
        } else {
          loadZX().then(function (ZX) {
            zxr = new ZX.BrowserMultiFormatReader();
            zxr.decodeFromStream(stream, vd, function (r) {
              if (r && !stop) hit(String(r.getText()).trim());
            });
          }).catch(function (e) { toast(String(e.message || e)); done(null); });
        }
      })
      .catch(function () { toast('Không mở được camera - kiểm tra quyền truy cập'); done(null); });
  });
}

/* ---- tra ma vach ra ma hang hoa ---- */
async function itemByBarcode(code) {
  if (!code) return null;
  try {
    var bc = await getList('Item Barcode', { parent: 'Item', fields: ['parent', 'barcode'], filters: { barcode: code, parenttype: 'Item' }, limit_page_length: 5 });
    if (bc && bc.length) return bc[0].parent;
  } catch (e) { }
  try {
    var it = await getList('Item', { fields: ['name'], filters: { name: code, disabled: 0 }, limit_page_length: 1 });
    if (it && it.length) return it[0].name;
  } catch (e) { }
  return null;
}

/* bottom sheet picker */
function sheet(title, items, cur, onPick, searchable) {
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  var hd = '<div class="shh"><b>' + h(title) + '</b><div class="x">&times;</div></div>';
  if (searchable) hd += '<div style="padding:10px 14px 4px;display:flex;gap:8px"><input class="nt" placeholder="Tìm nhanh..." style="height:46px;padding:0 12px;flex:1"><button class="nt" id="shQuet" title="Quét mã vạch" style="height:46px;width:54px;flex:none;font-size:20px;cursor:pointer">&#128247;</button></div>';
  box.innerHTML = hd + '<div class="shl"></div>';
  var lst = box.querySelector('.shl');
  function draw(q) {
    q = (q || '').toLowerCase();
    var f = items.filter(function (it) { return !q || ((it.label || '') + ' ' + (it.tim || '') + ' ' + (it.value || '')).toLowerCase().indexOf(q) >= 0; });
    lst.innerHTML = f.length ? f.map(function (it, i) {
      return '<div class="shi' + (it.value === cur ? ' on' : '') + '" data-i="' + items.indexOf(it) + '">' +
        (it.img ? '<img src="' + it.img + '" style="width:36px;height:36px;object-fit:cover;border-radius:8px;flex:none;border:1px solid #e5e7eb" loading="lazy">' : (it.icon ? '<span>' + it.icon + '</span>' : '')) + '<span style="flex:1;min-width:0">' + h(it.label) + (it.phu ? '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(it.phu) + '</div>' : '') + '</span>' +
        (it.value === cur ? '<span>&#10003;</span>' : '') + '</div>';
    }).join('') : '<div class="emp"><div class="e2">Không tìm thấy</div></div>';
  }
  draw('');
  ov.appendChild(box); document.body.appendChild(ov);
  var inp = box.querySelector('input');
  if (inp) inp.oninput = function () { draw(inp.value); };
  var shQ = box.querySelector('#shQuet');
  if (shQ) shQ.onclick = async function () {
    var code = null;
    try { code = await scanBarcode(); } catch (e) { code = null; }
    if (code && inp) { inp.value = code; draw(code); }
  };
  function close() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) close(); };
  box.querySelector('.x').onclick = close;
  lst.onclick = function (e) {
    var r = e.target.closest('.shi'); if (!r) return;
    close(); onPick(items[+r.dataset.i]);
  };
  return close;
}
function confirmSheet(title, msg, okLabel, danger) {
  return new Promise(function (res) {
    var ov = document.createElement('div'); ov.className = 'sh';
    ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
      '<div style="font-size:17.5px;font-weight:700;margin-bottom:8px">' + h(title) + '</div>' +
      '<div style="font-size:15px;color:#5a6070;line-height:1.5;margin-bottom:18px;white-space:pre-line">' + h(msg) + '</div>' +
      '<button class="btn ' + (danger ? 'dg' : '') + '" data-y>' + h(okLabel || 'Đồng ý') + '</button>' +
      '<button class="btn gh" data-n style="margin-top:9px">Huỷ</button></div>';
    document.body.appendChild(ov);
    ov.onclick = function (e) {
      if (e.target === ov || e.target.hasAttribute('data-n')) { ov.remove(); res(false); }
      if (e.target.hasAttribute('data-y')) { ov.remove(); res(true); }
    };
  });
}
function promptSheet(title, placeholder) {
  return new Promise(function (res) {
    var ov = document.createElement('div'); ov.className = 'sh';
    ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
      '<div style="font-size:17.5px;font-weight:700;margin-bottom:12px">' + h(title) + '</div>' +
      '<textarea class="nt" rows="3" placeholder="' + h(placeholder || '') + '"></textarea>' +
      '<button class="btn" data-y style="margin-top:12px">Xác nhận</button>' +
      '<button class="btn gh" data-n style="margin-top:9px">Huỷ</button></div>';
    document.body.appendChild(ov);
    var ta = ov.querySelector('textarea'); setTimeout(function () { ta.focus(); }, 120);
    ov.onclick = function (e) {
      if (e.target === ov || e.target.hasAttribute('data-n')) { ov.remove(); res(null); }
      if (e.target.hasAttribute('data-y')) { var v = ta.value.trim(); ov.remove(); res(v); }
    };
  });
}


/* ==================== PWA: biểu tượng màn hình chính và thông báo đẩy ====

Anh Việt 20/08/2026: *"Khi user dùng tính năng 'Add to Homescreen', hiện tại
đang mất logo thương hiệu"* và *"Khi có một phiếu mới chuyển sang trạng thái
chờ duyệt của đúng User đó, hệ thống phải bắn notification làm rung điện
thoại"*.

Trang /bep không nằm trong git (nó là một Page trên site), nên không chèn
được thẻ <link rel="manifest"> vào HTML gốc. Thay vào đó chèn từ đây bằng
JavaScript - hiệu lực y hệt, mà mã nguồn vẫn nằm trong git. */

var PWA_MAU = '#50DBF2';   /* nen that cua tep logo 2025, trung .vh cua app */
var PWA_DA_GAN = 0;         /* de bo kiem thu doc duoc rang ham DA CHAY */

function pwaGan() {
  PWA_DA_GAN = 1;
  try {
    if (!document.querySelector('link[rel="manifest"]')) {
      var l = document.createElement('link');
      l.rel = 'manifest';
      l.href = '/manifest.json';
      document.head.appendChild(l);
    }
    /* Màu thanh trạng thái trên điện thoại, cho khớp thanh tiêu đề app. */
    if (!document.querySelector('meta[name="theme-color"]')) {
      var m = document.createElement('meta');
      m.name = 'theme-color';
      m.content = PWA_MAU;
      document.head.appendChild(m);
    }
    /* iOS không đọc manifest cho biểu tượng, nó đọc apple-touch-icon, và nó
       muốn đúng 180x180. Thiếu thẻ này là iPhone tự chụp màn hình trang làm
       biểu tượng, và đó chính là cái "mất logo" anh Việt thấy.

       iOS cũng KHÔNG đọc lại thẻ này sau khi đã thêm ra màn hình chính. Ai
       đã thêm nhầm biểu tượng trắng thì phải xoá đi rồi thêm lại. */
    if (!document.querySelector('link[rel="apple-touch-icon"]')) {
      var a = document.createElement('link');
      a.rel = 'apple-touch-icon';
      a.setAttribute('sizes', '180x180');
      a.href = '/assets/vagabond/pwa/icon-180.png';
      document.head.appendChild(a);
    }
    /* Safari cũ đọc hai thẻ này để mở app không có thanh địa chỉ. */
    if (!document.querySelector('meta[name="apple-mobile-web-app-capable"]')) {
      var c = document.createElement('meta');
      c.name = 'apple-mobile-web-app-capable';
      c.content = 'yes';
      document.head.appendChild(c);
      var t = document.createElement('meta');
      t.name = 'apple-mobile-web-app-title';
      t.content = 'Vagabond';
      document.head.appendChild(t);
    }
    if (navigator.serviceWorker) {
      navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function () { });
    }
  } catch (e) { }
}

/* GỌI NGAY LÚC NẠP TỆP, khong doi __boot.

   Vi sao: ban v242 co du ham pwaGan nhung KHONG CHO NAO GOI no, nen khong
   the manifest nao duoc chen, va anh Viet bao "Logo van chua hien khi them
   vao man hinh chinh". Bo kiem thu luc do chi soi rang trong than ham co
   chu manifest, nen no xanh trong khi tinh nang chet.

   Dat o day chu khong trong __boot vi hai le. Mot, iOS doc the
   apple-touch-icon ngay luc nguoi ta bam Chia se roi Them vao man hinh
   chinh, viec do co the xay ra truoc khi dang nhap xong. Hai, __boot co
   nhanh thoat som (reset(scrLogin)) nen dat trong do la mat luon o man
   dang nhap. */
if (typeof document !== 'undefined' && document.head) pwaGan();

/* Xin quyền thông báo. CỐ Ý không gọi ngay lúc mở app.

   Trình duyệt chỉ cho hỏi MỘT lần: người dùng bấm Chặn là chặn vĩnh viễn,
   muốn mở lại phải vào phần cài đặt của trình duyệt tìm từng mục. Nên chỉ
   hỏi khi người ta đã cài app ra màn hình chính, tức là đã tỏ ý muốn dùng
   lâu dài, đúng như anh Việt dặn. */
function pwaDaCaiRaManHinh() {
  try {
    return window.matchMedia('(display-mode: standalone)').matches ||
      window.navigator.standalone === true;
  } catch (e) { return false; }
}

async function pwaXinQuyenThongBao(batBuocHoi) {
  try {
    if (!('Notification' in window) || !navigator.serviceWorker) return 'khong_ho_tro';
    if (Notification.permission === 'granted') return await pwaDangKyDay();
    if (Notification.permission === 'denied') return 'da_chan';
    if (!batBuocHoi && !pwaDaCaiRaManHinh()) return 'chua_cai';
    var q = await Notification.requestPermission();
    if (q !== 'granted') return 'tu_choi';
    return await pwaDangKyDay();
  } catch (e) { return 'loi'; }
}

async function pwaDangKyDay() {
  try {
    var kh = await api('vagabond.thong_bao.khoa_cong_khai', {});
    if (!kh || !kh.khoa) return 'chua_khai_khoa';
    var reg = await navigator.serviceWorker.ready;
    var dk = await reg.pushManager.getSubscription();
    if (!dk) {
      dk = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: pwaB64(kh.khoa)
      });
    }
    await api('vagabond.thong_bao.dang_ky', { goi: JSON.stringify(dk) });
    return 'xong';
  } catch (e) { return 'loi'; }
}

/* Khoá VAPID gửi xuống dạng base64url, trình duyệt đòi Uint8Array. */
function pwaB64(s) {
  var d = (s + '='.repeat((4 - s.length % 4) % 4)).replace(/-/g, '+').replace(/_/g, '/');
  var raw = atob(d), ra = new Uint8Array(raw.length);
  for (var i = 0; i < raw.length; i++) ra[i] = raw.charCodeAt(i);
  return ra;
}
