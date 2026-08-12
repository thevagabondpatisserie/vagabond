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
.vf{flex:0 0 auto;padding:10px 12px calc(env(safe-area-inset-bottom,0px) + 12px);background:#fff;border-top:1px solid #e3e6ee;box-shadow:0 -2px 10px rgba(0,0,0,.05)}
.btn{display:block;width:100%;border:0;border-radius:14px;padding:16px;font-size:17px;font-weight:600;background:#50DBF2;color:#05323C;cursor:pointer}
.btn:active{background:#2FC9E6}
.btn[disabled]{background:#c3c8d4;color:#fff}
.btn.gh{background:#fff;color:#0B7C93;border:1.5px solid #7FE5F6}
.btn.dg{background:#e04b4b}
.btn.gr{background:#12a150}
.row2{display:flex;gap:10px}.row2>*{flex:1}
.card{background:#fff;border-radius:16px;margin-bottom:12px;overflow:hidden;box-shadow:0 1px 3px rgba(20,25,40,.07)}
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
.amt{font-size:19px;font-weight:700;color:#16181d}
.st{font-size:11.5px;font-weight:700;padding:4px 9px;border-radius:7px;display:inline-block}
.st.w{background:#fff4e0;color:#c07800}.st.b{background:#E4F9FD;color:#0B7C93}
.st.g{background:#e4f7ec;color:#0d8a45}.st.r{background:#fdeaea;color:#c93a3a}
.st.n{background:#eef0f3;color:#6b7280}
.tst{position:fixed;left:50%;transform:translateX(-50%);bottom:96px;background:#23262f;color:#fff;padding:13px 20px;border-radius:12px;font-size:14.5px;z-index:200;max-width:88%;text-align:center;box-shadow:0 6px 20px rgba(0,0,0,.3)}
.ld{position:fixed;inset:0;background:rgba(238,240,245,.75);z-index:150;display:flex;align-items:center;justify-content:center}
.ld i{width:38px;height:38px;border:3.5px solid #cdd5e6;border-top-color:#0FB5CE;border-radius:50%;animation:sp .8s linear infinite;display:block}
.li .im{width:46px;height:46px;flex:0 0 46px;border-radius:11px;object-fit:cover;background:#E4F9FD}
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
async function rawCall(method, args) {
  var r;
  try {
    r = await fetch('/api/method/' + method, {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', 'X-Frappe-CSRF-Token': csrfTok() },
      body: JSON.stringify(args || {})
    });
  } catch (ne) { throw new Error('Mất kết nối mạng, kiểm tra rồi thử lại'); }
  var txt = await r.text();
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

/* ---------- 3. State + router ---------- */
var APPNAME = 'The Vagabond Pâtisserie';
var S = {
  user: frappe.session.user, roles: [], wh: [], groups: [], suppliers: null,
  gtree: {}, gis: {}, gbep: {}, me: { user: frappe.session.user, full_name: '', bo_phan: '' },
  draft: null, stack: [], counts: {}
};
var DEPT_ORDER = ['Pha chế', 'Thu ngân', 'Phục vụ', 'Sales', 'Marketing', 'Bếp Pastry', 'Bếp Baker', 'Tạp vụ', 'Bảo vệ', 'Kế toán', 'Thu mua', 'Kho', 'Vận hành', 'Giám đốc', 'Sonneto Lab'];
var DEPTS = DEPT_ORDER.map(function (x) { return x + ' - TV'; });
function shortDep(x) { return shortWh(x); }
function deptRank(x) { var i = DEPT_ORDER.indexOf(shortDep(x)); return i < 0 ? 99 : i; }
var TYPES = {
  Purchase:  { key: 'Purchase',          icon: '🛒', title: 'Yêu cầu mua hàng',  sub: 'Mua từ nhà cung cấp, nhận về kho', timeLabel: 'Giờ cần hàng',  needFrom: false, needSup: true,  hasTime: false, roots: ['Mua vào'] },
  Transfer:  { key: 'Material Transfer', icon: '🚚', title: 'Yêu cầu điều chuyển nội bộ', sub: 'Xin kho khác soạn hàng chuyển sang', timeLabel: 'Giờ cần hàng',  needFrom: true,  needSup: false, hasTime: false, roots: null },
  Manufacture: { key: 'Manufacture',     icon: '🎂', title: 'Phiếu yêu cầu sản xuất', sub: 'Đặt bếp làm bánh, ghi rõ giờ cần', timeLabel: 'Giờ cần bánh', needFrom: false, needSup: false, hasTime: true, roots: ['Bán ra', 'Sản xuất'] }
};
function typeOf(k) { for (var x in TYPES) if (TYPES[x].key === k) return TYPES[x]; return TYPES.Purchase; }
function curUser() {
  var u = '';
  try { u = (window.frappe && frappe.session && frappe.session.user) || ''; } catch (e) { }
  if (!u || u === 'Guest') { try { u = (window.frappe && frappe.boot && frappe.boot.user && frappe.boot.user.name) || u; } catch (e) { } }
  if (!u || u === 'Guest') u = S.user || '';
  return u;
}
function syncUser() { var u = curUser(); if (u) { S.user = u; S.me.user = u; } return S.user; }

/* Moi man hinh trong app la MOT moc lich su that (vgbD = do sau trong S.stack).
   Nho vay nut Back / vuot lui cua trinh duyet lui dung tung man trong app,
   het canh dang o Chi tiet don ma Back lai vang sang trang /kiem-banh. */
var VGB_LUI_TAY = 0;
function manSoan(f) {
  try { return f === scrStep1 || f === scrStep2 || f === scrStep3 || f === scrStep4; } catch (e) { return false; }
}
function roiPhieuDo(dich) {
  /* Dang dung o man soan phieu, co it nhat mot mon, va dich den KHONG con
     trong luong soan -> roi di la mat ban nhap, phai hoi mot cau. */
  return !!(S.draft && (S.draft.items || []).length) && manSoan(S.stack[S.stack.length - 1]) && !manSoan(dich);
}
function go(fn, replace) {
  if (!replace) {
    S.stack.push(fn);
    try { history.pushState({ vgbD: S.stack.length - 1 }, '', location.href); } catch (e) { }
  } else S.stack[S.stack.length - 1] = fn;
  render();
}
function back() {
  if (S.stack.length <= 1) return;
  var buoc = function () {
    S.stack.pop(); render();
    VGB_LUI_TAY++;
    try { history.back(); } catch (e) { VGB_LUI_TAY--; }
  };
  if (roiPhieuDo(S.stack[S.stack.length - 2])) {
    confirmSheet('Phiếu đang soạn dở', 'Rời màn này thì danh sách món đang chọn sẽ mất.', 'Rời đi, bỏ phiếu nháp', true)
      .then(function (ok) { if (ok) { S.draft = null; buoc(); } });
    return;
  }
  buoc();
}
function reset(fn) {
  S.stack = [fn];
  try { history.replaceState({ vgbD: 0 }, '', location.href); } catch (e) { }
  render();
}
function render() { var f = S.stack[S.stack.length - 1]; if (f) f(); }

/* Man hinh nao cung ve lai bang cach ghi de root.innerHTML, nen moi lan
   bam mot nut la khung cuon moi tinh - nguoi dung bi nem len dau trang.
   Anh Viet bao 09/08/2026 o man tinh tien quay, nhung loi nay co o MOI man.
   Cach chua: truoc khi ghi de thi nho vi tri cuon kem tieu de man hinh cu;
   ghi de xong, neu van dung man do (tieu de khong doi) thi tra vi tri cu ve.
   Doi sang man khac thi tieu de khac nen van bat dau tu dau trang. */
var VGB_TD = '', VGB_CUON = 0;

function frame(title, bodyHtml, opt) {
  opt = opt || {};
  /* Tieu de tab trinh duyet theo man hinh, liec tab biet ngay dang o dau */
  try { document.title = (title && title !== APPNAME) ? title + ' · Vagabond' : APPNAME; } catch (e) { }
  var cuOb = document.getElementById('vgbBody');
  if (cuOb) VGB_CUON = cuOb.scrollTop || 0;
  var giuCuon = !!(cuOb && VGB_TD === title && VGB_CUON > 0);
  VGB_TD = title;
  var showBack = S.stack.length > 1;
  root.innerHTML =
    '<div class="vh">' +
      (showBack ? '<button class="ic" id="vgbBack">&#8249;</button>' : '<span class="ic"></span>') +
      (showBack ? '<button class="ic" id="vgbHome" aria-label="Ve trang chu">&#127968;</button>' : '') +
      '<b>' + h(title) + '</b>' +
      (opt.action ? '<button class="ic" id="vgbAct">' + opt.action + '</button>' : '') +
      (showBack ? (opt.action ? '' : '<span class="ic"></span>') : '<button class="ic" id="vgbAcc" aria-label="Tai khoan">&#128100;</button>') +
    '</div>' +
    '<div class="vb" id="vgbBody">' + bodyHtml + '</div>' +
    (opt.footer ? '<div class="vf">' + opt.footer + '</div>' : '') +
    (opt.fab ? '<button class="fab" id="vgbFab">+</button>' : '');
  var b = document.getElementById('vgbBack'); if (b) b.onclick = back;
  var hb = document.getElementById('vgbHome'); if (hb) hb.onclick = function () {
    if (roiPhieuDo(scrHome)) {
      confirmSheet('Phiếu đang soạn dở', 'Về trang chủ thì danh sách món đang chọn sẽ mất.', 'Về trang chủ, bỏ phiếu nháp', true)
        .then(function (ok) { if (ok) { S.draft = null; reset(scrHome); } });
      return;
    }
    reset(scrHome);
  };
  var ab = document.getElementById('vgbAcc'); if (ab) ab.onclick = function () { go(scrAccount); };
  var a = document.getElementById('vgbAct'); if (a && opt.onAction) a.onclick = opt.onAction;
  var f = document.getElementById('vgbFab'); if (f && opt.onFab) f.onclick = opt.onFab;
  dSkin(root);
  var moiOb = document.getElementById('vgbBody');
  if (giuCuon && moiOb) {
    var dat = VGB_CUON;
    moiOb.scrollTop = dat;
    /* Anh mon, QR... tai xong moi day chieu cao len; dat lai mot nhip nua
       cho chac, nhung chi khi nguoi dung chua tu cuon di cho khac. */
    try {
      requestAnimationFrame(function () {
        if (moiOb.isConnected && moiOb.scrollTop !== dat && moiOb.scrollTop === 0) moiOb.scrollTop = dat;
      });
    } catch (e) { }
  }
  return moiOb;
}

/* ---------- 4. Master data ---------- */
async function loadMasters() {
  if (S.wh.length) return;
  syncUser();
  var _kd = null;
  try { _kd = await api('vagabond.nhan_su.khoi_dong', {}); } catch (e) { _kd = null; }
  var r = (_kd && _kd.kho) ? [
    _kd.kho.map(function (n) { return { name: n }; }),
    _kd.nhom || [],
    (_kd.vai || []).map(function (v) { return { role: v }; })
  ] : await Promise.all([
    getList('Warehouse', { fields: ['name'], filters: { is_group: 0, disabled: 0, company: COMPANY }, limit_page_length: 200, order_by: 'name' }),
    getList('Item Group', { fields: ['name', 'parent_item_group', 'is_group', 'custom_bep_phu_trach'], limit_page_length: 0, order_by: 'name' }),
    getList('Has Role', { parent: 'User', fields: ['role'], filters: { parent: S.user || '__khong_co__', parenttype: 'User' }, limit_page_length: 100 })
  ]);
  S.wh = r[0].map(function (x) { return x.name; });
  S.roles = r[2].map(function (x) { return x.role; });
  S.gtree = {}; S.gis = {}; S.groups = []; S.gbep = {};
  r[1].forEach(function (g) {
    S.gis[g.name] = g.is_group ? 1 : 0;
    if (!g.is_group) S.groups.push(g.name);
    if (g.custom_bep_phu_trach) S.gbep[g.name] = g.custom_bep_phu_trach;
    var p = g.parent_item_group || '';
    if (!S.gtree[p]) S.gtree[p] = [];
    S.gtree[p].push(g.name);
  });
  r[1].forEach(function (g) {
    if (S.gbep[g.name]) return;
    var p = g.parent_item_group, n = 0;
    while (p && n < 8) { if (S.gbep[p]) { S.gbep[g.name] = S.gbep[p]; break; } var f = r[1].filter(function (x) { return x.name === p; })[0]; p = f ? f.parent_item_group : ''; n++; }
  });
  if (S.user) {
    try {
      var u = await api('frappe.client.get_value', { doctype: 'User', filters: { name: S.user }, fieldname: ['name', 'full_name', 'custom_phong_ban', 'custom_bo_phan', 'custom_kho_phu_trach'] });
      if (u && u.name === S.user) { S.me.full_name = u.full_name || ''; S.me.bo_phan = u.custom_phong_ban || u.custom_bo_phan || ''; S.me.khoGiu = String(u.custom_kho_phu_trach || '').split(',').map(function (s2) { return s2.trim(); }).filter(function (s2) { return !!s2; }); }
    } catch (e) { }
  }
  if (!S.me.full_name) { try { S.me.full_name = frappe.session.user_fullname || ''; } catch (e) { } }
  if (!S.me.bo_phan) { try { S.me.bo_phan = localStorage.getItem('vgb_bp_' + S.user) || ''; } catch (e) { } }
  try {
    var dp = await getList('Department', { fields: ['name'], filters: { is_group: 0, disabled: 0 }, limit_page_length: 0 });
    if (dp && dp.length) DEPTS = dp.map(function (x) { return x.name; }).sort(function (a, b2) { return (deptRank(a) - deptRank(b2)) || (a < b2 ? -1 : 1); });
  } catch (e) { }
}

/* tat ca nhom la nam duoi cac nhom goc */
function leavesUnder(roots) {
  if (!roots || !roots.length) return null;
  var out = [];
  function walk(nm) {
    if (S.gis[nm]) { (S.gtree[nm] || []).forEach(walk); }
    else if (out.indexOf(nm) < 0) out.push(nm);
  }
  roots.forEach(walk);
  return out;
}
function hasRole(r) { return S.roles.indexOf(r) >= 0; }

/* Ai duoc xem don mua hang va cong no phai tra: ke toan, thu mua, giam doc.
   Danh sach nay khop voi QUYEN_MUA ben vagabond/mua_hang.py - o day chi de
   an nut cho gon mat, con chan that su thi nam o may chu. */
function coQuyenMua() {
  return hasRole('System Manager') || hasRole('Accounts Manager') || hasRole('Accounts User')
    || hasRole('Purchase Manager') || hasRole('Purchase User') || hasRole('Bộ phận đặt hàng');
}

/* Ai duoc go dau huy mot phieu nhap. Khop voi QUYEN_HUY ben
   vagabond/chung_tu.py - o day chi de an nut, chan that nam o may chu. */
function coQuyenHuy() {
  return hasRole('System Manager') || hasRole('Accounts Manager') || hasRole('Accounts User');
}

/* ---------- Bep: dinh tuyen phieu yeu cau san xuat ---------- */
var BEPS = ['Bếp Pastry', 'Bếp Baker', 'Bếp Lab'];
function myKitchen() {
  var d = shortDep(S.me.bo_phan || '');
  for (var i = 0; i < BEPS.length; i++) if (d.indexOf(BEPS[i]) === 0) return BEPS[i];
  if (d.indexOf('Sonneto Lab') === 0 || d.indexOf('Lab') === 0) return 'Bếp Lab';
  return '';
}
function bepOfItem(it) { return it.bep || S.gbep[it.item_group] || ''; }
function autoKitchen(items) {
  var seen = {}, ks = [];
  (items || []).forEach(function (it) { var k = bepOfItem(it); if (k && !seen[k]) { seen[k] = 1; ks.push(k); } });
  if (!ks.length) return '';
  if (ks.length === 1) return ks[0];
  return 'Cả hai bếp';
}
function bepSeesRow(v) {
  var me = myKitchen();
  if (!me) return true;
  if (!v) return true;
  return v === me || v === 'Cả hai bếp';
}
function whOpts() { return S.wh.map(function (w) { return { value: w, label: shortWh(w) }; }); }

/* ---------- 5. Home ---------- */
async function scrHome() {
  frame(APPNAME, '<div class="emp"><div class="e1">⏳</div></div>');
  await loadMasters();
  var apRoles = hasRole('AP Kiểm soát (FIN)') || hasRole('AP Giám đốc') || hasRole('AP Officer');
  var q = [
    getList('Material Request', { fields: ['name'], filters: { material_request_type: 'Purchase', docstatus: ['<', 2], status: ['in', ['Draft', 'Pending', 'Partially Ordered']] }, limit_page_length: 0 }),
    getList('Material Request', { fields: ['name'], filters: { material_request_type: 'Material Transfer', docstatus: ['<', 2], status: ['in', ['Draft', 'Pending', 'Partially Ordered']] }, limit_page_length: 0 }),
    getList('Material Request', { fields: ['name'], filters: { material_request_type: 'Manufacture', docstatus: ['<', 2], status: ['in', ['Draft', 'Pending', 'Partially Ordered']] }, limit_page_length: 0 })
  ];
  if (apRoles) q.push(getList('Payment Entry', { fields: ['name'], filters: { workflow_state: ['in', myPayStates()] }, limit_page_length: 0 }));
  var c = await Promise.all(q.map(function (p) { return (p && p.catch) ? p.catch(function () { return []; }) : p; }));
  var n = c.map(function (x) { return x.length; });

  function card(icon, t1, t2, cnt, fn, green) {
    return '<div class="hub" data-go="' + fn + '"><div class="hi">' + icon + '</div>' +
      '<div class="ht"><div class="h1">' + h(t1) + '</div><div class="h2">' + h(t2) + '</div></div>' +
      (cnt ? '<span class="bdg' + (green ? ' g' : '') + '">' + cnt + '</span>' : '') +
      '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
  }
  var html = '<div class="sec">Đặt hàng</div><div class="card">' +
    card(TYPES.Purchase.icon, TYPES.Purchase.title, TYPES.Purchase.sub, n[0], 'Purchase') +
    card(TYPES.Transfer.icon, TYPES.Transfer.title, TYPES.Transfer.sub, n[1], 'Transfer') +
    card(TYPES.Manufacture.icon, TYPES.Manufacture.title, TYPES.Manufacture.sub, n[2], 'Manufacture') +
    /* Uyen theo doi don mua hang va cong no nha cung cap ngay tren app,
       khoi mo Desk (anh Viet 12/08/2026). Hai o nay chi hien voi ke toan,
       thu mua va giam doc - gia mua la thong tin nhay cam. */
    (coQuyenMua()
      ? card('🧾', 'Đơn mua hàng', 'Đơn đã gửi nhà cung cấp, hàng về tới đâu', 0, 'PO') +
        card('💸', 'Công nợ phải trả', 'Còn nợ nhà cung cấp nào, khoản nào quá hạn', 0, 'CNPT')
      : '') +
    '</div>';
  if (apRoles) {
    html += '<div class="sec">Duyệt chi</div><div class="card">' +
      card('✍️', 'Duyệt phiếu chi', myPayRoleLabel(), n[3], 'PAY', false) + '</div>';
  }
  if (isBep()) {
    var kcn = 0;
    try {
      var kdd = await getList('Material Request', { fields: ['name', 'trang_thai_bep'], filters: { material_request_type: 'Manufacture', docstatus: 1, schedule_date: ['<=', today()] }, limit_page_length: 0 });
      kcn = kdd.filter(function (x) { return x.trang_thai_bep !== 'Đã xong'; }).length;
    } catch (e) { }
    var wcn = 0;
    try {
      var wdd = await getList('Work Order', { fields: ['name', 'status'], filters: { docstatus: 1 }, limit_page_length: 0 });
      wcn = wdd.filter(function (x) { return WODONE.indexOf(x.status) < 0; }).length;
    } catch (e) { }
    html += '<div class="sec">Bếp</div><div class="card">' +
      card('🧑‍🍳', 'Bảng bếp hôm nay', 'Tổng số bánh cần làm, gộp theo món', kcn, 'KIT') +
      card('🏭', 'Lệnh sản xuất', 'Tạo lệnh, trừ nguyên liệu, in tem', wcn, 'MFG') + '</div>';
  }
  html += '<div class="sec">Bán hàng</div><div class="card">' +
    card('\uD83C\uDF82', 'Kiểm bánh hôm nay', 'Tồn - bếp làm - đã đặt - bán được, đồng bộ Pancake', 0, 'KBD') + '</div>';
  if (isKho()) {
    var rcn = 0;
    try { rcn = (await getList('Purchase Receipt', { fields: ['name'], filters: { docstatus: 0 }, limit_page_length: 0 })).length; } catch (e) { }
    html += '<div class="sec">Kho</div><div class="card">' +
      card('\ud83d\udce5', 'Nhập kho', 'Quét mã phiếu, đếm hàng rồi nhập máy', rcn, 'RCV') + '</div>';
  }
  if (isRnd()) {
    var rdn = 0;
    try { rdn = (await getList('RnD Purchase Request', { fields: ['name'], filters: { trang_thai: ['in', ['Mới tạo', 'Đang xử lý']] }, limit_page_length: 0 })).length; } catch (e) { }
    html += '<div class="sec">Mua hàng test (R&amp;D)</div><div class="card">' +
      card('🧪', 'Yêu cầu mua hàng test', 'Hàng test không tạo mã, không nhập kho', rdn, 'RND') + '</div>';
  }
  var kkn = 0;
  try { kkn = (await getList('Phieu Kiem Ke', { fields: ['name'], filters: { trang_thai: 'Đang kiểm' }, limit_page_length: 0 })).length; } catch (e) { }
  html += '<div class="sec">Kiểm kê</div><div class="card">' +
    card('\ud83d\udccb', 'Kiểm kê kho', 'Quét mã, đếm hàng thực tế trong kho', kkn, 'KK') + '</div>';
  if (isSales()) {
    var dsn = 0;
    try { dsn = (await getList('Sales Invoice', { fields: ['name'], filters: { posting_date: today(), docstatus: 0, custom_pancake_id: ['!=', ''] }, limit_page_length: 0 })).length; } catch (e) { }
    html += '<div class="sec">Bán hàng</div><div class="card">' +
      /* Ba diem ban gio nam chung mot cua: bam vao la chon D1, NVHTN hay
         Sales Online (anh Viet 10/08/2026). Truoc day Sales dung rieng mot
         nut o ngoai nen nhan vien hay vao nham. */
      card('🧾', 'Tính tiền - hoá đơn bán hàng', 'Chọn điểm bán: District 1, NVHTN, Sales Online', dsn, 'POS') +
      card('📑', 'Hợp đồng Event', 'Catering, teabreak, bánh thiết kế theo hợp đồng', 0, 'HDG') +
      card('🔐', 'Mã OTP quản lý', 'Cấp mã cho nhân viên sửa hoặc xoá hoá đơn', 0, 'OTP') +
      card('🎫', 'Chương trình khuyến mãi - combo', 'Bảy cách thức khuyến mãi, combo rã món, mã voucher, báo cáo tiền đã giảm', 0, 'KM') +
      card('📒', 'Công nợ phải thu', 'Khách sỉ gom hoá đơn trả sau: gom phiếu, sinh QR, đối soát', 0, 'CN') +
      card('👥', 'Danh sách khách hàng', 'Tra cứu khách sỉ và lẻ, hạng khách, mức chi tiêu', 0, 'KH') + '</div>';
  }
  if (isSales() || hasRole('Shipper') || hasRole('Accounts User') || hasRole('Purchase User')) {
    html += '<div class="sec">Giao hàng</div><div class="card">'
      + card('🛵', 'Vận đơn', 'Shipper giao bánh, book xe, chi phí xăng xe', 0, 'VD')
      + '</div>';
  }
  if (isSales() || hasRole('Accounts User') || hasRole('Accounts Manager')) {
    /* Phan he Bao cao (anh Viet 12/08/2026): so lieu thoi gian thuc, gop
       ca ba diem ban, xem theo ngay - tuan - thang - quy - nam va xuat
       Excel cho ke toan. Mot cua vao, 12 bao cao ben trong. */
    html += '<div class="sec">Báo cáo</div><div class="card">' +
      card('📈', 'Báo cáo tổng hợp', 'Đang cộng sổ doanh thu hôm nay...', 0, 'BCHUB') +
      card('🛵', 'Doanh thu theo nguồn đơn', 'Tại chỗ, Sales Online, GrabFood, ShopeeFood...', 0, 'BC:BC03') +
      card('💳', 'Phương thức thanh toán', 'Tiền mặt, chuyển khoản, thẻ, ví, công nợ', 0, 'BC:BC04') +
      card('🧾', 'Đối soát hoá đơn điện tử', 'Chờ ký, đã ký, CQT chấp nhận, chưa xuất', 0, 'BC:BC05') +
      card('🍰', 'Món bán chạy', 'Xếp hạng theo số lượng bán ra', 0, 'BC:BC08') +
      card('✂️', 'Sửa và huỷ hoá đơn', 'Ai sửa, ai huỷ, làm gì trên hoá đơn nào', 0, 'BC:BC07') + '</div>';
    html += '<div class="sec">Kế toán</div><div class="card">' +
      card('🧾', 'Hoá đơn bán ra', 'Lọc theo điểm bán và trạng thái hoá đơn điện tử', 0, 'HDBAN') +
      card('🛒', 'Hoá đơn mua vào', 'Lọc theo nhà cung cấp, hạn trả, còn nợ', 0, 'HDMUA') +
      card('🔗', 'Đối chiếu hoá đơn mua', 'Nối hoá đơn nhà cung cấp với phiếu nhập kho rồi ghi sổ một nút', 0, 'DCM') +
      card('📒', 'Công nợ phải thu', 'Khách nào còn nợ mình', 0, 'CN') +
      card('💸', 'Công nợ phải trả', 'Mình còn nợ nhà cung cấp nào', 0, 'CNPT') +
      card('🏛️', 'Đối soát hoá đơn điện tử', 'Chờ ký, đã ký, CQT chấp nhận, chưa xuất', 0, 'BC:BC05') + '</div>';
  }
  html += '<div class="sec">Cài đặt</div><div class="card">' +
    (coQuyenMua() || hasRole('Accounts Manager') || hasRole('System Manager')
      ? card('🏪', 'Điểm bán', 'Chi nhánh, mã quầy, nguồn đơn - khai một nơi dùng cho cả hệ', 0, 'CDDB') +
        card('🔒', 'Khoá sổ', 'Chốt số liệu kỳ cũ, không ai sửa hay huỷ được nữa', 0, 'CDKS') +
        card('💳', 'Phương thức thanh toán', 'Máy cà thẻ, ví, công nợ - và mã gửi cơ quan thuế', 0, 'CDPT') +
        card('🏦', 'Tài khoản nhận tiền', 'Số tài khoản sinh mã QR, khai riêng được cho từng nguồn đơn', 0, 'CDTK') +
        card('🎂', 'Danh mục sản phẩm', 'Mở mã hàng mới trong bảy ô, máy tự đặt mã và cảnh báo trùng tên', 0, 'CDSP') +
        card('🙅', 'Quyền tại quầy', 'Thu ngân được bỏ món tới đâu, khi nào phải xin quản lý', 0, 'CDQQ') +
        card('🎖️', 'Hạng thành viên', 'Ngưỡng lên hạng, giảm giá, tích điểm và xét lại hàng loạt', 0, 'CDHT') +
        card('🌙', 'Cuối ngày: ghi sổ và xuất hoá đơn', 'Bật tắt từng điểm bán, chọn giờ chạy', 0, 'CDCN')
      : '') +
    card('📦', 'Tra tồn kho', 'Xem tồn hiện tại theo kho', 0, 'STOCK') +
    card('👤', 'Tài khoản', 'Thông tin tài khoản và đăng xuất', 0, 'ACC') +
    '</div>' +
    '<div style="text-align:center;color:#a0a6b4;font-size:12px;padding:14px 10px 4px;line-height:1.6">' +
    h(S.me.full_name || S.user) + ' &middot; ' + h(shortDep(S.me.bo_phan) || 'Chưa gắn bộ phận') +
    '<br>' + h(S.user) +
    '<br>Bấm chia sẻ trên trình duyệt rồi chọn "Thêm vào MH chính" để dùng như app</div>';

  var b = frame(APPNAME, html);
  b.onclick = function (e) {
    var r = e.target.closest('[data-go]'); if (!r) return;
    var k = r.dataset.go;
    if (k === 'KBD') { location.href = '/kiem-banh'; return; }
  if (k === 'BTPO') { location.href = '/btp'; return; }
    if (k === 'PAY') return go(scrPayList);
    if (k === 'STOCK') return go(scrStock);
    if (k === 'KIT') return go(scrKitchen);
    if (k === 'MFG') return go(scrMfgList);
    if (k === 'RCV') return go(scrRecvList);
    if (k === 'KK') return go(scrKkList);
    if (k === 'DS') return go(scrDoanhSo);
    if (k === 'POS') return go(scrPosChonQuay);
    if (k === 'HDG') return go(scrHopDong);
    if (k === 'BC3') return go(function () { kmThe = 'bc'; scrKhuyenMai(); });
    if (k === 'KT1') return go(scrDoanhSo);
    if (k === 'BCHUB') return go(scrBaoCao);
    if (k === 'PO') return go(scrDonMua);
    if (k === 'CNPT') return go(scrNoPhaiTra);
    if (k === 'HDBAN') return go(scrHdBan);
    if (k === 'HDMUA') return go(scrHdMua);
    if (k === 'DCM') return go(scrDoiChieuMua);
    if (k && k.indexOf('BC:') === 0) { bcMa = k.slice(3); return go(scrBaoCaoXem); }
    if (k && k.indexOf('BC') === 0) return toast('Báo cáo này chưa dựng. Anh Việt chốt nội dung rồi em điền vào.', 4200);
    if (k && k.indexOf('KT') === 0) return toast('Mục kế toán này chưa dựng. Anh Việt chốt nội dung rồi em điền vào.', 4200);
    if (k === 'OTP') return go(scrOtp);
    if (k === 'KM') return go(scrKhuyenMai);
    if (k === 'CN') return go(scrCongNo);
    if (k === 'KH') return go(scrKhachHang);
    if (k === 'VD') return go(scrVanDon);
    if (k === 'RND') return go(scrRndList);
    if (k === 'CDDB') return go(scrDiemBan);
    if (k === 'CDKS') return go(scrKhoaSo);
    if (k === 'CDPT') return go(scrPtThanhToan);
    if (k === 'CDTK') return go(scrTaiKhoan);
    if (k === 'CDSP') return go(scrDanhMuc);
    if (k === 'CDQQ') return go(scrQuyenQuay);
    if (k === 'CDHT') return go(scrHangKhach);
    if (k === 'CDCN') return go(scrCaiDatCuoiNgay);
    if (k === 'ACC') return go(scrAccount);
    go(function () { scrMRList(TYPES[k]); });
  };
  vgbGomNhom();
  bcSoHomNay();
}

/* Doanh thu hom nay hien thang tren the "Bao cao tong hop" o trang chu, de
   mo app phat la thay so - anh Viet 12/08/2026. Chay SAU khi ve xong man,
   hong thi de nguyen dong chu cu chu khong lam vo trang chu. */
async function bcSoHomNay() {
  var el = document.querySelector('[data-go="BCHUB"] .h2');
  var el2 = document.querySelector('[data-nhom="BC"] .gs');
  if (!el && !el2) return;
  try {
    var kq = await api('vagabond.bao_cao.danh_sach', { ky: 'ngay' });
    var chu = 'Hôm nay ' + money(kq.tong_doanh_thu) + ' đ · ' + money(kq.so_hoa_don) + ' hoá đơn';
    if (el) el.textContent = chu;
    if (el2) el2.textContent = money(kq.tong_doanh_thu) + ' đ hôm nay';
  } catch (e) {
    if (el) el.textContent = 'Doanh thu, nguồn đơn, thanh toán, hoá đơn điện tử';
  }
}

/* ---------- 5b. Nhom nghiep vu: o lon o trang chu, bam vao moi hien o nho ----------

Anh Viet dat ngay 03/08/2026: nghiep vu nhieu qua roi, trang chu cuon dai
khong nhin het. Gom thanh 8 o lon kieu iPOS, bam o lon moi ra danh sach o nho.

Cach lam co y: KHONG dung lai phan dem so cua scrHome. scrHome van dung so
lieu va van dung ham card() cu de dung tung dong; xong roi vgbGomNhom() moi
doc lai cac dong da dung duoc, xep vao nhom rong. Them nghiep vu moi chi can
them key vao VGB_NHOM, khong phai sua cho nao khac.
*/
var VGB_NHOM = [
  { k: 'DH', ten: 'Đặt hàng', icon: '🛒', keys: ['Purchase', 'Transfer', 'RND', 'PAY', 'PO', 'CNPT'] },
  { k: 'SX', ten: 'Sản xuất', icon: '🧑‍🍳', keys: ['Manufacture', 'KIT', 'MFG', 'BTPO'] },
  { k: 'NK', ten: 'Nhập kho', icon: '📥', keys: ['RCV'] },
  { k: 'XK', ten: 'Xuất kho', icon: '📤', keys: ['XKH', 'XKD'] },
  { k: 'KK', ten: 'Kiểm kê', icon: '🧮', keys: ['KK', 'STOCK'] },
  { k: 'BH', ten: 'Bán hàng', icon: '🎂', keys: ['KBD', 'POS', 'HDG', 'OTP', 'KM', 'CN', 'KH'] },
  { k: 'GH', ten: 'Giao hàng', icon: '🚚', keys: ['VD'] },
  { k: 'BC', ten: 'Báo cáo', icon: '📈', keys: ['BCHUB', 'BC:BC03', 'BC:BC04', 'BC:BC05', 'BC:BC08', 'BC:BC07'] },
  { k: 'KT', ten: 'Kế toán', icon: '🧮', keys: ['HDBAN', 'HDMUA', 'DCM', 'CN', 'CNPT', 'BC:BC05'] },
  { k: 'KHAC', ten: 'Cài đặt', icon: '⚙️', keys: ['CDDB', 'CDKS', 'CDPT', 'CDTK', 'CDSP', 'CDQQ', 'CDHT', 'CDCN', 'ACC', 'STOCK'] }
];

var VGB_HUB = {};

function vgbCss() {
  if (document.getElementById('vgbHubCss')) return;
  var st = document.createElement('style');
  st.id = 'vgbHubCss';
  st.textContent =
    '.gwrap{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:12px}' +
    '.gt{position:relative;background:#fff;border-radius:16px;padding:16px 14px 14px;' +
    'box-shadow:0 1px 3px rgba(16,24,40,.08);min-height:104px;display:flex;' +
    'flex-direction:column;justify-content:space-between;cursor:pointer;' +
    '-webkit-tap-highlight-color:transparent}' +
    '.gt:active{transform:scale(.98)}' +
    '.gt .gi{font-size:30px;line-height:1}' +
    '.gt .gn{font-size:17px;font-weight:700;color:#101828}' +
    '.gt .gs{font-size:12px;color:#98a2b3;margin-top:2px}' +
    '.gt .gb{position:absolute;top:12px;right:12px;background:#fee4e2;color:#d92d20;' +
    'font-size:13px;font-weight:700;border-radius:999px;padding:2px 9px}' +
    '.vxf{padding:12px}' +
    '.vxl{font-size:13px;color:#667085;margin:14px 2px 6px;font-weight:600}' +
    '.vxi,.vxs{width:100%;box-sizing:border-box;border:1px solid #d0d5dd;border-radius:10px;' +
    'padding:11px 12px;font-size:16px;background:#fff;color:#101828}' +
    '.vxb{width:100%;box-sizing:border-box;border:0;border-radius:12px;padding:14px;' +
    'font-size:16px;font-weight:700;background:#101828;color:#fff;margin-top:16px}' +
    '.vxb.o{background:#fff;color:#101828;border:1px solid #d0d5dd;margin-top:8px}' +
    '.vxb.r{background:#d92d20;color:#fff}' +
    '.vxb[disabled]{opacity:.45}' +
    '.vxr{display:flex;align-items:center;gap:10px;background:#fff;border-radius:12px;' +
    'padding:10px 12px;margin-bottom:8px;box-shadow:0 1px 2px rgba(16,24,40,.06)}' +
    '.vxr .t{flex:1;min-width:0}' +
    '.vxr .t b{display:block;font-size:15px;color:#101828;font-weight:600;' +
    'white-space:nowrap;overflow:hidden;text-overflow:ellipsis}' +
    '.vxr .t i{font-style:normal;font-size:12px;color:#98a2b3}' +
    '.vxq{width:78px;text-align:right;border:1px solid #d0d5dd;border-radius:8px;' +
    'padding:8px;font-size:15px}' +
    '.vxx{border:0;background:transparent;color:#d92d20;font-size:20px;padding:0 4px}' +
    '.vxtag{display:inline-block;font-size:12px;font-weight:600;border-radius:999px;' +
    'padding:2px 9px}' +
    '.vxtag.c{background:#fef0c7;color:#b54708}' +
    '.vxtag.d{background:#d1fadf;color:#027a48}' +
    '.vxtag.x{background:#fee4e2;color:#912018}' +
    '.vxtag.c2{background:#eceff2;color:#5c6670}' +
    '.vtb{display:flex;gap:8px;padding:12px 12px 2px;overflow-x:auto}' +
    '.vt{flex:0 0 auto;padding:8px 14px;border-radius:20px;background:#fff;border:1px solid #dfe4ea;font-size:14px;font-weight:600;color:#5c6670;cursor:pointer;-webkit-tap-highlight-color:transparent}' +
    '.vt.on{background:#101828;color:#fff;border-color:#101828}' +
    '.vt b{font-weight:700;margin-left:4px}' +
    '.vxg{display:grid;grid-template-columns:1fr 1fr;gap:10px}' +
    '.vxgi{background:#fff;border-radius:12px;padding:10px;box-shadow:0 1px 2px rgba(16,24,40,.06);cursor:pointer}' +
    '.vxgi:active{transform:scale(.97)}' +
    '.vxga{width:100%;height:84px;object-fit:cover;border-radius:8px;display:block}' +
    '.vxga.t{display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:700;color:#475467}' +
    '.vxgn{font-size:13.5px;font-weight:600;color:#101828;margin-top:6px;line-height:1.3;max-height:36px;overflow:hidden}' +
    '.vxgm{font-size:11px;color:#98a2b3;margin-top:2px}' +
    '.vxgt{font-size:12px;font-weight:700;color:#027a48;margin-top:3px}' +
    '.vxgt.r{color:#d92d20}' +
    '.gt.vcl{grid-column:1/-1;min-height:0;flex-direction:row;align-items:center;justify-content:flex-start;gap:12px;padding-right:56px}' +
    '.gt.vcl .gi{font-size:26px}' +
    '.rcvths{display:flex;gap:10px;padding:0 12px 8px;flex-wrap:wrap}' +
    '.rcvth{width:110px;text-decoration:none;color:#475467;font-size:12px;text-align:center}' +
    '.rcvthi{width:110px;height:110px;object-fit:cover;border-radius:10px;border:1px solid #e4e7ec;display:block;background:#fff}' +
    '.rcvthf{width:110px;height:110px;display:flex;align-items:center;justify-content:center;font-size:40px;background:#fff;border:1px solid #e4e7ec;border-radius:10px}' +
    '.rcvth span{display:block;margin-top:4px}';
  document.head.appendChild(st);
}

function vgbSoNhom(nh) {
  var t = 0;
  for (var i = 0; i < nh.keys.length; i++) {
    var o = VGB_HUB[nh.keys[i]];
    if (o && o.cnt) t += o.cnt;
  }
  return t;
}

function vgbGomNhom() {
  vgbCss();
  VGB_HUB = {};
  var body = document.getElementById('vgbBody');
  if (!body) return;
  var rows = body.querySelectorAll('[data-go]');
  for (var i = 0; i < rows.length; i++) {
    var el = rows[i];
    var b = el.querySelector('.bdg');
    var n = b ? parseInt((b.textContent || '').replace(/\D/g, ''), 10) : 0;
    VGB_HUB[el.dataset.go] = { html: el.outerHTML, cnt: n || 0 };
  }

  /* Hai o nho cua Xuat kho - dung o day de khong phai dong vao scrHome. */
  VGB_HUB.XKH = {
    cnt: 0,
    html: vgbODong('XKH', '🗑️', 'Xuất huỷ', 'Hàng hỏng, hết hạn, không đạt')
  };
  VGB_HUB.XKD = {
    cnt: 0,
    html: vgbODong('XKD', '🔁', 'Xuất điều chuyển nội bộ', 'Chuyển hàng sang kho khác')
  };

  var daXep = {};
  for (var a = 0; a < VGB_NHOM.length; a++) {
    for (var c = 0; c < VGB_NHOM[a].keys.length; c++) daXep[VGB_NHOM[a].keys[c]] = 1;
  }
  var khac = VGB_NHOM[VGB_NHOM.length - 1];
  for (var kk in VGB_HUB) {
    if (!daXep[kk] && khac.keys.indexOf(kk) < 0) khac.keys.push(kk);
  }

  var tongViec = 0;
  for (var vk in VGB_HUB) if (VGB_HUB[vk].cnt) tongViec += VGB_HUB[vk].cnt;
  var g = '<div class="gwrap">' +
    '<div class="gt vcl" data-nhom="VCL">' +
    '<div class="gi">📌</div>' +
    '<div><div class="gn">Việc cần làm</div>' +
    '<div class="gs">' + 'Danh sách phiếu đang chờ bạn xử lý' + '</div></div></div>';
  for (var j = 0; j < VGB_NHOM.length; j++) {
    var nh = VGB_NHOM[j];
    var co = 0;
    for (var m = 0; m < nh.keys.length; m++) if (VGB_HUB[nh.keys[m]]) co++;
    if (!co) continue;
    var so = vgbSoNhom(nh);
    g +=
      '<div class="gt" data-nhom="' + nh.k + '">' +
      (so ? '<span class="gb">' + so + '</span>' : '') +
      '<div class="gi">' + nh.icon + '</div>' +
      '<div><div class="gn">' + h(nh.ten) + '</div>' +
      '<div class="gs">' + co + ' nghiệp vụ</div></div></div>';
  }
  g += '</div>';
  body.innerHTML = g;
  body.onclick = function (e) {
    var t = e.target.closest('[data-nhom]');
    if (!t) return;
    var nh = null;
    for (var i = 0; i < VGB_NHOM.length; i++) if (VGB_NHOM[i].k === t.dataset.nhom) nh = VGB_NHOM[i];
    if (t.dataset.nhom === 'VCL') return go(scrVclList);
    if (nh) go(function () { scrNhom(nh); });
  };
}

async function scrVclList() {
  vgbCss();
  frame('Việc cần làm', '<div class="emp"><div class="e1">⏳</div><div class="e2">Đang gom việc của bạn...</div></div>');
  var td = today();
  var giu = khoGiuCuaToi();
  var khoNhan = giu.length ? giu : S.wh;
  var TT = typeOf('Material Transfer');
  var TM = typeOf('Manufacture');
  var R = [], daCo = {};
  function them(o) { R.push(o); }
  function tre(n) { return !!(n && String(n) < td); }
  async function lay(fn) { try { await fn(); } catch (e) { } }

  await lay(async function () {
    var ds = await getList('Purchase Receipt', { fields: ['name', 'supplier_name', 'posting_date'], filters: { docstatus: 0 }, limit_page_length: 60, order_by: 'posting_date asc' });
    (ds || []).forEach(function (x) {
      them({ nhom: 'Phiếu nhập kho chờ đếm hàng', icon: '📥', t: x.name, s: (x.supplier_name || '') + ' · ' + dmy(x.posting_date), chip: 'chờ nhận', mau: '#1a73c7', mo: function () { go(function () { scrRecvDoc(x.name); }); } });
    });
  });

  await lay(async function () {
    var f = { material_request_type: 'Material Transfer', docstatus: 1, status: ['in', ['Pending', 'Partially Ordered']] };
    if (giu.length) f.set_from_warehouse = ['in', giu];
    var ds = await getList('Material Request', { fields: ['name', 'set_from_warehouse', 'set_warehouse', 'schedule_date'], filters: f, limit_page_length: 60, order_by: 'schedule_date asc' });
    (ds || []).forEach(function (x) {
      daCo[x.name] = 1;
      them({ nhom: 'Kho bạn giữ phải soạn hàng', icon: '🧺', t: x.name, s: shortWh(x.set_from_warehouse) + ' → ' + shortWh(x.set_warehouse) + ' · cần ' + dmy(x.schedule_date), chip: tre(x.schedule_date) ? 'trễ hẹn' : 'chờ soạn', mau: tre(x.schedule_date) ? '#c0392b' : '#c77700', mo: function () { go(function () { scrMRView(x.name, TT); }); } });
    });
  });

  await lay(async function () {
    var f = { material_request_type: 'Material Transfer', docstatus: 1, status: ['in', ['Pending', 'Partially Ordered']] };
    if (khoNhan && khoNhan.length) f.set_warehouse = ['in', khoNhan];
    var ds = await getList('Material Request', { fields: ['name', 'set_from_warehouse', 'set_warehouse', 'schedule_date', 'per_ordered'], filters: f, limit_page_length: 60, order_by: 'schedule_date asc' });
    (ds || []).forEach(function (x) {
      if (daCo[x.name]) return;
      if (!((x.per_ordered || 0) > 0)) return;
      daCo[x.name] = 1;
      them({ nhom: 'Hàng đã chuyển, chờ bạn xác nhận nhận', icon: '📦', t: x.name, s: shortWh(x.set_from_warehouse) + ' → ' + shortWh(x.set_warehouse) + ' · cần ' + dmy(x.schedule_date), chip: 'chờ nhận', mau: '#0a8f9e', mo: function () { go(function () { scrMRView(x.name, TT); }); } });
    });
  });

  var bep = shortDep(S.me.bo_phan || '');
  if (bep && bep.indexOf('Bếp') === 0) {
    await lay(async function () {
      var ds = await getList('Material Request', { fields: ['name', 'set_warehouse', 'schedule_date', 'bo_phan_yeu_cau'], filters: { material_request_type: 'Manufacture', docstatus: 1, status: ['in', ['Pending', 'Partially Ordered']], custom_bep_nhan: bep }, limit_page_length: 60, order_by: 'schedule_date asc' });
      (ds || []).forEach(function (x) {
        them({ nhom: 'Bếp bạn phải làm', icon: '🎂', t: x.name, s: (x.bo_phan_yeu_cau || '') + ' · cần ' + dmy(x.schedule_date), chip: tre(x.schedule_date) ? 'trễ hẹn' : 'chờ làm', mau: tre(x.schedule_date) ? '#c0392b' : '#7a4bbf', mo: function () { go(function () { scrMRView(x.name, TM); }); } });
      });
    });
  }

  await lay(async function () {
    var ds = await getList('Stock Entry', { fields: ['name', 'purpose', 'from_warehouse', 'to_warehouse', 'posting_date', 'owner'], filters: { docstatus: 0, purpose: ['in', ['Material Transfer', 'Material Issue']] }, limit_page_length: 60, order_by: 'creation desc' });
    (ds || []).forEach(function (x) {
      var cuaToi = (x.owner === S.user) || (giu.length && giu.indexOf(x.from_warehouse) >= 0);
      if (!cuaToi) return;
      them({ nhom: 'Phiếu xuất nháp chờ ghi sổ', icon: '📤', t: x.name, s: shortWh(x.from_warehouse) + (x.to_warehouse ? ' → ' + shortWh(x.to_warehouse) : '') + ' · ' + dmy(x.posting_date), chip: 'bản nháp', mau: '#8a8f98', mo: function () { go(function () { scrXkView(x.name); }); } });
    });
  });

  if (kkCanPost()) {
    await lay(async function () {
      var ds = await getList('Phieu Kiem Ke', { fields: ['name', 'kho', 'ngay_kiem'], filters: { trang_thai: 'Chờ duyệt' }, limit_page_length: 40, order_by: 'ngay_kiem asc' });
      (ds || []).forEach(function (x) {
        them({ nhom: 'Phiếu kiểm kê chờ bạn chốt sổ', icon: '🧮', t: x.name, s: shortWh(x.kho) + ' · kiểm ' + dmy(x.ngay_kiem), chip: 'chờ chốt', mau: '#c77700', mo: function () { go(scrKkList); } });
      });
    });
  }

  if (hasRole('Purchase User') || hasRole('Stock Manager') || hasRole('System Manager')) {
    await lay(async function () {
      var ds = await getList('Purchase Order', { fields: ['name', 'supplier_name', 'schedule_date', 'trang_thai_pnk'], filters: { docstatus: 1, status: ['not in', ['Closed', 'Completed']], schedule_date: ['<', td] }, limit_page_length: 30, order_by: 'schedule_date asc' });
      (ds || []).forEach(function (x) {
        if ((x.trang_thai_pnk || '') === 'Đã nhập đủ') return;
        them({ nhom: 'Cảnh báo: đơn mua quá hẹn chưa nhập đủ', icon: '⚠️', t: x.name, s: (x.supplier_name || '') + ' · hẹn ' + dmy(x.schedule_date) + ' · ' + (x.trang_thai_pnk || 'Chưa tạo phiếu'), chip: 'quá hẹn', mau: '#c0392b', mo: function () { toast('Đơn ' + x.name + ' cần xử lý trên máy tính.', 4200); } });
      });
    });
  }

  var nhoms = [];
  R.forEach(function (x) { if (nhoms.indexOf(x.nhom) < 0) nhoms.push(x.nhom); });
  var body = '';
  if (!R.length) {
    body = '<div class="emp"><div class="e1">🎉</div><div class="e2">Không có việc nào đang chờ bạn</div></div>';
  } else {
    body = '<div style="padding:14px 14px 0;font-size:13px;color:#8a90a0">Đang chờ bạn xử lý <b>' + R.length + '</b> việc</div>';
    nhoms.forEach(function (n) {
      body += '<div class="sec">' + h(n) + '</div>';
      R.forEach(function (x, i) {
        if (x.nhom !== n) return;
        body += '<div data-v="' + i + '" style="background:#fff;border-radius:16px;margin:8px 12px;padding:13px 15px;display:flex;align-items:center;gap:12px;box-shadow:0 1px 3px rgba(16,24,40,.07)">' +
          '<div style="font-size:22px">' + x.icon + '</div>' +
          '<div style="flex:1;min-width:0"><div style="font-weight:700;font-size:15px">' + h(x.t) + '</div>' +
          '<div style="font-size:12.5px;color:#8a90a0;margin-top:2px">' + h(x.s) + '</div></div>' +
          '<span style="padding:3px 10px;border-radius:11px;font-size:11.5px;font-weight:700;color:#fff;white-space:nowrap;background:' + x.mau + '">' + h(x.chip) + '</span></div>';
      });
    });
  }
  var b = frame('Việc cần làm', body);
  b.onclick = function (e) {
    var el = e.target.closest('[data-v]');
    if (!el) return;
    var x = R[+el.dataset.v];
    if (x && x.mo) x.mo();
  };
}
function vgbODong(k, icon, t1, t2) {
  return '<div class="hub" data-go="' + k + '"><div class="hi">' + icon + '</div>' +
    '<div class="ht"><div class="h1">' + h(t1) + '</div><div class="h2">' + h(t2) + '</div></div>' +
    '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
}

function scrNhom(nh) {
  vgbCss();
  var rows = '';
  for (var i = 0; i < nh.keys.length; i++) {
    var o = VGB_HUB[nh.keys[i]];
    if (o) rows += o.html;
  }
  var body = frame(nh.ten, '<div class="card">' + rows + '</div>');
  root.onclick = null;
  body.onclick = function (e) {
    var r = e.target.closest('[data-go]');
    if (r) vgbGo(r.dataset.go);
  };
}

/* Mot cho duy nhat dinh tuyen tu o nho sang man hinh. */
function vgbGo(k) {
  if (k === 'KBD') { location.href = '/kiem-banh'; return; }
  if (k === 'BTPO') { location.href = '/btp'; return; }
  if (k === 'PAY') return go(scrPayList);
  if (k === 'STOCK') return go(scrStock);
  if (k === 'KIT') return go(scrKitchen);
  if (k === 'MFG') return go(scrMfgList);
  if (k === 'RCV') return go(scrRecvList);
  if (k === 'KK') return go(scrKkList);
  if (k === 'DS') return go(scrDoanhSo);
  if (k === 'POS') return go(scrPosChonQuay);
  if (k === 'HDG') return go(scrHopDong);
  if (k === 'BC3') return go(function () { kmThe = 'bc'; scrKhuyenMai(); });
  if (k === 'KT1') return go(scrDoanhSo);
  if (k === 'BCHUB') return go(scrBaoCao);
  if (k === 'PO') return go(scrDonMua);
  if (k === 'CNPT') return go(scrNoPhaiTra);
  if (k === 'HDBAN') return go(scrHdBan);
  if (k === 'HDMUA') return go(scrHdMua);
  if (k === 'DCM') return go(scrDoiChieuMua);
  if (k && k.indexOf('BC:') === 0) { bcMa = k.slice(3); return go(scrBaoCaoXem); }
  if (k && k.indexOf('BC') === 0) return toast('Báo cáo này chưa dựng. Anh Việt chốt nội dung rồi em điền vào.', 4200);
  if (k && k.indexOf('KT') === 0) return toast('Mục kế toán này chưa dựng. Anh Việt chốt nội dung rồi em điền vào.', 4200);
  if (k === 'OTP') return go(scrOtp);
  if (k === 'KM') return go(scrKhuyenMai);
  if (k === 'CN') return go(scrCongNo);
    if (k === 'KH') return go(scrKhachHang);
  if (k === 'VD') return go(scrVanDon);
  if (k === 'RND') return go(scrRndList);
  if (k === 'CDDB') return go(scrDiemBan);
  if (k === 'CDKS') return go(scrKhoaSo);
  if (k === 'CDPT') return go(scrPtThanhToan);
  if (k === 'CDTK') return go(scrTaiKhoan);
  if (k === 'CDSP') return go(scrDanhMuc);
  if (k === 'CDQQ') return go(scrQuyenQuay);
  if (k === 'CDHT') return go(scrHangKhach);
  if (k === 'CDCN') return go(scrCaiDatCuoiNgay);
  if (k === 'ACC') return go(scrAccount);
  if (k === 'XKH') return go(scrXkHuyList);
  if (k === 'XKD') return go(scrXkCkList);
  go(function () { scrMRList(TYPES[k]); });
}

/* ---------- 5c. Xuat kho: xuat huy va xuat dieu chuyen noi bo ----------

Hai luat khac nhau, co y:
- Xuat huy: nhan vien luu ban nhap, quan ly kho bam Ghi so thi ton moi tru.
- Dieu chuyen: ghi so ngay, vi hang chi doi kho chu khong mat di.
*/
var XK = { boot: null, gio: [], kho: '', khoNhan: '', lyDo: '', ghiChu: '', anh: '', yc: '' };

async function xkBoot() {
  if (!XK.boot) XK.boot = await api('vagabond.xuat_kho.khoi_dong');
  return XK.boot;
}

function vxSo(n) {
  n = Number(n || 0);
  var s = (Math.round(n * 1000) / 1000).toString();
  var p = s.split('.');
  p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return p.join(',');
}

function vxKhoOpt(ds, chon) {
  var s = '<option value="">-- chọn kho --</option>';
  for (var i = 0; i < ds.length; i++) {
    s += '<option value="' + h(ds[i].name) + '"' + (ds[i].name === chon ? ' selected' : '') + '>' +
      h(ds[i].warehouse_name || ds[i].name) + '</option>';
  }
  return s;
}

function khoGiuCuaToi() { return (S.me && S.me.khoGiu) ? S.me.khoGiu : []; }
function laKhoCuaToi(k) { var g0 = khoGiuCuaToi(); return !!(k && g0.length && g0.indexOf(k) >= 0); }
function vxKhoXuatOpt(ds, chon) {
  var g0 = khoGiuCuaToi();
  if (g0.length) {
    var loc = (ds || []).filter(function (x) { return g0.indexOf(x.name) >= 0; });
    if (loc.length) ds = loc;
  }
  return vxKhoOpt(ds, chon);
}
try {
  window.vgbLapPhieuChuyen = function (khoXuat, khoNhan) {
    XK.gio = []; XK.ghiChu = ''; XK.yc = '';
    XK.kho = khoXuat || ''; XK.khoNhan = khoNhan || '';
    go(scrXkCkNew);
  };
} catch (eW) { }

function vxDongHtml() {
  if (!XK.gio.length) {
    return '<div style="text-align:center;color:#98a2b3;padding:22px 0;font-size:14px">' +
      'Chưa có món nào. Bấm <b>Thêm hàng</b> ở dưới.</div>';
  }
  var s = '';
  for (var i = 0; i < XK.gio.length; i++) {
    var d = XK.gio[i];
    s += '<div class="vxr"><div class="t"><b>' + h(d.ten || d.ma) + '</b>' +
      '<i>' + h(d.ma) + ' · tồn ' + vxSo(d.ton) + ' ' + h(d.dvt || '') + '</i></div>' +
      '<input class="vxq" type="number" inputmode="decimal" min="0" step="any" ' +
      'value="' + d.sl + '" data-sl="' + i + '">' +
      '<button class="vxx" data-bo="' + i + '">&times;</button></div>';
  }
  return s;
}

function vxNoiDong(body) {
  var o = body.querySelector('#vxDong');
  if (o) o.innerHTML = vxDongHtml();
  vxNoiSuKien(body);
}

function vxNoiSuKien(body) {
  var qs = body.querySelectorAll('[data-sl]');
  for (var i = 0; i < qs.length; i++) {
    qs[i].onchange = function () {
      XK.gio[+this.dataset.sl].sl = Number(this.value || 0);
    };
  }
  var bs = body.querySelectorAll('[data-bo]');
  for (var j = 0; j < bs.length; j++) {
    bs[j].onclick = function () {
      XK.gio.splice(+this.dataset.bo, 1);
      vxNoiDong(body);
    };
  }
}

/* Man chon hang: chi liet ke ma CON TON trong kho da chon. */
function scrXkChonHang(kho, quayVe) {
  vgbCss();
  var body = frame('Thêm hàng', '<div class="vxf">' +
    srchBox('vxQ', 'Gõ tên hoặc mã hàng rồi Enter', '', true) +
    '<div id="vxKq" style="margin-top:12px"></div></div>');
  var q = body.querySelector('#vxQ');
  var kq = body.querySelector('#vxKq');
  var ds = [];

  function themMon(x) {
    for (var m = 0; m < XK.gio.length; m++) {
      if (XK.gio[m].ma === x.ma) { toast('Món này đã có trong phiếu.'); return; }
    }
    XK.gio.push({ ma: x.ma, ten: x.ten, dvt: x.dvt, ton: x.ton, sl: 1 });
    toast('Đã thêm ' + (x.ten || x.ma));
    back();
  }

  async function tim() {
    kq.innerHTML = '<div style="text-align:center;color:#98a2b3;padding:18px">Đang tìm...</div>';
    ds = (await api('vagabond.xuat_kho.tim_hang', { kho: kho, tu_khoa: q.value || '' })) || [];
    if (!ds.length) {
      kq.innerHTML = '<div style="text-align:center;color:#98a2b3;padding:18px;font-size:14px">' +
        'Kho này không còn tồn mã nào khớp.</div>';
      return;
    }
    var anh = {};
    try {
      var its = await getList('Item', { fields: ['name', 'image'], filters: { name: ['in', ds.map(function (x) { return x.ma; })] }, limit_page_length: 0 });
      its.forEach(function (x) { if (x.image) anh[x.name] = x.image; });
    } catch (e) { }
    var MAU = ['#e0f2fe', '#fce7f3', '#ecfdf3', '#fef0c7', '#ede9fe', '#fee4e2'];
    var s = '<div class="vxg">';
    for (var i = 0; i < ds.length; i++) {
      var x = ds[i];
      var a = anh[x.ma] ?
        '<img class="vxga" src="' + h(anh[x.ma]) + '" loading="lazy">' :
        '<div class="vxga t" style="background:' + MAU[i % MAU.length] + '">' + h((x.ten || x.ma).charAt(0).toUpperCase()) + '</div>';
      s += '<div class="vxgi" data-th="' + i + '">' + a +
        '<div class="vxgn">' + h(x.ten || x.ma) + '</div>' +
        '<div class="vxgm">' + h(x.ma) + '</div>' +
        '<div class="vxgt' + (x.ton > 0 ? '' : ' r') + '">Tồn ' + vxSo(x.ton) + ' ' + h(x.dvt || '') + '</div></div>';
    }
    kq.innerHTML = s + '</div>';
    var rs = kq.querySelectorAll('[data-th]');
    for (var j = 0; j < rs.length; j++) {
      rs[j].onclick = function () { themMon(ds[+this.dataset.th]); };
    }
  }

  async function quet() {
    var code = await scanBarcode(null);
    if (!code) return;
    var ic = await itemByBarcode(String(code).trim());
    if (!ic) { toast('Chưa nhận ra mã ' + code); return; }
    for (var i = 0; i < ds.length; i++) if (ds[i].ma === ic) return themMon(ds[i]);
    var them = (await api('vagabond.xuat_kho.tim_hang', { kho: kho, tu_khoa: ic })) || [];
    for (var j = 0; j < them.length; j++) if (them[j].ma === ic) return themMon(them[j]);
    toast(ic + ' không còn tồn trong kho này');
  }

  q.onkeydown = function (e) { if (e.key === 'Enter') tim(); };
  var sb = body.querySelector('#vxQscan');
  if (sb) sb.onclick = quet;
  tim();
}

/* Tab dung chung cho cac danh sach xuat kho */
function vxTabsHtml(TB, cur, dem) {
  return '<div class="vtb">' + TB.map(function (t) {
    return '<div class="vt' + (cur === t.k ? ' on' : '') + '" data-tb="' + t.k + '">' +
      h(t.ten) + (dem[t.k] ? ' <b>' + dem[t.k] + '</b>' : '') + '</div>';
  }).join('') + '</div>';
}
async function vxDsHuy(loai) {
  var moc = new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10);
  var ds = [];
  try {
    ds = await getList('Stock Entry', {
      fields: ['name', 'posting_date', 'from_warehouse', 'to_warehouse'],
      filters: { docstatus: 2, purpose: loai === 'huy' ? 'Material Issue' : 'Material Transfer', posting_date: ['>=', moc] },
      limit_page_length: 40, order_by: 'modified desc'
    });
  } catch (e) { }
  return ds.map(function (x) {
    return { name: x.name, posting_date: x.posting_date, from_warehouse: shortWh(x.from_warehouse) || '',
      to_warehouse: shortWh(x.to_warehouse) || '', so_dong: 0, nguoi_tao: '', docstatus: 2, trang_thai: 'Đã huỷ' };
  });
}
function vxTheRow(d, tag) {
  var meta = [d.posting_date, d.so_dong ? d.so_dong + ' món' : '', d.nguoi_tao].filter(Boolean).join(' · ');
  return '<div class="vxr" data-xem="' + h(d.name) + '"><div class="t">' +
    '<b>' + h(d.tieu_de || d.name) + '</b>' +
    '<i>' + h(meta) + '</i></div>' + tag + '</div>';
}



/* ----- Xuat huy ----- */
async function scrXkHuyList() {
  vgbCss();
  frame('Xuất huỷ', '<div class="emp"><div class="e1">⏳</div></div>');
  await xkBoot();
  var ds = [];
  try { ds = (await api('vagabond.xuat_kho.ds_phieu', { loai: 'huy', gioi_han: 40 })) || []; } catch (e) { }
  var D = {
    cho: ds.filter(function (x) { return x.docstatus === 0; }),
    xong: ds.filter(function (x) { return x.docstatus === 1; }),
    huy: await vxDsHuy('huy')
  };
  if (!XK.tabH) XK.tabH = 'cho';
  var dem = { cho: D.cho.length, xong: D.xong.length, huy: D.huy.length };
  var TB = [{ k: 'cho', ten: 'Chờ ghi sổ' }, { k: 'xong', ten: 'Đã ghi sổ' }, { k: 'huy', ten: 'Đã huỷ' }];
  var TAG = { cho: ['c', 'Chờ ghi sổ'], xong: ['d', 'Đã ghi sổ'], huy: ['x', 'Đã huỷ'] };

  function listHtml() {
    var ls = D[XK.tabH] || [];
    if (!ls.length) {
      return '<div style="text-align:center;color:#98a2b3;padding:40px 20px;font-size:14px">' +
        (XK.tabH === 'cho' ? 'Không có phiếu nào chờ ghi sổ.<br>Bấm nút + để lập phiếu.' :
          XK.tabH === 'xong' ? 'Chưa có phiếu huỷ nào đã ghi sổ.' : 'Không có phiếu bị huỷ trong 30 ngày qua.') + '</div>';
    }
    var c = TAG[XK.tabH], s = '';
    for (var i = 0; i < ls.length; i++) {
      var x = ls[i];
      x.tieu_de = x.name + (x.from_warehouse ? ' · ' + x.from_warehouse : '');
      s += vxTheRow(x, '<span class="vxtag ' + c[0] + '">' + h(x.trang_thai || c[1]) + '</span>');
    }
    return s;
  }

  var body = frame('Xuất huỷ',
    vxTabsHtml(TB, XK.tabH, dem) + '<div class="vxf" id="vxLst">' + listHtml() + '</div>', {
    fab: 1,
    onFab: function () { XK.gio = []; XK.lyDo = ''; XK.ghiChu = ''; XK.anh = ''; go(scrXkHuyNew); }
  });
  body.onclick = function (e) {
    var tb = e.target.closest('[data-tb]');
    if (tb) {
      XK.tabH = tb.dataset.tb;
      var ts = body.querySelectorAll('[data-tb]');
      for (var i = 0; i < ts.length; i++) ts[i].classList.toggle('on', ts[i].dataset.tb === XK.tabH);
      var el = body.querySelector('#vxLst'); if (el) el.innerHTML = listHtml();
      return;
    }
    var r = e.target.closest('[data-xem]');
    if (r) { var n = r.dataset.xem; go(function () { scrXkView(n); }); }
  };
}



async function scrXkHuyNew() {
  vgbCss();
  if (!XK.kho) { try { XK.kho = localStorage.getItem('vgbKhoXuat') || ''; } catch (e) { } }
  frame('Lập phiếu xuất huỷ', '<div class="emp"><div class="e1">⏳</div></div>');
  var b = await xkBoot();
  var ly = '<option value="">-- chọn lý do --</option>';
  for (var i = 0; i < b.ly_do.length; i++) {
    ly += '<option value="' + h(b.ly_do[i]) + '"' + (b.ly_do[i] === XK.lyDo ? ' selected' : '') +
      '>' + h(b.ly_do[i]) + '</option>';
  }
  var body = frame('Lập phiếu xuất huỷ',
    '<div class="vxf">' +
    '<div class="vxl">Kho xuất</div><select class="vxs" id="vxKho">' + vxKhoXuatOpt(b.kho, XK.kho) + '</select>' +
    '<div class="vxl">Lý do huỷ</div><select class="vxs" id="vxLy">' + ly + '</select>' +
    '<div class="vxl">Ảnh chứng minh (không bắt buộc)</div>' +
    '<input class="vxi" type="file" accept="image/*" id="vxAnh">' +
    '<div id="vxAnhOk" style="font-size:13px;color:#027a48;margin-top:6px"></div>' +
    '<div class="vxl">Danh sách hàng huỷ</div><div id="vxDong">' + vxDongHtml() + '</div>' +
    '<button class="vxb o" id="vxThem">+ Thêm hàng</button>' +
    '<div class="vxl">Ghi chú</div>' +
    '<input class="vxi" id="vxGc" placeholder="Ví dụ: bánh trưng bày hết ngày 03/08" value="' + h(XK.ghiChu) + '">' +
    '<button class="vxb" id="vxLuu">Lưu phiếu, chờ quản lý ghi sổ</button>' +
    '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:10px">' +
    'Tồn kho chỉ trừ sau khi quản lý kho bấm Ghi sổ.</div></div>');

  var eKho = body.querySelector('#vxKho');
  var eLy = body.querySelector('#vxLy');
  var eGc = body.querySelector('#vxGc');

  eKho.onchange = function () {
    if (XK.kho && this.value !== XK.kho && XK.gio.length) {
      XK.gio = [];
      toast('Đổi kho nên phải chọn lại hàng.');
    }
    XK.kho = this.value;
    try { localStorage.setItem('vgbKhoXuat', XK.kho); } catch (e) { }
    var seYc = body.querySelector('#vxYc');
    if (seYc && XK.yc) { XK.yc = ''; seYc.value = ''; toast('Đổi kho xuất nên đã bỏ liên kết phiếu yêu cầu.'); }
    vxNoiDong(body);
  };
  eLy.onchange = function () { XK.lyDo = this.value; };
  eGc.onchange = function () { XK.ghiChu = this.value; };
  vxNoiSuKien(body);

  body.querySelector('#vxThem').onclick = function () {
    XK.kho = eKho.value;
    XK.ghiChu = eGc.value;
    XK.lyDo = eLy.value;
    if (!XK.kho) { toast('Chọn kho xuất trước đã.'); return; }
    var kho = XK.kho;
    go(function () { scrXkChonHang(kho, scrXkHuyNew); });
  };

  body.querySelector('#vxAnh').onchange = async function () {
    var f = this.files && this.files[0];
    if (!f) return;
    var ok = body.querySelector('#vxAnhOk');
    ok.textContent = 'Đang tải ảnh lên...';
    try {
      XK.anh = await vxUpAnh(f);
      ok.textContent = 'Đã tải ảnh lên.';
    } catch (e) {
      ok.style.color = '#d92d20';
      ok.textContent = 'Không tải được ảnh: ' + (e.message || e);
    }
  };

  body.querySelector('#vxLuu').onclick = async function () {
    XK.kho = eKho.value; XK.lyDo = eLy.value; XK.ghiChu = eGc.value;
    if (!XK.kho) { toast('Chưa chọn kho xuất.'); return; }
    if (!XK.lyDo) { toast('Chưa chọn lý do huỷ.'); return; }
    if (!XK.gio.length) { toast('Chưa có món nào.'); return; }
    this.disabled = true;
    try {
      var r = await api('vagabond.xuat_kho.luu_xuat_huy', {
        kho: XK.kho, ly_do: XK.lyDo, ghi_chu: XK.ghiChu, anh: XK.anh,
        dong: JSON.stringify(XK.gio.map(function (d) { return { ma: d.ma, sl: d.sl }; }))
      });
      XK.gio = []; XK.anh = ''; XK.ghiChu = ''; XK.tabH = 'cho';
      toast('Đã lưu ' + r.name + ', phiếu chờ quản lý ghi sổ.');
      go(function () { scrXkView(r.name); }, true);
    } catch (e) {
      this.disabled = false;
      toast(e.message || 'Không lưu được phiếu.');
    }
  };
}

/* ----- Xuat dieu chuyen noi bo ----- */
async function scrXkCkList() {
  vgbCss();
  frame('Xuất điều chuyển', '<div class="emp"><div class="e1">⏳</div></div>');
  await xkBoot();
  var ds = [];
  try { ds = (await api('vagabond.xuat_kho.ds_phieu', { loai: 'chuyen', gioi_han: 40 })) || []; } catch (e) { }
  var D = {
    cho: ds.filter(function (x) { return x.docstatus === 0; }),
    xong: ds.filter(function (x) { return x.docstatus === 1; }),
    huy: await vxDsHuy('chuyen')
  };
  if (!XK.tabC) XK.tabC = 'xong';
  if (D.cho.length) XK.tabC = 'cho';
  var dem = { cho: D.cho.length, xong: D.xong.length, huy: D.huy.length };
  var TB = [{ k: 'cho', ten: 'Chờ ghi sổ' }, { k: 'xong', ten: 'Đã chuyển' }, { k: 'huy', ten: 'Đã huỷ' }];
  var TAG = { cho: ['c', 'Chờ ghi sổ'], xong: ['d', 'Đã chuyển'], huy: ['x', 'Đã huỷ'] };

  function listHtml() {
    var ls = D[XK.tabC] || [];
    if (!ls.length) {
      return '<div style="text-align:center;color:#98a2b3;padding:40px 20px;font-size:14px">' +
        (XK.tabC === 'cho' ? 'Không có phiếu nào chờ ghi sổ.<br>Bấm nút + để lập phiếu.' :
          XK.tabC === 'xong' ? 'Chưa có phiếu điều chuyển nào.<br>Bấm nút + để lập phiếu.' : 'Không có phiếu bị huỷ trong 30 ngày qua.') + '</div>';
    }
    var c = TAG[XK.tabC], s = '';
    for (var i = 0; i < ls.length; i++) {
      var x = ls[i];
      x.tieu_de = (x.from_warehouse || '') + ' → ' + (x.to_warehouse || '');
      var meta0 = x.so_dong; x.nguoi_tao = x.nguoi_tao || x.name;
      s += vxTheRow(x, '<span class="vxtag ' + c[0] + '">' + h(x.trang_thai || c[1]) + '</span>');
    }
    return s;
  }

  var body = frame('Xuất điều chuyển',
    vxTabsHtml(TB, XK.tabC, dem) + '<div class="vxf" id="vxLst">' + listHtml() + '</div>', {
    fab: 1,
    onFab: function () { XK.gio = []; XK.khoNhan = ''; XK.ghiChu = ''; XK.yc = ''; go(scrXkCkNew); }
  });
  body.onclick = function (e) {
    var tb = e.target.closest('[data-tb]');
    if (tb) {
      XK.tabC = tb.dataset.tb;
      var ts = body.querySelectorAll('[data-tb]');
      for (var i = 0; i < ts.length; i++) ts[i].classList.toggle('on', ts[i].dataset.tb === XK.tabC);
      var el = body.querySelector('#vxLst'); if (el) el.innerHTML = listHtml();
      return;
    }
    var r = e.target.closest('[data-xem]');
    if (r) { var n = r.dataset.xem; go(function () { scrXkView(n); }); }
  };
}



async function scrXkCkNew() {
  vgbCss();
  if (!XK.kho) { try { XK.kho = localStorage.getItem('vgbKhoXuat') || ''; } catch (e) { } }
  frame('Lập phiếu điều chuyển', '<div class="emp"><div class="e1">⏳</div></div>');
  var b = await xkBoot();
  var yc = await api('vagabond.xuat_kho.yeu_cau_cho_chuyen', { kho_xuat: XK.kho || '' });
  var ycOpt = '<option value="">-- không theo phiếu nào --</option>';
  for (var i = 0; i < (yc || []).length; i++) {
    ycOpt += '<option value="' + h(yc[i].name) + '"' + (yc[i].name === XK.yc ? ' selected' : '') +
      '>' + h(yc[i].name) + ' → ' + h(yc[i].set_warehouse || '') + '</option>';
  }
  var body = frame('Lập phiếu điều chuyển',
    '<div class="vxf">' +
    '<div class="vxl">Theo phiếu yêu cầu điều chuyển</div>' +
    '<select class="vxs" id="vxYc">' + ycOpt + '</select>' +
    '<div class="vxl">Kho xuất</div><select class="vxs" id="vxKho">' + vxKhoXuatOpt(b.kho, XK.kho) + '</select>' +
    '<div class="vxl">Kho nhận</div><select class="vxs" id="vxKhoN">' + vxKhoOpt(b.kho, XK.khoNhan) + '</select>' +
    '<div class="vxl">Danh sách hàng chuyển</div><div id="vxDong">' + vxDongHtml() + '</div>' +
    '<button class="vxb o" id="vxThem">+ Thêm hàng</button>' +
    '<div class="vxl">Ghi chú</div>' +
    '<input class="vxi" id="vxGc" placeholder="Ví dụ: chuyển bánh cho cửa hàng Trần Cao Vân" value="' + h(XK.ghiChu) + '">' +
    '<button class="vxb" id="vxLuu">Ghi sổ phiếu chuyển</button>' +
    '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:10px">' +
    'Ghi sổ xong hàng đã nằm ở kho nhận. Kho nhận vẫn phải đếm lại khi nhận.</div></div>');

  var eKho = body.querySelector('#vxKho');
  var eKhoN = body.querySelector('#vxKhoN');
  var eGc = body.querySelector('#vxGc');
  var eYc = body.querySelector('#vxYc');

  eKho.onchange = function () {
    if (XK.kho && this.value !== XK.kho && XK.gio.length) {
      XK.gio = [];
      toast('Đổi kho nên phải chọn lại hàng.');
    }
    XK.kho = this.value;
    try { localStorage.setItem('vgbKhoXuat', XK.kho); } catch (e) { }
    var seYc = body.querySelector('#vxYc');
    if (seYc && XK.yc) { XK.yc = ''; seYc.value = ''; toast('Đổi kho xuất nên đã bỏ liên kết phiếu yêu cầu.'); }
    vxNoiDong(body);
  };
  eKhoN.onchange = function () { XK.khoNhan = this.value; };
  eGc.onchange = function () { XK.ghiChu = this.value; };
  vxNoiSuKien(body);

  eYc.onchange = async function () {
    XK.yc = this.value;
    if (!XK.yc) return;
    var ct = await api('vagabond.xuat_kho.dong_cua_yeu_cau', { name: XK.yc });
    XK.gio = (ct.dong || []).map(function (d) {
      return { ma: d.ma, ten: d.ten, dvt: d.dvt, ton: d.sl, sl: d.sl };
    });
    if (ct.kho_xuat) { XK.kho = ct.kho_xuat; eKho.value = ct.kho_xuat; }
    if (ct.kho_nhan) { XK.khoNhan = ct.kho_nhan; eKhoN.value = ct.kho_nhan; }
    vxNoiDong(body);
    toast('Đã điền ' + XK.gio.length + ' món theo phiếu.');
  };
  if (XK.yc && !XK.gio.length) { eYc.value = XK.yc; eYc.onchange(); }

  body.querySelector('#vxThem').onclick = function () {
    XK.kho = eKho.value; XK.khoNhan = eKhoN.value; XK.ghiChu = eGc.value;
    if (!XK.kho) { toast('Chọn kho xuất trước đã.'); return; }
    var kho = XK.kho;
    go(function () { scrXkChonHang(kho, scrXkCkNew); });
  };

  body.querySelector('#vxLuu').onclick = async function () {
    XK.kho = eKho.value; XK.khoNhan = eKhoN.value; XK.ghiChu = eGc.value;
    if (!XK.kho || !XK.khoNhan) { toast('Phải chọn cả kho xuất và kho nhận.'); return; }
    if (XK.kho === XK.khoNhan) { toast('Kho xuất và kho nhận trùng nhau.'); return; }
    if (!XK.gio.length) { toast('Chưa có món nào.'); return; }
    this.disabled = true;
    try {
      var r = await api('vagabond.xuat_kho.luu_dieu_chuyen', {
        kho_xuat: XK.kho, kho_nhan: XK.khoNhan, ghi_chu: XK.ghiChu, yeu_cau: XK.yc,
        dong: JSON.stringify(XK.gio.map(function (d) { return { ma: d.ma, sl: d.sl }; }))
      });
      XK.gio = []; XK.ghiChu = ''; XK.yc = ''; XK.tabC = 'xong';
      toast('✓ Đã ghi sổ ' + r.name + '. Phiếu nằm ở tab Đã chuyển.');
      go(function () { scrXkView(r.name); }, true);
    } catch (e) {
      this.disabled = false;
      toast(e.message || 'Không ghi sổ được.');
    }
  };
}

/* ----- Xem mot phieu xuat ----- */
async function scrXkView(name) {
  vgbCss();
  frame('Phiếu xuất', '<div class="emp"><div class="e1">⏳</div></div>');
  var d = await api('vagabond.xuat_kho.chi_tiet', { name: name });
  var laHuy = d.loai === 'Material Issue';
  var rows = '';
  for (var i = 0; i < d.dong.length; i++) {
    var x = d.dong[i];
    rows += '<div class="vxr"><div class="t"><b>' + h(x.ten || x.ma) + '</b>' +
      '<i>' + h(x.ma) + (x.tien ? ' · ' + vxSo(x.tien) + 'đ' : '') + '</i></div>' +
      '<span style="font-weight:700">' + vxSo(x.sl) + ' ' + h(x.dvt || '') + '</span></div>';
  }
  var nut = '';
  if (d.docstatus === 1 && !laHuy && d.kho_nhan && (!khoGiuCuaToi().length || laKhoCuaToi(d.kho_nhan))) {
    nut += '<button class="vxb o" id="vxHuyTiep">🗑️ Xuất huỷ hàng này tại ' + h(shortWh(d.kho_nhan)) + '</button>';
  }
  if (d.docstatus === 0 && d.vgb_huy) {
    /* Phieu da bo: khong ghi so duoc nua, nhung van con nguyen de truy. */
    nut += '<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:11px 13px;margin-top:10px">' +
      '<b style="color:#991b1b;font-size:14px">🚫 Phiếu này đã bỏ</b>' +
      '<div style="font-size:12.5px;color:#7f1d1d;line-height:1.6;margin-top:3px">Lý do: ' +
      h(d.vgb_huy_ly_do || 'không ghi') + (d.vgb_huy_boi ? ' - ' + h(d.vgb_huy_boi) : '') +
      '<br>Phiếu vẫn nằm nguyên trong hệ thống, chỉ không ghi sổ được nữa.</div></div>';
  } else if (d.docstatus === 0) {
    if (d.duoc_duyet) nut += '<button class="vxb" id="vxGhi">Ghi sổ phiếu này</button>';
    if (d.la_cua_toi || d.duoc_duyet) nut += '<button class="vxb o" id="vxXoa">🚫 Bỏ phiếu này</button>';
    if (!d.duoc_duyet) {
      nut += '<div style="font-size:12px;color:#98a2b3;text-align:center;margin-top:10px">' +
        'Phiếu đang chờ quản lý kho ghi sổ.</div>';
    }
  }
  var body = frame(laHuy ? 'Phiếu xuất huỷ' : 'Phiếu điều chuyển',
    '<div class="vxf">' +
    '<div class="vxr"><div class="t"><b>' + h(d.name) + '</b>' +
    '<i>' + h(d.ngay) + ' · ' + h(d.nguoi_tao) + '</i></div>' +
    '<span class="vxtag ' + (d.docstatus === 0 ? 'c' : 'd') + '">' + h(d.trang_thai) + '</span></div>' +
    '<div class="vxl">' + (laHuy ? 'Kho xuất' : 'Chuyển kho') + '</div>' +
    '<div class="vxr"><div class="t"><b>' + h(d.kho_xuat || '') +
    (d.kho_nhan ? ' → ' + h(d.kho_nhan) : '') + '</b></div></div>' +
    (d.ly_do ? '<div class="vxl">Lý do huỷ</div><div class="vxr"><div class="t"><b>' +
      h(d.ly_do) + '</b></div></div>' : '') +
    (d.ghi_chu ? '<div class="vxl">Ghi chú</div><div class="vxr"><div class="t"><b>' +
      h(d.ghi_chu) + '</b></div></div>' : '') +
    (d.anh ? '<div class="vxl">Ảnh chứng minh</div><img src="' + h(d.anh) +
      '" style="width:100%;border-radius:12px">' : '') +
    '<div class="vxl">Hàng trong phiếu (' + d.dong.length + ' món)</div>' + rows +
    (d.tong_tien ? '<div style="text-align:right;font-weight:700;margin-top:8px">Giá trị: ' +
      vxSo(d.tong_tien) + 'đ</div>' : '') +
    nut + '</div>');

  var hu = body.querySelector('#vxHuyTiep');
  if (hu) hu.onclick = function () {
    XK.kho = d.kho_nhan; XK.lyDo = ''; XK.anh = ''; XK.ghiChu = 'Hàng nhận từ phiếu ' + d.name + ' không bán được';
    XK.gio = (d.dong || []).map(function (x) { return { ma: x.ma, ten: x.ten, dvt: x.dvt, ton: x.sl, sl: x.sl }; });
    go(scrXkHuyNew);
  };
  var g = body.querySelector('#vxGhi');
  if (g) g.onclick = async function () {
    this.disabled = true;
    try {
      await api('vagabond.xuat_kho.ghi_so_xuat_huy', { name: name });
      toast('Đã ghi sổ, tồn kho đã trừ.');
      go(function () { scrXkView(name); }, true);
    } catch (e) {
      this.disabled = false;
      toast(e.message || 'Không ghi sổ được.');
    }
  };
  var x = body.querySelector('#vxXoa');
  if (x) x.onclick = async function () {
    /* Khong con xoa phieu nua (anh Viet 11/08/2026): phieu kho cung la
       chung tu. Danh dau da bo, phieu van nam lai de con truy. */
    var ly_do = await promptSheet('Vì sao bỏ phiếu này?', 'Lập nhầm, sai kho, sai số lượng...');
    if (ly_do === null) return;
    if (!ly_do) return toast('Phải ghi lý do thì sau này còn biết vì sao.', 4000);
    this.disabled = true;
    try {
      await api('vagabond.xuat_kho.xoa_ban_nhap', { name: name, ly_do: ly_do });
      toast('Đã bỏ phiếu. Phiếu vẫn còn trong danh sách, đánh dấu đã bỏ.', 4000);
      back();
    } catch (e) {
      this.disabled = false;
      toast(e.message || 'Không bỏ được.');
    }
  };
}

/* Nen anh truoc khi tai len: canh dai toi da 1600px, JPEG 72% - anh dien thoai 5MB con ~300KB */
async function vxNenAnh(f) {
  if (!/^image\//.test(f.type || '')) return f;
  var url = '';
  try {
    url = URL.createObjectURL(f);
    var img = await new Promise(function (res, rej) {
      var i = new Image();
      i.onload = function () { res(i); };
      i.onerror = function () { rej(new Error('anh loi')); };
      i.src = url;
    });
    var MAX = 1600, w = img.naturalWidth, hh = img.naturalHeight;
    if (!w || !hh) return f;
    if (w > MAX || hh > MAX) { var ty = Math.min(MAX / w, MAX / hh); w = Math.round(w * ty); hh = Math.round(hh * ty); }
    var cv = document.createElement('canvas');
    cv.width = w; cv.height = hh;
    cv.getContext('2d').drawImage(img, 0, 0, w, hh);
    var blob = await new Promise(function (res) { cv.toBlob(res, 'image/jpeg', 0.72); });
    if (!blob || blob.size >= f.size) return f;
    var ten = (f.name || 'anh').replace(/\.[a-zA-Z0-9]+$/, '') + '.jpg';
    return new File([blob], ten, { type: 'image/jpeg' });
  } catch (e) { return f; }
  finally { try { if (url) URL.revokeObjectURL(url); } catch (e2) { } }
}
async function vxUpAnh(f) {
  f = await vxNenAnh(f);
  function ban() {
    var fd = new FormData();
    fd.append('file', f, f.name);
    fd.append('is_private', '0');
    fd.append('folder', 'Home');
    return fetch('/api/method/upload_file', {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'X-Frappe-CSRF-Token': csrfTok() },
      body: fd
    });
  }
  var r = await ban();
  if (r.status === 400 || r.status === 403) {
    if (await refreshCsrf()) r = await ban();
  }
  var j = {};
  try { j = await r.json(); } catch (e) { }
  if (!r.ok || !j.message || !j.message.file_url) throw new Error('máy chủ không nhận ảnh (mã ' + r.status + ')');
  return j.message.file_url;
}

/* ---------- 6. Danh sach chung tu ---------- */
var mrFilter = { status: 'Tất cả', q: '' };
function bepWhFg(v) {
  var lw = String(v || '').toLowerCase();
  var k = lw.indexOf('baker') >= 0 ? 'baker' : (lw.indexOf('lab') >= 0 ? 'lab' : (lw.indexOf('pastry') >= 0 ? 'pastry' : ''));
  if (!k) return '';
  return whFind(k, 'thành phẩm') || whFind(k) || '';
}
function canGiaoBep(d, dlv) {
  if (!d || d.docstatus !== 1) return false;
  if (d.material_request_type !== 'Manufacture') return false;
  if (d.status === 'Stopped' || d.status === 'Cancelled') return false;
  if (!d.set_warehouse) return false;
  if (!bepWhFg(d.custom_bep_nhan)) return false;
  return (d.items || []).some(function (it) {
    var con = (it.stock_qty || (it.qty || 0) * (it.conversion_factor || 1)) - ((dlv || {})[it.name] || 0);
    return con > 0.0001;
  });
}
function bepMau(v) {
  var C = { 'Bếp Pastry': ['#fce7f3', '#9d174d'], 'Bếp Baker': ['#fef3c7', '#92400e'], 'Bếp Lab': ['#dbeafe', '#1e40af'], 'Cả hai bếp': ['#ede9fe', '#5b21b6'] };
  return C[v] || ['#e5e7eb', '#4b5563'];
}
function bepBadge(v) {
  var c = bepMau(v), t = v || 'Chưa rõ bếp';
  return '<span style="display:inline-block;margin-left:6px;padding:1px 7px;border-radius:9px;font-size:11px;font-weight:700;vertical-align:middle;background:' + c[0] + ';color:' + c[1] + '">' + h(t) + '</span>';
}
var BEPS = ['Tất cả', 'Bếp Pastry', 'Bếp Baker', 'Bếp Lab', 'Cả hai bếp', 'Chưa rõ bếp'];

async function scrMRList(T) {
  var body = frame(T.title, '<div class="emp"><div class="e1">⏳</div></div>', { fab: true, onFab: function () { startDraft(T); } });
  var f = { material_request_type: T.key };
  var docs = await getList('Material Request', {
    fields: ['name', 'transaction_date', 'schedule_date', 'status', 'docstatus', 'set_warehouse', 'set_from_warehouse', 'owner', 'title', 'custom_bep_nhan', 'trang_thai_bep'],
    filters: f, limit_page_length: 60, order_by: 'creation desc'
  });
  var STATS = T.key === 'Manufacture'
    ? ['Tất cả', 'Draft', 'Chưa làm', 'Đang làm', 'Đã xong', 'Cancelled']
    : ['Tất cả', 'Draft', 'Pending', 'Partially Ordered', 'Ordered', 'Received', 'Cancelled'];
  function stKey(d) {
    if (T.key !== 'Manufacture') return d.status;
    if (d.docstatus === 0) return 'Draft';
    if (d.status === 'Cancelled') return 'Cancelled';
    return d.trang_thai_bep || 'Chưa làm';
  }
  function drawList() {
    var q = mrFilter.q.toLowerCase();
    var rows = docs.filter(function (d) {
      if (mrFilter.status !== 'Tất cả' && stKey(d) !== mrFilter.status) return false;
      if (T.key === 'Manufacture' && mrFilter.bep && mrFilter.bep !== 'Tất cả' && (d.custom_bep_nhan || 'Chưa rõ bếp') !== mrFilter.bep) return false;
      if (q && (d.name + ' ' + (d.title || '')).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    var chips = STATS.map(function (s) {
      var c = s === 'Tất cả' ? docs.length : docs.filter(function (d) { return stKey(d) === s; }).length;
      if (s !== 'Tất cả' && !c) return '';
      return '<div class="chip' + (mrFilter.status === s ? ' on' : '') + '" data-s="' + h(s) + '">' + h(vnSt(s)) + ' ' + c + '</div>';
    }).join('');
    var lst = rows.length ? '<div class="lst">' + rows.map(function (d) {
      var k = stKey(d);
      var cls = k === 'Cancelled' ? 'r' : (k === 'Draft' ? 'w' : ((k === 'Pending' || k === 'Chưa làm') ? 'b' : ((k === 'Đang làm') ? 'w' : 'g')));
      return '<div class="li" data-n="' + h(d.name) + '"><div class="lt">' +
        '<div class="l1">' + h(d.name) + (T.key === 'Manufacture' ? bepBadge(d.custom_bep_nhan) : '') + '</div>' +
        '<div class="l2">' + dmy(d.transaction_date) + ' &middot; cần ' + dmy(d.schedule_date) +
        (d.set_warehouse ? ' &middot; ' + h(shortWh(d.set_warehouse)) : '') + '</div></div>' +
        '<span class="st ' + cls + '">' + h(vnSt(k)) + '</span></div>';
    }).join('') + '</div>' : '<div class="emp"><div class="e1">📄</div><div class="e2">Không có chứng từ nào</div></div>';
    var bchips = T.key !== 'Manufacture' ? '' : '<div class="chips">' + BEPS.map(function (s) {
      var n = s === 'Tất cả' ? docs.length : docs.filter(function (d) { return (d.custom_bep_nhan || 'Chưa rõ bếp') === s; }).length;
      if (s !== 'Tất cả' && !n) return '';
      var cl = bepMau(s === 'Chưa rõ bếp' ? '' : s);
      var on = (mrFilter.bep || 'Tất cả') === s;
      return '<div class="chip' + (on ? ' on' : '') + '" data-bp="' + h(s) + '"' + (on ? '' : ' style="background:' + cl[0] + ';color:' + cl[1] + '"') + '>' + h(s) + ' ' + n + '</div>';
    }).join('') + '</div>';
    var b2 = frame(T.title, '<div class="chips">' + chips + '</div>' + bchips +
      srchBox('mrq', 'Nhập mã chứng từ', mrFilter.q, true) + lst,
      { fab: true, onFab: function () { startDraft(T); } });
    b2.querySelector('#mrq').oninput = function (e) { mrFilter.q = e.target.value; var v = e.target.value; drawList(); var i = document.getElementById('mrq'); i.focus(); i.value = v; i.setSelectionRange(v.length, v.length); };
    document.getElementById('mrqscan').onclick = async function () {
      var code = await scanBarcode();
      if (code) { mrFilter.q = code; drawList(); }
    };
    b2.onclick = function (e) {
      var c = e.target.closest('[data-s]'); if (c) { mrFilter.status = c.dataset.s; return drawList(); }
      var cb = e.target.closest('[data-bp]'); if (cb) { mrFilter.bep = cb.dataset.bp; return drawList(); }
      var r = e.target.closest('[data-n]'); if (r) go(function () { scrMRView(r.dataset.n, T); });
    };
  }
  mrFilter.q = ''; mrFilter.bep = 'Tất cả'; drawList();
}

async function scrMRView(name, T) {
  frame(name, '<div class="emp"><div class="e1">⏳</div></div>');
  var d = await api('frappe.client.get', { doctype: 'Material Request', name: name });
  var dlv = {};
  if (T.key === 'Manufacture' && d.docstatus === 1) {
    try {
      var sedRows = await getList('Stock Entry Detail', {
        parent: 'Stock Entry',
        fields: ['material_request_item', 'transfer_qty'],
        filters: { material_request: name, docstatus: 1 },
        limit_page_length: 0
      });
      (sedRows || []).forEach(function (x) {
        if (!x.material_request_item) return;
        dlv[x.material_request_item] = (dlv[x.material_request_item] || 0) + (x.transfer_qty || 0);
      });
    } catch (eDlv) { }
  }
  var CU_MAU = { 'Chờ mua': '#8a8f98', 'Đang xử lý': '#c77700', 'Đã đặt NCC': '#1a73c7', 'Về một phần': '#7a4bbf', 'Đã nhập kho': '#1f9254', 'Lấy từ kho nội bộ': '#0a8f9e', 'Đã dừng': '#c0392b' };
  function chipCU(v) {
    if (!v) return '';
    return '<span style="display:inline-block;margin-top:5px;padding:2px 9px;border-radius:11px;font-size:12px;font-weight:600;color:#fff;background:' + (CU_MAU[v] || '#8a8f98') + '">' + h(v) + '</span>';
  }
  var laMua = d.material_request_type === 'Purchase';
  var rows = (d.items || []).map(function (it, i) {
    return '<div class="ic1"><div class="ih"><div class="n">' + (i + 1) + '</div>' +
      '<div class="in">' + h(it.item_name || it.item_code) + '<div class="ig">Mã: ' + h(it.item_code) + '</div>' + (laMua ? chipCU(it.trang_thai_cung_ung) : '') + '</div></div>' +
      '<div class="stk"><div><div class="s1">Số lượng</div><div class="s2">' + num(it.qty) + ' ' + h(it.uom) + '</div></div>' +
      (T.hasTime ? '<div><div class="s1">' + h(T.timeLabel) + '</div><div class="s2">' + h(it.gio_can_lay ? String(it.gio_can_lay).slice(0, 5) : '-') + '</div></div>' : '') +
      '<div><div class="s1">Ngày cần</div><div class="s2">' + dmy(it.schedule_date) + '</div></div>' + (laMua && it.ncc_dat_hang ? '<div><div class="s1">Nhà cung cấp</div><div class="s2">' + h(it.ncc_dat_hang) + '</div></div>' : '') + (laMua && it.ngay_hen_giao ? '<div><div class="s1">NCC hẹn giao</div><div class="s2">' + dmy(it.ngay_hen_giao) + '</div></div>' : '') + ((dlv[it.name] || 0) > 0.0001 ? '<div><div class="s1">Đã giao</div><div class="s2">' + num(dlv[it.name] / (it.conversion_factor || 1)) + ' ' + h(it.uom) + '</div></div>' : '') + '</div>' +
      (it.description && it.description.replace(/<[^>]*>/g, '').trim() && it.description.indexOf(it.item_name) < 0 ?
        '<div style="padding:10px 14px;font-size:13.5px;color:#5a6070">' + h(it.description.replace(/<[^>]*>/g, '').trim()) + '</div>' : '') +
      '</div>';
  }).join('');
  var b = frame(name, '<div class="card">' +
    '<div class="kv"><span>Loại phiếu</span><b>' + h(T.title) + '</b></div>' +
    '<div class="kv"><span>Ngày lập</span><b>' + dmy(d.transaction_date) + '</b></div>' +
    '<div class="kv"><span>Ngày cần</span><b>' + dmy(d.schedule_date) + '</b></div>' +
    (d.set_from_warehouse ? '<div class="kv"><span>Kho xuất</span><b>' + h(shortWh(d.set_from_warehouse)) + '</b></div>' : '') +
    (d.set_warehouse ? '<div class="kv"><span>Kho nhận</span><b>' + h(shortWh(d.set_warehouse)) + '</b></div>' : '') +
    (d.bo_phan_yeu_cau ? '<div class="kv"><span>Bộ phận yêu cầu</span><b>' + h(d.bo_phan_yeu_cau) + '</b></div>' : '') +
    (d.nguoi_yeu_cau ? '<div class="kv"><span>Người yêu cầu</span><b>' + h(d.nguoi_yeu_cau) + '</b></div>' : '') +
    (d.custom_bep_nhan ? '<div class="kv"><span>Bếp nhận</span><b>' + h(d.custom_bep_nhan) + '</b></div>' : '') +
    (T.key === 'Manufacture' ? '<div class="kv"><span>Trạng thái bếp</span><b>' + h(d.trang_thai_bep || 'Chưa làm') + (d.bep_nguoi_xong ? ' (' + h(d.bep_nguoi_xong) + ')' : '') + '</b></div>' : '') +
    '<div class="kv"><span>Trạng thái</span><b>' + h(vnSt(d.status)) + '</b></div>' +
    '<div class="kv"><span>Người lập</span><b>' + h(d.nguoi_lap_ten || d.owner) + '</b></div>' + (laMua && d.trang_thai_cung_ung ? '<div class="kv"><span>Cung ứng</span><b>' + chipCU(d.trang_thai_cung_ung) + (d.tom_tat_cung_ung ? '<div style="font-weight:400;font-size:12.5px;color:#5a6070;margin-top:3px">' + h(d.tom_tat_cung_ung) + '</div>' : '') + '</b></div>' : '') + '</div>' +
    '<div class="sec">' + (d.items || []).length + ' hàng hoá</div>' + rows,
    (d.docstatus === 0 ? { footer: '<button class="btn" id="vSub">Gửi duyệt</button>' }
      : (canReceive(d) ? { footer: '<div style="display:flex;gap:10px"><button class="btn" id="vSoan" style="background:#fff;color:#101828;border:1px solid #d0d5dd">🧺 Soạn hàng (kho xuất)</button><button class="btn" id="vRecv">📦 Đã nhận hàng</button></div>' }
      : (canGiaoBep(d, dlv) ? { footer: '<button class="btn" id="vGiao">🚚 Giao hàng sang ' + h(shortWh(d.set_warehouse)) + '</button>' } : {}))));
  var sn = document.getElementById('vSoan');
  if (sn) sn.onclick = function () {
    XK.gio = []; XK.ghiChu = '';
    XK.yc = d.name;
    XK.kho = d.set_from_warehouse || '';
    XK.khoNhan = d.set_warehouse || '';
    go(scrXkCkNew);
  };
  var rc = document.getElementById('vRecv');
  if (rc) rc.onclick = async function () {
    var nhap = [];
    try { nhap = await getList('Stock Entry Detail', { parent: 'Stock Entry', fields: ['parent'], filters: { material_request: d.name, docstatus: 0 }, limit_page_length: 1 }); } catch (e) { }
    if (nhap.length) {
      if (!await confirmSheet('Kho xuất đang soạn phiếu ' + nhap[0].parent, 'Phiếu điều chuyển nháp của yêu cầu này đang chờ ghi sổ. Bấm nhận ở đây nữa là trừ kho HAI LẦN. Chỉ tiếp tục nếu chắc chắn phiếu kia sẽ bị huỷ.', 'Vẫn tiếp tục')) return;
    }
    go(function () { scrRecvTransfer(d); });
  };
  var gb = document.getElementById('vGiao');
  if (gb) gb.onclick = function () {
    var srcW = bepWhFg(d.custom_bep_nhan);
    if (!srcW) return toast('Phiếu chưa ghi bếp nhận nên chưa biết xuất từ kho nào');
    go(function () {
      scrRecvTransfer(d, {
        src: srcW,
        doneMap: dlv,
        title: 'Giao hàng ',
        okLabel: 'Xác nhận giao hàng',
        emptyMsg: 'Phiếu này đã giao đủ hàng',
        remarks: 'Bếp giao hàng cho kho nhận theo phiếu '
      });
    });
  };
  var s = document.getElementById('vSub');
  if (s) s.onclick = async function () {
    if (!await confirmSheet('Gửi duyệt phiếu?', 'Sau khi gửi sẽ không sửa được nội dung.', 'Gửi duyệt')) return;
    busy(1);
    try { await api('frappe.client.submit', { doc: d }); toast('Đã gửi phiếu ' + name); back(); }
    catch (err) { toast(errMsg(err)); } finally { busy(0); }
  };
}

/* ---------- 6b. Xac nhan nhan hang cua phieu dieu chuyen noi bo ---------- */
function canReceive(d) {
  if (!d || d.docstatus !== 1) return false;
  if (d.material_request_type !== 'Material Transfer') return false;
  if (d.status === 'Stopped' || d.status === 'Cancelled') return false;
  var left = (d.items || []).some(function (it) { return (it.qty || 0) - (it.ordered_qty || 0) > 0.0001; });
  return left;
}

async function fefoPick(code, wh, need) {
  var q = {};
  try {
    var bq = await api('erpnext.stock.doctype.batch.batch.get_batch_qty', { item_code: code, warehouse: wh }) || [];
    bq.forEach(function (x) { if (x.batch_no) q[x.batch_no] = (q[x.batch_no] || 0) + (x.qty || 0); });
  } catch (e) {
    var sle = await getList('Stock Ledger Entry', {
      fields: ['batch_no', 'actual_qty'],
      filters: { item_code: code, warehouse: wh, is_cancelled: 0 }, limit_page_length: 0
    });
    sle.forEach(function (x) { if (x.batch_no) q[x.batch_no] = (q[x.batch_no] || 0) + (x.actual_qty || 0); });
  }
  var names = Object.keys(q).filter(function (b) { return q[b] > 0.0000001; });
  if (!names.length) return { short: need, list: [] };
  var ex = {};
  try {
    var bs = await getList('Batch', { fields: ['name', 'expiry_date'], filters: { name: ['in', names] }, limit_page_length: 0 });
    bs.forEach(function (b) { ex[b.name] = b.expiry_date || '9999-12-31'; });
  } catch (e2) { }
  names.sort(function (a, b) {
    var ea = ex[a] || '9999-12-31', eb = ex[b] || '9999-12-31';
    if (ea !== eb) return ea < eb ? -1 : 1;
    return a < b ? -1 : 1;
  });
  var out = [], rem = need;
  for (var i = 0; i < names.length && rem > 0.0000001; i++) {
    var take = q[names[i]] < rem ? q[names[i]] : rem;
    out.push({ batch: names[i], qty: Math.round(take * 1000000) / 1000000 });
    rem -= take;
  }
  return { short: rem > 0.0000001 ? rem : 0, list: out };
}

var rcv = { mr: null, rows: [] };
async function scrRecvTransfer(mr, opt) {
  opt = opt || {};
  rcv.mr = mr;
  rcv.rows = (mr.items || []).map(function (it) {
    var done = opt.doneMap ? ((opt.doneMap[it.name] || 0) / (it.conversion_factor || 1)) : (it.ordered_qty || 0);
    var left = (it.qty || 0) - done;
    return {
      row: it.name, item_code: it.item_code, item_name: it.item_name || it.item_code,
      uom: it.uom, stock_uom: it.stock_uom || it.uom, cf: it.conversion_factor || 1,
      max: left, qty: left > 0 ? left : 0, done: done
    };
  }).filter(function (r) { return r.max > 0.0001; });

  var src = opt.src || mr.set_from_warehouse || (mr.items && mr.items[0] && mr.items[0].from_warehouse) || '';
  var dst = mr.set_warehouse || (mr.items && mr.items[0] && mr.items[0].warehouse) || '';

  function draw() {
    var cards = rcv.rows.map(function (r, i) {
      return '<div class="ic1">' +
        '<div class="ih"><div class="n">' + (i + 1) + '</div>' +
        '<div class="in">' + h(r.item_name) + '<div class="ig">Mã: ' + h(r.item_code) + '</div></div></div>' +
        '<div class="stk"><div><div class="s1">Phiếu xin</div><div class="s2">' + num(r.max) + ' ' + h(r.uom) + '</div></div>' +
        (r.done > 0.0001 ? '<div><div class="s1">Đã nhận trước</div><div class="s2">' + num(r.done) + ' ' + h(r.uom) + '</div></div>' : '') +
        '</div>' +
        '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số lượng thực nhận</div>' +
        '<div class="qr"><div class="stp"><button data-m="' + i + '">&minus;</button>' +
        '<input type="number" inputmode="decimal" data-q="' + i + '" value="' + r.qty + '"><button data-p="' + i + '">+</button></div>' +
        '<div class="uom" style="display:flex;align-items:center;justify-content:center">' + h(r.uom) + '</div></div></div></div>' +
        '</div>';
    }).join('');

    var head = '<div class="card">' +
      '<div class="kv"><span>Phiếu</span><b>' + h(mr.name) + '</b></div>' +
      '<div class="kv"><span>Kho xuất</span><b>' + h(shortWh(src) || '-') + '</b></div>' +
      '<div class="kv"><span>Kho nhận</span><b>' + h(shortWh(dst) || '-') + '</b></div>' +
      '</div>' +
      '<div style="padding:2px 16px 0;font-size:12.5px;color:#8a8f9c;line-height:1.5">Sửa lại số lượng nếu nhận thiếu. Bấm xác nhận là máy trừ kho ' + h(shortWh(src)) + ' và nhập vào kho ' + h(shortWh(dst)) + '. Lô hàng máy tự chọn theo hạn dùng gần nhất trước.</div>';

    var body = rcv.rows.length
      ? head + '<div class="sec">' + rcv.rows.length + ' hàng hoá</div>' + cards
      : head + '<div class="emp"><div class="e1">✅</div><div class="e2">' + h(opt.emptyMsg || 'Phiếu này đã nhận đủ hàng') + '</div></div>';

    var b = frame((opt.title || 'Nhận hàng ') + mr.name, body,
      rcv.rows.length ? { footer: '<button class="btn" id="rcOk">' + h(opt.okLabel || 'Xác nhận nhập kho') + '</button>' } : {});

    b.onclick = function (e) {
      var p = e.target.closest('[data-p]'), m = e.target.closest('[data-m]');
      var i = p ? +p.dataset.p : (m ? +m.dataset.m : -1);
      if (i < 0) return;
      var r = rcv.rows[i];
      var v = (r.qty || 0) + (p ? 1 : -1);
      if (v < 0) v = 0;
      if (v > r.max) v = r.max;
      r.qty = Math.round(v * 1000000) / 1000000;
      var inp = b.querySelector('[data-q="' + i + '"]');
      if (inp) inp.value = r.qty;
    };
    b.addEventListener('input', function (e) {
      var q = e.target.closest('[data-q]'); if (!q) return;
      var i = +q.dataset.q, r = rcv.rows[i];
      var v = parseFloat(q.value); if (!(v >= 0)) v = 0;
      if (v > r.max) { v = r.max; q.value = v; toast('Không nhận quá số trên phiếu'); }
      r.qty = v;
    });

    var ok = document.getElementById('rcOk');
    if (ok) ok.onclick = function () { doReceive(mr, src, dst, opt); };
  }
  draw();
}

async function doReceive(mr, src, dst, opt) {
  opt = opt || {};
  var use = rcv.rows.filter(function (r) { return r.qty > 0.0001; });
  if (!use.length) return toast('Chưa nhập số lượng nào');
  if (!src) return toast('Phiếu chưa có kho xuất, không nhập kho được');
  if (!dst) return toast('Phiếu chưa có kho nhận, không nhập kho được');
  var ok = await confirmSheet('Nhập hàng vào kho ' + shortWh(dst),
    'Máy sẽ trừ ' + use.length + ' món ở kho ' + shortWh(src) + ' và nhập vào kho ' + shortWh(dst) + '. Bút toán kho không sửa lại được.',
    'Xác nhận nhập kho');
  if (!ok) return;
  busy(1);
  try {
    var codes = use.map(function (r) { return r.item_code; });
    var metas = await getList('Item', { fields: ['name', 'has_batch_no'], filters: { name: ['in', codes] }, limit_page_length: 0 });
    var hb = {};
    metas.forEach(function (x) { hb[x.name] = x.has_batch_no ? 1 : 0; });

    var items = [], thieu = [];
    for (var i = 0; i < use.length; i++) {
      var r = use[i];
      if (hb[r.item_code]) {
        var need = r.qty * (r.cf || 1);
        var al = await fefoPick(r.item_code, src, need);
        if (al.short > 0.0001) { thieu.push(r.item_name + ' (thiếu ' + num(al.short) + ' ' + r.stock_uom + ')'); continue; }
        al.list.forEach(function (a) {
          items.push({
            item_code: r.item_code, qty: a.qty, uom: r.stock_uom, conversion_factor: 1,
            s_warehouse: src, t_warehouse: dst, use_serial_batch_fields: 1, batch_no: a.batch,
            material_request: mr.name, material_request_item: r.row
          });
        });
      } else {
        items.push({
          item_code: r.item_code, qty: r.qty, uom: r.uom, conversion_factor: r.cf || 1,
          s_warehouse: src, t_warehouse: dst,
          material_request: mr.name, material_request_item: r.row
        });
      }
    }
    if (thieu.length) { busy(0); return toast('Kho ' + shortWh(src) + ' không đủ lô hàng: ' + thieu.join('; '), 7000); }
    if (!items.length) { busy(0); return toast('Không có dòng nào để nhập kho'); }

    var doc = {
      doctype: 'Stock Entry', company: COMPANY,
      stock_entry_type: 'Material Transfer', purpose: 'Material Transfer',
      set_posting_time: 1, posting_date: today(), posting_time: nowStamp().slice(11),
      from_warehouse: src, to_warehouse: dst, items: items,
      remarks: (opt.remarks || 'Nhận hàng điều chuyển nội bộ trên app - phiếu ') + mr.name + ' - ' + (S.me.full_name || S.user)
    };
    var ins = await api('frappe.client.insert', { doc: doc });
    await api('frappe.client.submit', { doc: ins });
    busy(0);
    toast('Đã nhập kho ' + shortWh(dst) + ' theo phiếu ' + mr.name + ' (' + ins.name + ')', 4500);
    back();
    setTimeout(function () { render(); }, 60);
  } catch (err) { busy(0); toast(errMsg(err), 6000); }
}

function errMsg(e) {
  var m = (e && (e.message || e._server_messages || '')) + '';
  try { var a = JSON.parse(e._server_messages); m = JSON.parse(a[0]).message; } catch (x) { }
  return (m || 'Có lỗi xảy ra').replace(/<[^>]*>/g, '').slice(0, 180);
}

/* ---------- 7. Tao moi: buoc 1 thong tin chung ---------- */
function startDraft(T) {
  S.draft = {
    T: T, type: T.key,
    schedule_date: addDays(today(), 1),
    time: T.key === 'Manufacture' ? '06:00' : '08:00',
    set_warehouse: '', set_from_warehouse: '',
    bo_phan: S.me.bo_phan || '', nguoi_yeu_cau: S.me.full_name || S.user, note: '',
    bep_nhan: '', items: [], photos: []
  };
  var pref = { Purchase: 'Kho tổng 307 - TV', 'Material Transfer': '', Manufacture: '' };
  if (S.wh.indexOf(pref[T.key]) >= 0) S.draft.set_warehouse = pref[T.key];
  if (T.key === 'Manufacture') S.draft.bep_nhan = myKitchen() || '';
  go(scrStep1);
}

var TIMES = ['05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '14:00', '16:00', '18:00'];

function scrStep1() {
  var d = S.draft, T = d.T;
  function fld(icon, label, val, ph, act) {
    return '<div class="fld" data-a="' + act + '"><div class="fi">' + icon + '</div>' +
      '<div class="ft"><div class="fl">' + h(label) + '</div>' +
      '<div class="fv' + (val ? '' : ' ph') + '">' + h(val || ph) + '</div></div>' +
      '<div class="fc">&#8250;</div></div>';
  }
  var html = '<div class="card">' +
    (T.needFrom ? fld('📤', 'Kho xuất hàng', shortWh(d.set_from_warehouse), 'Chọn kho lấy hàng', 'from') : '') +
    (T.needFrom && laKhoCuaToi(d.set_from_warehouse) ? '<div style="margin:10px 0 0;padding:12px 14px;border-radius:14px;background:#fff6e5;color:#8a5b00;font-size:13px;line-height:1.5">Kho này do bạn phụ trách, không cần xin ai. <b onclick="vgbLapPhieuChuyen(\'' + h(d.set_from_warehouse) + '\', \'' + h(d.set_warehouse || '') + '\')" style="text-decoration:underline">Lập thẳng phiếu điều chuyển</b></div>' : '') +
    fld('📥', T.key === 'Manufacture' ? 'Kho nhận bánh' : 'Kho nhận hàng', shortWh(d.set_warehouse), 'Chọn kho nhận', 'to') +
    (T.key === 'Manufacture' ? fld('🧑‍🍳', 'Gửi yêu cầu đến bếp', d.bep_nhan, 'Bắt buộc - chọn bếp', 'bep') : '') +
    fld('📅', 'Ngày cần', dmy(d.schedule_date), '', 'date') +
    '</div>' +
    (T.key === 'Manufacture' && !d.bep_nhan ?
      '<div style="padding:2px 16px 0;font-size:12.5px;color:#8a8f9c;line-height:1.5">Bếp nào được gửi thì bếp đó mới thấy phiếu.</div>' : '') +
    (T.hasTime ?
      '<div class="card"><div style="padding:14px 14px 4px"><div class="fl" style="font-size:12px;color:#8a8f9c;margin-bottom:8px">' + h(T.timeLabel) + ' (áp dụng cho cả phiếu)</div>' +
      '<input type="time" class="tin" id="t1time" value="' + h(hm(d.time)) + '" step="60">' +
      '<div class="tch">' + TIMES.map(function (t) { return '<span data-t="' + t + '"' + (t === hm(d.time) ? ' class="on"' : '') + '>' + t + '</span>'; }).join('') + '</div></div>' +
      '<div style="padding:10px 14px 14px;font-size:12.5px;color:#8a8f9c;line-height:1.5">Từng món có thể đổi giờ riêng ở bước sau.</div></div>'
      : '') +
    '<div class="sec">Người yêu cầu</div><div class="card">' +
    fld('🏢', 'Bộ phận yêu cầu', shortDep(d.bo_phan), 'Bắt buộc - chọn bộ phận', 'dept') +
    '<div class="fld" style="cursor:default"><div class="fi">👤</div><div class="ft">' +
    '<div class="fl">Người yêu cầu</div><div class="fv">' + h(d.nguoi_yeu_cau) + '</div></div></div>' +
    '</div>';

  var b = frame(T.title, html, { footer: '<button class="btn" id="t1next">Tiếp tục</button>' });
  var ti = document.getElementById('t1time');
  if (ti) ti.onchange = function () { d.time = hm(ti.value); scrStep1(); };
  b.onclick = function (e) {
    var t = e.target.closest('[data-t]'); if (t) { d.time = t.dataset.t; return scrStep1(); }
    var a = e.target.closest('[data-a]'); if (!a) return;
    var k = a.dataset.a;
    if (k === 'from') sheet('Kho xuất hàng', whOpts(), d.set_from_warehouse, function (o) { d.set_from_warehouse = o.value; scrStep1(); }, true);
    if (k === 'to') sheet('Kho nhận hàng', whOpts(), d.set_warehouse, function (o) { d.set_warehouse = o.value; scrStep1(); }, true);
    if (k === 'bep') {
      var bo = [];
      BEPS.forEach(function (x) { bo.push({ value: x, label: x, icon: '🧑‍🍳' }); });
      sheet('Gửi yêu cầu đến bếp', bo, d.bep_nhan, function (o) { d.bep_nhan = o.value; scrStep1(); }, true);
    }
    if (k === 'dept') {
      sheet('Bộ phận yêu cầu', DEPTS.map(function (x) { return { value: x, label: shortDep(x) }; }), d.bo_phan, function (o) {
        d.bo_phan = o.value;
        S.me.bo_phan = o.value;
        if (syncUser()) {
          try { localStorage.setItem('vgb_bp_' + S.user, o.value); } catch (x) { }
          api('frappe.client.set_value', { doctype: 'User', name: S.user, fieldname: 'custom_phong_ban', value: o.value }).catch(function () { });
        }
        scrStep1();
      }, true);
    }
    if (k === 'date') {
      var opts = [];
      for (var i = 0; i <= 14; i++) { var iso = addDays(today(), i); opts.push({ value: iso, label: dmy(iso) + (i === 0 ? ' (hôm nay)' : i === 1 ? ' (ngày mai)' : '') }); }
      sheet('Ngày cần hàng', opts, d.schedule_date, function (o) { d.schedule_date = o.value; scrStep1(); });
    }
  };
  document.getElementById('t1next').onclick = function () {
    if (T.needFrom && !d.set_from_warehouse) return toast('Chưa chọn kho xuất hàng');
    if (!d.set_warehouse) return toast('Chưa chọn kho nhận hàng');
    if (T.key === 'Manufacture' && !d.bep_nhan) return toast('Chưa chọn bếp nhận yêu cầu');
    if (!d.bo_phan) return toast('Chưa chọn bộ phận yêu cầu');
    go(scrStep2);
  };
}

/* ---------- 8. Buoc 2: chon hang hoa ---------- */
var pick = { group: '', q: '', cache: {}, sel: {}, nm: {}, allow: null, seq: 0 };
async function scrStep2() {
  var d = S.draft;
  pick.sel = {}; pick.nm = {};
  (d.items || []).forEach(function (it) { pick.sel[it.item_code] = 1; pick.nm[it.item_code] = it.item_name; });
  pick.cache = {}; pick.group = ''; pick.q = '';
  pick.allow = leavesUnder(d.T.roots);
  await drawPick(true);
}

/* dung danh sach hang hoa day du tu [{item_code, qty, uom, note, time}] */
async function buildItems(reqs, existing) {
  var d = S.draft;
  existing = existing || [];
  var codes = reqs.map(function (r) { return r.item_code; });
  var keep = existing.filter(function (it) { return codes.indexOf(it.item_code) >= 0; });
  var have = keep.map(function (it) { return it.item_code; });
  var need = codes.filter(function (c) { return have.indexOf(c) < 0; });
  if (need.length) {
    var meta = await getList('Item', { fields: ['name', 'item_name', 'stock_uom', 'purchase_uom', 'item_group', 'image', 'custom_bep_phu_trach'], filters: { name: ['in', need] }, limit_page_length: 500 });
    var conv = await getList('UOM Conversion Detail', { parent: 'Item', fields: ['parent', 'uom', 'conversion_factor'], filters: { parent: ['in', need], parenttype: 'Item' }, limit_page_length: 500 });
    var bins = await getList('Bin', { fields: ['item_code', 'actual_qty'], filters: { item_code: ['in', need], warehouse: 'Kho tổng 307 - TV' }, limit_page_length: 500 });
    var bm = {}; bins.forEach(function (x) { bm[x.item_code] = x.actual_qty; });
    var rq = {}; reqs.forEach(function (r) { rq[r.item_code] = r; });
    meta.forEach(function (m) {
      var us = conv.filter(function (c) { return c.parent === m.name; }).map(function (c) { return { uom: c.uom, cf: c.conversion_factor }; });
      if (!us.some(function (u) { return u.uom === m.stock_uom; })) us.unshift({ uom: m.stock_uom, cf: 1 });
      var r = rq[m.name] || {};
      var dfl = (m.purchase_uom && us.some(function (u) { return u.uom === m.purchase_uom; })) ? m.purchase_uom : m.stock_uom;
      var uom = (r.uom && us.some(function (u) { return u.uom === r.uom; })) ? r.uom : dfl;
      var cf = (us.filter(function (u) { return u.uom === uom; })[0] || { cf: 1 }).cf;
      keep.push({
        item_code: m.name, item_name: m.item_name, image: m.image || '',
        item_group: m.item_group || '', bep: m.custom_bep_phu_trach || '',
        stock_uom: m.stock_uom, uom: uom, cf: cf, uoms: us,
        qty: (r.qty > 0 ? r.qty : 1), time: hm(r.time || d.time), note: r.note || '', ton: bm[m.name] || 0
      });
    });
  }
  keep.sort(function (a, b2) { return codes.indexOf(a.item_code) - codes.indexOf(b2.item_code); });
  return keep;
}

/* lay hang hoa tu mau don da luu */
async function loadTemplate() {
  var d = S.draft;
  var tpls = [];
  busy(1);
  try {
    tpls = await getList('VGB Order Template', { fields: ['name', 'template_name', 'items_json', 'bo_phan'], filters: { request_type: d.type }, limit_page_length: 100, order_by: 'template_name' });
  } catch (e) { busy(0); return toast(errMsg(e)); }
  busy(0);
  if (!tpls.length) return toast('Chưa có mẫu nào cho loại phiếu này');
  /* bang chon mau tu dung, moi dong co nut doi ten va xoa (Uyen/De yeu cau 07/08) */
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>Mẫu đơn đã lưu</b><div class="x">&times;</div></div>' +
    '<div style="padding:2px 14px 6px;display:flex;gap:8px"><input class="nt" placeholder="Tìm nhanh..." style="height:46px;padding:0 12px;flex:1"></div>' +
    '<div style="padding:0 14px 6px;color:#a0a6b4;font-size:12.5px">Bấm tên mẫu để lấy món vào phiếu. Mẫu dùng chung cả tiệm, xoá là mất với mọi người.</div>' +
    '<div class="shl"></div>';
  var lst = box.querySelector('.shl');
  var q0 = '';
  function veDs() {
    var f = tpls.filter(function (t) { return !q0 || (t.template_name + ' ' + (t.bo_phan || '')).toLowerCase().indexOf(q0) >= 0; });
    lst.innerHTML = f.length ? f.map(function (t) {
      var i = tpls.indexOf(t);
      return '<div class="shi" data-i="' + i + '"><span>📋</span>' +
        '<span style="flex:1;min-width:0">' + h(t.template_name) +
        (t.bo_phan ? '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(t.bo_phan) + '</div>' : '') + '</span>' +
        '<button class="nt" data-s="' + i + '" title="Đổi tên mẫu" style="height:40px;width:46px;flex:none;font-size:16px;cursor:pointer">✏️</button>' +
        '<button class="nt" data-x="' + i + '" title="Xoá mẫu" style="height:40px;width:46px;flex:none;font-size:16px;cursor:pointer;margin-left:6px;color:#b91c1c">🗑️</button></div>';
    }).join('') : '<div class="emp"><div class="e2">Không tìm thấy</div></div>';
  }
  veDs();
  ov.appendChild(box); document.body.appendChild(ov);
  var tim = box.querySelector('input');
  tim.oninput = function () { q0 = (tim.value || '').toLowerCase(); veDs(); };
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  lst.onclick = async function (e) {
    var bs = e.target.closest('[data-s]');
    if (bs) {
      var ts = tpls[+bs.dataset.s];
      var nm2 = await promptSheet('Đổi tên mẫu "' + ts.template_name + '"', ts.template_name);
      if (!nm2 || nm2 === ts.template_name) return;
      busy(1);
      try {
        await api('frappe.client.set_value', { doctype: 'VGB Order Template', name: ts.name, fieldname: 'template_name', value: nm2 });
        ts.template_name = nm2; veDs(); toast('Đã đổi tên mẫu');
      } catch (err) { toast(errMsg(err), 4200); } finally { busy(0); }
      return;
    }
    var bx = e.target.closest('[data-x]');
    if (bx) {
      var tx = tpls[+bx.dataset.x];
      var chac = await confirmSheet('Xoá mẫu "' + tx.template_name + '"?', 'Mẫu dùng chung cả tiệm, xoá rồi là mất với mọi người, không lấy lại được.', 'Xoá mẫu', true);
      if (!chac) return;
      busy(1);
      try {
        await api('frappe.client.delete', { doctype: 'VGB Order Template', name: tx.name });
        tpls.splice(tpls.indexOf(tx), 1); veDs(); toast('Đã xoá mẫu "' + tx.template_name + '"');
      } catch (err) { toast(errMsg(err), 4200); } finally { busy(0); }
      return;
    }
    var r = e.target.closest('.shi'); if (!r) return;
    var t = tpls[+r.dataset.i];
    var arr = [];
    try { arr = JSON.parse(t.items_json || '[]'); } catch (e2) { }
    if (!arr.length) return toast('Mẫu này không có hàng hoá');
    dong();
    busy(1);
    try {
      d.items = await buildItems(arr, d.items);
      arr.forEach(function (r2) { pick.sel[r2.item_code] = 1; });
      (d.items || []).forEach(function (it) { pick.nm[it.item_code] = it.item_name; });
      toast('Đã lấy ' + arr.length + ' món từ mẫu ' + t.template_name);
      go(scrStep3);
    } catch (err) { toast(errMsg(err)); } finally { busy(0); }
  };
}
function selInner() {
  var selc = Object.keys(pick.sel).filter(function (k) { return pick.sel[k]; });
  if (!selc.length) return '';
  return '<div class="selh">Đã chọn (' + selc.length + ')</div><div class="sell">' +
    selc.map(function (c) {
      return '<div class="selc" data-r="' + h(c) + '">' + h(pick.nm[c] || c) + '<span>&times;</span></div>';
    }).join('') + '</div>';
}
function paintSel() {
  var n = Object.keys(pick.sel).filter(function (k) { return pick.sel[k]; }).length;
  var w = document.getElementById('selw');
  if (w) { w.innerHTML = selInner(); w.style.display = n ? '' : 'none'; }
  var bt = document.getElementById('p2next');
  if (bt) { bt.disabled = !n; bt.textContent = 'Tiếp tục' + (n ? ' (' + n + ')' : ''); }
}
async function drawPick(fetch) {
  var d = S.draft;
  var key = pick.group || '*';
  var qs = (pick.q || '').trim();
  var qk = qs.length >= 2 ? 'q|' + key + '|' + qs.toLowerCase() : null;
  var ck = qk || key;
  if ((qk && !pick.cache[qk]) || (!qk && fetch && !pick.cache[key])) {
    var myq = ++pick.seq;
    if (!qk) frame('Chọn hàng hoá', '<div class="emp"><div class="e1">⏳</div></div>');
    var f = { disabled: 0, has_variants: 0 };
    if (pick.group) f.item_group = pick.group;
    else if (pick.allow && pick.allow.length) f.item_group = ['in', pick.allow];
    if (d.type === 'Purchase') f.is_purchase_item = 1;
    var ar = { fields: ['name', 'item_name', 'item_group', 'stock_uom', 'image'], filters: f, limit_page_length: 500, order_by: 'item_name' };
    if (qk) { ar.or_filters = { item_name: ['like', '%' + qs + '%'], name: ['like', '%' + qs + '%'] }; ar.limit_page_length = 300; }
    var res = [];
    try { res = await getList('Item', ar); } catch (e) { toast(errMsg(e)); }
    if (myq !== pick.seq) return;
    pick.cache[ck] = res;
  }
  var all = pick.cache[ck] || [];
  all.forEach(function (it) { if (!pick.nm[it.name]) pick.nm[it.name] = it.item_name; });
  var q = qs.toLowerCase();
  var rows = qk ? all.slice(0, 300)
    : all.filter(function (it) { return !q || (it.item_name + ' ' + it.name).toLowerCase().indexOf(q) >= 0; }).slice(0, 300);
  var nsel = Object.keys(pick.sel).filter(function (k) { return pick.sel[k]; }).length;
  var selHtml = '<div class="selw" id="selw"' + (nsel ? '' : ' style="display:none"') + '>' + selInner() + '</div>';
  var html = '<div class="card"><div class="fld" data-g><div class="fi">🏷️</div><div class="ft">' +
    '<div class="fl">Nhóm hàng hoá</div><div class="fv">' + h(pick.group || 'Tất cả') + '</div></div><div class="fc">&#8250;</div></div></div>' +
    srchBox('pq', 'Tìm theo tên hoặc mã', pick.q, true) + selHtml +
    '<button class="btn gh" id="p2tpl" style="margin-bottom:12px">📋 Lấy từ mẫu đã lưu</button>' +
    (rows.length ? '<div class="lst">' + rows.map(function (it) {
      return '<div class="li" data-c="' + h(it.name) + '">' +
        (it.image ? '<img class="im" src="' + h(it.image) + '" loading="lazy">' : '<div class="im imp">🍰</div>') +
        '<div class="lt"><div class="l1">' + h(it.item_name) + '</div>' +
        '<div class="l2">Mã: ' + h(it.name) + ' &middot; ' + h(it.stock_uom) + '</div></div>' +
        '<div class="ck' + (pick.sel[it.name] ? ' on' : '') + '">&#10003;</div></div>';
    }).join('') + '</div>' : '<div class="emp"><div class="e1">🔎</div><div class="e2">Không tìm thấy hàng hoá</div></div>');

  var b = frame('Chọn hàng hoá', html, { footer: '<button class="btn" id="p2next"' + (nsel ? '' : ' disabled') + '>Tiếp tục' + (nsel ? ' (' + nsel + ')' : '') + '</button>' });
  var pq = document.getElementById('pq');
  var tmr = null;
  pq.oninput = function () { pick.q = pq.value; clearTimeout(tmr); tmr = setTimeout(async function () { var v = pick.q; await drawPick(false); var i = document.getElementById('pq'); if (!i) return; i.focus(); i.value = v; i.setSelectionRange(v.length, v.length); }, 260); };
  document.getElementById('pqscan').onclick = async function () {
    var added = 0, miss = 0;
    await scanBarcode(async function (code) {
      var ic = null;
      try { ic = await itemByBarcode(code); } catch (e) { }
      if (!ic) { miss++; return '❌ Không có hàng hoá cho mã ' + code; }
      if (pick.sel[ic]) return '• Đã có trong danh sách: ' + (pick.nm[ic] || ic);
      if (!pick.nm[ic]) {
        try {
          var mm = await getList('Item', { fields: ['name', 'item_name'], filters: { name: ic }, limit_page_length: 1 });
          if (mm && mm.length) pick.nm[ic] = mm[0].item_name;
        } catch (e) { }
      }
      pick.sel[ic] = 1; added++;
      return '✅ ' + (pick.nm[ic] || ic) + '  (đã thêm ' + added + ')';
    });
    if (added) { await drawPick(false); toast('Đã thêm ' + added + ' món từ mã vạch'); }
    else if (miss) toast('Không tìm thấy hàng hoá có mã vạch này');
  };
  document.getElementById('p2tpl').onclick = function () { loadTemplate(); };
  b.onclick = function (e) {
    if (e.target.closest('[data-g]')) {
      var gl = (pick.allow && pick.allow.length) ? pick.allow : S.groups;
      var opts = [{ value: '', label: 'Tất cả' }].concat(gl.map(function (g) { return { value: g, label: g }; }));
      return sheet('Nhóm hàng hoá', opts, pick.group, function (o) { pick.group = o.value; pick.q = ''; drawPick(true); }, true);
    }
    var rm = e.target.closest('[data-r]');
    if (rm) {
      var rc = rm.dataset.r;
      pick.sel[rc] = 0;
      var row = document.querySelector('#vgb .li[data-c="' + rc.replace(/"/g, '\\"') + '"]');
      if (row) row.querySelector('.ck').classList.remove('on');
      return paintSel();
    }
    var r = e.target.closest('[data-c]'); if (!r) return;
    var c = r.dataset.c;
    pick.sel[c] = pick.sel[c] ? 0 : 1;
    r.querySelector('.ck').classList.toggle('on', !!pick.sel[c]);
    paintSel();
  };
  document.getElementById('p2next').onclick = async function () {
    var codes = Object.keys(pick.sel).filter(function (k) { return pick.sel[k]; });
    busy(1);
    try {
      d.items = await buildItems(codes.map(function (c) { return { item_code: c }; }), d.items);
      go(scrStep3);
    } catch (err) { toast(errMsg(err)); } finally { busy(0); }
  };
}

/* ---------- 9. Buoc 3: danh sach da chon ---------- */
function qdText(it) {
  return (it.uom === it.stock_uom || !(it.cf > 0) || it.cf === 1)
    ? '1 ' + it.uom + ' (gốc)'
    : '1 ' + it.uom + ' = ' + num(it.cf) + ' ' + it.stock_uom;
}
function setQty(b, i, v) {
  var el = b.querySelector('[data-q="' + i + '"]');
  if (el) el.value = v;
}
function scrStep3() {
  var d = S.draft, T = d.T;
  var rows = d.items.map(function (it, i) {
    var uomSel = '<select class="uom" data-u="' + i + '">' + (it.uoms || [{ uom: it.stock_uom, cf: 1 }]).map(function (u) {
      return '<option value="' + h(u.uom) + '"' + (u.uom === it.uom ? ' selected' : '') + '>' + h(u.uom) + '</option>';
    }).join('') + '</select>';
    var img = it.image ? '<img class="im3" src="' + h(it.image) + '" alt="">' : '<div class="im3 im3p">🍰</div>';
    var qd = h(qdText(it));
    return '<div class="ic1">' +
      '<div class="ih"><div class="n">' + (i + 1) + '</div>' + img +
      '<div class="in">' + h(it.item_name) + '<div class="ig">Mã: ' + h(it.item_code) + '</div></div>' +
      '<div class="del" data-x="' + i + '" title="Xoá món này">&times;</div></div>' +
      '<div class="stk"><div><div class="s1">Tồn kho tổng 307</div><div class="s2">' + num(it.ton) + ' ' + h(it.stock_uom) + '</div></div>' +
      '<div><div class="s1">Quy đổi</div><div class="s2">' + qd + '</div></div></div>' +
      '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số lượng đặt</div>' +
      '<div class="qr"><div class="stp"><button data-m="' + i + '">&minus;</button>' +
      '<input type="number" inputmode="decimal" data-q="' + i + '" value="' + it.qty + '"><button data-p="' + i + '">+</button></div>' + uomSel + '</div></div></div>' +
      (T.hasTime ?
        '<div class="tw"><div class="lb">' + h(T.timeLabel) + '</div>' +
        '<input type="time" class="tin" data-t="' + i + '" value="' + h(hm(it.time)) + '" step="60">' +
        '<div class="tch">' + TIMES.map(function (t) { return '<span data-tc="' + i + '_' + t + '"' + (t === hm(it.time) ? ' class="on"' : '') + '>' + t + '</span>'; }).join('') + '</div></div>'
        : '') +
      '<div class="tw"><textarea class="nt" rows="2" data-n="' + i + '" placeholder="Ghi chú cho món này...">' + h(it.note) + '</textarea></div>' +
      '</div>';
  }).join('');
  var b = frame('Danh sách đã chọn', (d.items.length ? rows : '<div class="emp"><div class="e1">🧺</div><div class="e2">Chưa chọn món nào</div></div>') +
    '<button class="btn gh" id="s3add" style="margin-top:4px">+ Thêm hàng hoá</button>' +
    (d.items.length ? '<button class="btn gh" id="s3tpl" style="margin-top:9px">💾 Lưu danh sách này thành mẫu</button>' : ''),
    { footer: '<button class="btn" id="s3next"' + (d.items.length ? '' : ' disabled') + '>Tiếp tục</button>' });

  b.addEventListener('input', function (e) {
    var t = e.target;
    if (t.dataset.q != null) { d.items[+t.dataset.q].qty = parseFloat(t.value) || 0; }
    if (t.dataset.n != null) { d.items[+t.dataset.n].note = t.value; }
    if (t.dataset.t != null) { var i = +t.dataset.t; var tv = hm(t.value); d.items[i].time = tv; syncChips(b, i, tv); }
  });
  b.addEventListener('change', function (e) {
    var t = e.target;
    if (t.dataset.u != null) {
      var i = +t.dataset.u, it = d.items[i];
      it.uom = t.value;
      var u = (it.uoms || []).filter(function (x) { return x.uom === t.value; })[0];
      it.cf = u ? u.cf : 1;
      var card = t.closest('.ic1');
      var cell = card ? card.querySelectorAll('.stk .s2')[1] : null;
      if (cell) { cell.textContent = qdText(it); } else { scrStep3(); }
    }
  });
  b.addEventListener('click', function (e) {
    var t = e.target.closest('[data-x],[data-m],[data-p],[data-tc]'); if (!t) return;
    if (t.dataset.x != null) {
      var sc = b.scrollTop;
      d.items.splice(+t.dataset.x, 1);
      scrStep3();
      var nb = document.getElementById('vgbBody');
      if (nb) nb.scrollTop = sc;
      return;
    }
    if (t.dataset.m != null) { var i = +t.dataset.m; d.items[i].qty = Math.max(0, Math.round((d.items[i].qty - 1) * 1000) / 1000); return setQty(b, i, d.items[i].qty); }
    if (t.dataset.p != null) { var j = +t.dataset.p; d.items[j].qty = Math.round((d.items[j].qty + 1) * 1000) / 1000; return setQty(b, j, d.items[j].qty); }
    if (t.dataset.tc != null) {
      var p = t.dataset.tc.split('_'); var k = +p[0];
      d.items[k].time = p[1];
      b.querySelector('[data-t="' + k + '"]').value = p[1];
      syncChips(b, k, p[1]);
    }
  });
  document.getElementById('s3add').onclick = function () { go(scrStep2, true); };
  var s3t = document.getElementById('s3tpl');
  if (s3t) s3t.onclick = async function () {
    var nm = await promptSheet('Tên mẫu đơn hàng', 'VD: Đơn NVL hàng tuần - Bếp Baker');
    if (!nm) return;
    var noiDung = JSON.stringify(d.items.map(function (it) {
      return { item_code: it.item_code, qty: it.qty, uom: it.uom, note: it.note || '', time: it.time };
    }));
    busy(1);
    try {
      /* trung ten voi mau cu cung loai phieu thi hoi ghi de, do la cach SUA noi dung mau */
      var cu = await getList('VGB Order Template', { fields: ['name'], filters: { template_name: nm, request_type: d.type }, limit_page_length: 1 });
      if (cu.length) {
        busy(0);
        var ghiDe = await confirmSheet('Đã có mẫu tên "' + nm + '"', 'Ghi đè mẫu cũ bằng danh sách món hiện tại? Mẫu dùng chung cả tiệm.', 'Ghi đè mẫu cũ');
        if (!ghiDe) return;
        busy(1);
        await api('frappe.client.set_value', { doctype: 'VGB Order Template', name: cu[0].name, fieldname: { items_json: noiDung, bo_phan: shortDep(d.bo_phan) || '' } });
        toast('Đã cập nhật mẫu "' + nm + '"', 3200);
      } else {
        await api('frappe.client.insert', {
          doc: {
            doctype: 'VGB Order Template', template_name: nm, request_type: d.type,
            bo_phan: shortDep(d.bo_phan) || undefined, dung_chung: 1,
            items_json: noiDung
          }
        });
        toast('Đã lưu mẫu "' + nm + '"', 3200);
      }
    } catch (err) { toast(errMsg(err), 4200); } finally { busy(0); }
  };
  document.getElementById('s3next').onclick = function () {
    if (d.items.some(function (it) { return !(it.qty > 0); })) return toast('Có món chưa nhập số lượng');
    go(scrStep4);
  };
}
function syncChips(b, i, v) {
  b.querySelectorAll('[data-tc^="' + i + '_"]').forEach(function (s) { s.classList.toggle('on', s.dataset.tc === i + '_' + v); });
}

/* ---------- 10. Buoc 4: xem lai va luu ---------- */
function scrStep4() {
  var d = S.draft, T = d.T;
  var times = {};
  d.items.forEach(function (it) { var k = hm(it.time); times[k] = (times[k] || 0) + 1; });
  var tSum = Object.keys(times).sort().map(function (t) { return t + ' (' + times[t] + ')'; }).join(', ');
  var lines = d.items.map(function (it, i) {
    return '<div class="kv"><span style="flex:1;color:#16181d;text-align:left">' + (i + 1) + '. ' + h(it.item_name) + '</span>' +
      '<b style="flex:0 0 auto">' + num(it.qty) + ' ' + h(it.uom) + (T.hasTime ? ' &middot; ' + h(hm(it.time)) : '') + '</b></div>';
  }).join('');
  var photos = d.photos.map(function (p, i) { return '<img src="' + p.url + '" data-rm="' + i + '">'; }).join('');
  var html = '<div class="card">' +
    '<div class="kv"><span>Loại phiếu</span><b>' + h(T.title) + '</b></div>' +
    (d.set_from_warehouse ? '<div class="kv"><span>Kho xuất</span><b>' + h(shortWh(d.set_from_warehouse)) + '</b></div>' : '') +
    '<div class="kv"><span>Kho nhận</span><b>' + h(shortWh(d.set_warehouse)) + '</b></div>' +
    '<div class="kv"><span>Ngày cần</span><b>' + dmy(d.schedule_date) + '</b></div>' +
    (T.hasTime ? '<div class="kv"><span>' + h(T.timeLabel) + '</span><b>' + h(tSum) + '</b></div>' : '') +
    '<div class="kv"><span>Bộ phận yêu cầu</span><b>' + h(shortDep(d.bo_phan)) + '</b></div>' +
    '<div class="kv"><span>Người yêu cầu</span><b>' + h(d.nguoi_yeu_cau) + '</b></div>' +
    '</div>' +
    '<div class="sec">' + d.items.length + ' hàng hoá</div><div class="card">' + lines + '</div>' +
    '<div class="sec">Ghi chú chung</div><div class="card"><div style="padding:12px 14px">' +
    '<textarea class="nt" id="s4note" rows="3" placeholder="Ghi chú cho cả phiếu...">' + h(d.note) + '</textarea></div>' +
    '<div class="att">' + photos + '<div class="ph" id="s4cam"><div style="font-size:22px">📷</div>Thêm ảnh</div></div></div>' +
    '<input type="file" accept="image/*" id="s4file" style="display:none">';
  var b = frame('Xem lại phiếu', html, {
    footer: '<div class="row2"><button class="btn gh" id="s4save">Lưu nháp</button><button class="btn" id="s4send">Lưu và gửi</button></div>'
  });
  var fi = document.getElementById('s4file');
  document.getElementById('s4cam').onclick = function () { fi.click(); };
  fi.onchange = function () { if (fi.files[0]) addPhoto(fi.files[0]); };
  b.onclick = function (e) {
    var r = e.target.closest('[data-rm]');
    if (r) { d.photos.splice(+r.dataset.rm, 1); scrStep4(); }
  };
  document.getElementById('s4save').onclick = function () { d.note = document.getElementById('s4note').value; saveDraft(0); };
  document.getElementById('s4send').onclick = function () { d.note = document.getElementById('s4note').value; saveDraft(1); };
}

function addPhoto(file) {
  var fr = new FileReader();
  fr.onload = function () {
    var img = new Image();
    img.onload = function () {
      var mx = 1280, w = img.width, ht = img.height;
      if (w > mx || ht > mx) { var s = mx / Math.max(w, ht); w = Math.round(w * s); ht = Math.round(ht * s); }
      var cv = document.createElement('canvas'); cv.width = w; cv.height = ht;
      cv.getContext('2d').drawImage(img, 0, 0, w, ht);
      var url = cv.toDataURL('image/jpeg', 0.72);
      S.draft.photos.push({ url: url, b64: url.split(',')[1], name: 'anh-' + (S.draft.photos.length + 1) + '.jpg' });
      scrStep4();
    };
    img.src = fr.result;
  };
  fr.readAsDataURL(file);
}

async function saveDraft(submitIt) {
  var d = S.draft, T = d.T;
  busy(1);
  try {
    var doc = {
      doctype: 'Material Request', naming_series: 'MAT-MR-.YYYY.-', company: COMPANY,
      material_request_type: T.key, transaction_date: today(), schedule_date: d.schedule_date,
      set_warehouse: d.set_warehouse || undefined,
      set_from_warehouse: d.set_from_warehouse || undefined,
      bo_phan_yeu_cau: shortDep(d.bo_phan) || undefined,
      nguoi_yeu_cau: d.nguoi_yeu_cau || undefined,
      custom_bep_nhan: (T.key === 'Manufacture' ? d.bep_nhan : '') || undefined,
      items: d.items.map(function (it) {
        return {
          doctype: 'Material Request Item', item_code: it.item_code, item_name: it.item_name,
          qty: it.qty, uom: it.uom, stock_uom: it.stock_uom, conversion_factor: it.cf || 1,
          schedule_date: d.schedule_date,
          gio_can_lay: T.hasTime ? (hm(it.time) + ':00') : undefined,
          warehouse: d.set_warehouse || undefined,
          from_warehouse: d.set_from_warehouse || undefined,
          description: (it.note ? it.item_name + ' - ' + it.note : it.item_name)
        };
      })
    };
    var saved = await api('frappe.client.insert', { doc: doc });
    if (d.note) {
      try { await api('frappe.desk.form.utils.add_comment', { reference_doctype: 'Material Request', reference_name: saved.name, content: d.note, comment_email: S.user, comment_by: S.user }); } catch (e) { }
    }
    for (var i = 0; i < d.photos.length; i++) {
      try {
        await api('frappe.client.insert', {
          doc: {
            doctype: 'File', file_name: saved.name + '-' + d.photos[i].name, is_private: 0,
            attached_to_doctype: 'Material Request', attached_to_name: saved.name,
            content: d.photos[i].b64, decode: 1
          }
        });
      } catch (e) { }
    }
    if (submitIt) {
      var full = await api('frappe.client.get', { doctype: 'Material Request', name: saved.name });
      await api('frappe.client.submit', { doc: full });
    }
    busy(0);
    toast('Đã lưu phiếu ' + saved.name, 3200);
    S.draft = null;
    reset(scrHome);
    go(function () { scrMRList(T); });
  } catch (err) { busy(0); toast(errMsg(err), 4200); }
}

/* ---------- 11. Duyet phieu chi ---------- */
var PAYFLOW = [
  { state: 'Nháp', action: 'Gửi kiểm tra', next: 'Chờ FIN kiểm tra', role: 'AP Officer', ok: 1 },
  { state: 'Chờ FIN kiểm tra', action: 'Xác nhận hợp lệ', next: 'Chờ giám đốc duyệt', role: 'AP Kiểm soát (FIN)', ok: 1 },
  { state: 'Chờ FIN kiểm tra', action: 'Trả lại', next: 'Bị trả lại', role: 'AP Kiểm soát (FIN)', ok: 0 },
  { state: 'Chờ giám đốc duyệt', action: 'Duyệt chi', next: 'Đã duyệt - Đã ghi sổ', role: 'AP Giám đốc', ok: 1 },
  { state: 'Chờ giám đốc duyệt', action: 'Trả lại', next: 'Bị trả lại', role: 'AP Giám đốc', ok: 0 },
  { state: 'Bị trả lại', action: 'Gửi kiểm tra', next: 'Chờ FIN kiểm tra', role: 'AP Officer', ok: 1 }
];
function myPayStates() {
  var s = [];
  PAYFLOW.forEach(function (t) { if (hasRole(t.role) && s.indexOf(t.state) < 0) s.push(t.state); });
  return s.length ? s : ['__none__'];
}
function myPayRoleLabel() {
  if (hasRole('AP Giám đốc')) return 'Giám đốc duyệt chi';
  if (hasRole('AP Kiểm soát (FIN)')) return 'Kiểm soát tài chính';
  return 'Lập và gửi phiếu chi';
}
var payTab = '';
async function scrPayList() {
  frame('Duyệt phiếu chi', '<div class="emp"><div class="e1">⏳</div></div>');
  var mine = myPayStates();
  var docs = await getList('Payment Entry', {
    fields: ['name', 'posting_date', 'party_name', 'party', 'paid_amount', 'workflow_state', 'mode_of_payment', 'custom_loai_chi', 'remarks', 'owner'],
    filters: { workflow_state: ['in', mine] }, limit_page_length: 60, order_by: 'posting_date desc, name desc'
  });
  var done = await getList('Payment Entry', {
    fields: ['name', 'posting_date', 'party_name', 'paid_amount', 'workflow_state'],
    filters: { workflow_state: ['in', ['Đã duyệt - Đã ghi sổ', 'Bị trả lại']] }, limit_page_length: 25, order_by: 'modified desc'
  });
  if (!payTab) payTab = mine[0] || 'Xong';
  function draw() {
    var tabs = mine.concat(['Đã xử lý']);
    var chips = tabs.map(function (s) {
      var c = s === 'Đã xử lý' ? done.length : docs.filter(function (d) { return d.workflow_state === s; }).length;
      return '<div class="chip' + (payTab === s ? ' on' : '') + '" data-s="' + h(s) + '">' + h(s) + ' ' + c + '</div>';
    }).join('');
    var rows = payTab === 'Đã xử lý' ? done : docs.filter(function (d) { return d.workflow_state === payTab; });
    var lst = rows.length ? '<div class="lst">' + rows.map(function (d) {
      var cls = d.workflow_state === 'Đã duyệt - Đã ghi sổ' ? 'g' : (d.workflow_state === 'Bị trả lại' ? 'r' : (d.workflow_state === 'Nháp' ? 'w' : 'b'));
      return '<div class="li" data-n="' + h(d.name) + '"><div class="lt">' +
        '<div class="l1">' + h(d.party_name || d.party || d.name) + '</div>' +
        '<div class="l2">' + h(d.name) + ' &middot; ' + dmy(d.posting_date) + (d.custom_loai_chi ? '<br>' + h(d.custom_loai_chi) : '') + '</div></div>' +
        '<div style="text-align:right"><div class="amt">' + money(d.paid_amount) + '</div>' +
        '<span class="st ' + cls + '" style="margin-top:4px">' + h(d.workflow_state) + '</span></div></div>';
    }).join('') + '</div>' : '<div class="emp"><div class="e1">✅</div><div class="e2">Không có phiếu nào cần xử lý</div></div>';
    var b = frame('Duyệt phiếu chi', '<div class="chips">' + chips + '</div>' + lst);
    b.onclick = function (e) {
      var c = e.target.closest('[data-s]'); if (c) { payTab = c.dataset.s; return draw(); }
      var r = e.target.closest('[data-n]'); if (r) go(function () { scrPayView(r.dataset.n); });
    };
  }
  draw();
}

async function scrPayView(name) {
  frame(name, '<div class="emp"><div class="e1">⏳</div></div>');
  var d = await api('frappe.client.get', { doctype: 'Payment Entry', name: name });
  var files = await getList('File', { fields: ['file_url', 'file_name'], filters: { attached_to_doctype: 'Payment Entry', attached_to_name: name }, limit_page_length: 20 });
  var acts = PAYFLOW.filter(function (t) { return t.state === d.workflow_state && hasRole(t.role); });
  var refs = (d.references || []).map(function (r) {
    return '<div class="kv"><span style="flex:1;text-align:left;color:#16181d">' + h(r.reference_name) + '</span><b>' + money(r.allocated_amount) + '</b></div>';
  }).join('');
  var imgs = files.filter(function (f) { return /\.(jpe?g|png|webp|gif)$/i.test(f.file_url || ''); });
  var docs2 = files.filter(function (f) { return imgs.indexOf(f) < 0; });
  var html = '<div class="card">' +
    '<div style="padding:16px 14px;background:#E4F9FD"><div style="font-size:12.5px;color:#4E7C88;margin-bottom:4px">Số tiền chi</div>' +
    '<div style="font-size:28px;font-weight:800;color:#0B7C93">' + money(d.paid_amount) + ' đ</div></div>' +
    '<div class="kv"><span>Số phiếu</span><b>' + h(d.name) + '</b></div>' +
    '<div class="kv"><span>Ngày</span><b>' + dmy(d.posting_date) + '</b></div>' +
    '<div class="kv"><span>Người nhận</span><b>' + h(d.party_name || d.party || '-') + '</b></div>' +
    (d.custom_loai_chi ? '<div class="kv"><span>Loại chi</span><b>' + h(d.custom_loai_chi) + '</b></div>' : '') +
    '<div class="kv"><span>Hình thức</span><b>' + h(d.mode_of_payment || '-') + '</b></div>' +
    '<div class="kv"><span>Tài khoản chi</span><b>' + h(d.paid_from || '-') + '</b></div>' +
    '<div class="kv"><span>Trạng thái</span><b>' + h(d.workflow_state) + '</b></div>' +
    '<div class="kv"><span>Người lập</span><b>' + h(d.nguoi_lap_ten || d.owner) + '</b></div>' +
    '</div>' +
    (refs ? '<div class="sec">Hoá đơn thanh toán</div><div class="card">' + refs + '</div>' : '') +
    (d.remarks ? '<div class="sec">Diễn giải</div><div class="card"><div style="padding:12px 14px;font-size:14.5px;line-height:1.55;color:#3a404e">' + h(String(d.remarks).replace(/<[^>]*>/g, '')) + '</div></div>' : '') +
    (files.length ? '<div class="sec">Chứng từ đính kèm (' + files.length + ')</div><div class="card"><div class="att">' +
      imgs.map(function (f) { return '<a href="' + h(f.file_url) + '" target="_blank"><img src="' + h(f.file_url) + '"></a>'; }).join('') + '</div>' +
      docs2.map(function (f) { return '<div class="kv"><span style="flex:1;text-align:left">📎 ' + h(f.file_name) + '</span><a href="' + h(f.file_url) + '" target="_blank"><b style="color:#0B7C93">Mở</b></a></div>'; }).join('') +
      '</div>' : '') +
    '<button class="btn gh" id="pvPrint" style="margin-bottom:10px">Xem bản in đầy đủ</button>';

  var ft = acts.map(function (t) {
    return '<button class="btn ' + (t.ok ? 'gr' : 'dg') + '" data-act="' + h(t.action) + '" style="margin-bottom:9px">' + h(t.action) + '</button>';
  }).join('');
  var b = frame(name, html, { footer: ft || '<button class="btn gh" disabled>Không có thao tác cho vai trò của bạn</button>' });
  document.getElementById('pvPrint').onclick = function () {
    window.open('/printview?doctype=Payment%20Entry&name=' + encodeURIComponent(name) + '&format=' + encodeURIComponent('Vagabond - Chứng từ thanh toán') + '&no_letterhead=0&_lang=vi', '_blank');
  };
  var f = root.querySelector('.vf');
  if (f) f.onclick = async function (e) {
    var t = e.target.closest('[data-act]'); if (!t) return;
    var action = t.dataset.act;
    var tr = acts.filter(function (x) { return x.action === action; })[0];
    var reason = null;
    if (!tr.ok) {
      reason = await promptSheet('Lý do trả lại', 'Nhập lý do để người lập biết cần sửa gì...');
      if (reason === null) return;
      if (!reason) return toast('Cần nhập lý do trả lại');
    } else {
      var msg = action === 'Duyệt chi'
        ? 'Duyệt chi ' + money(d.paid_amount) + ' đ cho ' + (d.party_name || d.party) + '. Chữ ký và con dấu của anh sẽ được in lên chứng từ.'
        : 'Chuyển phiếu sang bước "' + tr.next + '".';
      if (!await confirmSheet(action + '?', msg, action)) return;
    }
    busy(1);
    try {
      if (reason) {
        await api('frappe.desk.form.utils.add_comment', { reference_doctype: 'Payment Entry', reference_name: name, content: 'Trả lại: ' + reason, comment_email: S.user, comment_by: S.user });
      }
      await api('frappe.model.workflow.apply_workflow', { doc: d, action: action });
      busy(0);
      toast(action === 'Duyệt chi' ? 'Đã duyệt và ký ' + name : 'Đã ' + action.toLowerCase() + ' ' + name, 3200);
      back();
    } catch (err) { busy(0); toast(errMsg(err), 4200); }
  };
}

/* ---------- 12. Tra ton kho ---------- */
var stk = { wh: 'Kho tổng 307 - TV', q: '' };
async function scrStock() {
  frame('Tra tồn kho', '<div class="emp"><div class="e1">⏳</div></div>');
  var rows = await getList('Bin', { fields: ['item_code', 'actual_qty', 'stock_uom'], filters: { warehouse: stk.wh, actual_qty: ['!=', 0] }, limit_page_length: 0, order_by: 'item_code' });
  var codes = rows.map(function (r) { return r.item_code; });
  var names = {};
  for (var ci = 0; ci < codes.length; ci += 400) {
    var lot = codes.slice(ci, ci + 400);
    var its = await getList('Item', { fields: ['name', 'item_name'], filters: { name: ['in', lot] }, limit_page_length: 0 });
    its.forEach(function (i) { names[i.name] = i.item_name; });
  }
  function draw() {
    var q = stk.q.toLowerCase();
    var f = rows.filter(function (r) { return !q || ((names[r.item_code] || '') + ' ' + r.item_code).toLowerCase().indexOf(q) >= 0; }).slice(0, 250);
    var b = frame('Tra tồn kho',
      '<div class="card"><div class="fld" data-w><div class="fi">🏬</div><div class="ft"><div class="fl">Kho</div>' +
      '<div class="fv">' + h(shortWh(stk.wh)) + '</div></div><div class="fc">&#8250;</div></div></div>' +
      srchBox('sq', 'Tìm hàng hoá', stk.q, true) +
      (f.length ? '<div class="lst">' + f.map(function (r) {
        return '<div class="li"><div class="lt"><div class="l1">' + h(names[r.item_code] || r.item_code) + '</div>' +
          '<div class="l2">Mã: ' + h(r.item_code) + '</div></div>' +
          '<div style="text-align:right"><div class="amt">' + num(r.actual_qty) + '</div>' +
          '<div class="l2">' + h(r.stock_uom) + '</div></div></div>';
      }).join('') + '</div>' : '<div class="emp"><div class="e1">📦</div><div class="e2">Kho này chưa có tồn</div></div>'));
    var sq = document.getElementById('sq');
    var tm = null;
    sq.oninput = function () { stk.q = sq.value; clearTimeout(tm); tm = setTimeout(function () { var v = stk.q; draw(); var i = document.getElementById('sq'); i.focus(); i.value = v; i.setSelectionRange(v.length, v.length); }, 200); };
    document.getElementById('sqscan').onclick = async function () {
      var code = await scanBarcode();
      if (!code) return;
      busy(1);
      var ic = null;
      try { ic = await itemByBarcode(code); } catch (e) { }
      busy(0);
      stk.q = ic || code;
      if (!ic) toast('Không tìm thấy hàng hoá có mã vạch này');
      draw();
    };
    b.onclick = function (e) {
      if (e.target.closest('[data-w]')) sheet('Chọn kho', whOpts(), stk.wh, function (o) { stk.wh = o.value; stk.q = ''; scrStock(); }, true);
    };
  }
  draw();
}

/* ---------- 12b. Bang bep ---------- */
function isBep() { return hasRole('Bếp phó') || hasRole('Manufacturing User') || hasRole('Manufacturing Manager') || hasRole('System Manager'); }
function nowStamp() {
  var d = new Date(), p = function (n) { return ('0' + n).slice(-2); };
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds());
}
var kit = { date: '', mine: 1 };

async function scrKitchen() {
  if (!kit.date) kit.date = today();
  var td = today();
  frame('Bảng bếp', '<div class="emp"><div class="e1">⏳</div></div>');

  var meBep = myKitchen();
  var docs = await getList('Material Request', {
    fields: ['name', 'schedule_date', 'set_warehouse', 'bo_phan_yeu_cau', 'nguoi_yeu_cau', 'trang_thai_bep', 'status', 'custom_bep_nhan'],
    filters: { material_request_type: 'Manufacture', docstatus: 1, schedule_date: kit.date },
    limit_page_length: 0, order_by: 'creation asc'
  });
  var tong = docs.length;
  if (meBep && kit.mine) docs = docs.filter(function (x) { return bepSeesRow(x.custom_bep_nhan); });
  var an = tong - docs.length;
  var late = [];
  try {
    var lt = await getList('Material Request', {
      fields: ['name', 'trang_thai_bep', 'custom_bep_nhan'],
      filters: { material_request_type: 'Manufacture', docstatus: 1, schedule_date: ['<', td] },
      limit_page_length: 0
    });
    late = lt.filter(function (x) { return x.trang_thai_bep !== 'Đã xong' && (!meBep || !kit.mine || bepSeesRow(x.custom_bep_nhan)); });
  } catch (e) { }

  var names = docs.map(function (d) { return d.name; });
  var lines = [];
  if (names.length) {
    lines = await getList('Material Request Item', {
      parent: 'Material Request',
      fields: ['name', 'parent', 'item_code', 'item_name', 'qty', 'uom', 'gio_can_lay', 'warehouse', 'bep_da_lam'],
      filters: { parent: ['in', names] }, limit_page_length: 0
    });
  }
  var byDoc = {}; docs.forEach(function (d) { byDoc[d.name] = d; });

  var groups = {}, order = [];
  lines.forEach(function (l) {
    var k = l.item_code + '|' + l.uom;
    if (!groups[k]) { groups[k] = { code: l.item_code, name: l.item_name || l.item_code, uom: l.uom, qty: 0, rows: [], gio: '99:99' }; order.push(k); }
    var g = groups[k];
    g.qty += (l.qty || 0);
    g.rows.push(l);
    var t = hm(l.gio_can_lay) || '99:99';
    if (t < g.gio) g.gio = t;
  });
  order.sort(function (a, b) {
    if (groups[a].gio !== groups[b].gio) return groups[a].gio < groups[b].gio ? -1 : 1;
    return groups[a].name.localeCompare(groups[b].name, 'vi');
  });
  function gDone(k) { return groups[k].rows.every(function (r) { return !!r.bep_da_lam; }); }
  function docDone(n) {
    var rs = lines.filter(function (l) { return l.parent === n; });
    return rs.length > 0 && rs.every(function (r) { return !!r.bep_da_lam; });
  }

  function draw() {
    var doneN = order.filter(gDone).length, allN = order.length;
    var pct = allN ? Math.round(doneN * 100 / allN) : 0;
    var chips = [['prev', 'Hôm qua', addDays(td, -1)], ['td', 'Hôm nay', td], ['tm', 'Ngày mai', addDays(td, 1)]]
      .map(function (c) { return '<div class="chip' + (kit.date === c[2] ? ' on' : '') + '" data-d="' + c[2] + '">' + c[1] + '</div>'; }).join('') +
      '<div class="chip" data-pick>📅 ' + dmy(kit.date) + '</div>' +
      (meBep ? '<div class="chip' + (kit.mine ? ' on' : '') + '" data-bep>' + (kit.mine ? '🧑‍🍳 ' + meBep : '👥 Tất cả bếp') + '</div>' : '');

    var warn = (late.length && kit.date === td) ?
      '<div class="kwn">⚠️ Còn ' + late.length + ' phiếu của những ngày trước chưa xác nhận xong. Bấm vào chip Hôm qua để xem.</div>' : '';
    if (meBep && kit.mine && an > 0) warn += '<div class="kwn" style="background:#E4F9FD;color:#05323C">Đang lọc phiếu gửi cho ' + h(meBep) + '. Còn ' + an + ' phiếu gửi cho bếp khác, bấm chip bên trên để xem tất cả.</div>';

    var body = '<div class="kbar">' + chips + '</div>' + warn;

    if (!allN) {
      body += '<div class="emp"><div class="e1">🎂</div><div class="e2">Ngày ' + dmy(kit.date) + ' chưa có phiếu sản xuất nào</div></div>';
    } else {
      body += '<div class="card"><div class="kpg"><div class="kpt">ĐÃ LÀM ' + doneN + '/' + allN + ' MÓN &middot; TỔNG ' + docs.length + ' PHIẾU</div>' +
        '<div class="kpb"><i style="width:' + pct + '%"></i></div></div></div>';
      body += '<div class="sec">Cần làm - gộp theo món</div><div class="card">' +
        order.map(function (k) {
          var g = groups[k];
          var det = g.rows.map(function (r) {
            var d = byDoc[r.parent] || {};
            return h(shortWh(r.warehouse || d.set_warehouse)) + ' ' + num(r.qty) + (hm(r.gio_can_lay) ? ' lúc ' + hm(r.gio_can_lay) : '');
          }).join(' &middot; ');
          return '<div class="kc' + (gDone(k) ? ' on' : '') + '" data-g="' + h(k) + '">' +
            '<div class="ktk">&#10003;</div>' +
            '<div class="kb"><div class="kn">' + h(g.name) + '</div><div class="kd">' + det + '</div></div>' +
            '<div class="kq"><b>' + num(g.qty) + '</b><small>' + h(g.uom) + '</small></div></div>';
        }).join('') + '</div>';
      body += '<div class="sec">Phiếu trong ngày</div><div class="card"><div class="lst">' +
        docs.map(function (d) {
          var rs = lines.filter(function (l) { return l.parent === d.name; });
          var dn = rs.filter(function (r) { return !!r.bep_da_lam; }).length;
          var fin = d.trang_thai_bep === 'Đã xong';
          var rdy = !fin && rs.length > 0 && dn === rs.length;
          var cls = fin ? 'g' : (rdy ? 'b' : (dn ? 'w' : 'n'));
          var lbl = fin ? 'Đã giao' : (rdy ? 'Sẵn sàng giao' : (dn ? 'Đang làm ' + dn + '/' + rs.length : 'Chưa làm'));
          var whs = [];
          rs.forEach(function (r) { var w = shortWh(r.warehouse); if (w && whs.indexOf(w) < 0) whs.push(w); });
          var p2 = [d.name];
          if (d.bo_phan_yeu_cau) p2.push(d.bo_phan_yeu_cau);
          if (d.nguoi_yeu_cau) p2.push(d.nguoi_yeu_cau);
          return '<div class="li" data-n="' + h(d.name) + '"><div class="lt">' +
            '<div class="l1">' + h(whs.join(', ') || shortWh(d.set_warehouse) || d.name) + '</div>' +
            '<div class="l2">' + h(p2.join(' \u00b7 ')) + '</div></div>' +
            '<span class="st ' + cls + '">' + h(lbl) + '</span></div>';
        }).join('') + '</div></div>';
    }

    var ready = docs.filter(function (d) { return d.trang_thai_bep !== 'Đã xong' && docDone(d.name); });
    var b = frame('Bảng bếp ' + dmy(kit.date), body,
      ready.length ? { footer: '<button class="btn" id="kfin">Xác nhận đã giao ' + ready.length + ' phiếu</button>' } : {});

    b.onclick = async function (e) {
      var dc = e.target.closest('[data-d]');
      if (dc) { kit.date = dc.dataset.d; return scrKitchen(); }
      if (e.target.closest('[data-bep]')) { kit.mine = kit.mine ? 0 : 1; return scrKitchen(); }
      if (e.target.closest('[data-pick]')) {
        var v = await promptSheet('Xem ngày khác', 'Nhập ngày dạng nn/tt/nnnn');
        if (!v) return;
        var m = String(v).match(/^(\d{1,2})\D(\d{1,2})\D(\d{4})$/);
        if (!m) return toast('Ngày chưa đúng dạng nn/tt/nnnn');
        kit.date = m[3] + '-' + ('0' + m[2]).slice(-2) + '-' + ('0' + m[1]).slice(-2);
        return scrKitchen();
      }
      var rw = e.target.closest('[data-n]');
      if (rw) return go(function () { scrMRView(rw.dataset.n, TYPES.Manufacture); });
      var gc = e.target.closest('[data-g]');
      if (!gc) return;
      var k = gc.dataset.g, g = groups[k];
      if (!g) return;
      var want = gDone(k) ? 0 : 1;
      busy(1);
      try {
        for (var i = 0; i < g.rows.length; i++) {
          if ((g.rows[i].bep_da_lam ? 1 : 0) === want) continue;
          await api('frappe.client.set_value', { doctype: 'Material Request Item', name: g.rows[i].name, fieldname: { bep_da_lam: want } });
          g.rows[i].bep_da_lam = want;
        }
        if (want) {
          var ps = {};
          g.rows.forEach(function (r) { ps[r.parent] = 1; });
          for (var p in ps) {
            var dd = byDoc[p];
            if (dd && !dd.trang_thai_bep) {
              try { await api('frappe.client.set_value', { doctype: 'Material Request', name: p, fieldname: { trang_thai_bep: 'Đang làm' } }); dd.trang_thai_bep = 'Đang làm'; } catch (x2) { }
            }
          }
        }
      } catch (err) { toast(errMsg(err)); }
      busy(0);
      draw();
    };

    var fb = document.getElementById('kfin');
    if (fb) fb.onclick = async function () {
      if (!await confirmSheet('Xác nhận đã giao bánh?', 'Đánh dấu ' + ready.length + ' phiếu là đã làm xong và đã giao cho nơi nhận. Phiếu sẽ chuyển sang trạng thái Đã giao.', 'Xác nhận')) return;
      busy(1);
      try {
        for (var i = 0; i < ready.length; i++) {
          await api('frappe.client.set_value', {
            doctype: 'Material Request', name: ready[i].name,
            fieldname: { trang_thai_bep: 'Đã xong', bep_xong_luc: nowStamp(), bep_nguoi_xong: (S.me.full_name || S.user) }
          });
          ready[i].trang_thai_bep = 'Đã xong';
        }
        toast('Đã xác nhận ' + ready.length + ' phiếu');
      } catch (err) { toast(errMsg(err)); }
      busy(0);
      draw();
    };
  }
  draw();
}

/* ---------- 12c. Lenh san xuat ---------- */
var WOST = {
  'Draft': 'Nháp', 'Submitted': 'Đã duyệt', 'Not Started': 'Chưa bắt đầu', 'In Process': 'Đang làm',
  'Completed': 'Đã xong', 'Stopped': 'Đã dừng', 'Closed': 'Đã đóng', 'Cancelled': 'Đã huỷ'
};
var WODONE = ['Completed', 'Stopped', 'Closed', 'Cancelled'];
var mfg = { src: '', fg: '', tab: 'open' };
var mfgN = { horizon: 0, rows: null };
var mfgD = null;
var mfgL = null;

function whFind() {
  var a = Array.prototype.slice.call(arguments);
  for (var i = 0; i < S.wh.length; i++) {
    var lw = S.wh[i].toLowerCase(), ok = 1;
    for (var j = 0; j < a.length; j++) { if (lw.indexOf(String(a[j]).toLowerCase()) < 0) { ok = 0; break; } }
    if (ok) return S.wh[i];
  }
  return '';
}
function mfgKey() {
  var bp = (S.me.bo_phan || '').toLowerCase();
  if (bp.indexOf('baker') >= 0) return 'baker';
  if (bp.indexOf('pastry') >= 0) return 'pastry';
  if (bp.indexOf('lab') >= 0) return 'lab';
  return '';
}
function mfgInitWh() {
  try {
    if (!mfg.src) mfg.src = localStorage.getItem('vgb_mfg_src') || '';
    if (!mfg.fg) mfg.fg = localStorage.getItem('vgb_mfg_fg') || '';
  } catch (e) { }
  if (S.wh.indexOf(mfg.src) < 0) mfg.src = '';
  if (S.wh.indexOf(mfg.fg) < 0) mfg.fg = '';
  var k = mfgKey();
  if (!mfg.src) mfg.src = (k && whFind(k, 'nguyên liệu')) || whFind('pastry', 'nguyên liệu') || whFind('nguyên liệu') || S.wh[0] || '';
  if (!mfg.fg) mfg.fg = (k && whFind(k, 'thành phẩm')) || whFind('pastry', 'thành phẩm') || whFind('thành phẩm') || S.wh[0] || '';
}
function mfgSaveWh() { try { localStorage.setItem('vgb_mfg_src', mfg.src); localStorage.setItem('vgb_mfg_fg', mfg.fg); } catch (e) { } }
function mfgShift() { var hh = (new Date()).getHours(); return hh < 12 ? 'Sáng' : (hh < 18 ? 'Chiều' : 'Đêm'); }
function mfgArea() { var k = mfgKey(); return k === 'baker' ? 'Bếp Baker' : (k === 'pastry' ? 'Bếp Pastry' : (k === 'lab' ? 'Sonneto Lab' : '')); }

async function inChunks(arr, n, fn) {
  var out = [];
  for (var i = 0; i < arr.length; i += n) {
    var r = await fn(arr.slice(i, i + n));
    if (r && r.length) out = out.concat(r);
  }
  return out;
}
function pad2(n) { return ('0' + n).slice(-2); }
function hmOf(d) { return pad2(d.getHours()) + ':' + pad2(d.getMinutes()) + ':00'; }
function ymdOf(d) { return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()); }
async function freshOf(codes) {
  var m = {};
  if (!codes || !codes.length) return m;
  var rows = await inChunks(codes, 80, function (lot) {
    return getList('Item', { fields: ['name', 'custom_lam_tuoi'], filters: { name: ['in', lot] }, limit_page_length: 0 });
  });
  rows.forEach(function (r) { if (r.custom_lam_tuoi) m[r.name] = 1; });
  return m;
}
async function mfgBatchOf(woName) {
  if (!woName) return '';
  try {
    var r = await getList('Batch', { fields: ['name'], filters: { custom_lenh_san_xuat: woName }, order_by: 'creation desc', limit_page_length: 1 });
    return r.length ? r[0].name : '';
  } catch (e) { return ''; }
}
async function bomOf(codes) {
  var m = {};
  if (!codes || !codes.length) return m;
  var rows = await inChunks(codes, 80, function (lot) {
    return getList('BOM', { fields: ['name', 'item', 'quantity', 'uom'], filters: { item: ['in', lot], docstatus: 1, is_active: 1, is_default: 1 }, limit_page_length: 0 });
  });
  rows.forEach(function (r) { if (!m[r.item]) m[r.item] = r; });
  return m;
}
async function stockOf(codes, wh) {
  var m = {};
  if (!codes || !codes.length || !wh) return m;
  var rows = await inChunks(codes, 80, function (lot) {
    return getList('Bin', { fields: ['item_code', 'actual_qty'], filters: { warehouse: wh, item_code: ['in', lot] }, limit_page_length: 0 });
  });
  rows.forEach(function (r) { m[r.item_code] = (m[r.item_code] || 0) + (r.actual_qty || 0); });
  return m;
}
async function openWoQty(codes) {
  var m = {};
  if (!codes || !codes.length) return m;
  var rows = await inChunks(codes, 80, function (lot) {
    return getList('Work Order', { fields: ['production_item', 'qty', 'produced_qty', 'status'], filters: { docstatus: 1, production_item: ['in', lot] }, limit_page_length: 0 });
  });
  rows.forEach(function (w) {
    if (WODONE.indexOf(w.status) >= 0) return;
    var left = (w.qty || 0) - (w.produced_qty || 0);
    if (left > 0) m[w.production_item] = (m[w.production_item] || 0) + left;
  });
  return m;
}
async function mfgLoadItem(code) {
  var m = await getList('Item', { fields: ['name', 'item_name', 'stock_uom', 'image', 'shelf_life_in_days', 'has_batch_no', 'custom_dieu_kien_bao_quan', 'custom_lam_tuoi', 'custom_han_dung_gio'], filters: { name: code }, limit_page_length: 1 });
  if (!m.length) throw new Error('Không tìm thấy hàng hoá ' + code);
  var it = m[0];
  var us = [];
  try {
    var conv = await getList('UOM Conversion Detail', { parent: 'Item', fields: ['uom', 'conversion_factor'], filters: { parent: code, parenttype: 'Item' }, limit_page_length: 60 });
    us = conv.map(function (c) { return { uom: c.uom, cf: c.conversion_factor }; });
  } catch (e) { }
  if (!us.some(function (u) { return u.uom === it.stock_uom; })) us.unshift({ uom: it.stock_uom, cf: 1 });
  it.uoms = us;
  return it;
}

/* --- o chon kho nguyen lieu / kho thanh pham dung chung cho ca phan he --- */
function mfgWhCard() {
  return '<div class="card">' +
    '<div class="fld" data-mw="src"><div class="fi">🧂</div><div class="ft"><div class="fl">Lấy nguyên liệu từ kho</div>' +
    '<div class="fv">' + h(shortWh(mfg.src) || 'Chưa chọn') + '</div></div><div class="fc">&#8250;</div></div>' +
    '<div class="fld" data-mw="fg"><div class="fi">🎂</div><div class="ft"><div class="fl">Nhập thành phẩm vào kho</div>' +
    '<div class="fv">' + h(shortWh(mfg.fg) || 'Chưa chọn') + '</div></div><div class="fc">&#8250;</div></div></div>';
}
function mfgWhTap(e, redraw) {
  var t = e.target.closest('[data-mw]');
  if (!t) return false;
  var k = t.dataset.mw;
  sheet(k === 'src' ? 'Kho nguyên liệu' : 'Kho thành phẩm', whOpts(), mfg[k], function (o) {
    mfg[k] = o.value; mfgSaveWh(); redraw();
  }, true);
  return true;
}

/* --- o nhap so luong dang bottom sheet --- */
function qtySheet(title, label, def, uom) {
  return new Promise(function (res) {
    var ov = document.createElement('div'); ov.className = 'sh';
    ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
      '<div style="font-size:17.5px;font-weight:700;margin-bottom:12px">' + h(title) + '</div>' +
      '<div style="font-size:12px;color:#8a8f9c;margin-bottom:6px">' + h(label || '') + '</div>' +
      '<div class="qr"><div class="stp"><button data-m>&minus;</button>' +
      '<input type="number" inputmode="decimal" id="qsv" value="' + (def || 0) + '">' +
      '<button data-p>+</button></div>' + (uom ? '<div class="uml">' + h(uom) + '</div>' : '') + '</div>' +
      '<button class="btn" data-y style="margin-top:14px">Xác nhận</button>' +
      '<button class="btn gh" data-n style="margin-top:9px">Huỷ</button></div>';
    document.body.appendChild(ov);
    var inp = ov.querySelector('#qsv');
    ov.onclick = function (e) {
      var t = e.target;
      if (t.hasAttribute && t.hasAttribute('data-m')) { inp.value = Math.max(0, r3((parseFloat(inp.value) || 0) - 1)); return; }
      if (t.hasAttribute && t.hasAttribute('data-p')) { inp.value = r3((parseFloat(inp.value) || 0) + 1); return; }
      if (t === ov || (t.hasAttribute && t.hasAttribute('data-n'))) { ov.remove(); res(null); return; }
      if (t.hasAttribute && t.hasAttribute('data-y')) { var v = parseFloat(inp.value) || 0; ov.remove(); res(v > 0 ? v : null); }
    };
    setTimeout(function () { try { inp.focus(); inp.select(); } catch (e) { } }, 150);
  });
}

/* --- tim hang hoa nhanh (dung cho khai nguyen lieu va them mon) --- */
function mfgPickItem(title, groups, onPick) {
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>' + h(title) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:10px 14px 6px;display:flex;gap:8px;align-items:center">' +
    '<input class="nt" id="mpq" placeholder="Gõ tên hoặc mã (từ 2 ký tự)" style="height:46px;padding:0 12px;flex:1">' +
    '<button class="sbtn" id="mpsc" style="width:46px;height:46px;flex:0 0 46px">&#128247;</button></div>' +
    '<div class="shl" style="min-height:170px"></div>';
  ov.appendChild(box); document.body.appendChild(ov);
  var lst = box.querySelector('.shl'), inp = box.querySelector('#mpq'), seq = 0, tmr = null;
  function close() { ov.remove(); }
  function msg(s) { lst.innerHTML = '<div class="emp" style="padding:34px 20px"><div class="e2">' + h(s) + '</div></div>'; }
  msg('Gõ để tìm hàng hoá');
  ov.onclick = function (e) { if (e.target === ov) close(); };
  box.querySelector('.x').onclick = close;
  async function run(q) {
    var my = ++seq;
    lst.innerHTML = '<div class="emp" style="padding:34px"><div class="e1">⏳</div></div>';
    var f = { disabled: 0, has_variants: 0 };
    if (groups && groups.length) f.item_group = ['in', groups];
    var res = [];
    try {
      res = await getList('Item', {
        fields: ['name', 'item_name', 'stock_uom', 'image'], filters: f,
        or_filters: { item_name: ['like', '%' + q + '%'], name: ['like', '%' + q + '%'] },
        limit_page_length: 60, order_by: 'item_name'
      });
    } catch (e) { }
    if (my !== seq) return;
    if (!res.length) return msg('Không tìm thấy hàng hoá');
    lst.innerHTML = res.map(function (it) {
      return '<div class="li" data-c="' + h(it.name) + '">' +
        (it.image ? '<img class="im" src="' + h(it.image) + '" loading="lazy">' : '<div class="im imp">🍰</div>') +
        '<div class="lt"><div class="l1">' + h(it.item_name) + '</div>' +
        '<div class="l2">Mã: ' + h(it.name) + ' &middot; ' + h(it.stock_uom) + '</div></div></div>';
    }).join('');
  }
  inp.oninput = function () {
    clearTimeout(tmr);
    var v = inp.value.trim();
    if (v.length < 2) return msg('Gõ ít nhất 2 ký tự');
    tmr = setTimeout(function () { run(v); }, 280);
  };
  lst.onclick = function (e) { var r = e.target.closest('[data-c]'); if (!r) return; close(); onPick(r.dataset.c); };
  box.querySelector('#mpsc').onclick = async function () {
    close();
    var code = await scanBarcode();
    if (!code) return;
    busy(1); var ic = null;
    try { ic = await itemByBarcode(code); } catch (e) { }
    busy(0);
    if (!ic) return toast('Không tìm thấy hàng hoá có mã vạch này');
    onPick(ic);
  };
  setTimeout(function () { try { inp.focus(); } catch (e) { } }, 160);
}

/* ---------- 12c-1. Danh sach lenh san xuat ---------- */
async function scrMfgList() {
  await loadMasters();
  mfgInitWh();
  frame('Lệnh sản xuất', '<div class="emp"><div class="e1">⏳</div></div>');
  var wos = [];
  try {
    wos = await getList('Work Order', {
      fields: ['name', 'production_item', 'item_name', 'qty', 'produced_qty', 'status', 'planned_start_date', 'stock_uom'],
      filters: { docstatus: ['<', 2] }, limit_page_length: 80, order_by: 'creation desc'
    });
  } catch (e) { toast(errMsg(e)); }

  function draw() {
    var f = wos.filter(function (w) {
      if (mfg.tab === 'open') return WODONE.indexOf(w.status) < 0;
      if (mfg.tab === 'done') return w.status === 'Completed';
      return true;
    });
    var chips = [['open', 'Đang làm'], ['done', 'Đã xong'], ['all', 'Tất cả']].map(function (c) {
      return '<div class="chip' + (mfg.tab === c[0] ? ' on' : '') + '" data-t="' + c[0] + '">' + c[1] + '</div>';
    }).join('');
    var body = mfgWhCard() +
      '<button class="btn gh" id="mNoBom" style="margin-bottom:12px">🧾 Làm món chưa có công thức</button>' +
      '<div class="chips">' + chips + '</div>' +
      (f.length ? '<div class="lst">' + f.map(function (w) {
        var done = w.status === 'Completed';
        var cls = done ? 'g' : (w.status === 'Stopped' || w.status === 'Closed' ? 'n' : ((w.produced_qty || 0) > 0 ? 'w' : 'b'));
        return '<div class="li" data-n="' + h(w.name) + '"><div class="lt">' +
          '<div class="l1">' + h(w.item_name || w.production_item) + '</div>' +
          '<div class="l2">' + h(w.name) + ' &middot; ' + h(dmy(w.planned_start_date)) + '</div></div>' +
          '<div style="text-align:right"><div class="amt">' + num(w.produced_qty || 0) + '/' + num(w.qty) + '</div>' +
          '<div class="st ' + cls + '" style="margin-top:4px">' + h(WOST[w.status] || w.status) + '</div></div></div>';
      }).join('') + '</div>'
        : '<div class="emp"><div class="e1">🏭</div><div class="e2">Chưa có lệnh sản xuất nào</div></div>');

    var b = frame('Lệnh sản xuất', body, { fab: true, onFab: function () { mfgN.rows = null; go(scrMfgNew); } });
    b.onclick = function (e) {
      if (mfgWhTap(e, draw)) return;
      var c = e.target.closest('[data-t]');
      if (c) { mfg.tab = c.dataset.t; return draw(); }
      var r = e.target.closest('[data-n]');
      if (r) { var nm = r.dataset.n; return go(function () { scrMfgView(nm); }); }
    };
    document.getElementById('mNoBom').onclick = function () {
      mfgPickItem('Chọn món cần làm', leavesUnder(['Bán ra', 'Sản xuất']), async function (code) {
        busy(1);
        try {
          var it = await mfgLoadItem(code);
          mfgD = { code: code, name: it.item_name || code, stock_uom: it.stock_uom, meta: it, qty: 1, mats: [], saveBom: 1 };
          go(scrMfgDeclare);
        } catch (err) { toast(errMsg(err)); } finally { busy(0); }
      });
    };
  }
  draw();
}

/* ---------- 12c-2. Tao lenh: gop nhu cau tu cac phieu yeu cau ---------- */
async function scrMfgNew() {
  mfgInitWh();
  if (!mfgN.rows) {
    frame('Tạo lệnh sản xuất', '<div class="emp"><div class="e1">⏳</div></div>');
    try { mfgN.rows = await mfgDemand(mfgN.horizon); }
    catch (e) { mfgN.rows = []; toast(errMsg(e), 5000); }
  }
  var rows = mfgN.rows;

  function draw() {
    var nsel = rows.filter(function (r) { return r.on && r.bom; }).length;
    var chips = [[0, 'Đến hôm nay'], [1, 'Đến ngày mai'], [7, 'Đến hết tuần']].map(function (c) {
      return '<div class="chip' + (mfgN.horizon === c[0] ? ' on' : '') + '" data-hz="' + c[0] + '">' + c[1] + '</div>';
    }).join('');
    var body = mfgWhCard() + '<div class="chips">' + chips + '</div>' +
      (rows.length ? rows.map(function (r, i) {
        var img = r.image ? '<img class="im3" src="' + h(r.image) + '">' : '<div class="im3 im3p">🍰</div>';
        return '<div class="ic1' + (r.on && r.bom ? ' ok' : '') + '" data-i="' + i + '">' +
          '<div class="ih">' + img +
          '<div class="in">' + h(r.name) + '<div class="ig">Mã: ' + h(r.code) +
          (r.bom ? '' : ' &middot; <span class="mno">Chưa có công thức</span>') + '</div></div>' +
          (r.bom ? '<div class="rok" data-k="' + i + '">&#10003;</div>' : '') + '</div>' +
          '<div class="stk">' +
          '<div><div class="s1">Phòng ban cần</div><div class="s2">' + num(r.need) + ' ' + h(r.uom) + '</div></div>' +
          '<div><div class="s1">Đã có lệnh</div><div class="s2">' + num(r.wo) + '</div></div>' +
          '<div><div class="s1">Tồn thành phẩm</div><div class="s2">' + num(r.ton) + '</div></div></div>' +
          (r.bom ?
            '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số lượng sẽ làm</div>' +
            '<div class="qr"><div class="stp"><button data-m="' + i + '">&minus;</button>' +
            '<input type="number" inputmode="decimal" data-q="' + i + '" value="' + r.qty + '">' +
            '<button data-p="' + i + '">+</button></div><div class="uml">' + h(r.uom) + '</div></div></div></div>'
            : '<div class="qw"><button class="btn gh" data-dec="' + i + '">🧾 Khai nguyên liệu đã dùng</button></div>') +
          '</div>';
      }).join('')
        : '<div class="emp"><div class="e1">✅</div><div class="e2">Không còn món nào cần sản xuất trong khoảng này</div></div>') +
      '<button class="btn gh" id="mAdd" style="margin-top:4px">+ Thêm món ngoài phiếu yêu cầu</button>';

    var b = frame('Tạo lệnh sản xuất', body, {
      footer: '<button class="btn" id="mGo"' + (nsel ? '' : ' disabled') + '>Tạo ' + (nsel || '') + ' lệnh sản xuất</button>'
    });
    b.addEventListener('input', function (e) {
      var t = e.target;
      if (t.dataset.q != null) rows[+t.dataset.q].qty = parseFloat(t.value) || 0;
    });
    b.onclick = function (e) {
      if (mfgWhTap(e, draw)) return;
      var hz = e.target.closest('[data-hz]');
      if (hz) { mfgN.horizon = +hz.dataset.hz; mfgN.rows = null; return scrMfgNew(); }
      var t = e.target.closest('[data-k],[data-m],[data-p],[data-dec]');
      if (!t) return;
      if (t.dataset.k != null) { var i = +t.dataset.k; rows[i].on = !rows[i].on; return draw(); }
      if (t.dataset.m != null) { var j = +t.dataset.m; rows[j].qty = Math.max(0, r3(rows[j].qty - 1)); var el = b.querySelector('[data-q="' + j + '"]'); if (el) el.value = rows[j].qty; return; }
      if (t.dataset.p != null) { var k2 = +t.dataset.p; rows[k2].qty = r3(rows[k2].qty + 1); var e2 = b.querySelector('[data-q="' + k2 + '"]'); if (e2) e2.value = rows[k2].qty; return; }
      if (t.dataset.dec != null) {
        var r = rows[+t.dataset.dec];
        busy(1);
        mfgLoadItem(r.code).then(function (it) {
          mfgD = { code: r.code, name: r.name, stock_uom: it.stock_uom, meta: it, qty: r.qty || 1, mats: [], saveBom: 1 };
          go(scrMfgDeclare);
        }).catch(function (err) { toast(errMsg(err)); }).then(function () { busy(0); });
      }
    };
    document.getElementById('mAdd').onclick = function () {
      mfgPickItem('Thêm món cần làm', leavesUnder(['Bán ra', 'Sản xuất']), async function (code) {
        if (rows.some(function (x) { return x.code === code; })) return toast('Món này đã có trong danh sách');
        busy(1);
        try {
          var it = await mfgLoadItem(code);
          var bm = await bomOf([code]);
          var tn = await stockOf([code], mfg.fg);
          rows.push({ code: code, name: it.item_name || code, uom: it.stock_uom, image: it.image || '', need: 0, wo: 0, ton: tn[code] || 0, bom: bm[code] ? bm[code].name : '', qty: 1, on: 1 });
          draw();
        } catch (err) { toast(errMsg(err)); } finally { busy(0); }
      });
    };
    document.getElementById('mGo').onclick = async function () {
      var sel = rows.filter(function (r) { return r.on && r.bom && r.qty > 0; });
      if (!sel.length) return toast('Chưa chọn món nào');
      if (!mfg.src || !mfg.fg) return toast('Chưa chọn kho nguyên liệu hoặc kho thành phẩm');
      busy(1);
      var made = [], errs = [];
      for (var i = 0; i < sel.length; i++) {
        try { made.push(await mfgCreateWO(sel[i])); }
        catch (err) { errs.push(sel[i].name + ': ' + errMsg(err)); }
      }
      busy(0);
      if (errs.length) toast(errs[0], 6000);
      if (!made.length) return;
      toast('Đã tạo ' + made.length + ' lệnh sản xuất');
      mfgN.rows = null;
      go(function () { scrMfgBtp(made, 1); }, true);
    };
  }
  draw();
}

/* gop nhu cau tu cac phieu yeu cau san xuat da duyet */
async function mfgDemand(horizon) {
  var td = today();
  var to = addDays(td, horizon || 0);
  var from = addDays(td, -45);
  var docs = await getList('Material Request', {
    fields: ['name', 'trang_thai_bep'],
    filters: [['material_request_type', '=', 'Manufacture'], ['docstatus', '=', 1],
    ['schedule_date', '>=', from], ['schedule_date', '<=', to]],
    limit_page_length: 0
  });
  var names = docs.filter(function (d) { return d.trang_thai_bep !== 'Đã xong'; }).map(function (d) { return d.name; });
  var lines = [];
  if (names.length) {
    lines = await inChunks(names, 60, function (lot) {
      return getList('Material Request Item', {
        parent: 'Material Request',
        fields: ['item_code', 'item_name', 'qty', 'stock_qty', 'uom', 'stock_uom', 'bep_da_lam'],
        filters: { parent: ['in', lot] }, limit_page_length: 0
      });
    });
  }
  var agg = {}, order = [];
  lines.forEach(function (l) {
    if (l.bep_da_lam) return;
    var c = l.item_code;
    if (!agg[c]) { agg[c] = { code: c, name: l.item_name || c, uom: l.stock_uom || l.uom, need: 0, wo: 0, ton: 0 }; order.push(c); }
    agg[c].need += (l.stock_qty || l.qty || 0);
  });
  if (!order.length) return [];
  var wq = await openWoQty(order);
  var tn = await stockOf(order, mfg.fg);
  var bm = await bomOf(order);
  var meta = {};
  var mrows = await inChunks(order, 80, function (lot) {
    return getList('Item', { fields: ['name', 'item_name', 'image', 'stock_uom'], filters: { name: ['in', lot] }, limit_page_length: 0 });
  });
  mrows.forEach(function (m) { meta[m.name] = m; });
  return order.map(function (c) {
    var a = agg[c], m = meta[c] || {};
    a.wo = wq[c] || 0;
    a.ton = tn[c] || 0;
    a.image = m.image || '';
    a.name = m.item_name || a.name;
    a.uom = m.stock_uom || a.uom;
    a.bom = bm[c] ? bm[c].name : '';
    a.qty = Math.max(0, r3(a.need - a.wo));
    a.on = a.qty > 0 ? 1 : 0;
    return a;
  }).filter(function (a) { return a.need > 0; });
}

async function mfgCreateWO(row) {
  var doc = {
    doctype: 'Work Order', company: COMPANY,
    production_item: row.code, item_name: row.name, bom_no: row.bom,
    qty: row.qty, stock_uom: row.uom,
    fg_warehouse: row.fg || mfg.fg, source_warehouse: row.src || mfg.src,
    skip_transfer: 1, use_multi_level_bom: 0,
    planned_start_date: today() + ' 05:00:00'
  };
  var ins = await api('frappe.client.insert', { doc: doc });
  var sub = await api('frappe.client.submit', { doc: ins });
  return (sub && sub.name) || ins.name;
}

/* ---------- 12c-3. May de xuat lenh ban thanh pham, bep bam duyet ---------- */
async function scrMfgBtp(woNames, depth) {
  depth = depth || 1;
  frame('Bán thành phẩm cần làm', '<div class="emp"><div class="e1">⏳</div></div>');
  var rows = [];
  try {
    var wis = await inChunks(woNames, 50, function (lot) {
      return getList('Work Order Item', {
        parent: 'Work Order', fields: ['item_code', 'item_name', 'required_qty', 'stock_uom'],
        filters: { parent: ['in', lot] }, limit_page_length: 0
      });
    });
    var agg = {}, order = [];
    wis.forEach(function (w) {
      var c = w.item_code;
      if (!agg[c]) { agg[c] = { code: c, name: w.item_name || c, uom: w.stock_uom, need: 0 }; order.push(c); }
      agg[c].need += (w.required_qty || 0);
    });
    var bm = await bomOf(order);
    var fr = await freshOf(order);
    var prod = order.filter(function (c) { return !!bm[c] && !fr[c]; });
    if (prod.length) {
      var tn = await stockOf(prod, mfg.src);
      var wq = await openWoQty(prod);
      rows = prod.map(function (c) {
        var a = agg[c];
        a.ton = tn[c] || 0; a.wo = wq[c] || 0; a.bom = bm[c].name;
        a.short = r3(a.need - a.ton - a.wo);
        a.qty = a.short > 0 ? Math.ceil(a.short) : 0;
        a.on = a.short > 0 ? 1 : 0;
        return a;
      }).filter(function (a) { return a.short > 0; });
    }
  } catch (e) { toast(errMsg(e), 5000); }

  if (!rows.length) {
    toast('Không cần làm thêm bán thành phẩm nào', 4000);
    return go(scrMfgList, true);
  }

  function draw() {
    var nsel = rows.filter(function (r) { return r.on; }).length;
    var body = '<div class="rcvh">Máy tính ra các bán thành phẩm còn thiếu để làm được số bánh vừa tạo lệnh. ' +
      'Bếp xem lại rồi bấm duyệt, máy sẽ tạo lệnh sản xuất cho từng loại. ' +
      'Các loại làm tươi như mousse hay bán thành phẩm cấp 2 không hiện ở đây, máy sẽ tự làm khi bếp bấm hoàn tất lệnh của món cha.</div>' +
      rows.map(function (r, i) {
        return '<div class="ic1' + (r.on ? ' ok' : '') + '">' +
          '<div class="ih"><div class="n">' + (i + 1) + '</div>' +
          '<div class="in">' + h(r.name) + '<div class="ig">Mã: ' + h(r.code) + '</div></div>' +
          '<div class="rok" data-k="' + i + '">&#10003;</div></div>' +
          '<div class="stk">' +
          '<div><div class="s1">Công thức cần</div><div class="s2">' + num(r.need) + ' ' + h(r.uom) + '</div></div>' +
          '<div><div class="s1">Tồn kho NVL</div><div class="s2">' + num(r.ton) + '</div></div>' +
          '<div><div class="s1">Còn thiếu</div><div class="s2" style="color:#c93a3a">' + num(r.short) + '</div></div></div>' +
          '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số lượng sẽ làm</div>' +
          '<div class="qr"><div class="stp"><button data-m="' + i + '">&minus;</button>' +
          '<input type="number" inputmode="decimal" data-q="' + i + '" value="' + r.qty + '">' +
          '<button data-p="' + i + '">+</button></div><div class="uml">' + h(r.uom) + '</div></div></div></div>' +
          '</div>';
      }).join('') +
      '<button class="btn gh" id="mSkip" style="margin-top:4px">Bỏ qua bước này</button>';

    var b = frame('Bán thành phẩm cần làm', body, {
      footer: '<button class="btn" id="mBtpGo"' + (nsel ? '' : ' disabled') + '>Duyệt và tạo ' + (nsel || '') + ' lệnh</button>'
    });
    b.addEventListener('input', function (e) {
      if (e.target.dataset.q != null) rows[+e.target.dataset.q].qty = parseFloat(e.target.value) || 0;
    });
    b.onclick = function (e) {
      var t = e.target.closest('[data-k],[data-m],[data-p]'); if (!t) return;
      if (t.dataset.k != null) { var i = +t.dataset.k; rows[i].on = !rows[i].on; return draw(); }
      if (t.dataset.m != null) { var j = +t.dataset.m; rows[j].qty = Math.max(0, r3(rows[j].qty - 1)); var el = b.querySelector('[data-q="' + j + '"]'); if (el) el.value = rows[j].qty; return; }
      if (t.dataset.p != null) { var k2 = +t.dataset.p; rows[k2].qty = r3(rows[k2].qty + 1); var e2 = b.querySelector('[data-q="' + k2 + '"]'); if (e2) e2.value = rows[k2].qty; }
    };
    document.getElementById('mSkip').onclick = function () { go(scrMfgList, true); };
    document.getElementById('mBtpGo').onclick = async function () {
      var sel = rows.filter(function (r) { return r.on && r.qty > 0; });
      if (!sel.length) return toast('Chưa chọn món nào');
      busy(1);
      var made = [], errs = [];
      for (var i = 0; i < sel.length; i++) {
        try { made.push(await mfgCreateWO(sel[i])); }
        catch (err) { errs.push(sel[i].name + ': ' + errMsg(err)); }
      }
      busy(0);
      if (errs.length) toast(errs[0], 6000);
      if (!made.length) return;
      toast('Đã tạo ' + made.length + ' lệnh bán thành phẩm');
      if (depth < 4) return go(function () { scrMfgBtp(made, depth + 1); }, true);
      go(scrMfgList, true);
    };
  }
  draw();
}

/* ---------- 12c-4. Chi tiet lenh va hoan tat san xuat ---------- */
async function scrMfgView(name) {
  frame('Lệnh sản xuất', '<div class="emp"><div class="e1">⏳</div></div>');
  var d = null;
  try { d = await api('frappe.client.get', { doctype: 'Work Order', name: name }); }
  catch (e) { toast(errMsg(e), 5000); return; }
  var mats = d.required_items || [];
  var src = d.source_warehouse || mfg.src;
  var tn = {};
  try { tn = await stockOf(mats.map(function (m) { return m.item_code; }), src); } catch (e) { }
  var left = r3((d.qty || 0) - (d.produced_qty || 0));
  var canDo = d.docstatus === 1 && WODONE.indexOf(d.status) < 0 && left > 0;

  var head = '<div class="card"><div class="kpg">' +
    '<div style="font-size:18px;font-weight:700;line-height:1.3">' + h(d.item_name || d.production_item) + '</div>' +
    '<div style="font-size:12.5px;color:#8a8f9c;margin-top:5px">' + h(d.name) + ' &middot; ' + h(WOST[d.status] || d.status) + '</div>' +
    '</div><div class="stk">' +
    '<div><div class="s1">Cần làm</div><div class="s2">' + num(d.qty) + ' ' + h(d.stock_uom || '') + '</div></div>' +
    '<div><div class="s1">Đã làm</div><div class="s2">' + num(d.produced_qty || 0) + '</div></div>' +
    '<div><div class="s1">Còn lại</div><div class="s2">' + num(left) + '</div></div></div>' +
    '<div class="fld"><div class="fi">🧂</div><div class="ft"><div class="fl">Trừ nguyên liệu tại kho</div>' +
    '<div class="fv">' + h(shortWh(src) || 'Chưa có') + '</div></div></div>' +
    '<div class="fld"><div class="fi">🎂</div><div class="ft"><div class="fl">Nhập thành phẩm vào kho</div>' +
    '<div class="fv">' + h(shortWh(d.fg_warehouse) || 'Chưa có') + '</div></div></div></div>';

  var short = 0;
  var list = mats.length ? '<div class="sec">Nguyên liệu sẽ trừ</div><div class="lst">' + mats.map(function (m) {
    var have = tn[m.item_code] || 0;
    var per = (d.qty || 1);
    var needNow = r3((m.required_qty || 0) / per * left);
    var bad = have < needNow - 0.0001;
    if (bad) short++;
    return '<div class="li"><div class="lt"><div class="l1">' + h(m.item_name || m.item_code) + '</div>' +
      '<div class="l2">Tồn ' + num(have) + ' ' + h(m.stock_uom || '') + '</div></div>' +
      '<div style="text-align:right"><div class="amt"' + (bad ? ' style="color:#c93a3a"' : '') + '>' + num(needNow) + '</div>' +
      '<div class="l2">' + h(m.stock_uom || '') + '</div></div></div>';
  }).join('') + '</div>' : '';

  var warn = short ? '<div class="kwn">⚠️ Có ' + short + ' nguyên liệu tồn kho không đủ. Nếu vẫn bấm hoàn tất thì máy sẽ báo lỗi thiếu hàng.</div>' : '';

  var b = frame('Lệnh sản xuất', head + warn + list, {
    footer: canDo
      ? '<div class="row2"><button class="btn gh" id="mLbl">🖨️ In tem</button>' +
        '<button class="btn gr" id="mFin">✅ Hoàn tất</button></div>'
      : '<button class="btn gh" id="mLbl">🖨️ In lại tem</button>'
  });
  document.getElementById('mLbl').onclick = async function () {
    busy(1);
    try {
      var it = await mfgLoadItem(d.production_item);
      if (!it.has_batch_no) { busy(0); return toast('Món này chưa bật theo dõi lô nên chưa in được tem', 5000); }
      var bt = await mfgBatchOf(d.name);
      if (!bt) bt = await mfgMakeBatch(d.production_item, it, left || d.qty, d.name);
      busy(0);
      if (!bt) return toast('Chưa tạo được mẻ để in tem', 5000);
      mfgL = { batch: bt, item: d.production_item, name: d.item_name || d.production_item, qty: left || d.qty, uom: d.stock_uom, meta: it, pre: canDo ? 1 : 0 };
      return go(scrMfgLabel);
    } catch (err) { busy(0); toast(errMsg(err), 7000); }
  };
  if (!canDo) return;
  document.getElementById('mFin').onclick = async function () {
    var q = await qtySheet('Hoàn tất sản xuất', 'Số lượng làm được thực tế', left, d.stock_uom);
    if (!q) return;
    if (q > left + 0.0001) return toast('Không được nhiều hơn số còn lại là ' + num(left));
    var ratio = (d.qty || 1) ? q / (d.qty || 1) : 1;
    var plan = [];
    busy(1);
    try { plan = await mfgFreshPlan(mats, ratio, src); } catch (e) { }
    busy(0);
    if (plan.length) {
      var lines = plan.map(function (f) { return '- ' + f.name + ': ' + num(f.qty) + ' ' + (f.uom || ''); }).join('\n');
      var okf = await confirmSheet('Máy làm luôn giúp bếp',
        'Các bán thành phẩm làm tươi sau đây chưa có tồn. Máy sẽ tự tạo lệnh và trừ nguyên liệu cho từng loại ngay trước khi hoàn tất món chính:\n\n' +
        lines + '\n\nBếp chỉ cần bấm một lần, không phải nhập tồn thủ công.', 'Đồng ý, làm luôn');
      if (!okf) return;
    }
    busy(1);
    try {
      if (plan.length) await mfgRunFresh(plan, 1);
      var it = await mfgLoadItem(d.production_item);
      var batch = await mfgBatchOf(d.name);
      if (!batch) batch = await mfgMakeBatch(d.production_item, it, q, d.name);
      var se = await api('erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry',
        { work_order_id: d.name, purpose: 'Manufacture', qty: q });
      se.set_posting_time = 1;
      se.posting_date = today();
      se.posting_time = nowStamp().slice(11);
      (se.items || []).forEach(function (r) {
        if (r.is_finished_item && batch) { r.use_serial_batch_fields = 1; r.batch_no = batch; }
      });
      var ins = await api('frappe.client.insert', { doc: se });
      await api('frappe.client.submit', { doc: ins });
      busy(0);
      toast('Đã hoàn tất và trừ nguyên liệu');
      if (!batch) return go(scrMfgList, true);
      mfgL = { batch: batch, item: d.production_item, name: d.item_name || d.production_item, qty: q, uom: d.stock_uom, meta: it };
      return go(scrMfgLabel, true);
    } catch (err) { busy(0); toast(errMsg(err), 7000); }
  };
}

async function mfgMakeBatch(code, meta, qty, woName) {
  if (!meta || !meta.has_batch_no) return null;
  var now = new Date();
  var d0 = ymdOf(now);
  var doc = {
    doctype: 'Batch', item: code, manufacturing_date: d0,
    custom_gio_san_xuat: hmOf(now),
    custom_nguoi_san_xuat: S.user || undefined,
    custom_ca_san_xuat: mfgShift(),
    custom_khu_vuc_san_xuat: mfgArea() || undefined,
    custom_dieu_kien_bao_quan: meta.custom_dieu_kien_bao_quan || undefined,
    custom_trang_thai_qc: 'Chờ kiểm',
    custom_so_tem: Math.max(1, Math.ceil(qty || 1)),
    custom_lenh_san_xuat: woName || undefined
  };
  if (meta.custom_han_dung_gio > 0) {
    var e = new Date(now.getTime() + meta.custom_han_dung_gio * 3600000);
    doc.expiry_date = ymdOf(e);
    doc.custom_gio_het_han = hmOf(e);
  } else if (meta.shelf_life_in_days > 0) {
    doc.expiry_date = addDays(d0, meta.shelf_life_in_days);
    doc.custom_gio_het_han = hmOf(now);
  }
  var b = await api('frappe.client.insert', { doc: doc });
  return b && b.name;
}

/* --- Ban thanh pham lam tuoi: may tu lam noi duoi truoc khi hoan tat mon cha --- */
async function mfgFreshPlan(mats, ratio, src) {
  if (!mats || !mats.length) return [];
  var codes = mats.map(function (m) { return m.item_code; });
  var fr = await freshOf(codes);
  var fresh = codes.filter(function (c) { return fr[c]; });
  if (!fresh.length) return [];
  var bm = await bomOf(fresh);
  var tn = await stockOf(fresh, src);
  var out = [];
  mats.forEach(function (m) {
    var c = m.item_code;
    if (!fr[c] || !bm[c]) return;
    var need = r3((m.required_qty || 0) * ratio);
    var miss = r3(need - (tn[c] || 0));
    if (miss > 0.0001) out.push({
      code: c, name: m.item_name || c, uom: m.stock_uom,
      qty: miss, bom: bm[c].name, fg: src, src: src
    });
  });
  return out;
}
async function mfgRunFresh(list, depth) {
  depth = depth || 1;
  for (var i = 0; i < list.length; i++) {
    var f = list[i];
    var wo = await mfgCreateWO(f);
    var d = await api('frappe.client.get', { doctype: 'Work Order', name: wo });
    if (depth < 3) {
      var sub = await mfgFreshPlan(d.required_items || [], 1, d.source_warehouse || mfg.src);
      if (sub.length) await mfgRunFresh(sub, depth + 1);
    }
    var it = await mfgLoadItem(f.code);
    var batch = await mfgMakeBatch(f.code, it, f.qty, wo);
    var se = await api('erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry',
      { work_order_id: wo, purpose: 'Manufacture', qty: f.qty });
    se.set_posting_time = 1; se.posting_date = today(); se.posting_time = nowStamp().slice(11);
    (se.items || []).forEach(function (r) {
      if (r.is_finished_item && batch) { r.use_serial_batch_fields = 1; r.batch_no = batch; }
    });
    var ins = await api('frappe.client.insert', { doc: se });
    await api('frappe.client.submit', { doc: ins });
  }
}

/* ---------- 12c-5. Mon chua co cong thuc: khai nguyen lieu ngay tren app ---------- */
async function scrMfgDeclare() {
  mfgInitWh();
  var st = mfgD;
  if (!st) return go(scrMfgList, true);

  function draw() {
    var body = mfgWhCard() +
      '<div class="ic1"><div class="ih">' +
      (st.meta && st.meta.image ? '<img class="im3" src="' + h(st.meta.image) + '">' : '<div class="im3 im3p">🍰</div>') +
      '<div class="in">' + h(st.name) + '<div class="ig">Mã: ' + h(st.code) + '</div></div></div>' +
      '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số lượng làm được</div>' +
      '<div class="qr"><div class="stp"><button data-fm>&minus;</button>' +
      '<input type="number" inputmode="decimal" id="mdq" value="' + st.qty + '"><button data-fp>+</button></div>' +
      '<div class="uml">' + h(st.stock_uom) + '</div></div></div></div></div>' +
      '<div class="sec">Nguyên liệu đã dùng</div>' +
      (st.mats.length ? st.mats.map(function (m, i) {
        var sel = '<select class="uom" data-u="' + i + '">' + (m.uoms || [{ uom: m.stock_uom, cf: 1 }]).map(function (u) {
          return '<option value="' + h(u.uom) + '"' + (u.uom === m.uom ? ' selected' : '') + '>' + h(u.uom) + '</option>';
        }).join('') + '</select>';
        return '<div class="ic1"><div class="ih"><div class="n">' + (i + 1) + '</div>' +
          '<div class="in">' + h(m.name) + '<div class="ig">Tồn ' + num(m.ton) + ' ' + h(m.stock_uom) + '</div></div>' +
          '<div class="del" data-x="' + i + '">&times;</div></div>' +
          '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số lượng đã dùng</div>' +
          '<div class="qr"><div class="stp"><button data-m="' + i + '">&minus;</button>' +
          '<input type="number" inputmode="decimal" data-q="' + i + '" value="' + m.qty + '">' +
          '<button data-p="' + i + '">+</button></div>' + sel + '</div></div></div></div>';
      }).join('') : '<div class="emp" style="padding:26px"><div class="e2">Chưa khai nguyên liệu nào</div></div>') +
      '<button class="btn gh" id="mdAdd">+ Thêm nguyên liệu</button>' +
      '<div class="card" style="margin-top:12px"><div class="fld" data-sb>' +
      '<div class="fi">💾</div><div class="ft"><div class="fl">Lần sau khỏi khai lại</div>' +
      '<div class="fv">Lưu thành công thức của món này</div></div>' +
      '<div class="ck' + (st.saveBom ? ' on' : '') + '">&#10003;</div></div></div>';

    var b = frame('Khai nguyên liệu', body, {
      footer: '<button class="btn gr" id="mdGo"' + (st.mats.length ? '' : ' disabled') + '>Xong - trừ kho nguyên liệu</button>'
    });
    b.addEventListener('input', function (e) {
      var t = e.target;
      if (t.id === 'mdq') st.qty = parseFloat(t.value) || 0;
      if (t.dataset.q != null) st.mats[+t.dataset.q].qty = parseFloat(t.value) || 0;
    });
    b.addEventListener('change', function (e) {
      var t = e.target;
      if (t.dataset.u != null) {
        var m = st.mats[+t.dataset.u];
        m.uom = t.value;
        var u = (m.uoms || []).filter(function (x) { return x.uom === t.value; })[0];
        m.cf = u ? u.cf : 1;
      }
    });
    b.onclick = function (e) {
      if (mfgWhTap(e, draw)) return;
      if (e.target.closest('[data-sb]')) { st.saveBom = st.saveBom ? 0 : 1; return draw(); }
      var t = e.target.closest('[data-fm],[data-fp],[data-x],[data-m],[data-p]'); if (!t) return;
      if (t.hasAttribute('data-fm')) { st.qty = Math.max(0, r3(st.qty - 1)); document.getElementById('mdq').value = st.qty; return; }
      if (t.hasAttribute('data-fp')) { st.qty = r3(st.qty + 1); document.getElementById('mdq').value = st.qty; return; }
      if (t.dataset.x != null) { st.mats.splice(+t.dataset.x, 1); return draw(); }
      if (t.dataset.m != null) { var i = +t.dataset.m; st.mats[i].qty = Math.max(0, r3(st.mats[i].qty - 1)); var el = b.querySelector('[data-q="' + i + '"]'); if (el) el.value = st.mats[i].qty; return; }
      if (t.dataset.p != null) { var j = +t.dataset.p; st.mats[j].qty = r3(st.mats[j].qty + 1); var e2 = b.querySelector('[data-q="' + j + '"]'); if (e2) e2.value = st.mats[j].qty; }
    };
    document.getElementById('mdAdd').onclick = function () {
      mfgPickItem('Chọn nguyên liệu', null, async function (code) {
        if (code === st.code) return toast('Không thể dùng chính món đang làm làm nguyên liệu');
        if (st.mats.some(function (x) { return x.code === code; })) return toast('Nguyên liệu này đã có trong danh sách');
        busy(1);
        try {
          var it = await mfgLoadItem(code);
          var tn = await stockOf([code], mfg.src);
          var u0 = it.uoms[0] || { uom: it.stock_uom, cf: 1 };
          st.mats.push({ code: code, name: it.item_name || code, stock_uom: it.stock_uom, uom: it.stock_uom, cf: 1, uoms: it.uoms, qty: 1, ton: tn[code] || 0 });
          draw();
        } catch (err) { toast(errMsg(err)); } finally { busy(0); }
      });
    };
    document.getElementById('mdGo').onclick = mfgDeclareSubmit;
  }
  draw();
}

async function mfgDeclareSubmit() {
  var st = mfgD;
  if (!(st.qty > 0)) return toast('Chưa nhập số lượng làm được');
  if (!st.mats.length) return toast('Chưa khai nguyên liệu nào');
  if (st.mats.some(function (m) { return !(m.qty > 0); })) return toast('Có nguyên liệu chưa nhập số lượng');
  if (!mfg.src || !mfg.fg) return toast('Chưa chọn kho nguyên liệu hoặc kho thành phẩm');
  var ok = await confirmSheet('Trừ kho nguyên liệu',
    'Máy sẽ trừ ' + st.mats.length + ' nguyên liệu tại kho ' + shortWh(mfg.src) + ' và nhập ' + num(st.qty) + ' ' + st.stock_uom + ' ' + st.name + ' vào kho ' + shortWh(mfg.fg) + '. Bút toán kho không sửa lại được.',
    'Xác nhận trừ kho');
  if (!ok) return;
  busy(1);
  try {
    var batch = await mfgMakeBatch(st.code, st.meta, st.qty, '');
    var items = st.mats.map(function (m) {
      return { item_code: m.code, qty: m.qty, uom: m.uom, conversion_factor: m.cf || 1, s_warehouse: mfg.src };
    });
    var fg = { item_code: st.code, qty: st.qty, uom: st.stock_uom, conversion_factor: 1, t_warehouse: mfg.fg, is_finished_item: 1 };
    if (batch) { fg.use_serial_batch_fields = 1; fg.batch_no = batch; }
    items.push(fg);
    var doc = {
      doctype: 'Stock Entry', company: COMPANY,
      stock_entry_type: 'Manufacture', purpose: 'Manufacture', from_bom: 0,
      set_posting_time: 1, posting_date: today(), posting_time: nowStamp().slice(11),
      from_warehouse: mfg.src, to_warehouse: mfg.fg, items: items,
      remarks: 'Bếp khai nguyên liệu trên app - ' + (S.me.full_name || S.user)
    };
    var ins = await api('frappe.client.insert', { doc: doc });
    await api('frappe.client.submit', { doc: ins });
    busy(0);
    toast('Đã trừ kho nguyên liệu');
    if (st.saveBom) {
      busy(1);
      try {
        await api('frappe.client.insert', {
          doc: {
            doctype: 'BOM', item: st.code, company: COMPANY, quantity: st.qty, uom: st.stock_uom,
            currency: 'VND', is_active: 1, is_default: 1, with_operations: 0, rm_cost_as_per: 'Valuation Rate',
            items: st.mats.map(function (m) {
              return { item_code: m.code, qty: m.qty, uom: m.uom, stock_uom: m.stock_uom, conversion_factor: m.cf || 1 };
            })
          }
        });
        toast('Đã lưu công thức nháp, quản lý bếp duyệt là lần sau khỏi khai lại', 5000);
      } catch (e2) { toast('Đã trừ kho xong. Phần lưu công thức chưa được: ' + errMsg(e2), 6000); }
      busy(0);
    }
    if (!batch) return go(scrMfgList, true);
    mfgL = { batch: batch, item: st.code, name: st.name, qty: st.qty, uom: st.stock_uom, meta: st.meta };
    return go(scrMfgLabel, true);
  } catch (err) { busy(0); toast(errMsg(err), 7000); }
}

/* ---------- 12c-6. In tem HACCP ---------- */
function mfgBqText(v) {
  return v === 'Freeze' ? 'CẤP ĐÔNG -18°C' : (v === 'Chill' ? 'BẢO QUẢN MÁT 0 - 5°C' : (v === 'Room Temp' ? 'NHIỆT ĐỘ PHÒNG dưới 25°C' : ''));
}
function scrMfgLabel() {
  var L = mfgL;
  if (!L) return go(scrMfgList, true);
  if (!L.n) L.n = Math.max(1, Math.ceil(L.qty || 1));
  var m = L.meta || {};
  var nw = new Date();
  var nsx = ymdOf(nw), gsx = hmOf(nw).slice(0, 5), hsd = '', ghh = '';
  if (m.custom_han_dung_gio > 0) {
    var ex = new Date(nw.getTime() + m.custom_han_dung_gio * 3600000);
    hsd = ymdOf(ex); ghh = hmOf(ex).slice(0, 5);
  } else if (m.shelf_life_in_days > 0) {
    hsd = addDays(nsx, m.shelf_life_in_days); ghh = gsx;
  }
  var bq = mfgBqText(m.custom_dieu_kien_bao_quan);

  function draw() {
    var body = '<div class="rcvh">' + (L.pre
      ? 'Đây là tem của mẻ này. Bếp in trước để dán cũng được, sau đó quay lại bấm Hoàn tất để trừ nguyên liệu.'
      : 'Sản xuất xong rồi. Bấm In tem để gửi sang máy in Brother, rồi dán lên từng cái bánh.') + '</div>' +
      '<div class="mtem"><div class="t1">' + h(L.name) + '</div>' +
      '<div class="t2"><b>NSX</b> ' + dmy(nsx) + ' ' + gsx +
      (hsd ? ' &nbsp; <b>HSD</b> ' + dmy(hsd) + ' ' + ghh : '') + '</div>' +
      (bq ? '<div class="bq">' + h(bq) + '</div>' : '') +
      '<div class="bcd">' + h(L.batch) + '</div></div>' +
      '<div class="card"><div class="qw"><div style="flex:1;min-width:0"><div class="lb">Số tem cần in</div>' +
      '<div class="qr"><div class="stp"><button data-m>&minus;</button>' +
      '<input type="number" inputmode="numeric" id="mln" value="' + L.n + '"><button data-p>+</button></div>' +
      '<div class="uml">tem</div></div></div></div></div>' +
      '<button class="btn gh" id="mlOne" style="margin-bottom:12px">In thử 1 tem</button>';

    var b = frame('In tem HACCP', body, { footer: '<button class="btn" id="mlGo">🖨️ In ' + L.n + ' tem</button>' });
    b.addEventListener('input', function (e) { if (e.target.id === 'mln') L.n = Math.max(1, parseInt(e.target.value, 10) || 1); });
    b.onclick = function (e) {
      var t = e.target.closest('[data-m],[data-p]'); if (!t) return;
      if (t.hasAttribute('data-m')) L.n = Math.max(1, L.n - 1); else L.n = L.n + 1;
      var el = document.getElementById('mln'); if (el) el.value = L.n;
      var g = document.getElementById('mlGo'); if (g) g.textContent = '🖨️ In ' + L.n + ' tem';
    };
    document.getElementById('mlOne').onclick = function () { mfgPrint(L.batch, 1); };
    document.getElementById('mlGo').onclick = function () { mfgPrint(L.batch, L.n); };
  }
  draw();
}
function mfgPrint(batch, n) {
  var w = window.open('', '_blank');
  var fmt = n > 1 ? 'Vagabond - Tem HACCP nhieu tem' : 'Vagabond - Tem HACCP';
  api('frappe.client.set_value', { doctype: 'Batch', name: batch, fieldname: { custom_so_tem: n } })
    .catch(function () { })
    .then(function () {
      var u = '/printview?doctype=Batch&name=' + encodeURIComponent(batch) +
        '&format=' + encodeURIComponent(fmt) + '&no_letterhead=1&trigger_print=1';
      if (w) { w.location.href = u; } else { window.location.href = u; }
    });
}

/* ---------- 13. Nhap kho tu Don mua hang ---------- */
function isKho() { return hasRole('Stock Manager') || hasRole('Stock User') || hasRole('System Manager'); }
function r3(v) { return Math.round((v || 0) * 1000) / 1000; }
var rcv = { q: '', tab: 'cho' };

async function scrRecvList() {
  vgbCss();
  frame('Nhập kho', '<div class="emp"><div class="e1">⏳</div></div>');
  var TB = [
    { k: 'cho', ten: 'Chờ nhận', ds: 0 },
    { k: 'xong', ten: 'Đã nhập kho', ds: 1 },
    { k: 'huy', ten: 'Đã huỷ', ds: 2 }
  ];
  if (!rcv.tab) rcv.tab = 'cho';
  var D = {}, dem = {};
  for (var ti = 0; ti < TB.length; ti++) {
    var t = TB[ti], f = { docstatus: t.ds };
    if (t.ds === 1) f.posting_date = ['>=', new Date(Date.now() - 7 * 864e5).toISOString().slice(0, 10)];
    if (t.ds === 2) f.posting_date = ['>=', new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10)];
    var docs = [];
    try {
      docs = await getList('Purchase Receipt', {
        fields: ['name', 'supplier', 'supplier_name', 'posting_date', 'set_warehouse'],
        filters: f, limit_page_length: 0, order_by: 'modified desc'
      });
    } catch (e) { }
    D[t.k] = docs; dem[t.k] = docs.length;
  }
  var all = [];
  for (var k2 in D) D[k2].forEach(function (x) { all.push(x.name); });
  var rows = [];
  if (all.length) {
    try {
      rows = await getList('Purchase Receipt Item', {
        parent: 'Purchase Receipt', fields: ['parent', 'qty', 'warehouse'],
        filters: { parent: ['in', all] }, limit_page_length: 0
      });
    } catch (e) { }
  }
  var CHIP = { cho: ['c2', 'Chờ nhận'], xong: ['d', 'Đã nhập kho'], huy: ['x', 'Đã huỷ'] };

  function tabsHtml() {
    return '<div class="vtb">' + TB.map(function (t) {
      return '<div class="vt' + (rcv.tab === t.k ? ' on' : '') + '" data-tb="' + t.k + '">' +
        h(t.ten) + (dem[t.k] ? ' <b>' + dem[t.k] + '</b>' : '') + '</div>';
    }).join('') + '</div>';
  }
  function listHtml() {
    var q = (rcv.q || '').toLowerCase().trim();
    var ls = (D[rcv.tab] || []).filter(function (x) {
      if (!q) return true;
      return (x.name + ' ' + (x.supplier_name || x.supplier || '')).toLowerCase().indexOf(q) >= 0;
    });
    if (!ls.length) {
      var rong = rcv.tab === 'cho' ?
        'Chưa có phiếu nào chờ nhận hàng.<br>Thu mua tạo phiếu nhập kho nháp từ Đơn mua hàng thì phiếu sẽ hiện ở đây.' :
        (rcv.tab === 'xong' ? 'Chưa có phiếu nào nhập kho trong 7 ngày qua.' : 'Không có phiếu huỷ nào trong 30 ngày qua.');
      return '<div class="emp"><div class="e1">📦</div><div class="e2">' +
        ((D[rcv.tab] || []).length ? 'Không tìm thấy phiếu nào' : rong) + '</div></div>';
    }
    var c = CHIP[rcv.tab];
    return '<div class="lst">' + ls.map(function (x) {
      var rs = rows.filter(function (r) { return r.parent === x.name; });
      var whs = [];
      rs.forEach(function (r) { var w = shortWh(r.warehouse); if (w && whs.indexOf(w) < 0) whs.push(w); });
      return '<div class="li" data-p="' + h(x.name) + '"><div class="lt">' +
        '<div class="l1">' + h(x.supplier_name || x.supplier || x.name) + '</div>' +
        '<div class="l2">' + h(x.name) + ' · ' + rs.length + ' món · ' + h(whs.join(', ') || shortWh(x.set_warehouse) || '') + '</div></div>' +
        '<span style="text-align:right;flex:none"><span class="vxtag ' + c[0] + '">' + c[1] + '</span>' +
        '<div style="font-size:12px;color:#98a2b3;margin-top:4px">' + h(dmy(x.posting_date)) + '</div></span></div>';
    }).join('') + '</div>';
  }

  var body = tabsHtml() +
    '<div class="rcvh">Quét mã vạch số phiếu ở đầu tờ phiếu in để mở đúng phiếu, hoặc chọn trong danh sách bên dưới.</div>' +
    srchBox('rcvq', 'Tìm số phiếu hoặc nhà cung cấp', rcv.q, true) +
    '<div id="rcvl">' + listHtml() + '</div>';

  var b = frame('Nhập kho', body, { action: '&#128247;', onAction: rcvScanOpen });
  var qi = document.getElementById('rcvq');
  if (qi) qi.oninput = function () { rcv.q = qi.value; var el = document.getElementById('rcvl'); if (el) el.innerHTML = listHtml(); };
  var sb = document.getElementById('rcvqscan');
  if (sb) sb.onclick = rcvScanOpen;
  b.onclick = function (e) {
    var tb = e.target.closest('[data-tb]');
    if (tb) {
      rcv.tab = tb.dataset.tb;
      var ts = b.querySelectorAll('[data-tb]');
      for (var i = 0; i < ts.length; i++) ts[i].classList.toggle('on', ts[i].dataset.tb === rcv.tab);
      var el = document.getElementById('rcvl'); if (el) el.innerHTML = listHtml();
      return;
    }
    var r = e.target.closest('[data-p]');
    if (r) {
      var nm = r.dataset.p;
      if (rcv.tab === 'cho') return go(function () { scrRecvDoc(nm); });
      return go(function () { rcvXemXong(nm); });
    }
  };
}

/* Khu chung tu giao nhan: 2 anh hang + ban scan bien ban NCC */
function rcvAnhHtml(doc) {
  function o(url, ten) {
    if (!url) return '';
    var laPdf = String(url).toLowerCase().indexOf('.pdf') >= 0;
    var trong = laPdf ? '<div class="rcvthf">📄</div>' : '<img class="rcvthi" src="' + h(url) + '" loading="lazy">';
    return '<a class="rcvth" href="' + h(url) + '" target="_blank">' + trong + '<span>' + ten + '</span></a>';
  }
  var s = o(doc.custom_hinh_nhan_hang_1, 'Ảnh hàng (1)') +
    o(doc.custom_hinh_nhan_hang_2, 'Ảnh hàng (2)') +
    o(doc.custom_scan_bien_ban, 'Biên bản NCC');
  if (!s) s = '<div style="color:#98a2b3;font-size:13px;padding:2px 14px 8px">Chưa đính kèm ảnh hay biên bản lúc nhận.</div>';
  return '<div class="sec">Chứng từ giao nhận</div><div class="rcvths">' + s + '</div>';
}

/* Xem phieu da nhap / da huy - chi doc */
async function rcvXemXong(name) {
  frame('Nhập kho', '<div class="emp"><div class="e1">⏳</div></div>');
  var doc = null;
  try { doc = await api('frappe.client.get', { doctype: 'Purchase Receipt', name: name }); }
  catch (e) { toast(errMsg(e)); return back(); }
  vgbCss();
  var tag = doc.docstatus === 1 ? '<span class="vxtag d">Đã nhập kho</span>' :
    (doc.docstatus === 2 ? '<span class="vxtag x">Đã huỷ</span>' : '<span class="vxtag c2">Chờ nhận</span>');
  var s = '<div class="card">' +
    '<div class="kv"><span>Nhà cung cấp</span><b>' + h(doc.supplier_name || doc.supplier || '') + '</b></div>' +
    '<div class="kv"><span>Ngày</span><b>' + h(dmy(doc.posting_date)) + '</b></div>' +
    '<div class="kv"><span>Trạng thái</span><b>' + tag + '</b></div></div>' +
    '<div class="sec">' + (doc.items || []).length + ' hàng hoá</div><div class="lst">' +
    (doc.items || []).map(function (r) {
      return '<div class="li"><div class="lt"><div class="l1">' + h(r.item_name || r.item_code) + '</div>' +
        '<div class="l2">' + h(r.item_code) + ' · ' + h(shortWh(r.warehouse) || '') + '</div></div>' +
        '<span class="st b">' + num(r.qty) + ' ' + h(r.uom || '') + '</span></div>';
    }).join('') + '</div>' + rcvAnhHtml(doc);
  frame('Phiếu ' + name, s);
}


async function rcvScanOpen() {
  var code = await scanBarcode(null);
  if (!code) return;
  code = String(code).trim().replace(/^\*+|\*+$/g, '').toUpperCase();
  busy(1);
  var r = [];
  try { r = await getList('Purchase Receipt', { fields: ['name', 'docstatus'], filters: { name: code }, limit_page_length: 1 }); } catch (e) { }
  busy(0);
  if (!r.length) return toast('Không thấy phiếu ' + code + ' trong hệ thống');
  if (r[0].docstatus === 1) return toast('Phiếu ' + code + ' đã nhập máy xong rồi');
  if (r[0].docstatus === 2) return toast('Phiếu ' + code + ' đã bị huỷ');
  go(function () { scrRecvDoc(code); });
}

var rcvD = null;

function hsdNote(x) {
  if (!x.hsd) return 'Món này chưa có hạn chuẩn, xem bao bì rồi điền giúp.';
  if (x.dflt) return 'Máy tự tính sẵn: ' + dmy(x.hsd) + '. Bao bì ghi hạn khác thì bấm vào sửa lại.';
  return 'Lấy theo bao bì: ' + dmy(x.hsd) + ', khác với hạn chuẩn.';
}
async function scrRecvDoc(name) {
  frame('Nhập kho', '<div class="emp"><div class="e1">\u23f3</div></div>');
  var doc = null;
  try { doc = await api('frappe.client.get', { doctype: 'Purchase Receipt', name: name }); }
  catch (e) { toast(errMsg(e)); return back(); }
  if (!doc || !doc.items || !doc.items.length) { toast('Phiếu này không có dòng hàng nào'); return back(); }

  var codes = doc.items.map(function (r) { return r.item_code; });
  var bat = {}, slf = {};
  var base = String(doc.posting_date || '').slice(0, 10) || today();
  try {
    var its = await getList('Item', { fields: ['name', 'has_batch_no', 'shelf_life_in_days'], filters: { name: ['in', codes] }, limit_page_length: 0 });
    its.forEach(function (x) { bat[x.name] = x.has_batch_no ? 1 : 0; slf[x.name] = x.shelf_life_in_days || 0; });
  } catch (e) { }

  rcvD = {
    name: name, doc: doc,
    anh1: doc.custom_hinh_nhan_hang_1 || '', anh2: doc.custom_hinh_nhan_hang_2 || '', scan: doc.custom_scan_bien_ban || '',
    lines: doc.items.map(function (r) {
      return {
        row: r.name, code: r.item_code, nm: r.item_name || r.item_code,
        uom: r.uom || r.stock_uom || '', wh: r.warehouse, ord: r.qty || 0,
        got: r.qty || 0, sl: slf[r.item_code] || 0,
        hsd: r.han_su_dung || (slf[r.item_code] ? addDays(base, slf[r.item_code]) : ''),
        dflt: r.han_su_dung ? 0 : 1, batch: bat[r.item_code] ? 1 : 0, ok: 0
      };
    })
  };

  function syncHdr() {
    var L = rcvD.lines, okN = L.filter(function (x) { return x.ok; }).length;
    var t = document.getElementById('rcvpt'), pb = document.getElementById('rcvpb');
    if (t) t.textContent = 'ĐÃ ĐẾM ' + okN + '/' + L.length + ' MÓN';
    if (pb) pb.style.width = (L.length ? Math.round(okN * 100 / L.length) : 0) + '%';
  }
  function syncRow(i) {
    var x = rcvD.lines[i], el = document.querySelector('#vgbBody [data-r="' + i + '"]');
    if (!el) return;
    if (x.ok) el.classList.add('ok'); else el.classList.remove('ok');
    if (x.got > 0) el.classList.remove('zero'); else el.classList.add('zero');
    var q = el.querySelector('[data-q]');
    if (q && String(q.value) !== String(x.got)) q.value = x.got;
    var lb = el.querySelector('.lb');
    if (lb) lb.innerHTML = 'Số lượng thực nhận' + (Math.abs(x.got - x.ord) > 0.0001 ? ' <b class="lbw">(lệch so với đặt)</b>' : '');
    syncHdr();
  }

  async function scanTick() {
    await scanBarcode(async function (code) {
      var ic = await itemByBarcode(code);
      if (!ic) return 'Chưa nhận ra mã ' + code;
      var i = -1, L = rcvD.lines;
      for (var j = 0; j < L.length; j++) if (L[j].code === ic) { i = j; break; }
      if (i < 0) return ic + ' không có trong phiếu này';
      L[i].ok = 1;
      syncRow(i);
      return '\u2713 ' + L[i].nm + ' \u00b7 đặt ' + num(L[i].ord) + ' ' + L[i].uom;
    });
  }

  async function doSubmit() {
    var L = rcvD.lines;
    var keep = L.filter(function (x) { return (x.got || 0) > 0; });
    if (!keep.length) return toast('Chưa có món nào có số lượng, chưa nhập kho được');
    var du = L.filter(function (x) { return (x.got || 0) > (x.ord || 0) + 0.0001; });
    if (du.length) return toast('Nhà cung cấp giao dư ' + du.length + ' món so với đơn đặt. Chỉ nhập đúng số đã đặt, phần dư báo chị Uyên lên đơn bổ sung rồi nhập sau.', 7000);
    var thieu = L.filter(function (x) { return (x.got || 0) < (x.ord || 0) - 0.0001; });
    var msg = 'Nhập kho ' + keep.length + ' món.';
    if (thieu.length) msg += ' Có ' + thieu.length + ' món nhận thiếu hoặc không về, phần còn lại vẫn treo trên đơn mua hàng để lần sau nhận tiếp.';
    msg += ' Xác nhận xong là phiếu khoá lại, muốn sửa phải báo kế toán.';
    if (!await confirmSheet('Xác nhận nhập kho?', msg, 'Nhập kho')) return;
    busy(1);
    try {
      var d = rcvD.doc, byRow = {};
      if (rcvD.anh1) d.custom_hinh_nhan_hang_1 = rcvD.anh1;
      if (rcvD.anh2) d.custom_hinh_nhan_hang_2 = rcvD.anh2;
      if (rcvD.scan) d.custom_scan_bien_ban = rcvD.scan;
      L.forEach(function (x) { byRow[x.row] = x; });
      d.items = d.items.filter(function (r) { var x = byRow[r.name]; return x && x.got > 0; });
      d.items.forEach(function (r) {
        var x = byRow[r.name];
        r.qty = x.got; r.received_qty = x.got; r.rejected_qty = 0;
        if (x.batch && x.hsd) r.han_su_dung = x.hsd;
      });
      /* Bo sung gia tam cho dong chua co gia tren don */
      var zeroRows = d.items.filter(function (r) { return !((r.rate || 0) > 0); });
      var chuaGia = [];
      if (zeroRows.length) {
        var zc = [];
        zeroRows.forEach(function (r) { if (zc.indexOf(r.item_code) < 0) zc.push(r.item_code); });
        var lastP = {};
        try {
          var pri = await getList('Purchase Receipt Item', {
            parent: 'Purchase Receipt',
            fields: ['item_code', 'rate', 'conversion_factor', 'creation'],
            filters: { item_code: ['in', zc], docstatus: 1, rate: ['>', 0] },
            order_by: 'creation desc', limit_page_length: 0
          });
          pri.forEach(function (x) { if (!lastP[x.item_code]) lastP[x.item_code] = x; });
        } catch (e1) { }
        var conCan = zc.filter(function (c0) { return !lastP[c0]; });
        if (conCan.length) {
          try {
            var poi = await getList('Purchase Order Item', {
              parent: 'Purchase Order',
              fields: ['item_code', 'rate', 'conversion_factor', 'creation'],
              filters: { item_code: ['in', conCan], docstatus: 1, rate: ['>', 0] },
              order_by: 'creation desc', limit_page_length: 0
            });
            poi.forEach(function (x) { if (!lastP[x.item_code]) lastP[x.item_code] = x; });
          } catch (e2) { }
        }
        zeroRows.forEach(function (r) {
          var gg = r.purchase_order ? null : lastP[r.item_code];
          if (gg) {
            var donVi = (gg.rate || 0) / (gg.conversion_factor || 1);
            r.rate = Math.round(donVi * (r.conversion_factor || 1) * 100) / 100;
          } else {
            r.allow_zero_valuation_rate = 1;
            chuaGia.push(r.item_name || r.item_code);
          }
        });
        d.remarks = (d.remarks || '') + (chuaGia.length
          ? ' | Nhap kho khi chua co gia: ' + chuaGia.join(', ') + ' - ke toan bo sung gia sau.'
          : ' | May tu lay gia mua gan nhat cho ' + zeroRows.length + ' dong chua co gia tren don.');
        if (chuaGia.length) setTimeout(function () { toast('Có ' + chuaGia.length + ' món nhập kho khi chưa có giá. Báo kế toán bổ sung giá giúp em.', 7000); }, 1400);
      }

      await api('frappe.client.submit', { doc: d });
      busy(0);
      rcv.tab = 'xong';
      toast('✓ Đã nhập kho phiếu ' + rcvD.name + '. Phiếu nằm ở tab Đã nhập kho.');
      return back();
    } catch (e) { busy(0); toast(errMsg(e)); }
  }

  function draw() {
    var L = rcvD.lines;
    var okN = L.filter(function (x) { return x.ok; }).length;
    var body = '<div class="card"><div class="kpg"><div class="kpt" id="rcvpt">ĐÃ ĐẾM ' + okN + '/' + L.length + ' MÓN</div>' +
      '<div class="kpb"><i id="rcvpb" style="width:' + (L.length ? Math.round(okN * 100 / L.length) : 0) + '%"></i></div></div>' +
      '<div class="kv"><span>Nhà cung cấp</span><b>' + h(doc.supplier_name || doc.supplier || '') + '</b></div>' +
      '<div class="kv"><span>Số phiếu</span><b>' + h(name) + '</b></div></div>';
    body += '<div class="rcvh">Đếm tới đâu sửa số tới đó, số điền sẵn là số đã đặt. Không nhập quá số đã đặt: nhà cung cấp giao dư thì báo thu mua lên đơn bổ sung. Bấm nút máy ảnh ở góc trên để quét mã từng món cho nhanh.</div>';
    var chuaGiaN = (doc.items || []).filter(function (rr) { return !((rr.rate || 0) > 0); }).length;
    if (chuaGiaN) body += '<div style="margin:10px 12px;padding:12px 14px;border-radius:14px;background:#fff6e5;color:#8a5b00;font-size:13px;line-height:1.5">Đơn này có ' + chuaGiaN + ' món chưa có đơn giá. Vẫn nhập kho được nhưng giá vốn ghi 0, nhớ báo kế toán bổ sung giá.</div>';
    body += L.map(function (x, i) {
      return '<div class="ic1' + (x.ok ? ' ok' : '') + (x.got > 0 ? '' : ' zero') + '" data-r="' + i + '">' +
        '<div class="ih"><div class="n">' + (i + 1) + '</div>' +
        '<div class="in">' + h(x.nm) +
        '<div class="ig">' + h(x.code) + ' \u00b7 Đặt ' + num(x.ord) + ' ' + h(x.uom) + ' \u00b7 ' + h(shortWh(x.wh) || '') + '</div></div>' +
        '<div class="rok" data-ok="' + i + '">&#10003;</div></div>' +
        '<div class="qw"><div style="flex:1;min-width:0">' +
        '<div class="lb">Số lượng thực nhận' + (Math.abs(x.got - x.ord) > 0.0001 ? ' <b class="lbw">(lệch so với đặt)</b>' : '') + '</div>' +
        '<div class="qr"><div class="stp"><button data-m="' + i + '">&minus;</button>' +
        '<input type="number" inputmode="decimal" step="any" data-q="' + i + '" value="' + x.got + '">' +
        '<button data-a="' + i + '">+</button></div>' +
        '<div class="uml">' + h(x.uom) + '</div></div></div></div>' +
        (x.batch ? '<div class="hw"><div class="hl">Hạn sử dụng' +
          (x.sl ? '<b class="hbd">chuẩn ' + x.sl + ' ngày</b>' : '') + '</div>' +
          '<input type="date" class="hin' + (x.dflt ? '' : ' ed') + '" data-h="' + i + '" value="' + h(x.hsd) + '">' +
          '<div class="hn' + (x.dflt ? '' : ' ed') + '" data-hn="' + i + '">' + hsdNote(x) + '</div></div>' : '') +
        '</div>';
    }).join('');
    vgbCss();
    body += '<div class="sec">Chứng từ giao nhận (không bắt buộc)</div><div class="card" style="padding:12px">' +
      '<div class="vxl" style="margin-top:0">Ảnh hàng đã nhận (1)</div>' +
      '<input class="vxi" type="file" accept="image/*" id="rcvA1">' +
      '<div id="rcvA1ok" style="font-size:13px;color:#027a48;margin-top:4px"></div>' +
      '<div class="vxl">Ảnh hàng đã nhận (2)</div>' +
      '<input class="vxi" type="file" accept="image/*" id="rcvA2">' +
      '<div id="rcvA2ok" style="font-size:13px;color:#027a48;margin-top:4px"></div>' +
      '<div class="vxl">Bản scan hoặc ảnh biên bản giao nhận của NCC</div>' +
      '<input class="vxi" type="file" accept="image/*,.pdf" id="rcvA3">' +
      '<div id="rcvA3ok" style="font-size:13px;color:#027a48;margin-top:4px"></div></div>';

    var b = frame('Nhập kho', body, {
      action: '&#128247;', onAction: scanTick,
      footer: '<button class="btn" id="rcvSub">Xác nhận nhập kho</button>'
    });
    b.onclick = function (e) {
      var t = e.target.closest('[data-ok]');
      if (t) { var i = parseInt(t.dataset.ok, 10); L[i].ok = L[i].ok ? 0 : 1; return syncRow(i); }
      t = e.target.closest('[data-m]');
      if (t) { var j = parseInt(t.dataset.m, 10); L[j].got = Math.max(0, r3(L[j].got - 1)); L[j].ok = 1; return syncRow(j); }
      t = e.target.closest('[data-a]');
      if (t) { var k = parseInt(t.dataset.a, 10); var v1 = r3(L[k].got + 1); if (v1 > L[k].ord + 0.0001) { v1 = L[k].ord; toast('Chỉ nhập được tối đa ' + num(L[k].ord) + ' ' + L[k].uom + ' theo đơn đặt. Hàng giao dư phải báo thu mua lên đơn bổ sung.', 5200); } L[k].got = v1; L[k].ok = 1; return syncRow(k); }
    };
    Array.prototype.forEach.call(b.querySelectorAll('[data-q]'), function (el) {
      el.onchange = function () { var i = parseInt(el.dataset.q, 10); var v2 = Math.max(0, parseFloat(el.value) || 0); if (v2 > L[i].ord + 0.0001) { v2 = L[i].ord; toast('Chỉ nhập được tối đa ' + num(L[i].ord) + ' ' + L[i].uom + ' theo đơn đặt. Hàng giao dư phải báo thu mua lên đơn bổ sung.', 5200); } L[i].got = v2; L[i].ok = 1; syncRow(i); };
    });
    Array.prototype.forEach.call(b.querySelectorAll('[data-h]'), function (el) {
      el.onchange = function () {
        var i = parseInt(el.dataset.h, 10), x = L[i];
        if (!el.value && x.sl) el.value = addDays(base, x.sl);
        x.hsd = el.value || '';
        x.dflt = (x.sl && x.hsd === addDays(base, x.sl)) ? 1 : 0;
        el.classList.toggle('ed', !x.dflt);
        var nt = b.querySelector('[data-hn="' + i + '"]');
        if (nt) { nt.textContent = hsdNote(x); nt.classList.toggle('ed', !x.dflt); }
      };
    });
    var sb = document.getElementById('rcvSub');
    if (sb) sb.onclick = doSubmit;
    function ganAnh(id, key) {
      var inp = document.getElementById(id), ok = document.getElementById(id + 'ok');
      if (!inp) return;
      if (rcvD[key]) ok.innerHTML = 'Đã có tệp: <a href="' + h(rcvD[key]) + '" target="_blank">xem</a>';
      inp.onchange = async function () {
        var f = this.files && this.files[0];
        if (!f) return;
        ok.textContent = 'Đang tải lên...';
        try {
          rcvD[key] = await vxUpAnh(f);
          ok.innerHTML = 'Đã tải lên: <a href="' + h(rcvD[key]) + '" target="_blank">xem</a>';
        } catch (e) { ok.style.color = '#d92d20'; ok.textContent = 'Không tải được: ' + (e.message || e); }
      };
    }
    ganAnh('rcvA1', 'anh1'); ganAnh('rcvA2', 'anh2'); ganAnh('rcvA3', 'scan');
  }
  draw();
}

/* ---------- 14. Dang nhap - Tai khoan ---------- */
function scrLogin() {
  root.innerHTML =
    '<div class="lgw"><div class="lgb">' +
      '<img class="lgo" src="/files/vagabond_logo_print.png" alt="The Vagabond Pâtisserie">' +
      '<div class="lgc">' +
        '<div class="lgl">Tài khoản (email)</div>' +
        '<input class="lgi" id="lgU" type="email" inputmode="email" autocomplete="username" autocapitalize="off" autocorrect="off" spellcheck="false" placeholder="email@vagabond">' +
        '<div class="lgl">Mật khẩu</div>' +
        '<input class="lgi" id="lgP" type="password" autocomplete="current-password" placeholder="Nhập mật khẩu">' +
        '<div class="lge" id="lgE"></div>' +
        '<button class="btn" id="lgGo">Đăng nhập</button>' +
        '<div class="lgfp" id="lgFp">Quên mật khẩu?</div>' +
      '</div>' +
      '<div class="lgf">Ứng dụng nghiệp vụ nội bộ<br>Chưa có mật khẩu thì bấm dòng Quên mật khẩu ở trên.</div>' +
    '</div></div>';
  var iu = document.getElementById('lgU'), ip = document.getElementById('lgP'), ie = document.getElementById('lgE');
  function fail(m) { ie.textContent = m || ''; }
  var running = 0;
  async function doLogin() {
    if (running) return;
    var usr = (iu.value || '').trim(), pwd = ip.value || '';
    if (!usr || !pwd) return fail('Nhập đủ tài khoản và mật khẩu.');
    fail(''); running = 1; busy(1);
    try {
      var hd = { 'Content-Type': 'application/json', 'Accept': 'application/json' };
      try { if (window.frappe && frappe.csrf_token) hd['X-Frappe-CSRF-Token'] = frappe.csrf_token; } catch (e) { }
      var r = await fetch('/api/method/login', { method: 'POST', headers: hd, credentials: 'same-origin', body: JSON.stringify({ usr: usr, pwd: pwd }) });
      running = 0; busy(0);
      if (r.ok) { clearFresh(); hardNav(); return; }
      if (r.status === 401) return fail('Sai tài khoản hoặc mật khẩu.');
      if (r.status === 417) return fail('Tài khoản đang bị khoá hoặc chưa được kích hoạt.');
      fail('Không đăng nhập được (mã ' + r.status + ').');
    } catch (e) { running = 0; busy(0); fail('Lỗi kết nối, kiểm tra mạng rồi thử lại.'); }
  }
  var fp = document.getElementById('lgFp');
  if (fp) fp.onclick = async function () {
    var em = (iu.value || '').trim();
    ie.style.color = '#c0392b';
    if (!em) { iu.focus(); return fail('Nhập địa chỉ email của bạn vào ô trên rồi bấm lại dòng này.'); }
    fail(''); busy(1);
    try {
      var hf = { 'Content-Type': 'application/json', 'Accept': 'application/json' };
      try { if (window.frappe && frappe.csrf_token) hf['X-Frappe-CSRF-Token'] = frappe.csrf_token; } catch (e) { }
      var rr = await fetch('/api/method/frappe.core.doctype.user.user.reset_password', { method: 'POST', headers: hf, credentials: 'same-origin', body: JSON.stringify({ user: em }) });
      busy(0);
      if (rr.ok) { ie.style.color = '#0B7C93'; return fail('Đã gửi thư đặt lại mật khẩu tới ' + em + '. Mở thư rồi đặt mật khẩu mới, nhớ xem cả mục thư rác.'); }
      if (rr.status === 404 || rr.status === 417) return fail('Không có tài khoản nào dùng email này.');
      fail('Chưa gửi được thư (mã ' + rr.status + '), báo quản trị viên giúp.');
    } catch (e) { busy(0); fail('Lỗi kết nối, kiểm tra mạng rồi thử lại.'); }
  };
  document.getElementById('lgGo').onclick = doLogin;
  ip.onkeydown = function (e) { if (e.key === 'Enter') doLogin(); };
  iu.onkeydown = function (e) { if (e.key === 'Enter') ip.focus(); };
}

async function scrAccount() {
  var rl = (S.roles || []).slice().sort().join(', ');
  frame('Tài khoản', '<div class="card">' +
    '<div class="kv"><span>Họ tên</span><b>' + h(S.me.full_name || '-') + '</b></div>' +
    '<div class="kv"><span>Tài khoản</span><b>' + h(S.user || '-') + '</b></div>' +
    '<div class="kv"><span>Bộ phận</span><b>' + h(shortDep(S.me.bo_phan) || 'Chưa gắn') + '</b></div>' +
    '</div>' +
    '<div class="sec">Vai trò được cấp</div><div class="card">' +
    '<div style="padding:13px 14px;font-size:13.5px;color:#5a6070;line-height:1.6">' + h(rl || 'Chưa gắn vai trò nào') + '</div></div>' +
    '<div style="text-align:center;color:#a0a6b4;font-size:12px;padding:10px 10px 4px;line-height:1.6">' + h(APPNAME) + '</div>',
    { footer: '<button class="btn gh" id="acOut">Đăng xuất</button>' });
  var o = document.getElementById('acOut');
  if (o) o.onclick = async function () {
    if (!await confirmSheet('Đăng xuất khỏi app?', 'Bạn sẽ phải nhập lại tài khoản và mật khẩu.', 'Đăng xuất')) return;
    busy(1);
    var hdo = { 'Accept': 'application/json' };
    try { if (window.frappe && frappe.csrf_token) hdo['X-Frappe-CSRF-Token'] = frappe.csrf_token; } catch (e) { }
    try { await fetch('/api/method/logout', { method: 'POST', headers: hdo, credentials: 'same-origin' }); } catch (e) { }
    try { localStorage.removeItem('vgb_bp_' + S.user); } catch (e) { }
    clearFresh(); hardNav();
  };
}

/* ---------- 14. Kiem ke (stocktake) ---------- */
var KKSCOPE = [
  { value: 'Nguyên vật liệu', icon: '🥚', sub: 'Bột, sữa, trứng, trái cây, chocolate...', roots: ['Nguyên vật liệu Thô', 'Nguyên vật liệu Sonneto'] },
  { value: 'Bán thành phẩm', icon: '🧁', sub: 'Cốt bánh, nhân, kem, sốt đã làm sẵn', roots: ['Bán thành phẩm Bánh', 'Bán thành phẩm Nước', 'Nhân bán thành phẩm'] },
  { value: 'Thành phẩm', icon: '🎂', sub: 'Bánh và nước đã hoàn thiện, chờ bán', roots: ['Thành phẩm Bánh', 'Thành phẩm Nước'] },
  { value: 'Công cụ - Bao bì', icon: '📦', sub: 'Hộp, túi, khuôn, dụng cụ, văn phòng phẩm', roots: ['Công cụ Dụng cụ', 'Công cụ dụng cụ Sonneto', 'Bao bì', 'Văn phòng phẩm'] },
  { value: 'Tất cả', icon: '🗂️', sub: 'Toàn bộ hàng hoá có quản lý tồn kho', roots: null }
];
var KKST = {
  'Đang kiểm': { c: 'w', t: 'Đang kiểm' },
  'Chờ duyệt': { c: 'b', t: 'Chờ duyệt' },
  'Đã chốt': { c: 'b', t: 'Đã chốt' },
  'Đã ghi sổ': { c: 'g', t: 'Đã ghi sổ' },
  'Đã huỷ': { c: 'n', t: 'Đã huỷ' }
};
function kkScope(v) { for (var i = 0; i < KKSCOPE.length; i++) if (KKSCOPE[i].value === v) return KKSCOPE[i]; return KKSCOPE[0]; }
function kkAllUnder(roots) {
  var out = [];
  function walk(nm) { if (out.indexOf(nm) < 0) out.push(nm); (S.gtree[nm] || []).forEach(walk); }
  (roots || []).forEach(walk);
  return out;
}
function kkGroups(v) { var s = kkScope(v); return s.roots ? kkAllUnder(s.roots) : null; }
function kkCanPost() { return hasRole('Stock Manager') || hasRole('System Manager') || shortDep(S.me.bo_phan) === 'Giám đốc'; }
/* Kho khoa so: chi nhung nguoi trong danh sach (hoac nguoi ghi so duoc) moi sua duoc so kiem ke.
   Nguoi khac van mo phieu xem binh thuong de tham chieu ton kho luc dat hang. */
var KKWLOCK = { 'Kho tổng 307 - TV': ['kiendoforwork@gmail.com'] };
function kkWhOwner(wh) { return KKWLOCK[wh] || null; }
function kkCanEditWh(wh) {
  var l = kkWhOwner(wh);
  if (!l) return true;
  return l.indexOf(S.user) >= 0 || kkCanPost();
}
function kkLockNote(wh) {
  return 'Kho ' + h(shortWh(wh)) + ' do anh Kiên chốt số. Bạn mở được để xem và tham chiếu tồn, nhưng không sửa số trong phiếu kho này.';
}
function kkNum(v) { var n = parseFloat(v); return isNaN(n) ? 0 : r3(n); }

var kk = { doc: null, rows: [], cat: null, catKey: '', sys: {}, conv: {}, convLoaded: 0, tab: 'da', q: '', dirty: 0, savedAt: '', saving: 0, tmr: null, newf: null };

/* ---------- 14-0. Quy doi don vi tinh khi dem ----------
   Ton kho luon ghi so bang don vi goc (gram / ml / cai). Nhung luc dem thi
   nguoi kiem can dem theo quy cach: 3 bich nguyen + 800 gram cua bich mo do.
   Nen 1 mon co the co nhieu dong dem bang nhieu don vi, cong lai ra don vi goc. */

/* Kg / Lit la don vi chung, khong phai quy cach dong goi cua rieng mon nao */
var KKGEN = { 'Kg': 1, 'KG': 1, 'Kilogram': 1, 'Tấn': 1, 'Lít': 1, 'Lit': 1, 'Litre': 1, 'Liter': 1, 'Gram': 1, 'ML': 1, 'Ml': 1, 'ml': 1 };

async function kkLoadConv() {
  if (kk.convLoaded) return kk.conv;
  var m = {};
  try {
    var rs = await getList('UOM Conversion Detail', {
      parent: 'Item', parenttype: 'Item',
      fields: ['parent', 'uom', 'conversion_factor'],
      filters: { parenttype: 'Item' }, limit_page_length: 0
    });
    rs.forEach(function (x) {
      var f = parseFloat(x.conversion_factor);
      if (!x.parent || !x.uom || !f || f <= 0) return;
      (m[x.parent] = m[x.parent] || []).push({ uom: x.uom, f: f });
    });
    kk.convLoaded = 1;
  } catch (e) { }
  kk.conv = m;
  return m;
}

/* danh sach o nhap cho 1 mon: quy cach lon -> nho, cuoi cung luon la don vi goc */
function kkUnits(r) {
  var out = (kk.conv[r.item_code] || []).filter(function (u) {
    return u.uom !== r.dvt && Math.abs(u.f - 1) > 1e-9;
  }).slice().sort(function (a, b) { return b.f - a.f; });
  out.push({ uom: r.dvt || 'Đơn vị', f: 1 });
  return out;
}
/* don vi dong goi thuc su (bo qua Kg/Lit chung chung) - dung cho quet lien tuc */
function kkPack(r) {
  var c = (kk.conv[r.item_code] || []).filter(function (u) {
    return u.f > 0 && Math.abs(u.f - 1) > 1e-9 && !KKGEN[u.uom] && u.uom !== r.dvt;
  }).slice().sort(function (a, b) { return a.f - b.f; });
  return c[0] || null;
}
/* ma hoa cach dem: "Bịch|3|2500;Gram|800|1" */
function kkPartsEnc(ps) {
  return ps.filter(function (p) { return kkNum(p.qty) > 0; })
    .map(function (p) { return p.uom + '|' + r3(kkNum(p.qty)) + '|' + (parseFloat(p.f) || 1); }).join(';');
}
function kkPartsDec(s) {
  return String(s || '').split(';').filter(Boolean).map(function (x) {
    var a = x.split('|');
    return { uom: a[0], qty: kkNum(a[1]), f: parseFloat(a[2]) || 1 };
  });
}
function kkPartsSum(ps) {
  var t = 0;
  ps.forEach(function (p) { t += kkNum(p.qty) * (parseFloat(p.f) || 1); });
  return r3(t);
}
function kkPartsText(s) {
  var ps = kkPartsDec(s).filter(function (p) { return kkNum(p.qty) > 0; });
  if (!ps.length) return '';
  return ps.map(function (p) { return num(p.qty) + ' ' + p.uom; }).join(' + ');
}

/* ---- o nhap so luong: 1 o cho moi don vi, tu cong ra don vi goc ---- */
function kkCountSheet(title, label, r, initEnc) {
  var units = kkUnits(r);
  var base = r.dvt || 'Đơn vị';
  var init = {};
  kkPartsDec(initEnc).forEach(function (p) { init[p.uom] = p.qty; });
  if (!Object.keys(init).length && kkNum(r.so_luong) > 0 && r.da_dem) init[base] = kkNum(r.so_luong);
  var multi = units.length > 1;

  return new Promise(function (res) {
    var ov = document.createElement('div'); ov.className = 'sh';
    var rows = units.map(function (u, k) {
      return '<div class="kku">' +
        '<div class="qr"><div class="stp">' +
        '<button data-m="' + k + '">&minus;</button>' +
        '<input type="number" inputmode="decimal" step="any" data-u="' + k + '" value="' +
        (init[u.uom] == null ? '' : init[u.uom]) + '" placeholder="0">' +
        '<button data-p="' + k + '">+</button></div>' +
        '<div class="uml">' + h(u.uom) + '</div></div>' +
        (Math.abs(u.f - 1) > 1e-9 ? '<div class="kkuf">1 ' + h(u.uom) + ' = ' + num(u.f) + ' ' + h(base) + '</div>' : '') +
        '</div>';
    }).join('');

    ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px);max-height:88vh;overflow:auto">' +
      '<div style="font-size:17.5px;font-weight:700;margin-bottom:4px;line-height:1.3">' + h(title) + '</div>' +
      '<div style="font-size:12.5px;color:#8a8f9c;margin-bottom:12px">' + h(label || '') + '</div>' +
      (multi ? '<div class="kkuh">Nguyên đai nguyên kiện đếm theo quy cách, hàng đã mở dở thì cân rồi nhập ở dòng ' + h(base) + '. Hệ thống tự cộng lại.</div>' : '') +
      rows +
      (multi ? '<div class="kkut">Tổng: <b id="kkuts">0</b> ' + h(base) + '</div>' : '') +
      '<button class="btn" data-y style="margin-top:14px">Xác nhận</button>' +
      '<button class="btn gh" data-n style="margin-top:9px">Huỷ</button></div>';
    document.body.appendChild(ov);

    var ins = [].slice.call(ov.querySelectorAll('[data-u]'));
    function parts() {
      return units.map(function (u, k) { return { uom: u.uom, qty: kkNum(ins[k].value), f: u.f }; });
    }
    function sync() {
      var t = ov.querySelector('#kkuts');
      if (t) t.textContent = num(kkPartsSum(parts()));
    }
    ov.addEventListener('input', sync);
    ov.onclick = function (e) {
      var t = e.target;
      var m = t.closest && t.closest('[data-m]'); if (m) { var a = ins[+m.dataset.m]; a.value = Math.max(0, r3((parseFloat(a.value) || 0) - 1)); return sync(); }
      var p = t.closest && t.closest('[data-p]'); if (p) { var b = ins[+p.dataset.p]; b.value = r3((parseFloat(b.value) || 0) + 1); return sync(); }
      if (t === ov || (t.closest && t.closest('[data-n]'))) { ov.remove(); return res(null); }
      if (t.closest && t.closest('[data-y]')) {
        var ps = parts();
        var any = ins.some(function (x) { return String(x.value).trim() !== ''; });
        ov.remove();
        return res(any ? { qty: kkPartsSum(ps), enc: kkPartsEnc(ps) } : null);
      }
    };
    sync();
    setTimeout(function () { try { ins[0].focus(); ins[0].select(); } catch (e) { } }, 150);
  });
}

function kkPackHtml(r, i, live) {
  var us = kkUnits(r);
  if (us.length < 2) return '';
  var txt = kkPartsText(r.cach_dem);
  if (!txt && !live) return '';
  return '<div class="tw"><div class="lb kkpk"' + (live ? ' data-pack="' + i + '"' : '') + '>' +
    (txt ? '&#9878; Đếm theo quy cách: <b>' + h(txt) + '</b> = ' + num(kkNum(r.so_luong)) + ' ' + h(r.dvt)
      : '&#9878; Đếm theo quy cách (' + h(us.filter(function (u) { return Math.abs(u.f - 1) > 1e-9; }).map(function (u) { return u.uom; }).join(', ')) + ')') +
    '</div></div>';
}

/* mo bang dem theo quy cach cho 1 dong da co tren phieu */
async function kkPackAsk(i) {
  if (!kkLive()) return;
  var r = kk.rows[i];
  var v = await kkCountSheet(r.item_name,
    r.item_code + (kkNum(r.ton_he_thong) ? ' · máy đang có ' + num(r.ton_he_thong) + ' ' + r.dvt : ' · máy chưa có tồn'),
    r, r.cach_dem);
  if (v === null) return;
  r.so_luong = v.qty; r.cach_dem = v.enc; r.da_dem = 1;
  var inp = document.querySelector('[data-q="' + i + '"]');
  if (inp) inp.value = r.so_luong;
  kkRowSync(i); kkTouch();
}


/* ---------- 14a. Danh sach phieu kiem ke ---------- */
async function scrKkList() {
  frame('Kiểm kê', '<div class="emp"><div class="e1">⏳</div></div>');
  await loadMasters();
  var docs = [];
  try {
    docs = await getList('Phieu Kiem Ke', {
      fields: ['name', 'ngay_kiem', 'kho', 'pham_vi', 'trang_thai', 'so_mon', 'nguoi_kiem', 'owner', 'modified'],
      filters: {}, limit_page_length: 80, order_by: 'modified desc'
    });
  } catch (e) { toast(errMsg(e)); }

  var dang = docs.filter(function (d) { return d.trang_thai === 'Đang kiểm'; });
  var xong = docs.filter(function (d) { return d.trang_thai !== 'Đang kiểm' && d.trang_thai !== 'Đã huỷ'; });
  var huy = docs.filter(function (d) { return d.trang_thai === 'Đã huỷ'; });

  function row(d) {
    var s = KKST[d.trang_thai] || KKST['Đang kiểm'];
    return '<div class="li" data-p="' + h(d.name) + '"><div class="lt">' +
      '<div class="l1">' + h(shortWh(d.kho)) + ' · ' + h(d.pham_vi || '') + '</div>' +
      '<div class="l2">' + h(d.name) + ' · ' + h(dmy(d.ngay_kiem)) + ' · ' + (d.so_mon || 0) + ' món' +
      (d.nguoi_kiem ? ' · ' + h(d.nguoi_kiem) : '') + '</div></div>' +
      '<span class="st ' + s.c + '">' + h(s.t) + '</span></div>';
  }

  var body = '<div class="rcvh">Mỗi phiếu kiểm kê là <b>một kho, một nhóm hàng</b>. Quét mã vạch rồi nhập số đếm được, phiếu tự lưu lại nên có thể kiểm nhiều buổi. Đếm xong mới bấm <b>Chốt phiếu</b>.</div>';
  if (dang.length) body += '<div class="sec">Đang kiểm dở</div><div class="lst">' + dang.map(row).join('') + '</div>';
  if (xong.length) body += '<div class="sec">Đã chốt</div><div class="lst">' + xong.map(row).join('') + '</div>';
  if (huy.length) body += '<div class="sec">Đã huỷ</div><div class="lst">' + huy.map(row).join('') + '</div>';
  if (!docs.length) body += '<div class="emp"><div class="e1">📋</div><div class="e2">Chưa có phiếu kiểm kê nào.<br>Bấm dấu + để bắt đầu kiểm kho.</div></div>';

  var b = frame('Kiểm kê', body, { fab: true, onFab: function () { go(scrKkNew); } });
  b.onclick = function (e) {
    var r = e.target.closest('[data-p]'); if (!r) return;
    go(function () { scrKkDoc(r.dataset.p); });
  };
}

/* ---------- 14b. Tao phieu kiem ke moi ---------- */
async function scrKkNew() {
  await loadMasters();
  if (!kk.newf) {
    kk.newf = {
      ngay: today(),
      kho: (S.wh.filter(function (w) { return shortWh(w).indexOf('Kho tổng') === 0; })[0] || S.wh[0] || ''),
      pv: 'Nguyên vật liệu',
      vt: ''
    };
  }
  var f = kk.newf;
  if (!kk.vtAll) {
    try { kk.vtAll = await getList('Vi Tri Kho', { fields: ['name', 'kho', 'loai', 'thu_tu'], filters: { active: 1 }, limit_page_length: 0, order_by: 'thu_tu asc, name asc' }); }
    catch (e) { kk.vtAll = []; }
  }
  function vtOpts() {
    var l = (kk.vtAll || []).filter(function (v) { return v.kho === f.kho; });
    return [{ value: '', label: 'Cả kho (không chia tủ)' }].concat(l.map(function (v) {
      return { value: v.name, label: v.name + (v.loai ? ' · ' + v.loai : '') };
    }));
  }
  function draw() {
    var vtl = (kk.vtAll || []).filter(function (v) { return v.kho === f.kho; });
    if (f.vt && vtl.map(function (v) { return v.name; }).indexOf(f.vt) < 0) f.vt = '';
    var sc = kkScope(f.pv);
    var body = '<div class="rcvh">Chọn đúng <b>kho</b> và <b>nhóm hàng</b> sẽ kiểm. Bếp thứ 6 chỉ kịp nguyên vật liệu thì cứ chọn Nguyên vật liệu, bán thành phẩm để phiếu riêng kiểm sau cũng được.</div>' +
      '<div class="card">' +
      '<div class="fld" data-d><div class="fi">📅</div><div class="ft"><div class="fl">Ngày kiểm</div><div class="fv">' + h(dmy(f.ngay)) + '</div></div><div class="fc">&#8250;</div></div>' +
      '<div class="fld" data-w><div class="fi">🏬</div><div class="ft"><div class="fl">Kho kiểm</div><div class="fv' + (f.kho ? '' : ' ph') + '">' + h(shortWh(f.kho) || 'Chọn kho') + '</div></div><div class="fc">&#8250;</div></div>' +
      '<div class="fld" data-s><div class="fi">' + sc.icon + '</div><div class="ft"><div class="fl">Nhóm hàng kiểm</div><div class="fv">' + h(f.pv) + '</div></div><div class="fc">&#8250;</div></div>' +
      (vtl.length ? '<div class="fld" data-v><div class="fi">📍</div><div class="ft"><div class="fl">Vị trí kiểm</div><div class="fv' + (f.vt ? '' : ' ph') + '">' + h(f.vt || 'Cả kho (không chia tủ)') + '</div></div><div class="fc">&#8250;</div></div>' : '') +
      '</div>' +
      '<div class="kwn">' + h(sc.sub) + '</div>' +
      (kkCanEditWh(f.kho) ? '' : '<div class="kkq" style="margin-top:10px">🔒 ' + kkLockNote(f.kho) + '</div>');
    var b = frame('Phiếu kiểm kê mới', body, {
      footer: kkCanEditWh(f.kho)
        ? '<button class="btn" id="kknew">Bắt đầu kiểm</button>'
        : '<div class="kkq">Chọn kho khác để bắt đầu kiểm.</div>'
    });
    b.onclick = function (e) {
      if (e.target.closest('[data-w]')) return sheet('Chọn kho kiểm', whOpts(), f.kho, function (o) { f.kho = o.value; f.vt = ''; draw(); }, true);
      if (e.target.closest('[data-v]')) return sheet('Vị trí kiểm', vtOpts(), f.vt, function (o) { f.vt = o.value; draw(); }, true);
      if (e.target.closest('[data-s]')) return sheet('Nhóm hàng kiểm', KKSCOPE.map(function (x) { return { value: x.value, label: x.value, icon: x.icon }; }), f.pv, function (o) { f.pv = o.value; draw(); });
      if (e.target.closest('[data-d]')) {
        return pickDate(f.ngay, function (v) { f.ngay = v; draw(); });
      }
    };
    var bn = document.getElementById('kknew'); if (bn) bn.onclick = kkCreate;
  }
  draw();
}

async function kkCreate() {
  var f = kk.newf;
  if (!f.kho) return toast('Chọn kho trước đã');
  if (!kkCanEditWh(f.kho)) return toast('Kho ' + shortWh(f.kho) + ' chỉ anh Kiên kiểm số');
  busy(1);
  try {
    var dup = await getList('Phieu Kiem Ke', {
      fields: ['name', 'nguoi_kiem', 'so_mon'],
      filters: { kho: f.kho, pham_vi: f.pv, vi_tri: f.vt || '', trang_thai: 'Đang kiểm' },
      limit_page_length: 1
    });
    busy(0);
    if (dup && dup.length) {
      var ok = await confirmSheet('Kho này đang có phiếu kiểm dở',
        'Phiếu ' + dup[0].name + ' (' + (dup[0].nguoi_kiem || 'chưa rõ người kiểm') + ', ' + (dup[0].so_mon || 0) + ' món) vẫn đang kiểm cùng kho, cùng nhóm hàng.\n\nNên kiểm tiếp phiếu đó thay vì tạo phiếu mới, tránh đếm trùng.',
        'Mở phiếu đang kiểm');
      if (ok) return go(function () { scrKkDoc(dup[0].name); }, true);
    }
    busy(1);
    var d = await api('frappe.client.insert', {
      doc: {
        doctype: 'Phieu Kiem Ke',
        ngay_kiem: f.ngay, kho: f.kho, pham_vi: f.pv, vi_tri: f.vt || '',
        trang_thai: 'Đang kiểm',
        nguoi_kiem: S.me.full_name || S.user,
        so_mon: 0, items: []
      }
    });
    busy(0);
    if (!d || !d.name) return toast('Không tạo được phiếu, thử lại giúp');
    toast('Đã tạo phiếu ' + d.name);
    go(function () { scrKkDoc(d.name); }, true);
  } catch (e) { busy(0); toast(errMsg(e)); }
}

/* ---------- 14c. Man hinh dem ---------- */
async function kkLoadCat(pv, vt) {
  var key = pv + '|' + (vt || '');
  if (kk.cat && kk.catKey === key) return kk.cat;
  var gs = kkGroups(pv);
  var flt = { is_stock_item: 1, disabled: 0 };
  if (gs && gs.length) flt.item_group = ['in', gs];
  if (vt) flt.custom_vi_tri_luu = vt;
  var its = await getList('Item', {
    fields: ['name', 'item_name', 'item_group', 'stock_uom', 'has_batch_no', 'custom_vi_tri_luu'],
    filters: flt, limit_page_length: 0, order_by: 'item_name'
  });
  kk.cat = its; kk.catKey = key;
  return its;
}

async function scrKkDoc(name) {
  frame('Kiểm kê', '<div class="emp"><div class="e1">⏳</div></div>');
  await loadMasters();
  var doc = null;
  try { doc = await api('frappe.client.get', { doctype: 'Phieu Kiem Ke', name: name }); }
  catch (e) { toast(errMsg(e)); return back(); }
  kk.doc = doc; kk.q = ''; kk.tab = 'da'; kk.dirty = 0; kk.savedAt = '';
  kk.rows = (doc.items || []).map(function (r) {
    return {
      item_code: r.item_code, item_name: r.item_name || r.item_code, item_group: r.item_group || '',
      dvt: r.dvt || '', ton_he_thong: kkNum(r.ton_he_thong), so_luong: kkNum(r.so_luong),
      cach_dem: r.cach_dem || '',
      han_su_dung: r.han_su_dung || '', ghi_chu: r.ghi_chu || '', da_dem: r.da_dem ? 1 : 0,
      name: r.name, docstatus: 0
    };
  });
  try { await kkLoadCat(doc.pham_vi, doc.vi_tri); } catch (e) { kk.cat = kk.cat || []; }
  try { await kkLoadConv(); } catch (e) { kk.conv = kk.conv || {}; }
  try {
    kk.sys = {};
    var bins = await getList('Bin', { fields: ['item_code', 'actual_qty'], filters: { warehouse: doc.kho, actual_qty: ['!=', 0] }, limit_page_length: 0 });
    bins.forEach(function (b) { kk.sys[b.item_code] = b.actual_qty; });
  } catch (e) { kk.sys = {}; }
  kkDraw();
}

function kkCatMap() {
  var m = {};
  (kk.cat || []).forEach(function (i) { m[i.name] = i; });
  return m;
}
function kkIdx(code) {
  for (var i = 0; i < kk.rows.length; i++) if (kk.rows[i].item_code === code) return i;
  return -1;
}
function kkLive() { return (kk.doc || {}).trang_thai === 'Đang kiểm' && kkCanEditWh((kk.doc || {}).kho); }

/* them 1 mon vao phieu, tra ve chi so dong */
function kkAdd(code) {
  var i = kkIdx(code);
  if (i >= 0) return i;
  var m = kkCatMap(), it = m[code];
  kk.rows.push({
    item_code: code,
    item_name: (it && it.item_name) || code,
    item_group: (it && it.item_group) || '',
    dvt: (it && it.stock_uom) || '',
    ton_he_thong: kkNum(kk.sys[code]),
    so_luong: 0, cach_dem: '', han_su_dung: '', ghi_chu: '', da_dem: 0, name: ''
  });
  return kk.rows.length - 1;
}

function kkDraw(keepScroll) {
  var d = kk.doc, live = kkLive();
  var sc = kkScope(d.pham_vi);
  var cat = kk.cat || [];
  var done = kk.rows.filter(function (r) { return r.da_dem; });
  var inSheet = {}; kk.rows.forEach(function (r) { inSheet[r.item_code] = 1; });
  var missing = cat.filter(function (i) { return !inSheet[i.name]; });
  var q = (kk.q || '').toLowerCase().trim();
  var st = KKST[d.trang_thai] || KKST['Đang kiểm'];

  var head = '<div class="card">' +
    '<div class="stk" style="border-top:0">' +
    '<div><div class="s1">KHO</div><div class="s2">' + h(shortWh(d.kho)) + '</div></div>' +
    '<div><div class="s1">NHÓM HÀNG</div><div class="s2">' + h(d.pham_vi) + '</div></div>' +
    '<div><div class="s1">NGÀY</div><div class="s2">' + h(dmy(d.ngay_kiem)) + '</div></div>' +
    '</div>' +
    '<div class="kpg"><div class="kpt" id="kkpt">' + kkProgText() + '</div>' +
    '<div class="kpb"><i id="kkpb" style="width:' + kkProgPct() + '%"></i></div></div>' +
    '<div class="kv" style="border-top:1px solid #f0f2f6"><span>Trạng thái</span><b><span class="st ' + st.c + '">' + h(st.t) + '</span></b></div>' +
    (d.vi_tri ? '<div class="kv"><span>Vị trí</span><b>📍 ' + h(d.vi_tri) + '</b></div>' : '') +
    '<div class="kv"><span>Người kiểm</span><b>' + h(d.nguoi_kiem || '') + '</b></div>' +
    '<div class="kv"><span>Số phiếu</span><b>' + h(d.name) + '</b></div>' +
    '</div>';

  var bar = live ? '<button class="kkbig" id="kkscan">📷 &nbsp;Quét mã vạch liên tục</button>' : '';

  var tabs = '<div class="chips">' +
    '<div class="chip' + (kk.tab === 'da' ? ' on' : '') + '" data-t="da">Đã đếm (' + kk.rows.length + ')</div>' +
    '<div class="chip' + (kk.tab === 'chua' ? ' on' : '') + '" data-t="chua">Chưa đếm (' + missing.length + ')</div>' +
    (kk.rows.filter(kkHasLech).length ? '<div class="chip' + (kk.tab === 'lech' ? ' on' : '') + '" data-t="lech">Lệch tồn (' + kk.rows.filter(kkHasLech).length + ')</div>' : '') +
    '</div>';

  var srch = srchBox('kkq', kk.tab === 'chua' ? 'Tìm theo tên hoặc mã để thêm' : 'Tìm theo tên hoặc mã hàng', kk.q, live);

  var listHtml = '';
  if (kk.tab === 'chua') {
    var ms = missing.filter(function (i) { return !q || (i.item_name + ' ' + i.name).toLowerCase().indexOf(q) >= 0; });
    listHtml = ms.length
      ? '<div class="lst">' + ms.slice(0, 300).map(function (i) {
        return '<div class="li" data-add="' + h(i.name) + '"><div class="lt">' +
          '<div class="l1">' + h(i.item_name) + '</div>' +
          '<div class="l2">' + h(i.name) + ' · ' + h(i.item_group) + '</div></div>' +
          '<div class="ck" style="border-radius:50%;font-size:20px;color:#0B7C93;border-color:#7FE5F6">+</div></div>';
      }).join('') + '</div>' + (ms.length > 300 ? '<div class="kkq">Còn ' + (ms.length - 300) + ' món nữa, gõ tên vào ô tìm để lọc bớt.</div>' : '')
      : '<div class="emp"><div class="e1">✅</div><div class="e2">' + (missing.length ? 'Không tìm thấy món nào' : 'Đã đếm hết ' + cat.length + ' món trong nhóm này') + '</div></div>';
  } else {
    var rs = kk.rows.map(function (r, i) { return { r: r, i: i }; });
    if (kk.tab === 'lech') rs = rs.filter(function (x) { return kkHasLech(x.r); });
    if (q) rs = rs.filter(function (x) { return (x.r.item_name + ' ' + x.r.item_code).toLowerCase().indexOf(q) >= 0; });
    listHtml = rs.length ? rs.map(function (x) { return kkRowHtml(x.r, x.i, live); }).join('') : '';
    if (q && live) {
      var mq = missing.filter(function (i) { return (i.item_name + ' ' + i.name).toLowerCase().indexOf(q) >= 0; });
      if (mq.length) {
        listHtml += '<div class="kkq" style="padding-top:10px">' +
          (rs.length ? 'Món khớp nhưng <b>chưa có trong phiếu</b>, bấm + để thêm và đếm:'
                     : 'Chưa có món nào khớp trong phiếu. <b>' + mq.length + ' món chưa đếm</b> khớp với từ khoá, bấm + để thêm:') +
          '</div><div class="lst">' + mq.slice(0, 60).map(function (i) {
            return '<div class="li" data-add="' + h(i.name) + '"><div class="lt">' +
              '<div class="l1">' + h(i.item_name) + '</div>' +
              '<div class="l2">' + h(i.name) + ' · ' + h(i.item_group) + '</div></div>' +
              '<div class="ck" style="border-radius:50%;font-size:20px;color:#0B7C93;border-color:#7FE5F6">+</div></div>';
          }).join('') + '</div>' +
          (mq.length > 60 ? '<div class="kkq">Còn ' + (mq.length - 60) + ' món nữa khớp, gõ thêm chữ cho gọn.</div>' : '');
      }
    }
    if (!listHtml) listHtml = '<div class="emp"><div class="e1">🔍</div><div class="e2">' +
      (q ? 'Không tìm thấy món nào tên hoặc mã có <b>' + h(kk.q) + '</b>'
         : (kk.rows.length ? 'Không tìm thấy món nào' : 'Phiếu còn trống.<br>Gõ tên món vào ô tìm ở trên, hoặc bấm <b>Quét mã vạch liên tục</b>.')) + '</div></div>';
  }

  var foot = '';
  if (live) {
    foot = '<div class="kkq" id="kksv">' + (kk.savedAt ? 'Đã lưu lúc ' + kk.savedAt : (kk.rows.length ? 'Có thay đổi chưa lưu' : 'Phiếu mới, chưa có món nào')) + '</div>' +
      '<div class="row2"><button class="btn gh" id="kksave">Lưu lại</button>' +
      '<button class="btn gr" id="kkdone">Chốt phiếu</button></div>' +
      '<button class="kkcx" id="kkcancel">Huỷ phiếu kiểm kê này</button>';
  } else if (d.trang_thai === 'Đang kiểm') {
    foot = '<div class="kkq">🔒 ' + kkLockNote(d.kho) + '</div>';
  } else if (d.trang_thai === 'Chờ duyệt' || d.trang_thai === 'Đã chốt') {
    foot = (kkCanPost() ? '<button class="btn" id="kkpost">Ghi sổ vào phần mềm</button>' : '<div class="kkq">Phiếu đã chốt, chờ kho hoặc giám đốc ghi sổ.</div>') +
      '<button class="btn gh" id="kkreopen" style="margin-top:9px">Mở lại để sửa</button>';
  } else if (d.trang_thai === 'Đã huỷ') {
    foot = '<div class="kkq">Phiếu đã huỷ, số đếm trong phiếu không được ghi vào sổ.</div>' +
      '<button class="btn gh" id="kkreopen">Mở lại để kiểm tiếp</button>';
  } else if (d.trang_thai === 'Đã ghi sổ') {
    foot = '<div class="kkq">Đã ghi sổ' + (d.stock_reconciliation ? ' bằng phiếu ' + h(d.stock_reconciliation) : '') + '. Phiếu này chỉ còn để tra cứu.</div>';
  }

  var b = frame('Kiểm kê ' + shortWh(d.kho), head + bar + tabs + srch + '<div id="kkl">' + listHtml + '</div>',
    { footer: foot, action: live ? '&#128247;' : '' , onAction: live ? kkScanTick : null });

  var sv = document.getElementById('kkq');
  if (sv) {
    var tm = null;
    sv.oninput = function () {
      kk.q = sv.value; clearTimeout(tm);
      tm = setTimeout(function () { var v = kk.q, p = sv.selectionStart; kkDraw(); var i2 = document.getElementById('kkq'); if (i2) { i2.focus(); i2.value = v; try { i2.setSelectionRange(p, p); } catch (e) { } } }, 220);
    };
  }
  var sb = document.getElementById('kkqscan');
  if (sb) sb.onclick = kkScanOne;
  var bs = document.getElementById('kkscan');
  if (bs) bs.onclick = kkScanTick;
  var s1 = document.getElementById('kksave'); if (s1) s1.onclick = function () { kkSave(1); };
  var s2 = document.getElementById('kkdone'); if (s2) s2.onclick = kkFinish;
  var s3 = document.getElementById('kkpost'); if (s3) s3.onclick = function () { go(function () { scrKkPost(kk.doc.name); }); };
  var s4 = document.getElementById('kkreopen'); if (s4) s4.onclick = kkReopen;
  var s5 = document.getElementById('kkcancel'); if (s5) s5.onclick = kkCancel;

  b.onclick = function (e) {
    var t = e.target.closest('[data-t]');
    if (t) { kk.tab = t.dataset.t; return kkDraw(); }
    var ad = e.target.closest('[data-add]');
    if (ad) return kkAddAsk(ad.dataset.add);
    var dl = e.target.closest('[data-x]');
    if (dl) return kkDel(+dl.dataset.x);
    var mi = e.target.closest('[data-m]');
    if (mi) return kkStep(+mi.dataset.m, -1);
    var pl = e.target.closest('[data-a]');
    if (pl) return kkStep(+pl.dataset.a, 1);
    var tm = e.target.closest('[data-tem]');
    if (tm) return kkTem(+tm.dataset.tem);
    var nb = e.target.closest('[data-note]');
    if (nb) return kkNote(+nb.dataset.note);
    var pk = e.target.closest('[data-pack]');
    if (pk) return kkPackAsk(+pk.dataset.pack);
  };
  b.addEventListener('change', function (e) {
    var qi = e.target.closest('[data-q]');
    if (qi) { var i = +qi.dataset.q; kk.rows[i].so_luong = kkNum(qi.value); kk.rows[i].cach_dem = ''; kk.rows[i].da_dem = 1; kkTouch(); kkRowSync(i); return; }
    var hi = e.target.closest('[data-h]');
    if (hi) { kk.rows[+hi.dataset.h].han_su_dung = hi.value || ''; kkTouch(); }
  });
  b.addEventListener('input', function (e) {
    var qi = e.target.closest('[data-q]');
    if (qi) { var i = +qi.dataset.q; kk.rows[i].so_luong = kkNum(qi.value); kk.rows[i].cach_dem = ''; kk.rows[i].da_dem = 1; kkTouch(); kkRowSync(i); }
  });
}

function kkHasLech(r) { return r.da_dem && Math.abs(kkNum(r.so_luong) - kkNum(r.ton_he_thong)) > 0.0001; }
function kkProgText() {
  var cat = (kk.cat || []).length, done = kk.rows.filter(function (r) { return r.da_dem; }).length;
  return 'ĐÃ ĐẾM ' + done + '/' + cat + ' MÓN TRONG NHÓM';
}
function kkProgPct() {
  var cat = (kk.cat || []).length, done = kk.rows.filter(function (r) { return r.da_dem; }).length;
  return cat ? Math.min(100, Math.round(done * 100 / cat)) : 0;
}
function kkProgSync() {
  var p = document.getElementById('kkpt'); if (p) p.textContent = kkProgText();
  var b = document.getElementById('kkpb'); if (b) b.style.width = kkProgPct() + '%';
}

function kkLechHtml(r) {
  if (!r.da_dem) return '';
  var s = kkNum(r.ton_he_thong), c = kkNum(r.so_luong), d = r3(c - s);
  if (!s && !c) return '';
  if (Math.abs(d) < 0.0001) return '<div class="kkl eq">Khớp với tồn trên máy (' + num(s) + ' ' + h(r.dvt) + ')</div>';
  return '<div class="kkl ' + (d > 0 ? 'up' : 'dn') + '">' + (d > 0 ? 'Thừa ' : 'Thiếu ') + num(Math.abs(d)) + ' ' + h(r.dvt) +
    ' so với máy (máy ' + num(s) + ', đếm ' + num(c) + ')</div>';
}

function kkRowHtml(r, i, live) {
  var it = kkCatMap()[r.item_code] || {};
  return '<div class="ic1' + (r.da_dem ? ' ok' : '') + '" id="kkr' + i + '">' +
    '<div class="ih"><div class="n">' + (i + 1) + '</div>' +
    '<div class="in">' + h(r.item_name) +
    '<div class="ig">' + h(r.item_code) + (r.item_group ? ' · ' + h(r.item_group) : '') +
    (kkNum(r.ton_he_thong) ? ' · máy ' + num(r.ton_he_thong) + ' ' + h(r.dvt) : ' · máy chưa có tồn') + '</div></div>' +
    (live ? '<div class="del" data-x="' + i + '">&times;</div>' : '<div class="rok">&#10003;</div>') + '</div>' +
    '<div class="qw"><div style="flex:1;min-width:0">' +
    '<div class="lb">Số lượng thực đếm' + (r.da_dem ? '' : ' <b class="lbw">(chưa nhập)</b>') + '</div>' +
    '<div class="qr"><div class="stp">' +
    (live ? '<button data-m="' + i + '">&minus;</button>' : '') +
    '<input type="number" inputmode="decimal" step="any" data-q="' + i + '" value="' + (r.da_dem ? r.so_luong : '') + '" placeholder="0"' + (live ? '' : ' readonly') + '>' +
    (live ? '<button data-a="' + i + '">+</button>' : '') +
    '</div><div class="uml">' + h(r.dvt) + '</div></div></div></div>' +
    '<div id="kkp' + i + '">' + kkPackHtml(r, i, live) + '</div>' +
    (it.has_batch_no ? '<div class="hw"><div class="hl">Hạn sử dụng lô đang tồn <b class="hbd">nếu có</b></div>' +
      '<input type="date" class="hin' + (r.han_su_dung ? ' ed' : '') + '" data-h="' + i + '" value="' + h(r.han_su_dung) + '"' + (live ? '' : ' disabled') + '>' +
      '<div class="hn">Món này quản lý theo lô. Ghi hạn trên bao bì để hệ thống lấy hàng theo FEFO cho đúng.</div>' +
      (live ? '<button class="btn gh" data-tem="' + i + '" style="height:44px;font-size:14px;margin-top:8px">&#127991; In tem dán lên hàng</button>' : '') +
      '</div>' : '') +
    '<div id="kkw' + i + '">' + kkLechHtml(r) + '</div>' +
    (live ? '<div class="tw"><div class="lb" data-note="' + i + '" style="color:#0B7C93;font-weight:600;cursor:pointer">' +
      (r.ghi_chu ? '✎ Ghi chú: ' + h(r.ghi_chu) : '✎ Thêm ghi chú (hàng hỏng, hàng gửi, đang mượn...)') + '</div></div>'
      : (r.ghi_chu ? '<div class="tw"><div class="lb">Ghi chú: ' + h(r.ghi_chu) + '</div></div>' : '')) +
    '</div>';
}

/* ---- in tem nhap kho ngay tai dong dang dem ---- */
function kkBatchId(docname, code) {
  return 'KK' + String(docname).replace(/[^0-9A-Za-z]/g, '').slice(-8) + '-' + String(code).replace(/[^0-9A-Za-z]/g, '');
}
async function kkTem(i) {
  if (!kkLive()) return;
  var r = kk.rows[i];
  var it = kkCatMap()[r.item_code] || {};
  if (!it.has_batch_no) return toast('Món này không quản lý theo lô nên chưa in tem lô được');
  if (!kk.doc || !kk.doc.name) return toast('Lưu phiếu một lần trước đã rồi in tem nhé');
  if (!r.han_su_dung) {
    var go1 = await confirmSheet('Chưa điền hạn sử dụng', r.item_name + '\n\nTem in ra sẽ không có HSD. Điền hạn vào ô ngay phía trên rồi in lại sẽ đầy đủ hơn.', 'Cứ in không HSD');
    if (!go1) return;
  }
  var nv = await promptSheet('In bao nhiêu tem cho ' + r.item_name + '?', 'Số tem, ví dụ 1');
  if (nv === null) return;
  var n = Math.max(1, parseInt(nv, 10) || 1);
  var w = window.open('', '_blank');
  busy(1);
  try {
    if (kk.dirty) { try { await kkSave(0); } catch (e0) { } }
    var bid = kkBatchId(kk.doc.name, r.item_code);
    var ex = await getList('Batch', { fields: ['name'], filters: { name: bid }, limit_page_length: 1 });
    if (ex && ex.length) {
      var fv = { custom_so_tem: n };
      if (r.han_su_dung) fv.expiry_date = r.han_su_dung;
      await api('frappe.client.set_value', { doctype: 'Batch', name: bid, fieldname: fv });
    } else {
      var bd = { doctype: 'Batch', batch_id: bid, item: r.item_code, custom_so_tem: n };
      if (r.han_su_dung) bd.expiry_date = r.han_su_dung;
      await api('frappe.client.insert', { doc: bd });
    }
    busy(0);
    var u = '/printview?doctype=Batch&name=' + encodeURIComponent(bid) +
      '&format=' + encodeURIComponent('Vagabond - Tem nhan hang') + '&no_letterhead=1&trigger_print=1';
    if (w) { w.location.href = u; } else { window.location.href = u; }
  } catch (e) {
    busy(0);
    if (w) { try { w.close(); } catch (e2) { } }
    toast(errMsg(e), 7000);
  }
}

function kkRowSync(i) {
  var el = document.getElementById('kkr' + i); if (!el) return;
  var r = kk.rows[i];
  if (r.da_dem) el.classList.add('ok'); else el.classList.remove('ok');
  var w = document.getElementById('kkw' + i); if (w) w.innerHTML = kkLechHtml(r);
  var p = document.getElementById('kkp' + i); if (p) p.innerHTML = kkPackHtml(r, i, kkLive());
  kkProgSync();
}

function kkStep(i, d) {
  if (!kkLive()) return;
  var r = kk.rows[i];
  r.so_luong = Math.max(0, r3(kkNum(r.so_luong) + d));
  r.cach_dem = '';
  r.da_dem = 1;
  var inp = document.querySelector('[data-q="' + i + '"]');
  if (inp) inp.value = r.so_luong;
  kkRowSync(i); kkTouch();
}

async function kkNote(i) {
  var v = await promptSheet('Ghi chú cho ' + kk.rows[i].item_name, 'Ví dụ: 2 hộp bị móp, 1 thùng đang gửi bên bếp Lab...');
  if (v === null) return;
  kk.rows[i].ghi_chu = v;
  kkTouch(); kkDraw();
}

async function kkDel(i) {
  var ok = await confirmSheet('Bỏ món này khỏi phiếu?', kk.rows[i].item_name + '\n' + kk.rows[i].item_code, 'Bỏ ra', true);
  if (!ok) return;
  kk.rows.splice(i, 1);
  kkTouch(); kkDraw();
}

async function kkAddAsk(code) {
  if (!kkLive()) return;
  var i = kkAdd(code), r = kk.rows[i];
  var v = await kkCountSheet(r.item_name, r.item_code + (kkNum(r.ton_he_thong) ? ' · máy đang có ' + num(r.ton_he_thong) + ' ' + r.dvt : ' · máy chưa có tồn'), r, r.cach_dem);
  if (v === null) { if (!r.da_dem) kk.rows.splice(i, 1); kkDraw(); return; }
  r.so_luong = v.qty; r.cach_dem = v.enc; r.da_dem = 1;
  kkTouch(); kkDraw();
}

/* quet 1 lan tu o tim kiem */
async function kkScanOne() {
  var code = await scanBarcode(null);
  if (!code) return;
  busy(1);
  var ic = null;
  try { ic = await itemByBarcode(String(code).trim().replace(/^\*+|\*+$/g, '')); } catch (e) { }
  busy(0);
  if (!ic) return toast('Chưa nhận ra mã ' + code + '. Tìm bằng tên món giúp em.');
  if (kk.tab === 'chua' && kkIdx(ic) < 0) return kkAddAsk(ic);
  kk.q = ic; kk.tab = 'da'; kkDraw();
}

/* quet lien tuc: moi lan quet cong them 1 don vi, tien cho hang dem tung cai */
async function kkScanTick() {
  if (!kkLive()) return;
  var cat = kkCatMap();
  await scanBarcode(async function (code) {
    var raw = String(code).trim().replace(/^\*+|\*+$/g, '');
    var ic = null;
    try { ic = await itemByBarcode(raw); } catch (e) { }
    if (!ic) { try { ic = await itemByBarcode(raw.toUpperCase()); } catch (e) { } }
    if (!ic) return '✗ Chưa nhận ra mã ' + raw;
    if (!cat[ic]) {
      var extra = null;
      try { extra = (await getList('Item', { fields: ['name', 'item_name', 'item_group', 'stock_uom', 'has_batch_no'], filters: { name: ic }, limit_page_length: 1 }))[0]; } catch (e) { }
      if (!extra) return '✗ ' + ic + ' không có trong hệ thống';
      return '✗ ' + (extra.item_name || ic) + ' thuộc nhóm ' + (extra.item_group || '?') + ', không nằm trong phiếu này';
    }
    var i = kkAdd(ic), r = kk.rows[i];
    var pk = kkPack(r);
    if (pk) {
      var ps = kkPartsDec(r.cach_dem);
      if (!ps.length && kkNum(r.so_luong) > 0 && r.da_dem) ps.push({ uom: r.dvt, qty: kkNum(r.so_luong), f: 1 });
      var hit = null;
      ps.forEach(function (x) { if (x.uom === pk.uom) hit = x; });
      if (!hit) { hit = { uom: pk.uom, qty: 0, f: pk.f }; ps.push(hit); }
      hit.qty = r3(kkNum(hit.qty) + 1); hit.f = pk.f;
      r.cach_dem = kkPartsEnc(ps); r.so_luong = kkPartsSum(ps);
    } else {
      r.so_luong = r3(kkNum(r.so_luong) + 1); r.cach_dem = '';
    }
    r.da_dem = 1;
    kkTouch();
    return '✓ ' + r.item_name + '\n' +
      (pk ? kkPartsText(r.cach_dem) + ' = ' + num(r.so_luong) + ' ' + r.dvt : num(r.so_luong) + ' ' + r.dvt);
  });
  kkDraw();
}

/* ---------- 14d. Luu phieu ---------- */
function kkTouch() {
  kk.dirty = 1;
  var el = document.getElementById('kksv');
  if (el) el.textContent = 'Có thay đổi chưa lưu...';
  clearTimeout(kk.tmr);
  kk.tmr = setTimeout(function () { kkSave(0); }, 3000);
}

async function kkSave(loud) {
  if (!kk.doc || !kkLive()) return true;
  if (kk.saving) { clearTimeout(kk.tmr); kk.tmr = setTimeout(function () { kkSave(loud); }, 1500); return false; }
  if (!kk.dirty && !loud) return true;
  kk.saving = 1;
  clearTimeout(kk.tmr);
  if (loud) busy(1);
  var el = document.getElementById('kksv');
  if (el) el.textContent = 'Đang lưu...';
  try {
    var d = kk.doc;
    d.items = kk.rows.map(function (r, i) {
      var o = {
        idx: i + 1, item_code: r.item_code, item_name: r.item_name, item_group: r.item_group,
        dvt: r.dvt, ton_he_thong: kkNum(r.ton_he_thong), so_luong: kkNum(r.so_luong),
        cach_dem: r.cach_dem || '',
        lech: r3(kkNum(r.so_luong) - kkNum(r.ton_he_thong)),
        han_su_dung: r.han_su_dung || null, ghi_chu: r.ghi_chu || '', da_dem: r.da_dem ? 1 : 0
      };
      if (r.name) { o.name = r.name; o.parent = d.name; o.parenttype = 'Phieu Kiem Ke'; o.parentfield = 'items'; o.doctype = 'Chi Tiet Kiem Ke'; }
      return o;
    });
    d.so_mon = kk.rows.filter(function (r) { return r.da_dem; }).length;
    if (!d.nguoi_kiem) d.nguoi_kiem = S.me.full_name || S.user;
    var nd = await api('frappe.client.save', { doc: d });
    if (nd && nd.name) {
      kk.doc = nd; kk.dirty = 0;
      var byc = {}; (nd.items || []).forEach(function (x) { byc[x.item_code] = x.name; });
      kk.rows.forEach(function (r) { if (byc[r.item_code]) r.name = byc[r.item_code]; });
    }
    var t = new Date();
    kk.savedAt = pad2(t.getHours()) + ':' + pad2(t.getMinutes());
    if (loud) busy(0);
    var e2 = document.getElementById('kksv');
    if (e2) e2.textContent = 'Đã lưu lúc ' + kk.savedAt + ' · ' + d.so_mon + ' món';
    if (loud) toast('Đã lưu phiếu ' + d.name);
    kk.saving = 0;
    return true;
  } catch (e) {
    kk.saving = 0;
    if (loud) busy(0);
    var e3 = document.getElementById('kksv');
    if (e3) e3.textContent = 'Chưa lưu được, sẽ thử lại...';
    if (loud) toast(errMsg(e));
    if (String(errMsg(e)).indexOf('sửa') >= 0 || String(errMsg(e)).indexOf('Timestamp') >= 0) {
      try { kk.doc = await api('frappe.client.get', { doctype: 'Phieu Kiem Ke', name: kk.doc.name }); } catch (x) { }
    }
    clearTimeout(kk.tmr);
    kk.tmr = setTimeout(function () { kkSave(0); }, 6000);
    return false;
  }
}

async function kkFinish() {
  var chua = (kk.cat || []).length - kk.rows.filter(function (r) { return r.da_dem; }).length;
  var msg = 'Phiếu ' + kk.doc.name + ' · ' + shortWh(kk.doc.kho) + ' · ' + kk.doc.pham_vi +
    '\nĐã đếm ' + kk.rows.filter(function (r) { return r.da_dem; }).length + ' món.';
  if (chua > 0) msg += '\n\nCòn ' + chua + ' món trong nhóm chưa đếm. Những món này sẽ KHÔNG được ghi vào sổ, tồn kho của chúng giữ nguyên như cũ.';
  msg += '\n\nChốt xong thì không sửa số được nữa (vẫn mở lại được nếu cần).';
  var ok = await confirmSheet('Chốt phiếu kiểm kê?', msg, 'Chốt phiếu');
  if (!ok) return;
  if (!await kkSave(1)) return toast('Chưa lưu được phiếu, kiểm tra mạng rồi chốt lại');
  busy(1);
  try {
    kk.doc.trang_thai = 'Chờ duyệt';
    kk.doc = await api('frappe.client.save', { doc: kk.doc });
    busy(0);
    toast('Đã chốt phiếu ' + kk.doc.name);
    kkDraw();
  } catch (e) { busy(0); kk.doc.trang_thai = 'Đang kiểm'; toast(errMsg(e)); }
}

async function kkCancel() {
  var ok = await confirmSheet('Huỷ phiếu kiểm kê này?',
    'Phiếu ' + kk.doc.name + ' sẽ chuyển sang trạng thái Đã huỷ và không ghi vào sổ kho.\nSố đã đếm vẫn giữ lại trong phiếu để tra cứu, mở lại được nếu cần.',
    'Huỷ phiếu', true);
  if (!ok) return;
  busy(1);
  try {
    await kkSave(0);
    kk.doc.trang_thai = 'Đã huỷ';
    kk.doc = await api('frappe.client.save', { doc: kk.doc });
    busy(0); toast('Đã huỷ phiếu ' + kk.doc.name); kkDraw();
  } catch (e) { busy(0); kk.doc.trang_thai = 'Đang kiểm'; toast(errMsg(e)); }
}

async function kkReopen() {
  var ok = await confirmSheet('Mở lại phiếu để sửa?', 'Phiếu sẽ quay về trạng thái Đang kiểm để đếm hoặc sửa tiếp.', 'Mở lại');
  if (!ok) return;
  busy(1);
  try {
    kk.doc.trang_thai = 'Đang kiểm';
    kk.doc = await api('frappe.client.save', { doc: kk.doc });
    busy(0); toast('Đã mở lại phiếu'); kkDraw();
  } catch (e) { busy(0); toast(errMsg(e)); }
}

/* ---------- 14e. Ghi so: tao Stock Reconciliation ---------- */
var kkp = { doc: null, rows: [], rates: {}, opening: 1 };

async function scrKkPost(name) {
  frame('Ghi sổ kiểm kê', '<div class="emp"><div class="e1">⏳</div></div>');
  var d = null;
  try { d = await api('frappe.client.get', { doctype: 'Phieu Kiem Ke', name: name }); }
  catch (e) { toast(errMsg(e)); return back(); }
  if (d.trang_thai === 'Đã ghi sổ') { toast('Phiếu này đã ghi sổ rồi'); return back(); }
  kkp.doc = d;
  kkp.rows = (d.items || []).filter(function (r) { return r.da_dem; });
  var codes = kkp.rows.map(function (r) { return r.item_code; });
  var info = {};
  try {
    var its = await inChunks(codes, 80, function (lot) {
      return getList('Item', { fields: ['name', 'item_name', 'stock_uom', 'has_batch_no', 'valuation_rate', 'last_purchase_rate'], filters: { name: ['in', lot] }, limit_page_length: 0 });
    });
    its.forEach(function (i) { info[i.name] = i; });
  } catch (e) { toast(errMsg(e)); }
  kkp.info = info;
  kkp.acc = ''; kkp.cc = ''; kkp.accs = [];
  try {
    var cp = await api('frappe.client.get_value', { doctype: 'Company', filters: { name: COMPANY }, fieldname: ['stock_adjustment_account', 'cost_center'] });
    kkp.accAdj = (cp && cp.stock_adjustment_account) || '';
    kkp.cc = (cp && cp.cost_center) || '';
  } catch (e) { }
  kkp.accOpen = '';
  try {
    var tmpa = await getList('Account', { fields: ['name'], filters: { company: COMPANY, account_type: 'Temporary', is_group: 0 }, limit_page_length: 1 });
    if (tmpa && tmpa.length) kkp.accOpen = tmpa[0].name;
  } catch (e) { }
  kkp.acc = kkp.opening ? (kkp.accOpen || kkp.accAdj) : (kkp.accAdj || kkp.accOpen);
  try {
    kkp.accs = (await getList('Account', { fields: ['name'], filters: { company: COMPANY, is_group: 0 }, limit_page_length: 0, order_by: 'name' })).map(function (a) { return { value: a.name, label: a.name }; });
  } catch (e) { kkp.accs = []; }
  kkp.rates = {};
  kkp.rows.forEach(function (r) {
    var i = info[r.item_code] || {};
    kkp.rates[r.item_code] = kkNum(i.valuation_rate) || kkNum(i.last_purchase_rate) || 0;
  });
  kkpDraw();
}

function kkpDraw() {
  var d = kkp.doc;
  var noRate = kkp.rows.filter(function (r) { return kkNum(r.so_luong) > 0 && !kkp.rates[r.item_code]; });
  var batchN = kkp.rows.filter(function (r) { return (kkp.info[r.item_code] || {}).has_batch_no && kkNum(r.so_luong) > 0; }).length;

  var body = '<div class="rcvh">Bước này ghi số đã đếm vào sổ kho thật. Máy sẽ tạo <b>một phiếu điều chỉnh tồn kho</b> (Stock Reconciliation) và nộp luôn. Sau khi nộp thì tồn kho đổi theo số đã đếm.</div>' +
    '<div class="card">' +
    '<div class="kv"><span>Phiếu kiểm kê</span><b>' + h(d.name) + '</b></div>' +
    '<div class="kv"><span>Kho</span><b>' + h(shortWh(d.kho)) + '</b></div>' +
    '<div class="kv"><span>Nhóm hàng</span><b>' + h(d.pham_vi) + '</b></div>' +
    '<div class="kv"><span>Số món ghi sổ</span><b>' + kkp.rows.length + '</b></div>' +
    '<div class="kv"><span>Món quản lý theo lô</span><b>' + batchN + '</b></div>' +
    '</div>' +
    '<div class="card"><div class="fld" data-op><div class="fi">📘</div><div class="ft">' +
    '<div class="fl">Kiểu ghi sổ</div><div class="fv">' + (kkp.opening ? 'Tồn đầu kỳ (lần đầu đưa số lên máy)' : 'Điều chỉnh tồn (kiểm kê định kỳ)') + '</div></div>' +
    '<div class="fc">&#8250;</div></div>' +
    '<div class="fld" data-acc><div class="fi">🧾</div><div class="ft">' +
    '<div class="fl">Tài khoản đối ứng chênh lệch</div><div class="fv' + (kkp.acc ? '' : ' ph') + '">' + h(kkp.acc || 'Chọn tài khoản') + '</div></div>' +
    '<div class="fc">&#8250;</div></div>' +
    '<div class="fld" data-cc><div class="fi">🏷️</div><div class="ft">' +
    '<div class="fl">Trung tâm chi phí</div><div class="fv' + (kkp.cc ? '' : ' ph') + '">' + h(kkp.cc || 'Chọn') + '</div></div>' +
    '<div class="fc">&#8250;</div></div></div>' +
    (kkp.opening ? '<div class="kwn">Ghi <b>tồn đầu kỳ</b> thì phần chênh lệch đối ứng vào tài khoản ở trên. Kế toán đã chốt dùng <b>Temporary Opening</b> cho lần đầu đưa số lên máy. Bút toán sẽ vào sổ cái thật.</div>' : '<div class="kwn">Kiểm kê định kỳ thì chênh lệch đối ứng vào tài khoản chi phí ở trên (mặc định 811 - Chi phí khác). Hỏi kế toán nếu không chắc.</div>');

  if (batchN) {
    body += '<div class="kwn">Có ' + batchN + ' món quản lý theo lô. Máy sẽ tự tạo một lô tồn đầu kỳ cho mỗi món, đặt tên theo phiếu kiểm kê này, lấy hạn sử dụng đã nhập nếu có.</div>';
  }

  if (noRate.length) {
    body += '<div class="sec">Cần điền giá vốn (' + noRate.length + ' món)</div>' +
      '<div class="kwn">Máy chưa biết giá vốn của những món này nên chưa ghi sổ được. Điền giá mua 1 đơn vị (chưa VAT) rồi bấm ghi sổ.</div>' +
      noRate.slice(0, 120).map(function (r) {
        return '<div class="ic1"><div class="ih"><div class="n">!</div><div class="in">' + h(r.item_name || r.item_code) +
          '<div class="ig">' + h(r.item_code) + ' · đếm ' + num(r.so_luong) + ' ' + h(r.dvt) + '</div></div></div>' +
          '<div class="qw"><div style="flex:1;min-width:0"><div class="lb">Giá vốn 1 ' + h(r.dvt) + ' (VND)</div>' +
          '<div class="qr"><div class="stp"><input type="number" inputmode="decimal" step="any" data-rate="' + h(r.item_code) + '" value="" placeholder="0"></div>' +
          '<div class="uml">VND</div></div></div></div></div>';
      }).join('');
  }

  var lech = kkp.rows.filter(function (r) { return Math.abs(kkNum(r.so_luong) - kkNum(r.ton_he_thong)) > 0.0001; });
  if (lech.length) {
    body += '<div class="sec">Lệch so với máy (' + lech.length + ' món)</div><div class="lst">' +
      lech.slice(0, 200).map(function (r) {
        var dv = r3(kkNum(r.so_luong) - kkNum(r.ton_he_thong));
        return '<div class="li"><div class="lt"><div class="l1">' + h(r.item_name || r.item_code) + '</div>' +
          '<div class="l2">máy ' + num(r.ton_he_thong) + ' → đếm ' + num(r.so_luong) + ' ' + h(r.dvt) +
          (kkPartsText(r.cach_dem) ? ' (' + h(kkPartsText(r.cach_dem)) + ')' : '') + '</div></div>' +
          '<span class="st ' + (dv > 0 ? 'g' : 'r') + '">' + (dv > 0 ? '+' : '') + num(dv) + '</span></div>';
      }).join('') + '</div>';
  }

  var b = frame('Ghi sổ kiểm kê', body, { footer: '<button class="btn" id="kkpgo">Tạo phiếu điều chỉnh và nộp</button>' });
  b.onclick = function (e) {
    if (e.target.closest('[data-acc]')) {
      return sheet('Tài khoản đối ứng', kkp.accs, kkp.acc, function (o) { kkp.acc = o.value; kkpDraw(); }, true);
    }
    if (e.target.closest('[data-cc]')) {
      if (!kkp.ccs) {
        return getList('Cost Center', { fields: ['name'], filters: { company: COMPANY, is_group: 0 }, limit_page_length: 0 }).then(function (cs) {
          kkp.ccs = cs.map(function (c) { return { value: c.name, label: c.name }; });
          sheet('Trung tâm chi phí', kkp.ccs, kkp.cc, function (o) { kkp.cc = o.value; kkpDraw(); }, true);
        });
      }
      return sheet('Trung tâm chi phí', kkp.ccs, kkp.cc, function (o) { kkp.cc = o.value; kkpDraw(); }, true);
    }
    if (e.target.closest('[data-op]')) {
      sheet('Kiểu ghi sổ', [
        { value: 1, label: 'Tồn đầu kỳ (lần đầu đưa số lên máy)' },
        { value: 0, label: 'Điều chỉnh tồn (kiểm kê định kỳ)' }
      ], kkp.opening, function (o) { kkp.opening = o.value; kkp.acc = o.value ? (kkp.accOpen || kkp.accAdj) : (kkp.accAdj || kkp.accOpen); kkpDraw(); });
    }
  };
  b.addEventListener('input', function (e) {
    var ri = e.target.closest('[data-rate]');
    if (ri) kkp.rates[ri.dataset.rate] = kkNum(ri.value);
  });
  document.getElementById('kkpgo').onclick = kkpSubmit;
}

async function kkpSubmit() {
  var d = kkp.doc;
  var rows = kkp.rows.filter(function (r) { return kkNum(r.so_luong) > 0 || kkNum(r.ton_he_thong) > 0; });
  if (!rows.length) return toast('Phiếu không có món nào để ghi sổ');
  var bad = rows.filter(function (r) { return kkNum(r.so_luong) > 0 && !kkp.rates[r.item_code]; });
  if (bad.length) return toast('Còn ' + bad.length + ' món chưa có giá vốn, điền giúp em rồi ghi sổ lại');
  if (!kkp.acc) return toast('Chọn tài khoản đối ứng chênh lệch trước đã');

  var ok = await confirmSheet('Ghi sổ ' + rows.length + ' món?',
    'Kho ' + shortWh(d.kho) + ' · ' + d.pham_vi + '\n\nMáy sẽ tạo phiếu điều chỉnh tồn kho và NỘP luôn. Sau đó tồn kho đổi theo số đã đếm và không sửa lại bằng app được, phải huỷ phiếu trên máy tính.',
    'Ghi sổ ngay');
  if (!ok) return;

  busy(1);
  try {
    /* 1. tao lo ton dau ky cho cac mon quan ly theo lo */
    var batches = {};
    var need = rows.filter(function (r) { return (kkp.info[r.item_code] || {}).has_batch_no && kkNum(r.so_luong) > 0; });
    for (var i = 0; i < need.length; i++) {
      var r = need[i];
      var bid = kkBatchId(d.name, r.item_code);
      var bd = { doctype: 'Batch', batch_id: bid, item: r.item_code };
      if (r.han_su_dung) bd.expiry_date = r.han_su_dung;
      var exist = await getList('Batch', { fields: ['name'], filters: { name: bid }, limit_page_length: 1 });
      if (exist && exist.length) {
        if (r.han_su_dung) { try { await api('frappe.client.set_value', { doctype: 'Batch', name: bid, fieldname: { expiry_date: r.han_su_dung } }); } catch (eb) { } }
        batches[r.item_code] = bid; continue;
      }
      var nb = await api('frappe.client.insert', { doc: bd });
      batches[r.item_code] = (nb && nb.name) || bid;
    }

    /* 2. dung phieu dieu chinh ton kho */
    var now = new Date();
    var sr = {
      doctype: 'Stock Reconciliation',
      company: COMPANY,
      purpose: kkp.opening ? 'Opening Stock' : 'Stock Reconciliation',
      posting_date: d.ngay_kiem || ymdOf(now),
      posting_time: hmOf(now),
      set_posting_time: 1,
      set_warehouse: d.kho,
      expense_account: kkp.acc,
      cost_center: kkp.cc || undefined,
      items: rows.map(function (r) {
        var it = { item_code: r.item_code, warehouse: d.kho, qty: kkNum(r.so_luong), valuation_rate: kkp.rates[r.item_code] || 0 };
        if (kkp.cc) it.cost_center = kkp.cc;
        if (batches[r.item_code]) { it.use_serial_batch_fields = 1; it.batch_no = batches[r.item_code]; }
        return it;
      })
    };
    var doc = await api('frappe.client.insert', { doc: sr });
    if (!doc || !doc.name) throw new Error('Không tạo được phiếu điều chỉnh');
    await api('frappe.client.submit', { doc: doc });

    /* 3. dong phieu kiem ke */
    d.trang_thai = 'Đã ghi sổ';
    d.stock_reconciliation = doc.name;
    await api('frappe.client.save', { doc: d });

    busy(0);
    toast('Đã ghi sổ bằng phiếu ' + doc.name, 4200);
    kk.doc = null; kk.cat = null; kk.catKey = '';
    reset(scrHome); go(scrKkList);
  } catch (e) { busy(0); toast(errMsg(e), 5000); }
}

/* ---------- 15. Yeu cau mua hang test (R&D) ---------- */
var RNDST = {
  'Mới tạo': { c: 'w', t: 'Mới tạo' },
  'Đang xử lý': { c: 'b', t: 'Đang xử lý' },
  'Hoàn thành': { c: 'g', t: 'Hoàn thành' },
  'Huỷ': { c: 'n', t: 'Đã huỷ' }
};
var RNDLS = {
  'Chưa mua': { c: 'w', t: 'Chưa mua' },
  'Đã mua': { c: 'g', t: 'Đã mua' },
  'Không mua được': { c: 'r', t: 'Không mua được' }
};
var rnd = { newf: null };
function isRnd() { return hasRole('Mua hàng R&D') || hasRole('System Manager'); }
function isSales() { return hasRole('Sales User') || hasRole('Sales Manager') || hasRole('Bộ phận đặt hàng') || hasRole('System Manager'); }
function pickDate(cur, cb) {
  var base = /^\d{4}-\d{2}-\d{2}$/.test(cur || '') ? cur : today();
  var sel = base, pp = base.split('-'), vy = +pp[0], vm = +pp[1] - 1;
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function iso(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>Chọn ngày</b><div class="x">&times;</div></div>' +
    '<div class="shl" style="padding:6px 12px 16px"></div>';
  var bd = box.querySelector('.shl');
  function close() { try { ov.remove(); } catch (x) { } }
  function nav(t) { return '<div data-p="' + t + '" style="width:46px;height:46px;border-radius:14px;background:#f2f4f8;display:flex;align-items:center;justify-content:center;font-size:22px;color:#3a4152">' + (t < 0 ? '&#8249;' : '&#8250;') + '</div>'; }
  function quick(n, lb) { return '<div data-q="' + n + '" style="flex:1;height:46px;border-radius:14px;background:#f2f4f8;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:600;color:#3a4152">' + lb + '</div>'; }
  function draw() {
    var st = (new Date(vy, vm, 1).getDay() + 6) % 7, dim = new Date(vy, vm + 1, 0).getDate(), td = today();
    var s = '<div style="display:flex;align-items:center;gap:8px;padding:4px 0 10px">' + nav(-1) +
      '<b style="flex:1;text-align:center;font-size:16.5px">Tháng ' + (vm + 1) + ' / ' + vy + '</b>' + nav(1) + '</div>' +
      '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:5px;font-size:12px;color:#8a90a0;text-align:center;padding-bottom:5px">' +
      'T2,T3,T4,T5,T6,T7,CN'.split(',').map(function (x) { return '<div>' + x + '</div>'; }).join('') +
      '</div><div style="display:grid;grid-template-columns:repeat(7,1fr);gap:5px">';
    for (var k = 0; k < st; k++) s += '<div></div>';
    for (var d = 1; d <= dim; d++) {
      var v = vy + '-' + pad(vm + 1) + '-' + pad(d);
      var stl = v === sel ? 'background:#111827;color:#fff;font-weight:700' : (v === td ? 'background:#e6efff;color:#1b4dd8;font-weight:700' : 'background:#f7f8fb;color:#20242e');
      s += '<div data-dd="' + v + '" style="height:46px;display:flex;align-items:center;justify-content:center;border-radius:14px;font-size:15.5px;' + stl + '">' + d + '</div>';
    }
    s += '</div><div style="display:flex;gap:8px;padding-top:14px">' + quick(0, 'Hôm nay') + quick(1, 'Ngày mai') + quick(7, 'Sau 7 ngày') + '</div>';
    bd.innerHTML = s;
  }
  box.onclick = function (e) {
    if (e.target.closest('.x')) return close();
    var p = e.target.closest('[data-p]');
    if (p) { vm += +p.dataset.p; if (vm < 0) { vm = 11; vy--; } if (vm > 11) { vm = 0; vy++; } return draw(); }
    var q = e.target.closest('[data-q]');
    if (q) { var dt = new Date(); dt.setDate(dt.getDate() + (+q.dataset.q)); close(); return cb(iso(dt)); }
    var dd = e.target.closest('[data-dd]');
    if (dd) { close(); return cb(dd.dataset.dd); }
  };
  ov.onclick = function (e) { if (e.target === ov) close(); };
  ov.appendChild(box); document.body.appendChild(ov); draw();
}
/* ---- anh dinh kem, tien do, quy OCB cho phieu mua hang test ---- */
var RND_OCB_TK = '1411 - Tạm ứng - Nguyễn Hoàng Việt (OCB) - TV';
var RND_NCC_LE = 'NCC lẻ - mua hàng test (R&D)';
function rndLaThuMua() { return hasRole('Purchase User') || hasRole('Accounts User') || hasRole('System Manager'); }
function rndAnhDs(v) { return String(v || '').split('\n').map(function (x) { return x.trim(); }).filter(Boolean); }
function rndAnhChuoi(a) { return (a || []).join('\n'); }
function rndXemAnh(url) {
  var ov = document.createElement('div');
  ov.style.cssText = 'position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.92);display:flex;align-items:center;justify-content:center;padding:16px';
  ov.innerHTML = '<img src="' + h(url) + '" style="max-width:100%;max-height:100%;border-radius:8px">' +
    '<div style="position:absolute;top:calc(env(safe-area-inset-top,0px) + 12px);right:18px;color:#fff;font-size:32px;line-height:1">&times;</div>';
  ov.onclick = function () { ov.remove(); };
  document.body.appendChild(ov);
}
/* luoi anh. sua = true thi hien nut them va nut xoa */
function rndAnhLuoi(urls, sua, tag) {
  var o = '<div class="rndAnh" data-tag="' + h(tag || '') + '" style="display:flex;flex-wrap:wrap;gap:8px' + (sua ? ';margin-bottom:11px' : ';margin-top:7px') + '">';
  (urls || []).forEach(function (u, i) {
    o += '<div style="position:relative;width:' + (sua ? 68 : 54) + 'px;height:' + (sua ? 68 : 54) + 'px;border-radius:9px;overflow:hidden;border:1px solid #e3e6ec;background:#f5f6f8">' +
      '<img src="' + h(u) + '" data-anh="' + h(u) + '" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block">' +
      (sua ? '<span data-xoa="' + i + '" style="position:absolute;top:0;right:0;width:22px;height:22px;line-height:21px;text-align:center;background:rgba(0,0,0,.62);color:#fff;font-size:15px;border-bottom-left-radius:9px">&times;</span>' : '') +
      '</div>';
  });
  if (sua) o += '<button type="button" data-them style="width:68px;height:68px;border-radius:9px;border:1px dashed #b9c0cc;background:#fafbfc;color:#6b7280;font-size:11.5px;line-height:1.3;padding:4px">\uD83D\uDCF7<br>Thêm ảnh</button>';
  o += '</div>';
  return o;
}
/* gan hanh vi cho luoi anh trong pham vi root. layDs() tra ve mang hien tai, cb(dsMoi) goi sau moi thay doi */
function rndGanAnh(root, tag, layDs, cb) {
  if (!root) return;
  var el = root.querySelector('.rndAnh[data-tag="' + tag + '"]');
  if (!el) return;
  el.onclick = function (e) {
    var im = e.target.closest('[data-anh]');
    if (im) return rndXemAnh(im.getAttribute('data-anh'));
    var x = e.target.closest('[data-xoa]');
    if (x) { var ds = layDs().slice(); ds.splice(+x.getAttribute('data-xoa'), 1); return cb(ds); }
    if (!e.target.closest('[data-them]')) return;
    var inp = document.createElement('input');
    inp.type = 'file'; inp.accept = 'image/*'; inp.multiple = true; inp.style.display = 'none';
    inp.onchange = async function () {
      var fs = Array.prototype.slice.call(this.files || []);
      var self = this;
      if (!fs.length) { self.remove(); return; }
      busy(1);
      var ds = layDs().slice(), loi = 0;
      for (var i = 0; i < fs.length; i++) {
        try { ds.push(await vxUpAnh(fs[i])); } catch (err) { loi++; }
      }
      busy(0); self.remove();
      if (loi) toast('Có ' + loi + ' ảnh không tải lên được, thử lại giúp em', 4200);
      cb(ds);
    };
    document.body.appendChild(inp); inp.click();
  };
}
function rndTienDo(items) {
  var t = { tong: (items || []).length, mua: 0, khong: 0, chua: 0, tien: 0, ocb: 0, anh: 0 };
  (items || []).forEach(function (x) {
    if (x.trang_thai_dong === 'Đã mua') {
      t.mua++; t.tien += Number(x.gia) || 0;
      if ((x.tra_bang || 'Quỹ OCB') === 'Quỹ OCB') t.ocb += Number(x.gia) || 0;
      if (rndAnhDs(x.anh_chung_tu).length) t.anh++;
    } else if (x.trang_thai_dong === 'Không mua được') t.khong++;
    else t.chua++;
  });
  return t;
}
function rndThanh(t) {
  if (!t.tong) return '';
  var pc = Math.round((t.mua + t.khong) * 100 / t.tong);
  return '<div style="margin:9px 0 1px"><div style="height:6px;border-radius:99px;background:#e8eaef;overflow:hidden">' +
    '<div style="height:100%;width:' + pc + '%;background:#0B7C93;transition:width .25s"></div></div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-top:6px">' + t.mua + '/' + t.tong + ' đã mua' +
    (t.khong ? ' · ' + t.khong + ' không mua được' : '') +
    (t.chua ? ' · ' + t.chua + ' chưa mua' : '') + '</div></div>';
}
function rndTre(d) {
  return !!(d && d.ngay_can && String(d.ngay_can).slice(0, 10) < today() &&
    (d.trang_thai === 'Mới tạo' || d.trang_thai === 'Đang xử lý'));
}
function rndBlank() {
  return { ten_hang: '', so_luong: '', link_tham_khao: '', anh_dinh_kem: '', yeu_cau_them: '', can_hoa_don: 0, trang_thai_dong: 'Chưa mua', ncc: '', sdt_ncc: '', gia: 0, tra_bang: 'Quỹ OCB', anh_chung_tu: '', ghi_chu_mua: '' };
}
function rndCopy(x) {
  var o = rndBlank(), k;
  for (k in o) if (x && x[k] !== undefined && x[k] !== null) o[k] = x[k];
  if (x && x.name) o.name = x.name;
  if (x && x.idx) o.idx = x.idx;
  return o;
}
function rndMoney(n) { n = Number(n) || 0; return n.toLocaleString('vi-VN'); }
function rndLbl(t) { return '<div style="font-size:12.5px;font-weight:700;color:#6b7280;margin:2px 0 5px">' + h(t) + '</div>'; }
function rndSeg(nm, opts, cur) {
  return '<div style="display:flex;gap:7px;margin-bottom:11px">' + opts.map(function (o) {
    return '<button type="button" class="btn' + (o === cur ? '' : ' gh') + '" data-seg="' + h(nm) + '" data-v="' + h(o) + '" style="flex:1;height:42px;font-size:13.5px;padding:0 4px">' + h(o) + '</button>';
  }).join('') + '</div>';
}
function rndInp(id, ph, val, num) {
  return '<input class="nt" id="' + id + '" placeholder="' + h(ph) + '" value="' + h(val === 0 ? '' : (val || '')) + '"' +
    (num ? ' type="number" inputmode="decimal" step="any"' : '') + ' style="height:46px;padding:0 12px;margin-bottom:11px">';
}
function rndTa(id, ph, val, rows) {
  return '<textarea class="nt" id="' + id + '" rows="' + (rows || 2) + '" placeholder="' + h(ph) + '" style="margin-bottom:11px">' + h(val || '') + '</textarea>';
}

/* form them / sua mot dong hang, mode = 'req' (nguoi yeu cau) hoac 'buy' (nguoi mua) */
function rndLineSheet(line, mode) {
  return new Promise(function (res) {
    var L = rndCopy(line), isNew = !line;
    var ov = document.createElement('div'); ov.className = 'sh';
    function draw() {
      var b = '<div class="shb" style="padding:16px 16px calc(env(safe-area-inset-bottom,0px) + 16px);max-height:88vh;overflow:auto">' +
        '<div style="font-size:17.5px;font-weight:700;margin-bottom:13px">' +
        (mode === 'buy' ? 'Kết quả mua hàng' : (isNew ? 'Thêm hàng cần mua' : 'Sửa dòng hàng')) + '</div>';
      if (mode === 'buy') {
        b += '<div style="background:#f5f6f8;border-radius:10px;padding:11px 12px;margin-bottom:13px;font-size:14px;line-height:1.6;color:#4a5060">' +
          '<b>' + h(L.ten_hang) + '</b>' + (L.so_luong ? ' · ' + h(L.so_luong) : '') +
          (L.link_tham_khao ? '<br>' + h(L.link_tham_khao) : '') +
          (L.yeu_cau_them ? '<br>' + h(L.yeu_cau_them) : '') +
          (L.can_hoa_don ? '<br>Cần hoá đơn VAT' : '') +
          (rndAnhDs(L.anh_dinh_kem).length ? rndAnhLuoi(rndAnhDs(L.anh_dinh_kem), false, 'xem') : '') + '</div>' +
          rndLbl('Trạng thái dòng này') + rndSeg('trang_thai_dong', ['Chưa mua', 'Đã mua', 'Không mua được'], L.trang_thai_dong) +
          rndLbl('Nhà cung cấp tìm được') + rndInp('rl_ncc', 'Tên farm, shop, nhà cung cấp', L.ncc) +
          rndLbl('Điện thoại nhà cung cấp') + rndInp('rl_sdt', 'Số để lần sau gọi lại', L.sdt_ncc) +
          rndLbl('Giá mua thực tế (đồng)') + rndInp('rl_gia', '0', L.gia, 1) +
          rndLbl('Trả bằng') + rndSeg('tra_bang', ['Quỹ OCB', 'Tiền công ty', 'Khác'], L.tra_bang || 'Quỹ OCB') +
          rndLbl('Ảnh chứng từ (biên lai, hoá đơn)') + rndAnhLuoi(rndAnhDs(L.anh_chung_tu), true, 'buy') +
          rndLbl('Ghi chú của người mua') + rndTa('rl_gcm', 'MOQ bao nhiêu, có xuất hoá đơn không, giao mấy ngày...', L.ghi_chu_mua, 3);
      } else {
        b += rndLbl('Tên hàng cần mua') + rndInp('rl_ten', 'vd: Dứa MD2, chất bảo quản...', L.ten_hang) +
          rndLbl('Số lượng cần') + rndInp('rl_sl', 'vd: 20 kg, 2 thùng, 5 hộp', L.so_luong) +
          rndLbl('Link tham khảo (nếu có)') + rndTa('rl_link', 'Dán link Shopee, website, bài đăng...', L.link_tham_khao, 2) +
          rndLbl('Ảnh tham khảo (chụp màn hình, ảnh sản phẩm)') + rndAnhLuoi(rndAnhDs(L.anh_dinh_kem), true, 'req') +
          rndLbl('Yêu cầu thêm') + rndTa('rl_yc', 'Hỏi MOQ, quy cách đóng gói, cần giao trước ngày nào...', L.yeu_cau_them, 3) +
          rndLbl('Có cần hoá đơn VAT không') + rndSeg('can_hoa_don', ['Cần hoá đơn', 'Không cần'], L.can_hoa_don ? 'Cần hoá đơn' : 'Không cần');
      }
      b += '<button class="btn" data-y>Lưu</button>';
      if (!isNew && mode !== 'buy') b += '<button class="btn dg" data-del style="margin-top:9px">Xoá dòng này</button>';
      b += '<button class="btn gh" data-n style="margin-top:9px">Huỷ</button></div>';
      ov.innerHTML = b;
      var tg = (mode === 'buy') ? 'buy' : 'req';
      rndGanAnh(ov, tg, function () { return rndAnhDs(mode === 'buy' ? L.anh_chung_tu : L.anh_dinh_kem); }, function (ds) {
        grab();
        if (mode === 'buy') L.anh_chung_tu = rndAnhChuoi(ds); else L.anh_dinh_kem = rndAnhChuoi(ds);
        draw();
      });
      rndGanAnh(ov, 'xem', function () { return rndAnhDs(L.anh_dinh_kem); }, function () { });
    }
    function grab() {
      function v(id) { var e = ov.querySelector('#' + id); return e ? e.value.trim() : ''; }
      if (mode === 'buy') {
        L.ncc = v('rl_ncc'); L.sdt_ncc = v('rl_sdt'); L.gia = Number(v('rl_gia')) || 0; L.ghi_chu_mua = v('rl_gcm');
      } else {
        L.ten_hang = v('rl_ten'); L.so_luong = v('rl_sl'); L.link_tham_khao = v('rl_link'); L.yeu_cau_them = v('rl_yc');
      }
    }
    draw();
    document.body.appendChild(ov);
    ov.onclick = function (e) {
      var sg = e.target.closest('[data-seg]');
      if (sg) {
        grab();
        var f = sg.dataset.seg, val = sg.dataset.v;
        if (f === 'can_hoa_don') L.can_hoa_don = (val === 'Cần hoá đơn') ? 1 : 0;
        else L[f] = val;
        return draw();
      }
      if (e.target.hasAttribute('data-del')) { ov.remove(); return res({ del: 1 }); }
      if (e.target === ov || e.target.hasAttribute('data-n')) { ov.remove(); return res(null); }
      if (e.target.hasAttribute('data-y')) {
        grab();
        if (mode !== 'buy' && !L.ten_hang) return toast('Chưa ghi tên hàng cần mua');
        ov.remove(); return res(L);
      }
    };
  });
}

/* ---- 15a. Danh sach phieu ---- */
async function scrRndList() {
  frame('Mua hàng test', '<div class="emp"><div class="e1">⏳</div></div>');
  await loadMasters();
  var docs = [];
  try {
    docs = await getList('RnD Purchase Request', {
      fields: ['name', 'muc_dich', 'ngay_can', 'trang_thai', 'nguoi_yeu_cau', 'nguoi_mua', 'tong_tien', 'modified'],
      limit_page_length: 80, order_by: 'modified desc'
    });
  } catch (e) { toast(errMsg(e)); }
  var dang = docs.filter(function (d) { return d.trang_thai === 'Mới tạo' || d.trang_thai === 'Đang xử lý'; });
  var xong = docs.filter(function (d) { return d.trang_thai === 'Hoàn thành'; });
  var huy = docs.filter(function (d) { return d.trang_thai === 'Huỷ'; });
  function row(d) {
    var s = RNDST[d.trang_thai] || RNDST['Mới tạo'];
    return '<div class="li" data-p="' + h(d.name) + '"><div class="lt">' +
      '<div class="l1">' + h(d.muc_dich || d.name) + '</div>' +
      '<div class="l2">' + h(d.name) + (d.ngay_can ? ' · cần ' + h(dmy(d.ngay_can)) : '') +
      (d.nguoi_yeu_cau ? ' · ' + h(d.nguoi_yeu_cau) : '') +
      (d.tong_tien ? ' · ' + rndMoney(d.tong_tien) + 'đ' : '') + '</div></div>' +
      (rndTre(d) ? '<span class="st r" style="margin-right:5px">Trễ hạn</span>' : '') +
      '<span class="st ' + s.c + '">' + h(s.t) + '</span></div>';
  }
  var body = '<div class="rcvh">Phiếu này dành cho <b>hàng mua về test</b>: không tạo mã, không theo dõi tồn kho. Ghi rõ tên hàng, số lượng, link tham khảo và ảnh chụp màn hình để bạn thu mua khỏi phải hỏi lại. Mua xong bấm <b>Hoàn thành phiếu</b>.</div>';
  if (dang.length) body += '<div class="sec">Đang chờ mua</div><div class="lst">' + dang.map(row).join('') + '</div>';
  if (xong.length) body += '<div class="sec">Đã hoàn thành</div><div class="lst">' + xong.map(row).join('') + '</div>';
  if (huy.length) body += '<div class="sec">Đã huỷ</div><div class="lst">' + huy.map(row).join('') + '</div>';
  if (!docs.length) body += '<div class="emp"><div class="e1">🧪</div><div class="e2">Chưa có phiếu nào.<br>Bấm dấu + để tạo yêu cầu mua hàng test.</div></div>';
  var b = frame('Mua hàng test', body, { fab: true, onFab: function () { rnd.newf = null; go(scrRndNew); } });
  b.onclick = function (e) {
    var r = e.target.closest('[data-p]'); if (!r) return;
    go(function () { scrRndDoc(r.dataset.p); });
  };
}

/* ---- 15b. Tao phieu moi ---- */
async function scrRndNew() {
  await loadMasters();
  if (!rnd.newf) rnd.newf = { muc_dich: '', ngay_can: '', ghi_chu: '', anh_dinh_kem: '', items: [] };
  var f = rnd.newf;
  function draw() {
    var body = '<div class="rcvh">Gom tất cả thứ cần mua để test vào <b>một phiếu</b> theo từng đợt, khỏi nhắn lẻ tẻ qua Lark. Hàng này không nhập kho và không tạo mã.</div>' +
      '<div class="card">' +
      '<div class="fld" data-m><div class="fi">🧪</div><div class="ft"><div class="fl">Mục đích / dự án</div><div class="fv' + (f.muc_dich ? '' : ' ph') + '">' + h(f.muc_dich || 'Bắt buộc - vd: Test bánh dứa MD2') + '</div></div><div class="fc">&#8250;</div></div>' +
      '<div class="fld" data-d><div class="fi">📅</div><div class="ft"><div class="fl">Ngày cần hàng</div><div class="fv' + (f.ngay_can ? '' : ' ph') + '">' + h(f.ngay_can ? dmy(f.ngay_can) : 'Chưa chọn') + '</div></div><div class="fc">&#8250;</div></div>' +
      '<div class="fld" data-g><div class="fi">📝</div><div class="ft"><div class="fl">Ghi chú chung</div><div class="fv' + (f.ghi_chu ? '' : ' ph') + '">' + h(f.ghi_chu || 'Không bắt buộc') + '</div></div><div class="fc">&#8250;</div></div>' +
      '</div>';
    body += '<div class="sec">Ảnh / tài liệu đính kèm cả phiếu</div>' +
      '<div style="padding:0 14px 2px">' + rndAnhLuoi(rndAnhDs(f.anh_dinh_kem), true, 'ph') +
      '<div style="font-size:12.5px;color:#8a90a0;margin:-4px 0 8px">Ảnh chụp màn hình, báo giá, danh sách cần mua... Ảnh riêng của từng món thì đính ngay trong dòng hàng.</div></div>';
    body += '<div class="sec">Hàng cần mua (' + f.items.length + ')</div>';
    if (f.items.length) {
      body += '<div class="lst">' + f.items.map(function (it, i) {
        return '<div class="li" data-i="' + i + '"><div class="lt">' +
          '<div class="l1">' + h(it.ten_hang) + '</div>' +
          '<div class="l2">' + h(it.so_luong || 'chưa ghi số lượng') +
          (it.can_hoa_don ? ' · cần hoá đơn VAT' : '') +
          (it.link_tham_khao ? ' · có link' : '') +
          (rndAnhDs(it.anh_dinh_kem).length ? ' · ' + rndAnhDs(it.anh_dinh_kem).length + ' ảnh' : '') + '</div></div>' +
          '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
      }).join('') + '</div>';
    } else {
      body += '<div class="emp"><div class="e1">🛒</div><div class="e2">Chưa có dòng nào.<br>Bấm nút bên dưới để thêm hàng.<br><span style="font-size:13px;color:#8a90a0">Mỗi dòng có ô dán link tham khảo và ô tải ảnh lên.</span></div></div>';
    }
    body += '<div style="padding:4px 14px 10px"><button class="btn gh" id="rndAdd">+ Thêm hàng cần mua</button></div>';
    var b = frame('Yêu cầu mua hàng test', body, { footer: '<button class="btn" id="rndSave">Gửi yêu cầu</button>' });
    rndGanAnh(b, 'ph', function () { return rndAnhDs(f.anh_dinh_kem); }, function (ds) { f.anh_dinh_kem = rndAnhChuoi(ds); draw(); });
    b.onclick = function (e) {
      if (e.target.closest('[data-m]')) {
        return promptSheet('Mục đích / dự án', 'vd: Test nhân bánh dứa MD2').then(function (v) { if (v !== null) { f.muc_dich = v; draw(); } });
      }
      if (e.target.closest('[data-g]')) {
        return promptSheet('Ghi chú chung cho cả phiếu', 'Không bắt buộc').then(function (v) { if (v !== null) { f.ghi_chu = v; draw(); } });
      }
      if (e.target.closest('[data-d]')) return pickDate(f.ngay_can || today(), function (v) { f.ngay_can = v; draw(); });
      var r = e.target.closest('[data-i]');
      if (r) {
        var i = +r.dataset.i;
        return rndLineSheet(f.items[i], 'req').then(function (v) {
          if (!v) return;
          if (v.del) f.items.splice(i, 1); else f.items[i] = v;
          draw();
        });
      }
    };
    document.getElementById('rndAdd').onclick = function () {
      rndLineSheet(null, 'req').then(function (v) { if (v && !v.del) { f.items.push(v); draw(); } });
    };
    document.getElementById('rndSave').onclick = rndCreate;
  }
  draw();
}

async function rndCreate() {
  var f = rnd.newf;
  if (!f.muc_dich) return toast('Chưa ghi mục đích của phiếu');
  if (!f.items.length) return toast('Chưa có dòng hàng nào');
  busy(1);
  try {
    var d = await api('frappe.client.insert', {
      doc: {
        doctype: 'RnD Purchase Request',
        muc_dich: f.muc_dich,
        ngay_can: f.ngay_can || undefined,
        ghi_chu: f.ghi_chu || undefined,
        anh_dinh_kem: f.anh_dinh_kem || undefined,
        trang_thai: 'Mới tạo',
        nguoi_yeu_cau: S.user,
        items: f.items.map(function (x) { return rndCopy(x); })
      }
    });
    busy(0);
    if (!d || !d.name) return toast('Không tạo được phiếu, thử lại giúp');
    rnd.newf = null;
    toast('Đã gửi yêu cầu ' + d.name);
    go(function () { scrRndDoc(d.name); }, true);
  } catch (e) { busy(0); toast(errMsg(e), 5000); }
}

/* ---- 15c. Xem va xu ly phieu ---- */
async function scrRndDoc(name) {
  frame('Phiếu mua test', '<div class="emp"><div class="e1">⏳</div></div>');
  await loadMasters();
  var doc = null;
  try { doc = await api('frappe.client.get', { doctype: 'RnD Purchase Request', name: name }); }
  catch (e) { toast(errMsg(e)); return back(); }

  function tong() {
    return (doc.items || []).reduce(function (a, x) { return a + (x.trang_thai_dong === 'Đã mua' ? (Number(x.gia) || 0) : 0); }, 0);
  }
  async function save(msg) {
    busy(1);
    try {
      doc.tong_tien = tong();
      doc = await api('frappe.client.save', { doc: doc });
      busy(0);
      if (msg) toast(msg);
      draw();
    } catch (e) { busy(0); toast(errMsg(e), 5000); }
  }

  function draw() {
    var live = doc.trang_thai === 'Mới tạo' || doc.trang_thai === 'Đang xử lý';
    var mine = doc.nguoi_yeu_cau === S.user || doc.owner === S.user;
    var s = RNDST[doc.trang_thai] || RNDST['Mới tạo'];
    var td = rndTienDo(doc.items);
    var chua = td.chua;
    var body = '<div class="card" style="padding:13px 14px">' +
      '<div style="display:flex;align-items:center;gap:9px;margin-bottom:7px">' +
      '<b style="font-size:16.5px;flex:1">' + h(doc.muc_dich || doc.name) + '</b>' +
      (rndTre(doc) ? '<span class="st r">Trễ hạn</span>' : '') +
      '<span class="st ' + s.c + '">' + h(s.t) + '</span></div>' +
      '<div style="font-size:13.5px;color:#6b7280;line-height:1.7">' + h(doc.name) +
      (doc.ngay_can ? '<br>Cần hàng ngày ' + h(dmy(doc.ngay_can)) : '') +
      (doc.nguoi_yeu_cau ? '<br>Người yêu cầu: ' + h(doc.nguoi_yeu_cau) : '') +
      (doc.nguoi_mua ? '<br>Người mua: ' + h(doc.nguoi_mua) : '') +
      (doc.ghi_chu ? '<br>Ghi chú: ' + h(doc.ghi_chu) : '') +
      '<br>Tổng tiền đã mua: <b>' + rndMoney(tong()) + 'đ</b>' +
      '</div>' + rndThanh(td) + '</div>';

    var suaAnh = live && mine;
    body += '<div class="sec">Ảnh / tài liệu đính kèm cả phiếu</div><div style="padding:0 14px 6px">';
    if (rndAnhDs(doc.anh_dinh_kem).length || suaAnh) body += rndAnhLuoi(rndAnhDs(doc.anh_dinh_kem), suaAnh, 'ph');
    else body += '<div style="font-size:13.5px;color:#8a90a0;padding-bottom:6px">Chưa có ảnh nào.</div>';
    body += '</div>';

    body += '<div class="sec">Hàng cần mua (' + (doc.items || []).length + ')</div><div class="lst">' +
      (doc.items || []).map(function (it, i) {
        var ls = RNDLS[it.trang_thai_dong] || RNDLS['Chưa mua'];
        var sub = h(it.so_luong || 'chưa ghi số lượng');
        if (it.can_hoa_don) sub += ' · cần hoá đơn VAT';
        if (it.ncc) sub += '<br>NCC: ' + h(it.ncc) + (it.sdt_ncc ? ' · ' + h(it.sdt_ncc) : '');
        if (it.gia) sub += '<br>Giá: ' + rndMoney(it.gia) + 'đ';
        if (it.yeu_cau_them) sub += '<br>' + h(it.yeu_cau_them);
        if (it.trang_thai_dong === 'Đã mua' && it.tra_bang) sub += '<br>Trả bằng: ' + h(it.tra_bang);
        if (it.link_tham_khao) sub += '<br><span style="color:#0B7C93;word-break:break-all">' + h(it.link_tham_khao) + '</span>';
        if (it.ghi_chu_mua) sub += '<br>Người mua: ' + h(it.ghi_chu_mua);
        var anhL = rndAnhDs(it.anh_dinh_kem).concat(rndAnhDs(it.anh_chung_tu));
        if (anhL.length) sub += rndAnhLuoi(anhL, false, '');
        return '<div class="li" data-i="' + i + '"><div class="lt">' +
          '<div class="l1">' + h(it.ten_hang) + '</div>' +
          '<div class="l2">' + sub + '</div></div>' +
          '<span class="st ' + ls.c + '">' + h(ls.t) + '</span></div>';
      }).join('') + '</div>';

    if (live) {
      body += '<div class="kwn">Bấm vào một dòng để ghi kết quả mua: nhà cung cấp, giá, ghi chú. ' +
        (mine ? 'Là người tạo phiếu nên anh chị vẫn sửa hoặc thêm dòng được khi phiếu chưa hoàn thành.' : '') + '</div>';
      if (mine) body += '<div style="padding:4px 14px 10px"><button class="btn gh" id="rndAdd2">+ Thêm hàng cần mua</button></div>';
    }

    if (doc.trang_thai === 'Hoàn thành' && td.tien > 0) {
      body += '<div class="sec">Quỹ tạm ứng OCB</div><div class="card" style="padding:13px 14px;font-size:14px;line-height:1.75;color:#4a5060">' +
        'Chi từ quỹ OCB: <b>' + rndMoney(td.ocb) + 'đ</b><br>' +
        'Tổng tiền cả phiếu: <b>' + rndMoney(td.tien) + 'đ</b><br>' +
        'Khoản đã có ảnh chứng từ: <b>' + td.anh + '/' + td.mua + '</b>' +
        (doc.phieu_chi_phi ? '<br>Đã lập phiếu ghi chi phí: <b>' + h(doc.phieu_chi_phi) + '</b>' : '') +
        '</div>';
      if (!doc.phieu_chi_phi && td.ocb > 0 && rndLaThuMua()) {
        body += '<div class="kwn">Bấm nút dưới để em dựng sẵn một hoá đơn mua hàng ở dạng nháp, ghi là đã trả từ quỹ OCB. Kế toán xem lại rồi mới ghi sổ.</div>' +
          '<div style="padding:4px 14px 10px"><button class="btn gh" id="rndChiPhi">Lập phiếu ghi chi phí (nháp)</button></div>';
      }
    }

    var ft = '';
    if (live) {
      ft = '<button class="btn" id="rndDone">Hoàn thành phiếu' + (chua ? ' (' + chua + ' dòng chưa mua)' : '') + '</button>';
      if (mine) ft += '<button class="btn gh" id="rndCancel" style="margin-top:9px">Huỷ phiếu</button>';
    }
    var b = frame('Phiếu mua test', body, ft ? { footer: ft } : {});
    rndGanAnh(b, 'ph', function () { return rndAnhDs(doc.anh_dinh_kem); }, function (ds) {
      doc.anh_dinh_kem = rndAnhChuoi(ds); save('Đã cập nhật ảnh');
    });
    b.onclick = function (e) {
      var im0 = e.target.closest('[data-anh]');
      if (im0 && !e.target.closest('.rndAnh[data-tag="ph"]')) return rndXemAnh(im0.getAttribute('data-anh'));
      var r = e.target.closest('[data-i]'); if (!r) return;
      var i = +r.dataset.i;
      if (!live) return;
      var canEdit = mine && doc.items[i].trang_thai_dong === 'Chưa mua';
      var opts = [{ value: 'buy', label: 'Ghi kết quả mua hàng', icon: '💰' }];
      if (canEdit) opts.push({ value: 'req', label: 'Sửa nội dung yêu cầu', icon: '✏️' });
      function open(mode) {
        rndLineSheet(doc.items[i], mode).then(function (v) {
          if (!v) return;
          if (v.del) { doc.items.splice(i, 1); return save('Đã xoá dòng'); }
          var row = doc.items[i], k;
          for (k in v) if (k !== 'name' && k !== 'idx') row[k] = v[k];
          if (mode === 'buy' && !doc.nguoi_mua) doc.nguoi_mua = S.user;
          if (mode === 'buy' && doc.trang_thai === 'Mới tạo') doc.trang_thai = 'Đang xử lý';
          save('Đã lưu');
        });
      }
      if (opts.length === 1) return open('buy');
      sheet(doc.items[i].ten_hang, opts, '', function (o) { open(o.value); });
    };
    var ad = document.getElementById('rndAdd2');
    if (ad) ad.onclick = function () {
      rndLineSheet(null, 'req').then(function (v) {
        if (!v || v.del) return;
        doc.items.push(v); save('Đã thêm dòng');
      });
    };
    var cpn = document.getElementById('rndChiPhi');
    if (cpn) cpn.onclick = async function () {
      var ds = (doc.items || []).filter(function (x) {
        return x.trang_thai_dong === 'Đã mua' && (x.tra_bang || 'Quỹ OCB') === 'Quỹ OCB' && (Number(x.gia) || 0) > 0;
      });
      if (!ds.length) return toast('Không có khoản nào chi từ quỹ OCB');
      var tongDs = ds.reduce(function (a, x) { return a + (Number(x.gia) || 0); }, 0);
      var coVat = ds.filter(function (x) { return x.can_hoa_don; }).length;
      var ok = await confirmSheet('Lập phiếu ghi chi phí?',
        'Em tạo một hoá đơn mua hàng ở dạng NHÁP gồm ' + ds.length + ' khoản, tổng ' + rndMoney(tongDs) + 'đ, ghi là đã trả từ quỹ OCB.\n\n' +
        (coVat ? 'Trong đó ' + coVat + ' khoản có hoá đơn VAT, kế toán sẽ nhập phần thuế và đổi sang đúng nhà cung cấp.\n\n' : '') +
        'Phiếu chỉ ở dạng nháp, kế toán xem lại rồi mới ghi sổ.', 'Lập phiếu nháp');
      if (!ok) return;
      function than(coTra) {
        var d2 = {
          doctype: 'Purchase Invoice', company: COMPANY, supplier: RND_NCC_LE,
          posting_date: today(), set_posting_time: 1, bill_no: doc.name,
          remarks: 'Mua hàng test theo phiếu ' + doc.name + (doc.muc_dich ? ' - ' + doc.muc_dich : ''),
          items: ds.map(function (x) {
            return {
              item_code: x.can_hoa_don ? 'CP-MUANHO-HD' : 'CP-MUANHO-KHD',
              item_name: String(x.ten_hang || 'Hàng test').slice(0, 140),
              description: String(x.ten_hang || '') + (x.so_luong ? ' - ' + x.so_luong : '') + (x.ncc ? ' - NCC: ' + x.ncc : ''),
              qty: 1, uom: 'Lần', rate: Number(x.gia) || 0
            };
          })
        };
        if (coTra) { d2.is_paid = 1; d2.mode_of_payment = 'Chuyển khoản'; d2.cash_bank_account = RND_OCB_TK; d2.paid_amount = tongDs; }
        return d2;
      }
      busy(1);
      var pi = null;
      try { pi = await api('frappe.client.insert', { doc: than(true) }); }
      catch (e1) {
        try { pi = await api('frappe.client.insert', { doc: than(false) }); }
        catch (e2) { busy(0); return toast(errMsg(e2), 6000); }
      }
      busy(0);
      if (!pi || !pi.name) return toast('Không lập được phiếu, thử lại giúp em');
      doc.phieu_chi_phi = pi.name;
      await save('Đã lập phiếu nháp ' + pi.name);
    };
    var dn = document.getElementById('rndDone');
    if (dn) dn.onclick = async function () {
      var ok = await confirmSheet('Hoàn thành phiếu này?',
        chua ? ('Còn ' + chua + ' dòng đang ở trạng thái Chưa mua. Nếu không mua được thì nên đánh dấu "Không mua được" cho từng dòng rồi hãy hoàn thành, để sau này còn tra lại.\n\nVẫn hoàn thành phiếu?')
          : 'Sau khi hoàn thành, phiếu sẽ chuyển sang mục Đã hoàn thành và không sửa được nữa.',
        'Hoàn thành phiếu');
      if (!ok) return;
      doc.trang_thai = 'Hoàn thành';
      if (!doc.nguoi_mua) doc.nguoi_mua = S.user;
      var _n = new Date(); doc.ngay_hoan_thanh = ymdOf(_n) + ' ' + hmOf(_n);
      await save('Đã hoàn thành phiếu');
    };
    var cn = document.getElementById('rndCancel');
    if (cn) cn.onclick = async function () {
      var ok = await confirmSheet('Huỷ phiếu này?', 'Phiếu sẽ chuyển sang mục Đã huỷ. Nội dung vẫn giữ lại để tra cứu.', 'Huỷ phiếu', true);
      if (!ok) return;
      doc.trang_thai = 'Huỷ';
      await save('Đã huỷ phiếu');
    };
  }
  draw();
}

/* ---------- 16. Boot ---------- */
document.title = APPNAME;
/* ---------- Doanh thu Sales: ra soat, chot le tung don, nhap tay ---------- */
var dsNgay = null;
var dsLoc = 'tat_ca', dsLocNg = '', dsLocHd = '';
function dsChip(txt, bg, fg) {
  return '<span style="display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:700;background:' + bg + ';color:' + fg + ';margin-right:5px;white-space:nowrap">' + txt + '</span>';
}
var DS_MAU_HD = {
  'Chờ duyệt': ['#fef3c7', '#92400e'], 'Chờ ký': ['#fef3c7', '#92400e'], 'Đang ký': ['#fef3c7', '#92400e'],
  'Đã ký': ['#dcfce7', '#166534'], 'Đã gửi CQT': ['#dcfce7', '#166534'], 'CQT chấp nhận': ['#bbf7d0', '#14532d'],
  'CQT báo lỗi': ['#fee2e2', '#991b1b'], 'Lỗi': ['#fee2e2', '#991b1b'], 'Đã hủy': ['#fee2e2', '#991b1b'],
  'HĐ điều chỉnh': ['#ede9fe', '#5b21b6'], 'HĐ thay thế': ['#ede9fe', '#5b21b6'],
  'Bị điều chỉnh': ['#ede9fe', '#5b21b6'], 'Bị thay thế': ['#ede9fe', '#5b21b6']
};
function dsChips(r) {
  var out = '';
  var tt = r.custom_hddt_trang_thai || '';
  if (r.custom_hddt_so || tt) {
    var mau = DS_MAU_HD[tt] || ['#e5e7eb', '#374151'];
    var nhan = (r.custom_hddt_so ? 'HĐ ' + h(r.custom_hddt_so) : 'HĐĐT') + (tt ? ' · ' + h(tt) : '');
    out += dsChip(nhan, mau[0], mau[1]);
  } else if (r.docstatus === 1) {
    out += dsChip('Chưa có HĐĐT', '#fee2e2', '#991b1b');
  }
  if (r.vgb_pt_thanh_toan) out += dsChip(h(r.vgb_pt_thanh_toan), '#e0f2fe', '#075985');
  else out += dsChip('Chưa chọn thanh toán', '#fee2e2', '#991b1b');
  /* SePay doc thang tu giao dich ngan hang, khong phu thuoc ai co go tay ma
     tham chieu hay khong. Truoc day chip nay bat theo o ma tham chieu nen
     don chuyen khoan da vao du tien van trong nhu chua nhan, con don ca the
     Payoo go so bill lai hien "SePay" - sai ca hai chieu. */
  if (r.sepay_du) out += dsChip('SePay ✓ đủ tiền', '#dcfce7', '#166534');
  else if (r.sepay_nhan) out += dsChip('SePay thiếu ' + money(Number(r.grand_total || 0) - Number(r.sepay_nhan || 0)) + ' đ', '#ffedd5', '#9a3412');
  if (r.vgb_ma_tham_chieu) out += dsChip('Mã ' + h(r.vgb_ma_tham_chieu), '#ede9fe', '#5b21b6');
  if (r.vgb_xhd_mst) out += dsChip('Xuất cho công ty', '#fef9c3', '#854d0e');
  if (r.trung) out += dsChip('⚠ Trùng phiếu', '#fee2e2', '#991b1b');
  return out;
}
async function scrDoanhSo() {
  if (!dsNgay) dsNgay = today();
  frame('Doanh thu Sales', '<div class="emp"><div class="e1">⏳</div><div>Đang tải doanh thu...</div></div>');
  var d;
  try { d = await api('vagabond.ban_hang.bang_doanh_so', { ngay: dsNgay }); }
  catch (e) { frame('Doanh thu Sales', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được, thử lại sau') + '</div></div>'); return; }
  var rows = d.rows || [];
  var nhap = rows.filter(function (r) { return r.docstatus === 0; });
  var html = '<div class="card" style="padding:12px 14px;display:flex;align-items:center;gap:12px">' +
    '<div style="font-weight:600;white-space:nowrap">Ngày bán</div>' +
    '<input type="date" class="hin" id="dsDate" value="' + dsNgay + '" max="' + today() + '" style="flex:1;margin:0">' +
    '</div>' + '<div class="card" style="padding:2px 14px 12px">' + chipNgay('data-dsbuoc') + '</div>';
  html += '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between"><span>Chưa chốt</span><b>' + money(d.tong_nhap) + ' đ · ' + nhap.length + ' đơn</b></div>' +
    '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Đã chốt</span><b style="color:#0a8a4a">' + money(d.tong_chot) + ' đ · ' + (rows.length - nhap.length) + ' đơn</b></div>' +
    (d.dong_bo_luc ? '<div style="color:#a0a6b4;font-size:12px;margin-top:6px">Máy tự đồng bộ Pancake 30 phút một lần · lần cuối ' + h(d.dong_bo_luc) + '</div>' : '') +
    '<div id="dsChoGiao"></div></div>';
  if (d.so_don_trung) {
    html += '<div class="sec">Đơn bị trùng phiếu</div><div class="card" style="padding:12px 14px;border:1.5px solid #fecaca;background:#fff1f2;color:#991b1b;font-size:13px;line-height:1.6">' +
      '<b>' + d.so_don_trung + ' đơn đang có hai mã phiếu</b><br>' +
      'Một đơn Pancake mà thành hai phiếu thì ghi sổ xong doanh thu bị tính đôi. Bấm nút dưới, em giữ lại một phiếu và gỡ phiếu thừa (chỉ gỡ phiếu còn nháp, phiếu đã ghi sổ hay đã có hoá đơn điện tử thì em không đụng vào).' +
      '<div style="margin-top:10px"><button class="btn gh" data-ds="gotrung" style="width:100%">🧹 Rà và gỡ phiếu trùng</button></div></div>';
  }
  if ((d.loi || []).length) {
    html += '<div class="sec">Cần xử lý trước khi chốt</div><div class="card" style="padding:12px 14px;color:#b3261e;font-size:13px;line-height:1.6">' + d.loi.map(h).join('<br>') + '</div>';
  }
  /* Bo loc nhanh: sau muoi may dong ma soat bang mat thi de sot. */
  /* Bo loc hai tang: tinh trang x nguon/phuong thuc, giao nhau de soat
     duoc kieu "GrabFood ma chua ve tien" (anh Viet 10/08/2026). */
  var DSTT = [
    { k: 'tat_ca', nhan: 'Tất cả', loc: function () { return true; } },
    { k: 'chua_ghi', nhan: '📄 Chưa ghi sổ', loc: function (r) { return r.docstatus === 0; } },
    { k: 'da_ghi', nhan: '✅ Đã ghi sổ', loc: function (r) { return r.docstatus === 1; } },
    { k: 'chua_pt', nhan: '❓ Chưa chọn thanh toán', loc: function (r) { return r.docstatus === 0 && !r.vgb_pt_thanh_toan; } },
    { k: 'chua_tien', nhan: '⏳ Chuyển khoản chưa về tiền', loc: function (r) { return r.vgb_pt_thanh_toan === 'Chuyển khoản' && !r.sepay_du; } },
    { k: 'du_tien', nhan: '💰 SePay đã đủ tiền', loc: function (r) { return !!r.sepay_du; } },
    { k: 'chua_hddt', nhan: '📌 Chưa có hoá đơn điện tử', loc: function (r) { return r.docstatus === 1 && !r.custom_hddt_so; } },
    { k: 'xhd_cty', nhan: '🏢 Xuất hoá đơn công ty', loc: function (r) { return !!(r.vgb_xhd_mst || r.can_hddt); } },
    { k: 'trung', nhan: '⚠ Trùng phiếu', loc: function (r) { return !!r.trung; } }
  ];
  var DSNG = locNguonPt(rows);
  var DSHD = locHddt();
  if (!locTim(DSTT, dsLoc) || locTim(DSTT, dsLoc).k !== dsLoc) dsLoc = 'tat_ca';
  var fTt = locTim(DSTT, dsLoc), fNg = locTim(DSNG, dsLocNg), fHd = locTim(DSHD, dsLocHd);
  dsLocNg = fNg.k; dsLocHd = fHd.k;
  html += '<div class="card" style="padding:10px 12px;display:flex;flex-direction:column;gap:7px">' +
    locHang(DSTT, dsLoc, 'data-loc', rows) +
    locHang(DSNG, dsLocNg, 'data-locng', rows.filter(fTt.loc)) +
    locHang(DSHD, dsLocHd, 'data-lochd', rows.filter(fTt.loc)) + '</div>';
  var loc = rows.filter(function (r) { return fTt.loc(r) && fNg.loc(r) && fHd.loc(r); });
  html += locKhoiTong(loc, [
    dsLoc === 'tat_ca' ? '' : fTt.nhan, fNg.k ? fNg.nhan : '', fHd.k ? fHd.nhan : ''
  ].filter(Boolean).join(' · '));
  html += '<div class="sec">Đơn trong ngày · bấm vào đơn để xem chi tiết</div><div class="card">';
  if (!rows.length) html += '<div class="emp" style="padding:24px"><div class="e1">🌤️</div><div>Chưa có đơn nào. Bấm Đồng bộ để kéo từ Pancake, hoặc dấu ➕ để nhập tay đơn Grab, Be.</div></div>';
  else if (!loc.length) html += '<div class="emp" style="padding:24px"><div class="e1">✅</div><div>Không có đơn nào thuộc nhóm <b>' + fTt.nhan + (fNg.k ? ' · ' + fNg.nhan : '') + '</b>.</div></div>';
  loc.forEach(function (r) {
    var kh = (r.remarks || '').split(' - ');
    var ng = (r.custom_nguon && r.custom_nguon !== 'Pancake') ? h(r.custom_nguon) + ' ' : '';
    var dong2 = h(r.name) + ' · ' + (r.docstatus === 1 ? 'Đã chốt' : 'Nháp');
    var chips = dsChips(r);
    html += '<div class="hub" data-si="' + h(r.name) + '" data-can="' + (r.can_hddt ? 1 : 0) + '"><div class="hi">' + (r.docstatus === 1 ? '✅' : '📝') + '</div>' +
      '<div class="ht"><div class="h1">' + ng + '#' + h(r.custom_pancake_display_id || '?') + ' · ' + h(kh[1] || 'Khách lẻ') + '</div>' +
      '<div class="h2">' + dong2 + '</div>' + (chips ? '<div class="h2" style="margin-top:4px;line-height:1.9">' + chips + '</div>' : '') + '</div>' +
      '<b style="white-space:nowrap;font-size:13px">' + money(r.grand_total) + '</b></div>';
  });
  html += '</div>';
  var foot = '<div style="display:flex;gap:10px"><button class="btn gh" data-ds="dongbo" style="flex:1">🔄 Đồng bộ Pancake</button>' +
    (nhap.length ? '<button class="btn" data-ds="chot" style="flex:2">Ghi sổ hoá đơn bán hàng (' + nhap.length + ' đơn)</button>' : '') + '</div>';
  var b = frame('Doanh thu Sales', html, { footer: foot, action: '➕', onAction: function () { go(scrDsNhapTay); } });
  var di = document.getElementById('dsDate');
  if (di) di.onchange = function () { if (di.value && di.value <= today()) { dsNgay = di.value; dsLoc = 'tat_ca'; dsLocNg = ''; go(scrDoanhSo, true); } };
  veODate('dsDate');
  /* Doanh thu chi ghi nhan don DA GIAO XONG. Sang som chua ai giao thi
     man nay 0 dong, sales tuong mat dong bo roi bam Dong bo hoai (anh Viet
     bao 11/08/2026). Nay dem luon so don CON CHO GIAO de biet la binh
     thuong, khong phai hong. */
  (async function () {
    try {
      var vd = await getList('Van Don', {
        fields: ['name', 'trang_thai'],
        filters: { ngay_giao: dsNgay },
        limit_page_length: 0
      });
      var cho = (vd || []).filter(function (x) { return x.trang_thai === 'Chờ giao' || x.trang_thai === 'Đang giao'; }).length;
      var o2 = document.getElementById('dsChoGiao');
      if (o2 && cho) {
        o2.innerHTML = '<div style="margin-top:8px;background:#ecfeff;border:1.5px solid #7fe5f6;border-radius:9px;padding:9px 11px;font-size:12.5px;color:#0b7c93;line-height:1.5">' +
          '🛵 Còn <b>' + cho + ' đơn chưa giao xong</b> trong ngày. Doanh thu chỉ ghi nhận khi đơn đã giao thành công, nên số ở trên còn thiếu là bình thường.</div>';
      }
    } catch (e2) { }
  })();
  b.addEventListener('click', function (e) {
    var t = e.target.closest('[data-dsbuoc]'); if (!t) return;
    var bu = +t.getAttribute('data-dsbuoc');
    var moi = bu ? ngayCong(dsNgay, bu) : today();
    if (moi > today()) return toast('Chưa tới ngày đó.');
    dsNgay = moi; dsLoc = 'tat_ca'; dsLocNg = '';
    go(scrDoanhSo, true);
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-loc]'), function (el) {
    el.onclick = function () { dsLoc = el.getAttribute('data-loc'); go(scrDoanhSo, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-lochd]'), function (el) {
    el.onclick = function () { dsLocHd = el.getAttribute('data-lochd'); go(scrDoanhSo, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-locng]'), function (el) {
    el.onclick = function () { dsLocNg = el.getAttribute('data-locng'); go(scrDoanhSo, true); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-ds]'), function (el) {
    el.onclick = function () { dsHanh(el.getAttribute('data-ds')); };
  });
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-si]'); if (!r) return;
    var nm = r.getAttribute('data-si'), can = r.getAttribute('data-can') === '1';
    go(function () { scrDsView(nm, can); });
  });
}
var dsDangDongBo = false;
async function dsHanh(k) {
  if (k === 'gotrung') {
    busy(true);
    var ke;
    try { ke = await api('vagabond.ban_hang.ds_don_trung', { ngay: dsNgay }); }
    catch (e) { busy(false); window.alert((e && e.message) || 'Không rà được'); return; }
    busy(false);
    var nhom = (ke && ke.nhom) || [];
    if (!nhom.length) { toast('Rà xong, không còn đơn nào bị trùng.'); go(scrDoanhSo, true); return; }
    var mo = nhom.map(function (n) {
      return '#' + n.don + ': giữ ' + n.giu + (n.go.length ? ', gỡ ' + n.go.join(', ') : '') + (n.ket.length ? '\n   ' + n.ket.join('\n   ') : '');
    }).join('\n');
    if (!window.confirm('Em sẽ xử lý như sau:\n\n' + mo + '\n\nĐồng ý gỡ chứ?')) return;
    busy(true);
    try { var kq3 = await api('vagabond.ban_hang.go_don_trung', { ngay: dsNgay }); busy(false); toast('Đã gỡ ' + (kq3.da_go || []).length + ' phiếu thừa' + ((kq3.ket || []).length ? ', ' + kq3.ket.length + ' phiếu phải xử lý tay' : ''), 3500); if ((kq3.ket || []).length) window.alert(kq3.ket.join('\n')); }
    catch (e) { busy(false); window.alert((e && e.message) || 'Gỡ lỗi'); }
    go(scrDoanhSo, true); return;
  }
  if (k === 'dongbo') {
    /* Bam hai lan trong vong vai giay la hai yeu cau chay song song, moi ben
       tao mot phieu cho cung mot don. May chu da co khoa, day chan them o
       ngay dau ngon tay cho khoi phai cho bao loi. */
    if (dsDangDongBo) { toast('Đang đồng bộ rồi, chờ chút nhé.'); return; }
    dsDangDongBo = true;
    busy(true);
    try { var kq = await api('vagabond.ban_hang.dong_bo_doanh_so', { ngay: dsNgay }); busy(false); toast('Kéo ' + (kq.so_don_pancake || 0) + ' đơn: ' + (kq.tao_moi || 0) + ' mới, ' + (kq.cap_nhat || 0) + ' cập nhật' + ((kq.loi || []).length ? ', ' + kq.loi.length + ' lỗi' : ''), 3500); }
    catch (e) { busy(false); window.alert((e && e.message) || 'Đồng bộ lỗi'); }
    dsDangDongBo = false;
    go(scrDoanhSo, true); return;
  }
  if (k === 'chot') {
    if (!window.confirm('Chốt TOÀN BỘ đơn nháp của ngày ' + dsNgay.split('-').reverse().join('/') + '? Muốn chốt lẻ thì bấm vào từng đơn.')) return;
    busy(true);
    try {
      var kq2 = await api('vagabond.ban_hang.chot_doanh_so', { ngay: dsNgay }); busy(false);
      toast('Đã chốt ' + kq2.da_chot + ' đơn, xuất ' + (kq2.da_xuat_hddt || 0) + ' hoá đơn điện tử' + ((kq2.loi || []).length ? ', ' + kq2.loi.length + ' đơn cần xem lại' : ''), 4000);
      if ((kq2.loi || []).length) window.alert(kq2.loi.join('\n'));
    }
    catch (e) { busy(false); window.alert((e && e.message) || 'Chốt lỗi'); }
    go(scrDoanhSo, true); return;
  }
}
var CFGBH = null;
async function cfgBanHang() {
  if (!CFGBH) CFGBH = await api('vagabond.ban_hang.cau_hinh_ban_hang', {});
  return CFGBH;
}
function nguonBH(v) {
  var r = null;
  ((CFGBH || {}).nguon || []).forEach(function (n) { if (n.v === v) r = n; });
  return r;
}
function ptTheoNguon(v) {
  var c = CFGBH || { pt: [], nguon: [] };
  var n = nguonBH(v);
  var ds = n ? n.pt : (c.pt_pancake || []);
  return (c.pt || []).filter(function (p) { return ds.indexOf(p.v) >= 0; });
}
function quyPt(v) {
  var r = null;
  ((CFGBH || {}).pt || []).forEach(function (p) { if (p.v === v) r = p; });
  return r;
}
function chipPt(ds, chon) {
  return ds.map(function (p) {
    var on = p.v === chon;
    return '<button class="ptc" data-pt="' + p.v + '" style="display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:8px;font-size:13px;border:1.5px solid ' +
      (on ? '#0d9488;background:#ccfbf1;color:#0f766e;font-weight:bold' : '#e5e7eb;background:#fff;color:#374151') + '">' +
      (p.lg ? '<img src="' + p.lg + '" style="height:18px;border-radius:3px">' : '🏦 ') + p.v + '</button>';
  }).join('');
}
function veChipPt(wrap, chon) {
  if (!wrap) return;
  wrap.querySelectorAll('.ptc').forEach(function (x) {
    var on = x.getAttribute('data-pt') === chon;
    x.style.border = '1.5px solid ' + (on ? '#0d9488' : '#e5e7eb');
    x.style.background = on ? '#ccfbf1' : '#fff';
    x.style.color = on ? '#0f766e' : '#374151';
    x.style.fontWeight = on ? 'bold' : 'normal';
  });
}
/* O ngay tren MAY TINH: tren dien thoai cham dau vao o cung mo lich,
   nhung tren laptop thi phai bam trung dung cai bieu tuong lich be xiu o
   goc phai - anh Viet 11/08/2026 bao khong chon duoc ngay. Nay bam bat cu
   dau trong o la lich bat ra (showPicker), khong con phai nham nhi. */
/* Cong tru mot ngay cho o ngay. Thu ngan doi ngay chu yeu la "hom qua"
   hay "hom nay", bam chip nhanh hon mo lich nhieu - va chac an tren MOI
   may, khong phu thuoc lich cua trinh duyet (anh Viet 11/08/2026). */
function ngayCong(iso, buoc) {
  var d = new Date(String(iso || today()) + 'T00:00:00');
  d.setDate(d.getDate() + buoc);
  var hs = function (n) { return (n < 10 ? '0' : '') + n; };
  return d.getFullYear() + '-' + hs(d.getMonth() + 1) + '-' + hs(d.getDate());
}
function chipNgay(attr) {
  return '<div style="display:flex;gap:7px;flex-wrap:wrap;margin-top:9px">' +
    posChipNut(attr + '="-1"', '\u25c0 Hôm trước', false) +
    posChipNut(attr + '="0"', 'Hôm nay', false) +
    posChipNut(attr + '="1"', 'Hôm sau \u25b6', false) +
    '</div>';
}

function veODate(id) {
  var o = document.getElementById(id);
  if (!o) return null;
  var mo = function (e) {
    if (typeof o.showPicker !== 'function') return;
    /* Bam trung bieu tuong lich thi de trinh duyet tu lo, goi them
       showPicker nua se bi bao loi da mo roi. */
    try { o.showPicker(); if (e) e.preventDefault(); } catch (er) { }
  };
  o.onmousedown = function (e) {
    if (e && e.button) return;
    mo(e);
  };
  o.onkeydown = function (e) {
    if (e && (e.key === 'Enter' || e.key === ' ')) mo(e);
  };
  return o;
}

function veOMtc(pt, idO, idNhan) {
  var q = quyPt(pt) || {};
  var o = document.getElementById(idO), nh = document.getElementById(idNhan);
  if (!o) return;
  var hien = !!(q.nhan || q.bat);
  o.parentElement.style.display = hien ? '' : 'none';
  var ten = q.nhan || 'Mã tham chiếu';
  o.placeholder = ten + (q.vd ? ' - vd ' + q.vd : '');
  o.style.borderColor = q.bat && !o.value.trim() ? '#f59e0b' : '#e5e7eb';
  /* TEN cua o phai nam NGOAI o. Truoc day ten chi nam trong placeholder,
     nhan vien go xong roi quay lai sua thi placeholder bi che mat, khong
     con biet o do la o gi (anh Viet 11/08/2026). */
  if (nh) {
    nh.innerHTML = '<b style="color:#374151;font-size:12.5px">' + h(ten) + '</b>' +
      (q.bat
        ? ' · <b style="color:#b45309">bắt buộc</b> để đối soát'
        : (pt === 'Chuyển khoản' ? ' · SePay tự khớp, để trống cũng được' : ' · không bắt buộc'));
  }
}
async function scrDsView(name, can) {
  frame('Chi tiết đơn', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('frappe.client.get', { doctype: 'Sales Invoice', name: name }); }
  catch (e) { frame('Chi tiết đơn', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được đơn') + '</div></div>'); return; }
  var kh = (d.remarks || '').split(' - ');
  var vn = String(d.posting_date || '').split('-');
  var html = '<div class="card" style="padding:12px 14px;line-height:1.7">' +
    '<div style="display:flex;justify-content:space-between"><b>#' + h(d.custom_pancake_display_id || '?') + ' · ' + h(d.custom_nguon || 'Pancake') + '</b>' +
    '<span>' + (d.docstatus === 1 ? '✅ Đã chốt' : '📝 Nháp') + '</span></div>' +
    '<div>' + h(kh[1] || 'Khách lẻ') + (kh[2] ? ' · ' + h(kh[2]) : '') + '</div>' +
    '<div style="color:#6b7280;font-size:13px">Mã phiếu: <b>' + h(d.name) + '</b> · Ngày ' + (vn.length === 3 ? vn[2] + '/' + vn[1] + '/' + vn[0] : h(d.posting_date)) + '</div>' +
    (d.custom_hddt_so ? '<div style="color:#0a8a4a;font-size:13px">HĐĐT số ' + h(d.custom_hddt_so) + (d.custom_hddt_trang_thai ? ' (' + h(d.custom_hddt_trang_thai) + ')' : '') + '</div>' : '') +
    '</div>';
  /* Don cua ngay cu ma con nhap: luat ke toan bat xuat hoa don dien tu ngay
     trong ngay ban, nen don hom qua co truc trac thi phai keo sang hom nay
     roi moi ghi so duoc (chi Dung 12/08/2026). Chi quan ly va ke toan thay
     nut nay, va phai co ma OTP. */
  var laCu = d.docstatus === 0 && !d.custom_hddt_so && String(d.posting_date || '') < today();
  if (laCu) {
    html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fcd34d">' +
      '<div style="font-size:13px;color:#92400e;line-height:1.6">Đơn này còn nháp và mang ngày <b>' +
      (vn.length === 3 ? vn[2] + '/' + vn[1] + '/' + vn[0] : h(d.posting_date)) + '</b>. ' +
      'Luật kế toán bắt xuất hoá đơn điện tử ngay trong ngày bán, nên đơn cũ ghi sổ xong vẫn không xuất được hoá đơn mang ngày cũ. ' +
      'Chuyển sang hôm nay rồi ghi sổ thì hoá đơn điện tử mang đúng ngày xuất.</div>' +
      '<button class="btn" id="dsvDoiNgay" style="margin-top:10px">📅 Chuyển đơn sang hôm nay (' + posNgayVn(today()) + ')</button></div>';
  }
  html += '<div class="sec">Món trong đơn</div><div class="card" style="padding:6px 14px">';
  (d.items || []).forEach(function (r) {
    html += '<div style="display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
      '<div style="flex:1;min-width:0">' + h(r.item_name) + '<div style="color:#a0a6b4;font-size:12px">' + money(r.qty) + ' x ' + money(r.rate) + ' đ</div></div>' +
      '<b style="white-space:nowrap">' + money(r.amount) + '</b></div>';
  });
  if (d.discount_amount) html += '<div style="display:flex;justify-content:space-between;padding:8px 0;color:#b3261e"><span>Giảm giá</span><b>-' + money(d.discount_amount) + '</b></div>';
  html += '<div style="display:flex;justify-content:space-between;padding:10px 0;font-size:16px"><b>Tổng tiền</b><b>' + money(d.grand_total) + ' đ</b></div></div>';
  await cfgBanHang();
  var PTDS = ptTheoNguon(d.custom_nguon || 'Pancake');
  html += '<div style="padding:8px 0 2px"><div style="font-size:12px;color:#6b7280;margin-bottom:6px">Phương thức thanh toán' + (d.vgb_pt_thanh_toan ? '' : ' - <b style="color:#b45309">chưa rõ, chọn giúp trước khi ghi sổ</b>') + '</div><div id="dsvPt" style="display:flex;gap:6px;flex-wrap:wrap">' + PTDS.map(function (p) { var on = p.v === d.vgb_pt_thanh_toan; return '<button class="ptc" data-pt="' + p.v + '" style="display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:8px;font-size:13px;border:1.5px solid ' + (on ? '#0d9488;background:#ccfbf1;color:#0f766e;font-weight:bold' : '#e5e7eb;background:#fff;color:#374151') + '">' + (p.lg ? '<img src="' + p.lg + '" style="height:18px;border-radius:3px">' : '🏦 ') + p.v + '</button>'; }).join('') + '</div></div>';
  /* Khach chuyen khoan cho don ben Sales cung phai co ma QR nhu ben quay.
     Truoc day man nay chi co o go ma tham chieu, nen diem Sales chon nguon
     Tai cho hoac Mang ve roi chon Chuyen khoan la khong sinh duoc QR - thu
     ngan phai mo app ngan hang go tay (anh Viet 12/08/2026). */
  html += '<div id="dsvQr" style="margin-top:10px"></div>';
    html += '<div style="border:1.5px solid #e5e7eb;border-radius:10px;padding:10px;margin-top:10px">'
    + '<div id="dsvMtcNhan" style="font-size:12px;color:#6b7280;margin-bottom:6px"></div>'
    + '<input id="dsvMtc" placeholder="Mã tham chiếu" value="' + xesc(d.vgb_ma_tham_chieu) + '" style="width:100%;box-sizing:border-box;padding:9px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:14px;font-family:inherit">'
    + '<div style="font-size:12px;color:#6b7280;margin-top:8px">Đối soát thanh toán: '
    + (d.vgb_ghi_chu_doi_soat ? xesc(d.vgb_ghi_chu_doi_soat) : '<span style="color:#9ca3af">chưa có, chờ máy đối soát</span>')
    + '</div></div>';
  html += '<div id="dsvSepay" style="border:1.5px solid #e5e7eb;border-radius:10px;padding:10px;margin-top:10px;font-size:13px;color:#6b7280">Đang tìm giao dịch SePay của đơn này...</div>';
  /* Khach cong no: ban chiu thi phai biet no cua AI. O nay hien mo ma
     bat buoc khi chon phuong thuc Cong no (anh Viet 12/08/2026 - don
     91513 cua OSHIMA ghi cong no ma khong gan duoc khach nen man Cong no
     phai thu khong thay ten). */
  html += '<div id="dsvKhachBox" style="border:1.5px solid #e5e7eb;border-radius:10px;padding:10px;margin-top:10px"></div>';
  var XHD_MD = 'Bán cho người tiêu dùng';
  function xesc(t) { return String(t == null ? '' : t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  var xhdCty = (d.vgb_xhd_ten && d.vgb_xhd_ten !== XHD_MD) ? d.vgb_xhd_ten : '';
  var xhdLoai = (d.vgb_xhd_mst || xhdCty) ? 'cong_ty' : 'ca_nhan';
  var xin = 'width:100%;box-sizing:border-box;padding:9px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:14px;font-family:inherit';
  html += '<div style="border:1.5px solid #e5e7eb;border-radius:10px;padding:10px;margin-top:10px">'
    + '<div style="font-size:12px;color:#6b7280;margin-bottom:8px"><b>Tên khách xuất hoá đơn</b></div>'
    + '<div id="xhdChon" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">'
    + '<button class="xhdc" data-loai="ca_nhan" style="padding:6px 10px;border-radius:8px;font-size:13px">Bán cho người tiêu dùng</button>'
    + '<button class="xhdc" data-loai="cong_ty" style="padding:6px 10px;border-radius:8px;font-size:13px">Xuất cho công ty</button>'
    + '</div>'
    + '<div id="xhdForm" style="display:none;flex-direction:column;gap:6px">'
    + '<input id="xhdMst" placeholder="Mã số thuế - chi nhánh nhớ gõ cả dấu gạch, vd 0311638525-027" value="' + xesc(d.vgb_xhd_mst) + '" style="' + xin + '">'
    + '<input id="xhdTen" placeholder="Tên pháp nhân trên hoá đơn" value="' + xesc(xhdCty) + '" style="' + xin + '">'
    + '<textarea id="xhdDc" rows="2" placeholder="Địa chỉ trên hoá đơn" style="' + xin + '">' + xesc(d.vgb_xhd_dia_chi) + '</textarea>'
    + '<input id="xhdEmail" placeholder="Email nhận hoá đơn" value="' + xesc(d.vgb_xhd_email) + '" style="' + xin + '">'
    + '<div id="xhdBao" style="font-size:12px;color:#6b7280"></div>'
    + '</div>'
    + (d.custom_hddt_so ? '<div style="font-size:12px;color:#0f766e">Đã xuất HĐĐT số ' + xesc(d.custom_hddt_so) + ' nên không sửa được nữa.</div>' : '<button class="btn" id="xhdLuu" style="margin-top:8px">Lưu thông tin đơn</button>')
    + '<div style="font-size:11px;color:#9ca3af;margin-top:8px">Luật kế toán hiện hành: mỗi đơn hàng là một hoá đơn VAT riêng, không được gộp đơn.</div>'
    + '</div>';
  var foot = '';
  if (d.docstatus === 0) foot = '<button class="btn" id="dsvChot">Ghi sổ hoá đơn bán hàng</button>';
  else if (can && !d.custom_hddt_so) foot = '<button class="btn" id="dsvHddt">Xuất HĐĐT (Chờ ký)</button>';
  frame('Chi tiết đơn', html, foot ? { footer: foot } : {});
  var DSV_PT = d.vgb_pt_thanh_toan || '';
  var ptWrap = document.getElementById('dsvPt');
  if (ptWrap) ptWrap.querySelectorAll('.ptc').forEach(function (b) {
    b.onclick = function () {
      DSV_PT = b.getAttribute('data-pt');
      ptWrap.querySelectorAll('.ptc').forEach(function (x) {
        var on = x.getAttribute('data-pt') === DSV_PT;
        x.style.border = '1.5px solid ' + (on ? '#0d9488' : '#e5e7eb');
        x.style.background = on ? '#ccfbf1' : '#fff';
        x.style.color = on ? '#0f766e' : '#374151';
        x.style.fontWeight = on ? 'bold' : 'normal';
      });
    };
  });
    if (ptWrap) ptWrap.addEventListener('click', function () { setTimeout(function () { veOMtc(DSV_PT, 'dsvMtc', 'dsvMtcNhan'); veKhachNo(); dsvVeQr(); }, 0); });
  veOMtc(DSV_PT, 'dsvMtc', 'dsvMtcNhan');

  /* Ma diem ban cua nguon don nay, de noi dung chuyen khoan mang ma diem -
     ke toan doc sao ke la biet ngay tien cua noi nao. */
  var dsvDiem = (nguonBH(d.custom_nguon) || {}).diem || d.vgb_quay || '';
  var dsvNoiDung = posNoiDungCk(d.name, dsvDiem);
  function dsvVeQr() {
    var o = document.getElementById('dsvQr');
    if (!o) return;
    if (DSV_PT !== 'Chuyển khoản') { o.innerHTML = ''; return; }
    var tien = d.grand_total || 0;
    var url = posQrUrl(dsvNoiDung, tien, d.custom_nguon || '');
    if (!url) {
      o.innerHTML = '<div style="border:1.5px solid #fecaca;background:#fef2f2;border-radius:10px;padding:12px;font-size:13px;color:#b3261e;line-height:1.6">' +
        'Chưa khai số tài khoản nhận chuyển khoản nên chưa sinh được mã QR. Vào Cài đặt · Tài khoản nhận tiền để khai.</div>';
      return;
    }
    var tk = posTaiKhoan(d.custom_nguon || '');
    o.innerHTML = '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:12px;text-align:center;background:#fff">' +
      '<div style="font-size:12.5px;color:#6b7280">Khách quét mã này, máy tự điền số tiền và nội dung</div>' +
      '<img src="' + url + '" alt="Mã QR chuyển khoản" style="width:min(240px,62vw);aspect-ratio:1;margin:10px auto 6px;display:block;border-radius:10px;background:#fff">' +
      '<div style="font-size:18px;font-weight:800;color:#0f766e">' + money(tien) + ' đ</div>' +
      '<div style="font-size:13px;color:#374151;margin-top:2px">Nội dung: <b>' + h(dsvNoiDung) + '</b></div>' +
      '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' + h(tk.ten || '') + ' · ' + h((tk.bank || '') + ' ' + (tk.stk || '')) +
      (tk.rieng ? ' · tài khoản riêng của nguồn này' : '') + '</div></div>';
  }
  dsvVeQr();

  /* --- khach cong no --- */
  var KHACH_LE_TEN = 'Khách lẻ';
  var dsvKhach = { ma: d.vgb_khach_no || '', ten: '' };
  if (!dsvKhach.ma && d.customer && String(d.customer).indexOf(KHACH_LE_TEN) !== 0) {
    dsvKhach = { ma: d.customer, ten: d.customer_name || d.customer };
  } else if (dsvKhach.ma) {
    dsvKhach.ten = d.vgb_khach_no;
  }
  function veKhachNo() {
    var box = document.getElementById('dsvKhachBox');
    if (!box) return;
    var canNo = DSV_PT === 'Công nợ';
    box.style.borderColor = canNo && !dsvKhach.ma ? '#fcd34d' : '#e5e7eb';
    box.style.background = canNo && !dsvKhach.ma ? '#fffbeb' : '#fff';
    box.innerHTML = '<div style="font-size:12px;color:#6b7280;margin-bottom:8px"><b>Khách công nợ</b>' +
      (canNo ? ' <span style="color:#b45309">- bắt buộc với đơn bán chịu</span>'
             : ' <span style="color:#9ca3af">- không bắt buộc</span>') + '</div>' +
      (dsvKhach.ma
        ? '<div style="display:flex;align-items:center;gap:8px"><span style="font-size:17px">🏢</span>' +
          '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(dsvKhach.ten || dsvKhach.ma) + '</b>' +
          '<div style="font-size:11.5px;color:#6b7280">mã ' + h(dsvKhach.ma) + '</div></div>' +
          '<button id="dsvKhachBo" style="border:0;background:transparent;color:#b3261e;font-size:17px;cursor:pointer">✕</button></div>'
        : '<button class="btn gh" id="dsvKhachChon" style="margin:0">📒 Chọn khách công nợ</button>') +
      (d.docstatus === 1
        ? '<div style="font-size:11px;color:#9ca3af;margin-top:8px">Đơn đã ghi sổ nên chỉ gắn được tên chủ nợ cho màn Công nợ phải thu, bút toán trên sổ cái giữ nguyên.</div>'
        : '');
    var nChon = document.getElementById('dsvKhachChon');
    if (nChon) nChon.onclick = function () {
      sheetTimKhach('Chọn khách công nợ', async function (x) {
        dsvKhach = { ma: x.name, ten: x.customer_name || x.name };
        veKhachNo();
        if (d.docstatus === 1) {
          try { await api('vagabond.ban_hang.luu_khach_no', { si_name: d.name, khach: x.name }); toast('Đã gắn ' + dsvKhach.ten); }
          catch (e) { toast((e && e.message) || 'Không gắn được'); }
        }
      });
    };
    var nBo = document.getElementById('dsvKhachBo');
    if (nBo) nBo.onclick = function () { dsvKhach = { ma: '', ten: '' }; veKhachNo(); };
  }
  veKhachNo();
  function mtcGiaTri() { var o = document.getElementById('dsvMtc'); return o ? o.value : ''; }
  function xhdVe() {
    var ch = document.getElementById('xhdChon');
    if (!ch) return;
    ch.querySelectorAll('.xhdc').forEach(function (b) {
      var on = b.getAttribute('data-loai') === xhdLoai;
      b.style.border = '1.5px solid ' + (on ? '#0d9488' : '#e5e7eb');
      b.style.background = on ? '#ccfbf1' : '#fff';
      b.style.color = on ? '#0f766e' : '#374151';
      b.style.fontWeight = on ? 'bold' : 'normal';
    });
    var f = document.getElementById('xhdForm');
    if (f) f.style.display = xhdLoai === 'cong_ty' ? 'flex' : 'none';
  }
  var xhdCh = document.getElementById('xhdChon');
  if (xhdCh) {
    xhdCh.querySelectorAll('.xhdc').forEach(function (b) {
      b.onclick = function () { xhdLoai = b.getAttribute('data-loai'); xhdVe(); };
    });
    xhdVe();
  }
  var xmst = document.getElementById('xhdMst');
  if (xmst) xmst.onblur = async function () {
    var so = (xmst.value || '').replace(/[^0-9]/g, '');
    var bao = document.getElementById('xhdBao');
    if (so.length !== 10 && so.length !== 13) { if (bao) bao.textContent = so ? 'Mã số thuế phải 10 hoặc 13 số.' : ''; return; }
    if (bao) bao.textContent = 'Đang tra mã số thuế...';
    try {
      var kq = await api('vagabond.api.tra_mst', { mst: so });
      var t = document.getElementById('xhdTen'), dc = document.getElementById('xhdDc');
      if (kq && kq.ok) {
        if (t && !t.value.trim()) t.value = kq.ten || '';
        if (dc && !dc.value.trim()) dc.value = kq.dia_chi || '';
        if (bao) bao.textContent = 'Tra được: ' + (kq.ten || '');
      } else if (bao) bao.textContent = 'Không tra được mã này, điền tay giúp em.';
    } catch (e) { if (bao) bao.textContent = 'Không tra được mã này, điền tay giúp em.'; }
  };
  async function luuXhd(ten_si) {
    if (d.custom_hddt_so) return;
    if (xhdLoai !== 'cong_ty') { await api('vagabond.ban_hang.luu_xhd', { si_name: ten_si, ten: XHD_MD }); return; }
    var mst = ((document.getElementById('xhdMst') || {}).value || '').replace(/[^0-9]/g, '');
    var ten = ((document.getElementById('xhdTen') || {}).value || '').trim();
    if (!mst || !ten) throw new Error('Xuất cho công ty thì phải có mã số thuế và tên pháp nhân.');
    await api('vagabond.ban_hang.luu_xhd', { si_name: ten_si, ten: ten, mst: mst, dia_chi: ((document.getElementById('xhdDc') || {}).value || ''), email: ((document.getElementById('xhdEmail') || {}).value || '') });
  }
  var xlu = document.getElementById('xhdLuu');
  if (xlu) xlu.onclick = async function () {
    busy(true);
    try { await api('vagabond.ban_hang.luu_thanh_toan', { si_name: d.name, pt: DSV_PT, ma_tham_chieu: mtcGiaTri() }); await luuXhd(d.name); busy(false); toast('Đã lưu thông tin đơn'); }
    catch (e) { busy(false); window.alert((e && e.message) || 'Lưu lỗi'); }
  };
  (async function () {
    var o = document.getElementById('dsvSepay');
    if (!o) return;
    try {
      var kq = await api('vgb_gd_sepay', { phieu: d.name });
      var ds = (kq && kq.giao_dich) || [];
      var tieu = '<div style="font-size:12px;color:#6b7280;margin-bottom:6px"><b>Giao dịch SePay khớp theo mã đơn</b></div>';
      if (!ds.length) {
        o.innerHTML = tieu + '<div style="color:#9ca3af">Chưa nhận được chuyển khoản nào mang mã đơn này.</div>';
        return;
      }
      var dong = ds.map(function (g) {
        var vn = String(g.ngay || '').split('-');
        var ng = vn.length === 3 ? vn[2] + '/' + vn[1] : g.ngay;
        return '<div style="display:flex;justify-content:space-between;gap:8px;padding:5px 0;border-top:1px solid #f1f5f9">'
          + '<span style="color:#374151">' + ng + ' · ' + xesc(g.ma_tham_chieu || g.ma_gd) + '</span>'
          + '<b style="white-space:nowrap;color:#166534">' + Number(g.so_tien || 0).toLocaleString('vi-VN') + ' đ</b></div>';
      }).join('');
      var du = kq.du_tien ? '<span style="color:#166534;font-weight:700">Đủ tiền</span>'
        : '<span style="color:#b45309;font-weight:700">Thiếu ' + Number((kq.tien_phieu || 0) - (kq.tong_da_nhan || 0)).toLocaleString('vi-VN') + ' đ</span>';
      o.innerHTML = tieu + dong
        + '<div style="display:flex;justify-content:space-between;padding-top:6px;border-top:1.5px solid #e5e7eb;margin-top:4px">'
        + '<span>Đã nhận ' + Number(kq.tong_da_nhan || 0).toLocaleString('vi-VN') + ' đ / đơn ' + Number(kq.tien_phieu || 0).toLocaleString('vi-VN') + ' đ</span>' + du + '</div>';
    } catch (e) {
      o.innerHTML = '<div style="color:#9ca3af;font-size:12px">Chưa tra được giao dịch SePay.</div>';
    }
  })();
  var cDn = document.getElementById('dsvDoiNgay');
  if (cDn) cDn.onclick = async function () {
    var ok = await confirmSheet(
      'Chuyển đơn sang hôm nay',
      'Đơn #' + (d.custom_pancake_display_id || d.name) + ' đang mang ngày ' + d.posting_date +
      '.\nChuyển sang ' + today() + ' để hoá đơn điện tử xuất đúng ngày theo luật thuế.\n\n' +
      'Doanh thu của đơn sẽ tính vào ngày mới, không còn nằm ở ngày cũ.',
      'Chuyển sang hôm nay');
    if (!ok) return;
    var otp = await promptSheet('Đổi ngày hoá đơn cần mã OTP của quản lý', 'Nhập 6 số quản lý đọc cho');
    if (otp === null) return;
    busy(true);
    try {
      await api('vagabond.ban_hang.doi_ngay_hoa_don', { si_name: d.name, otp: (otp || '').replace(/\D/g, ''), ly_do: 'sửa đơn trục trặc' });
      busy(false);
      toast('Đã chuyển đơn sang ' + posNgayVn(today()));
      dsNgay = today();
      go(scrDoanhSo, true);
    } catch (e) { busy(false); window.alert((e && e.message) || 'Không đổi được ngày'); }
  };
  var c1 = document.getElementById('dsvChot');
  if (c1) c1.onclick = async function () {
    if (!DSV_PT && !window.confirm('Chưa chọn phương thức thanh toán. Vẫn ghi sổ chứ?')) return;
    if (DSV_PT === 'Công nợ' && !dsvKhach.ma) {
      return window.alert('Đơn bán công nợ phải chọn khách công nợ, không thì cuối tháng không biết đòi ai.');
    }
    if (!window.confirm('Ghi sổ hoá đơn cho đơn #' + (d.custom_pancake_display_id || '') + '? Số sẽ vào doanh thu chính thức.')) return;
    busy(true);
    try { await luuXhd(d.name); await api('vagabond.ban_hang.chot_mot_don', { si_name: d.name, pt: DSV_PT, ma_tham_chieu: mtcGiaTri(), khach: dsvKhach.ma || '' }); busy(false); toast('Đã ghi sổ ' + d.name); }
    catch (e) { busy(false); window.alert((e && e.message) || 'Chốt lỗi'); }
    go(scrDoanhSo, true);
  };
  var c2 = document.getElementById('dsvHddt');
  if (c2) c2.onclick = async function () {
    if (!window.confirm('Xuất hoá đơn điện tử (Chờ ký) cho đơn này?')) return;
    busy(true);
    try { var kq = await api('vagabond.ban_hang.xuat_hoa_don_dien_tu', { si_name: d.name }); busy(false); toast('Đã tạo HĐĐT Chờ ký' + (kq && kq.inv_invoiceNumber ? ', số ' + kq.inv_invoiceNumber : '')); }
    catch (e) { busy(false); window.alert((e && e.message) || 'Xuất HĐĐT lỗi'); }
    go(scrDoanhSo, true);
  };
}
function dstSoThuan(v) {
  return String(v == null ? '' : v).replace(/[^0-9]/g, '');
}
function dstNganCach(v) {
  var t = dstSoThuan(v);
  return t ? t.replace(/\B(?=(\d{3})+(?!\d))/g, '.') : '';
}
function dstGanNganCach() {
  ['dstGiam', 'dstShip'].forEach(function (id) {
    var el = document.getElementById(id);
    if (!el || el.dataset.ngan) return;
    el.dataset.ngan = '1';
    el.addEventListener('input', function () { el.value = dstNganCach(el.value); });
  });
}
var dsTay = null, dsItemsCache = null;
function dsTayDoc() {
  if (!dsTay) return;
  var g = function (id) { var el = document.getElementById(id); return el ? el.value : ''; };
  dsTay.ma = g('dstMa'); dsTay.ten = g('dstTen'); dsTay.sdt = g('dstSdt'); dsTay.giam = dstSoThuan(g('dstGiam')); dsTay.ship = dstSoThuan(g('dstShip')); dsTay.mtc = g('dstMtc');
}
async function scrDsNhapTay() {
  await cfgBanHang();
  /* Ma bill sinh ngay luc mo man, giong hetben quay: co ma thi moi sinh
     duoc QR cho khach quet TRUOC khi luu don, va luu xong thi chinh ma nay
     di vao o ma tham chieu de SePay doi soat (anh Viet 12/08/2026). */
  if (!dsTay) dsTay = { nguon: 'GrabFood', bill: posMaBill(), ma: '', ten: '', sdt: '', giam: '', ship: '', pt: '', mtc: '', mon: [] };
  if (!dsTay.bill) dsTay.bill = posMaBill();
  var dsPt = ptTheoNguon(dsTay.nguon);
  if (dsPt.length === 1) dsTay.pt = dsPt[0].v;
  if (dsTay.pt && !dsPt.some(function (p) { return p.v === dsTay.pt; })) dsTay.pt = dsPt.length === 1 ? dsPt[0].v : '';
  var tong = dsTay.mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0);
  var html = '<div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    '<div class="hub" data-t="nguon" style="padding:10px 0;border:none"><div class="ht"><div class="h2">Nguồn đơn</div><div class="h1">' + h(dsTay.nguon) + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    '<input class="tin" id="dstMa" placeholder="Mã đơn bên app (vd GF-123 hoặc số HĐ Fabi)" value="' + h(dsTay.ma) + '">' +
    '<input class="tin" id="dstTen" placeholder="Tên khách" value="' + h(dsTay.ten) + '">' +
    '<input class="tin" id="dstSdt" placeholder="Số điện thoại (không bắt buộc)" inputmode="tel" value="' + h(dsTay.sdt) + '">' +
    '</div>';
  html += '<div class="sec">Phương thức thanh toán</div><div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    (dsPt.length > 1
      ? '<div id="dstPt" style="display:flex;gap:6px;flex-wrap:wrap">' + chipPt(dsPt, dsTay.pt) + '</div>'
      : '<div style="font-size:13px;color:#6b7280">Đơn ' + h(dsTay.nguon) + ' chỉ có một phương thức: <b>' + h(dsPt.length ? dsPt[0].v : '') + '</b></div>') +
    '<div><div id="dstMtcNhan" style="font-size:12px;color:#6b7280;margin-bottom:6px"></div>' +
    '<input class="tin" id="dstMtc" placeholder="Mã tham chiếu" value="' + h(dsTay.mtc || '') + '"></div>' +
    '<div id="dstQr"></div>' +
    '</div>';
  html += '<div class="sec">Món trong đơn</div><div class="card" style="padding:6px 14px">';
  if (!dsTay.mon.length) html += '<div style="padding:14px 0;color:#a0a6b4">Chưa có món nào, bấm Thêm món.</div>';
  dsTay.mon.forEach(function (m, i) {
    /* Co anh mon thi nhin phat ra ngay, khong phai doc ten dai (anh Viet
       12/08/2026: "mon khi chon xong bi thieu hinh anh, kho nhan biet"). */
    html += '<div style="display:flex;flex-direction:row;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
      (m.anh
        ? '<img src="' + h(m.anh) + '" style="width:42px;height:42px;flex:none;border-radius:9px;object-fit:cover;background:#f2f4f7" onerror="this.style.visibility=\'hidden\'">'
        : '<div style="width:42px;height:42px;flex:none;border-radius:9px;background:#f2f4f7;display:flex;align-items:center;justify-content:center;font-size:19px">🎂</div>') +
      '<div style="flex:1;min-width:0">' + h(m.ten) + '<div style="color:#a0a6b4;font-size:12px">' + money(m.qty) + ' x ' + money(m.rate) + ' đ</div></div>' +
      '<b>' + money(m.qty * m.rate) + '</b><button class="ic" data-x="' + i + '" style="color:#b3261e">✕</button></div>';
  });
  html += '<div style="padding:10px 0"><button class="btn gh" id="dstThem" style="width:100%">➕ Thêm món</button></div></div>';
  html += '<div class="sec">Giảm giá và phí giao</div><div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    '<input class="tin" id="dstGiam" placeholder="Giảm giá cả đơn (đ), vd chiết khấu Grab" inputmode="numeric" value="' + h(dstNganCach(dsTay.giam)) + '">' +
    '<input class="tin" id="dstShip" placeholder="Phí giao thu của khách (đ), để trống nếu không" inputmode="numeric" value="' + h(dstNganCach(dsTay.ship)) + '">' +
    '</div>';
  html += '<div style="text-align:right;padding:6px 14px;color:#6b7280">Tạm tính: <b>' + money(tong) + ' đ</b> (chưa trừ giảm, chưa cộng ship)</div>';
  var b = frame('Nhập đơn tay', html, { footer: '<button class="btn" id="dstLuu">Lưu đơn nháp vào ngày ' + dsNgay.split('-').reverse().join('/') + '</button>' });
  dstGanNganCach();
  b.addEventListener('click', function (e) {
    if (e.target.closest('[data-t="nguon"]')) {
      dsTayDoc();
      return sheet('Nguồn đơn', ((CFGBH || {}).nguon || []).map(function (n) { return { value: n.v, label: n.v, icon: n.ic || '', img: n.lg || '' }; }), dsTay.nguon, function (o) { dsTay.nguon = o.value; go(scrDsNhapTay, true); });
    }
    var x = e.target.closest('[data-x]');
    if (x) { dsTayDoc(); dsTay.mon.splice(parseInt(x.getAttribute('data-x'), 10), 1); go(scrDsNhapTay, true); }
  });
  /* Ma QR cho don nhap tay. Noi dung mang ma diem ban cua nguon don, cong
     ma bill sinh san - de ke toan doc sao ke la biet tien cua noi nao, va
     SePay tu khop duoc vao dung don sau khi luu. */
  function dstVeQr() {
    var o = document.getElementById('dstQr');
    if (!o) return;
    if (dsTay.pt !== 'Chuyển khoản') { o.innerHTML = ''; return; }
    var giam = parseFloat(dsTay.giam || 0) || 0, ship = parseFloat(dsTay.ship || 0) || 0;
    var thu = dsTay.mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0) - giam + ship;
    var diem = (nguonBH(dsTay.nguon) || {}).diem || '';
    var nd = posNoiDungCk(dsTay.bill, diem);
    var url = posQrUrl(nd, thu, dsTay.nguon);
    if (!url) {
      o.innerHTML = '<div style="border:1.5px solid #fecaca;background:#fef2f2;border-radius:10px;padding:12px;font-size:13px;color:#b3261e;line-height:1.6">' +
        'Chưa khai số tài khoản nhận chuyển khoản nên chưa sinh được mã QR. Vào Cài đặt · Tài khoản nhận tiền để khai.</div>';
      return;
    }
    var tk = posTaiKhoan(dsTay.nguon);
    o.innerHTML = '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:12px;text-align:center;background:#fff">' +
      '<div style="font-size:12.5px;color:#6b7280">Khách quét mã này, máy tự điền số tiền và nội dung</div>' +
      '<img src="' + url + '" alt="Mã QR chuyển khoản" style="width:min(230px,60vw);aspect-ratio:1;margin:10px auto 6px;display:block;border-radius:10px;background:#fff">' +
      '<div style="font-size:18px;font-weight:800;color:#0f766e">' + money(thu) + ' đ</div>' +
      '<div style="font-size:13px;color:#374151;margin-top:2px">Nội dung: <b>' + h(nd) + '</b></div>' +
      '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' + h(tk.ten || '') + ' · ' + h((tk.bank || '') + ' ' + (tk.stk || '')) +
      (tk.rieng ? ' · tài khoản riêng của nguồn này' : '') + '</div>' +
      '<div style="font-size:11.5px;color:#98a2b3;margin-top:6px;line-height:1.5">Số tiền trên mã đã trừ giảm giá và cộng phí giao. Sửa món hay giảm giá thì mã tự vẽ lại.</div></div>';
  }

  function dstVeMtc() {
    var q = quyPt(dsTay.pt) || {};
    var oMtc = document.getElementById('dstMtc');
    var oMa = document.getElementById('dstMa');
    var boc = oMtc ? oMtc.parentElement : null;
    if (dsPt.length === 1) {
      // Don san: ma don ben app CHINH LA ma tham chieu, chi nhap mot lan.
      if (boc) boc.style.display = 'none';
      if (oMa) oMa.placeholder = (q.nhan || 'Mã đơn bên app') + (q.vd ? ' - vd ' + q.vd : '');
    } else {
      if (boc) boc.style.display = '';
      if (oMa) oMa.placeholder = 'Số phiếu nội bộ (không bắt buộc)';
      veOMtc(dsTay.pt, 'dstMtc', 'dstMtcNhan');
    }
  }
  var ptw = document.getElementById('dstPt');
  if (ptw) ptw.querySelectorAll('.ptc').forEach(function (b) {
    b.onclick = function () {
      dsTayDoc();
      dsTay.pt = b.getAttribute('data-pt');
      veChipPt(ptw, dsTay.pt);
      dstVeMtc();
      dstVeQr();
    };
  });
  dstVeMtc();
  dstVeQr();
  /* Sua so tien la mo QR phai doi theo, khong thi khach quet ra so cu. */
  ['dstGiam', 'dstShip'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('input', function () { dsTayDoc(); dstVeQr(); });
  });
  document.getElementById('dstThem').onclick = dsTayThemMon;
  document.getElementById('dstLuu').onclick = dsTayLuu;
}
function themMonSheet(o, giaGoi) {
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  var g0 = parseFloat(giaGoi || 0) || 0;
  box.innerHTML = '<div class="shh"><b>Thêm món</b><div class="x">&times;</div></div>' +
    '<div style="padding:12px 14px calc(env(safe-area-inset-bottom,0px) + 14px);display:grid;gap:14px">' +
    '<div style="display:flex;gap:10px;align-items:center">' +
      (o.img ? '<img src="' + o.img + '" style="width:52px;height:52px;object-fit:cover;border-radius:10px;border:1px solid #e5e7eb">' : '<span style="font-size:34px">🎂</span>') +
      '<div style="flex:1;min-width:0"><b>' + h(o.label) + '</b><div style="color:#a0a6b4;font-size:12px">' + h(o.value) + '</div></div></div>' +
    '<div><div style="font-size:12px;color:#6b7280;margin-bottom:6px">Giá bán 1 đơn vị (đ)</div>' +
      '<input class="nt" id="tmGia" inputmode="numeric" value="' + (g0 ? money(g0) : '') + '" placeholder="0" style="height:48px;padding:0 12px;width:100%;box-sizing:border-box;text-align:right;font-size:18px;font-weight:bold"></div>' +
    '<div><div style="font-size:12px;color:#6b7280;margin-bottom:6px">Số lượng</div>' +
      '<div style="display:flex;gap:10px;align-items:center">' +
      '<button class="nt" id="tmTru" style="height:54px;width:58px;flex:none;font-size:26px;cursor:pointer">&minus;</button>' +
      '<input class="nt" id="tmSl" inputmode="decimal" value="1" style="height:54px;flex:1;text-align:center;font-size:22px;font-weight:bold;padding:0">' +
      '<button class="nt" id="tmCong" style="height:54px;width:58px;flex:none;font-size:26px;cursor:pointer">+</button></div></div>' +
    '<div style="display:flex;justify-content:space-between;align-items:center;font-size:16px"><span style="color:#5a6070">Tạm tính</span><b id="tmTong">0 đ</b></div>' +
    '<button class="btn" id="tmOk">Thêm vào đơn</button></div>';
  ov.appendChild(box); document.body.appendChild(ov);
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  var oGia = box.querySelector('#tmGia'), oSl = box.querySelector('#tmSl'), oTong = box.querySelector('#tmTong');
  // Tien Viet dung dau cham lam phan cach nghin: o TIEN phai bo sach dau cham,
  // chi o SO LUONG moi cho phep dau thap phan.
  function soGia(el) { return parseFloat(String(el.value || '').replace(/[^0-9]/g, '')) || 0; }
  function soSl(el) { return parseFloat(String(el.value || '').replace(/,/g, '.').replace(/[^0-9.]/g, '')) || 0; }
  function ve() { oTong.textContent = money(soGia(oGia) * soSl(oSl)) + ' đ'; }
  oGia.oninput = ve; oSl.oninput = ve; ve();
  box.querySelector('#tmTru').onclick = function () { oSl.value = Math.max(1, soSl(oSl) - 1); ve(); };
  box.querySelector('#tmCong').onclick = function () { oSl.value = soSl(oSl) + 1; ve(); };
  oGia.onblur = function () { var g = soGia(oGia); oGia.value = g ? money(g) : ''; ve(); };
  box.querySelector('#tmOk').onclick = function () {
    var sl = soSl(oSl), gia = soGia(oGia);
    if (sl <= 0) return toast('Số lượng phải lớn hơn 0');
    dong();
    dsTay.mon.push({ item_code: o.value, ten: o.label, qty: sl, rate: gia, anh: o.img || '' });
    go(scrDsNhapTay, true);
  };
  setTimeout(function () { oSl.focus(); oSl.select(); }, 60);
}
async function dsTayThemMon() {
  dsTayDoc();
  if (!dsItemsCache) {
    busy(true);
    try { dsItemsCache = await getList('Item', { filters: { is_sales_item: 1, disabled: 0, item_group: ['not in', ['Nguyên vật liệu Thô', 'Bán thành phẩm Bánh', 'Bán thành phẩm Nước', 'Nhân bán thành phẩm', 'Công cụ Dụng cụ', 'Bao bì', 'Văn phòng phẩm', 'Tài sản Cố định']] }, fields: ['name', 'item_name', 'image', 'standard_rate'], limit_page_length: 0, order_by: 'item_name' });
      try {
        var dsBC = await getList('Item Barcode', { parent: 'Item', fields: ['parent', 'barcode'], limit_page_length: 0 });
        var dsBCM = {};
        (dsBC || []).forEach(function (b) { dsBCM[b.parent] = (dsBCM[b.parent] ? dsBCM[b.parent] + ' ' : '') + b.barcode; });
        dsItemsCache.forEach(function (x) { x.ma_vach = dsBCM[x.name] || ''; });
      } catch (e2) { /* khong co quyen doc barcode thi thoi, van tim duoc theo ma */ } }
    catch (e) { busy(false); return window.alert('Không tải được danh mục món'); }
    busy(false);
  }
  sheet('Chọn món', dsItemsCache.map(function (x) { return { value: x.name, label: x.item_name, icon: '🎂', img: x.image || '', gia: x.standard_rate || 0, phu: (x.standard_rate ? money(x.standard_rate) + ' đ' : 'chưa có giá') + ' · ' + x.name, tim: x.name + ' ' + (x.ma_vach || '') }; }), null, function (o) {
    return themMonSheet(o, o.gia);
    dsTay.mon.push({ item_code: o.value, ten: o.label, qty: sl, rate: gia });
    go(scrDsNhapTay, true);
  }, true);
}
async function dsTayLuu() {
  dsTayDoc();
  if (!dsTay.mon.length) return window.alert('Đơn chưa có món nào.');
  var giam = parseFloat(dsTay.giam || 0) || 0, ship = parseFloat(dsTay.ship || 0) || 0;
  var tong = dsTay.mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0) - giam + ship;
  if (!window.confirm('Lưu đơn ' + h(dsTay.nguon) + (dsTay.ma ? ' #' + dsTay.ma : '') + ', tổng ' + money(tong) + ' đ vào doanh thu ngày ' + dsNgay.split('-').reverse().join('/') + '?')) return;
  busy(true);
  try {
    await api('vagabond.ban_hang.tao_don_tay', {
      ngay: dsNgay, nguon: dsTay.nguon, ma_don: dsTay.ma, ten_khach: dsTay.ten, dien_thoai: dsTay.sdt,
      /* Chuyen khoan ma thu ngan khong go gi thi lay chinh ma bill in tren
         QR lam ma tham chieu, de SePay doi soat dung to khach da chuyen. */
      pt: dsTay.pt || '',
      ma_tham_chieu: (dsTay.mtc || '').trim() || (dsTay.pt === 'Chuyển khoản' ? dsTay.bill : ''),
      items: JSON.stringify(dsTay.mon.map(function (m) { return { item_code: m.item_code, qty: m.qty, rate: m.rate }; })),
      giam_gia: giam, phi_ship: ship
    });
    busy(false); toast('Đã lưu đơn nháp'); dsTay = null;
  } catch (e) { busy(false); return window.alert((e && e.message) || 'Lưu lỗi'); }
  go(scrDoanhSo, true);
}


/* ---------- Tinh tien quay: D1 (TCV) va NVHTN (08/08/2026) ----------
   Buoc 1 chon quay, buoc 2 chon NGUON DON cho tung bill: Tai cho, Mang ve,
   hoac app (Grab, Be, GreenSM, Shopee) - dung nguyen tac "vao nguon nao ra
   nguon do" cua SOP. Bill luu bang tao_don_tay thanh Sales Invoice NHAP,
   ra soat va ghi so cuoi ngay tren man Doanh thu Sales. Chuyen khoan thi
   hien VietQR dien san so tien + so phieu. Chua tru kho, chua in bill. */
var posDon = null, posHomNayTxt = null, posQuay = null;
var posDsNgay = null; /* ngay dang xem o danh sach hoá đơn; null = hom nay */
var posLocTt = 'tat_ca', posLocNg = '', posLocHd = ''; /* chip loc: tinh trang x nguon-pt x trang thai HDDT */
function posNgayVn(iso) {
  var d = new Date(iso + 'T00:00:00');
  var thu = ['Chủ nhật', 'Thứ hai', 'Thứ ba', 'Thứ tư', 'Thứ năm', 'Thứ sáu', 'Thứ bảy'][d.getDay()];
  var p = iso.split('-');
  return thu + ', ' + p[2] + '/' + p[1] + '/' + p[0];
}
/* Ma bill sinh ngay luc mo bill, dung lam NOI DUNG CHUYEN KHOAN in trong
   ma QR. Sinh truoc thi khach quet duoc ngay, khoi doi luu bill xong;
   luu bill thi chinh ma nay di vao o ma tham chieu de ke toan doi soat
   dung cai khach da chuyen (giong ma HD tren bill Fabi). */
function posMaBill() {
  var chu = 'ACDEFGHJKLMNPQRSTUVWXY3456789';
  var s = '';
  for (var i = 0; i < 5; i++) s += chu.charAt(Math.floor(Math.random() * chu.length));
  return 'VGB' + s;
}
function posMoi() {
  posSepayNhan = 0;
  return { che_do: 'Tại chỗ', ma: '', bill: posMaBill(), pt: 'Tiền mặt', mtc: '', ten: '', sdt: '', giam: '', dua: '', ghi_chu: '', km: null, so_ban: '', khach_no: null, xhd_mo: false, xh: { mst: '', ten: '', dc: '', email: '' }, mon: [], ctkm: [], combo: [], maVc: '', otpKm: '', kmKq: null, khach_ma: '', khach_hang: '' };
}
function posKmGiam(km, tong) {
  if (!km) return 0;
  if (km.loai === 'Phần trăm') return Math.round(tong * flt0(km.gia_tri) / 100);
  return Math.round(flt0(km.gia_tri));
}
/* Tien SePay da nhan cho ma bill dang mo - poll 5 giay mot lan khi dang
   chia QR chuyen khoan, de khach chuyen den noi la cashier thay ngay. */
var posSepayNhan = 0, posPollId = null;
function posPollTat() { if (posPollId) { clearInterval(posPollId); posPollId = null; } }
function posPollBat(ma, tien) {
  posPollTat();
  posPollId = setInterval(async function () {
    /* Roi man tinh tien thi tu tat, khoi goi may chu vo ich. */
    if (!document.getElementById('posNd')) return posPollTat();
    try {
      var kq = await api('vagabond.ban_hang.pos_kiem_sepay', { noi_dung: ma, tien: tien });
      if (kq && flt0(kq.nhan) > posSepayNhan) {
        posSepayNhan = flt0(kq.nhan);
        if (document.getElementById('posNd')) go(scrPosQuay, true);
      }
      if (kq && kq.du) posPollTat();
    } catch (e) { }
  }, 5000);
}
function flt0(v) { return parseFloat(v) || 0; }
function posSoTien(v) { return parseFloat(String(v == null ? '' : v).replace(/[^0-9]/g, '')) || 0; }
function posDsCheDo() {
  var app = (((CFGBH || {}).nguon) || []).filter(function (n) {
    return n.v.indexOf('Tại chỗ') !== 0 && n.v.indexOf('Mang về') !== 0 && n.v !== 'Khách sỉ' && n.v !== 'Pancake';
  });
  return [{ v: 'Tại chỗ', ic: '🏬' }, { v: 'Mang về', ic: '🥡' }].concat(app.map(function (n) { return { v: n.v, ic: n.ic || '', lg: n.lg || '' }; }));
}
function posNguonThuc() {
  if (!posQuay || !posDon) return '';
  if (posDon.che_do === 'Tại chỗ') return posQuay.tai_cho;
  if (posDon.che_do === 'Mang về') return posQuay.mang_ve;
  return posDon.che_do;
}
function posDoc() {
  if (!posDon) return;
  var g = function (id) { var o = document.getElementById(id); return o ? o.value : null; };
  var v;
  v = g('posMa'); if (v !== null) posDon.ma = v;
  v = g('posTen'); if (v !== null) posDon.ten = v;
  v = g('posSdt'); if (v !== null) posDon.sdt = v;
  v = g('posMtc'); if (v !== null) posDon.mtc = v;
  if (!posDon.bill) posDon.bill = posMaBill();
  v = g('posGiam'); if (v !== null) posDon.giam = posSoTien(v) ? String(posSoTien(v)) : '';
  v = g('posDua'); if (v !== null) posDon.dua = posSoTien(v) ? String(posSoTien(v)) : '';
  v = g('posGhiChu'); if (v !== null) posDon.ghi_chu = v;
  v = g('posXhMst'); if (v !== null) posDon.xh.mst = v;
  v = g('posXhTen'); if (v !== null) posDon.xh.ten = v;
  v = g('posXhDc'); if (v !== null) posDon.xh.dc = v;
  v = g('posXhEmail'); if (v !== null) posDon.xh.email = v;
}
/* Buoc chon quay: vao card la hoi, khong nho lua chon cu (anh Viet 08/08). */
async function scrPosChonQuay() {
  await cfgBanHang();
  var dsQ = ((CFGBH || {}).quay) || [];
  /* Thumbnail la anh cua hang that (anh Viet gui 09/08), nhin phat biet
     ngay minh dang chon quay nao. Anh nam trong repo, thieu thi lui ve
     bieu tuong cu. */
  /* Sales Online la diem ban thu ba, nam duoi hai quay (anh Viet
     10/08/2026). Khong phai quay tinh tien nen bam vao di thang sang man
     Doanh thu Sales, khong qua man tinh tien. */
  var CARD_SALES = {
    ma: 'SALES',
    ten: 'Sales Online 307/1 Nguyễn Văn Trỗi',
    phu: 'Đơn online: Pancake, GrabFood, ShopeeFood, BeFood, GreenSM',
    anh: (CFGBH || {}).anh_sales || '',
    sales: 1
  };
  var dsAll = dsQ.concat([CARD_SALES]);
  var suaAnh = typeof isSales === 'function' ? isSales() : false;
  var html = '<div class="sec">Chọn điểm bán</div>';
  dsAll.forEach(function (q, i) {
    html += '<div class="card" style="margin-bottom:12px;overflow:hidden;padding:0;position:relative">' +
      '<div data-q="' + i + '" style="cursor:pointer">' +
      (q.anh
        ? '<img src="' + h(q.anh) + '" alt="" style="width:100%;height:150px;object-fit:cover;display:block" onerror="this.style.display=\'none\'">'
        : '<div style="height:96px;display:flex;align-items:center;justify-content:center;background:#f6f7f9;color:#c3c8d4;font-size:34px">🏬</div>') +
      '<div style="display:flex;align-items:center;gap:10px;padding:13px 14px">' +
      '<div style="flex:1"><div class="h1" style="font-size:17px;font-weight:700">' + h(q.ten) + '</div>' +
      '<div class="h2" style="color:#98a2b3;font-size:13px">' + h(q.phu || '') + '</div></div>' +
      '<span style="color:#c3c8d4;font-size:22px">&#8250;</span></div></div>' +
      (suaAnh
        ? '<button data-anh="' + h(q.ma) + '" style="position:absolute;top:9px;right:9px;border:0;background:rgba(16,24,40,.62);color:#fff;border-radius:999px;padding:6px 12px;font-size:12px;font-weight:700;cursor:pointer;font-family:inherit">✎ Ảnh</button>'
        : '') +
      '</div>';
  });
  html += '<div style="text-align:center;color:#a0a6b4;font-size:12px;padding:4px 10px 10px">Chọn đúng điểm bán mình đang đứng - doanh thu và đối soát tách riêng từng điểm, không gộp chung</div>';
  var b = frame('Tính tiền - hoá đơn bán hàng', html);
  b.onclick = function (e) {
    var a = e.target.closest('[data-anh]');
    if (a) return posDoiAnhQuay(a.getAttribute('data-anh'));
    var r = e.target.closest('[data-q]');
    if (!r) return;
    var q = dsAll[+r.getAttribute('data-q')];
    if (q && q.sales) { posQuay = null; return go(scrDoanhSo); }
    posQuay = q;
    posHomNayTxt = null;
    go(scrPosQuay);
  };
}

/* Doi anh thumbnail diem ban ngay trong app: quan ly chup anh cua hang
   bang dien thoai roi tai len, khong phai nho ky thuat (anh Viet
   10/08/2026). Anh luu thanh File cua Frappe, duong dan cat vao default. */
async function posDoiAnhQuay(ma) {
  var inp = document.createElement('input');
  inp.type = 'file';
  inp.accept = 'image/*';
  inp.onchange = async function () {
    var f = inp.files && inp.files[0];
    if (!f) return;
    if (f.size > 8 * 1024 * 1024) return toast('Ảnh nặng quá 8MB, chụp lại hoặc giảm kích thước giúp em.', 4000);
    busy(true);
    try {
      var fd = new FormData();
      fd.append('file', f, f.name);
      fd.append('is_private', '0');
      fd.append('folder', 'Home');
      var rs = await fetch('/api/method/upload_file', {
        method: 'POST',
        headers: { 'X-Frappe-CSRF-Token': (window.frappe && frappe.csrf_token) || '' },
        body: fd,
        credentials: 'same-origin'
      });
      var kq = await rs.json();
      var url = ((kq || {}).message || {}).file_url || '';
      if (!url) throw new Error('Tải ảnh lên không thành công');
      await api('vagabond.ban_hang.pos_anh_quay_luu', { ma: ma, url: url });
      CFGBH = null;
      busy(false);
      toast('Đã đổi ảnh điểm bán.');
      go(scrPosChonQuay, true);
    } catch (e) {
      busy(false);
      toast((e && e.message) || 'Không tải được ảnh lên.', 4000);
    }
  };
  inp.click();
}
/* Logo GrabFood, GreenSM, ShopeeFood... moi cai mot ti le khac nhau (co cai
   rong gap 3 lan chieu cao), de chung mot dong voi chu thi chu bi day tran
   ra ngoai nut (anh Viet 09/08). Nay moi logo deu duoc gioi han CUNG MOT
   CHIEU CAO va khong bao gio rong qua nut - nhin ngang hang, chu xuong
   dong ben duoi nen nut nao cung vuong van bang nhau. */
function posONhan(n, cao) {
  cao = cao || 22;
  var k = 'height:' + cao + 'px;max-width:100%;flex:none;display:flex;align-items:center;justify-content:center';
  if (n.lg) return '<span style="' + k + '"><img src="' + n.lg + '" style="max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain;display:block"></span>';
  if (n.ic) return '<span style="' + k + ';width:' + cao + 'px;font-size:' + Math.round(cao * 0.86) + 'px">' + n.ic + '</span>';
  return '';
}
function posNutNguon(ds, chon) {
  return ds.map(function (n) {
    var on = n.v === chon;
    return '<button class="pnc" data-nd="' + h(n.v) + '" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;min-height:66px;padding:6px 4px;border-radius:10px;overflow:hidden;border:1.5px solid ' + (on ? '#0d9488;background:#ccfbf1;color:#0f766e' : '#e5e7eb;background:#fff;color:#374151') + '">' +
      posONhan(n) +
      '<span style="font-size:12.5px;line-height:1.15;text-align:center;font-weight:' + (on ? '700' : '500') + '">' + h(n.v) + '</span></button>';
  }).join('');
}
function posNutPt(ds, chon) {
  return ds.map(function (p) {
    var on = p.v === chon;
    return '<button class="ptc" data-pt="' + h(p.v) + '" style="display:flex;align-items:center;justify-content:center;gap:8px;min-height:56px;padding:6px 8px;border-radius:10px;overflow:hidden;border:1.5px solid ' + (on ? '#0d9488;background:#ccfbf1;color:#0f766e' : '#e5e7eb;background:#fff;color:#374151') + '">' +
      posONhan({ lg: p.lg, ic: p.lg ? '' : (p.ic || '🏦') }, 24) +
      '<span style="font-size:14px;line-height:1.15;font-weight:' + (on ? '700' : '500') + '">' + h(p.v) + '</span></button>';
  }).join('');
}
async function scrPosQuay() {
  await cfgBanHang();
  posPollTat();
  if (!posQuay) return go(scrPosChonQuay, true);
  if (!posDon) posDon = posMoi();
  var laApp = posDon.che_do !== 'Tại chỗ' && posDon.che_do !== 'Mang về';
  var nguonThuc = posNguonThuc();
  var dsPt = ptTheoNguon(nguonThuc);
  if (laApp) posDon.pt = dsPt.length === 1 ? dsPt[0].v : '';
  else if (!posDon.pt || !dsPt.some(function (p) { return p.v === posDon.pt; })) posDon.pt = 'Tiền mặt';
  var tong = posDon.mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0);
  /* Voucher phan tram bam theo tong bill: them bot mon la so giam tu tinh lai. */
  if (posDon.km) posDon.giam = String(posKmGiam(posDon.km, tong) || '');
  /* Khuyen mai moi: so tien giam do MAY CHU tinh, may khach chi hien lai.
     Gio hang doi mot chut la tinh lai ngay, khong de so cu tren man hinh
     roi luc chot ra so khac (anh Viet 11/08/2026). */
  await posTinhKm();
  var giamTay = posSoTien(posDon.giam), dua = posSoTien(posDon.dua);
  var giamKm = (posDon.kmKq && posDon.kmKq.tong_giam) || 0;
  var giam = giamTay + giamKm;
  var phaiThu = Math.max(0, tong - giam);
  var qApp = laApp ? (quyPt(posDon.pt) || {}) : {};
  var html = '<div class="card" style="padding:8px 14px">' +
    '<div class="hub" data-t="posDoiQuay" style="padding:6px 0;border:none"><div class="ht"><div class="h2">Quầy đang bán · bấm để đổi</div><div class="h1">' + h(posQuay.ten) + '</div></div>' +
    '<div style="text-align:right;flex:none"><div class="h2" style="color:#6b7280">Ngày bán</div><div style="font-weight:700;font-size:14px">' + posNgayVn(today()) + '</div></div>' +
    '<span style="color:#c3c8d4;margin-left:4px">&#8250;</span></div></div>';
  /* O TO mo danh sach hoa don trong ngay (anh Viet 09/08) - cashier va
     quan ly bam phat vao ngay, khoi phai mo dong chu nho. */
  html += '<div class="card" data-t="posDsBill" style="padding:13px 14px;cursor:pointer;border:1.5px solid #7fe5f6;background:#f4feff">' +
    '<div style="display:flex;align-items:center;gap:10px;pointer-events:none">' +
    '<span style="font-size:24px">📋</span>' +
    '<div style="flex:1;min-width:0"><div style="font-weight:800;font-size:15.5px;color:#0b7c93">Danh sách hoá đơn bán hàng trong ngày</div>' +
    '<div id="posHomNay" style="font-size:12.5px;color:#0b7c93;margin-top:2px">' + h(posHomNayTxt || 'Đang đếm hoá đơn hôm nay...') + '</div></div>' +
    '<span style="color:#0b7c93;font-size:22px">&#8250;</span></div></div>';
  html += '<div class="sec">Nguồn đơn</div><div class="card" style="padding:12px 14px">' +
    '<div id="posNd" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">' + posNutNguon(posDsCheDo(), posDon.che_do) + '</div>' +
    (laApp ? '<input class="tin" id="posMa" style="margin-top:10px" placeholder="' + h((qApp.nhan || 'Mã đơn bên app') + (qApp.vd ? ' - vd ' + qApp.vd : '')) + '" value="' + h(posDon.ma || '') + '">' : '') +
    '</div>';
  /* So ban: don ngoi tai quan thi waiter nhin so ban tren phieu ma bung
     mon cho dung khach (anh Viet 09/08/2026). Chon xong in len hoa don. */
  if (posDon.che_do === 'Tại chỗ') {
    var dsBan = [];
    for (var sb = 1; sb <= 20; sb++) dsBan.push(String(sb));
    html += '<div class="sec">Số bàn</div><div class="card" style="padding:10px 14px">' +
      '<div id="posBan" style="display:flex;flex-wrap:wrap;gap:8px">' +
      dsBan.map(function (b) {
        var on = posDon.so_ban === b;
        return posChipNut('data-ban="' + b + '"', 'Bàn ' + b, on);
      }).join('') +
      posChipNut('data-ban="Mang đi"', '🥡 Mang đi', posDon.so_ban === 'Mang đi') +
      (posDon.so_ban ? posChipNut('data-ban=""', '✕ Bỏ chọn', false, 1) : '') +
      '</div></div>';
  }
  html += '<div class="sec">Món trong hoá đơn</div><div class="card" style="padding:6px 14px">';
  if (!posDon.mon.length) html += '<div style="padding:14px 0;color:#a0a6b4">Chưa có món nào. Bấm Thêm món: tìm theo tên, mã hoặc quét mã vạch.</div>';
  /* Anh mon de nhin mat banh la biet dung mon chua; gia don vi nam ngay
     duoi ten, KHONG con duong bam sua gia (gia o quay khong duoc sua tay -
     anh Viet 09/08). Ba nut tru, cong, xoa cung mot kieu vuong 38px. */
  var NUT = 'height:38px;width:38px;flex:none;display:flex;align-items:center;justify-content:center;' +
    'border:1px solid #e5e7eb;background:#fff;border-radius:9px;font-size:19px;line-height:1;padding:0;cursor:pointer';
  posDon.mon.forEach(function (m, i) {
    html += '<div style="display:flex;align-items:center;gap:8px;padding:9px 0;border-bottom:1px solid #f0f2f6">' +
      (m.anh
        ? '<img src="' + h(m.anh) + '" loading="lazy" style="width:44px;height:44px;flex:none;object-fit:cover;border-radius:9px;border:1px solid #eef0f4" onerror="this.style.display=\'none\'">'
        : '<span style="width:44px;height:44px;flex:none;display:flex;align-items:center;justify-content:center;border-radius:9px;background:#f6f7f9;font-size:22px">🎂</span>') +
      '<div style="flex:1;min-width:0"><div data-tc-mo="' + i + '" style="font-size:14.5px;line-height:1.25;cursor:pointer">' + h(m.ten) + '</div>' +
      '<div style="color:#a0a6b4;font-size:12px;margin-top:1px">' + money(m.rate) + ' đ/cái</div>' +
      /* Tuy chon pha che la CHIP cho to ro (anh Viet 09/08): da chon thi
         chip xanh liet ke, chua chon mon nuoc thi chip nhac bam vao. */
      ((m.tc || []).length
        ? '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:5px">' +
          m.tc.map(function (x) {
            return '<span data-tc-mo="' + i + '" style="display:inline-block;background:#ccfbf1;color:#0f766e;border:1.5px solid #5eead4;border-radius:999px;padding:3px 11px;font-size:12.5px;font-weight:700;cursor:pointer">' + h(x) + '</span>';
          }).join('') +
          '<span data-tc-mo="' + i + '" style="display:inline-block;background:#fff;color:#6b7280;border:1.5px dashed #cbd5e1;border-radius:999px;padding:3px 10px;font-size:12.5px;cursor:pointer">✎ sửa</span></div>'
        : (m.nhom && ['Trà', 'Cà phê', 'Matcha', 'Cacao', 'Ice Cream - Kem'].indexOf(m.nhom) >= 0
          ? '<div style="margin-top:5px"><span data-tc-mo="' + i + '" style="display:inline-block;background:#ecfeff;color:#0b7c93;border:1.5px solid #7fe5f6;border-radius:999px;padding:4px 12px;font-size:12.5px;font-weight:700;cursor:pointer">🧊 Chọn đá / đường</span></div>'
          : '')) +
      /* Ghi chu RIENG cua tung mon (anh Viet 10/08/2026): o ghi chu chung
         ca hoa don khong du - bep khong biet loi dan la cho mon nao. */
      /* Moi ghi chu MOT chip rieng cho de nhin, khong don het vao mot
         chip dai (anh Viet 11/08/2026). */
      '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:5px">' +
      /* Chip TEN COMBO: mon ra tu combo nao thi mang chip cua combo do, de
         nguoi di lay mon biet gom du bo, va de cuoi ngay dem duoc ban bao
         nhieu bo combo (anh Viet 11/08/2026). */
      (m.combo
        ? '<span style="display:inline-block;background:#ede9fe;color:#5b21b6;border:1.5px solid #c4b5fd;border-radius:999px;padding:4px 12px;font-size:12.5px;font-weight:700">🧺 ' + h(m.combo) + '</span>'
        : '') +
      /* Chip MA DON cua san food app: dong bo tu ma don nhap ben tren, de
         in bill va in tem ra la biet mon nay cua don nao (anh Viet
         11/08/2026). Chip nay may tu dien, khong bam sua duoc. */
      (posMaAppHienTai()
        ? '<span style="display:inline-block;background:#111827;color:#fff;border-radius:999px;padding:4px 12px;font-size:12.5px;font-weight:700">🛵 ' + h(posMaAppHienTai()) + '</span>'
        : '') +
      (m.gc
        ? String(m.gc).split(',').map(function (x) { return x.trim(); }).filter(Boolean).map(function (x) {
          return '<span data-gc-mo="' + i + '" style="display:inline-block;background:#fef3c7;color:#92400e;border:1.5px solid #fcd34d;border-radius:999px;padding:4px 12px;font-size:12.5px;font-weight:700;cursor:pointer">📝 ' + h(x) + '</span>';
        }).join('') +
        '<span data-gc-mo="' + i + '" style="display:inline-block;background:#fff;color:#6b7280;border:1.5px dashed #cbd5e1;border-radius:999px;padding:4px 10px;font-size:12.5px;cursor:pointer">✎ sửa</span>'
        : '<span data-gc-mo="' + i + '" style="display:inline-block;background:#fff;color:#98a2b3;border:1.5px dashed #d7dce5;border-radius:999px;padding:4px 12px;font-size:12.5px;cursor:pointer">📝 Ghi chú món</span>') +
      '</div></div>' +
      '<button data-bot="' + i + '" style="' + NUT + '">&minus;</button>' +
      '<b style="min-width:22px;text-align:center;font-size:15px">' + money(m.qty) + '</b>' +
      '<button data-cong="' + i + '" style="' + NUT + '">+</button>' +
      '<b style="min-width:70px;text-align:right;font-size:15px">' + money(m.qty * m.rate) + '</b>' +
      '<button data-x="' + i + '" style="' + NUT + ';color:#b3261e;font-size:16px">✕</button></div>';
  });
  html += '<div style="padding:10px 0"><button class="btn gh" id="posThem" style="width:100%">➕ Thêm món</button></div></div>';
  html += '<div class="sec">Thanh toán</div><div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    (posDon.pt === 'Công nợ' && !laApp ? posKhoiKhachNo() : '') +
    (laApp
      ? '<div style="font-size:13.5px;color:#6b7280">Đơn ' + h(posDon.che_do) + ' thanh toán bằng nguồn <b>' + h(posDon.pt || posDon.che_do) + '</b> - vào nguồn nào ra nguồn đó.</div>'
      : '<div id="posPt" style="display:grid;grid-template-columns:1fr 1fr;gap:8px">' + posNutPt(dsPt, posDon.pt) + '</div>' +
        (posDon.pt === 'Chuyển khoản'
          ? posKhoiQr(posNoiDungCk(posDon.bill), phaiThu, posNguonThuc())
          : '<div><div id="posMtcNhan" style="font-size:12px;color:#6b7280;margin-bottom:6px"></div>' +
            '<input class="tin" id="posMtc" placeholder="Mã tham chiếu" value="' + h(posDon.mtc || '') + '"></div>')) +
    posKhoiKm() +
    '<div><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">' +
    '<span style="font-size:12.5px;color:#6b7280;font-weight:600">GIẢM GIÁ TAY THÊM (đ)</span></div>' +
    '<input class="tin" id="posGiam" placeholder="0" inputmode="numeric" value="' + (giamTay ? money(giamTay) : '') + '"></div>' +
    (!laApp && posDon.pt === 'Tiền mặt'
      ? '<div><div style="font-size:12.5px;color:#6b7280;font-weight:600;margin-bottom:6px">KHÁCH ĐƯA (đ) - máy tính tiền thối</div>' +
        '<input class="tin" id="posDua" placeholder="0" inputmode="numeric" value="' + (dua ? money(dua) : '') + '"></div>'
      : '') +
    '</div>';
  html += '<div class="sec">Khách (không bắt buộc)</div><div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    /* O ten khach co GOI Y: go ten, ma, ma so thue hay so dien thoai la
       xo ra danh sach de bam chon (anh Viet 11/08/2026). Chon xong may
       dien luon so dien thoai va gan ho so khach vao hoa don, nho vay
       chuong trinh khuyen mai theo hang khach moi ap duoc. */
    '<div style="position:relative">' +
    (posDon.khach_ma
      ? '<div style="display:flex;align-items:center;gap:8px;background:#f0fdfa;border:1.5px solid #7fe5f6;border-radius:10px;padding:9px 11px;margin-bottom:8px">' +
        '<span style="font-size:17px">👤</span>' +
        '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(posDon.ten || posDon.khach_ma) + '</b>' +
        '<div style="font-size:11.5px;color:#0b7c93">mã ' + h(posDon.khach_ma) + (posDon.khach_hang ? ' · hạng ' + h(posDon.khach_hang) : '') + '</div></div>' +
        '<button id="posBoKhach" style="border:0;background:transparent;color:#b3261e;font-size:17px;cursor:pointer">✕</button></div>'
      : '') +
    '<input class="tin" id="posTen" placeholder="Tên khách, mã khách, MST hoặc số điện thoại" autocomplete="off" value="' + h(posDon.ten || '') + '">' +
    '<div id="posTenGoi"></div></div>' +
    '<input class="tin" id="posSdt" placeholder="Số điện thoại" inputmode="tel" value="' + h(posDon.sdt || '') + '">' +
    '<input class="tin" id="posGhiChu" placeholder="Ghi chú bill: gói quà, để lạnh, giao lầu 2..." value="' + h(posDon.ghi_chu || '') + '">' +
    '</div>';
  /* Khach can hoa don cong ty thi dien ngay tai quay - nhap MST la may tu
     tra ten va dia chi (giong man Doanh thu Sales). Khong dien o day thi
     khach van quet duoc QR cuoi bill giay de tu dien sau. */
  var xin2 = 'width:100%;box-sizing:border-box;padding:10px 11px;border:1.5px solid #e5e7eb;border-radius:9px;font-size:14px;font-family:inherit';
  html += '<div class="card" style="padding:12px 14px;margin-top:10px">' +
    '<div id="posXhMo" style="display:flex;align-items:center;gap:8px;cursor:pointer"><span style="font-size:17px">🧾</span>' +
    '<div style="flex:1"><b style="font-size:14px">Khách cần hoá đơn công ty?</b><div style="font-size:12px;color:#98a2b3">Không điền cũng được - khách quét QR cuối hoá đơn tự điền sau</div></div>' +
    '<span style="color:#c3c8d4;font-size:18px">' + (posDon.xhd_mo ? '▾' : '▸') + '</span></div>' +
    (posDon.xhd_mo
      ? '<div style="display:grid;gap:8px;margin-top:10px">' +
        '<input id="posXhMst" placeholder="Mã số thuế - chi nhánh gõ cả dấu gạch, vd 0311638525-027" value="' + h(posDon.xh.mst) + '" style="' + xin2 + '">' +
        '<input id="posXhTen" placeholder="Tên pháp nhân trên hoá đơn" value="' + h(posDon.xh.ten) + '" style="' + xin2 + '">' +
        '<textarea id="posXhDc" rows="2" placeholder="Địa chỉ trên hoá đơn" style="' + xin2 + '">' + h(posDon.xh.dc) + '</textarea>' +
        '<input id="posXhEmail" placeholder="Email nhận hoá đơn" value="' + h(posDon.xh.email) + '" style="' + xin2 + '">' +
        '<div id="posXhBao" style="font-size:12px;color:#6b7280"></div></div>'
      : '') +
    '</div>';
  html += '<div class="card" style="padding:12px 14px;display:grid;gap:6px;margin-top:10px">' +
    '<div style="display:flex;justify-content:space-between;color:#5a6070"><span>Tạm tính</span><span>' + money(tong) + ' đ</span></div>' +
    (((posDon.kmKq && posDon.kmKq.ap) || []).map(function (a) {
      return '<div style="display:flex;justify-content:space-between;color:#0f766e"><span>' + h(a.ten) + '</span><span>&minus;' + money(a.giam) + ' đ</span></div>';
    }).join('')) +
    (giamTay ? '<div style="display:flex;justify-content:space-between;color:#b45309"><span>Giảm giá tay</span><span>&minus;' + money(giamTay) + ' đ</span></div>' : '') +
    '<div style="display:flex;justify-content:space-between;font-size:19px"><b>PHẢI THU</b><b>' + money(phaiThu) + ' đ</b></div>' +
    (!laApp && posDon.pt === 'Tiền mặt' && dua ? '<div style="display:flex;justify-content:space-between;color:' + (dua >= phaiThu ? '#0f766e' : '#b3261e') + '"><span>Khách đưa ' + money(dua) + ' đ</span><b>' + (dua >= phaiThu ? 'Thối ' + money(dua - phaiThu) : 'Còn thiếu ' + money(phaiThu - dua)) + ' đ</b></div>' : '') +
    '</div>';
  /* In bill tam tinh (y Felix): khach dat qua sale hoac ban thanh toan
     chung cuoi buoi - in phieu giu mon kem QR, cashier chot sau. Don app
     thi khong co khai niem tam tinh. */
  var footer = (laApp ? '' : '<button class="btn gh" id="posTam" style="flex:0 0 34%;margin:0">🖨 Tạm tính</button>') +
    '<button class="btn" id="posLuu" style="flex:1;margin:0">💰 Thu tiền ' + money(phaiThu) + ' đ</button>';
  var b = frame('Tính tiền · ' + (posQuay.ma || ''), html, { footer: '<div style="display:flex;gap:8px">' + footer + '</div>' });
  if (!laApp && posDon.pt !== 'Chuyển khoản') veOMtc(posDon.pt, 'posMtc', 'posMtcNhan');
  posDemHomNay();
  b.addEventListener('click', function (e) {
    if (e.target.closest('[data-t="posDoiQuay"]')) { posDoc(); posQuay = null; posHomNayTxt = null; return go(scrPosChonQuay, true); }
    if (e.target.closest('[data-t="posDsBill"]')) { posDoc(); posDsNgay = null; return go(scrPosDs); }
    var t;
    t = e.target.closest('[data-nd]');
    if (t) { posDoc(); posDon.che_do = t.getAttribute('data-nd'); return go(scrPosQuay, true); }
    t = e.target.closest('[data-cong]');
    if (t) { posDoc(); posDon.mon[+t.getAttribute('data-cong')].qty += 1; return go(scrPosQuay, true); }
    t = e.target.closest('[data-bot]');
    if (t) {
      posDoc();
      var i = +t.getAttribute('data-bot');
      posDon.mon[i].qty -= 1;
      if (posDon.mon[i].qty <= 0) posDon.mon.splice(i, 1);
      return go(scrPosQuay, true);
    }
    t = e.target.closest('[data-x]');
    if (t) { posDoc(); posDon.mon.splice(+t.getAttribute('data-x'), 1); return go(scrPosQuay, true); }
    t = e.target.closest('[data-ban]');
    if (t) { posDoc(); posDon.so_ban = t.getAttribute('data-ban') || ''; return go(scrPosQuay, true); }
    t = e.target.closest('[data-tc-mo]');
    if (t) { posDoc(); return posMoTuyChon(+t.getAttribute('data-tc-mo')); }
    t = e.target.closest('[data-gc-mo]');
    if (t) { posDoc(); return posMoGhiChuMon(+t.getAttribute('data-gc-mo')); }
  });
  var ptw = document.getElementById('posPt');
  if (ptw) ptw.querySelectorAll('.ptc').forEach(function (c) {
    c.onclick = function () { posDoc(); posDon.pt = c.getAttribute('data-pt'); go(scrPosQuay, true); };
  });
  ['posGiam', 'posDua'].forEach(function (id) {
    var o = document.getElementById(id);
    if (o) o.onblur = function () { posDoc(); go(scrPosQuay, true); };
  });
  document.getElementById('posThem').onclick = posThemMon;
  document.getElementById('posLuu').onclick = posLuuDon;
  var nTam = document.getElementById('posTam');
  if (nTam) nTam.onclick = posInTamTinh;
  var nCn = document.getElementById('posChonKhachNo');
  if (nCn) nCn.onclick = posSheetKhachNo;
  var nCnBo = document.getElementById('posBoKhachNo');
  if (nCnBo) nCnBo.onclick = function () { posDoc(); posDon.khach_no = null; go(scrPosQuay, true); };
  posNoiKm();
  posNoiTimKhach();
  /* Go xong ma don san food app thi ve lai man de chip ma don hien ngay
     tren tung mon (anh Viet 11/08/2026). */
  var nMa = document.getElementById('posMa');
  if (nMa) nMa.onchange = function () { posDoc(); go(scrPosQuay, true); };
  var xhMo = document.getElementById('posXhMo');
  if (xhMo) xhMo.onclick = function () { posDoc(); posDon.xhd_mo = !posDon.xhd_mo; go(scrPosQuay, true); };
  var xhMst = document.getElementById('posXhMst');
  if (xhMst) xhMst.onblur = async function () {
    var so = (xhMst.value || '').replace(/[^0-9]/g, '');
    var bao = document.getElementById('posXhBao');
    if (so.length !== 10 && so.length !== 13) { if (bao) bao.textContent = so ? 'Mã số thuế phải 10 hoặc 13 số.' : ''; return; }
    if (bao) bao.textContent = 'Đang tra mã số thuế...';
    try {
      var kq = await api('vagabond.api.tra_mst', { mst: so });
      var t = document.getElementById('posXhTen'), dc = document.getElementById('posXhDc');
      if (kq && kq.ok) {
        if (t && !t.value.trim()) t.value = kq.ten || '';
        if (dc && !dc.value.trim()) dc.value = kq.dia_chi || '';
        if (bao) bao.textContent = 'Tra được: ' + (kq.ten || '');
      } else if (bao) bao.textContent = 'Không tra được mã này, điền tay giúp em.';
    } catch (e) { if (bao) bao.textContent = 'Không tra được mã này, điền tay giúp em.'; }
  };
  ['posGhiChu'].forEach(function (id) {
    var o = document.getElementById(id);
    if (o) o.onblur = function () { posDoc(); };
  });
  /* Chuyen khoan dang cho tien: poll SePay de bao ngay khi tien ve. */
  if (!laApp && posDon.pt === 'Chuyển khoản' && phaiThu > 0 && posSepayNhan < phaiThu - 1) posPollBat(posDon.bill, phaiThu);
}
async function posDemHomNay() {
  if (!posQuay) return;
  try {
    var kq = await api('vagabond.ban_hang.pos_ds_bill', { quay: posQuay.ma || '' });
    /* Bill da huy khong phai tien: dong nay la cho thu ngan nhin nhieu nhat
       trong ngay, lech voi Chot ca la sinh chuyen cai nhau luc giao ca. */
    var ds = ((kq && kq.bill) || []).filter(function (r) { return !r.vgb_huy; });
    var tong = 0, tam = 0, chua = 0, xong = 0;
    ds.forEach(function (r) {
      tong += r.grand_total || 0;
      if (r.docstatus === 1) xong++;
      else if (r.vgb_tam_tinh) tam++;
      else chua++;
    });
    posHomNayTxt = 'Hôm nay ' + ds.length + ' hoá đơn · ' + money(tong) + ' đ · ' +
      (tam ? '🕐 ' + tam + ' tạm tính · ' : '') +
      (chua ? '📄 ' + chua + ' chưa ghi sổ · ' : '') +
      '✅ ' + xong + ' đã ghi sổ.';
  } catch (e) { posHomNayTxt = ''; }
  var o = document.getElementById('posHomNay');
  if (o) o.textContent = posHomNayTxt;
}
async function posThemMon() {
  posDoc();
  if (!dsItemsCache) {
    busy(true);
    try {
      dsItemsCache = await getList('Item', { filters: { is_sales_item: 1, disabled: 0, item_group: ['not in', ['Nguyên vật liệu Thô', 'Bán thành phẩm Bánh', 'Bán thành phẩm Nước', 'Nhân bán thành phẩm', 'Công cụ Dụng cụ', 'Bao bì', 'Văn phòng phẩm', 'Tài sản Cố định']] }, fields: ['name', 'item_name', 'image', 'standard_rate', 'item_group'], limit_page_length: 0, order_by: 'item_name' });
      try {
        var bc = await getList('Item Barcode', { parent: 'Item', fields: ['parent', 'barcode'], limit_page_length: 0 });
        var bcm = {};
        (bc || []).forEach(function (r) { bcm[r.parent] = (bcm[r.parent] ? bcm[r.parent] + ' ' : '') + r.barcode; });
        dsItemsCache.forEach(function (x) { x.ma_vach = bcm[x.name] || ''; });
      } catch (e2) { /* khong doc duoc barcode thi van tim theo ma */ }
    } catch (e) { busy(false); return toast('Không tải được danh mục món'); }
    busy(false);
  }
  /* Combo nam ngay trong bang chon mon, nhom "Combo" xep dau tien (anh
     Viet 11/08/2026). Bam mot combo la may RA no thanh cac mon thanh phan
     do vao gio, moi mon mang chip ten combo de nguoi di lay mon biet no
     thuoc combo nao. */
  var dsCombo = [];
  try {
    var kqCb = await api('vagabond.khuyen_mai.ds_combo', { quay: (posQuay && posQuay.ma) || '', nguon: posNguonThuc() });
    dsCombo = ((kqCb && kqCb.combo) || []).filter(function (x) { return x.dung_duoc; });
  } catch (e3) { dsCombo = []; }
  var oCombo = dsCombo.map(function (c) {
    return {
      value: '@CB@' + c.name, label: '🧺 ' + c.ten, icon: '🧺', img: c.anh || '',
      gia: c.gia_combo, nhom: NHOM_COMBO, combo: c,
      phu: comboMoTa(c) + ' · ' + money(c.gia_combo) + ' đ, tiết kiệm ' + (c.co_nhom ? 'từ ' : '') + money(c.tiet_kiem) + ' đ',
      tim: c.name + ' combo'
    };
  });
  posSheetMon(oCombo.concat(dsItemsCache.map(function (x) {
    return { value: x.name, label: x.item_name, icon: '🎂', img: x.image || '', gia: x.standard_rate || 0, nhom: x.item_group || '', phu: (x.standard_rate ? money(x.standard_rate) + ' đ' : 'chưa có giá') + ' · ' + x.name, tim: x.name + ' ' + (x.ma_vach || '') };
  })), function (o) {
    if (o.combo) { return posBamCombo(o.combo); }
    var i = -1;
    posDon.mon.forEach(function (m, k) { if (m.item_code === o.value && !m.combo) i = k; });
    if (i >= 0) { posDon.mon[i].qty += 1; return posDon.mon[i].qty; }
    /* Gia o quay khong duoc sua tay: mon chua co gia ban thi bao Sales dat
       gia trong danh muc, chu khong go tay tai quay (anh Viet 09/08). */
    if (!o.gia) { toast('Món ' + o.label + ' chưa có giá bán trong danh mục. Nhờ Sales đặt giá rồi bấm lại.', 4500); return 0; }
    posDon.mon.push({ item_code: o.value, ten: o.label, qty: 1, rate: o.gia, anh: o.img || '', nhom: o.nhom, tc: [], gc: '' });
    return 1;
  }, function () { go(scrPosQuay, true); }, function (ma) {
    var q = 0;
    if (String(ma).indexOf('@CB@') === 0) {
      var mc = String(ma).slice(4);
      (posDon.combo || []).forEach(function (c) { if (c.ma === mc) q = c.so_bo; });
      return q;
    }
    posDon.mon.forEach(function (m) { if (m.item_code === ma) q += m.qty; });
    return q;
  });
}

var NHOM_COMBO = 'Combo';

/* Mot dong chu ta noi dung combo: mon co san cong voi cac nhom cho chon. */
function comboMoTa(c) {
  var ph = (c.bat_buoc || c.dong || []).map(function (d) { return num(d.so_luong) + '× ' + h(d.ten_mon || d.item_code); });
  (c.nhom_ds || []).forEach(function (g) {
    var tt = parseInt(g.toi_thieu, 10); if (isNaN(tt)) tt = g.chon || 1;
    var td = parseInt(g.toi_da, 10); if (isNaN(td) || td < 1) td = g.chon || 1;
    ph.push((tt === td ? 'chọn ' + td : 'chọn ' + tt + ' đến ' + td) + ' trong ' + (g.mon || []).length + ' ' + h(g.ten));
  });
  return ph.join(' + ');
}

/* Them mot bo combo vao gio: ra thanh tung mon thanh phan, moi mon mang
   ten combo de bep va nguoi di lay mon biet mon do thuoc combo nao, va de
   cuoi ngay dem duoc ban bao nhieu bo (anh Viet 11/08/2026). */
function posThemCombo(c, chon) {
  chon = chon || [];
  /* Mon vao bill = mon bat buoc + mon khach vua chon trong tung nhom.
     Combo cu khong co nhom nao thi bat_buoc chinh la ca danh sach dong. */
  var dong = (c.bat_buoc || c.dong || []).slice();
  chon.forEach(function (x) {
    (c.nhom_ds || []).forEach(function (g) {
      if (g.ten !== x.nhom) return;
      (g.mon || []).forEach(function (m) { if (m.item_code === x.item_code) dong.push(m); });
    });
  });
  dong.forEach(function (d) {
    var i = -1;
    posDon.mon.forEach(function (m, k) {
      if (m.item_code === d.item_code && m.combo === c.ten) i = k;
    });
    if (i >= 0) posDon.mon[i].qty += flt0(d.so_luong);
    else posDon.mon.push({
      item_code: d.item_code, ten: d.ten_mon || d.item_code,
      qty: flt0(d.so_luong), rate: flt0(d.gia_goc),
      anh: '', nhom: '', tc: [], gc: '', combo: c.ten, combo_ma: c.name
    });
  });
  posDon.combo = posDon.combo || [];
  /* Cung mot combo ma khach chon hai bo mon khac nhau thi phai la HAI dong
     rieng: gop chung lai la may chu khong biet bo thu hai gom nhung mon gi,
     tinh sai tien giam. */
  var khoa = comboKhoa(c.name, chon);
  var cu = null;
  posDon.combo.forEach(function (x) { if (comboKhoa(x.ma, x.chon) === khoa) cu = x; });
  if (cu) cu.so_bo += 1;
  else posDon.combo.push({ ma: c.name, so_bo: 1, ten: c.ten, chon: chon });
  posDon.kmKq = null;
  toast('Đã thêm combo ' + c.ten);
}

/* Bam combo o bang chon mon: co nhom thi hoi truoc, khong co thi do luon. */
function posBamCombo(c) {
  if (c.co_nhom) {
    posSheetChonCombo(c, function (chon) {
      posThemCombo(c, chon);
      /* Bang chon mon van dang mo o duoi, dong no lai roi hay ve man tinh
         tien - khong thi thu ngan bam OK xong van thay bang chon mon. */
      Array.prototype.forEach.call(document.querySelectorAll('.sh'), function (o) { o.remove(); });
      go(scrPosQuay, true);
    });
    return 0;
  }
  posThemCombo(c);
  return 1;
}

/* Hang chip LOC dung chung cho ba man danh sach hoa don (anh Viet
   10/08/2026). Moi chip kem so dem; chip khong co hoa don nao thi an di
   cho do roi mat, rieng chip "Tat ca" luon hien. */
/* Nhom trang thai hoa don dien tu, dung chung cho ca ba man danh sach hoa
   don: Doanh thu Sales, hoa don quay D1 va quay NVHTN (anh Viet 12/08/2026).
   Ke toan can loc nhanh "don nao chua ky", "don nao bi thay the" ma khong
   phai mo tung don ra xem. */
var HD_NHOM = {
  cho_ky: ['Chờ ký', 'Chờ duyệt', 'Đang ký'],
  da_ky: ['Đã ký', 'Đã gửi CQT', 'CQT chấp nhận'],
  loi: ['CQT báo lỗi', 'Lỗi'],
  huy: ['Đã hủy', 'Đã huỷ'],
  thay_the: ['HĐ thay thế', 'Bị thay thế'],
  dieu_chinh: ['HĐ điều chỉnh', 'Bị điều chỉnh']
};
function hdThuoc(r, nhom) {
  var tt = (r.custom_hddt_trang_thai || '').trim();
  return tt ? (HD_NHOM[nhom] || []).indexOf(tt) >= 0 : false;
}
function locHddt() {
  return [
    { k: '', nhan: 'Mọi trạng thái HĐ', loc: function () { return true; } },
    { k: 'chua', nhan: '📌 Chưa xuất HĐĐT', loc: function (r) { return r.docstatus === 1 && !r.custom_hddt_so && !(r.custom_hddt_trang_thai || '').trim(); } },
    { k: 'cho_ky', nhan: '✍️ Chờ ký', loc: function (r) { return hdThuoc(r, 'cho_ky'); } },
    { k: 'da_ky', nhan: '✅ Đã ký', loc: function (r) { return hdThuoc(r, 'da_ky'); } },
    { k: 'thay_the', nhan: '🔁 Thay thế', loc: function (r) { return hdThuoc(r, 'thay_the'); } },
    { k: 'dieu_chinh', nhan: '✏️ Điều chỉnh', loc: function (r) { return hdThuoc(r, 'dieu_chinh'); } },
    { k: 'huy', nhan: '🚫 Đã huỷ', loc: function (r) { return hdThuoc(r, 'huy'); } },
    { k: 'loi', nhan: '⚠ Cơ quan thuế báo lỗi', loc: function (r) { return hdThuoc(r, 'loi'); } }
  ];
}

/* Loc cai gi thi phai biet loc ra BAO NHIEU TIEN. Cuoi ngay bam chip
   GrabFood la de doi soat voi Grab: khong co dong tong thi phai lay may
   tinh cong tay tung dong tren man (anh Viet 12/08/2026).

   Tinh tren TOAN BO tap da loc, khong tinh tren phan dang hien: man nao
   cat bot dong de ve nhanh thi con so o day van la con so that. */
function locKhoiTong(rows, nhan) {
  var so = 0, tien = 0, chot = 0, tienChot = 0, nhap = 0, tienNhap = 0, huy = 0, tienHuy = 0;
  (rows || []).forEach(function (r) {
    var v = Number(r.grand_total || 0);
    if (r.vgb_huy) { huy++; tienHuy += v; return; }
    so++; tien += v;
    if (r.docstatus === 1) { chot++; tienChot += v; }
    else { nhap++; tienNhap += v; }
  });
  var dong = function (chu, n, t, mau) {
    return '<div style="display:flex;justify-content:space-between;font-size:12.5px;color:' + (mau || '#6b7280') + ';margin-top:3px">' +
      '<span>' + chu + ' ' + n + ' đơn</span><b>' + money(t) + ' đ</b></div>';
  };
  return '<div class="card" style="padding:12px 14px;background:#f0fdfa;border:1.5px solid #99f6e4">' +
    '<div style="font-size:11.5px;color:#0f766e;font-weight:800;letter-spacing:.3px">TỔNG THEO BỘ LỌC' +
    (nhan ? ' · ' + h(nhan) : '') + '</div>' +
    '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">' +
    '<span style="font-size:13.5px;color:#374151">' + so + ' hoá đơn</span>' +
    '<b style="font-size:20px;color:#0f766e">' + money(tien) + ' đ</b></div>' +
    (chot && nhap ? dong('Đã ghi sổ', chot, tienChot) + dong('Chưa ghi sổ', nhap, tienNhap) : '') +
    (huy ? dong('Đã huỷ, không tính vào tổng', huy, tienHuy, '#991b1b') : '') +
    '</div>';
}

function locHang(ds, dangChon, attr, rows) {
  var ra = ds.map(function (c) {
    var n = rows.filter(c.loc).length;
    if (!n && c.k !== '') return '';
    var on = c.k === dangChon;
    return '<button ' + attr + '="' + h(c.k) + '" style="flex:0 0 auto;border:1.5px solid ' +
      (on ? '#0d9488' : '#d7dce5') + ';background:' + (on ? '#0d9488' : '#fff') +
      ';color:' + (on ? '#fff' : '#374151') + ';border-radius:999px;padding:7px 13px;font-size:12.5px;' +
      'font-weight:' + (on ? '800' : '600') + ';cursor:pointer;white-space:nowrap;font-family:inherit">' +
      c.nhan + ' <span style="opacity:.75">' + n + '</span></button>';
  }).join('');
  return '<div style="flex:0 0 auto;display:flex;gap:7px;padding:2px 0;overflow-x:auto;-webkit-overflow-scrolling:touch">' + ra + '</div>';
}

/* Chip nguon don + phuong thuc thanh toan sinh theo du lieu that cua ngay,
   khong bay ra chip rong. */
function locNguonPt(rows) {
  var ds = [{ k: '', nhan: 'Mọi nguồn', loc: function () { return true; } }];
  var ng = [], pt = [];
  rows.forEach(function (r) {
    var a = r.custom_nguon || '';
    if (a && ng.indexOf(a) < 0) ng.push(a);
    var b = r.vgb_pt_thanh_toan || '';
    if (b && pt.indexOf(b) < 0) pt.push(b);
  });
  ng.sort(function (a, b) { return a.localeCompare(b, 'vi'); });
  pt.sort(function (a, b) { return a.localeCompare(b, 'vi'); });
  ng.forEach(function (a) {
    ds.push({ k: 'ng:' + a, nhan: h(a), loc: function (r) { return (r.custom_nguon || '') === a; } });
  });
  pt.forEach(function (b) {
    /* Don san co phuong thuc trung ten nguon (GrabFood tra qua GrabFood):
       bay hai chip giong het nhau chi lam roi mat, bo bot mot. */
    if (ng.indexOf(b) >= 0) return;
    ds.push({ k: 'pt:' + b, nhan: 'Trả: ' + h(b), loc: function (r) { return (r.vgb_pt_thanh_toan || '') === b; } });
  });
  return ds;
}
function locTim(ds, k) {
  for (var i = 0; i < ds.length; i++) if (ds[i].k === k) return ds[i];
  return ds[0];
}

/* Chip chung cho moi nut chon nhanh cua app (anh Viet 09/08/2026: nut
   bam thi lam dang CHIP cho de nhin, de phan biet). */
function posChipNut(attr, chu, dangChon, laXoa) {
  var vien = dangChon ? '#0d9488' : (laXoa ? '#fecaca' : '#d7dce5');
  var nen = dangChon ? '#0d9488' : '#fff';
  var chuMau = dangChon ? '#fff' : (laXoa ? '#b3261e' : '#374151');
  return '<button ' + attr + ' style="border:1.5px solid ' + vien + ';background:' + nen +
    ';color:' + chuMau + ';border-radius:999px;padding:9px 15px;font-size:14px;font-weight:' +
    (dangChon ? '800' : '600') + ';cursor:pointer;white-space:nowrap;line-height:1.2">' + chu + '</button>';
}

/* Sheet chon mon rieng cho quay: co hang chip NHOM MON nhu cot trai Fabi
   (anh Viet 09/08/2026) - bam nhom la loc, do phai go tim tung mon. */
var posNhomChon = '';
/* Thu tu nhom mon o hang chip: xep theo tan suat ban that tai quay chu
   khong theo bang chu cai (anh Viet 10/08/2026). Danh sach thu tu do
   backend giu, nhom la de cuoi. */
function posXepNhom(nhoms) {
  var uu = ((CFGBH || {}).thu_tu_nhom) || [];
  return nhoms.slice().sort(function (a, b) {
    /* Combo luon dau hang chip: cashier bam vao la thay ngay, khong phai
       cuon di tim (anh Viet 11/08/2026). */
    if (a === NHOM_COMBO) return -1;
    if (b === NHOM_COMBO) return 1;
    var ia = uu.indexOf(a), ib = uu.indexOf(b);
    if (ia < 0) ia = 9999;
    if (ib < 0) ib = 9999;
    if (ia !== ib) return ia - ib;
    return a.localeCompare(b, 'vi');
  });
}
function posSheetMon(items, onPick, onDong, demSo) {
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  var nhoms = [];
  items.forEach(function (it) { if (it.nhom && nhoms.indexOf(it.nhom) < 0) nhoms.push(it.nhom); });
  nhoms = posXepNhom(nhoms);
  var hd = '<div class="shh"><b>Chọn món</b><div class="x">&times;</div></div>' +
    '<div style="flex:0 0 auto;padding:10px 14px 4px;display:flex;gap:8px"><input class="nt" placeholder="Tìm nhanh..." style="height:46px;padding:0 12px;flex:1"><button class="nt" id="shQuet" title="Quét mã vạch" style="height:46px;width:54px;flex:none;font-size:20px;cursor:pointer">&#128247;</button></div>' +
    /* flex:0 0 auto: .shb la flex column nen hang chip tung bi danh sach mon
       dai nen bep con 12px, mat chu (loi anh Viet bao 09/08). */
    '<div id="shNhom" style="flex:0 0 auto;min-height:40px;display:flex;gap:6px;padding:8px 14px 6px;overflow-x:auto;-webkit-overflow-scrolling:touch"></div>';
  /* Thanh duoi: dem so mon da chon va nut Xong. Truoc day bam mot mon la
     sheet dong luon, muon them mon thu hai phai mo lai tu dau - Dễ bao
     10/08/2026. Nay bam bao nhieu mon cung duoc, xong moi dong. */
  box.innerHTML = hd + '<div class="shl"></div>' +
    '<div id="shDay" style="flex:0 0 auto;display:flex;align-items:center;gap:10px;' +
    'padding:10px 14px calc(env(safe-area-inset-bottom,0px) + 10px);border-top:1px solid #eef0f4;background:#fff">' +
    '<div id="shDem" style="flex:1;min-width:0;font-size:13px;color:#6b7280"></div>' +
    '<button id="shXong" style="flex:none;border:0;background:#0d9488;color:#fff;border-radius:999px;' +
    'padding:11px 22px;font-size:15px;font-weight:800;cursor:pointer;font-family:inherit">Xong</button></div>';
  var lst = box.querySelector('.shl'), oNhom = box.querySelector('#shNhom');
  var soLanChon = 0;
  function veDem() {
    var o = box.querySelector('#shDem');
    if (!o) return;
    o.innerHTML = soLanChon
      ? '<b style="color:#0f766e">Đã thêm ' + soLanChon + ' lượt món</b> · bấm tiếp để thêm nữa'
      : 'Bấm liên tiếp để thêm nhiều món, xong thì bấm Xong';
  }
  function veNhom() {
    var ds = ['Tất cả'].concat(nhoms);
    oNhom.innerHTML = ds.map(function (n) {
      var v = n === 'Tất cả' ? '' : n;
      var on = v === posNhomChon;
      return '<button data-nh="' + h(v) + '" style="flex:0 0 auto;padding:7px 13px;border-radius:18px;font-size:13px;white-space:nowrap;cursor:pointer;border:1.5px solid ' + (on ? '#0d9488;background:#0d9488;color:#fff;font-weight:700' : '#e5e7eb;background:#fff;color:#374151') + '">' + h(n) + '</button>';
    }).join('');
  }
  function draw(q) {
    q = (q || '').toLowerCase();
    var f = items.filter(function (it) {
      if (posNhomChon && it.nhom !== posNhomChon) return false;
      return !q || ((it.label || '') + ' ' + (it.tim || '') + ' ' + (it.value || '')).toLowerCase().indexOf(q) >= 0;
    });
    lst.innerHTML = f.length ? f.map(function (it) {
      var dc = demSo ? (demSo(it.value) || 0) : 0;
      return '<div class="shi" data-i="' + items.indexOf(it) + '"' + (dc ? ' style="background:#f0fdfa"' : '') + '>' +
        (it.img ? '<img src="' + it.img + '" style="width:36px;height:36px;object-fit:cover;border-radius:8px;flex:none;border:1px solid #e5e7eb" loading="lazy">' : '<span>' + (it.icon || '🎂') + '</span>') +
        '<span style="flex:1;min-width:0">' + h(it.label) + (it.phu ? '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(it.phu) + '</div>' : '') + '</span>' +
        (dc ? '<b style="flex:none;background:#0d9488;color:#fff;border-radius:999px;min-width:26px;height:26px;' +
          'display:flex;align-items:center;justify-content:center;font-size:13px;padding:0 8px">' + money(dc) + '</b>' : '') +
        '</div>';
    }).join('') : '<div class="emp"><div class="e2">Không tìm thấy trong nhóm này</div></div>';
  }
  veNhom(); draw(''); 
  ov.appendChild(box); document.body.appendChild(ov);
  var inp = box.querySelector('input');
  inp.oninput = function () { draw(inp.value); };
  oNhom.onclick = function (e) {
    var t = e.target.closest('[data-nh]'); if (!t) return;
    posNhomChon = t.getAttribute('data-nh');
    veNhom(); draw(inp.value);
  };
  var shQ = box.querySelector('#shQuet');
  if (shQ) shQ.onclick = async function () {
    var code = null;
    try { code = await scanBarcode(); } catch (e) { code = null; }
    if (code) { inp.value = code; draw(code); }
  };
  function close() { ov.remove(); if (onDong) onDong(); }
  ov.onclick = function (e) { if (e.target === ov) close(); };
  box.querySelector('.x').onclick = close;
  box.querySelector('#shXong').onclick = close;
  lst.onclick = function (e) {
    var r = e.target.closest('.shi'); if (!r) return;
    var kq = onPick(items[+r.dataset.i]);
    /* Ham chon tra ve so luong moi cua mon do (0 = khong them duoc, vi du
       mon chua co gia). Sheet van mo, chi ve lai dong cho thay so. */
    if (kq) {
      soLanChon += 1;
      r.style.background = '#ccfbf1';
      setTimeout(function () { draw(inp.value); }, 130);
    }
    veDem();
  };
  veDem();
}

/* Ban cho khach cong no thi PHAI biet la no cua ai, khong thi cuoi
   thang khong doi duoc (anh Viet 11/08/2026). Chon khach xong, thong tin
   xuat hoa don da luu cua khach do tu dien luon xuong duoi. */
function posKhoiKhachNo() {
  var k = posDon.khach_no;
  if (k) {
    return '<div style="border:1.5px solid #fcd34d;background:#fffbeb;border-radius:10px;padding:11px 12px">' +
      '<div style="display:flex;align-items:center;gap:8px">' +
      '<span style="font-size:18px">📒</span>' +
      '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(k.ten) + '</b>' +
      '<div style="font-size:12px;color:#92400e">Ghi nợ cho khách này · mã ' + h(k.ma) + (k.mst ? ' · MST ' + h(k.mst) : '') + '</div></div>' +
      '<button id="posBoKhachNo" style="border:0;background:transparent;color:#b3261e;font-size:18px;cursor:pointer">✕</button></div></div>';
  }
  return '<button id="posChonKhachNo" class="btn gh" style="margin:0;border-color:#fcd34d;color:#92400e">📒 Chọn khách công nợ (bắt buộc)</button>';
}

/* Sheet tim khach hang: go ten hay ma deu ra, giong bang tim mon. */
/* Sheet chon khach dung chung cho ca man tinh tien quay va man Chi tiet
   don ben Doanh thu Sales. Go la hoi thang MAY CHU chu khong loc tren
   danh sach da tai ve - danh muc hang nghin khach, loc tai cho thi go
   "Oshima" khong bao gio ra (anh Viet 12/08/2026). */
async function sheetTimKhach(tieuDe, onChon) {
  busy(true);
  var kq;
  try { kq = await api('vagabond.cong_no.tim_khach', { tu_khoa: '' }); }
  catch (e) { busy(false); return toast((e && e.message) || 'Không tải được danh sách khách'); }
  busy(false);
  var ds = (kq && kq.khach) || [];
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>' + h(tieuDe) + '</b><div class="x">&times;</div></div>' +
    '<div style="flex:0 0 auto;padding:10px 14px 4px"><input class="nt" id="tkTim" placeholder="Gõ tên, mã khách, MST hoặc số điện thoại..." style="height:46px;padding:0 12px;width:100%;box-sizing:border-box"></div>' +
    '<div class="shl"></div>';
  var lst = box.querySelector('.shl');
  function ve() {
    lst.innerHTML = ds.length ? ds.map(function (x) {
      return '<div class="shi" data-kh="' + h(x.name) + '"><span>🏢</span>' +
        '<span style="flex:1;min-width:0">' + h(x.customer_name || x.name) +
        '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(x.name) +
        (x.tax_id ? ' · MST ' + h(x.tax_id) : '') +
        (x.mobile_no ? ' · ' + h(x.mobile_no) : '') +
        (x.customer_group ? ' · ' + h(x.customer_group) : '') + '</div></span></div>';
    }).join('') : '<div class="emp"><div class="e2">Không tìm thấy khách nào. Kế toán tạo khách bên Next trước nhé.</div></div>';
  }
  ve();
  ov.appendChild(box); document.body.appendChild(ov);
  var inp = box.querySelector('#tkTim');
  var tre = null;
  inp.oninput = function () {
    if (tre) clearTimeout(tre);
    tre = setTimeout(async function () {
      try {
        var k2 = await api('vagabond.cong_no.tim_khach', { tu_khoa: inp.value });
        ds = (k2 && k2.khach) || [];
        ve();
      } catch (e) { }
    }, 260);
  };
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  lst.onclick = function (e) {
    var r = e.target.closest('[data-kh]'); if (!r) return;
    var ma = r.getAttribute('data-kh');
    var x = ds.filter(function (y) { return y.name === ma; })[0] || {};
    dong();
    onChon(x.name ? x : { name: ma, customer_name: ma });
  };
  setTimeout(function () { try { inp.focus(); } catch (e) { } }, 120);
}

async function posSheetKhachNo() {
  busy(true);
  var kq;
  try { kq = await api('vagabond.cong_no.tim_khach', { tu_khoa: '' }); }
  catch (e) { busy(false); return toast((e && e.message) || 'Không tải được danh sách khách'); }
  busy(false);
  var ds = (kq && kq.khach) || [];
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>Chọn khách công nợ</b><div class="x">&times;</div></div>' +
    '<div style="flex:0 0 auto;padding:10px 14px 4px"><input class="nt" id="cnTim" placeholder="Gõ tên hoặc mã khách..." style="height:46px;padding:0 12px;width:100%;box-sizing:border-box"></div>' +
    '<div class="shl"></div>';
  var lst = box.querySelector('.shl');
  function ve(q) {
    q = (q || '').toLowerCase();
    var f = ds.filter(function (x) {
      return !q || ((x.customer_name || '') + ' ' + (x.name || '') + ' ' + (x.tax_id || '')).toLowerCase().indexOf(q) >= 0;
    });
    lst.innerHTML = f.length ? f.map(function (x) {
      return '<div class="shi" data-kh="' + h(x.name) + '"><span>🏢</span>' +
        '<span style="flex:1;min-width:0">' + h(x.customer_name || x.name) +
        '<div style="color:#a0a6b4;font-size:12px;margin-top:2px">' + h(x.name) +
        (x.tax_id ? ' · MST ' + h(x.tax_id) : '') + (x.customer_group ? ' · ' + h(x.customer_group) : '') + '</div></span></div>';
    }).join('') : '<div class="emp"><div class="e2">Không tìm thấy khách nào. Kế toán tạo khách bên Next trước nhé.</div></div>';
  }
  ve('');
  ov.appendChild(box); document.body.appendChild(ov);
  var inp = box.querySelector('#cnTim');
  /* Danh sach khach hang dai (hang tram khach si va khach cong ty) nen
     lan dau chi lay 60 cai dau. Go tim thi phai hoi lai MAY CHU chu khong
     duoc loc tren 60 cai da tai ve - go "ravie" ma khong ra vi Ravie
     khong nam trong 60 khach dau bang chu cai (bat duoc 11/08/2026). */
  var tre = null;
  inp.oninput = function () {
    var q = inp.value;
    ve(q);
    if (tre) clearTimeout(tre);
    tre = setTimeout(async function () {
      try {
        var k2 = await api('vagabond.cong_no.tim_khach', { tu_khoa: q });
        ds = (k2 && k2.khach) || [];
        ve(inp.value);
      } catch (e) { }
    }, 280);
  };
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  lst.onclick = async function (e) {
    var r = e.target.closest('[data-kh]'); if (!r) return;
    var ma = r.getAttribute('data-kh');
    var x = ds.filter(function (y) { return y.name === ma; })[0] || {};
    dong();
    posDoc();
    posDon.khach_no = { ma: ma, ten: x.customer_name || ma, mst: x.tax_id || '' };
    if (!posDon.ten) posDon.ten = x.customer_name || '';
    if (!posDon.sdt) posDon.sdt = x.mobile_no || '';
    /* Khach si nao da luu thong tin xuat hoa don thi dien san luon, thu
       ngan khoi go lai tung chu. */
    try {
      var tt = await api('vagabond.cong_no.thong_tin_xhd', { khach: ma });
      if (tt && (tt.mst || tt.ten)) {
        posDon.xhd_mo = true;
        posDon.xh = {
          mst: tt.mst || '', ten: tt.ten || '',
          dc: tt.dia_chi || '', email: tt.email || ''
        };
        toast('Đã điền sẵn thông tin xuất hoá đơn của ' + (tt.ten || ma));
      }
    } catch (e2) { }
    go(scrPosQuay, true);
  };
}

/* Ghi chu cho MOT mon: bep va quay pha che doc tren phieu lam mon va
   tem dan, nen phai go duoc loi dan rieng tung mon chu khong dung chung
   mot o ghi chu ca hoa don (anh Viet 10/08/2026). */
var POS_GC_NHANH = [
  'Không đá', 'Ít đá', 'Đá riêng', 'Ít ngọt', 'Không đường',
  'Nóng', 'Mang đi', 'Gói riêng', 'Để lạnh', 'Không hộp',
  'Cắt sẵn', 'Không nến', 'Viết lời chúc'
];
function posMoGhiChuMon(i) {
  var m = posDon.mon[i];
  if (!m) return;
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>Ghi chú · ' + h(m.ten) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:6px 14px calc(env(safe-area-inset-bottom,0px) + 14px)">' +
    '<div style="font-size:12px;color:#98a2b3;margin-bottom:8px">Ghi chú này in lên phiếu làm món và tem dán món, chỉ áp cho món này.</div>' +
    '<textarea id="gcO" rows="2" placeholder="Ví dụ: ít ngọt, gói riêng, viết chữ Happy Birthday..." style="width:100%;box-sizing:border-box;padding:11px 12px;border:1.5px solid #d7dce5;border-radius:10px;font-size:15px;font-family:inherit">' + h(m.gc || '') + '</textarea>' +
    '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-top:10px">' +
    POS_GC_NHANH.map(function (x) {
      return '<button data-gcn="' + h(x) + '" style="border:1.5px solid #d7dce5;background:#fff;color:#374151;border-radius:999px;padding:8px 13px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit">' + h(x) + '</button>';
    }).join('') + '</div>' +
    '<button class="btn" id="gcXong" style="margin-top:16px">Xong</button>' +
    (m.gc ? '<button class="btn gh" id="gcXoa" style="margin-top:8px;color:#b3261e">Xoá ghi chú món này</button>' : '') +
    '</div>';
  ov.appendChild(box); document.body.appendChild(ov);
  var o = box.querySelector('#gcO');
  function dong(luu) {
    if (luu) m.gc = (o.value || '').trim().slice(0, 200);
    ov.remove();
    go(scrPosQuay, true);
  }
  ov.onclick = function (e) { if (e.target === ov) dong(1); };
  box.querySelector('.x').onclick = function () { dong(1); };
  box.querySelector('#gcXong').onclick = function () { dong(1); };
  var nx = box.querySelector('#gcXoa');
  if (nx) nx.onclick = function () { o.value = ''; dong(1); };
  box.addEventListener('click', function (e) {
    var t = e.target.closest('[data-gcn]'); if (!t) return;
    var v = t.getAttribute('data-gcn');
    var cu = (o.value || '').trim();
    o.value = cu ? (cu.indexOf(v) >= 0 ? cu : cu + ', ' + v) : v;
  });
  setTimeout(function () { try { o.focus(); } catch (e) { } }, 60);
}

/* Ma don cua san food app, de mapping vao ghi chu tung mon va in dam len
   tem: shipper GrabFood den doc dung ma la nhan dung tui (anh Viet
   10/08/2026). Don tai cho / mang ve thi khong co ma nay. */
function posMaAppHienTai() {
  if (!posDon) return '';
  var laApp = posDon.che_do !== 'Tại chỗ' && posDon.che_do !== 'Mang về';
  if (!laApp) return '';
  var ma = (posDon.ma || '').trim();
  return ma ? (posDon.che_do + ' ' + ma) : '';
}
function posGcGui(m, maApp) {
  var v = [];
  if (maApp) v.push(maApp);
  if (m.gc) v.push(m.gc);
  return v.join(' · ');
}

/* Tuy chon pha che kieu customization Fabi: it duong, it da, da rieng...
   Khong chon gi = mac dinh 100% duong 100% da, khong ghi gi len bill.
   Cac lua chon deu 0 dong - chi la loi dan cho quay pha che. */
var POS_TC = null;
async function posMoTuyChon(i) {
  var m = posDon.mon[i];
  if (!m) return;
  if (POS_TC === null) {
    try { var kq = await api('vagabond.ban_hang.pos_ds_tuy_chon', {}); POS_TC = (kq && kq.tc) || []; }
    catch (e) { POS_TC = []; }
  }
  var ds = POS_TC.filter(function (n) { return !n.nhom_mon.length || n.nhom_mon.indexOf(m.nhom || '') >= 0; });
  if (!ds.length) return;
  m.tc = m.tc || [];
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  var html = '<div class="shh"><b>' + h(m.ten) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 14px)">' +
    '<div style="font-size:12px;color:#98a2b3;margin-bottom:6px">Không chọn gì = 100% đường, 100% đá như bình thường.</div>';
  ds.forEach(function (n) {
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:10px 0 6px;text-transform:uppercase">' + h(n.nhom) + '</div>' +
      '<div style="display:flex;gap:7px;flex-wrap:wrap">' +
      n.lua_chon.map(function (lc) {
        var on = m.tc.indexOf(lc) >= 0;
        return '<button data-tc="' + h(lc) + '" style="padding:9px 13px;border-radius:10px;font-size:14px;cursor:pointer;border:1.5px solid ' + (on ? '#0d9488;background:#ccfbf1;color:#0f766e;font-weight:700' : '#e5e7eb;background:#fff;color:#374151') + '">' + h(lc) + '</button>';
      }).join('') + '</div>';
  });
  html += '<button class="btn" id="tcXong" style="margin-top:16px">Xong</button></div>';
  box.innerHTML = html;
  ov.appendChild(box); document.body.appendChild(ov);
  function dong() { ov.remove(); go(scrPosQuay, true); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  box.querySelector('#tcXong').onclick = dong;
  box.addEventListener('click', function (e) {
    var t = e.target.closest('[data-tc]'); if (!t) return;
    var lc = t.getAttribute('data-tc');
    var k = m.tc.indexOf(lc);
    if (k >= 0) m.tc.splice(k, 1); else m.tc.push(lc);
    var on = m.tc.indexOf(lc) >= 0;
    t.style.border = '1.5px solid ' + (on ? '#0d9488' : '#e5e7eb');
    t.style.background = on ? '#ccfbf1' : '#fff';
    t.style.color = on ? '#0f766e' : '#374151';
    t.style.fontWeight = on ? '700' : 'normal';
  });
}
/* Ma QR dong kieu bill Fabi: khach quet bang app ngan hang la so tien va
   noi dung chuyen khoan dien san, khoi go tay, khoi go nham (anh Viet
   09/08/2026). Dung anh VietQR nen may nao co mang la hien duoc. */
/* Noi dung chuyen khoan mang MA DIEM BAN o dau: "TCV VGBAB123".

   Ke toan nhin sao ke ngan hang la biet ngay giao dich thuoc diem nao ma
   khong phai mo tung don ra tra. Ma bill van nam nguyen trong chuoi nen bo
   do SePay khong he doi: no tim VGBxxxxx BEN TRONG noi dung chu khong so
   ca cum.

   Day chi la lop mem - khach sua duoc noi dung, app ngan hang co loai cat
   bot ky tu. Lop cung la moi diem mot tai khoan nhan rieng; luc nao mo
   duoc tai khoan ao rieng thi khai o man Diem ban. */
function posNoiDungCk(maBill, maDiem) {
  var d = String(maDiem || (typeof posQuay !== 'undefined' && posQuay ? posQuay.ma : '') || '').trim();
  var b = String(maBill || '').trim();
  return d ? (d + ' ' + b) : b;
}

/* Tai khoan nhan tien cua mot nguon don. Anh Viet dang xin MB Bank cap
   tai khoan ao rieng cho tung nguon de ke toan doc sao ke la biet ngay
   tien cua nguon nao. Nguon chua khai rieng thi dung tai khoan mac dinh. */
function posTaiKhoan(nguon) {
  var c = CFGBH || {};
  var n = String(nguon || '').trim();
  var b = c.qr_nguon || {};
  if (n && b[n] && b[n].stk) return b[n];
  return c.qr_quay || {};
}
function posQrUrl(noiDung, tien, nguon) {
  var q = posTaiKhoan(nguon);
  if (!q.stk) return '';
  return 'https://img.vietqr.io/image/' + (q.bank || 'MB') + '-' + q.stk + '-qr_only.png' +
    '?amount=' + Math.round(tien || 0) +
    '&addInfo=' + encodeURIComponent(noiDung || '') +
    '&accountName=' + encodeURIComponent(q.ten || '');
}
function posKhoiQr(noiDung, tien, nguon) {
  var q = posTaiKhoan(nguon);
  var url = posQrUrl(noiDung, tien, nguon);
  if (!url) return '<div style="font-size:13px;color:#b3261e">Chưa khai số tài khoản nhận chuyển khoản nên chưa sinh được mã QR.</div>';
  if (!tien) return '<div style="font-size:13px;color:#6b7280">Thêm món vào hoá đơn rồi mã QR chuyển khoản sẽ hiện ra đây.</div>';
  /* Tien ve du la khoi nay tu doi mau xanh - poll SePay 5 giay mot lan. */
  if (posSepayNhan >= tien - 1) {
    return '<div style="border:2px solid #16a34a;border-radius:12px;padding:16px;text-align:center;background:#f0fdf4">' +
      '<div style="font-size:34px">✅</div>' +
      '<div style="font-size:18px;font-weight:800;color:#15803d">ĐÃ NHẬN ĐỦ ' + money(posSepayNhan) + ' đ</div>' +
      '<div style="font-size:13px;color:#374151;margin-top:4px">SePay khớp nội dung <b>' + h(noiDung) + '</b>. Bấm Thu tiền để lưu hoá đơn rồi ghi sổ.</div>' +
      '</div>';
  }
  return '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:12px;text-align:center;background:#fff">' +
    '<div style="font-size:12.5px;color:#6b7280">Khách quét mã này, máy tự điền số tiền và nội dung</div>' +
    '<img src="' + url + '" alt="Mã QR chuyển khoản" style="width:min(240px,62vw);aspect-ratio:1;margin:10px auto 6px;display:block;border-radius:10px;background:#fff">' +
    '<div style="font-size:18px;font-weight:800;color:#0f766e">' + money(tien) + ' đ</div>' +
    '<div style="font-size:13px;color:#374151;margin-top:2px">Nội dung: <b>' + h(noiDung) + '</b></div>' +
    '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' + h(q.ten || '') + ' · ' + h((q.bank || '') + ' ' + (q.stk || '')) + '</div>' +
    '<div id="posChoTien" style="font-size:12px;color:#b45309;margin-top:8px">⏳ Đang chờ tiền về... màn hình tự báo khi SePay nhận đủ.</div>' +
    '</div>';
}
function posQrSheet(soPhieu, tien, siName, nguon) {
  var q = posTaiKhoan(nguon);
  var url = posQrUrl(soPhieu, tien, nguon);
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb" style="padding:20px 16px calc(env(safe-area-inset-bottom,0px) + 16px);text-align:center">' +
    '<div style="font-size:21px;font-weight:800">Chuyển khoản ' + money(tien) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-top:2px">' + h(q.ten || '') + ' · ' + h((q.bank || '') + ' ' + (q.stk || '')) + '</div>' +
    '<img src="' + url + '" alt="VietQR" style="width:min(300px,72vw);aspect-ratio:1;margin:12px auto 4px;display:block;border:1px solid #e5e7eb;border-radius:14px;background:#fff">' +
    '<div style="font-size:13px;color:#374151">Nội dung chuyển khoản: <b>' + h(soPhieu) + '</b></div>' +
    '<div id="qrsBao" style="font-size:12.5px;color:#b45309;margin-top:8px">⏳ Đang chờ tiền về... màn hình tự báo khi SePay nhận đủ.</div>' +
    '<div style="display:flex;gap:8px;margin-top:14px">' +
    (posBillVua ? '<button class="btn gh" data-in style="flex:0 0 34%;margin:0">🖨 In hoá đơn</button>' : '') +
    '<button class="btn" data-y style="flex:1;margin:0">Hoá đơn mới</button></div>' +
    (posBillVua && posCoNuoc(posBillVua.mon)
      ? '<div style="display:flex;gap:8px;margin-top:8px"><button class="btn gh" data-pm style="flex:1;margin:0">🧾 In phiếu làm món</button><button class="btn gh" data-tem style="flex:1;margin:0">🏷 In tem món</button></div>'
      : '') +
    '</div>';
  document.body.appendChild(ov);
  /* Tien ve la doi ngay thanh nut ghi so - cashier chot bill tai cho. */
  var pid = setInterval(async function () {
    if (!document.body.contains(ov)) return clearInterval(pid);
    try {
      var kq = await api('vagabond.ban_hang.pos_kiem_sepay', { noi_dung: soPhieu, tien: tien });
      if (kq && kq.du) {
        clearInterval(pid);
        var bao = ov.querySelector('#qrsBao');
        if (bao) { bao.style.color = '#15803d'; bao.innerHTML = '✅ <b>ĐÃ NHẬN ĐỦ ' + money(kq.nhan) + ' đ</b> - SePay khớp nội dung ' + h(soPhieu) + '.'; }
        var ny = ov.querySelector('[data-y]');
        if (ny && siName) { ny.textContent = '📒 Ghi sổ luôn - Hoá đơn mới'; ny.setAttribute('data-gs', '1'); }
      }
    } catch (e) { }
  }, 5000);
  ov.onclick = async function (e) {
    /* In bill / ghi so xong la ve DANH SACH BILL de quan ly thay chip
       trang thai ca (anh Viet 09/08); Bill moi thi ve man bam bill. */
    if (e.target.hasAttribute('data-in')) {
      if (posBillVua) posInBill(posBillVua);
      clearInterval(pid); ov.remove(); posHomNayTxt = null; go(scrPosDs, true);
      return;
    }
    if (e.target.hasAttribute('data-pm')) { if (posBillVua) posInPhieuMon(posBillVua); return; }
    if (e.target.hasAttribute('data-tem')) { if (posBillVua) posInTemLy(posBillVua); return; }
    if (!e.target.hasAttribute('data-y')) return;
    var ghiSo = !!(e.target.hasAttribute('data-gs') && siName);
    if (ghiSo) {
      busy(true);
      try { await api('vagabond.ban_hang.pos_ghi_so', { name: siName }); busy(false); toast('Đã ghi sổ ' + siName); }
      catch (er) { busy(false); toast((er && er.message) || 'Ghi sổ lỗi', 4000); }
    }
    clearInterval(pid); ov.remove(); posHomNayTxt = null; go(ghiSo ? scrPosDs : scrPosQuay, true);
  };
}
var posDangLuu = false;
async function posLuuDon() {
  /* Bam hai lan lien la ra hai bill cung so tien - khoa lai cho chac. */
  if (posDangLuu) return;
  posDoc();
  if (!posDon.mon.length) return toast('Hoá đơn chưa có món nào.');
  var thieuGia = posDon.mon.filter(function (m) { return !m.rate; });
  if (thieuGia.length) return toast('Món ' + thieuGia[0].ten + ' chưa có giá, bấm vào tên món để nhập.');
  var laApp = posDon.che_do !== 'Tại chỗ' && posDon.che_do !== 'Mang về';
  var nguon = posNguonThuc();
  var giamTay = posSoTien(posDon.giam), dua = posSoTien(posDon.dua);
  var tong = posDon.mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0);
  /* Tinh lai khuyen mai ngay truoc khi chot: gio hang co the vua doi ma
     man hinh chua kip ve lai. */
  await posTinhKm();
  var giamKm = (posDon.kmKq && posDon.kmKq.tong_giam) || 0;
  var giam = giamTay + giamKm;
  var phaiThu = Math.max(0, tong - giam);
  if (laApp && !(posDon.ma || '').trim()) return toast('Đơn ' + posDon.che_do + ' phải nhập mã đơn bên app để đối soát.');
  if (!laApp) {
    /* Cong no ma khong biet no cua ai thi cuoi thang khong doi duoc. */
    if (posDon.pt === 'Công nợ' && !(posDon.khach_no && posDon.khach_no.ma)) {
      return toast('Bán công nợ phải chọn khách hàng để còn theo dõi và thu sau.', 4000);
    }
    var qp = quyPt(posDon.pt) || {};
    if (qp.bat && !(posDon.mtc || '').trim()) return toast('Phương thức ' + posDon.pt + ' bắt buộc nhập ' + (qp.nhan || 'mã tham chiếu') + '.');
    /* Chuyen khoan: noi dung khach chuyen chinh la ma bill in trong QR. */
    if (posDon.pt === 'Chuyển khoản' && !(posDon.mtc || '').trim()) posDon.mtc = posDon.bill || '';
  }
  var canhBao = (!laApp && posDon.pt === 'Tiền mặt' && dua && dua < phaiThu) ? '\n⚠ Khách mới đưa ' + money(dua) + ' đ, còn thiếu ' + money(phaiThu - dua) + ' đ.' : '';
  /* Hai bill giong het nhau trong vong hai phut thuong la bam trung. */
  try {
    var kqT = await api('vagabond.ban_hang.pos_ds_bill', { quay: posQuay.ma || '' });
    var gio = Date.now();
    var trung = ((kqT && kqT.bill) || []).filter(function (r) {
      var t = new Date(String(r.creation || '').replace(' ', 'T')).getTime();
      return Math.abs((r.grand_total || 0) - phaiThu) < 1 && (gio - t) < 2 * 60 * 1000;
    });
    if (trung.length) canhBao += '\n⚠ CÓ ' + trung.length + ' HOÁ ĐƠN CÙNG SỐ TIỀN ' + money(phaiThu) + ' đ vừa lưu chưa đầy 2 phút. Có phải bấm trùng không? Kiểm trong danh sách hoá đơn trước khi thu tiếp.';
  } catch (e) { }
  var ok = await confirmSheet('Thu ' + money(phaiThu) + ' đ - ' + (laApp ? posDon.che_do : posDon.pt),
    posQuay.ten + ' · ' + posDon.che_do + '\n' + posDon.mon.map(function (m) { return m.ten + ' x' + money(m.qty); }).join(', ') +
    (giamKm ? '\n' + ((posDon.kmKq.ap || []).map(function (a) { return a.ten + ' −' + money(a.giam) + ' đ'; }).join('\n')) : '') +
    (giamTay ? '\nGiảm tay ' + money(giamTay) + ' đ' : '') + canhBao,
    'Thu tiền, lưu hoá đơn');
  if (!ok) return;
  var otpKm = await posXinOtpKm();
  if (posDon.kmKq && posDon.kmKq.can_otp && !otpKm) return toast('Chưa có mã OTP nên chưa lưu được hoá đơn.', 4000);
  if (posDangLuu) return;
  posDangLuu = true;
  busy(true);
  var r;
  try {
    r = await api('vagabond.ban_hang.tao_don_tay', {
      ngay: today(), nguon: nguon, ma_don: laApp ? (posDon.ma || '') : posDon.bill, ten_khach: posDon.ten || '', dien_thoai: posDon.sdt || '',
      pt: laApp ? '' : posDon.pt, ma_tham_chieu: laApp ? (posDon.ma || '') : (posDon.mtc || ''),
      items: JSON.stringify(posDon.mon.map(function (m) { return { item_code: m.item_code, qty: m.qty, rate: m.rate, tuy_chon: (m.tc || []).join(', '), ghi_chu: posGcGui(m, posMaAppHienTai()), combo: m.combo || '' }; })),
      giam_gia: giamTay, phi_ship: 0, quay: posQuay.ma || '', so_ban: posDon.so_ban || '',
      khach_no: (posDon.khach_no && posDon.khach_no.ma) || '',
      khach_ma: posDon.khach_ma || '',
      /* CHI gui ma chuong trinh, KHONG gui so tien giam - may chu tu tinh
         lai tu gio hang (anh Viet 11/08/2026). */
      ctkm_ap: JSON.stringify(posDon.ctkm || []),
      combo_ap: JSON.stringify(posDon.combo || []),
      ma_voucher: posDon.maVc || '',
      otp_km: otpKm || '',
      ghi_chu: (posDon.km ? 'KM: ' + posDon.km.ten + (posDon.ghi_chu ? '. ' : '') : '') + (posDon.ghi_chu || ''),
      xhd_mst: posDon.xhd_mo ? (posDon.xh.mst || '') : '',
      xhd_ten: posDon.xhd_mo ? (posDon.xh.ten || '') : '',
      xhd_dia_chi: posDon.xhd_mo ? (posDon.xh.dc || '') : '',
      xhd_email: posDon.xhd_mo ? (posDon.xh.email || '') : ''
    });
  } catch (e) { posDangLuu = false; busy(false); return toast((e && e.message) || 'Lưu hoá đơn lỗi, thử lại.', 4000); }
  posDangLuu = false;
  busy(false);
  var thu = (r && r.grand_total) || phaiThu;
  var laCK = !laApp && posDon.pt === 'Chuyển khoản';
  var thoi = !laApp && posDon.pt === 'Tiền mặt' && dua >= thu ? dua - thu : 0;
  var maCk = posDon.mtc || posDon.bill || '';
  /* Nguon phai doc TRUOC khi mo bill moi: posMoi() dat lai che_do ve
     "Tai cho", doc sau la don Mang ve lai ra ma QR cua nguon Tai cho. */
  var nguonCk = posNguonThuc();
  /* Giu ban sao de in bill ngay, truoc khi mo bill moi. */
  posBillVua = {
    name: (r && r.name) || '', bill: posDon.bill, mon: posDon.mon.slice(),
    tong: tong, giam: giam, giamTay: giamTay,
    kmAp: ((posDon.kmKq && posDon.kmKq.ap) || []).slice(),
    thu: thu, pt: laApp ? posDon.che_do : posDon.pt,
    quay: (posQuay && posQuay.ma) || '', nguon: nguonCk,
    ghi_chu: posDon.ghi_chu || '', ten: posDon.ten || '', so_ban: posDon.so_ban || '', tam_tinh: 0
  };
  posDon = posMoi();
  posHomNayTxt = null;
  /* Van la ma QR khach da quet luc nay, khong doi sang so phieu - de neu
     khach chua chuyen kip thi quet lai van ra dung noi dung. */
  if (laCK) return posQrSheet(maCk, thu, (r && r.name) || '', nguonCk);
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb" style="padding:22px 16px calc(env(safe-area-inset-bottom,0px) + 16px);text-align:center">' +
    '<div style="font-size:44px">✅</div>' +
    '<div style="font-size:19px;font-weight:700;margin:6px 0 2px">Đã thu ' + money(thu) + ' đ</div>' +
    (thoi ? '<div style="font-size:17px;color:#0f766e;font-weight:700">Thối khách ' + money(thoi) + ' đ</div>' : '') +
    '<div style="font-size:12.5px;color:#a0a6b4;margin-top:6px">' + h((r && r.name) || '') + ' · ghi sổ ngay tại quầy trong Hoá đơn hôm nay</div>' +
    '<div style="display:flex;gap:8px;margin-top:16px">' +
    '<button class="btn gh" data-in style="flex:1;margin:0">🖨 In hoá đơn</button>' +
    '<button class="btn" data-y style="flex:1;margin:0">🧾 Hoá đơn mới</button></div>' +
    (posCoNuoc(posBillVua.mon)
      ? '<div style="display:flex;gap:8px;margin-top:8px"><button class="btn gh" data-pm style="flex:1;margin:0">🧾 In phiếu làm món</button><button class="btn gh" data-tem style="flex:1;margin:0">🏷 In tem món</button></div>'
      : '') +
    '<button class="btn gh" data-ds style="margin-top:8px">📋 Về danh sách hoá đơn</button></div>';
  document.body.appendChild(ov);
  ov.onclick = function (e) {
    if (e.target.hasAttribute('data-in')) { posInBill(posBillVua); ov.remove(); go(scrPosDs, true); return; }
    if (e.target.hasAttribute('data-pm')) { posInPhieuMon(posBillVua); return; }
    if (e.target.hasAttribute('data-tem')) { posInTemLy(posBillVua); return; }
    if (e.target.hasAttribute('data-ds')) { ov.remove(); go(scrPosDs, true); return; }
    if (e.target === ov || e.target.hasAttribute('data-y')) { ov.remove(); go(scrPosQuay, true); }
  };
}


/* ---------- Bill quay: in 80mm, tam tinh, danh sach bill cua quay ----------
   Anh Viet 09/08/2026: build de thay the han Fabi tinh tien. Moi quay tu
   quan bill cua minh - tu xem, tu sua, tu xoa, tu ghi so tai cho, khong di
   vong qua man Doanh thu Sales cua ai het. */
var posBillVua = null;

/* Mau in kho 80mm, in qua trinh duyet (AirPrint / may in nhiet co driver).
   Logo den tren nen trang de hop in nhiet; thieu anh thi tu an, van in chu. */
async function posInBill(d) {
  /* Mo cua so TRUOC khi goi mang de giu user gesture (khoi bi chan popup).
     Bill that chua co link XHD thi tu xin: truoc day chi duong in lai tu
     chi tiet bill moi co QR, in ngay sau thu tien bi thieu (loi anh Viet
     bao 09/08) - gio moi duong in deu co. */
  var w = window.open('', '_blank');
  if (!w) return toast('Trình duyệt chặn cửa sổ in. Cho phép popup rồi bấm lại.', 4000);
  if (!d.tam_tinh && !d.huy && d.name && !d.xhd_url) {
    try { var lk0 = await api('vagabond.ban_hang.pos_link_xhd', { name: d.name }); d.xhd_url = (lk0 && lk0.url) || ''; } catch (e0) { }
  }
  var q = (CFGBH || {}).qr_quay || {};
  var mon = d.mon || [];
  var gio = new Date();
  var hs = function (n) { return (n < 10 ? '0' : '') + n; };
  var lucIn = hs(gio.getHours()) + ':' + hs(gio.getMinutes()) + ' ' + hs(gio.getDate()) + '/' + hs(gio.getMonth() + 1) + '/' + gio.getFullYear();
  var rows = mon.map(function (m) {
    return '<tr><td class="t">' + h(m.ten) + '</td></tr>' +
      /* Mon nao thuoc combo nao thi ghi ngay duoi ten mon: khach doc bill
         biet minh dang mua bo combo, nguoi di lay mon biet gom du bo (anh
         Viet 11/08/2026). Ma combo KHONG in, chi in ten. */
      (m.combo ? '<tr><td style="font-size:10px">&nbsp;&nbsp;&#9733; ' + h(m.combo) + '</td></tr>' : '') +
      ((m.tc || []).length ? '<tr><td style="font-size:10px">&nbsp;&nbsp;[' + h(m.tc.join(', ')) + ']</td></tr>' : '') +
      '<tr><td class="s">' + money(m.qty) + ' x ' + money(m.rate) + '<span class="r">' + money(m.qty * m.rate) + '</span></td></tr>';
  }).join('');
  var qrKhoi = '';
  if (d.tam_tinh) {
    /* Phieu tam tinh in kem QR THANH TOAN: khach xac nhan mon xong quet
       chuyen luon cung duoc, SePay khop theo ma bill. */
    var uq = posQrUrl(posNoiDungCk(d.bill, d.quay), d.thu, d.nguon || '');
    if (uq) qrKhoi = '<div class="qr"><img src="' + uq + '"><div>Quét để chuyển khoản ' + money(d.thu) + ' đ<br>Nội dung: <b>' + h(posNoiDungCk(d.bill, d.quay)) + '</b></div></div>';
  } else if (d.xhd_url) {
    /* Bill that in kem QR XUAT HOA DON: khach can hoa don cong ty thi quet,
       tu dien thong tin, ERP map vao don, cuoi ngay tu day m-invoice. */
    var ulink = location.origin + d.xhd_url;
    qrKhoi = '<div class="qr"><img src="https://api.qrserver.com/v1/create-qr-code/?size=190x190&data=' + encodeURIComponent(ulink) + '">' +
      '<div><b>Quý khách vui lòng quét mã QR (hiệu lực 2 tiếng)<br>để nhập thông tin xuất hoá đơn.</b><br>Hoá đơn điện tử gửi về email trong ngày.</div></div>';
  }
  /* MOT lenh in ra MOT lien (anh Viet 10/08/2026). Truoc day in lien
     nhau hai lien roi bat nhan vien cam keo cat giua - khong thong minh.
     Can lien thu hai thi bam In lai them mot lan, may tu ra to nua. */
  var lien2 = '';
  w.document.write('<html><head><meta charset="utf-8"><title>' + h(d.bill || d.name || 'Hoá đơn') + '</title><style>' +
    '@page{size:80mm auto;margin:0}' +
    '*{margin:0;padding:0;box-sizing:border-box}' +
    'body{width:72mm;margin:0 auto;font-family:Arial,sans-serif;font-size:11.5px;color:#000;padding:4mm 0 6mm}' +
    '.lg{display:block;width:44mm;margin:0 auto 2mm}' +
    'h1{font-size:13px;text-align:center;letter-spacing:.06em}' +
    '.ph{text-align:center;font-size:10px;line-height:1.45}' +
    '.tt{font-size:14px;font-weight:bold;text-align:center;margin:3mm 0 1mm;letter-spacing:.08em}' +
    'hr{border:0;border-top:1px dashed #000;margin:2mm 0}' +
    'table{width:100%;border-collapse:collapse}' +
    'td.t{font-weight:bold;padding-top:1.2mm}' +
    'td.s{font-size:11px;padding-bottom:.6mm}' +
    '.r{float:right;font-weight:bold}' +
    '.d{display:flex;justify-content:space-between;font-size:11.5px;padding:.4mm 0}' +
    '.d b.to{font-size:15px}' +
    '.gc{font-size:11px;border:1px solid #000;padding:1.5mm;margin-top:1.5mm}' +
    '.qr{text-align:center;margin-top:3mm;font-size:10px;line-height:1.5}' +
    '.qr img{width:34mm;height:34mm;display:block;margin:0 auto 1mm}' +
    '.ft{text-align:center;font-size:10px;margin-top:3mm;line-height:1.5}' +
    '</style></head><body>' +
    '<img class="lg" src="' + location.origin + '/files/logo-in.png" onerror="this.style.display=\'none\';document.getElementById(\'lgt\').style.display=\'block\'">' +
    '<h1 id="lgt" style="display:none">THE VAGABOND P&Acirc;TISSERIE</h1>' +
    '<div class="ph">' + h((posQuay && posQuay.ten) || '') + '<br>' + h((posQuay && posQuay.phu) || '') + '</div>' +
    '<div class="tt">' + (d.huy ? 'BILL ĐÃ HUỶ' : (d.tam_tinh ? 'PHIẾU TẠM TÍNH' : 'HOÁ ĐƠN BÁN HÀNG')) + '</div>' +
    /* Bill da huy in ra phai nhin la biet ngay: khong dong dau thi to giay
       giong het bill that, khach cam nham va thu ngan doi soat cung nham. */
    (d.huy
      ? '<div style="border:2px solid #000;text-align:center;font-weight:bold;font-size:13px;padding:2mm;margin:1.5mm 0;letter-spacing:.1em">' +
        'BILL NÀY ĐÃ HUỶ - KHÔNG CÓ GIÁ TRỊ THANH TOÁN' +
        (d.huy_ly_do ? '<div style="font-size:10px;font-weight:normal;letter-spacing:0;margin-top:1mm">Lý do: ' + h(d.huy_ly_do) + '</div>' : '') +
        '</div>'
      : '') +

    '<div class="d"><span>Mã bill: <b>' + h(d.bill || '') + '</b></span><span>' + h(d.name || '') + '</span></div>' +
    '<div class="d"><span>Thu ngân: ' + h(S.me.full_name || String(S.user).split('@')[0]) + '</span><span>' + lucIn + '</span></div>' +
    (d.so_ban ? '<div class="d"><span style="font-size:14px;font-weight:bold">Bàn: ' + h(d.so_ban) + '</span></div>' : '') +
    (d.ten ? '<div class="d"><span>Khách: ' + h(d.ten) + '</span></div>' : '') +
    '<hr><table>' + rows + '</table><hr>' +
    '<div class="d"><span>Tạm tính</span><b>' + money(d.tong) + '</b></div>' +
    /* Tach tung chuong trinh mot dong: khach doc bill la biet duoc giam
       nhung gi, khoi ra quay hoi lai (anh Viet 11/08/2026). Ma combo
       KHONG in - chi in ten combo cho nguoi doc, con mon thi da nam
       thanh tung dong o tren roi. */
    ((d.kmAp || []).map(function (a) {
      return '<div class="d"><span>' + h(a.ten) + '</span><b>-' + money(a.giam) + '</b></div>';
    }).join('')) +
    (d.giamTay ? '<div class="d"><span>Giảm giá</span><b>-' + money(d.giamTay) + '</b></div>' : '') +
    '<div class="d"><span style="font-size:13px;font-weight:bold">' + (d.tam_tinh ? 'TẠM TÍNH' : 'PHẢI THU') + '</span><b class="to">' + money(d.thu) + ' đ</b></div>' +
    (d.pt && !d.tam_tinh ? '<div class="d"><span>Thanh toán</span><b>' + h(d.pt) + '</b></div>' : '') +
    (d.ghi_chu ? '<div class="gc">Ghi chú: ' + h(d.ghi_chu) + '</div>' : '') +
    qrKhoi +
    '<div class="ft">' + (d.tam_tinh ? 'Phiếu giữ món, chưa phải hoá đơn thanh toán.' : 'Cảm ơn quý khách!') + '<br>thevagabondpatisserie.com</div>' +
    lien2 +
    '<script>window.onload=function(){setTimeout(function(){window.print()},1100)}<' + '/script>' +
    '</body></html>');
  w.document.close();
}

/* In phieu tam tinh: luu bill tam tinh vao so (giu mon, chua thanh toan)
   roi in ngay. Cashier sau nay vao Bill hom nay chot, thu tien, ghi so. */
async function posInTamTinh() {
  posDoc();
  if (!posDon.mon.length) return toast('Hoá đơn chưa có món nào.');
  var thieuGia = posDon.mon.filter(function (m) { return !m.rate; });
  if (thieuGia.length) return toast('Món ' + thieuGia[0].ten + ' chưa có giá trong danh mục.');
  var giamTay = posSoTien(posDon.giam);
  var tong = posDon.mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0);
  await posTinhKm();
  var giam = giamTay + ((posDon.kmKq && posDon.kmKq.tong_giam) || 0);
  var thu = Math.max(0, tong - giam);
  var ok = await confirmSheet('In phiếu tạm tính ' + money(thu) + ' đ',
    'Hoá đơn được lưu TẠM TÍNH - giữ món, chưa tính doanh thu.\nKhách thanh toán xong thì vào Hoá đơn hôm nay bấm Chốt.', 'Lưu và in phiếu');
  if (!ok) return;
  busy(true);
  var r;
  try {
    r = await api('vagabond.ban_hang.tao_don_tay', {
      ngay: today(), nguon: posNguonThuc(), ma_don: posDon.bill,
      ten_khach: posDon.ten || '', dien_thoai: posDon.sdt || '',
      items: JSON.stringify(posDon.mon.map(function (m) { return { item_code: m.item_code, qty: m.qty, rate: m.rate, tuy_chon: (m.tc || []).join(', '), ghi_chu: posGcGui(m, posMaAppHienTai()), combo: m.combo || '' }; })),
      giam_gia: giamTay, phi_ship: 0, quay: posQuay.ma || '', so_ban: posDon.so_ban || '',
      khach_no: (posDon.khach_no && posDon.khach_no.ma) || '',
      khach_ma: posDon.khach_ma || '',
      ctkm_ap: JSON.stringify(posDon.ctkm || []),
      combo_ap: JSON.stringify(posDon.combo || []),
      ma_voucher: posDon.maVc || '',
      ghi_chu: (posDon.km ? 'KM: ' + posDon.km.ten + (posDon.ghi_chu ? '. ' : '') : '') + (posDon.ghi_chu || ''), tam_tinh: 1
    });
  } catch (e) { busy(false); return toast((e && e.message) || 'Lưu lỗi, thử lại.', 4000); }
  busy(false);
  posBillVua = { name: (r && r.name) || '', bill: posDon.bill, mon: posDon.mon.slice(), tong: tong, giam: giam, giamTay: giamTay, kmAp: ((posDon.kmKq && posDon.kmKq.ap) || []).slice(), thu: thu, pt: '', quay: (posQuay && posQuay.ma) || '', nguon: posNguonThuc(), ghi_chu: posDon.ghi_chu || '', ten: posDon.ten || '', so_ban: posDon.so_ban || '', tam_tinh: 1 };
  posInBill(posBillVua);
  posDon = posMoi();
  posHomNayTxt = null;
  toast('Đã lưu hoá đơn tạm tính ' + ((r && r.name) || ''));
  go(scrPosDs, true);
}

/* ---------- Bill hom nay cua quay: xem - sua - xoa - chot - ghi so ---------- */
function posChipBill(r) {
  /* Chip pastel to ro nhu ben danh sach bill Doanh thu Sales
     (anh Viet 09/08: "lam chip the nay moi dep"). */
  var c = [];
  var the = function (bg, fg, chu) { return '<span style="display:inline-block;background:' + bg + ';color:' + fg + ';font-size:12px;font-weight:700;border-radius:999px;padding:3px 10px;margin:3px 5px 0 0;white-space:nowrap">' + chu + '</span>'; };
  if (r.vgb_huy) c.push(the('#fee2e2', '#991b1b', '🚫 Đã huỷ'));
  if (r.vgb_lan_sua) c.push(the('#fef3c7', '#92400e', '✏️ Đã sửa ' + r.vgb_lan_sua + ' lần'));
  if (r.docstatus === 1) c.push(the('#dcfce7', '#166534', '✅ Đã ghi sổ'));
  else if (r.vgb_tam_tinh) c.push(the('#fef3c7', '#92400e', '🕐 Tạm tính'));
  else c.push(the('#e5e7eb', '#374151', '📄 Chưa ghi sổ'));
  if (r.vgb_pt_thanh_toan) c.push(the('#e0f2fe', '#075985', h(r.vgb_pt_thanh_toan)));
  if ((r.vgb_pt_thanh_toan || '') === 'Chuyển khoản') {
    c.push(r.sepay_du ? the('#dcfce7', '#166534', 'SePay ✓ đủ tiền') : the('#fee2e2', '#991b1b', '⏳ Chờ tiền về'));
  }
  if (r.custom_hddt_so || (r.custom_hddt_trang_thai || '').trim()) {
    var mhd = DS_MAU_HD[r.custom_hddt_trang_thai] || ['#ede9fe', '#5b21b6'];
    c.push(the(mhd[0], mhd[1],
      (r.custom_hddt_so ? 'HĐ ' + h(r.custom_hddt_so) : 'HĐĐT') +
      (r.custom_hddt_trang_thai ? ' · ' + h(r.custom_hddt_trang_thai) : '')));
  }
  else if (r.vgb_xhd_mst) c.push(the('#fef9c3', '#854d0e', '🧾 Chờ xuất HĐ công ty'));
  if (r.discount_amount) c.push(the('#ffedd5', '#9a3412', '🎟 Giảm ' + money(r.discount_amount) + ' đ'));
  if (r.trung_ma) c.push(the('#fee2e2', '#991b1b', '⚠ Trùng mã trong ngày'));
  if (r.vgb_ghi_chu) c.push(the('#e0f7fa', '#0369a1', '📝 ' + h(String(r.vgb_ghi_chu).slice(0, 30))));
  return c.join('');
}
async function scrPosDs() {
  if (!posQuay) return go(scrPosChonQuay, true);
  if (!posDsNgay) posDsNgay = today();
  var laHomNay = posDsNgay === today();
  var tieuDe = (laHomNay ? 'Hoá đơn hôm nay' : 'Hoá đơn ' + posDsNgay.split('-').reverse().join('/')) + ' · ' + (posQuay.ma || '');
  frame(tieuDe, '<div class="emp"><div class="e1">⏳</div><div>Đang tải hoá đơn...</div></div>');
  var kq;
  try { kq = await api('vagabond.ban_hang.pos_ds_bill', { quay: posQuay.ma || '', ngay: posDsNgay }); }
  catch (e) { frame(tieuDe, '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var ds = (kq && kq.bill) || [];
  /* Bill da huy van nam trong danh sach de xem lai, nhung KHONG duoc cong
     vao tong: man Chot ca ben may chu da loc no ra roi, o day quen loc la
     hai con so lech nhau, thu ngan dem tien thay thieu ma khong hieu vi sao. */
  var dsTien = ds.filter(function (r) { return !r.vgb_huy; });
  var tong = dsTien.reduce(function (t, r) { return t + (r.grand_total || 0); }, 0);
  var soHuy = ds.length - dsTien.length;
  /* Tong theo phuong thuc de cashier doi soat nhanh ma khong can mo chot ca. */
  var ptTong = {};
  dsTien.forEach(function (r) {
    if (r.vgb_tam_tinh) return;
    var p = r.vgb_pt_thanh_toan || r.custom_nguon || 'Khác';
    ptTong[p] = (ptTong[p] || 0) + (r.grand_total || 0);
  });
  var ptTxt = Object.keys(ptTong).map(function (p) { return h(p) + ' ' + money(ptTong[p]) + ' đ'; }).join(' · ');
  /* Lich chon ngay: xem lai bill ngay qua khu (anh Viet 09/08). */
  var html = '<div class="card" style="padding:12px 14px;display:flex;align-items:center;gap:12px">' +
    '<div style="font-weight:600;white-space:nowrap">' + posNgayVn(posDsNgay) + '</div>' +
    '<input type="date" class="hin" id="posDsDate" value="' + posDsNgay + '" max="' + today() + '" style="flex:1;margin:0">' +
    chipNgay('data-pdbuoc') + '</div>';
  html += '<div class="card" style="padding:12px 14px;display:flex;align-items:center;gap:8px">' +
    '<div style="flex:1;min-width:0"><b>' + dsTien.length + ' hoá đơn · ' + money(tong) + ' đ</b>' +
    (soHuy ? '<span style="color:#991b1b;font-size:12.5px;font-weight:700;margin-left:8px">+ ' + soHuy + ' đã huỷ</span>' : '') +
    '<div style="font-size:12px;color:#5b6472">' + (ptTxt || 'Chưa có hoá đơn doanh thu') + '</div>' +
    '<div style="font-size:12px;color:#98a2b3">Hoá đơn của quầy ' + h(posQuay.ten) + ', mỗi quầy tự quản hoá đơn của mình.</div></div>' +
    (laHomNay ? '<button class="btn gh" id="posDsMoi" style="margin:0;padding:9px 11px;font-size:13px;flex:none">🧾 Hoá đơn mới</button>' : '') +
    '<button class="btn" id="posDsChotCa" style="margin:0;padding:9px 11px;font-size:13px;flex:none">🧮 Chốt ca</button></div>';
  /* Bo loc hai tang giong man Sales: tinh trang x nguon/phuong thuc.
     Quan ly ca soat cuoi ngay chi can bam vai chip la ra dung nhom can xem
     (anh Viet 10/08/2026). */
  var PTT = [
    { k: 'tat_ca', nhan: 'Tất cả', loc: function () { return true; } },
    { k: 'chua_ghi', nhan: '📄 Chưa ghi sổ', loc: function (r) { return r.docstatus === 0 && !r.vgb_tam_tinh && !r.vgb_huy; } },
    { k: 'da_ghi', nhan: '✅ Đã ghi sổ', loc: function (r) { return r.docstatus === 1; } },
    { k: 'tam_tinh', nhan: '🕐 Tạm tính', loc: function (r) { return !!r.vgb_tam_tinh && !r.vgb_huy; } },
    { k: 'da_huy', nhan: '🚫 Đã huỷ', loc: function (r) { return !!r.vgb_huy; } },
    { k: 'da_sua', nhan: '✏️ Đã sửa', loc: function (r) { return !!r.vgb_lan_sua; } },
    { k: 'cho_tien', nhan: '⏳ Chờ tiền về', loc: function (r) { return (r.vgb_pt_thanh_toan || '') === 'Chuyển khoản' && !r.sepay_du; } },
    { k: 'du_tien', nhan: '💰 SePay đã đủ tiền', loc: function (r) { return !!r.sepay_du; } },
    { k: 'xhd_cty', nhan: '🏢 Xuất hoá đơn công ty', loc: function (r) { return !!r.vgb_xhd_mst; } },
    { k: 'chua_hddt', nhan: '📌 Chưa có hoá đơn điện tử', loc: function (r) { return r.docstatus === 1 && !!r.vgb_xhd_mst && !r.custom_hddt_so; } },
    { k: 'giam', nhan: '🎟 Có giảm giá', loc: function (r) { return !!r.discount_amount; } },
    { k: 'ban', nhan: '🪑 Có số bàn', loc: function (r) { return !!r.vgb_so_ban; } },
    { k: 'ghi_chu', nhan: '📝 Có ghi chú', loc: function (r) { return !!r.vgb_ghi_chu; } },
    { k: 'trung', nhan: '⚠ Trùng mã trong ngày', loc: function (r) { return !!r.trung_ma; } }
  ];
  var PNG = locNguonPt(ds);
  var PHD = locHddt();
  var pTt = locTim(PTT, posLocTt), pNg = locTim(PNG, posLocNg), pHd = locTim(PHD, posLocHd);
  posLocTt = pTt.k; posLocNg = pNg.k; posLocHd = pHd.k;
  html += '<div class="card" style="padding:10px 12px;display:flex;flex-direction:column;gap:7px">' +
    locHang(PTT, posLocTt, 'data-ptt', ds) +
    locHang(PNG, posLocNg, 'data-png', ds.filter(pTt.loc)) +
    locHang(PHD, posLocHd, 'data-phd', ds.filter(pTt.loc)) + '</div>';
  var dsL = ds.filter(function (r) { return pTt.loc(r) && pNg.loc(r) && pHd.loc(r); });
  html += locKhoiTong(dsL, [
    posLocTt === 'tat_ca' ? '' : pTt.nhan, pNg.k ? pNg.nhan : '', pHd.k ? pHd.nhan : ''
  ].filter(Boolean).join(' · '));
  html += '<div class="card" style="margin-top:10px">';
  if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">🧾</div><div>' + (laHomNay ? 'Hôm nay chưa có hoá đơn nào.' : 'Ngày này không có hoá đơn nào.') + '</div></div>';
  else if (!dsL.length) html += '<div class="emp" style="padding:24px"><div class="e1">✅</div><div>Không có hoá đơn nào thuộc nhóm <b>' + pTt.nhan + (pNg.k ? ' · ' + pNg.nhan : '') + '</b>.</div></div>';
  dsL.forEach(function (r) {
    var gio = String(r.creation || '').slice(11, 16);
    var phu = [gio, h(r.custom_nguon || '')];
    if (r.total_qty) phu.push(money(r.total_qty) + ' món');
    /* "Ban cho nguoi tieu dung" la gia tri mac dinh, khong phai cong ty
       that - hien len moi dong chi gay nhieu. */
    if (r.vgb_xhd_ten && r.vgb_xhd_ten !== 'Bán cho người tiêu dùng') phu.push('🏢 ' + h(String(r.vgb_xhd_ten).slice(0, 26)));
    html += '<div class="hub" data-bill="' + h(r.name) + '"><div class="hi">🧾</div>' +
      '<div class="ht"><div class="h1">' + h(r.custom_pancake_display_id || r.name) + ' · ' + money(r.grand_total) + ' đ</div>' +
      '<div class="h2">' + phu.join(' · ') + '</div>' +
      '<div>' + posChipBill(r) + '</div></div>' +
      '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
  });
  html += '</div>';
  var b = frame(tieuDe, html);
  var oD = document.getElementById('posDsDate');
  if (oD) oD.onchange = function () { posDsNgay = oD.value || today(); posLocTt = 'tat_ca'; posLocNg = ''; go(scrPosDs, true); };
  veODate('posDsDate');
  b.addEventListener('click', function (e) {
    var t = e.target.closest('[data-pdbuoc]'); if (!t) return;
    var bu = +t.getAttribute('data-pdbuoc');
    var moi = bu ? ngayCong(posDsNgay || today(), bu) : today();
    if (moi > today()) return toast('Chưa tới ngày đó.');
    posDsNgay = moi; posLocTt = 'tat_ca'; posLocNg = '';
    go(scrPosDs, true);
  });
  b.onclick = function (e) {
    var ct = e.target.closest('[data-ptt]');
    if (ct) { posLocTt = ct.getAttribute('data-ptt'); return go(scrPosDs, true); }
    ct = e.target.closest('[data-png]');
    if (ct) { posLocNg = ct.getAttribute('data-png'); return go(scrPosDs, true); }
    ct = e.target.closest('[data-phd]');
    if (ct) { posLocHd = ct.getAttribute('data-phd'); return go(scrPosDs, true); }
    if (e.target.id === 'posDsMoi') return go(scrPosQuay);
    if (e.target.id === 'posDsChotCa') return go(scrPosChotCa);
    var r = e.target.closest('[data-bill]');
    if (r) go(function () { scrPosBill(r.dataset.bill); });
  };
}
/* Chi tiet hoa don quay. Anh Viet 09/08/2026: hoa don la tien that da thu
   cua khach nen mac dinh KHOA HET - xem thi duoc, sua thi phai bam nut Sua
   hoa don va co ma OTP cua quan ly. Rieng hoa don con TAM TINH (khach chua
   tra tien) thi cashier van chot binh thuong, do la nghiep vu hang ngay. */
var posSua = null; /* {name, otp, mon[], giam, pt, mtc, ghi_chu, so_ban, xh} */
async function scrPosBill(name) {
  frame('Hoá đơn ' + name, '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('frappe.client.get', { doctype: 'Sales Invoice', name: name }); }
  catch (e) { frame('Hoá đơn', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được hoá đơn') + '</div></div>'); return; }
  await cfgBanHang();
  var tamTinh = !!d.vgb_tam_tinh, nhap = d.docstatus === 0;
  var maBill = d.custom_pancake_display_id || '';
  var dsPt = ptTheoNguon(d.custom_nguon || '');
  var daKy = !!d.custom_hddt_so;
  if (posSua && posSua.name !== name) posSua = null;
  var suaMo = !!posSua;

  function monTuDoc() {
    return (d.items || []).map(function (m) {
      var tc = [];
      var mo = /\[([^\]]+)\]/.exec(String(m.description || ''));
      if (mo) tc = String(mo[1]).split(',').map(function (x) { return x.trim(); }).filter(Boolean);
      /* Dong bat dau bang dau ※ la GHI CHU RIENG cua mon do. */
      var gc = '';
      var mg = /\u203b\s*(.+)/.exec(String(m.description || ''));
      if (mg) gc = String(mg[1]).trim();
      /* Dong bat dau bang dau ◈ la TEN COMBO ma mon do thuoc ve - phai doc
         lai duoc thi in lai bill cu moi con thay combo (anh Viet 11/08). */
      var cb = '';
      var mc = /\u25c8\s*(.+)/.exec(String(m.description || ''));
      if (mc) cb = String(mc[1]).trim();
      return { item_code: m.item_code, ten: m.item_name || m.item_code, qty: m.qty, rate: m.rate, tc: tc, gc: gc, combo: cb };
    });
  }
  var mon = suaMo ? posSua.mon : monTuDoc();
  var giam = suaMo ? posSoTien(posSua.giam) : (d.discount_amount || 0);
  var tongMon = mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0);
  var phaiThu = suaMo ? Math.max(0, tongMon - giam) : d.grand_total;
  var soBan = suaMo ? posSua.so_ban : (d.vgb_so_ban || '');

  /* ----- the dau: ma, chip trang thai, so ban ----- */
  var html = '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between"><b style="font-size:16px">' + h(maBill || d.name) + '</b><span style="color:#98a2b3;font-size:12px">' + h(d.name) + '</span></div>' +
    '<div style="font-size:12px;color:#6b7280">' + h(d.custom_nguon || '') + ' · ' + h(String(d.creation || '').slice(0, 16)) +
    (d.vgb_quay ? ' · quầy ' + h(d.vgb_quay) : '') + '</div>' +
    '<div style="margin-top:4px">' + posChipBill({
      docstatus: d.docstatus, vgb_tam_tinh: d.vgb_tam_tinh, vgb_pt_thanh_toan: d.vgb_pt_thanh_toan,
      sepay_du: 0, custom_hddt_so: d.custom_hddt_so, vgb_xhd_mst: d.vgb_xhd_mst,
      discount_amount: d.discount_amount, vgb_ghi_chu: '',
      vgb_huy: d.vgb_huy, vgb_lan_sua: d.vgb_lan_sua
    }) +
    (soBan ? '<span style="display:inline-block;background:#fef3c7;color:#92400e;font-size:12px;font-weight:700;border-radius:999px;padding:3px 10px;margin:3px 5px 0 0">🪑 Bàn ' + h(soBan) + '</span>' : '') +
    '</div></div>';

  /* Bill da huy: noi thang o ngay dau man, khong de thu ngan doc het bang
     mon roi moi phat hien minh dang xem mot to da bo. */
  if (d.vgb_huy) {
    html += '<div class="card" style="padding:12px 14px;margin-top:10px;background:#fef2f2;border:1px solid #fecaca">' +
      '<b style="font-size:14.5px;color:#991b1b">🚫 Bill này đã huỷ</b>' +
      '<div style="font-size:13px;color:#7f1d1d;line-height:1.6;margin-top:3px">' +
      'Lý do: ' + h(d.vgb_huy_ly_do || 'không ghi') +
      (d.vgb_huy_boi ? '<br>Người huỷ: ' + h(d.vgb_huy_boi) : '') +
      (d.vgb_huy_luc ? ' · ' + h(String(d.vgb_huy_luc).slice(0, 16)) : '') +
      '<br>Bill vẫn nằm nguyên trong hệ thống để đối chiếu, chỉ không tính vào doanh thu.' +
      '</div></div>';
  }

  /* ----- bang mon ----- */
  var suaMon = suaMo && nhap; /* hoa don da ghi so thi khong doi mon duoc */
  html += '<div class="card" style="padding:6px 14px;margin-top:10px">';
  if (!mon.length) html += '<div style="padding:14px 0;color:#a0a6b4">Hoá đơn không còn món nào.</div>';
  mon.forEach(function (m, i) {
    var NUT = 'height:34px;width:34px;flex:none;border:1px solid #e5e7eb;background:#fff;border-radius:9px;font-size:17px;line-height:1;padding:0;cursor:pointer';
    html += '<div style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
      '<div style="flex:1;min-width:0"><div style="font-size:14px">' + h(m.ten) + '</div>' +
      ((m.tc || []).length ? '<div style="color:#0f766e;font-size:12px;margin-top:2px">⚙ ' + h(m.tc.join(', ')) + '</div>' : '') + '</div>' +
      (suaMon
        ? '<button data-sbot="' + i + '" style="' + NUT + '">&minus;</button>' +
          '<b style="min-width:20px;text-align:center">' + money(m.qty) + '</b>' +
          '<button data-scong="' + i + '" style="' + NUT + '">+</button>' +
          '<b style="min-width:66px;text-align:right">' + money(m.qty * m.rate) + '</b>' +
          '<button data-sxoa="' + i + '" style="' + NUT + ';color:#b3261e">✕</button>'
        : '<b style="white-space:nowrap">x' + money(m.qty) + '</b><b style="min-width:76px;text-align:right">' + money(m.qty * m.rate) + '</b>') +
      '</div>';
  });
  if (suaMon) html += '<div style="padding:9px 0"><button class="btn gh" id="pbThemMon" style="width:100%;margin:0">➕ Thêm món</button></div>';
  if (giam) html += '<div style="display:flex;justify-content:space-between;padding:7px 0;color:#b45309"><span>Giảm giá</span><b>-' + money(giam) + '</b></div>';
  html += '<div style="display:flex;justify-content:space-between;padding:9px 0;font-size:16px"><b>' + (tamTinh ? 'TẠM TÍNH' : 'PHẢI THU') + '</b><b>' + money(phaiThu) + ' đ</b></div></div>';

  /* ----- khoi thong tin xuat hoa don khach da dien ----- */
  var coXhd = d.vgb_xhd_mst && String(d.vgb_xhd_mst).trim();
  html += '<div class="sec">Thông tin xuất hoá đơn</div>';
  if (suaMo) {
    html += '<div class="card" style="padding:12px 14px;display:grid;gap:9px">' +
      '<input class="tin" id="pbXTen" placeholder="Tên công ty trên hoá đơn" value="' + h(posSua.xh.ten || '') + '">' +
      '<div style="display:flex;gap:8px"><input class="tin" id="pbXMst" inputmode="numeric" placeholder="Mã số thuế" value="' + h(posSua.xh.mst || '') + '" style="flex:1">' +
      '<button class="btn gh" id="pbXTra" style="margin:0;flex:0 0 34%">🔍 Tra MST</button></div>' +
      '<input class="tin" id="pbXDc" placeholder="Địa chỉ công ty" value="' + h(posSua.xh.dc || '') + '">' +
      '<input class="tin" id="pbXMail" placeholder="Email nhận hoá đơn điện tử" value="' + h(posSua.xh.email || '') + '"></div>';
  } else if (coXhd) {
    var dongX = function (nhan, gt) {
      return '<div style="display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid #f0f2f6">' +
        '<span style="color:#6b7280;font-size:13px;flex:none">' + nhan + '</span>' +
        '<b style="font-size:13.5px;text-align:right;word-break:break-word">' + h(gt || '-') + '</b></div>';
    };
    html += '<div class="card" style="padding:6px 14px">' +
      dongX('Tên công ty', d.vgb_xhd_ten) + dongX('Mã số thuế', d.vgb_xhd_mst) +
      dongX('Địa chỉ', d.vgb_xhd_dia_chi) + dongX('Email nhận', d.vgb_xhd_email) +
      '<div style="padding:8px 0;font-size:12.5px;color:' + (daKy ? '#15803d' : '#b45309') + '">' +
      (daKy ? '✅ Đã phát hành hoá đơn điện tử số ' + h(d.custom_hddt_so) : '⏳ Chờ 23h30 máy đẩy sang m-invoice ký và gửi email cho khách') + '</div></div>';
  } else {
    html += '<div class="card" style="padding:12px 14px;font-size:13.5px;color:#6b7280;line-height:1.6">' +
      'Khách chưa gửi thông tin xuất hoá đơn. Khách quét mã QR cuối hoá đơn giấy để tự điền (mã có hiệu lực 2 tiếng), ' +
      'hoặc nhân viên bấm <b>Sửa hoá đơn</b> để điền hộ.</div>';
  }

  /* ----- thanh toan ----- */
  var choChon = suaMo || (nhap && tamTinh); /* tam tinh la nghiep vu chot binh thuong */
  var PB_PT = suaMo ? (posSua.pt || d.vgb_pt_thanh_toan || '') : (d.vgb_pt_thanh_toan || '');
  html += '<div class="sec">' + (tamTinh && nhap && !suaMo ? 'Khách thanh toán bằng gì?' : 'Thanh toán') + '</div>';
  if (choChon) {
    html += '<div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
      '<div id="pbPt" style="display:grid;grid-template-columns:1fr 1fr;gap:8px">' + posNutPt(dsPt, PB_PT) + '</div>' +
      '<div id="pbQr"></div>' +
      '<input class="tin" id="pbMtc" placeholder="Mã tham chiếu (biên lai thẻ, mã giao dịch...)" value="' + h((suaMo ? posSua.mtc : d.vgb_ma_tham_chieu) || '') + '">' +
      (suaMo ? '<input class="tin" id="pbGiam" inputmode="numeric" placeholder="Giảm giá cả hoá đơn (đ)" value="' + (giam ? money(giam) : '') + '">' : '') +
      '<input class="tin" id="pbGhiChu" placeholder="Ghi chú hoá đơn" value="' + h((suaMo ? posSua.ghi_chu : d.vgb_ghi_chu) || '') + '">' +
      (suaMo && d.custom_nguon === 'Tại chỗ - Trần Cao Vân' || suaMo && String(d.custom_nguon || '').indexOf('Tại chỗ') === 0
        ? '<input class="tin" id="pbBan" placeholder="Số bàn" value="' + h(soBan) + '">' : '') +
      '</div>';
  } else {
    /* KHOA: chi doc, muon doi phai bam Sua hoa don + ma OTP quan ly */
    html += '<div class="card" style="padding:12px 14px">' +
      '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">' +
      '<span style="display:inline-block;background:#e0f2fe;color:#075985;font-size:13px;font-weight:700;border-radius:999px;padding:5px 13px">' + h(d.vgb_pt_thanh_toan || 'Chưa chọn') + '</span>' +
      (d.vgb_ma_tham_chieu ? '<span style="display:inline-block;background:#ede9fe;color:#5b21b6;font-size:13px;font-weight:700;border-radius:999px;padding:5px 13px">Mã ' + h(d.vgb_ma_tham_chieu) + '</span>' : '') +
      '</div>' +
      (d.vgb_ghi_chu ? '<div style="font-size:13.5px;margin-top:10px">📝 ' + h(d.vgb_ghi_chu) + '</div>' : '') +
      '<div style="font-size:12.5px;color:#6b7280;margin-top:10px;line-height:1.6">🔒 Hoá đơn đã thu tiền của khách nên khoá lại. ' +
      'Cần sửa thì bấm <b>Sửa hoá đơn</b> rồi nhập mã OTP xin của quản lý ca.</div></div>';
  }

  /* ----- nut duoi chan man ----- */
  var foot;
  if (d.vgb_huy) {
    foot = '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="pbIn" style="flex:1;margin:0">🖨 In</button>' +
      (coQuyenHuy() ? '<button class="btn gh" id="pbGoHuy" style="flex:1;margin:0">↩️ Gỡ dấu huỷ</button>' : '') +
      '</div>';
  } else if (suaMo) {
    foot = '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="pbHuySua" style="flex:0 0 34%;margin:0">✕ Thôi sửa</button>' +
      '<button class="btn" id="pbLuuSua" style="flex:1;margin:0">💾 Lưu thay đổi</button></div>';
  } else {
    foot = '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="pbIn" style="flex:0 0 30%;margin:0">🖨 In</button>' +
      (nhap
        ? (tamTinh
          ? '<button class="btn" id="pbChot" style="flex:1;margin:0">✅ Chốt hoá đơn - khách đã trả</button>'
          : '<button class="btn" id="pbGhiSo" style="flex:1;margin:0">📒 Ghi sổ tại quầy</button>')
        : '<div style="flex:1;display:flex;align-items:center;justify-content:center;color:#15803d;font-weight:700">✅ Đã ghi sổ</div>') +
      '</div>' +
      (posCoNuoc(d.items || [])
        ? '<div style="display:flex;gap:8px;margin-top:8px"><button class="btn gh" id="pbPhieuMon" style="flex:1;margin:0">🧾 In phiếu làm món</button><button class="btn gh" id="pbTemLy" style="flex:1;margin:0">🏷 In tem món</button></div>'
        : '') +
      '<div style="display:flex;gap:8px;margin-top:8px">' +
      '<button class="btn gh" id="pbSua" style="flex:1;margin:0">✏️ Sửa hoá đơn</button>' +
      (nhap ? '<button class="btn gh" id="pbXoa" style="flex:1;margin:0;color:#b3261e;border-color:#fecaca">🚫 Huỷ bill</button>' : '') +
      '</div>';
  }
  var b = frame('Hoá đơn ' + (maBill || d.name), html, { footer: foot });

  function veQr() {
    var o = document.getElementById('pbQr');
    if (!o) return;
    o.innerHTML = PB_PT === 'Chuyển khoản' ? posKhoiQr(posNoiDungCk(maBill || d.name, d.vgb_quay), phaiThu, d.custom_nguon || '') : '';
  }
  var ptw = document.getElementById('pbPt');
  if (ptw) ptw.querySelectorAll('.ptc').forEach(function (c) {
    c.onclick = function () {
      PB_PT = c.getAttribute('data-pt');
      if (posSua) posSua.pt = PB_PT;
      ptw.querySelectorAll('.ptc').forEach(function (x) {
        var on = x.getAttribute('data-pt') === PB_PT;
        x.style.border = '1.5px solid ' + (on ? '#0d9488' : '#e5e7eb');
        x.style.background = on ? '#ccfbf1' : '#fff';
        x.style.color = on ? '#0f766e' : '#374151';
      });
      var mo = document.getElementById('pbMtc');
      if (mo && PB_PT === 'Chuyển khoản' && !mo.value.trim()) mo.value = maBill || '';
      veQr();
    };
  });
  veQr();
  function docO(id) { var o = document.getElementById(id); return o ? o.value : ''; }
  function hutSua() {
    if (!posSua) return;
    posSua.pt = PB_PT;
    posSua.mtc = docO('pbMtc');
    posSua.ghi_chu = docO('pbGhiChu');
    posSua.giam = docO('pbGiam');
    var ob = document.getElementById('pbBan');
    if (ob) posSua.so_ban = ob.value;
    posSua.xh = {
      ten: docO('pbXTen'), mst: docO('pbXMst'), dc: docO('pbXDc'), email: docO('pbXMail')
    };
  }

  /* ----- chot / ghi so (nghiep vu binh thuong, khong can OTP) ----- */
  async function luuVe(chot) {
    if (!PB_PT) return toast('Chọn phương thức thanh toán trước.');
    busy(true);
    try {
      await api('vagabond.ban_hang.pos_chot', { name: d.name, pt: PB_PT, ma_tham_chieu: docO('pbMtc'), ghi_chu: docO('pbGhiChu') });
      if (chot) await api('vagabond.ban_hang.pos_ghi_so', { name: d.name });
      busy(false);
      toast(chot ? 'Đã ghi sổ ' + d.name : 'Đã chốt hoá đơn ' + d.name);
      posHomNayTxt = null;
      go(scrPosDs, true);
    } catch (e) { busy(false); toast((e && e.message) || 'Lỗi, thử lại.', 4500); }
  }
  var nc = document.getElementById('pbChot');
  if (nc) nc.onclick = async function () {
    var ok = await confirmSheet('Chốt hoá đơn ' + money(d.grand_total) + ' đ - ' + (PB_PT || 'chưa chọn'),
      'Khách đã thanh toán xong? Chốt xong hoá đơn thành doanh thu, ghi sổ được ngay.', 'Khách đã trả, chốt hoá đơn');
    if (ok) luuVe(false);
  };
  var ng = document.getElementById('pbGhiSo');
  if (ng) ng.onclick = async function () {
    var ok = await confirmSheet('Ghi sổ hoá đơn ' + money(d.grand_total) + ' đ',
      'Ghi sổ là chốt doanh thu chính thức tại quầy ' + (posQuay ? posQuay.ma : '') + '. Chuyển khoản thì máy tự kiểm SePay đủ tiền mới cho ghi.', 'Ghi sổ');
    if (ok) luuVe(true);
  };

  /* ----- go dau huy: danh dau nham thi lay lai duoc ----- */
  var ngh = document.getElementById('pbGoHuy');
  if (ngh) ngh.onclick = async function () {
    var ok = await confirmSheet('Gỡ dấu huỷ bill ' + (maBill || d.name) + '?',
      'Bill dùng lại bình thường và tính vào doanh thu trở lại.', 'Gỡ dấu huỷ');
    if (!ok) return;
    busy(true);
    try {
      await api('vagabond.chung_tu.bo_danh_dau_huy', { doctype: 'Sales Invoice', name: d.name });
      busy(false); toast('Đã gỡ dấu huỷ.'); posHomNayTxt = null;
      go(function () { scrPosBill(name); }, true);
    } catch (e) { busy(false); toast((e && e.message) || 'Không gỡ được', 5000); }
  };

  /* ----- huy bill: KHONG con xoa nua (anh Viet 11/08/2026) -----
     Hom 10/08 quan ly cua hang xoa 37 hoa don quay Tran Cao Van, so hoa
     don dien tu van nam ben co quan thue ma chung tu goc bien mat sach.
     Nay bill huy van nam nguyen trong danh sach, chi doi mau va bi loc ra
     khoi doanh thu - xem lai duoc bat cu luc nao. */
  var nx = document.getElementById('pbXoa');
  if (nx) nx.onclick = async function () {
    var ok = await confirmSheet('Huỷ bill ' + (maBill || d.name) + '?',
      'Bill ' + money(d.grand_total) + ' đ sẽ được đánh dấu đã huỷ và không tính vào doanh thu nữa. ' +
      'Bill vẫn nằm nguyên trong hệ thống để đối chiếu - không ai xoá được chứng từ. ' +
      'Thao tác này cần mã OTP của quản lý và ghi lại tên người huỷ.', 'Huỷ bill', true);
    if (!ok) return;
    var ly_do = await promptSheet('Vì sao huỷ bill ' + (maBill || d.name) + '?', 'Khách đổi ý, bấm nhầm món, trùng bill...');
    if (ly_do === null) return;
    if (!ly_do) return toast('Phải ghi lý do thì sau này còn biết vì sao.', 4000);
    var otp = await posXinPhep('Huỷ bill ' + (maBill || d.name));
    if (otp === null) return;
    busy(true);
    try {
      await api('vagabond.ban_hang.pos_xoa', { name: d.name, otp: otp, ly_do: ly_do });
      busy(false); toast('Đã huỷ bill ' + (maBill || d.name) + '. Bill vẫn còn trong danh sách.', 4000);
      posHomNayTxt = null; go(scrPosDs, true);
    }
    catch (e) { busy(false); toast((e && e.message) || 'Huỷ lỗi', 5000); }
  };

  /* ----- mo che do sua -----
     Muc quyen "duyet" thi xin OTP ngay tu dau nhu truoc gio. Hai muc con
     lai thi mo ra sua da, den luc Luu ma may chu doi ma moi hoi: luc bam
     Sua chua ai biet thu ngan sap THEM mon (duoc phep) hay BOT mon
     (khong duoc). Hoi truoc la bat ho go ma cho ca viec ho duoc lam. */
  var ns = document.getElementById('pbSua');
  if (ns) ns.onclick = async function () {
    var otp = '';
    if (posQuyenBoMon() === 'duyet') {
      otp = await posXinPhep('Sửa hoá đơn ' + (maBill || d.name));
      if (otp === null) return;
    }
    posSua = {
      name: d.name, otp: otp, mon: monTuDoc(),
      giam: String(d.discount_amount || ''), pt: d.vgb_pt_thanh_toan || '',
      mtc: d.vgb_ma_tham_chieu || '', ghi_chu: d.vgb_ghi_chu || '', so_ban: d.vgb_so_ban || '',
      xh: {
        ten: (d.vgb_xhd_ten && d.vgb_xhd_ten !== 'Bán cho người tiêu dùng') ? d.vgb_xhd_ten : '',
        mst: d.vgb_xhd_mst || '', dc: d.vgb_xhd_dia_chi || '', email: d.vgb_xhd_email || ''
      }
    };
    go(function () { scrPosBill(name); }, true);
  };
  var nhs = document.getElementById('pbHuySua');
  if (nhs) nhs.onclick = function () { posSua = null; go(function () { scrPosBill(name); }, true); };

  /* ----- sua so luong / xoa mon / them mon ----- */
  b.onclick = function (e) {
    if (!posSua) return;
    var t = e.target.closest('[data-scong]');
    if (t) { hutSua(); posSua.mon[+t.getAttribute('data-scong')].qty++; return go(function () { scrPosBill(name); }, true); }
    t = e.target.closest('[data-sbot]');
    if (t) {
      hutSua();
      var i = +t.getAttribute('data-sbot');
      if (posSua.mon[i].qty > 1) posSua.mon[i].qty--;
      return go(function () { scrPosBill(name); }, true);
    }
    t = e.target.closest('[data-sxoa]');
    if (t) { hutSua(); posSua.mon.splice(+t.getAttribute('data-sxoa'), 1); return go(function () { scrPosBill(name); }, true); }
  };
  var ntm = document.getElementById('pbThemMon');
  if (ntm) ntm.onclick = async function () {
    hutSua();
    if (!dsItemsCache) {
      busy(true);
      try {
        dsItemsCache = await getList('Item', { filters: { is_sales_item: 1, disabled: 0 }, fields: ['name', 'item_name', 'image', 'standard_rate', 'item_group'], limit_page_length: 0, order_by: 'item_name' });
      } catch (er) { busy(false); return toast('Không tải được danh mục món'); }
      busy(false);
    }
    posSheetMon(dsItemsCache.map(function (x) {
      return { value: x.name, label: x.item_name, icon: '🎂', img: x.image || '', gia: x.standard_rate || 0, nhom: x.item_group || '', phu: (x.standard_rate ? money(x.standard_rate) + ' đ' : 'chưa có giá') + ' · ' + x.name, tim: x.name + ' ' + (x.ma_vach || '') };
    }), function (o) {
      if (!o.gia) { toast('Món ' + o.label + ' chưa có giá bán trong danh mục.', 4000); return 0; }
      var vt = -1;
      posSua.mon.forEach(function (m, k) { if (m.item_code === o.value) vt = k; });
      if (vt >= 0) { posSua.mon[vt].qty += 1; return posSua.mon[vt].qty; }
      posSua.mon.push({ item_code: o.value, ten: o.label, qty: 1, rate: o.gia, nhom: o.nhom, tc: [], gc: '' });
      return 1;
    }, function () { go(function () { scrPosBill(name); }, true); }, function (ma) {
      var q = 0;
      (posSua ? posSua.mon : []).forEach(function (m) { if (m.item_code === ma) q = m.qty; });
      return q;
    });
  };

  /* ----- tra MST khi sua ----- */
  var nxt = document.getElementById('pbXTra');
  if (nxt) nxt.onclick = async function () {
    var mst = (docO('pbXMst') || '').replace(/\D/g, '');
    if (mst.length < 10) return toast('Nhập đủ mã số thuế 10 hoặc 13 số.');
    busy(true);
    try {
      var kq = await api('vagabond.api.tra_mst', { mst: mst });
      busy(false);
      if (kq && kq.ok) {
        if (kq.ten) document.getElementById('pbXTen').value = kq.ten;
        if (kq.dia_chi) document.getElementById('pbXDc').value = kq.dia_chi;
        toast('Tra được: ' + (kq.ten || ''));
      } else toast('Không tra được mã này, điền tay giúp em.', 4000);
    } catch (er) { busy(false); toast((er && er.message) || 'Không tra được mã số thuế', 4000); }
  };

  /* ----- luu thay doi ----- */
  var nls = document.getElementById('pbLuuSua');
  if (nls) nls.onclick = async function () {
    hutSua();
    if (nhap && !posSua.mon.length) return toast('Hoá đơn phải còn ít nhất một món.');
    var goi = {
      name: d.name, otp: posSua.otp,
      ghi_chu: posSua.ghi_chu || '', so_ban: posSua.so_ban || '',
      xhd_ten: posSua.xh.ten || '', xhd_mst: posSua.xh.mst || '',
      xhd_dia_chi: posSua.xh.dc || '', xhd_email: posSua.xh.email || ''
    };
    if (nhap) {
      goi.items = JSON.stringify(posSua.mon.map(function (m) {
        return { item_code: m.item_code, qty: m.qty, rate: m.rate, tuy_chon: (m.tc || []).join(', '), ghi_chu: m.gc || '' };
      }));
      goi.giam_gia = posSoTien(posSua.giam);
      if (posSua.pt) { goi.pt = posSua.pt; goi.ma_tham_chieu = posSua.mtc || ''; }
    }
    var ok = await confirmSheet('Lưu thay đổi hoá đơn ' + (maBill || d.name) + '?',
      (nhap ? 'Tổng mới: ' + money(Math.max(0, posSua.mon.reduce(function (t, m) { return t + m.qty * m.rate; }, 0) - posSoTien(posSua.giam))) + ' đ.\n' : '') +
      'Máy ghi lại tên người sửa vào lịch sử hoá đơn.', 'Lưu thay đổi');
    if (!ok) return;
    busy(true);
    try {
      await api('vagabond.ban_hang.pos_sua_don', goi);
    } catch (e) {
      busy(false);
      var loi = (e && e.message) || 'Lưu thay đổi lỗi';
      // May chu moi la noi quyet dinh co can OTP hay khong. App khong tu
      // doan: cu gui len, may chu doi ma thi luc do moi hoi quan ly.
      if (loi.indexOf('OTP') < 0) return toast(loi, 5000);
      var otp2 = await posSheetOtp('Sửa hoá đơn ' + (maBill || d.name) + ' - ' + loi);
      if (otp2 === null) return;
      goi.otp = otp2;
      busy(true);
      try { await api('vagabond.ban_hang.pos_sua_don', goi); }
      catch (e2) { busy(false); return toast((e2 && e2.message) || 'Lưu thay đổi lỗi', 5000); }
    }
    busy(false);
    posSua = null; posHomNayTxt = null;
    toast('Đã lưu thay đổi hoá đơn ' + (maBill || d.name));
    go(function () { scrPosBill(name); }, true);
  };

  /* ----- in ----- */
  function pbBillObj() {
    return {
      name: d.name, bill: maBill, tam_tinh: tamTinh ? 1 : 0, so_ban: soBan, quay: d.vgb_quay || '', nguon: d.custom_nguon || '',
      huy: d.vgb_huy ? 1 : 0, huy_ly_do: d.vgb_huy_ly_do || '',
      mon: monTuDoc(),
      tong: (d.items || []).reduce(function (t, m) { return t + (m.amount || 0); }, 0),
      giam: d.discount_amount || 0, thu: d.grand_total,
      pt: d.vgb_pt_thanh_toan || '', ghi_chu: d.vgb_ghi_chu || '', ten: ''
    };
  }
  var ni = document.getElementById('pbIn');
  if (ni) ni.onclick = function () {
    posInBill(pbBillObj());
    go(scrPosDs, true);
  };
  var nPm = document.getElementById('pbPhieuMon');
  if (nPm) nPm.onclick = function () { posInPhieuMon(pbBillObj()); };
  var nTem = document.getElementById('pbTemLy');
  if (nTem) nTem.onclick = function () { posInTemLy(pbBillObj()); };
}


/* ---------- Ma OTP quan ly (anh Viet 09/08/2026) ----------
   Hoa don quay la tien that da thu cua khach. Nhan vien muon sua hay xoa
   thi phai xin ma 6 so cua quan ly ca - vua chan gian lan, vua khong phai
   dua tai khoan sep cho nhan vien muon. Ma tu doi 10 phut mot lan. */
var otpDem = null;
async function scrOtp() {
  frame('Mã OTP quản lý', '<div class="emp"><div class="e1">⏳</div><div>Đang lấy mã...</div></div>');
  var k;
  try { k = await api('vagabond.ban_hang.otp_hien_tai'); }
  catch (e) {
    frame('Mã OTP quản lý', '<div class="card" style="padding:22px 18px;text-align:center">' +
      '<div style="font-size:40px">🔒</div>' +
      '<div style="font-size:15px;font-weight:700;margin-top:8px">Chỉ quản lý được cấp mã</div>' +
      '<div style="font-size:13.5px;color:#6b7280;margin-top:8px;line-height:1.6">' + h((e && e.message) || '') + '</div></div>');
    return;
  }
  var html = '<div class="card" style="padding:20px 18px;text-align:center">' +
    '<div style="font-size:12.5px;color:#6b7280;font-weight:600;letter-spacing:.06em">MÃ ĐANG CÓ HIỆU LỰC</div>' +
    '<div id="otpMa" style="font-size:46px;font-weight:800;letter-spacing:.16em;color:#0f766e;margin:8px 0 2px;font-variant-numeric:tabular-nums">' + h(k.ma) + '</div>' +
    '<div id="otpDem" style="font-size:13px;color:#b45309;font-weight:600"></div>' +
    '<div style="font-size:13px;color:#6b7280;margin-top:14px;line-height:1.7">Đọc mã này cho nhân viên khi họ cần sửa hoặc xoá hoá đơn. ' +
    'Mã tự đổi ' + (k.phut || 10) + ' phút một lần, mã cũ hết hiệu lực ngay.</div></div>';
  html += '<div class="card" style="padding:14px;font-size:13px;color:#5b6472;line-height:1.7">' +
    '<b>Trước khi đọc mã, hỏi nhân viên ba câu:</b><br>' +
    '1. Sửa hoá đơn nào, mã bao nhiêu?<br>' +
    '2. Sửa cái gì, vì sao phải sửa?<br>' +
    '3. Khách đã trả tiền chưa, tiền chênh xử lý thế nào?<br>' +
    '<span style="color:#98a2b3">Mỗi lần sửa hoặc xoá máy đều ghi lại tên người thao tác vào hoá đơn.</span></div>';
  frame('Mã OTP quản lý', html, { footer: '<button class="btn" id="otpMoi">🔄 Lấy mã mới nhất</button>' });
  document.getElementById('otpMoi').onclick = function () { go(scrOtp, true); };
  if (otpDem) clearInterval(otpDem);
  var con = k.con_lai || 0;
  var ve = function () {
    var o = document.getElementById('otpDem');
    if (!o) { clearInterval(otpDem); return; }
    if (con <= 0) { o.textContent = 'Mã đã đổi - bấm Lấy mã mới nhất'; o.style.color = '#b3261e'; clearInterval(otpDem); return; }
    o.textContent = 'Còn hiệu lực ' + Math.floor(con / 60) + ' phút ' + (con % 60) + ' giây';
    con--;
  };
  ve();
  otpDem = setInterval(ve, 1000);
}

/* Sheet nhap ma: tra ve chuoi ma, hoac null neu bo qua. */
function posSheetOtp(viec) {
  return new Promise(function (xong) {
    var ov = document.createElement('div'); ov.className = 'sh';
    ov.innerHTML = '<div class="shb" style="padding:20px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
      '<div style="font-size:18px;font-weight:800">🔐 Cần mã OTP quản lý</div>' +
      '<div style="font-size:13.5px;color:#6b7280;margin-top:6px;line-height:1.6">' + h(viec || 'Thao tác này') +
      ' phải được quản lý duyệt. Gọi quản lý ca xin mã 6 số rồi nhập vào đây.</div>' +
      '<input class="tin" id="otpNhap" inputmode="numeric" maxlength="6" placeholder="- - - - - -" ' +
      'style="margin-top:14px;text-align:center;font-size:30px;letter-spacing:.22em;height:60px;font-weight:800">' +
      '<div style="display:flex;gap:8px;margin-top:14px">' +
      '<button class="btn gh" data-huy style="flex:1;margin:0">Thôi</button>' +
      '<button class="btn" data-ok style="flex:1;margin:0">Xác nhận</button></div></div>';
    document.body.appendChild(ov);
    var o = ov.querySelector('#otpNhap');
    setTimeout(function () { try { o.focus(); } catch (e) { } }, 120);
    ov.onclick = function (e) {
      if (e.target.hasAttribute('data-ok')) {
        var ma = (o.value || '').replace(/\D/g, '');
        if (ma.length !== 6) return toast('Mã OTP gồm 6 số.');
        ov.remove(); return xong(ma);
      }
      if (e.target === ov || e.target.hasAttribute('data-huy')) { ov.remove(); xong(null); }
    };
  });
}

/* Sep thao tac thi may tu biet, khoi nhap ma. Nhan vien thi hien o nhap. */
/* Muc quyen bo mon cua thu ngan, khai o man Cai dat > Quyen tai quay.
   Mac dinh doc la "duyet" (chat nhat) khi chua tai duoc cau hinh - thieu
   mang thi phai nghieng ve phia chat, khong phai phia de. */
function posQuyenBoMon() { return ((CFGBH || {}).quyen_bo_mon) || 'duyet'; }

async function posXinPhep(viec) {
  try { await api('vagabond.ban_hang.otp_hien_tai'); return ''; }
  catch (e) { }
  return await posSheetOtp(viec);
}

/* ---------- Bao quay bar: phieu lam mon + tem ly (anh Viet 09/08/2026) ----------
   Mon nuoc nhan theo ma NU... (NUCF, NUTP, NUIC...) hoac nhom pha che.
   Phieu 80mm (xprinter quay bar) di theo ly thuy tinh ngoi tai quan;
   tem 4cm x 3cm (may in tem) dan ly mang di / giao hang. */
var POS_NHOM_NUOC = ['Trà', 'Cà phê', 'Matcha', 'Cacao', 'Ice Cream - Kem'];
function posLaNuoc(m) {
  if (String((m && m.item_code) || '').toUpperCase().indexOf('NU') === 0) return true;
  return POS_NHOM_NUOC.indexOf((m && m.nhom) || '') >= 0;
}
function posCoNuoc(mon) { return (mon || []).some(posLaNuoc); }
function posMonNuoc(mon) { return (mon || []).filter(posLaNuoc); }

function posInPhieuMon(d) {
  var nuoc = posMonNuoc(d.mon || []);
  if (!nuoc.length) return toast('Hoá đơn không có món nước nào.');
  var w = window.open('', '_blank');
  if (!w) return toast('Trình duyệt chặn cửa sổ in. Cho phép popup rồi bấm lại.', 4000);
  var gio = new Date();
  var hs = function (n) { return (n < 10 ? '0' : '') + n; };
  var rows = nuoc.map(function (m) {
    return '<div class="m"><span class="q">' + money(m.qty) + 'x</span> <b>' + h(m.ten) + '</b>' +
      (m.combo ? '<div class="tc" style="font-weight:bold">&#9733; ' + h(m.combo) + '</div>' : '') +
      ((m.tc || []).length ? '<div class="tc">&#8594; ' + h(m.tc.join(', ')) + '</div>' : '<div class="tc">&#8594; 100% đường · 100% đá</div>') +
      /* Ghi chu rieng cua mon: quay pha che doc ngay tren phieu, khong
         phai hoi lai thu ngan (anh Viet 10/08/2026). */
      (m.gc ? '<div class="tc" style="font-weight:bold">&#9755; ' + h(m.gc) + '</div>' : '') +
      '</div>';
  }).join('');
  w.document.write('<html><head><meta charset="utf-8"><title>Phiếu làm món ' + h(d.bill || d.name || '') + '</title><style>' +
    '@page{size:80mm auto;margin:0}*{margin:0;padding:0;box-sizing:border-box}' +
    'body{width:72mm;margin:0 auto;font-family:Arial,sans-serif;color:#000;padding:3mm 0 6mm}' +
    'h1{font-size:15px;text-align:center;letter-spacing:.1em}' +
    '.ph{text-align:center;font-size:11px;margin:1mm 0 2mm}' +
    'hr{border:0;border-top:1px dashed #000;margin:1.5mm 0}' +
    '.m{font-size:14px;padding:1.5mm 0;border-bottom:1px dashed #999}' +
    '.m .q{font-size:15px;font-weight:bold}' +
    '.tc{font-size:12px;padding-left:6mm}' +
    '.gc{font-size:12px;border:1px solid #000;padding:1.5mm;margin-top:2mm}' +
    '</style></head><body>' +
    '<h1>PHIẾU LÀM MÓN</h1>' +
    '<div class="ph">' + h((posQuay && posQuay.ten) || '') + ' · hoá đơn <b>' + h(d.bill || d.name || '') + '</b> · ' + hs(gio.getHours()) + ':' + hs(gio.getMinutes()) + '</div>' +
    (d.so_ban ? '<div style="text-align:center;font-size:17px;font-weight:bold;margin:1mm 0">BÀN ' + h(d.so_ban) + '</div>' : '') +
    '<hr>' + rows +
    (d.ghi_chu ? '<div class="gc">Ghi chú: ' + h(d.ghi_chu) + '</div>' : '') +
    '<script>window.onload=function(){setTimeout(function(){window.print()},900)}<' + '/script>' +
    '</body></html>');
  w.document.close();
}

/* Ma don cua san food app doc ra tu mot hoa don da luu: uu tien ma tham
   chieu, khong co thi lay nguon don. In DAM tren dau tem de shipper
   GrabFood, ShopeeFood den doc phat la nhan dung tui (anh Viet 10/08/2026). */
function posMaAppCuaBill(d) {
  var dsApp = ((CFGBH || {}).nguon_app) || ['GrabFood', 'ShopeeFood', 'BeFood', 'GreenSM Food'];
  var ng = (d.nguon || d.pt || '').trim();
  if (dsApp.indexOf(ng) < 0) return '';
  var ma = (d.mtc || d.ma || '').trim();
  return ma ? (ng + ' · ' + ma) : ng;
}

/* Tem dan mon: MOI mon deu duoc in tem chu khong rieng mon nuoc (anh Viet
   10/08/2026) - hop entremet cung can tem de khach nhin la biet banh gi.
   Moi don vi mot tem: 3 ly tra ra 3 tem, 2 hop banh ra 2 tem. */
function posInTemLy(d) {
  var mon = (d.mon || []).filter(function (m) { return (m.ten || '').trim(); });
  if (!mon.length) return toast('Hoá đơn không có món nào để in tem.');
  var ly = [];
  mon.forEach(function (m) {
    var n = Math.max(1, Math.round(m.qty || 1));
    for (var i = 0; i < n; i++) ly.push(m);
  });
  var w = window.open('', '_blank');
  if (!w) return toast('Trình duyệt chặn cửa sổ in. Cho phép popup rồi bấm lại.', 4000);
  var maApp = posMaAppCuaBill(d);
  var tem = ly.map(function (m, i) {
    /* Dong giua: tuy chon pha che voi mon nuoc, ghi chu rieng voi moi mon.
       Mon banh khong co tuy chon thi de trong chu khong in "100% da". */
    var giua = [];
    if (m.combo) giua.push('★ ' + m.combo);
    if ((m.tc || []).length) giua.push(m.tc.join(', '));
    else if (posLaNuoc(m)) giua.push('100% đường · 100% đá');
    if (m.gc) giua.push(m.gc);
    return '<div class="tem">' +
      (maApp
        ? '<div class="app">' + h(maApp) + '</div>'
        : '<div class="h">THE VAGABOND P&Acirc;TISSERIE</div>') +
      '<div class="t">' + h(m.ten) + '</div>' +
      '<div class="c">' + h(giua.join(' · ')) + '</div>' +
      '<div class="f"><span>' + h(d.bill || d.name || '') + (d.so_ban ? ' · Bàn ' + h(d.so_ban) : '') + '</span><span>' + (i + 1) + '/' + ly.length + '</span></div>' +
      '</div>';
  }).join('');
  w.document.write('<html><head><meta charset="utf-8"><title>Tem món ' + h(d.bill || d.name || '') + '</title><style>' +
    '@page{size:40mm 30mm;margin:0}*{margin:0;padding:0;box-sizing:border-box}' +
    'body{font-family:Arial,sans-serif;color:#000}' +
    '.tem{width:40mm;height:30mm;padding:1.5mm 2mm;page-break-after:always;overflow:hidden;display:flex;flex-direction:column}' +
    '.h{font-size:6.5px;text-align:center;letter-spacing:.06em}' +
    '.app{font-size:10px;font-weight:bold;text-align:center;background:#000;color:#fff;padding:.6mm 0;line-height:1.1}' +
    '.t{font-size:11px;font-weight:bold;text-align:center;line-height:1.15;margin-top:.5mm;flex:1;display:flex;align-items:center;justify-content:center}' +
    '.c{font-size:8px;text-align:center;line-height:1.2}' +
    '.f{display:flex;justify-content:space-between;font-size:7.5px;margin-top:.5mm;font-weight:bold}' +
    '</style></head><body>' + tem +
    '<script>window.onload=function(){setTimeout(function(){window.print()},900)}<' + '/script>' +
    '</body></html>');
  w.document.close();
}


/* ---------- Cong no phai thu (anh Viet 11/08/2026) ----------

Khach si nhu Ravie va khach VIP gom nhieu hoa don tra mot lan. Man nay lam
hai viec: xem ai dang no bao nhieu va bao lau, va gom hoa don thanh mot
PHIEU DOI NO co ma QR rieng de khach chuyen mot phat.

Co y de hai tab tach han: "Khach đang nợ" la viec di doi, "Phiếu đã gửi"
la viec doi soat. Tron chung vao mot danh sach la ke toan roi ngay. */
var cnTab = 'no', cnChon = {}, cnKhachMo = '';

async function scrCongNo() {
  frame('Công nợ phải thu', '<div class="emp"><div class="e1">⏳</div><div>Đang cộng sổ công nợ...</div></div>');
  var kq, kp;
  try {
    kq = await api('vagabond.cong_no.ds_khach_no', {});
    kp = await api('vagabond.cong_no.ds_phieu', {});
  } catch (e) {
    frame('Công nợ phải thu', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>');
    return;
  }
  var khach = (kq && kq.khach) || [], phieu = (kp && kp.phieu) || [];
  var choThu = phieu.filter(function (p) { return p.trang_thai === 'Cho thu' || p.trang_thai === 'Thu thieu'; });
  var tienChoThu = choThu.reduce(function (t, p) { return t + (p.con_thieu || 0); }, 0);

  var html = '<div class="card" style="padding:12px 14px;display:flex;gap:10px">' +
    '<div style="flex:1"><div style="font-size:12px;color:#98a2b3">CHƯA GOM PHIẾU</div>' +
    '<div style="font-size:19px;font-weight:800;color:#b45309">' + money(kq.tong || 0) + ' đ</div>' +
    '<div style="font-size:12px;color:#98a2b3">' + khach.length + ' khách</div></div>' +
    '<div style="flex:1;border-left:1px solid #eef0f4;padding-left:10px"><div style="font-size:12px;color:#98a2b3">ĐÃ GỬI, CHỜ TIỀN</div>' +
    '<div style="font-size:19px;font-weight:800;color:#0b7c93">' + money(tienChoThu) + ' đ</div>' +
    '<div style="font-size:12px;color:#98a2b3">' + choThu.length + ' phiếu</div></div></div>';

  html += '<div class="card" style="padding:10px 12px;display:flex;gap:8px">' +
    posChipNut('data-cntab="no"', '📒 Khách đang nợ ' + khach.length, cnTab === 'no') +
    posChipNut('data-cntab="phieu"', '📤 Phiếu đã gửi ' + phieu.length, cnTab === 'phieu') + '</div>';

  if (cnTab === 'no') {
    if (!khach.length) {
      html += '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🎉</div><div>Không còn khoản công nợ nào chưa gom. Sạch sổ.</div></div></div>';
    }
    khach.forEach(function (k) {
      var mo = cnKhachMo === k.khach;
      var chon = cnChon[k.khach] || {};
      var soChon = Object.keys(chon).filter(function (x) { return chon[x]; }).length;
      var tienChon = (k.hd || []).filter(function (d) { return chon[d.name]; }).reduce(function (t, d) { return t + d.tien; }, 0);
      /* Mau canh bao theo tuoi no: qua 30 ngay la do, 15 ngay la cam. */
      var mau = k.so_ngay >= 30 ? '#b91c1c' : (k.so_ngay >= 15 ? '#c2410c' : '#0f766e');
      html += '<div class="card" style="margin-bottom:10px;padding:0;overflow:hidden">' +
        '<div data-cnmo="' + h(k.khach) + '" style="padding:13px 14px;cursor:pointer;display:flex;align-items:center;gap:10px">' +
        '<div style="flex:1;min-width:0"><b style="font-size:15.5px">' + h(k.ten) + '</b>' +
        '<div style="font-size:12.5px;color:' + mau + ';font-weight:700;margin-top:2px">' +
        k.so_hd + ' hoá đơn · nợ lâu nhất ' + k.so_ngay + ' ngày</div></div>' +
        '<b style="font-size:16px;white-space:nowrap">' + money(k.tien) + ' đ</b>' +
        '<span style="color:#c3c8d4;font-size:20px">' + (mo ? '▾' : '▸') + '</span></div>';
      if (mo) {
        html += '<div style="border-top:1px solid #f0f2f6;padding:4px 14px 12px">';
        (k.hd || []).forEach(function (d) {
          var on = !!chon[d.name];
          html += '<div data-cnhd="' + h(k.khach) + '|' + h(d.name) + '" style="display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #f6f7f9;cursor:pointer">' +
            '<span style="width:22px;height:22px;flex:none;border-radius:6px;border:2px solid ' + (on ? '#0d9488;background:#0d9488' : '#d7dce5') + ';color:#fff;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:900">' + (on ? '✓' : '') + '</span>' +
            '<div style="flex:1;min-width:0"><div style="font-size:13.5px">' + h(d.name) + '</div>' +
            '<div style="font-size:12px;color:#98a2b3">' + posNgayVn(d.ngay) + (d.nguon ? ' · ' + h(d.nguon) : '') + (d.quay ? ' · ' + h(d.quay) : '') + '</div></div>' +
            '<b style="white-space:nowrap">' + money(d.tien) + ' đ</b></div>';
        });
        html += '<div style="display:flex;gap:7px;flex-wrap:wrap;margin-top:10px">' +
          posChipNut('data-cnall="' + h(k.khach) + '"', 'Chọn hết', false) +
          posChipNut('data-cnnone="' + h(k.khach) + '"', 'Bỏ chọn', false, 1) + '</div>';
        html += '<button class="btn" data-cngom="' + h(k.khach) + '" style="margin-top:12px"' + (soChon ? '' : ' disabled') + '>' +
          (soChon ? '📤 Gom ' + soChon + ' hoá đơn · ' + money(tienChon) + ' đ thành phiếu đề nghị thanh toán' : 'Tick hoá đơn cần thu ở trên') + '</button>';
        html += '</div>';
      }
      html += '</div>';
    });
  } else {
    var CPL = [
      { k: '', nhan: 'Tất cả', loc: function () { return true; } },
      { k: 'Cho thu', nhan: '⏳ Chờ tiền', loc: function (p) { return p.trang_thai === 'Cho thu'; } },
      { k: 'Thu thieu', nhan: '⚠ Thu thiếu', loc: function (p) { return p.trang_thai === 'Thu thieu'; } },
      { k: 'Da thu du', nhan: '✅ Đã thu đủ', loc: function (p) { return p.trang_thai === 'Da thu du'; } },
      { k: 'het_han', nhan: '⌛ QR hết hạn', loc: function (p) { return p.het_han && p.trang_thai !== 'Da thu du'; } },
      { k: 'Huy', nhan: '🚫 Đã huỷ', loc: function (p) { return p.trang_thai === 'Huy'; } }
    ];
    var fp = locTim(CPL, cnLocPhieu); cnLocPhieu = fp.k;
    html += '<div class="card" style="padding:10px 12px">' + locHang(CPL, cnLocPhieu, 'data-cnlp', phieu) + '</div>';
    var dsP = phieu.filter(fp.loc);
    if (!dsP.length) html += '<div class="card"><div class="emp" style="padding:26px"><div class="e1">📭</div><div>Chưa có phiếu nào thuộc nhóm này.</div></div></div>';
    dsP.forEach(function (p) {
      var mau = p.trang_thai === 'Da thu du' ? '#15803d' : (p.trang_thai === 'Huy' ? '#98a2b3' : (p.het_han ? '#b91c1c' : '#b45309'));
      var nhan = p.trang_thai === 'Da thu du' ? '✅ Đã thu đủ' : (p.trang_thai === 'Huy' ? '🚫 Đã huỷ' : (p.trang_thai === 'Thu thieu' ? '⚠ Thu thiếu' : '⏳ Chờ tiền'));
      html += '<div class="card" data-cnxem="' + h(p.name) + '" style="margin-bottom:10px;padding:13px 14px;cursor:pointer">' +
        '<div style="display:flex;align-items:center;gap:10px;pointer-events:none">' +
        '<div style="flex:1;min-width:0"><b style="font-size:15px">' + h(p.ten_khach || p.khach) + '</b>' +
        '<div style="font-size:12.5px;color:#98a2b3;margin-top:2px">' + h(p.ma_phieu) + ' · ' + p.so_hd + ' hoá đơn · tạo ' + posNgayVn(p.ngay_tao) + '</div>' +
        '<div style="font-size:12.5px;color:' + mau + ';font-weight:700;margin-top:3px">' + nhan +
        (p.het_han && p.trang_thai !== 'Da thu du' ? ' · QR hết hạn ' + posNgayVn(p.han_qr) : '') +
        (p.sepay ? ' · SePay đã nhận ' + money(p.sepay) + ' đ' : '') + '</div></div>' +
        '<div style="text-align:right"><b style="font-size:16px">' + money(p.tong_tien) + ' đ</b>' +
        (p.con_thieu && p.trang_thai !== 'Huy' ? '<div style="font-size:12px;color:#b91c1c">còn ' + money(p.con_thieu) + ' đ</div>' : '') + '</div>' +
        '<span style="color:#c3c8d4;font-size:20px">›</span></div></div>';
    });
  }

  var b = frame('Công nợ phải thu', html);
  b.onclick = async function (e) {
    var t = e.target.closest('[data-cntab]');
    if (t) { cnTab = t.getAttribute('data-cntab'); return go(scrCongNo, true); }
    t = e.target.closest('[data-cnlp]');
    if (t) { cnLocPhieu = t.getAttribute('data-cnlp'); return go(scrCongNo, true); }
    t = e.target.closest('[data-cnmo]');
    if (t) { var m = t.getAttribute('data-cnmo'); cnKhachMo = cnKhachMo === m ? '' : m; return go(scrCongNo, true); }
    t = e.target.closest('[data-cnhd]');
    if (t) {
      var v = t.getAttribute('data-cnhd').split('|');
      cnChon[v[0]] = cnChon[v[0]] || {};
      cnChon[v[0]][v[1]] = !cnChon[v[0]][v[1]];
      return go(scrCongNo, true);
    }
    t = e.target.closest('[data-cnall]');
    if (t) {
      var ka = t.getAttribute('data-cnall');
      var kk = khach.filter(function (x) { return x.khach === ka; })[0] || { hd: [] };
      cnChon[ka] = {};
      (kk.hd || []).forEach(function (d) { cnChon[ka][d.name] = true; });
      return go(scrCongNo, true);
    }
    t = e.target.closest('[data-cnnone]');
    if (t) { cnChon[t.getAttribute('data-cnnone')] = {}; return go(scrCongNo, true); }
    t = e.target.closest('[data-cnxem]');
    if (t) return go(function () { scrCnPhieu(t.getAttribute('data-cnxem')); });
    t = e.target.closest('[data-cngom]');
    if (t) {
      var kg = t.getAttribute('data-cngom');
      var ds = Object.keys(cnChon[kg] || {}).filter(function (x) { return cnChon[kg][x]; });
      if (!ds.length) return;
      var kx = khach.filter(function (x) { return x.khach === kg; })[0] || {};
      var tien = (kx.hd || []).filter(function (d) { return ds.indexOf(d.name) >= 0; }).reduce(function (s2, d) { return s2 + d.tien; }, 0);
      var ok = await confirmSheet('Gom ' + ds.length + ' hoá đơn · ' + money(tien) + ' đ',
        (kx.ten || kg) + '\nMáy sinh một phiếu đề nghị thanh toán công nợ kèm mã QR MB Bank sống 7 ngày. Khách chuyển một lần, SePay tự khớp và tự xoá nợ.',
        'Tạo phiếu yêu cầu thanh toán công nợ');
      if (!ok) return;
      busy(true);
      try {
        var r = await api('vagabond.cong_no.tao_phieu', { khach: kg, hoa_don: JSON.stringify(ds) });
        busy(false);
        cnChon[kg] = {};
        toast('Đã tạo phiếu ' + r.ma_phieu);
        return go(function () { scrCnPhieu(r.name); });
      } catch (er) { busy(false); toast((er && er.message) || 'Không tạo được phiếu', 5000); }
    }
  };
}
var cnLocPhieu = '';

/* Chi tiet mot phieu doi no: ma QR de gui khach, danh sach hoa don trong
   phieu, va nut doi chieu SePay. */
async function scrCnPhieu(name) {
  frame('Phiếu đề nghị thanh toán công nợ', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.cong_no.xem_phieu', { name: name }); }
  catch (e) { frame('Phiếu đề nghị thanh toán công nợ', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>'); return; }
  var du = d.sepay >= d.tong_tien - 1;
  var qr = d.qr || {};
  var url = qr.stk
    ? 'https://img.vietqr.io/image/' + (qr.bank || 'MB') + '-' + qr.stk + '-qr_only.png?amount=' + Math.round(d.tong_tien) +
      '&addInfo=' + encodeURIComponent(d.ma_phieu) + '&accountName=' + encodeURIComponent(qr.ten || '')
    : '';

  var html = '<div class="card" style="padding:14px">' +
    '<div style="display:flex;align-items:center;gap:10px">' +
    '<div style="flex:1"><div style="font-size:12px;color:#98a2b3">PHIẾU ĐÒI NỢ</div>' +
    '<b style="font-size:18px">' + h(d.ma_phieu) + '</b>' +
    '<div style="font-size:13.5px;color:#374151;margin-top:2px">' + h(d.ten_khach || d.khach) + '</div></div>' +
    '<div style="text-align:right"><b style="font-size:19px">' + money(d.tong_tien) + ' đ</b>' +
    '<div style="font-size:12px;color:#98a2b3">' + (d.dong || []).length + ' hoá đơn</div></div></div></div>';

  if (du) {
    html += '<div class="card" style="padding:18px;text-align:center;border:2px solid #16a34a;background:#f0fdf4">' +
      '<div style="font-size:34px">✅</div><div style="font-size:18px;font-weight:800;color:#15803d">ĐÃ NHẬN ĐỦ ' + money(d.sepay) + ' đ</div>' +
      '<div style="font-size:13px;color:#15803d;margin-top:4px">Công nợ của khách này đã sạch.</div></div>';
  } else {
    html += '<div class="card" style="padding:14px;text-align:center">' +
      (d.het_han
        ? '<div style="background:#fef2f2;border:1.5px solid #fecaca;color:#b91c1c;border-radius:9px;padding:9px;font-size:13px;font-weight:700;margin-bottom:10px">Mã QR đã quá hạn ' + posNgayVn(d.han_qr) + '. Huỷ phiếu này rồi gom lại phiếu mới.</div>'
        : '<div style="font-size:12.5px;color:#6b7280;margin-bottom:8px">Mã QR sống tới hết ngày <b>' + posNgayVn(d.han_qr) + '</b></div>') +
      (url ? '<img src="' + url + '" style="width:230px;height:230px;display:block;margin:0 auto;border:1px solid #eef0f4;border-radius:10px">' : '<div style="color:#b3261e;font-size:13px">Chưa khai số tài khoản nhận nên chưa sinh được QR.</div>') +
      '<div style="margin-top:10px;font-size:13.5px">Nội dung chuyển khoản: <b style="font-size:16px">' + h(d.ma_phieu) + '</b></div>' +
      '<div style="font-size:12.5px;color:#6b7280">' + h(qr.bank || '') + ' · ' + h(qr.stk || '') + ' · ' + h(qr.ten || '') + '</div>' +
      (d.sepay ? '<div style="margin-top:8px;color:#b45309;font-weight:700">SePay đã nhận ' + money(d.sepay) + ' đ, còn thiếu ' + money(d.con_thieu) + ' đ</div>' : '') +
      '</div>';
  }

  html += '<div class="sec">Hoá đơn trong phiếu</div><div class="card" style="padding:6px 14px">';
  (d.dong || []).forEach(function (x) {
    html += '<div style="display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #f6f7f9">' +
      '<div style="flex:1;min-width:0"><div style="font-size:13.5px">' + h(x.hoa_don) + '</div>' +
      '<div style="font-size:12px;color:#98a2b3">' + posNgayVn(x.ngay) + (x.nguon ? ' · ' + h(x.nguon) : '') + '</div></div>' +
      '<b style="white-space:nowrap">' + money(x.so_tien) + ' đ</b></div>';
  });
  html += '</div>';
  if (d.ghi_chu) html += '<div class="card" style="padding:12px 14px;font-size:13px;white-space:pre-wrap">' + h(d.ghi_chu) + '</div>';

  var foot = '<div style="display:flex;gap:8px">' +
    '<button class="btn gh" id="cnKiem" style="flex:1;margin:0">🔄 Đối chiếu SePay</button>' +
    (du || d.trang_thai === 'Huy' ? '' : '<button class="btn gh" id="cnHuy" style="flex:0 0 34%;margin:0;color:#b3261e">Huỷ phiếu</button>') +
    '</div>';
  var b = frame('Phiếu ' + h(d.ma_phieu), html, { footer: foot });
  document.getElementById('cnKiem').onclick = async function () {
    busy(true);
    try { var r = await api('vagabond.cong_no.kiem_sepay', { name: name }); busy(false); toast(r.sepay >= r.tong_tien - 1 ? 'Tiền đã về đủ, đã xoá nợ.' : 'SePay mới nhận ' + money(r.sepay) + ' đ.', 4000); go(function () { scrCnPhieu(name); }, true); }
    catch (e) { busy(false); toast((e && e.message) || 'Không đối chiếu được', 4000); }
  };
  var nh = document.getElementById('cnHuy');
  if (nh) nh.onclick = async function () {
    var ok = await confirmSheet('Huỷ phiếu ' + d.ma_phieu, 'Các hoá đơn trong phiếu sẽ quay lại danh sách chờ gom. Mã QR này sẽ không dùng nữa.', 'Huỷ phiếu');
    if (!ok) return;
    busy(true);
    try { await api('vagabond.cong_no.huy_phieu', { name: name, ly_do: S.me.full_name || S.user }); busy(false); toast('Đã huỷ phiếu.'); go(scrCongNo); }
    catch (e) { busy(false); toast((e && e.message) || 'Không huỷ được', 4000); }
  };
}


/* ---------- Danh sach khach hang (anh Viet 11/08/2026) ----------

Tra cuu khach: ai la khach si ai la khach le, ai dang o hang nao, da chi
bao nhieu trong nam. Chi tieu tinh tren hoa don DA GHI SO trong 12 thang -
don con o ban nhap chua phai tien that.

Hang do doctype "Vagabond Hang Khach" giu, khong nhet trong ma, nen anh
Viet chot muc chi tieu luc nao thi sua o do la xong. */
var khDang = '', khHang = '', khTim = '', khData = null;

async function scrKhachHang() {
  frame('Danh sách khách hàng', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc danh mục khách...</div></div>');
  var kq, kh;
  try {
    kq = await api('vagabond.khach_hang.ds_khach', { tu_khoa: khTim, dang: khDang, hang: khHang });
    kh = await api('vagabond.khach_hang.ds_hang', {});
  } catch (e) {
    frame('Danh sách khách hàng', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>');
    return;
  }
  khData = kq;
  var all = (kq && kq.khach) || [], hangs = (kh && kh.hang) || [];

  var DANG = [
    { k: '', nhan: 'Tất cả', loc: function () { return true; } },
    { k: 'si', nhan: '🏢 Khách sỉ', loc: function (x) { return !!x.si; } },
    { k: 'le', nhan: '🧍 Khách lẻ', loc: function (x) { return !x.si; } }
  ];
  var HANG = [{ k: '', nhan: 'Mọi hạng', loc: function () { return true; } }];
  hangs.forEach(function (hg) {
    HANG.push({
      k: hg.name,
      nhan: (hg.giam_gia ? '★ ' : '') + h(hg.ten_hang) + (hg.giam_gia ? ' −' + money(hg.giam_gia) + '%' : ''),
      loc: function (x) { return x.hang === hg.name; }
    });
  });
  HANG.push({ k: '_chua', nhan: '· Chưa xếp hạng', loc: function (x) { return !x.hang; } });

  var fD = locTim(DANG, khDang); khDang = fD.k;
  var fH = locTim(HANG, khHang); khHang = fH.k;
  /* May chu da loc san theo dang va hang roi (khong the loc o day duoc vi
     danh muc hon 1500 khach, chi tai ve mot phan). */
  var ds = all;
  var tong = ds.reduce(function (t, x) { return t + x.tien; }, 0);

  var html = '<div class="card" style="padding:12px 14px;display:flex;gap:10px">' +
    '<div style="flex:1"><div style="font-size:12px;color:#98a2b3">ĐANG XEM</div>' +
    '<div style="font-size:19px;font-weight:800">' + (kq.tong_so || ds.length) + ' khách</div>' +
    '<div style="font-size:12px;color:#98a2b3">' + kq.so_si + ' sỉ · ' + kq.so_le + ' lẻ</div></div>' +
    '<div style="flex:1;border-left:1px solid #eef0f4;padding-left:10px"><div style="font-size:12px;color:#98a2b3">CHI TIÊU 12 THÁNG</div>' +
    '<div style="font-size:19px;font-weight:800;color:#0f766e">' + money(tong) + ' đ</div></div></div>';

  html += '<div class="card" style="padding:10px 12px">' +
    '<input class="tin" id="khO" placeholder="Tìm theo tên, mã, mã số thuế, số điện thoại..." value="' + h(khTim) + '" style="margin-bottom:8px"></div>';
  var chipHang = function (ds2, chon, attr) {
    return '<div style="flex:0 0 auto;display:flex;gap:7px;padding:2px 0;overflow-x:auto;-webkit-overflow-scrolling:touch">' +
      ds2.map(function (c) { return posChipNut(attr + '="' + h(c.k) + '"', c.nhan, c.k === chon); }).join('') + '</div>';
  };
  html += '<div class="card" style="padding:10px 12px;display:flex;flex-direction:column;gap:7px">' +
    chipHang(DANG, khDang, 'data-khd') +
    chipHang(HANG, khHang, 'data-khh') + '</div>';

  if (!hangs.length) {
    html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fcd34d;font-size:13px;color:#92400e">' +
      'Chưa cấu hình hạng khách nào. Vào Desk mở danh mục <b>Vagabond Hang Khach</b> để điền mức chi tiêu và phần trăm giảm cho từng hạng.</div>';
  }

  html += '<div class="sec">Khách · chi nhiều nhất lên đầu</div><div class="card" style="padding:6px 14px">';
  if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">🔍</div><div>Không có khách nào thuộc nhóm này.</div></div>';
  ds.slice(0, 200).forEach(function (x) {
    var hg = hangs.filter(function (y) { return y.name === x.hang; })[0];
    html += '<div data-khx="' + h(x.ma) + '" style="display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #f6f7f9;cursor:pointer">' +
      '<span style="width:38px;height:38px;flex:none;border-radius:10px;background:' + (x.si ? '#eef2ff' : '#f0fdfa') + ';display:flex;align-items:center;justify-content:center;font-size:18px">' + (x.si ? '🏢' : '🧍') + '</span>' +
      '<div style="flex:1;min-width:0"><div style="font-size:14.5px;font-weight:600">' + h(x.ten) + '</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px">' +
      (hg
        ? '<span style="background:#fef3c7;color:#92400e;border:1.5px solid #fcd34d;border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:800">' + h(hg.ten_hang) + (hg.giam_gia ? ' · −' + money(hg.giam_gia) + '%' : '') + '</span>'
        : '<span style="background:#f6f7f9;color:#98a2b3;border:1.5px dashed #d7dce5;border-radius:999px;padding:2px 9px;font-size:11.5px">chưa xếp hạng</span>') +
      /* Ma khach hien ngay tren dong (anh Viet 11/08/2026): tra cuu, doi
         chieu voi phieu giay va goi dien cho nhau deu can doc ma. */
      '<span style="background:#f1f5f9;color:#475569;border:1.5px solid #e2e8f0;border-radius:999px;padding:2px 9px;font-size:11.5px;font-family:ui-monospace,monospace">' + h(x.ma) + '</span>' +
      (x.mst ? '<span style="background:#eef2ff;color:#3730a3;border-radius:999px;padding:2px 9px;font-size:11.5px">MST ' + h(x.mst) + '</span>' : '') +
      (x.dt ? '<span style="background:#f0fdfa;color:#0f766e;border-radius:999px;padding:2px 9px;font-size:11.5px">' + h(x.dt) + '</span>' : '') +
      '</div></div>' +
      '<div style="text-align:right;flex:none"><b style="font-size:14.5px">' + money(x.tien) + ' đ</b>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + x.so_don + ' hoá đơn</div></div>' +
      '<span style="color:#c3c8d4;font-size:18px">›</span></div>';
  });
  var conLai = Math.max(0, (kq.tong_so || ds.length) - Math.min(ds.length, 200));
  if (conLai) html += '<div style="padding:10px 0;text-align:center;font-size:12.5px;color:#98a2b3">Nhóm này có <b>' + (kq.tong_so || ds.length) + ' khách</b>, đang hiện ' + Math.min(ds.length, 200) + '. Gõ tìm để ra đúng khách cần.</div>';
  html += '</div>';

  var b = frame('Danh sách khách hàng', html);
  var o = document.getElementById('khO');
  if (o) {
    var tre = null;
    o.oninput = function () {
      if (tre) clearTimeout(tre);
      tre = setTimeout(function () { khTim = o.value; go(scrKhachHang, true); }, 320);
    };
  }
  b.onclick = function (e) {
    var t = e.target.closest('[data-khd]');
    if (t) { khDang = t.getAttribute('data-khd'); return go(scrKhachHang, true); }
    t = e.target.closest('[data-khh]');
    if (t) { khHang = t.getAttribute('data-khh'); return go(scrKhachHang, true); }
    t = e.target.closest('[data-khx]');
    if (t) return khSheetHang(t.getAttribute('data-khx'), hangs, all);
  };
}

/* Bang gan hang cho mot khach. Co hien ca hang MAY GOI Y theo chi tieu de
   quan ly doi chieu, nhung KHONG tu doi - len hang la quyet dinh cua
   nguoi, khong phai cua may. */
async function khSheetHang(ma, hangs, all) {
  var x = all.filter(function (y) { return y.ma === ma; })[0] || {};
  var gy = {};
  try { gy = await api('vagabond.khach_hang.goi_y_hang', { khach: ma }); } catch (e) { }
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  var html = '<div class="shh"><b>' + h(x.ten || ma) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 14px)">' +
    '<div style="font-size:12.5px;color:#6b7280;margin-bottom:10px">' +
    h(x.nhom || 'chưa gắn nhóm') + ' · đã chi <b>' + money(x.tien) + ' đ</b> qua ' + x.so_don + ' hoá đơn' +
    (x.gan_nhat ? ' · gần nhất ' + posNgayVn(x.gan_nhat) : '') + '</div>';
  if (gy && gy.hang) {
    html += '<div style="background:#ecfeff;border:1.5px solid #7fe5f6;border-radius:9px;padding:9px 11px;font-size:12.5px;color:#0b7c93;margin-bottom:10px">' +
      'Theo chi tiêu ' + money(gy.tien) + ' đ trong ' + (gy.so_thang || 12) + ' tháng, khách này <b>đủ điều kiện hạng ' + h(gy.hang) + '</b>.</div>';
  }
  html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin-bottom:7px">GẮN HẠNG</div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:7px">' +
    hangs.map(function (hg) {
      return posChipNut('data-sethang="' + h(hg.name) + '"',
        h(hg.ten_hang) + (hg.giam_gia ? ' −' + money(hg.giam_gia) + '%' : ''), x.hang === hg.name);
    }).join('') +
    (x.hang ? posChipNut('data-sethang=""', '✕ Bỏ hạng', false, 1) : '') +
    '</div>';
  var mt = hangs.filter(function (hg) { return (hg.mo_ta || '').trim(); });
  if (mt.length) {
    html += '<div style="margin-top:14px;font-size:12px;color:#98a2b3;line-height:1.6">' +
      mt.map(function (hg) { return '<b>' + h(hg.ten_hang) + ':</b> ' + h(hg.mo_ta); }).join('<br>') + '</div>';
  }
  html += '</div>';
  box.innerHTML = html;
  ov.appendChild(box); document.body.appendChild(ov);
  function dong() { ov.remove(); }
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  box.querySelector('.x').onclick = dong;
  box.addEventListener('click', async function (e) {
    var t = e.target.closest('[data-sethang]'); if (!t) return;
    var hg = t.getAttribute('data-sethang');
    busy(true);
    try {
      await api('vagabond.khach_hang.dat_hang', { khach: ma, hang: hg });
      busy(false); dong();
      toast(hg ? 'Đã xếp ' + (x.ten || ma) + ' vào hạng ' + hg : 'Đã bỏ hạng của ' + (x.ten || ma));
      go(scrKhachHang, true);
    } catch (er) { busy(false); toast((er && er.message) || 'Không đặt được hạng', 4000); }
  });
}

/* ---------- Chot ca: cong so cuoi ca cua MOT quay (anh Viet 09/08/2026) ----------
   Tien mat phai co trong ket, CK doi voi SePay da ve, tam tinh con treo,
   bill chua ghi so - lech la thay ngay truoc khi giao ca. */
async function scrPosChotCa() {
  if (!posQuay) return go(scrPosChonQuay, true);
  frame('Chốt ca · ' + (posQuay.ma || ''), '<div class="emp"><div class="e1">⏳</div><div>Đang cộng sổ ca hôm nay...</div></div>');
  var k;
  try { k = await api('vagabond.ban_hang.pos_chot_ca', { quay: posQuay.ma || '', ngay: posDsNgay || today() }); }
  catch (e) { frame('Chốt ca · ' + (posQuay.ma || ''), '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var dRow = function (nhan, tien, phu, mau) {
    return '<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
      '<span style="flex:1;min-width:0">' + nhan + (phu ? '<div style="font-size:12px;color:#98a2b3">' + phu + '</div>' : '') + '</span>' +
      '<b style="white-space:nowrap;margin-left:8px' + (mau ? ';color:' + mau : '') + '">' + money(tien) + ' đ</b></div>';
  };
  var html = '<div class="card" style="padding:12px 14px"><b>Ca ngày ' + h(k.ngay || today()) + ' · quầy ' + h(k.quay || '') + '</b>' +
    '<div style="font-size:12px;color:#98a2b3">' + (k.tong_bill || 0) + ' hoá đơn doanh thu · tổng ' + money(k.tong_tien || 0) + ' đ</div></div>';
  html += '<div class="sec">Tiền theo phương thức</div><div class="card" style="padding:6px 14px">';
  (k.pt || []).forEach(function (p) {
    var laTm = p.pt === 'Tiền mặt';
    html += dRow((laTm ? '💵 ' : '') + h(p.pt) + ' · ' + p.so + ' hoá đơn', p.tien,
      laTm ? 'PHẢI CÓ ĐỦ TRONG KÉT khi giao ca' : '', laTm ? '#b45309' : '');
  });
  if (!(k.pt || []).length) html += '<div style="padding:16px 0;color:#98a2b3;text-align:center">Chưa có hoá đơn doanh thu nào.</div>';
  html += '</div>';
  /* Tien CHUA nam trong ket luc giao ca: Grab Dine-Out Grab giu den T+1,
     Cong no khach si con thieu. Tach hin ra de thu ngan dem tien mat khong
     bi lech va quan ly biet con bao nhieu phai di doi (anh Viet 10/08/2026). */
  var cv = k.chua_ve || { so: 0, tien: 0, dong: [] };
  if (cv.so) {
    html += '<div class="sec">Tiền chưa về két</div><div class="card" style="padding:6px 14px;border:1.5px solid #fcd34d;background:#fffbeb">';
    (cv.dong || []).forEach(function (p) {
      html += dRow('⏳ ' + h(p.pt) + ' · ' + p.so + ' hoá đơn', p.tien,
        p.pt === 'Công nợ' ? 'khách sỉ gom hoá đơn, theo dõi ở Công nợ phải thu' : 'Grab giữ tiền, chuyển về tiệm ngày T+1', '#b45309');
    });
    html += dRow('<b>Cộng chưa về</b>', cv.tien, 'KHÔNG đếm số này trong két tiền mặt', '#b45309');
    html += '</div>';
  }
  html += '<div class="sec">Đối soát chuyển khoản (SePay)</div><div class="card" style="padding:6px 14px">' +
    dRow('✅ SePay đã nhận', k.ck_ve || 0, 'khớp theo mã hoá đơn VGB trong nội dung CK', '#0f766e');
  (k.ck_thieu || []).forEach(function (c) {
    html += dRow('⚠ ' + h(c.bill) + ' còn thiếu', c.thieu, 'kiểm với khách / SePay trước khi ghi sổ', '#b91c1c');
  });
  if (!(k.ck_thieu || []).length) html += '<div style="padding:8px 0;color:#15803d;font-size:13px">Không hoá đơn chuyển khoản nào thiếu tiền 👍</div>';
  html += '</div>';
  var tt = k.tam_tinh || { so: 0, tien: 0 };
  var tRow = function (nhan, gia, mau, phu) {
    return '<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
      '<span style="flex:1;min-width:0">' + nhan + (phu ? '<div style="font-size:12px;color:#98a2b3">' + phu + '</div>' : '') + '</span>' +
      '<b style="white-space:nowrap;margin-left:8px' + (mau ? ';color:' + mau : '') + '">' + gia + '</b></div>';
  };
  html += '<div class="sec">Sổ sách trước khi giao ca</div><div class="card" style="padding:6px 14px">' +
    tRow('📒 Đã ghi sổ', (k.da_ghi || 0) + ' hoá đơn', '') +
    tRow('📄 Chưa ghi sổ', (k.chua_ghi || 0) + ' hoá đơn', k.chua_ghi ? '#b91c1c' : '#15803d', k.chua_ghi ? 'vào Hoá đơn hôm nay ghi sổ hết rồi hãy chốt ca' : '') +
    tRow('🕐 Tạm tính còn treo', tt.so + ' hoá đơn · ' + money(tt.tien) + ' đ', tt.so ? '#c2410c' : '#15803d') + '</div>';
  frame('Chốt ca · ' + (posQuay.ma || ''), html, { footer: '<button class="btn" id="ccIn">🖨 In bảng chốt ca</button>' });
  document.getElementById('ccIn').onclick = function () { posInChotCa(k); };
}

function posInChotCa(k) {
  var w = window.open('', '_blank');
  if (!w) return toast('Trình duyệt chặn cửa sổ in. Cho phép popup rồi bấm lại.', 4000);
  var gio = new Date();
  var hs = function (n) { return (n < 10 ? '0' : '') + n; };
  var lucIn = hs(gio.getHours()) + ':' + hs(gio.getMinutes()) + ' ' + hs(gio.getDate()) + '/' + hs(gio.getMonth() + 1) + '/' + gio.getFullYear();
  var dd = function (a, b) { return '<div class="d"><span>' + a + '</span><b>' + b + '</b></div>'; };
  var tt = k.tam_tinh || { so: 0, tien: 0 };
  var thanPt = (k.pt || []).map(function (p) { return dd(h(p.pt) + ' (' + p.so + ' hoá đơn)', money(p.tien) + ' đ'); }).join('');
  var thanThieu = (k.ck_thieu || []).map(function (c) { return dd('Thiếu ' + h(c.bill), money(c.thieu) + ' đ'); }).join('');
  w.document.write('<html><head><meta charset="utf-8"><title>Chốt ca ' + h(k.quay || '') + '</title><style>' +
    '@page{size:80mm auto;margin:0}*{margin:0;padding:0;box-sizing:border-box}' +
    'body{width:72mm;margin:0 auto;font-family:Arial,sans-serif;font-size:11.5px;color:#000;padding:4mm 0 6mm}' +
    'h1{font-size:14px;text-align:center;letter-spacing:.08em}' +
    '.ph{text-align:center;font-size:10.5px;margin-bottom:2mm;line-height:1.5}' +
    'hr{border:0;border-top:1px dashed #000;margin:2mm 0}' +
    '.d{display:flex;justify-content:space-between;padding:.6mm 0}' +
    '.s{font-weight:bold;margin-top:1.5mm}' +
    '</style></head><body>' +
    '<h1>BẢNG CHỐT CA</h1>' +
    '<div class="ph">' + h((posQuay && posQuay.ten) || k.quay || '') + '<br>Ngày ' + h(k.ngay || '') + ' · in lúc ' + lucIn + '<br>Người chốt: ' + h(S.me.full_name || String(S.user).split('@')[0]) + '</div>' +
    '<hr><div class="s">TIỀN THEO PHƯƠNG THỨC</div>' + (thanPt || dd('Chưa có hoá đơn', '')) +
    '<hr><div class="s">ĐỐI SOÁT CHUYỂN KHOẢN</div>' +
    dd('SePay đã nhận', money(k.ck_ve || 0) + ' đ') + (thanThieu || dd('Không hoá đơn nào thiếu', '&#10003;')) +
    '<hr><div class="s">SỔ SÁCH</div>' +
    dd('Đã ghi sổ', (k.da_ghi || 0) + ' hoá đơn') + dd('Chưa ghi sổ', (k.chua_ghi || 0) + ' hoá đơn') +
    dd('Tạm tính còn treo', tt.so + ' hoá đơn · ' + money(tt.tien) + ' đ') +
    '<hr>' + dd('TỔNG DOANH THU', money(k.tong_tien || 0) + ' đ') +
    '<div style="margin-top:6mm;display:flex;justify-content:space-between;font-size:10.5px;text-align:center"><span>Người giao ca<br><br><br>____________</span><span>Người nhận ca<br><br><br>____________</span></div>' +
    '<script>window.onload=function(){setTimeout(function(){window.print()},900)}<' + '/script>' +
    '</body></html>');
  w.document.close();
}

/* ---------- Hop dong Event: catering, teabreak, banh thiet ke ---------- */
var hdLoc = null;
async function scrHopDong() {
  frame('Hợp đồng Event', '<div class="emp"><div class="e1">⏳</div><div>Đang tải hợp đồng...</div></div>');
  var ds;
  try { ds = await api('vagabond.hop_dong.danh_sach', hdLoc ? { trang_thai: hdLoc } : {}); }
  catch (e) { frame('Hợp đồng Event', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var html = '<div class="card" style="padding:12px 14px;display:flex;align-items:center;gap:12px">' +
    '<div style="font-weight:600">Trạng thái</div>' +
    '<button class="btn gh" id="hdLoc" style="flex:1;margin:0">' + h(hdLoc || 'Tất cả') + ' ▾</button></div>';
  html += '<div class="sec">' + ds.length + ' hợp đồng · bấm vào để xem chi tiết</div><div class="card">';
  if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">📑</div><div>Chưa có hợp đồng nào. Bấm dấu ➕ để tạo.</div></div>';
  var HDICON = { 'Nháp': '📝', 'Đang thực hiện': '🚚', 'Hoàn tất': '✅', 'Đã thanh lý': '🧾', 'Huỷ': '⛔' };
  ds.forEach(function (r) {
    html += '<div class="hub" data-hd="' + h(r.name) + '"><div class="hi">' + (HDICON[r.trang_thai] || '📑') + '</div>' +
      '<div class="ht"><div class="h1">' + h(r.ten) + '</div>' +
      '<div class="h2">' + h(r.so_hop_dong || r.name) + (r.khach_hang ? ' · ' + h(r.khach_hang) : '') + ' · ' + h(r.trang_thai) + '</div>' +
      '<div class="h2">Giá trị ' + money(r.gia_tri) + ' · đã xuất ' + money(r.da_xuat) + ' · đã thu ' + money(r.da_thu) + '</div></div></div>';
  });
  html += '</div>';
  var b = frame('Hợp đồng Event', html, { action: '➕', onAction: function () { go(scrHdTao); } });
  document.getElementById('hdLoc').onclick = function () {
    sheet('Lọc trạng thái', [
      { value: '', label: 'Tất cả', icon: '📚' },
      { value: 'Nháp', label: 'Nháp', icon: '📝' },
      { value: 'Đang thực hiện', label: 'Đang thực hiện', icon: '🚚' },
      { value: 'Hoàn tất', label: 'Hoàn tất', icon: '✅' },
      { value: 'Đã thanh lý', label: 'Đã thanh lý', icon: '🧾' },
      { value: 'Huỷ', label: 'Huỷ', icon: '⛔' }
    ], hdLoc || '', function (o) { hdLoc = o.value || null; go(scrHopDong, true); });
  };
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-hd]'); if (!r) return;
    var nm = r.getAttribute('data-hd');
    go(function () { scrHdView(nm); });
  });
}

async function scrHdView(name) {
  frame('Chi tiết hợp đồng', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.hop_dong.chi_tiet', { name: name }); }
  catch (e) { frame('Chi tiết hợp đồng', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>'); return; }
  var hd = d.hop_dong;
  var vn = function (s) { var p = String(s || '').split('-'); return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : (s || ''); };
  var html = '<div class="card" style="padding:12px 14px;line-height:1.7">' +
    '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center"><b style="flex:1">' + h(hd.ten) + '</b><button class="btn gh" id="hdTt" style="margin:0;padding:4px 10px;font-size:13px;width:auto;flex:none;white-space:nowrap">' + h(hd.trang_thai) + ' ▾</button></div>' +
    '<div style="color:#6b7280;font-size:13px">' + h(hd.name) + (hd.so_hop_dong ? ' · Số HĐ: <b>' + h(hd.so_hop_dong) + '</b>' : '') + '</div>' +
    '<div style="font-size:13px">' + h(hd.loai || '') + (hd.khach_hang ? ' · ' + h(hd.khach_hang) : '') + '</div>' +
    ((hd.ngay_ky || hd.ngay_su_kien) ? '<div style="font-size:13px">' + (hd.ngay_ky ? 'Ký ' + vn(hd.ngay_ky) : '') + (hd.ngay_su_kien ? ' · Sự kiện ' + vn(hd.ngay_su_kien) : '') + '</div>' : '') +
    (hd.mo_ta ? '<div style="font-size:13px;color:#6b7280;white-space:pre-wrap;margin-top:4px">' + h(hd.mo_ta) + '</div>' : '') +
    '</div>';
  html += '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between"><span>Giá trị hợp đồng</span><b>' + money(hd.gia_tri) + ' đ</b></div>' +
    '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Đã xuất hoá đơn</span><b>' + money(d.da_xuat) + ' đ · ' + d.so_hd_chot + ' chốt' + (d.so_hd_nhap ? ' + ' + d.so_hd_nhap + ' nháp' : '') + '</b></div>' +
    '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Đã thu</span><b style="color:#0a8a4a">' + money(d.da_thu) + ' đ</b></div>' +
    '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Còn phải thu</span><b style="color:#b3261e">' + money(d.con_no) + ' đ</b></div></div>';
  html += '<div class="sec">Hoá đơn thuộc hợp đồng · bấm vào để xem hoặc gỡ</div><div class="card">';
  if (!d.hoa_don.length) html += '<div class="emp" style="padding:20px"><div class="e1">🧾</div><div>Chưa gắn hoá đơn nào.</div></div>';
  d.hoa_don.forEach(function (r) {
    html += '<div class="hub" data-si="' + h(r.name) + '"><div class="hi">' + (r.docstatus === 1 ? '✅' : '📝') + '</div>' +
      '<div class="ht"><div class="h1">' + h(r.name) + '</div><div class="h2">' + vn(r.posting_date) + ' · ' + h(r.customer_name || '') + '</div></div>' +
      '<b style="white-space:nowrap;font-size:13px">' + money(r.grand_total) + '</b></div>';
  });
  html += '</div>';
  var b = frame('Chi tiết hợp đồng', html, { footer: '<button class="btn" id="hdGan">🔗 Gắn hoá đơn vào hợp đồng</button>' });
  document.getElementById('hdTt').onclick = function () {
    sheet('Đổi trạng thái', ['Nháp', 'Đang thực hiện', 'Hoàn tất', 'Đã thanh lý', 'Huỷ'].map(function (t) { return { value: t, label: t, icon: '📌' }; }), hd.trang_thai, async function (o) {
      busy(true);
      try { await api('vagabond.hop_dong.doi_trang_thai', { name: name, trang_thai: o.value }); busy(false); }
      catch (e) { busy(false); window.alert((e && e.message) || 'Lỗi'); }
      go(function () { scrHdView(name); }, true);
    });
  };
  document.getElementById('hdGan').onclick = async function () {
    busy(true);
    var cg;
    try { cg = await api('vagabond.hop_dong.hoa_don_chua_gan', hd.khach_hang ? { khach_hang: hd.khach_hang } : {}); }
    catch (e) { busy(false); return window.alert((e && e.message) || 'Lỗi'); }
    busy(false);
    if (!cg.length) return window.alert('Không có hoá đơn nào chưa gắn trong 90 ngày gần nhất' + (hd.khach_hang ? ' của khách ' + hd.khach_hang : '') + '.');
    sheet('Chọn hoá đơn để gắn', cg.map(function (x) { return { value: x.name, label: x.name + ' · ' + (x.customer_name || '') + ' · ' + money(x.grand_total) + ' đ', icon: x.docstatus === 1 ? '✅' : '📝' }; }), null, async function (o) {
      busy(true);
      try { await api('vagabond.hop_dong.gan_hoa_don', { hop_dong: name, si_name: o.value }); busy(false); toast('Đã gắn ' + o.value); }
      catch (e) { busy(false); window.alert((e && e.message) || 'Lỗi'); }
      go(function () { scrHdView(name); }, true);
    }, true);
  };
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-si]'); if (!r) return;
    var nm = r.getAttribute('data-si');
    sheet('Hoá đơn ' + nm, [
      { value: 'xem', label: 'Xem chi tiết hoá đơn', icon: '👁️' },
      { value: 'go', label: 'Gỡ khỏi hợp đồng', icon: '✂️' }
    ], null, async function (o) {
      if (o.value === 'xem') return go(function () { scrDsView(nm, false); });
      busy(true);
      try { await api('vagabond.hop_dong.gan_hoa_don', { hop_dong: name, si_name: nm, go: 1 }); busy(false); toast('Đã gỡ ' + nm); }
      catch (e) { busy(false); window.alert((e && e.message) || 'Lỗi'); }
      go(function () { scrHdView(name); }, true);
    });
  });
}

var hdTay = null;
function hdTaoDoc() {
  if (!hdTay) return;
  var g = function (id) { var el = document.getElementById(id); return el ? el.value : ''; };
  hdTay.ten = g('hdtTen'); hdTay.so = g('hdtSo'); hdTay.giatri = g('hdtGiaTri'); hdTay.ngayky = g('hdtNgayKy'); hdTay.ngaysk = g('hdtNgaySk'); hdTay.mota = g('hdtMoTa');
}
async function scrHdTao() {
  if (!hdTay) hdTay = { ten: '', so: '', loai: 'Event - Catering', khach: '', giatri: '', ngayky: today(), ngaysk: '', mota: '' };
  var html = '<div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    '<input class="tin" id="hdtTen" placeholder="Tên hợp đồng / sự kiện (bắt buộc)" value="' + h(hdTay.ten) + '">' +
    '<input class="tin" id="hdtSo" placeholder="Số hợp đồng (vd 026-022/PYR-VAGABOND)" value="' + h(hdTay.so) + '">' +
    '<div class="hub" data-t="loai" style="padding:10px 0;border:none"><div class="ht"><div class="h2">Loại</div><div class="h1">' + h(hdTay.loai) + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    '<div class="hub" data-t="khach" style="padding:10px 0;border:none"><div class="ht"><div class="h2">Khách hàng</div><div class="h1">' + h(hdTay.khach || 'Chọn khách...') + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    '<input class="tin" id="hdtGiaTri" placeholder="Giá trị hợp đồng (đ)" inputmode="numeric" value="' + h(hdTay.giatri) + '">' +
    '</div>';
  html += '<div class="sec">Ngày</div><div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    '<div style="display:flex;flex-direction:row;align-items:center;gap:10px"><span style="width:90px">Ngày ký</span><input type="date" class="hin" id="hdtNgayKy" value="' + h(hdTay.ngayky) + '" style="flex:1;margin:0"></div>' +
    '<div style="display:flex;flex-direction:row;align-items:center;gap:10px"><span style="width:90px">Sự kiện</span><input type="date" class="hin" id="hdtNgaySk" value="' + h(hdTay.ngaysk) + '" style="flex:1;margin:0"></div></div>';
  html += '<div class="sec">Nội dung (đúng câu chữ hợp đồng, dùng cho hoá đơn)</div><div class="card" style="padding:12px 14px">' +
    '<textarea class="tin" id="hdtMoTa" rows="3" placeholder="Vd: Cung cấp gói tea break 120 khách theo hợp đồng số...">' + h(hdTay.mota) + '</textarea></div>';
  var b = frame('Tạo hợp đồng', html, { footer: '<button class="btn" id="hdtLuu">Lưu hợp đồng</button>' });
  b.addEventListener('click', async function (e) {
    if (e.target.closest('[data-t="loai"]')) {
      hdTaoDoc();
      return sheet('Loại hợp đồng', ['Event - Catering', 'Teabreak', 'Bánh thiết kế', 'B2B sỉ', 'Khác'].map(function (t) { return { value: t, label: t, icon: '📑' }; }), hdTay.loai, function (o) { hdTay.loai = o.value; go(scrHdTao, true); });
    }
    if (e.target.closest('[data-t="khach"]')) {
      hdTaoDoc(); busy(true);
      var kh;
      try { kh = await getList('Customer', { fields: ['name', 'customer_name'], filters: { disabled: 0 }, limit_page_length: 0, order_by: 'customer_name' }); }
      catch (er) { busy(false); return window.alert('Không tải được danh sách khách'); }
      busy(false);
      return sheet('Chọn khách hàng', kh.map(function (x) { return { value: x.name, label: x.customer_name || x.name, icon: '👤' }; }), hdTay.khach, function (o) { hdTay.khach = o.value; go(scrHdTao, true); }, true);
    }
  });
  document.getElementById('hdtLuu').onclick = async function () {
    hdTaoDoc();
    if (!hdTay.ten.trim()) return window.alert('Nhập tên hợp đồng đã nhé.');
    busy(true);
    try {
      var nm = await api('vagabond.hop_dong.tao', { ten: hdTay.ten.trim(), so_hop_dong: hdTay.so.trim(), loai: hdTay.loai, khach_hang: hdTay.khach || '', ngay_ky: hdTay.ngayky || '', ngay_su_kien: hdTay.ngaysk || '', gia_tri: parseFloat(hdTay.giatri || 0) || 0, mo_ta: hdTay.mota });
      busy(false); toast('Đã tạo hợp đồng'); hdTay = null;
      go(function () { scrHdView(nm); }, true);
    } catch (e) { busy(false); window.alert((e && e.message) || 'Lưu lỗi'); }
  };
}


/* ---------- Van don: sales phan don, shipper giao kem anh, book xe, chi phi ---------- */
var vdNgay = null, vdLoc = null, vdTay = null;
function vdChupAnh(cb, nguon) {
  var inp = document.createElement('input');
  inp.type = 'file'; inp.accept = 'image/*';
  // Bo capture thi iOS va Android deu hien bang chon: chup anh moi HOAC
  // lay anh co san trong album. Truyen nguon la 'camera' neu cho nao do
  // muon ep mo thang camera.
  if (nguon === 'camera') inp.setAttribute('capture', 'environment');
  inp.onchange = function () {
    var f = inp.files && inp.files[0]; inp.remove(); if (!f) return;
    busy(true);
    var img = new Image();
    var url = URL.createObjectURL(f);
    img.onload = function () {
      var max = 1280, w = img.width, h2 = img.height;
      if (w >= h2 && w > max) { h2 = Math.round(h2 * max / w); w = max; }
      else if (h2 > w && h2 > max) { w = Math.round(w * max / h2); h2 = max; }
      var cv = document.createElement('canvas'); cv.width = w; cv.height = h2;
      cv.getContext('2d').drawImage(img, 0, 0, w, h2);
      cv.toBlob(function (b) { URL.revokeObjectURL(url); cb(b); }, 'image/jpeg', 0.72);
    };
    img.onerror = function () { busy(false); window.alert('Không đọc được ảnh, chụp lại giúp em.'); };
    img.src = url;
  };
  inp.style.display = 'none'; document.body.appendChild(inp); inp.click();
}
async function vdUpload(blob, doctype, docname, fieldname) {
  var fd = new FormData();
  fd.append('file', new File([blob], 'giao-' + docname + '-' + Date.now() + '.jpg', { type: 'image/jpeg' }));
  fd.append('is_private', '1');
  fd.append('doctype', doctype);
  fd.append('docname', docname);
  fd.append('fieldname', fieldname);
  var hd = {};
  hd['X-Frappe-' + 'CSRF-' + 'Token'] = frappe.csrf_token;
  var r = await fetch('/api/method/upload_file', { method: 'POST', headers: hd, body: fd });
  var j = await r.json();
  if (!r.ok || !j.message) throw new Error('Upload ảnh lỗi');
  return j.message.file_url;
}
function vdLaShipper() { return hasRole('Shipper'); }
function vdLaKeToan() { return hasRole('Accounts User') || hasRole('Purchase User') || hasRole('System Manager'); }

async function scrVanDon() {
  vdTuLamMoi();
  if (!vdNgay) vdNgay = today();
  frame('Vận đơn', '<div class="emp"><div class="e1">⏳</div><div>Đang tải vận đơn...</div></div>');
  var ds;
  try { ds = await api('vagabond.van_don.danh_sach', vdThamSo()); try { vdBoLoc = await api('vagabond.van_don.bo_loc', { ngay: vdNgay }); } catch (e9) { vdBoLoc = null; }
  if (!vtShipper) { try { vtShipper = await api('vagabond.van_don.ds_shipper'); } catch (e10) { vtShipper = []; } } }
  catch (e) { frame('Vận đơn', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var chonMode = !!window.vdChon;
  /* Hai nut lui/toi mot ngay: tren dien thoai bam nhanh hon mo bang chon
     ngay, va khong dinh loi bang chon ngay lam trang bi ve lai. */
  var html = '<div class="card" style="padding:12px 14px;display:flex;flex-direction:row;align-items:center;gap:8px">' +
    '<button class="btn gh" id="vdLui" style="margin:0;width:auto;padding:8px 13px;flex:0 0 auto">◀</button>' +
    '<input type="date" class="hin" id="vdDate" value="' + vdNgay + '" style="flex:1;margin:0;min-width:0">' +
    '<button class="btn gh" id="vdToi" style="margin:0;width:auto;padding:8px 13px;flex:0 0 auto">▶</button>' +
    '<button class="btn gh" id="vdLoc" style="flex:1;margin:0;width:auto;min-width:0">' + h(vdLoc || 'Tất cả') + ' ▾</button></div>';
  if (isSales() || vdLaKeToan()) html += '<button class="btn gh" id="vdDongBo" style="margin:0 0 10px">🔄 Đồng bộ đơn Pancake ngày ' + vdNgay.split('-').reverse().join('/') + '</button>';
  var ICON = VD_TT_ICON;
  if (chonMode) html += '<div class="sec" style="color:#0369a1">' + (window.vdChonDe === 'in' ? 'ĐANG CHỌN ĐƠN ĐỂ IN' : 'ĐANG GỘP CHUYẾN') + ' - BẤM VÀO TỪNG ĐƠN ĐỂ CHỌN</div>';
  else html += '<div class="sec">' + ds.length + ' vận đơn · bấm vào để xử lý</div>';
  html += vdChipsHtml();
  html += '<div class="card">';
  if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">🛵</div><div>Chưa có vận đơn nào cho ngày này.</div></div>';
  ds.forEach(function (r) {
    var daChon = chonMode && window.vdChon[r.name];
    /* Trang thai da co chip mau ben duoi nen bo khoi dong chu xam nay. */
    var d2 = (r.tag_gio ? '\u{1F552} ' + h(r.tag_gio) + ' · ' : (r.gio_giao ? r.gio_giao + ' · ' : '')) + (r.phuong ? h(vdPhuongNgan(r.phuong)) + ' · ' : '') + h(r.kenh) + (r.shipper ? ' · ' + h(vdTen(r.shipper)) : '') + (r.chuyen ? ' · 🧺' + h(r.chuyen) : '');
    /* Ten mon rut gon: mon dau + "còn N món". Ten day du xem trong chi tiet. */
    var mon1 = r.mon_chinh ? (h(r.mon_chinh) + (r.so_mon > 1 ? ' · còn ' + (r.so_mon - 1) + ' món' : '')) : h(r.mon_tat || '');
    var oAnh = daChon ? '☑️'
      : (r.anh ? '<img src="' + h(r.anh) + '" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:13px;display:block" onerror="this.style.display=\'none\'">'
              : (ICON[r.trang_thai] || '📦'));
    html += '<div class="hub" data-vd="' + h(r.name) + '" data-tt="' + h(r.trang_thai) + '"' + (daChon ? ' style="background:#dbeafe"' : '') + '><div class="hi" style="overflow:hidden">' + oAnh + '</div>' +
      '<div class="ht"><div class="h1">' + (r.ma_don ? '#' + h(r.ma_don) + ' · ' : '') + h(r.khach || 'Khách lẻ') + '</div>' +
      '<div class="h2">' + d2 + '</div>' +
      '<div class="h2">' + h((r.dia_chi || '').slice(0, 70)) + '</div>' +
      (mon1 ? '<div class="h2" style="color:#7a5b2e">🎂 ' + mon1 + '</div>' : '') + vdHuyHieu(r) + '</div>' +
      '<div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;flex:0 0 auto">'
      + (r.tien_thu_ho ? '<b style="white-space:nowrap;font-size:13px">COD ' + money(r.tien_thu_ho) + '</b>' : '')
      + vdNutDong(r, chonMode) + '</div></div>';
  });
  html += '</div>';
  var foot = '';
  if (chonMode) {
    foot = '<div style="display:flex;gap:10px"><button class="btn" id="vdGan" style="flex:2">'
      + (window.vdChonDe === 'in' ? '🖨️ In ' : '✅ Gán ') + Object.keys(window.vdChon).length + ' đơn</button>'
      + '<button class="btn gh" id="vdThoi" style="flex:1">✖ Thôi</button></div>';
  } else {
    var nutF = [];
    if (vdLaShipper() || vdLaKeToan()) nutF.push('<button class="btn gh" id="vdCp" style="flex:1">⛽ Chi phí</button>');
    if (isSales()) nutF.push('<button class="btn gh" id="vdGop" style="flex:1">🧺 Gộp chuyến</button>');
    if (isSales()) nutF.push('<button class="btn gh" id="vdTuyen" style="flex:1">🧭 Xếp tuyến</button>');
    nutF.push('<button class="btn gh" id="vdIn" style="flex:1">🖨️ In đơn</button>');
    if (vdLaShipper() && !isSales()) nutF.push('<button class="btn gh" id="vdDuong" style="flex:1">🗺️ Chỉ đường</button>');
    if (isSales() || vdLaKeToan()) nutF.push('<button class="btn gh" id="vdCod" style="flex:1">💵 Đối soát COD</button>');
    if (nutF.length) foot = '<div style="display:flex;gap:8px">' + nutF.join('') + '</div>';
  }
  var b = frame('Vận đơn', html, Object.assign({ action: '➕', onAction: function () { go(scrVdTao); } }, foot ? { footer: foot } : {}));
  var di = document.getElementById('vdDate');
  if (di) di.onchange = function () { if (di.value) { vdNgay = di.value; go(scrVanDon, true); } };
  function vdDoiNgay(buoc) {
    var t = new Date((vdNgay || today()) + 'T00:00:00');
    t.setDate(t.getDate() + buoc);
    vdNgay = t.getFullYear() + '-' + String(t.getMonth() + 1).padStart(2, '0') + '-' + String(t.getDate()).padStart(2, '0');
    go(scrVanDon, true);
  }
  var bLui = document.getElementById('vdLui'); if (bLui) bLui.onclick = function () { vdDoiNgay(-1); };
  var bToi = document.getElementById('vdToi'); if (bToi) bToi.onclick = function () { vdDoiNgay(1); };
  document.getElementById('vdLoc').onclick = function () {
    sheet('Lọc trạng thái', [
      { value: '', label: 'Tất cả', icon: '📚' },
      { value: 'Chờ giao', label: 'Chờ giao', icon: '📦' },
      { value: 'Đang giao', label: 'Đang giao', icon: '🛵' },
      { value: 'Đã giao', label: 'Đã giao', icon: '✅' },
      { value: 'Không giao được', label: 'Không giao được', icon: '⚠️' }
    ], vdLoc || '', function (o) { vdLoc = o.value || null; go(scrVanDon, true); });
  };
  vdGanChips();
  var btq = document.getElementById('vdTuyen'); if (btq) btq.onclick = function () { go(scrVdTuyen, true); };
  var bcd = document.getElementById('vdDuong'); if (bcd) bcd.onclick = vdChiDuongToi;
  var db = document.getElementById('vdDongBo');
    if (db) db.onclick = async function () {
      busy(true);
      try {
        var kq = await api('vagabond.van_don.dong_bo_pancake', { ngay: vdNgay });
        busy(false);
        toast(kq.them ? ('Đã kéo về ' + kq.them + ' vận đơn mới') : ('Không có đơn mới - ' + (kq.da_co || 0) + ' đơn đã kéo về trước đó'), 3200);
        go(scrVanDon, true);
      } catch (e) {
        busy(false);
        window.alert((e && e.message) || 'Đồng bộ Pancake lỗi');
      }
    };
    var cp = document.getElementById('vdCp');
  if (cp) cp.onclick = function () { go(scrVdChiPhi); };
  var gp = document.getElementById('vdGop');
  if (gp) gp.onclick = function () { window.vdChon = {}; window.vdChonDe = 'gan'; go(scrVanDon, true); };
  var bin = document.getElementById('vdIn');
  if (bin) bin.onclick = function () { window.vdChon = {}; window.vdChonDe = 'in'; go(scrVanDon, true); };
  var cod = document.getElementById('vdCod');
  if (cod) cod.onclick = function () { go(scrVdCod); };
  var th = document.getElementById('vdThoi');
  if (th) th.onclick = function () { window.vdChon = null; go(scrVanDon, true); };
  var gan = document.getElementById('vdGan');
  if (gan) gan.onclick = async function () {
    var names = Object.keys(window.vdChon || {});
    if (window.vdChonDe === 'in') {
      if (!names.length) return toast('Chưa chọn đơn nào để in.');
      window.vdChon = null; window.vdChonDe = null;
      await vdInPhieu(names);
      go(scrVanDon, true);
      return;
    }
    if (!names.length) return toast('Chưa chọn đơn nào, bấm vào các đơn cần gộp trước.');
    var ships;
    try { ships = await api('vagabond.van_don.ds_shipper', {}); } catch (er) { return window.alert((er && er.message) || 'Lỗi'); }
    if (!ships.length) return window.alert('Chưa có tài khoản nào gắn role Shipper. Anh Việt tạo user shipper trước.');
    var chot = async function (shipper, chuyen) {
      busy(true);
      try {
        var kq = await api('vagabond.van_don.gop_chuyen', { names: JSON.stringify(names), shipper: shipper, chuyen: chuyen || '' });
        busy(false);
        toast('Đã gộp ' + kq.so_don + ' đơn vào chuyến ' + kq.chuyen + (kq.bo_qua && kq.bo_qua.length ? ' · bỏ qua: ' + kq.bo_qua.join(', ') : ''), 4500);
      } catch (er) { busy(false); return window.alert((er && er.message) || 'Gộp lỗi'); }
      window.vdChon = null;
      go(scrVanDon, true);
    };
    sheet('Giao chuyến cho shipper nào?', ships.map(function (s) { return { value: s.user, label: s.ten, icon: '🛵' }; }), null, async function (o) {
      var chay = [];
      try { chay = (await api('vagabond.van_don.chuyen_dang_chay', { ngay: vdNgay })).filter(function (x) { return x.shipper === o.value; }); } catch (er) {}
      if (!chay.length) return chot(o.value, '');
      sheet('Chuyến mới hay chèn vào chuyến đang chạy?', [{ value: '', label: 'Chuyến mới', icon: '🆕' }].concat(chay.map(function (x) { return { value: x.chuyen, label: 'Chèn vào ' + x.chuyen + ' (' + x.so_don + ' đơn đang chạy)', icon: '➕' }; })), null, function (o2) { chot(o.value, o2.value); });
    });
  };
  b.addEventListener('click', function (e) {
    var r = e.target.closest('[data-vd]'); if (!r) return;
    var nutN = e.target.closest('[data-di],[data-pc]');
    if (nutN && !window.vdChon) {
      e.stopPropagation();
      if (nutN.hasAttribute('data-di')) { vdMoDuong(nutN.getAttribute('data-di')); return; }
      vdChonShipper(r.getAttribute('data-vd'));
      return;
    }
    var nm = r.getAttribute('data-vd');
    if (window.vdChon) {
      var tt = r.getAttribute('data-tt');
      if (tt !== 'Chờ giao' && tt !== 'Đang giao') return toast('Đơn ' + tt + ' không gộp chuyến được.');
      if (window.vdChon[nm]) { delete window.vdChon[nm]; r.style.background = ''; r.querySelector('.hi').textContent = '📦'; }
      else { window.vdChon[nm] = 1; r.style.background = '#dbeafe'; r.querySelector('.hi').textContent = '☑️'; }
      var g2 = document.getElementById('vdGan');
      if (g2) g2.textContent = (window.vdChonDe === 'in' ? '🖨️ In ' : '✅ Gán ') + Object.keys(window.vdChon).length + ' đơn';
      return;
    }
    go(function () { scrVdView(nm); });
  });
}

async function scrVdCod() {
  frame('Đối soát COD', '<div class="emp"><div class="e1">⏳</div></div>');
  var ng = vdNgay || today();
  var ds;
  try { ds = await api('vagabond.van_don.doi_soat_cod', { ngay: ng }); }
  catch (e) { frame('Đối soát COD', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'); return; }
  var html = '<div class="card" style="padding:12px 14px"><input type="date" class="hin" id="codDate" value="' + ng + '" style="margin:0"></div>';
  if (!ds.length) html += '<div class="emp"><div class="e1">💵</div><div>Chưa có đơn Đã giao nào trong ngày này.</div></div>';
  ds.forEach(function (g) {
    html += '<div class="sec">' + h(g.ten) + ' · ' + g.so_don + ' đơn đã giao</div><div class="card" style="padding:12px 14px;line-height:1.9">';
    g.don.forEach(function (d) {
      html += '<div style="display:flex;justify-content:space-between;font-size:13px;gap:8px"><span>' + (d.ma_don ? '#' + h(d.ma_don) : h(d.name)) + ' · ' + h(d.khach || 'Khách lẻ') + (d.chuyen ? ' · 🧺' + h(d.chuyen) : '') + '</span><span style="white-space:nowrap">' + (d.cod ? money(d.cod) : '0') + (d.da_doi_soat ? ' ✅' : '') + '</span></div>';
    });
    html += '<div style="display:flex;justify-content:space-between;margin-top:6px;border-top:1px solid #e5e7eb;padding-top:6px"><b>Tổng COD</b><b>' + money(g.tong_cod) + ' đ</b></div>';
    if (g.chua_doi_soat > 0) html += '<div style="display:flex;justify-content:space-between;color:#b3261e"><span>Chưa nộp về</span><b>' + money(g.chua_doi_soat) + ' đ</b></div>';
    else if (g.tong_cod > 0) html += '<div style="color:#15803d;font-size:13px">Đã đối soát đủ ✅</div>';
    if (vdLaKeToan() && g.so_don_chua > 0 && g.shipper.indexOf('@') > -1)
      html += '<button class="btn" data-cod="' + h(g.shipper) + '" style="margin-top:8px">✔ Đã nhận đủ ' + money(g.chua_doi_soat) + ' đ từ ' + h(g.ten) + '</button>';
    html += '</div>';
  });
  var b = frame('Đối soát COD', html);
  var di = document.getElementById('codDate');
  if (di) di.onchange = function () { if (di.value) { vdNgay = di.value; go(scrVdCod, true); } };
  b.addEventListener('click', async function (e) {
    var el = e.target.closest('[data-cod]'); if (!el) return;
    if (!window.confirm('Xác nhận ĐÃ NHẬN ĐỦ tiền COD shipper nộp về? Toàn bộ đơn Đã giao của bạn này trong ngày sẽ được đánh dấu đã đối soát.')) return;
    busy(true);
    try {
      var kq = await api('vagabond.van_don.xac_nhan_cod', { shipper: el.getAttribute('data-cod'), ngay: vdNgay || today() });
      busy(false);
      toast('Đã xác nhận ' + kq.so_don + ' đơn · ' + money(kq.tong) + ' đ', 3500);
    } catch (er) { busy(false); window.alert((er && er.message) || 'Lỗi'); }
    go(scrVdCod, true);
  });
}

function vdGioNgan(t) {
  var s = String(t || '');
  if (s.length < 16) return s;
  return s.slice(11, 16) + ' ngày ' + s.slice(8, 10) + '/' + s.slice(5, 7);
}
/* Man khach ky tay. May chu nhan data URL PNG cua the canvas roi luu thanh
   tep dinh kem (vagabond.van_don.luu_chu_ky). */
function scrVdKy(name, d) {
  var html = '<div class="card" style="padding:12px 14px;line-height:1.6">' +
    '<div><b>' + (d.ma_don ? '#' + h(d.ma_don) : h(name)) + '</b> · ' + h(d.khach || 'Khách lẻ') + '</div>' +
    (d.dia_chi ? '<div style="color:#6b7280;font-size:13px">' + h(d.dia_chi) + '</div>' : '') +
    (d.tien_thu_ho ? '<div><b>Thu hộ (COD): ' + money(d.tien_thu_ho) + ' đ</b></div>' : '') + '</div>';
  html += '<div class="card" style="padding:12px 14px">' +
    '<input class="tin" id="vdkTen" placeholder="Tên người ký" value="' + h(d.nguoi_nhan || d.khach || '') + '">' +
    '<div style="font-size:12px;color:#6b7280;margin:10px 0 6px">Mời khách ký vào khung dưới</div>' +
    '<canvas id="vdkCanvas" style="width:100%;height:200px;background:#fff;border:1.5px dashed #b9c7cc;border-radius:12px;touch-action:none;display:block"></canvas>' +
    '</div>';
  frame('Khách ký nhận', html, { footer: '<div style="display:flex;gap:8px"><button class="btn gh" id="vdkXoa" style="flex:1">Xoá nét</button><button class="btn" id="vdkLuu" style="flex:2">Lưu chữ ký</button></div>' });
  setTimeout(function () {
    var cv = document.getElementById('vdkCanvas');
    if (!cv) return;
    var ctx = cv.getContext('2d');
    var tl = window.devicePixelRatio || 1;
    var rong = cv.clientWidth || cv.offsetWidth || 300, cao = cv.clientHeight || 200;
    cv.width = Math.round(rong * tl); cv.height = Math.round(cao * tl);
    ctx.scale(tl, tl);
    function xoa() { ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, rong, cao); }
    xoa();
    ctx.lineWidth = 2.2; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.strokeStyle = '#111827';
    var dangVe = false, daVe = false;
    function toa(ev) { var q = cv.getBoundingClientRect(); return { x: ev.clientX - q.left, y: ev.clientY - q.top }; }
    cv.addEventListener('pointerdown', function (ev) {
      ev.preventDefault(); dangVe = true; daVe = true;
      var p = toa(ev); ctx.beginPath(); ctx.moveTo(p.x, p.y);
      try { cv.setPointerCapture(ev.pointerId); } catch (e0) { }
    });
    cv.addEventListener('pointermove', function (ev) {
      if (!dangVe) return; ev.preventDefault();
      var p = toa(ev); ctx.lineTo(p.x, p.y); ctx.stroke();
    });
    cv.addEventListener('pointerup', function () { dangVe = false; });
    cv.addEventListener('pointercancel', function () { dangVe = false; });
    cv.addEventListener('pointerleave', function () { dangVe = false; });
    var bx = document.getElementById('vdkXoa');
    if (bx) bx.onclick = function () { xoa(); daVe = false; };
    var bl = document.getElementById('vdkLuu');
    if (bl) bl.onclick = async function () {
      if (!daVe) return window.alert('Chưa có nét ký nào, mời khách ký giúp em.');
      var ten = (document.getElementById('vdkTen') || {}).value || '';
      busy(true);
      try {
        await api('vagabond.van_don.luu_chu_ky', { name: name, anh: cv.toDataURL('image/png'), nguoi_ky: ten });
        busy(false); toast('Đã lưu chữ ký');
      } catch (er) { busy(false); return window.alert((er && er.message) || 'Lưu chữ ký lỗi'); }
      go(function () { scrVdView(name); }, true);
    };
  }, 0);
}
async function scrVdView(name) {
  frame('Chi tiết vận đơn', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('frappe.client.get', { doctype: 'Van Don', name: name }); if (!vtShipper) { try { vtShipper = await api('vagabond.van_don.ds_shipper'); } catch (e11) { vtShipper = []; } } }
  catch (e) { frame('Chi tiết vận đơn', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>'); return; }
  var html = '<div class="card" style="padding:12px 14px;line-height:1.7">' +
    '<div style="display:flex;justify-content:space-between"><b>' + (d.ma_don ? '#' + h(d.ma_don) : h(d.name)) + '</b><span>' + h(d.trang_thai) + '</span></div>' +
    '<div>' + h(d.khach || 'Khách lẻ') + (d.sdt ? ' · <a href="tel:' + h(d.sdt) + '">' + h(d.sdt) + '</a>' : '') + '</div>' +
    '<div style="font-size:13px">' + h(d.dia_chi || '(chưa có địa chỉ)') + '</div>' +
    '<div style="color:#6b7280;font-size:13px">' + h(d.kenh) + (d.gio_giao ? ' · khung ' + h(d.gio_giao) : '') + (d.shipper ? ' · ' + h(vdTen(d.shipper)) : '') + (d.chuyen ? ' · 🧺' + h(d.chuyen) : '') + '</div>' +
    ((d.mon && d.mon.length) ? '<div style="margin-top:8px;padding-top:8px;border-top:1px dashed #e5e7eb">' +
      '<div style="font-size:12px;color:#6b7280;letter-spacing:.4px">HÀNG TRONG ĐƠN</div>' +
      d.mon.map(function (m) {
        return '<div style="display:flex;gap:8px;align-items:flex-start;padding:4px 0">' +
          '<span style="flex:1;min-width:0"><b>' + h(m.ten || m.ma_hang || '') + '</b>' +
          (m.ma_hang ? '<span style="color:#a0a6b4;font-size:12px"> · ' + h(m.ma_hang) + '</span>' : '') +
          (m.tang ? '<span style="color:#b45309;font-size:12px"> · tặng</span>' : '') +
          (m.ghi_chu ? '<div style="color:#7a5b2e;font-size:12px;line-height:1.4">' + h(m.ghi_chu) + '</div>' : '') +
          '</span><b style="flex:none">&times;' + (m.so_luong || 0) + '</b></div>';
      }).join('') + '</div>' : '') +
    (d.tien_thu_ho ? '<div><b>Thu hộ (COD): ' + money(d.tien_thu_ho) + ' đ</b>' + (d.da_doi_soat ? ' <span style="color:#15803d;font-size:13px">đã đối soát ✅</span>' : '') + '</div>' : '') +
    (d.booking_id ? '<div style="font-size:13px">Mã app ngoài: ' + h(d.booking_id) + (d.tracking_url ? ' · <a href="' + h(d.tracking_url) + '" target="_blank">theo dõi</a>' : '') + '</div>' : '') +
    (d.hoa_don ? '<div style="color:#6b7280;font-size:13px">Hoá đơn: ' + h(d.hoa_don) + '</div>' : '') +
    (d.anh_giao ? '<div style="margin-top:10px">' +
      '<div style="font-size:12px;color:#6b7280;margin-bottom:5px">Ảnh giao thành công' + (d.da_bao_pancake ? ' · đã báo Pancake ✅' : '') + '</div>' +
      '<a href="' + h(d.anh_giao) + '" target="_blank" rel="noopener" style="display:inline-block">' +
      '<img src="' + h(d.anh_giao) + '" alt="Ảnh giao" style="width:118px;height:118px;object-fit:cover;border-radius:10px;border:1px solid #d7e6ea;display:block">' +
      '</a></div>' : '') +
    (d.chu_ky ? '<div style="margin-top:10px">' +
      '<div style="font-size:12px;color:#6b7280;margin-bottom:5px">✍️ Khách ký nhận' +
      (d.nguoi_ky ? ' · ' + h(d.nguoi_ky) : '') + (d.ky_luc ? ' · ' + h(vdGioNgan(d.ky_luc)) : '') + '</div>' +
      '<a href="' + h(d.chu_ky) + '" target="_blank" rel="noopener" style="display:inline-block">' +
      '<img src="' + h(d.chu_ky) + '" alt="Chữ ký khách" style="width:230px;max-width:100%;background:#fff;border:1px solid #d7e6ea;border-radius:10px;display:block">' +
      '</a></div>'
      : (d.khong_ky ? '<div style="color:#b45309;font-size:13px;margin-top:8px">✍️ Khách không ký: ' + h(d.khong_ky) + '</div>' : '')) +
    (d.ly_do_loi ? '<div style="color:#b3261e;font-size:13px">Không giao được: ' + h(d.ly_do_loi) + '</div>' : '') +
    (d.ghi_chu ? '<div style="color:#6b7280;font-size:13px;white-space:pre-wrap">' + h(d.ghi_chu) + '</div>' : '') + vdKhoiNhan(d) + '</div>' + vdNutPhanCong(d);
  var dangGiao = d.trang_thai === 'Chờ giao' || d.trang_thai === 'Đang giao';
  if (dangGiao) {
    html += '<button class="btn" data-va="giao" style="margin-top:4px">📷 Đã giao, chụp ảnh</button>';
    var hang = [];
    if (vdLaShipper() && !d.shipper) hang.push('<button class="btn gh" data-va="nhan" style="flex:1">🙋 Nhận đơn</button>');
    if (isSales() && !d.booking_id) hang.push('<button class="btn gh" data-va="book" style="flex:1">🚕 Book xe app</button>');
    hang.push('<button class="btn gh" data-va="loi" style="flex:1;color:#b3261e">⚠️ Không giao được</button>');
    html += '<div style="display:flex;gap:8px;padding:8px 0 0">' + hang.join('') + '</div>';
  }
  /* Chu ky la chung tu giao nhan: cho ky ca truoc va sau khi bam Da giao,
     chi giau di khi don da huy hoac da co chu ky. */
  if (!d.chu_ky && d.trang_thai !== 'Huỷ') {
    html += '<div style="display:flex;gap:8px;padding:8px 0 0">' +
      '<button class="btn gh" data-va="ky" style="flex:2">✍️ Khách ký nhận</button>' +
      (d.khong_ky ? '' : '<button class="btn gh" data-va="khongky" style="flex:1">Khách không ký</button>') +
      '</div>';
  }
  var b = frame('Chi tiết vận đơn', html);
  b.addEventListener('click', async function (e) {
    var el = e.target.closest('[data-va]'); if (!el) return;
    var k = el.getAttribute('data-va');
    if (k === 'chiduong') { vdMoDuong(vdDich(d)); return; }
    if (k === 'phancong') {
      if (!vtShipper) { busy(true); try { vtShipper = await api('vagabond.van_don.ds_shipper'); } catch (e7) { vtShipper = []; } busy(false); }
      var opsP = vdOpsGiao(vtShipper);
      sheet('Phân công đơn này cho ai', opsP, d.shipper || '', async function (o) {
        busy(true);
        try {
          var kq = await vdGanNguoiGiao(name, o);
          busy(false);
          if (kq.app) {
            if (kq.goiXe) { go(function () { scrVdGoiXe(name, kq.app); }); return; }
            toast('Đã ghi nhận đơn đi ' + kq.app);
          go(function () { scrVdView(name); }, true);
            return;
          }
          toast(o.value ? 'Đã phân công cho ' + o.label : 'Đã gỡ người giao khỏi đơn');
          go(function () { scrVdView(name); }, true);
        } catch (e8) { busy(false); window.alert((e8 && e8.message) || 'Phân công lỗi'); }
      });
      return;
    }
    if (k === 'ky') { return go(function () { scrVdKy(name, d); }); }
    if (k === 'khongky') {
      var lk = window.prompt('Vì sao khách không ký? (gửi bảo vệ, giao qua cửa, khách bận tay...)', 'Khách không ký');
      if (!lk) return;
      busy(true);
      try { await api('vagabond.van_don.khach_khong_ky', { name: name, ly_do: lk }); busy(false); toast('Đã ghi nhận'); }
      catch (er) { busy(false); window.alert((er && er.message) || 'Lỗi'); }
      return go(function () { scrVdView(name); }, true);
    }
    if (k === 'nhan') {
      busy(true);
      try { await api('vagabond.van_don.nhan_don', { name: name }); busy(false); toast('Đã nhận đơn'); }
      catch (er) { busy(false); window.alert((er && er.message) || 'Lỗi'); }
      return go(function () { scrVdView(name); }, true);
    }
    if (k === 'giao') {
      return vdChupAnh(async function (blob) {
        try {
          var fu = await vdUpload(blob, 'Van Don', name, 'anh_giao');
          var kq = await api('vagabond.van_don.giao_xong', { name: name, file_url: fu });
          busy(false);
          toast(kq.da_bao_pancake ? 'Đã giao + báo Pancake ✅' : 'Đã giao (Pancake chưa nhận được, sales kiểm lại)', 3500);
        } catch (er) { busy(false); window.alert((er && er.message) || 'Lỗi khi lưu ảnh giao'); }
        go(function () { scrVdView(name); }, true);
      });
    }
    if (k === 'loi') {
      var ld = window.prompt('Vì sao không giao được? (khách không nghe máy, sai địa chỉ...)', '');
      if (!ld) return;
      busy(true);
      try { await api('vagabond.van_don.giao_loi', { name: name, ly_do: ld }); busy(false); }
      catch (er) { busy(false); window.alert((er && er.message) || 'Lỗi'); }
      return go(function () { scrVdView(name); }, true);
    }
    if (k === 'book') {
      return sheet('Book xe qua app', [
        { value: 'Ahamove', label: 'Ahamove (chạy thật)', icon: '🔵' },
        { value: 'GreenSM', label: 'GreenSM (chờ key NDA)', icon: '🟢' },
        { value: 'BE', label: 'BE Delivery (chờ API)', icon: '🟡' }
      ], null, async function (o) {
        busy(true);
        try {
          var kq = await api('vagabond.van_don.book_xe', { name: name, kenh: o.value });
          busy(false);
          toast('Đã book ' + o.value + (kq.booking_id ? ' · mã ' + kq.booking_id : '') + (kq.phi_giao ? ' · phí ' + money(kq.phi_giao) : ''), 4000);
        } catch (er) { busy(false); window.alert((er && er.message) || 'Book lỗi'); }
        go(function () { scrVdView(name); }, true);
      });
    }
  });
}

var vdTay = null;
function vdTayDoc() {
  if (!vdTay) return;
  var g = function (id) { var el = document.getElementById(id); return el ? el.value : ''; };
  vdTay.ma = g('vdtMa'); vdTay.khach = g('vdtKhach'); vdTay.sdt = g('vdtSdt');
  vdTay.diachi = g('vdtDiaChi'); vdTay.cod = g('vdtCod');
  vdTay.ngay = g('vdtNgay') || vdTay.ngay;
}
var VD_KHUNG_GIO = ['7h - 9h', '8h - 10h', '9h - 11h', '10h - 12h', '11h - 13h', '12h - 14h', '13h - 15h', '14h - 16h', '15h - 17h', '16h - 18h', '17h - 19h', '18h - 20h', '19h - 21h'];
var VD_KENH_TAO = [
  { ten: 'Shipper nội bộ', icon: '🛵', mo: 'Shipper của tiệm, có xếp tuyến và đối soát COD' },
  { ten: 'Ahamove', mo: 'Gọi xe qua API, báo giá được trước khi book' },
  { ten: 'GreenSM', mo: 'Gọi xe qua API, đang chờ khoá đối tác' },
  { ten: 'BE', mo: 'Đặt tay trên app BE rồi ghi mã vào đơn' },
  { ten: 'Grab', mo: 'Đặt tay trên app Grab rồi ghi mã vào đơn' },
  { ten: 'Lalamove', mo: 'Đặt tay trên app Lalamove rồi ghi mã vào đơn' },
  { ten: 'Khách tự lấy', icon: '🏬', mo: 'Khách ra tiệm nhận, không cần shipper' }
];
async function scrVdTao() {
  if (!isSales()) return window.alert('Chỉ sales tạo được vận đơn.');
  if (!vdTay) vdTay = { si: '', ma: '', khach: '', sdt: '', diachi: '', ngay: vdNgay || today(), gio: '', kenh: 'Shipper nội bộ', cod: '' };
  var html = '<div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    '<div class="hub" data-t="si" style="padding:10px 0;border:none"><div class="ht"><div class="h2">Lấy từ hoá đơn (tự điền khách + địa chỉ Pancake)</div><div class="h1">' + h(vdTay.si || 'Chọn hoá đơn hoặc bỏ qua...') + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    '<input class="tin" id="vdtMa" placeholder="Số đơn (91xxx / GF-xxx)" value="' + h(vdTay.ma) + '">' +
    '<input class="tin" id="vdtKhach" placeholder="Tên khách" value="' + h(vdTay.khach) + '">' +
    '<input class="tin" id="vdtSdt" placeholder="SĐT khách" inputmode="tel" value="' + h(vdTay.sdt) + '">' +
    '<textarea class="tin" id="vdtDiaChi" rows="2" placeholder="Địa chỉ giao - gõ vài chữ rồi bấm gợi ý">' + h(vdTay.diachi) + '</textarea>' +
    '<div id="vdtGoiY" style="display:none;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden"></div>' +
    '<div id="vdtToaDo" style="font-size:12px;color:' + (vdTay.lat ? '#15803d' : '#a0a6b4') + '">' + (vdTay.lat ? '📍 Đã có toạ độ chính xác, xếp tuyến khỏi đoán' : 'Gõ địa chỉ rồi chọn gợi ý để lưu kèm toạ độ') + '</div>' +
    '<input class="tin" id="vdtCod" placeholder="Tiền thu hộ COD (đ), 0 nếu đã thanh toán" inputmode="numeric" value="' + h(vdTay.cod) + '">' +
    '</div>';
  html += '<div class="sec">Giao khi nào, kênh nào</div><div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    '<div style="display:flex;flex-direction:row;align-items:center;gap:10px"><span style="width:80px">Ngày giao</span><input type="date" class="hin" id="vdtNgay" value="' + h(vdTay.ngay) + '" style="flex:1;margin:0"></div>' +
    '<div class="hub" data-t="gio" style="padding:10px 0;border:none"><div class="ht"><div class="h2">Khung giờ giao</div><div class="h1">' + h(vdTay.gio || 'Chọn khung giờ...') + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    '<div class="hub" data-t="kenh" style="padding:10px 0;border:none"><div class="ht"><div class="h2">Kênh giao</div><div class="h1">' + h(vdTay.kenh) + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    '</div>';
  var b = frame('Tạo vận đơn', html, { footer: '<button class="btn" id="vdtLuu">Lưu vận đơn</button>' });
  b.addEventListener('click', async function (e) {
    if (e.target.closest('[data-t="si"]')) {
      vdTayDoc(); busy(true);
      var si;
      try { si = await getList('Sales Invoice', { fields: ['name', 'customer_name', 'grand_total', 'remarks', 'custom_pancake_display_id'], filters: { posting_date: ['>=', vdTay.ngay || today()], docstatus: ['<', 2], vgb_huy: 0 }, limit_page_length: 100, order_by: 'creation desc' }); }
      catch (er) { busy(false); return window.alert('Không tải được hoá đơn'); }
      busy(false);
      return sheet('Chọn hoá đơn', si.map(function (x) {
        var kh = (x.remarks || '').split(' - ');
        return { value: x.name, label: '#' + (x.custom_pancake_display_id || '?') + ' · ' + (kh[1] || x.customer_name || '') + ' · ' + money(x.grand_total) + ' đ', icon: '🧾' };
      }), vdTay.si, function (o) { vdTay.si = o.value; go(scrVdTao, true); }, true);
    }
    if (e.target.closest('[data-t="gio"]')) {
      vdTayDoc();
      var dsGio = [{ value: '', label: 'Không đặt khung giờ', icon: '🕓' }].concat(VD_KHUNG_GIO.map(function (t) { return { value: t, label: t, icon: '🕐' }; }));
      return sheet('Khung giờ giao', dsGio, vdTay.gio || '', function (o) { vdTay.gio = o.value; go(scrVdTao, true); });
    }
    if (e.target.closest('[data-t="kenh"]')) {
      vdTayDoc();
      return sheet('Kênh giao', VD_KENH_TAO.map(function (t) {
        var a = vdApp(t.ten); var it = { value: t.ten, label: t.ten, phu: t.mo };
        if (a) it.img = vdLogoApp(a); else it.icon = t.icon;
        return it;
      }), vdTay.kenh, function (o) { vdTay.kenh = o.value; go(scrVdTao, true); });
    }
  });
  var vdtTimer = null;
  var vdtOto = document.getElementById('vdtDiaChi');
  var vdtBox = document.getElementById('vdtGoiY');
  function vdtVeGoiY(ds) {
    if (!ds || !ds.length) { vdtBox.style.display = 'none'; vdtBox.innerHTML = ''; return; }
    vdtBox.innerHTML = ds.map(function (s, i) {
      return '<div data-gy="' + i + '" style="padding:10px 12px;border-bottom:1px solid #f1f2f4;cursor:pointer;font-size:14px">📍 ' + h(s.mo_ta) + '</div>';
    }).join('');
    vdtBox.style.display = 'block';
    vdtBox.onclick = async function (ev) {
      var el = ev.target.closest('[data-gy]');
      if (!el) return;
      var s = ds[parseInt(el.getAttribute('data-gy'), 10)];
      vdtBox.style.display = 'none';
      var td = document.getElementById('vdtToaDo');
      try {
        var ct = await api('vagabond.dia_chi.chi_tiet_dia_chi', { place_id: s.place_id });
        vdtOto.value = ct.dia_chi || s.mo_ta;
        vdTay.diachi = vdtOto.value; vdTay.lat = ct.lat || null; vdTay.lng = ct.lng || null;
        if (td) { td.innerHTML = vdTay.lat ? '📍 Đã có toạ độ chính xác, xếp tuyến khỏi đoán' : 'Chưa lấy được toạ độ, vẫn lưu được địa chỉ'; td.style.color = vdTay.lat ? '#15803d' : '#b45309'; }
      } catch (e) {
        vdtOto.value = s.mo_ta; vdTay.diachi = s.mo_ta;
        if (td) { td.innerHTML = 'Chưa lấy được toạ độ, vẫn lưu được địa chỉ'; td.style.color = '#b45309'; }
      }
    };
  }
  if (vdtOto) vdtOto.addEventListener('input', function () {
    vdTay.lat = null; vdTay.lng = null;
    if (vdtTimer) clearTimeout(vdtTimer);
    var q = (vdtOto.value || '').trim();
    if (q.length < 4) { vdtVeGoiY([]); return; }
    vdtTimer = setTimeout(async function () {
      try { var kq = await api('vagabond.dia_chi.goi_y_dia_chi', { q: q }); vdtVeGoiY((kq && kq.suggestions) || []); }
      catch (e) { vdtVeGoiY([]); }
    }, 450);
  });
  document.getElementById('vdtLuu').onclick = async function () {
    vdTayDoc();
    if (!vdTay.si && !vdTay.diachi.trim() && vdTay.kenh !== 'Khách tự lấy') return window.alert('Chọn hoá đơn hoặc nhập địa chỉ giao đã nhé.');
    busy(true);
    try {
      var nm = await api('vagabond.van_don.tao_van_don', {
        si_name: vdTay.si || '', ma_don: vdTay.ma, khach: vdTay.khach, sdt: vdTay.sdt, dia_chi: vdTay.diachi,
        ngay_giao: vdTay.ngay, gio_giao: vdTay.gio, tag_gio: vdTay.gio, lat: vdTay.lat || 0, lng: vdTay.lng || 0, kenh: vdTay.kenh, tien_thu_ho: parseFloat(vdTay.cod || 0) || 0
      });
      busy(false); toast('Đã tạo vận đơn'); vdTay = null;
      go(function () { scrVdView(nm); }, true);
    } catch (er) { busy(false); window.alert((er && er.message) || 'Lưu lỗi'); }
  };
}

var cpTay = null;
function cpTayDoc() {
  if (!cpTay) return;
  var g = function (id) { var el = document.getElementById(id); return el ? el.value : ''; };
  cpTay.tien = g('cptTien'); cpTay.shd = g('cptShd'); cpTay.noi = g('cptNoi'); cpTay.ghichu = g('cptGhiChu');
}
async function scrVdChiPhi() {
  if (!cpTay) cpTay = { loai: 'Đổ xăng', tien: '', shd: '', noi: '', ghichu: '' };
  var ds = [];
  try { ds = await api('vagabond.van_don.chi_phi_danh_sach', {}); } catch (e) { }
  var html = '<div class="sec">Khai chi phí mới (chụp kèm hoá đơn Petrolimex, biên lai...)</div>' +
    '<div class="card" style="padding:12px 14px;display:grid;gap:10px">' +
    '<div class="hub" data-t="loai" style="padding:10px 0;border:none"><div class="ht"><div class="h2">Loại chi phí</div><div class="h1">' + h(cpTay.loai) + '</div></div><span style="color:#c3c8d4">&#8250;</span></div>' +
    '<input class="tin" id="cptTien" placeholder="Số tiền (đ)" inputmode="numeric" value="' + h(cpTay.tien) + '">' +
    '<input class="tin" id="cptShd" placeholder="Số hoá đơn / biên lai (nếu có)" value="' + h(cpTay.shd) + '">' +
    '<input class="tin" id="cptNoi" placeholder="Nơi chi (vd Petrolimex CHXD 25)" value="' + h(cpTay.noi) + '">' +
    '<input class="tin" id="cptGhiChu" placeholder="Ghi chú" value="' + h(cpTay.ghichu) + '">' +
    '<button class="btn" id="cptLuu">📷 Chụp hoá đơn và gửi duyệt</button>' +
    '</div>';
  var ICON = { 'Chờ duyệt': '⏳', 'Đã duyệt': '👍', 'Từ chối': '⛔', 'Đã hoàn ứng': '✅' };
  html += '<div class="sec">' + (vdLaKeToan() ? 'Tất cả chi phí (kế toán duyệt, bấm vào để xử lý)' : 'Chi phí của tôi') + '</div><div class="card">';
  if (!ds.length) html += '<div class="emp" style="padding:20px"><div class="e1">⛽</div><div>Chưa có khoản nào.</div></div>';
  ds.forEach(function (r) {
    var vn = String(r.ngay || '').split('-').reverse().join('/');
    html += '<div class="hub" data-cp="' + h(r.name) + '"><div class="hi">' + (ICON[r.trang_thai] || '⏳') + '</div>' +
      '<div class="ht"><div class="h1">' + h(r.loai) + ' · ' + money(r.so_tien) + ' đ</div>' +
      '<div class="h2">' + vn + ' · ' + h((r.shipper || '').split('@')[0]) + ' · ' + h(r.trang_thai) + (r.so_hoa_don ? ' · HĐ ' + h(r.so_hoa_don) : '') + '</div>' +
      (r.ghi_chu_duyet ? '<div class="h2" style="color:#b3261e">' + h(r.ghi_chu_duyet) + '</div>' : '') + '</div>' +
      (r.anh_hoa_don ? '<a href="' + h(r.anh_hoa_don) + '" target="_blank">📷</a>' : '') + '</div>';
  });
  html += '</div>';
  var b = frame('Chi phí shipper', html, {});
  b.addEventListener('click', function (e) {
    if (e.target.closest('[data-t="loai"]')) {
      cpTayDoc();
      return sheet('Loại chi phí', ['Đổ xăng', 'Bảo trì xe', 'Gửi xe', 'Rửa xe', 'Vá/thay vỏ xe', 'Khác'].map(function (t) { return { value: t, label: t, icon: '⛽' }; }), cpTay.loai, function (o) { cpTay.loai = o.value; go(scrVdChiPhi, true); });
    }
    var cp = e.target.closest('[data-cp]');
    if (cp && vdLaKeToan() && !e.target.closest('a')) {
      var nm = cp.getAttribute('data-cp');
      return sheet('Xử lý ' + nm, [
        { value: 'duyet', label: 'Duyệt khoản chi này', icon: '👍' },
        { value: 'hoan_ung', label: 'Đã hoàn ứng (đưa tiền lại shipper)', icon: '✅' },
        { value: 'tu_choi', label: 'Từ chối', icon: '⛔' }
      ], null, async function (o) {
        var gc = o.value === 'tu_choi' ? (window.prompt('Lý do từ chối?', '') || '') : '';
        if (o.value === 'tu_choi' && !gc) return;
        busy(true);
        try { await api('vagabond.van_don.duyet_chi_phi', { name: nm, hanh_dong: o.value, ghi_chu: gc }); busy(false); toast('Đã cập nhật'); }
        catch (er) { busy(false); window.alert((er && er.message) || 'Lỗi'); }
        go(scrVdChiPhi, true);
      });
    }
  });
  document.getElementById('cptLuu').onclick = function () {
    cpTayDoc();
    var tien = parseFloat(cpTay.tien || 0) || 0;
    if (tien <= 0) return window.alert('Nhập số tiền đã nhé.');
    vdChupAnh(async function (blob) {
      try {
        var nm = await api('vagabond.van_don.tao_chi_phi', { loai: cpTay.loai, so_tien: tien, so_hoa_don: cpTay.shd, nha_cung_cap: cpTay.noi, ghi_chu: cpTay.ghichu });
        var fu = await vdUpload(blob, 'Chi Phi Shipper', nm, 'anh_hoa_don');
        await api('vagabond.van_don.gan_anh', { doctype: 'Chi Phi Shipper', name: nm, fieldname: 'anh_hoa_don', file_url: fu });
        busy(false); toast('Đã gửi, chờ Thu mua/Kế toán duyệt'); cpTay = null;
      } catch (er) { busy(false); window.alert((er && er.message) || 'Lỗi khi lưu'); }
      go(scrVdChiPhi, true);
    });
  };
}

var APPVER = '132';
function freshN() { try { return parseInt(sessionStorage.getItem('vgb_fresh') || '0', 10) || 0; } catch (e) { return 0; } }
function setFreshN(n) { try { sessionStorage.setItem('vgb_fresh', String(n)); } catch (e) { } }
function clearFresh() { try { sessionStorage.removeItem('vgb_fresh'); } catch (e) { } }
function hardNav() { window.location.replace(location.pathname + '?v=' + APPVER + '&t=' + (new Date()).getTime()); }
function goFresh() {
  var n = freshN();
  if (n >= 2) return false;
  setFreshN(n + 1);
  hardNav();
  return true;
}
function napAgain(ms) { return new Promise(function (res) { setTimeout(res, ms); }); }
async function whoAmI() {
  try {
    var r = await fetch('/api/method/frappe.auth.get_logged_user', { credentials: 'same-origin', headers: { 'Accept': 'application/json' } });
    if (!r.ok) return '';
    var j = await r.json();
    return j && j.message ? j.message : '';
  } catch (e) { return ''; }
}
function adopt(u) {
  S.user = u; S.me.user = u;
  try { if (window.frappe) { if (!frappe.session) frappe.session = {}; frappe.session.user = u; } } catch (e) { }
}
async function __boot(){
  clearFresh();
  try {
    var real = await whoAmI();
    if (real && real !== 'Guest') { adopt(real); reset(scrHome); return; }
    if (real === 'Guest') { reset(scrLogin); return; }
    syncUser();
    for (var i = 0; i < 5 && (!S.user || S.user === 'Guest'); i++) { await napAgain(200); syncUser(); }
    if (S.user && S.user !== 'Guest') { reset(scrHome); return; }
    reset(scrLogin);
  } catch(e) { var el=document.getElementById('vgb'); if(el) el.textContent = 'Loi khoi dong: '+String(e.message||e); }
}
if (document.readyState === 'complete') { __boot(); } else { window.addEventListener('load', __boot); }
window.addEventListener('popstate', function (ev) {
  /* Nut ‹ trong app da tu lui va goi history.back(), popstate nay chi la dong bo, bo qua */
  if (VGB_LUI_TAY > 0) { VGB_LUI_TAY--; return; }
  var st = ev.state;
  var d = (st && typeof st.vgbD === 'number') ? st.vgbD : 0;
  if (d + 1 < S.stack.length) {
    if (roiPhieuDo(S.stack[d])) {
      var giu = S.stack.length - 1;
      confirmSheet('Phiếu đang soạn dở', 'Rời màn này thì danh sách món đang chọn sẽ mất.', 'Rời đi, bỏ phiếu nháp', true)
        .then(function (ok) {
          if (ok) { S.draft = null; S.stack.length = d + 1; render(); }
          else { try { history.pushState({ vgbD: giu }, '', location.href); } catch (e) { } }
        });
      return;
    }
    S.stack.length = d + 1; render(); return;
  }
  if (d + 1 > S.stack.length) {
    /* Nut Tien hoac moc cu con sot lai: khong dung lai man hinh nao duoc, chi dong bo lai moc */
    try { history.replaceState({ vgbD: S.stack.length - 1 }, '', location.href); } catch (e) { }
  }
});
try { history.replaceState({ vgbD: 0 }, '', location.href); } catch (e) { }


/* ---------- Van don: nguoi nhan, phan cong, va phieu in (02/08/2026) ---------- */
function vdKhoiNhan(d) {
  var s = '';
  var khac = (d.nguoi_nhan || '') && ((d.nguoi_nhan || '') !== (d.khach || '') || (d.sdt_nhan || '') !== (d.sdt || ''));
  if (khac) {
    s += '<div style="font-size:13px;margin-top:2px">Người nhận: <b>' + h(d.nguoi_nhan) + '</b>'
      + (d.sdt_nhan ? ' · <a href="tel:' + h(d.sdt_nhan) + '">' + h(d.sdt_nhan) + '</a>' : '') + '</div>';
  }
  var t = [];
  if (d.goi_truoc) t.push(vdThe('#b45309', '📞 Gọi trước khi giao'));
  if (d.chup_truoc) t.push(vdThe('#7c3aed', '📷 Gửi ảnh trước khi giao'));
  if (t.length) s += '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:6px">' + t.join('') + '</div>';
  if (d.ghi_chu_in) s += '<div style="margin-top:8px;background:#f7f1e6;border-left:3px solid #c9a24b;padding:8px 10px;font-size:13px;white-space:pre-wrap">' + h(d.ghi_chu_in) + '</div>';
  return s;
}
function vdNutPhanCong(d) {
  var b = [];
  if (d.dia_chi || (d.lat && d.lng)) b.push('<button class="btn gh" data-va="chiduong" style="flex:1">' + vdAnhMap(20) + ' Chỉ đường</button>');
  if (isSales() && d.trang_thai !== 'Đã giao' && d.trang_thai !== 'Huỷ') {
    var ten = vdTen(d.shipper);
    b.push('<button class="btn gh" data-va="phancong" style="flex:1">🛵 ' + (ten ? h(ten) : 'Phân công') + '</button>');
  }
  if (!b.length) return '';
  return '<div style="display:flex;gap:8px;margin-top:10px">' + b.join('') + '</div>';
}

var VD_CSS = ''
  + '@import url("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Inter:wght@300;400;500;600;700&display=swap");'
  + '*{margin:0;padding:0;box-sizing:border-box}'
  + 'body{font-family:Inter,sans-serif;color:#1f1c19;background:#e9e5de;padding:8mm 0}'
  + '.p{width:190mm;margin:0 auto 5mm;background:#fff;border:1.5px solid #1f1c19;page-break-inside:avoid;break-inside:avoid}'
  + '.hd{background:#f2efe9;border-bottom:1.5px solid #1f1c19;padding:9px 14px;display:flex;justify-content:space-between;align-items:center;gap:14px}'
  + '.bd{font-family:"Cormorant Garamond",serif;font-size:19px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:#1f1c19}'
  + '.dt{font-family:"Cormorant Garamond",serif;font-size:15px;letter-spacing:4px;text-transform:uppercase;font-weight:700;color:#1f1c19}'
  + '.stt{font-size:10.5px;letter-spacing:.8px;text-transform:uppercase;color:#6b645b}'
  + '.qr{width:21mm;height:21mm;flex:0 0 auto}'
  + '.qr svg{width:100%;height:100%;display:block}'
  + '.gr{display:grid;grid-template-columns:1fr 1fr;gap:0 16px;padding:10px 14px;border-bottom:1px solid #d9d3c9}'
  + '.f{padding:3px 0}'
  + '.l{text-transform:uppercase;letter-spacing:1px;font-size:8.5px;color:#6b645b;font-weight:700}'
  + '.v{font-size:13px;font-weight:500;line-height:1.45;color:#1f1c19}'
  + '.v.big{font-size:15px;font-weight:700}'
  + '.v .mo{color:#8a8279;font-weight:400}'
  + '.wide{grid-column:1 / -1}'
  + '.the{display:inline-block;border:1.2px solid #1f1c19;border-radius:3px;padding:1px 7px;font-size:10px;font-weight:700;margin:3px 5px 0 0;text-transform:uppercase;letter-spacing:.5px}'
  + '.note{margin:9px 14px;background:#f4f2ed;border-left:3px solid #1f1c19;padding:8px 11px;font-size:12.5px;white-space:pre-wrap;line-height:1.5}'
  + '.note b{display:block;text-transform:uppercase;letter-spacing:1px;font-size:8.5px;color:#6b645b;margin-bottom:3px}'
  + 'table{width:100%;border-collapse:collapse;font-size:12px}'
  + 'thead th{background:#f2efe9;color:#3d372f;text-transform:uppercase;letter-spacing:1px;font-size:8.5px;font-weight:700;padding:6px 8px;text-align:left;border-bottom:1px solid #1f1c19}'
  + 'th.q,th.a,td.q,td.a{text-align:right}'
  + 'tbody td{padding:5px 8px;border-bottom:1px solid #e6e1d8;vertical-align:top}'
  + 'td.n{color:#8a8279;width:20px}'
  + '.code{color:#8a8279;font-size:10px}'
  + '.cod{padding:9px 14px;display:flex;justify-content:space-between;align-items:center;gap:16px;border-top:1.5px solid #1f1c19}'
  + '.dan{font-size:11.5px;line-height:1.45;color:#3d372f;flex:1}'
  + '.cod .so{font-family:"Cormorant Garamond",serif;font-size:22px;font-weight:700;color:#1f1c19;white-space:nowrap}'
  + '.sig{display:flex;gap:18px;padding:10px 14px 4px}'
  + '.sig div{flex:1;text-align:center;font-size:9.5px;color:#6b645b;text-transform:uppercase;letter-spacing:1px}'
  + '.sig span{display:block;border-top:1px dotted #8a8279;margin-top:32px;padding-top:4px}'
  + '.ft{background:#f2efe9;border-top:1.5px solid #1f1c19;color:#3d372f;padding:6px 14px;font-size:9.5px;letter-spacing:.3px;text-align:center}'
  + '.ft b{color:#1f1c19}'
  + '@page{size:A4;margin:7mm}'
  + '@media print{body{background:#fff;padding:0}.p{margin:0 auto 3mm;width:100%}}';

function vdO(nhan, giatri, to) {
  if (!giatri) return '';
  return '<div class="f"><div class="l">' + nhan + '</div><div class="v' + (to ? ' big' : '') + '">' + giatri + '</div></div>';
}
var VD_DAN = 'Quý khách vui lòng kiểm tra bánh khi nhận, bảo quản ngăn mát tủ lạnh và dùng hết trong ngày.';
function vdPhieuHtml(d) {
  var s = '<div class="p">';
  s += '<div class="hd"><div><div class="bd">The Vagabond Pâtisserie</div>'
    + '<div class="stt">' + h(d.name || '') + (d.nguoi_tao ? ' · lập bởi ' + h(d.nguoi_tao) : '') + '</div></div>'
    + '<div style="text-align:right"><div class="dt">Phiếu giao hàng</div>'
    + '<div class="stt">' + h(d.trang_thai || '') + '</div></div>'
    + (d.qr ? '<div class="qr">' + d.qr + '</div>' : '')
    + '</div>';

  s += '<div class="gr">';
  s += vdO('Số đơn', h(d.ma_don || d.name || ''), true);
  s += vdO('Ngày giao', h(String(d.ngay_giao || '').split('-').reverse().join('/')) + (d.tag_gio ? ' · ' + h(d.tag_gio) : (d.gio_giao ? ' · ' + h(d.gio_giao) : '')), true);
  s += vdO('Người đặt', h(d.khach || '') + (d.sdt ? ' · ' + h(d.sdt) : ''));
  s += vdO('Người nhận', (d.nguoi_nhan ? h(d.nguoi_nhan) : '<span class="mo">như người đặt</span>') + (d.sdt_nhan ? ' · ' + h(d.sdt_nhan) : ''));
  s += '<div class="f wide"><div class="l">Địa chỉ giao</div><div class="v big">' + h(d.dia_chi || '') + '</div></div>';
  s += vdO('Phường / Xã', h(d.phuong || '') || '<span class="mo">chưa rõ</span>');
  var ten = d.ten_shipper || (d.shipper ? String(d.shipper).split('@')[0] : '');
  s += vdO('Shipper giao', (ten ? h(ten) : '<span class="mo">chưa phân công</span>') + (d.chuyen ? ' · ' + h(d.chuyen) : '') + (d.thu_tu ? ' · điểm số ' + d.thu_tu : ''), true);
  s += vdO('Kênh giao', h(d.kenh || '') + (d.booking_id ? ' · ' + h(d.booking_id) : ''));
  s += vdO('Giờ dự kiến đến', h(d.gio_du_kien || '') + (d.km_chang ? ' · ' + d.km_chang + ' km' : ''));
  s += vdO('Hoá đơn', h(d.hoa_don || ''));
  var the = [];
  if (d.goi_truoc) the.push('Gọi trước khi giao');
  if (d.chup_truoc) the.push('Chụp ảnh gửi trước khi giao');
  (String(d.the_don || '').split(', ')).forEach(function (x) { x = x.trim(); if (x && the.indexOf(x) < 0) the.push(x); });
  if (the.length) s += '<div class="f wide"><div class="l">Lưu ý khi giao</div><div>' + the.map(function (x) { return '<span class="the">' + h(x) + '</span>'; }).join('') + '</div></div>';
  s += '</div>';

  if (d.mon && d.mon.length) {
    s += '<table><thead><tr><th style="width:20px">#</th><th>Sản phẩm</th><th class="q" style="width:42px">SL</th><th class="a" style="width:92px">Thành tiền</th></tr></thead><tbody>';
    d.mon.forEach(function (m, i) {
      s += '<tr><td class="n">' + (i + 1) + '</td><td>' + h(m.item_name || m.item_code || '')
        + (m.item_code ? '<div class="code">' + h(m.item_code) + '</div>' : '') + '</td>'
        + '<td class="q">' + (m.qty != null ? m.qty : '') + '</td>'
        + '<td class="a">' + (Number(m.amount) ? money(m.amount) + ' đ' : '-') + '</td></tr>';
    });
    s += '</tbody></table>';
  }

  if (d.ghi_chu_in) s += '<div class="note"><b>Ghi chú giao hàng</b>' + h(d.ghi_chu_in) + '</div>';
  if (d.ghi_chu) s += '<div class="note" style="border-left-color:#8a8279"><b>Ghi chú nội bộ</b>' + h(d.ghi_chu) + '</div>';

  s += '<div class="cod"><div class="dan">' + VD_DAN + '</div>'
    + '<div style="text-align:right"><div class="l">Tiền thu hộ (COD)</div>'
    + '<div class="so">' + (Number(d.tien_thu_ho) ? money(d.tien_thu_ho) + ' đ' : 'Không thu') + '</div></div></div>';
  s += '<div class="sig"><div><span>Người giao</span></div><div><span>Người nhận ký</span></div></div>';
  s += '<div class="ft"><b>THE VAGABOND PÂTISSERIE</b> · 307/1 Nguyễn Văn Trỗi &amp; 9 Trần Cao Vân · Cảm ơn Quý khách đã tin chọn</div>';
  return s + '</div>';
}

// Logo Google Maps ve bang SVG cho net o moi co, khong phai tai anh ngoai.
var VD_GMAP_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
  + '<defs><clipPath id="k"><rect x="3" y="3" width="42" height="42" rx="6"/></clipPath></defs>'
  + '<g clip-path="url(#k)">'
  + '<rect x="3" y="3" width="42" height="42" fill="#1B9E4B"/>'
  + '<polygon points="3,45 24,20 45,45" fill="#1A73E8"/>'
  + '<polygon points="3,33 25,3 34,3 3,45" fill="#FBD200"/>'
  + '<polygon points="30,3 45,20 45,45 21,45" fill="#E8EAED"/>'
  + '</g>'
  + '<path d="M33 4c-5 0-9 4-9 9 0 6.6 9 17 9 17s9-10.4 9-17c0-5-4-9-9-9z" fill="#F03127"/>'
  + '<circle cx="33" cy="13" r="4.2" fill="#9E1B14"/></svg>';
var VD_GMAP = 'data:image/svg+xml;utf8,' + encodeURIComponent(VD_GMAP_SVG);
function vdAnhMap(px) {
  return '<img src="' + VD_GMAP + '" alt="Google Maps" style="width:' + px + 'px;height:' + px + 'px;display:inline-block;vertical-align:middle">';
}
function vdTen(u) {
  if (!u) return '';
  var x = (vtShipper || []).filter(function (s) { return s.user === u; })[0];
  return x && x.ten ? x.ten : String(u).split('@')[0];
}
function vdDich(r) {
  if (r.lat && r.lng) return encodeURIComponent(r.lat + ',' + r.lng);
  return encodeURIComponent(r.dia_chi || '');
}
function vdMoDuong(dich) {
  var u = 'https://www.google.com/maps/dir/?api=1&travelmode=driving&destination=' + dich;
  var a = document.createElement('a');
  a.href = u;
  a.target = '_blank';
  a.rel = 'noopener';
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  setTimeout(function () { if (a.parentNode) a.parentNode.removeChild(a); }, 0);
}
function vdNutDong(r, chon) {
  if (chon) return '';
  var b = [];
  if (r.dia_chi || (r.lat && r.lng)) b.push('<button class="btn gh" data-di="' + vdDich(r) + '" style="width:auto;padding:3px 10px;line-height:0">' + vdAnhMap(24) + '</button>');
  if (isSales() && r.trang_thai !== 'Đã giao' && r.trang_thai !== 'Huỷ') {
    b.push('<button class="btn gh" data-pc="1" style="width:auto;padding:4px 10px;font-size:12px">🛵 ' + (r.shipper ? h(vdTen(r.shipper)) : 'Phân công') + '</button>');
  }
  if (!b.length) return '';
  return '<div style="display:flex;gap:6px">' + b.join('') + '</div>';
}
var vdAhaDv = null, vdDaGanLamMoi = 0;
function vdDangOManDS() {
  return S.stack.length && S.stack[S.stack.length - 1] === scrVanDon;
}
var vdAnLuc = 0;
function vdTuLamMoi() {
  if (vdDaGanLamMoi) return;
  vdDaGanLamMoi = 1;
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) { vdAnLuc = Date.now(); return; }
    /* Tren dien thoai, bang chon ngay cua he dieu hanh lam trang bi coi la an
       di. Neu ve lai man hinh ngay luc quay ve thi o ngay bi dung ve gia tri
       cu truoc khi kip bao da doi - do la ly do Loan Anh khong chon duoc ngay
       con anh Viet ngoi may tinh thi chon duoc. Chi lam moi khi that su roi
       di cho khac tren 20 giay. */
    if (Date.now() - vdAnLuc < 20000) return;
    if (vdDangOManDS()) go(scrVanDon, true);
  });
  setInterval(function () {
    if (!document.hidden && vdDangOManDS() && !isSales()) go(scrVanDon, true);
  }, 45000);
}

async function scrVdGoiXe(name, kenh) {
  frame('Gọi xe ' + kenh, '<div class="emp"><div class="e1">⏳</div></div>');
  if (kenh !== 'Ahamove') {
    frame('Gọi xe ' + kenh, '<div class="emp"><div class="e1">🔑</div><div>' + h(kenh) + ' chưa cấp khoá API. Điền khoá vào Vagabond Settings là màn này chạy được ngay.</div></div>');
    return;
  }
  var d;
  try {
    d = await api('frappe.client.get', { doctype: 'Van Don', name: name });
    if (!vdAhaDv) vdAhaDv = await api('vagabond.van_don.aha_dich_vu');
  } catch (e) {
    frame('Gọi xe ' + kenh, '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>');
    return;
  }
  var dsDv = (vdAhaDv && vdAhaDv.dich_vu) || [];
  if (!dsDv.length) { frame('Gọi xe ' + kenh, '<div class="emp"><div class="e1">⚠️</div><div>Ahamove không trả về loại xe nào.</div></div>'); return; }
  var chonDv = (vdAhaDv && vdAhaDv.mac_dinh) || dsDv[0].id;
  var chonAdd = {};
  var gia = null, dangTinh = false;
  function dvHienTai() { for (var i = 0; i < dsDv.length; i++) { if (dsDv[i].id === chonDv) return dsDv[i]; } return dsDv[0]; }
  function ve() {
    var dv = dvHienTai();
    var html = '<div class="card" style="padding:12px 14px;line-height:1.7">' +
      '<div><b>' + (d.ma_don ? '#' + h(d.ma_don) : h(d.name)) + '</b> · ' + h(d.khach || 'Khách lẻ') + '</div>' +
      '<div style="font-size:13px">' + h(d.dia_chi || '(chưa có địa chỉ)') + '</div>' +
      (d.tien_thu_ho ? '<div><b>Thu hộ (COD): ' + money(d.tien_thu_ho) + ' đ</b></div>' : '') +
      '</div>';
    html += '<div class="sec">Loại xe</div><div class="card">';
    dsDv.forEach(function (x) {
      html += '<div class="row" data-dv="' + h(x.id) + '" style="cursor:pointer"><div>' + h(x.ten) + '</div><div>' + (x.id === chonDv ? '✓' : '') + '</div></div>';
    });
    html += '</div>';
    html += '<div class="sec">Dịch vụ thêm (Ahamove tính thêm tiền)</div><div class="card">';
    if (!(dv.addon || []).length) html += '<div class="row"><div style="color:#6b7280">Loại xe này không có dịch vụ thêm.</div></div>';
    (dv.addon || []).forEach(function (r) {
      html += '<div class="row" data-add="' + h(r.id) + '" style="cursor:pointer"><div>' + (chonAdd[r.id] ? '☑️ ' : '⬜ ') + h(r.ten) + '</div><div style="color:#6b7280">' + (r.gia ? '+' + money(r.gia) + ' đ' : '') + '</div></div>';
    });
    html += '</div>';
    html += '<div class="card" style="padding:12px 14px;margin-top:10px">' +
      (dangTinh ? '<div style="color:#6b7280">Đang hỏi giá Ahamove...</div>' :
        (gia === null ? '<div style="color:#6b7280">Bấm Xem giá để Ahamove báo cước.</div>' :
          '<div style="font-size:17px"><b>Cước: ' + money(gia.tong) + ' đ</b>' + (gia.km ? ' <span style="color:#6b7280;font-size:13px">· ' + num(gia.km) + ' km</span>' : '') + '</div>')) +
      '</div>';
    var ft = '<button class="btn gh" id="gxGia" style="flex:1">Xem giá</button>' +
      '<button class="btn" id="gxDat" style="flex:1"' + (gia === null ? ' disabled' : '') + '>Gọi xe</button>';
    var b = frame('Gọi xe Ahamove', html, { footer: '<div style="display:flex;gap:8px">' + ft + '</div>' });
    b.addEventListener('click', function (e) {
      var dvEl = e.target.closest('[data-dv]');
      if (dvEl) { chonDv = dvEl.getAttribute('data-dv'); chonAdd = {}; gia = null; ve(); return; }
      var adEl = e.target.closest('[data-add]');
      if (adEl) { var k = adEl.getAttribute('data-add'); chonAdd[k] = !chonAdd[k]; gia = null; ve(); return; }
    });
    document.getElementById('gxGia').onclick = async function () {
      dangTinh = true; ve();
      try {
        gia = await api('vagabond.van_don.aha_bao_gia', { name: name, service_id: chonDv, requests_them: JSON.stringify(Object.keys(chonAdd).filter(function (k) { return chonAdd[k]; })) });
      } catch (e2) { window.alert((e2 && e2.message) || 'Ahamove không báo giá được'); }
      dangTinh = false; ve();
    };
    document.getElementById('gxDat').onclick = async function () {
      if (gia === null) return;
      if (!window.confirm('Gọi xe Ahamove cho đơn này, cước ' + money(gia.tong) + ' đ?')) return;
      busy(true);
      try {
        await api('vagabond.van_don.book_xe', { name: name, kenh: 'Ahamove', service_id: chonDv, requests_them: JSON.stringify(Object.keys(chonAdd).filter(function (k) { return chonAdd[k]; })) });
        busy(false); toast('Đã gọi xe, Ahamove đang tìm tài xế');
        go(function () { scrVdView(name); }, true);
      } catch (e3) { busy(false); window.alert((e3 && e3.message) || 'Gọi xe lỗi'); }
    };
  }
  ve();
}
var VD_APPS = [
  { ten: 'Ahamove', api: 1, anh: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAABICAMAAABiM0N1AAAAkFBMVEX///////7+/////v7//v3+/v/+/v7//fz9/v79/f78/f39/Pz/+vf6+/z+9/P19/n38vDq7vLm4+Tj2NXAzdrDwcX/nGGar8SAm7b/jUf/hj7/gjb/gTL/gDP8gDP/fzP/fzL/fzH7fzL/fC7/eir/dyV9hJNhgqNMbpMzXYggTHsOP3ICNGoALWUAKmMAJF4QARquAAADF0lEQVR42u1Wf5OaMBAN4oEyQC4xJRGPFkSbHwT4/t+uu6jt6c10Dq//leeEkBhf3r7sZiRkwYIFC/5LhHG8/ic0U/dlqpCQ192Of5kpJGlRns5NsfsCUxAE63VenNuqqs7t80zh9CzOh6qu68NpnwfBk0xpnqe706FGNIfzjsTPsKzJrizL/aGpJiKQVDyhKAiDOECisq1vqFo+26XrzjGGdr6GVh/OxfzYwJ0rwOumPjbN8a067dO5p/Va/gaEdrTueHTm7ftpZgYA0f6Ctm2rG9HPt2dii/M0Tddw9HhkzXcMrWmqtsxn2o1m5/nrHvXUP6oJmAHzUynMi7o8tD+QpzlNmIiKa7p/XhFUannR0xyKCXB48P46kwkzoJiKA8IJYkAAefBMbDFBp6sKajUNwyC4jKFM1rOvxf25RWuuGsJ1Ok3AcKZLcbEvMJVuOQg1DEbti2dMQtw5EsefqZFNkly6iLy77IM/nqxRShg8ddE+XEDBhwtp9eFXL4RLEZEIOgaDT+IjD4kiM3hBMqJGuc2mmWQTbWA+gli3W+RebeF1tcHQ4bHCSUofeLZEdJ1XSDTIaafto4XwASQ3HdOISUlJ9H5ZAgTKObpBIiGQhwnOOOWcC5YIgeszIRhMM0IyznFEuQIj7ogItR3TAzAo73qvMyK7oXNe2K4brO17ywm3/dBJ4S19kYPmdhicuOzwXpAYNDZQ1DtlByF6J7UHot4Y77UZNbW9Vq4XBraz0PVKdu7RooTo3mrTOY5mY1OoTvegiNHOZcwb3IqIXotRi94I76S0sDa5N5I573vfeYkeJXKUuoe/DcBmHcvAO9YZAb8i0FPnDPjonXXWPhAlBIKGeKU306kBkRw1E+iRY3QisrxzgulRgYudYwzUU6XurV5F1I4C3+zIMTQ5qsyMHYjE0DKwgnlHJEgeDX3h3aDIZWRZFN1HZnS2TbIXacU3K4gAyVQZpTTXmmZaZxQWEKHNlDbKcEw8bVT2cPafQ3StpfejD7hUPoEawOqH6oCGiPCLW9vixLQ4In9GCxYsWLDg7/gF2A1dchuCKjkAAAAASUVORK5CYII=' },
  { ten: 'GreenSM', api: 1, nen: '#00A94F', chu: '#FFFFFF', nhan: 'GSM' },
  { ten: 'Grab', api: 0, anh: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAABICAMAAABiM0N1AAAAkFBMVEX///////7+///+//79//7+/v79/v38///8/v78/v38/vz7/vz6/vz6/fv2/Pnx+/bs+fLi9uvb9ObP8N7H7tjA7NO26Muk4r6V3rSL2quE2Kd71aB005xu0plsz5Rnzo9dzIxZyYRPxn5GxXtIwnQ9wXM0v280vGcou2Yjt10XtVkMsE4ArEQAqT4AqDoApDMl1P0BAAAEQElEQVR42u1WiY6jOBCtxYQdQsIVwBzmMpjDgPn/v9ty0t3T3TudtDTSaKXNk5KyDSm/eq6qGOCJJ5544n8Bw/jyAfm+F2LbANbR+l029tvXLx7leR3B97awwMu6QYgqAvI5WBvqZkzg+D0+ydyXjLF6jNGpaROwbLAPAAc0UNV9onezH/uhS8bGcZh4GcJBB4FUkJrronHQ0RiB53wV+xtMEi5pNya+F9A+BgeCSghOIe2nSaRgQt0mTEwDj3F8n1DDq/Fl4loQSc7KOm1nVpZs5ieDpd1QVGUls7uSG4Y75TICh5xc1z053lSV05RlczoOw5jODMKxYRi3SJfkXnQEwqmYXAJe2/f9yJKpmEMrlJlMAdI5k17b1jOK1Agm7gVn4o7FdMaocsbymme8Rw9UNC04DvC6L3ghA01lZGMA5A4jb85laBGPj+OY11nbUxMyzrOzc7SLlmepTC9n0zm0lbjcU8mGruYt5onvXaaqTnlPMSbR1poRQ7dz3BRwfsgILCNe6Fz5AIGoeHpzFEot7Q+/QoHyPJMx/J2PhbhfKRaUM+UT7+c6l17eYg6doOkz2fdN2aBiHU9n3o9UJg9y0oRyqbTUDe7MuKDgWN4g8rLK6nakf/kTjlkhi0e5DQeI+SjEWAdg0LyI4UDgVAxirNIMZ+CyUYzo/6vAyA3X6MANw/O7ctKrYfA2dvTY/E4juXo44qvEssit1aExreuM6Kfml3E5vu9p3AgbhBj/YvyzkAj5On0uUi6I2bePN1LXvR3HfmF0HeD8SG5Tx3l54Ug+OopWKRCd9ybKq5rW68h4nZO3A/4Fo2hrr6OQYqchENPQAI8yRl0gBwjSnKLASVGmge7FtGBZCODjC+mHBH/nSG6Yy3STIUST2pQa8QeJVNvOznzDBcyuYFBq3TvsFArXG2x/Hxx1l+gSBRCvMgiXJQZ/2po4btXgevNaJllQ7CKJ2Dad872NojSDUtVRlKXvM0prpLEXBPK96/YMCFVcC9Op5LJ1OPKWWW/dbFGhmJbSaFTu/Vujdaqqqk6wytt1bZwzMEWN8xnSPYtVSdxjtEjedXxS9LKoReQ+JOsmReaB8SuNsETTdc2wU5QqsU8nm6ocHeE8wuRATHMCcT2tSng3y913afXTkal/sCwRoKNCL5Q71Y5O4C/SfzvxH+Gwxfr1cFov78pXh9ZdNEx3UJSqyYNqXVPfT9fFTxQD5wc0qot8/5IFEQ29QGxRRAMvGD45ipUWe1vDdkdqzd651So2KdVKge7YIE2Cp75Kuaog3Re5KGEXaDG087tywqZfVxosqhm2R581IVMJHQa8MhgX7G42pp2Pd4KhTSDIO2xKvhEWYtJiP7jooNjw4V5CPlnjk32Z2Te8luvt1JxrSzFuvQSILlBc0E1Ff8wX++C/WzOyf//uRyCIHkb/h2Ha/y0+TzzxxBN/HP8AE5lzqxH/g6sAAAAASUVORK5CYII=' },
  { ten: 'BE', api: 0, anh: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAABICAMAAABiM0N1AAAAkFBMVEX/zQz/yhD/yRD/yA3/yAD4yBH/xw//xwb7xxP+xRj/xBn+xBv+xBr+xBn/xBj+xBj/xhX/xBf+xBf/xg3/xgz+xg39xB39xBv9xBr9xBj4xBj9wxn8wxr8wxn8wxj8whr7whrqvyHTti20qUJmh3QzdJsXa68XaK0SaLIRZ7MNZrYIY7oJYbMBYL8JUpwEQ40ERo27AAACN0lEQVR42u2XDW/bIBCGgXaquzSJ46Zd8ceKOSBgwP7//26H205rJ60hiSZV8imKuCh6DHf33hlyfSEjC2gBLaD/Crrf7x8e9ifY/XvQzeruRFvdvAettxXn1Tbf1n+Dnn4soK8M2qVS2J0N4mWv0fqSnwnqyn7w3smyOx9knDOXAQ3DJUGiE+INxnEtWn4SqLqllJWdSL8Jzii5YjvB80E96SXInl01vGloIQFA1mTTZoNAjeMYDhrY7paCdjHGQauaiTyQs9M0jeMhxKjqWgXvjDHWRy3Zcx7IzaBgjY1aTeMBIQkWP2bzKBDWd/DW+nEag9dKO29N1AXPPRr0ZQ0aSbjWULBS6ogkICIDZMMkyebnlvRIciM6dV2zb9obr4smAzQ/mG+5IBCtC+mUsw0OC+PPKH0eI1mkv3fVS8AwSLM55wbJ2nytNWV/GKxLaXszfyyI73o9WA9z6YlCBpdS+LojtEEeeTTeMhVNVCTpVBAVrPM6KQQ1Mn93G35cq50DbL1ihBGKxegcOuSaEIJiY4xtju3ZvKpTzqPGp+sRT4XRxvIGUFHXpWiPb/4tAz/gnlCnKNxpst7MTkS59BXPGEeCwoBFbMwhcQDM7MyqhQ/y/2SuCSo17sGHMGqgTKrk4AebSps3IAVjoJRWCgr6LEoqX5yaNbmTtm1YyhChDfafDh2anO8if2TzVrRNK167NC66387yNrKA/gF6ugRodbd+fFyff4W42KVmuUEuoAX0VUC/AHYG+ERa95YPAAAAAElFTkSuQmCC' },
  { ten: 'Lalamove', api: 0, anh: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAABICAMAAABiM0N1AAAAkFBMVEX9rCHnmh7WjhzKhRv8cifKfBu4eRipcBb1bCXraCTeYyK9ZByibRaXZRTAVh63URyyTxylSRmKURSVQxeEOxVtRw9ePg14NRNbNA5qLxFKLQtYJw5QIw1IIgtDHgs2IwcvGwctFAceEAUXDAMWCgQQCQMIAwEEAgEDAgACAgADAQACAQECAQABAQABAAAAAADZNdywAAAB/0lEQVR42u2V2Y7jIBBF8b4o3u04eA8OsZMB6v//bspJpPT0rErnYR5AQsZIHOpWXYDAmxrRIA3SIA3SIA3SoH8FyfeAlPhCREKoB+W6ALBpVa+BthjkFRdv68+05uolkMK13WkbLcBpEZfLq9KUZHVRd0wBj227hOWWJYEhittI4ketl1uXqxIrCKzHqi5CiB+lSTi1tCzLvveDcL7L+pM4+ftkw0zbtg6CwM7gXAzblnXCoC0xdzDFFJjn8ZPnzTxynAZ2BxDRIXdc93hL8LP8qIrSvrQDewAWDJitIfBbSDPUKRM/gYYQtifGbLljTpi1k3tjNKqx4ffQnz4SuG9ap3ayITiaIK6zEmK6nKGNuxAq02pc02sIh7NxyF0wqyPJ8+Ye0EdDSozEt0MmgMb424dlkC3hEe0QF7F/inZbiyoTYCLT3mlMWRlV3qifQFfR2n42o6gs7NpjWLMinGzaTnXIOr+zKo80ZjWRarRcGA1jD545jvOjKE+QUiIOh83jUCZJ2mYcpmJI05gWLUDRRVPl8d0Ie8fJOcxe9A1y17UauHwCXaELT7DIX9VYqg+p/NuhFdekh+UxxKOHhw+7uDWcUkKiDy8SVilXCeqy4iQaUn4GCegLWN5wH6lzyaT8OghrfwT1phtSvumqVfo50iAN0iAN0iAN+m9B3wHXSpRqyofP9gAAAABJRU5ErkJggg==' }
];
function vdOpsGiao(ds) {
  return [{ value: '', label: 'Gỡ ra, trả về Chờ giao', icon: '↩️' }]
    .concat((ds || []).map(function (x) { return { value: x.user, label: x.ten, icon: '🛵' }; }))
    .concat(VD_APPS.map(function (a) {
      return { value: 'app:' + a.ten, label: a.ten + (a.api ? '' : ' (đặt tay trên app)'), img: vdLogoApp(a) };
    }));
}
async function vdGanNguoiGiao(name, o) {
  var ten = (o.value || '').indexOf('app:') === 0 ? o.value.slice(4) : '';
  if (ten) {
    await api('vagabond.van_don.gan_shipper', { name: name, kenh: ten });
    var a = vdApp(ten);
    return { app: ten, goiXe: !!(a && a.api) };
  }
  await api('vagabond.van_don.gan_shipper', { name: name, shipper: o.value || '' });
  return { app: '' };
}
function vdApp(ten) {
  for (var i = 0; i < VD_APPS.length; i++) { if (VD_APPS[i].ten === ten) return VD_APPS[i]; }
  return null;
}
function vdLogoApp(a) {
  // Logo that cua don vi van chuyen (anh Viet gui 03/08), nhung thang vao ma
  // duoi dang data URI cho khoi phu thuoc tep ngoai. GreenSM chua co logo nen
  // van dung khoi chu tam.
  if (a.anh) return a.anh;
  var co = a.nhan.length <= 2 ? 15 : (a.nhan.length <= 3 ? 13 : 11);
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 40" width="64" height="40">' +
    '<rect x="0" y="0" width="64" height="40" rx="9" fill="' + a.nen + '"/>' +
    '<text x="32" y="20" fill="' + a.chu + '" font-family="Helvetica,Arial,sans-serif" font-size="' + co +
    '" font-weight="bold" text-anchor="middle" dominant-baseline="central">' + a.nhan + '</text></svg>';
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}
async function vdChonShipper(name) {
  if (!vtShipper) { busy(true); try { vtShipper = await api('vagabond.van_don.ds_shipper'); } catch (e) { vtShipper = []; } busy(false); }
  var ops = vdOpsGiao(vtShipper);
  sheet('Phân công đơn này cho ai', ops, '', async function (o) {
    busy(true);
    try {
      var kq = await vdGanNguoiGiao(name, o);
      busy(false);
      if (kq.app) {
        if (kq.goiXe) { go(function () { scrVdGoiXe(name, kq.app); }); return; }
        toast('Đã ghi nhận đơn đi ' + kq.app);
      go(scrVanDon, true);
        return;
      }
      toast(o.value ? 'Đã phân công cho ' + o.label : 'Đã gỡ người giao khỏi đơn');
      go(scrVanDon, true);
    } catch (e) { busy(false); window.alert((e && e.message) || 'Phân công lỗi'); }
  });
}

async function vdInPhieu(names) {
  busy(true);
  var ds;
  try { ds = await api('vagabond.van_don.phieu_in', { names: JSON.stringify(names) }); }
  catch (e) { busy(false); window.alert((e && e.message) || 'Không lấy được dữ liệu để in'); return; }
  busy(false);
  if (!ds || !ds.length) { toast('Không có đơn nào để in.'); return; }
  var body = ds.map(vdPhieuHtml).join('');
  var doc = '<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8">'
    + '<title>Phiếu giao hàng - The Vagabond Pâtisserie</title>'
    + '<style>' + VD_CSS + '</style></head><body>' + body
    + '<script>window.onload=function(){setTimeout(function(){window.print();},600);};<\/script>'
    + '</body></html>';
  var w = window.open('', '_blank');
  if (!w) { window.alert('Trình duyệt chặn cửa sổ in. Anh chị cho phép mở cửa sổ mới rồi bấm In đơn lại giúp em.'); return; }
  w.document.open(); w.document.write(doc); w.document.close();
}

/* ---------- Van don: loc theo phuong / khung gio + xep tuyen (03/08/2026) ----------
   Sales truoc day loc tay tren Pancake roi in mot to A4 moi shipper. Khoi nay dua
   the khung gio + phuong ve app, va de xuat thu tu chay cho tung chuyen. ---------- */
var vdPhuong = null, vdTagGio = null, vdBuoi = null, vdBoLoc = null;
var vtBuoiChon = null, vtSoTuyen = 2, vtDiemLay = 'Bếp', vtKq = null, vtShipper = null;

function vdThamSo() {
  var p = { ngay: vdNgay };
  if (vdLoc) p.trang_thai = vdLoc;
  if (vdPhuong) p.phuong = vdPhuong;
  if (vdTagGio) p.tag_gio = vdTagGio;
  if (vdBuoi) p.buoi = vdBuoi;
  return p;
}
function vdPhuongNgan(x) {
  var t = String(x || '').replace(/^(Phường|Xã|Thị trấn)\s+/i, '');
  return /^[0-9]+$/.test(t) ? 'P.' + t : t;
}
function vdThe(bg, txt) {
  return '<span style="display:inline-block;background:' + bg + ';color:#fff;border-radius:6px;padding:1px 6px;font-size:11px;line-height:16px">' + txt + '</span>';
}
/* Mau va icon cua tung trang thai van don, dung chung cho icon dau dong va
   chip mau. Loan Anh 08/08/2026: dau tick xanh nho o dau dong kho nhin, doi
   sang chip co chu. */
var VD_TT_ICON = { 'Chờ giao': '📦', 'Đang giao': '🛵', 'Đã giao': '✅', 'Không giao được': '⚠️', 'Huỷ': '⛔' };
var VD_TT_MAU = { 'Chờ giao': '#64748b', 'Đang giao': '#0369a1', 'Đã giao': '#12a150', 'Không giao được': '#b91c1c', 'Huỷ': '#7f1d1d' };
function vdHuyHieu(r) {
  var t = [];
  var tt = r.trang_thai || '';
  if (tt) t.push(vdThe(VD_TT_MAU[tt] || '#64748b', (VD_TT_ICON[tt] || '') + ' ' + h(tt)));
  /* Hai cho hay sot nhat: don chua ai nhan giao, va tien COD da thu ma chua
     doi soat. */
  if (tt === 'Chờ giao' && !r.shipper) t.push(vdThe('#c2410c', '🛵 Chưa phân công'));
  if (tt === 'Đã giao' && r.tien_thu_ho && !r.da_doi_soat) t.push(vdThe('#a16207', '💵 COD chưa đối soát'));
  if (r.thu_tu) t.push(vdThe('#0f766e', '#' + r.thu_tu + (r.gio_du_kien ? ' ~' + h(r.gio_du_kien) : '')));
  if (r.goi_truoc) t.push(vdThe('#b45309', '📞 Gọi trước'));
  if (r.chup_truoc) t.push(vdThe('#7c3aed', '📷 Gửi ảnh trước'));
  if (r.tre_khung_gio) t.push(vdThe('#b91c1c', '⚠️ Dễ trễ giờ'));
  if (r.ghi_chu_in) t.push(vdThe('#475569', '📝 ' + h(String(r.ghi_chu_in).replace(/[\r\n]+/g, ' ').slice(0, 38))));
  if (!t.length) return '';
  return '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:5px">' + t.join('') + '</div>';
}
function vdChip(id, nhan, dang) {
  return '<button class="btn gh" id="' + id + '" style="flex:0 0 auto;width:auto;padding:6px 12px;font-size:13px' + (dang ? ';background:#0f766e;color:#fff;border-color:#0f766e' : '') + '">' + nhan + '</button>';
}
function vdChipsHtml() {
  if (!vdBoLoc) return '';
  var s = '<div style="display:flex;gap:8px;overflow-x:auto;padding:0 14px 8px">';
  s += vdChip('vdFGio', vdTagGio ? '🕒 ' + h(vdTagGio) : '🕒 Khung giờ', !!vdTagGio);
  s += vdChip('vdFBuoi', vdBuoi ? '🌤️ ' + h(vdBuoi) : '🌤️ Buổi', !!vdBuoi);
  s += vdChip('vdFPhuong', vdPhuong ? '📍 ' + h(vdPhuongNgan(vdPhuong)) : '📍 Phường', !!vdPhuong);
  if (vdTagGio || vdBuoi || vdPhuong) s += vdChip('vdFXoa', '✖ Bỏ lọc', false);
  s += '</div>';
  if (vdBoLoc.so_thieu_the_gio) s += '<div class="sec" style="color:#b45309">⚠️ ' + vdBoLoc.so_thieu_the_gio + ' đơn chưa có thẻ khung giờ. Gắn thẻ bên Pancake rồi bấm Đồng bộ, đơn mới vào được tuyến.</div>';
  return s;
}
function vdGanChips() {
  var g = function (id, fn) { var b = document.getElementById(id); if (b) b.onclick = fn; };
  g('vdFGio', function () {
    var ops = [{ value: '', label: 'Tất cả khung giờ', icon: '🕒' }];
    ((vdBoLoc && vdBoLoc.khung_gio) || []).forEach(function (x) { ops.push({ value: x.v, label: x.v + '  (' + x.n + ' đơn)', icon: '🕒' }); });
    sheet('Lọc theo khung giờ', ops, vdTagGio || '', function (o) { vdTagGio = o.value || null; go(scrVanDon, true); });
  });
  g('vdFBuoi', function () {
    sheet('Lọc theo buổi', [
      { value: '', label: 'Cả ngày', icon: '🗓️' },
      { value: 'Sáng', label: 'Sáng (7h - 12h)', icon: '🌅' },
      { value: 'Chiều', label: 'Chiều (12h - 17h)', icon: '☀️' },
      { value: 'Tối', label: 'Tối (17h - 22h)', icon: '🌙' }
    ], vdBuoi || '', function (o) { vdBuoi = o.value || null; go(scrVanDon, true); });
  });
  g('vdFPhuong', function () {
    var ops = [{ value: '', label: 'Tất cả phường', icon: '📍' }];
    ((vdBoLoc && vdBoLoc.phuong) || []).forEach(function (x) { ops.push({ value: x.v, label: x.v + '  (' + x.n + ' đơn)', icon: '📍' }); });
    sheet('Lọc theo phường', ops, vdPhuong || '', function (o) { vdPhuong = o.value || null; go(scrVanDon, true); }, true);
  });
  g('vdFXoa', function () { vdTagGio = null; vdBuoi = null; vdPhuong = null; go(scrVanDon, true); });
}
async function vdChiDuongToi() {
  busy(true);
  try {
    var ds = await api('vagabond.van_don.chuyen_cua_toi', { ngay: vdNgay });
    busy(false);
    var co = (ds || []).filter(function (x) { return x.link_chi_duong; });
    if (!co.length) { toast('Chưa có đơn nào còn phải giao trong chuyến của mình.'); return; }
    if (co.length === 1) { window.open(co[0].link_chi_duong, '_blank'); return; }
    sheet('Mở chỉ đường chuyến nào?', co.map(function (x) { return { value: x.link_chi_duong, label: x.chuyen + ' · còn ' + x.con_lai + ' đơn', icon: '🗺️' }; }), '', function (o) { window.open(o.value, '_blank'); });
  } catch (e) { busy(false); window.alert((e && e.message) || 'Không tải được chuyến'); }
}

async function scrVdTuyen() {
  if (!vdNgay) vdNgay = today();
  var html = '<div class="card" style="padding:12px 14px">'
    + '<div class="sec" style="margin:0 0 8px;padding:0">Xếp tuyến ngày ' + h(vdNgay) + ' · chỉ lấy đơn nội bộ đang chờ giao, chưa gán ai</div>'
    + '<div style="display:flex;gap:8px;flex-wrap:wrap">'
    + '<button class="btn gh" id="vtB" style="flex:1;min-width:110px">🌤️ ' + h(vtBuoiChon || 'Cả ngày') + '</button>'
    + '<button class="btn gh" id="vtS" style="flex:1;min-width:110px">🛵 ' + vtSoTuyen + ' shipper</button>'
    + '<button class="btn gh" id="vtL" style="flex:1;min-width:110px">🏠 ' + h(vtDiemLay) + '</button>'
    + '</div>'
    + '<button class="btn" id="vtChay" style="margin-top:10px;width:100%">🧭 Đề xuất tuyến</button>'
    + '</div>';
  if (vtKq) {
    if (vtKq.thong_bao) html += '<div class="sec">' + h(vtKq.thong_bao) + '</div>';
    (vtKq.bo_qua || []).length && (html += '<div class="sec" style="color:#b45309">⚠️ ' + vtKq.bo_qua.length + ' đơn không xếp được vì chưa ra toạ độ: ' + h(vtKq.bo_qua.map(function (x) { return x.ma_don; }).join(', ')) + '</div>');
    (vtKq.tuyen || []).forEach(function (t, ix) {
      html += '<div class="sec">Tuyến ' + t.tuyen + ' · ' + t.so_don + ' đơn · ' + t.tong_km + ' km · ' + h(t.bat_dau) + ' đến ' + h(t.ket_thuc) + (t.tong_cod ? ' · COD ' + money(t.tong_cod) : '') + (t.phut_tre ? ' · ⚠️ trễ ' + t.phut_tre + ' phút' : '') + '</div>';
      html += '<div class="card">';
      t.diem.forEach(function (d) {
        html += '<div style="display:flex;gap:10px;padding:10px 14px;border-bottom:1px solid #f0f0f0">'
          + '<div style="flex:1;min-width:0">'
          + '<div class="h1">#' + d.thu_tu + ' · ' + h(d.ma_don || '') + ' · ' + h(d.khach || '') + '</div>'
          + '<div class="h2">' + (d.gio_du_kien ? 'đến ~' + h(d.gio_du_kien) + ' · ' : '') + (d.tag_gio ? h(d.tag_gio) + ' · ' : '') + h(vdPhuongNgan(d.phuong || '')) + ' · ' + d.km_chang + ' km</div>'
          + '<div class="h2">' + h((d.dia_chi || '').slice(0, 70)) + '</div>'
          + vdHuyHieu({ goi_truoc: d.goi_truoc, chup_truoc: d.chup_truoc, tre_khung_gio: d.tre, ghi_chu_in: d.ghi_chu_in })
          + '</div>'
          + (d.tien_thu_ho ? '<b style="white-space:nowrap;font-size:13px">' + money(d.tien_thu_ho) + '</b>' : '')
          + '</div>';
      });
      html += '</div>';
      html += '<div style="display:flex;gap:8px;padding:0 14px 16px">'
        + '<button class="btn" data-chot="' + ix + '" style="flex:2">✅ Giao tuyến này</button>'
        + '<button class="btn gh" data-map="' + ix + '" style="flex:1">🗺️ Chỉ đường</button>'
        + '</div>';
    });
  }
  frame('Xếp tuyến', html);
  var g = function (id, fn) { var b = document.getElementById(id); if (b) b.onclick = fn; };
  g('vtB', function () {
    sheet('Xếp cho buổi nào', [
      { value: '', label: 'Cả ngày', icon: '🗓️' },
      { value: 'Sáng', label: 'Sáng (7h - 12h)', icon: '🌅' },
      { value: 'Chiều', label: 'Chiều (12h - 17h)', icon: '☀️' },
      { value: 'Tối', label: 'Tối (17h - 22h)', icon: '🌙' }
    ], vtBuoiChon || '', function (o) { vtBuoiChon = o.value || null; vtKq = null; go(scrVdTuyen, true); });
  });
  g('vtS', function () {
    var ops = []; for (var i = 1; i <= 6; i++) ops.push({ value: String(i), label: i + ' shipper', icon: '🛵' });
    sheet('Chia cho mấy shipper', ops, String(vtSoTuyen), function (o) { vtSoTuyen = parseInt(o.value, 10) || 2; vtKq = null; go(scrVdTuyen, true); });
  });
  g('vtL', function () {
    sheet('Lấy bánh ở đâu', [{ value: 'Bếp', label: 'Bếp Nguyễn Văn Trỗi', icon: '🍳' }, { value: 'Tiệm', label: 'Tiệm Trần Cao Vân', icon: '🏬' }], vtDiemLay, function (o) { vtDiemLay = o.value; vtKq = null; go(scrVdTuyen, true); });
  });
  g('vtChay', async function () {
    busy(true);
    try {
      vtKq = await api('vagabond.xep_tuyen.de_xuat_tuyen', { ngay: vdNgay, buoi: vtBuoiChon || '', so_tuyen: vtSoTuyen, diem_lay: vtDiemLay });
      busy(false); go(scrVdTuyen, true);
    } catch (e) { busy(false); window.alert((e && e.message) || 'Không xếp được tuyến'); }
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-map]'), function (b) {
    b.onclick = function () { var t = vtKq.tuyen[parseInt(b.getAttribute('data-map'), 10)]; if (t && t.link_chi_duong) window.open(t.link_chi_duong, '_blank'); };
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-chot]'), function (b) {
    b.onclick = async function () {
      var t = vtKq.tuyen[parseInt(b.getAttribute('data-chot'), 10)];
      if (!t) return;
      if (!vtShipper) { busy(true); try { vtShipper = await api('vagabond.van_don.ds_shipper'); } catch (e) { vtShipper = []; } busy(false); }
      sheet('Giao tuyến ' + t.tuyen + ' (' + t.so_don + ' đơn) cho ai', (vtShipper || []).map(function (x) { return { value: x.user, label: x.ten, icon: '🛵' }; }), '', async function (o) {
        busy(true);
        try {
          await api('vagabond.xep_tuyen.chot_tuyen', { tuyen: JSON.stringify([{ tuyen: t.tuyen, shipper: o.value, diem: t.diem.map(function (d) { return { name: d.name, thu_tu: d.thu_tu, gio_du_kien: d.gio_du_kien, km_chang: d.km_chang, tre: d.tre }; }) }]) });
          busy(false); toast('Đã giao tuyến ' + t.tuyen + ' cho ' + o.label);
          vtKq.tuyen.splice(parseInt(b.getAttribute('data-chot'), 10), 1);
          go(scrVdTuyen, true);
        } catch (e) { busy(false); window.alert((e && e.message) || 'Chốt tuyến lỗi'); }
      });
    };
  });
}

// Trang chu cua site gio la app nhan vien (de app.thevagabondpatisserie.com
// mo ra la vao thang app). Rieng ten mien dat banh cua khach thi day ve /banh.
(function () {
  try {
    if ((location.hostname || '').indexOf('order') === 0 && location.pathname === '/') {
      location.replace('/banh');
    }
  } catch (eo) {}
})();

// Quet ma QR tren phieu in: /bep?vd=VD-2026-xxxxx mo thang van don do.
// Phai cho app boot xong (dang nhap + dung man chinh) roi moi nhay, nen doi
// theo nhip thay vi hen gio cung - 1,5 giay la chua kip.
(function () {
  var vdQR = null;
  try { vdQR = new URLSearchParams(location.search).get('vd'); } catch (e0) { return; }
  if (!vdQR) return;
  var n = 0;
  var hen = setInterval(function () {
    n++;
    if (n > 40) { clearInterval(hen); return; }
    try {
      if (S && S.stack && S.stack.length === 1 && root && (root.innerHTML || '').length > 400) {
        clearInterval(hen);
        history.replaceState({ vgbD: 0 }, '', location.pathname);
        go(function () { scrVdView(vdQR); });
      }
    } catch (e1) {}
  }, 400);
})();

/* ---------- Khuyen mai tren man tinh tien (anh Viet 11/08/2026) ----------

Cashier chon chuong trinh, bam combo, hoac go ma voucher. So tien giam
KHONG do may khach tu tinh: moi lan gio hang doi la goi may chu tinh lai.
Lam vay vi hai le:
  - so tren man hinh va so tren bill khong bao gio lech nhau
  - khong ai mo Devtools tu ha bill cua minh xuong duoc

Combo bam vao thi RA NGAY thanh tung mon thanh phan do vao gio (anh Viet
chot). Bill in ra chi thay ten mon that, khong in ma combo. */

function posKmChuKy() {
  return (posDon.mon || []).map(function (m) { return m.item_code + ':' + m.qty + ':' + m.rate; }).join('|') +
    '#' + (posDon.ctkm || []).join(',') +
    '#' + (posDon.combo || []).map(function (c) { return c.ma + 'x' + c.so_bo; }).join(',') +
    '#' + (posDon.maVc || '') +
    '#' + ((posDon.khach_no && posDon.khach_no.ma) || posDon.khach_ma || '') + '#' + (posDon.sdt || '');
}

async function posTinhKm() {
  var coGi = (posDon.ctkm && posDon.ctkm.length) || (posDon.combo && posDon.combo.length) || posDon.maVc;
  if (!coGi || !(posDon.mon || []).length) { posDon.kmKq = null; return; }
  var ck = posKmChuKy();
  if (posDon.kmKq && posDon.kmKq.ck === ck) return;
  try {
    var kq = await api('vagabond.khuyen_mai.xem_truoc', {
      items: JSON.stringify(posDon.mon.map(function (m) { return { item_code: m.item_code, qty: m.qty, rate: m.rate }; })),
      ctkm: JSON.stringify(posDon.ctkm || []),
      combo: JSON.stringify(posDon.combo || []),
      ma: posDon.maVc || '',
      quay: (posQuay && posQuay.ma) || '',
      nguon: posNguonThuc(),
      khach: (posDon.khach_no && posDon.khach_no.ma) || posDon.khach_ma || '',
      sdt: posDon.sdt || ''
    });
    kq.ck = ck;
    posDon.kmKq = kq;
  } catch (e) {
    /* Ma voucher hong thi go han ra khoi bill, khong de ket man hinh. */
    posDon.kmKq = null;
    posDon.maVc = '';
    toast((e && e.message) || 'Không tính được khuyến mãi', 4200);
  }
}

function posKhoiKm() {
  var kq = posDon.kmKq;
  var html = '<div><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:7px">' +
    '<span style="font-size:12.5px;color:#6b7280;font-weight:600">KHUYẾN MÃI</span></div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:8px">' +
    posChipNut('id="posKmChon"', '🎫 Chương trình', false) +
    /* KHONG co chip Combo o day nua (anh Viet 11/08/2026): combo la thu
       cashier chon LUC KHACH ORDER, nen no phai nam trong o "Them mon"
       cung cho voi mon binh thuong, khong phai o duoi khoi thanh toan. */
    posChipNut('id="posKmMa"', posDon.maVc ? '🎟 ' + h(posDon.maVc) : '🎟 Nhập mã', !!posDon.maVc) +
    '</div>';

  if (kq && (kq.ap || []).length) {
    html += '<div style="background:#f0fdfa;border:1.5px solid #7fe5f6;border-radius:9px;padding:9px 11px;margin-bottom:7px">';
    (kq.ap || []).forEach(function (a) {
      html += '<div style="display:flex;align-items:flex-start;gap:6px;padding:3px 0;font-size:13px">' +
        '<span style="flex:1;min-width:0">' + (a.loai === 'combo' ? '🧺 ' : '🎫 ') + '<b>' + h(a.ten) + '</b>' +
        (a.dien_giai ? '<div style="font-size:11.5px;color:#0b7c93;margin-top:1px">' + h(a.dien_giai) + '</div>' : '') + '</span>' +
        '<b style="flex:none;color:#0f766e">−' + money(a.giam) + ' đ</b>' +
        '<button data-kmbo="' + h(a.ma) + '" data-l="' + h(a.loai) + '" style="flex:none;border:0;background:transparent;color:#b3261e;font-size:15px;cursor:pointer;padding:0 2px">✕</button></div>';
    });
    html += '</div>';
  }
  if (kq && (kq.bo || []).length) {
    html += '<div style="background:#fff7ed;border:1.5px solid #fed7aa;border-radius:9px;padding:9px 11px;margin-bottom:7px;font-size:12px;color:#9a3412;line-height:1.6">' +
      (kq.bo || []).map(function (b) { return '<b>' + h(b.ten) + '</b>: ' + h(b.ly_do); }).join('<br>') + '</div>';
  }
  if (kq && (kq.them_mon || []).length) {
    html += '<div style="background:#fef3c7;border:1.5px solid #fcd34d;border-radius:9px;padding:9px 11px;margin-bottom:7px;font-size:12.5px;color:#92400e;line-height:1.6">' +
      'Khách được tặng ' + (kq.them_mon || []).map(function (t) { return '<b>' + num(t.qty) + '× ' + h(t.item_code) + '</b>'; }).join(', ') +
      ' nhưng chưa có trong đơn.<br>' +
      posChipNut('id="posKmThemTang"', '+ Thêm món tặng vào đơn', false) + '</div>';
  }
  if (kq && kq.can_otp) {
    html += '<div style="background:#fef2f2;border:1.5px solid #fecaca;border-radius:9px;padding:9px 11px;margin-bottom:7px;font-size:12.5px;color:#b3261e;line-height:1.6">' +
      '🔐 Chương trình này cần mã OTP của quản lý. Lúc bấm Thu tiền máy sẽ hỏi mã.</div>';
  }
  html += '</div>';
  return html;
}

function posNoiKm() {
  var n = document.getElementById('posKmChon');
  if (n) n.onclick = function () { posDoc(); posSheetChonKm(); };
  n = document.getElementById('posKmMa');
  if (n) n.onclick = function () { posDoc(); posSheetMaVc(); };
  n = document.getElementById('posKmThemTang');
  if (n) n.onclick = function () {
    posDoc();
    ((posDon.kmKq && posDon.kmKq.them_mon) || []).forEach(function (t) {
      var i = -1;
      posDon.mon.forEach(function (m, k) { if (m.item_code === t.item_code) i = k; });
      if (i >= 0) posDon.mon[i].qty += t.qty;
      else posDon.mon.push({ item_code: t.item_code, ten: t.item_code, qty: t.qty, rate: t.rate, anh: '', nhom: '', tc: [], gc: '' });
    });
    posDon.kmKq = null;
    go(scrPosQuay, true);
  };
  var b = document.getElementById('vgbBody');
  if (b) b.addEventListener('click', function (e) {
    var t = e.target.closest('[data-kmbo]');
    if (!t) return;
    posDoc();
    var ma = t.getAttribute('data-kmbo');
    if (t.getAttribute('data-l') === 'combo') {
      posDon.combo = (posDon.combo || []).filter(function (c) { return c.ma !== ma; });
    } else {
      posDon.ctkm = (posDon.ctkm || []).filter(function (c) { return c !== ma; });
      /* Chuong trinh nay den tu ma voucher thi go luon ma. */
      if (posDon.kmKq) {
        (posDon.kmKq.ap || []).forEach(function (a) { if (a.ma === ma && a.voucher) posDon.maVc = ''; });
      }
    }
    posDon.kmKq = null;
    go(scrPosQuay, true);
  });
}

async function posSheetChonKm() {
  busy(true);
  var kq;
  try {
    kq = await api('vagabond.khuyen_mai.ds_ctkm', {
      quay: (posQuay && posQuay.ma) || '', nguon: posNguonThuc(),
      khach: (posDon.khach_no && posDon.khach_no.ma) || posDon.khach_ma || '', sdt: posDon.sdt || ''
    });
  } catch (e) { busy(false); return toast((e && e.message) || 'Không tải được chương trình'); }
  busy(false);
  /* Chuong trinh phat ma dung mot lan thi phai go ma, khong bam chon
     thang duoc - khong thi ma xuat cho doi tac thanh vo nghia. */
  var ds = ((kq && kq.km) || []).filter(function (x) { return x.cach_ma !== 'Ma dung mot lan'; });
  if (!ds.length) return toast('Chưa có chương trình khuyến mãi nào đang bật cho quầy này.', 4500);

  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  function ve() {
    var html = '<div class="shh"><b>Chương trình khuyến mãi</b><div class="x">&times;</div></div>' +
      '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 14px);max-height:74vh;overflow:auto">';
    ds.forEach(function (x) {
      var chon = (posDon.ctkm || []).indexOf(x.name) >= 0;
      html += '<div data-kmc="' + h(x.name) + '" style="display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #f6f7f9;cursor:' + (x.dung_duoc ? 'pointer' : 'default') + ';opacity:' + (x.dung_duoc ? '1' : '.55') + '">' +
        '<span style="width:34px;height:34px;flex:none;border-radius:9px;background:' + (chon ? '#0d9488' : '#f0fdfa') + ';color:' + (chon ? '#fff' : '#0f766e') + ';display:flex;align-items:center;justify-content:center;font-size:17px">' + (chon ? '✓' : '🎫') + '</span>' +
        '<div style="flex:1;min-width:0"><div style="font-size:14.5px;font-weight:600">' + h(x.ten) + '</div>' +
        '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' + h(x.nhan_cach || '') + ' · ' + kmMucGiam(x) +
        (x.can_otp ? ' · 🔐 cần OTP' : '') + '</div>' +
        (x.dung_duoc ? '' : '<div style="font-size:11.5px;color:#9a3412;margin-top:3px">Không áp được lúc này: ' + h(x.ly_do) + '</div>') +
        '</div></div>';
    });
    html += '<button class="btn" id="kmXong" style="width:100%;margin-top:12px">Xong</button></div>';
    box.innerHTML = html;
    box.querySelector('.x').onclick = dong;
    box.querySelector('#kmXong').onclick = dong;
    box.querySelectorAll('[data-kmc]').forEach(function (o) {
      o.onclick = function () {
        var ma = o.getAttribute('data-kmc');
        var x = ds.filter(function (y) { return y.name === ma; })[0] || {};
        if (!x.dung_duoc) return toast(x.ly_do || 'Chương trình không áp được lúc này', 3800);
        posDon.ctkm = posDon.ctkm || [];
        var i = posDon.ctkm.indexOf(ma);
        if (i >= 0) posDon.ctkm.splice(i, 1); else posDon.ctkm.push(ma);
        posDon.kmKq = null;
        ve();
      };
    });
  }
  function dong() { ov.remove(); go(scrPosQuay, true); }
  ve();
  ov.appendChild(box);
  ov.onclick = function (e) { if (e.target === ov) dong(); };
  document.body.appendChild(ov);
}

async function posSheetCombo() {
  busy(true);
  var kq;
  try { kq = await api('vagabond.khuyen_mai.ds_combo', { quay: (posQuay && posQuay.ma) || '', nguon: posNguonThuc() }); }
  catch (e) { busy(false); return toast((e && e.message) || 'Không tải được combo'); }
  busy(false);
  var ds = (kq && kq.combo) || [];
  if (!ds.length) return toast('Chưa có combo nào đang bật cho quầy này.', 4500);

  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  var html = '<div class="shh"><b>Combo</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 14px);max-height:74vh;overflow:auto">' +
    '<div style="font-size:12px;color:#6b7280;margin-bottom:10px;line-height:1.6">Bấm một combo là máy tự đổ các món thành phần vào hoá đơn rồi trừ tiền bên dưới. Bill in ra chỉ thấy tên món thật.</div>';
  ds.forEach(function (x) {
    var mon = comboMoTa(x);
    html += '<div data-cbc="' + h(x.name) + '" style="display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #f6f7f9;cursor:pointer;opacity:' + (x.dung_duoc ? '1' : '.55') + '">' +
      '<span style="width:34px;height:34px;flex:none;border-radius:9px;background:#f0fdfa;display:flex;align-items:center;justify-content:center;font-size:17px">🧺</span>' +
      '<div style="flex:1;min-width:0"><div style="font-size:14.5px;font-weight:600">' + h(x.ten) + '</div>' +
      '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' + mon + '</div>' +
      '<div style="font-size:12px;color:#0f766e;margin-top:2px"><s style="color:#c3c8d4">' + money(x.gia_goc) + 'đ</s> → <b>' + money(x.gia_combo) + 'đ</b> · tiết kiệm ' + (x.co_nhom ? 'từ ' : '') + money(x.tiet_kiem) + 'đ</div>' +
      (x.dung_duoc ? '' : '<div style="font-size:11.5px;color:#9a3412;margin-top:3px">' + h(x.ly_do) + '</div>') +
      '</div><span style="color:#c3c8d4;font-size:18px">›</span></div>';
  });
  html += '</div>';
  box.innerHTML = html;
  box.querySelector('.x').onclick = function () { ov.remove(); };
  box.querySelectorAll('[data-cbc]').forEach(function (o) {
    o.onclick = async function () {
      var ma = o.getAttribute('data-cbc');
      var x = ds.filter(function (y) { return y.name === ma; })[0] || {};
      if (!x.dung_duoc) return toast(x.ly_do || 'Combo không bán được lúc này', 3800);
      ov.remove();
      if (x.co_nhom) {
        posSheetChonCombo(x, function (chon) { posThemCombo(x, chon); go(scrPosQuay, true); });
        return;
      }
      posThemCombo(x);
      go(scrPosQuay, true);
    };
  });
  ov.appendChild(box);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  document.body.appendChild(ov);
}

function posSheetMaVc() {
  var ov = document.createElement('div'); ov.className = 'sh';
  ov.innerHTML = '<div class="shb" style="padding:18px 16px calc(env(safe-area-inset-bottom,0px) + 16px)">' +
    '<div style="font-size:17.5px;font-weight:700;margin-bottom:4px">Mã ưu đãi của khách</div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-bottom:12px;line-height:1.6">Khách đọc mã, thu ngân gõ vào đây. Máy tự kiểm mã còn hạn không, đã ai dùng chưa.</div>' +
    '<input class="nt" id="vcO" placeholder="Ví dụ K7M2QP" autocapitalize="characters" style="text-transform:uppercase;letter-spacing:2px;font-size:18px;text-align:center" value="' + h(posDon.maVc || '') + '">' +
    '<div id="vcBao" style="font-size:12.5px;color:#b3261e;margin-top:8px;min-height:18px"></div>' +
    '<button class="btn" data-y style="margin-top:6px">Áp mã</button>' +
    (posDon.maVc ? '<button class="btn gh" data-x style="margin-top:9px">Bỏ mã đang dùng</button>' : '') +
    '<button class="btn gh" data-n style="margin-top:9px">Đóng</button></div>';
  document.body.appendChild(ov);
  var o = ov.querySelector('#vcO');
  setTimeout(function () { o.focus(); }, 120);
  async function ap() {
    var ma = (o.value || '').trim().toUpperCase();
    var bao = ov.querySelector('#vcBao');
    if (!ma) { bao.textContent = 'Chưa nhập mã.'; return; }
    bao.style.color = '#6b7280'; bao.textContent = 'Đang kiểm mã...';
    try {
      var kq = await api('vagabond.khuyen_mai.tra_ma', {
        ma: ma, quay: (posQuay && posQuay.ma) || '', nguon: posNguonThuc()
      });
      if (!kq.dung_duoc) { bao.style.color = '#b3261e'; bao.textContent = kq.ly_do || 'Mã không dùng được lúc này.'; return; }
      posDon.maVc = ma;
      posDon.kmKq = null;
      ov.remove();
      toast('Đã áp mã ' + ma + ' · ' + kq.ten);
      go(scrPosQuay, true);
    } catch (e) {
      bao.style.color = '#b3261e';
      bao.textContent = (e && e.message) || 'Mã không dùng được.';
    }
  }
  o.onkeydown = function (e) { if (e.key === 'Enter') ap(); };
  ov.onclick = function (e) {
    if (e.target === ov || e.target.hasAttribute('data-n')) return ov.remove();
    if (e.target.hasAttribute('data-x')) { posDon.maVc = ''; posDon.kmKq = null; ov.remove(); return go(scrPosQuay, true); }
    if (e.target.hasAttribute('data-y')) ap();
  };
}

/* O tim khach tren man tinh tien: go la xo danh sach, bam mot dong la gan
   ho so khach vao hoa don. Gan ho so khach KHONG phai chuyen sang ban cong
   no - no chi de biet khach nay la ai, hang gi, de ap dung chuong trinh
   khuyen mai theo hang va de cham soc sau nay (anh Viet 11/08/2026). */
var posTreTim = null;
function posNoiTimKhach() {
  var o = document.getElementById('posTen');
  var hop = document.getElementById('posTenGoi');
  if (!o || !hop) return;
  var nBo = document.getElementById('posBoKhach');
  if (nBo) nBo.onclick = function () {
    posDoc();
    posDon.khach_ma = ''; posDon.khach_hang = '';
    posDon.kmKq = null;
    go(scrPosQuay, true);
  };
  function dong() { hop.innerHTML = ''; }
  /* Hop goi y phai NOI TREN mat kinh chu khong nam trong the .card: CSS cua
     app dat .card{overflow:hidden} nen danh sach dai bi cat cut, tren dien
     thoai gan nhu khong thay gi (anh Viet 12/08/2026 - "vẫn chưa xổ ra danh
     sách"). Dung position:fixed va tu tinh toa do theo o nhap. */
  function neo(el) {
    var r = o.getBoundingClientRect();
    var duoi = window.innerHeight - r.bottom;
    el.style.position = 'fixed';
    el.style.left = r.left + 'px';
    el.style.width = r.width + 'px';
    el.style.zIndex = '2147483000';
    if (duoi < 190 && r.top > duoi) {
      el.style.bottom = (window.innerHeight - r.top + 4) + 'px';
      el.style.maxHeight = Math.max(140, r.top - 60) + 'px';
    } else {
      el.style.top = (r.bottom + 4) + 'px';
      el.style.maxHeight = Math.max(140, duoi - 16) + 'px';
    }
  }
  function ve(ds) {
    if (!ds.length) {
      hop.innerHTML = '<div style="background:#fff;border:1.5px solid #e5e7eb;border-radius:10px;padding:11px 13px;font-size:13px;color:#98a2b3;box-shadow:0 6px 18px rgba(16,24,40,.12)">Không có khách nào khớp. Cứ gõ tên tự do cũng được.</div>';
      neo(hop.firstElementChild);
      return;
    }
    hop.innerHTML = '<div style="overflow:auto;background:#fff;border:1.5px solid #7fe5f6;border-radius:10px;box-shadow:0 6px 18px rgba(16,24,40,.12)">' +
      ds.slice(0, 25).map(function (k) {
        return '<div data-kchon="' + h(k.name) + '" style="padding:10px 12px;border-bottom:1px solid #f6f7f9;cursor:pointer">' +
          '<div style="font-size:14px;font-weight:600">' + h(k.customer_name || k.name) + '</div>' +
          '<div style="font-size:11.5px;color:#98a2b3">' + h(k.name) +
          (k.mobile_no ? ' · ' + h(k.mobile_no) : '') +
          (k.tax_id ? ' · MST ' + h(k.tax_id) : '') +
          (k.customer_group ? ' · ' + h(k.customer_group) : '') + '</div></div>';
      }).join('') + '</div>';
    neo(hop.firstElementChild);
    hop.querySelectorAll('[data-kchon]').forEach(function (el) {
      el.onclick = async function () {
        var ma = el.getAttribute('data-kchon');
        var k = ds.filter(function (x) { return x.name === ma; })[0] || {};
        posDoc();
        posDon.khach_ma = ma;
        posDon.ten = k.customer_name || ma;
        if (k.mobile_no && !posDon.sdt) posDon.sdt = k.mobile_no;
        posDon.kmKq = null;
        dong();
        try {
          var tt = await api('vagabond.cong_no.thong_tin_xhd', { khach: ma });
          if (tt && tt.mst) {
            posDon.xhd_mo = true;
            posDon.xh = { mst: tt.mst || '', ten: tt.ten || '', dc: tt.dia_chi || '', email: tt.email || '' };
          }
        } catch (e) { }
        go(scrPosQuay, true);
      };
    });
  }
  async function tim(q) {
    try {
      var kq = await api('vagabond.cong_no.tim_khach', { tu_khoa: q });
      ve((kq && kq.khach) || []);
    } catch (e) { dong(); }
  }
  o.oninput = function () {
    if (posTreTim) clearTimeout(posTreTim);
    var q = o.value.trim();
    /* Mot ky tu cung tim: khach hay dat ten goi nho rat ngan ("Ry", "An"),
       bat tu hai ky tu la go mai khong thay gi. */
    if (!q) { return tim(''); }
    posTreTim = setTimeout(function () { tim(q); }, 260);
  };
  /* Bam vao o la xo luon danh sach khach gan day, khoi phai nho ten. */
  o.onfocus = function () { tim(o.value.trim()); };
  o.onblur = function () { setTimeout(dong, 220); };
}

/* Chuong trinh nao bat buoc OTP quan ly thi hoi ma ngay truoc khi luu.
   Sep tu thao tac thi may chu cho qua, khoi nhap. */
async function posXinOtpKm() {
  if (!(posDon.kmKq && posDon.kmKq.can_otp)) return '';
  var ma = await promptSheet('Khuyến mãi này cần mã OTP của quản lý', 'Nhập 6 số quản lý đọc cho');
  return (ma || '').replace(/\D/g, '');
}

/* ---------- Chuong trinh khuyen mai va combo (anh Viet 11/08/2026) ----------

Bay cach thuc anh Viet liet ke deu cau hinh duoc ngay tren app, khong phai
mo Desk. Man nay chia bon the:
  - Chuong trinh: bay cach thuc, thoi gian, doi tuong, kenh ban, han muc
  - Combo: phoi mon thanh goi; luc tinh tien may RA thanh mon thanh phan
  - Ma voucher: hai cach phat ma (co dinh cho cashier chon, hoac xuat lo
    ma 6 ky tu gui qua email cho doi tac)
  - Bao cao: tien da giam, xep hang thu ngan - de SOI ai giam bat thuong

MOI NUT DEU LA CHIP theo y anh Viet 09/08/2026. */

var kmThe = 'ct', kmLocCt = '', kmData = null, kmSua = null, kmDm = null;

/* Chip nhieu lua chon tren mot truong dang "moi dong mot gia tri". Tra ve
   HTML hang chip; nguoi dung bam chip nao thi them hoac bo dong do. */
function kmChipNhieu(thuoc, ds, giaTri) {
  var da = String(giaTri || '').split('\n').map(function (s) { return s.trim(); }).filter(Boolean);
  if (!ds || !ds.length) return '<div style="font-size:11.5px;color:#98a2b3;margin-bottom:10px">Danh mục đang trống.</div>';
  return '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px">' +
    ds.map(function (x) {
      var ma = typeof x === 'string' ? x : x.ma;
      var ten = typeof x === 'string' ? x : x.ten;
      return posChipNut(thuoc + '="' + h(ma) + '"', h(ten), da.indexOf(ma) >= 0);
    }).join('') + '</div>';
}

/* Bam mot chip nhieu lua chon: co roi thi bo ra, chua co thi them vao. */
function kmDoiDong(giaTri, ma) {
  var da = String(giaTri || '').split('\n').map(function (s) { return s.trim(); }).filter(Boolean);
  var i = da.indexOf(ma);
  if (i >= 0) da.splice(i, 1); else da.push(ma);
  return da.join('\n');
}

/* Ba diem ban. Don Sales online khong mang ma quay nen quy uoc la SALES,
   may chu cung hieu quy uoc nay (khuyen_mai._hop_kenh). */
var KM_QUAY = [
  { ma: 'SALES', ten: 'Sales Online' },
  { ma: 'TCV', ten: 'District 1' },
  { ma: 'NVHTN', ten: 'NVHTN' }
];

var KM_CACH = [
  { k: 'Giam tong hoa don', nhan: 'Giảm tổng hoá đơn', ic: '🧾', mo: 'Giảm % hoặc số tiền trên cả hoá đơn' },
  { k: 'Giam gia mon', nhan: 'Giảm giá món', ic: '🍰', mo: 'Chỉ giảm trên món hoặc nhóm món chỉ định' },
  { k: 'Mua A giam B', nhan: 'Mua A giảm B', ic: '🔁', mo: 'Mua đủ món điều kiện thì món ưu đãi được giảm' },
  { k: 'Mua X tang Y', nhan: 'Mua X tặng Y', ic: '🎁', mo: 'Mua 2 tặng 1, mua 3 tặng 1...' },
  { k: 'Tang mon', nhan: 'Tặng món', ic: '🍬', mo: 'Đạt điều kiện thì tặng hẳn một món' },
  { k: 'Dong gia', nhan: 'Đồng giá', ic: '🏷️', mo: 'Kéo món về một mức giá cố định' },
  { k: 'Giam luy ke', nhan: 'Giảm luỹ kế', ic: '📈', mo: 'Bậc thang: hoá đơn càng lớn giảm càng sâu' }
];
function kmNhanCach(k) {
  for (var i = 0; i < KM_CACH.length; i++) if (KM_CACH[i].k === k) return KM_CACH[i];
  return { k: k, nhan: k, ic: '🎫', mo: '' };
}

/* Bootstrap cua Frappe dat .card{display:flex;flex-direction:column} nen chip
   nhet thang vao .card se xep DOC va gian het be ngang (bat duoc khi nghiem
   thu v107). Luon boc chip trong mot lop div rieng. */
function kmHangChip(noiDung) {
  return '<div style="display:flex;flex-direction:row;flex-wrap:wrap;gap:7px">' + noiDung + '</div>';
}

function kmTheChip(t, nhan) { return posChipNut('data-kmthe="' + t + '"', nhan, kmThe === t); }

async function scrKhuyenMai() {
  frame('Khuyến mãi - combo', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc chương trình...</div></div>');
  var ct, cb;
  try {
    ct = await api('vagabond.khuyen_mai.ds_ctkm', { tat_ca: 1 });
    cb = await api('vagabond.khuyen_mai.ds_combo', { tat_ca: 1 });
    /* Hang khach, nhom khach, nhom mon va quay lay tu may de bay ra thanh
       chip cho bam, khoi go tay (anh Viet 12/08/2026). */
    if (!kmDm) { try { kmDm = await api('vagabond.khuyen_mai.danh_muc', {}); } catch (e2) { kmDm = null; } }
  } catch (e) {
    frame('Khuyến mãi - combo', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>');
    return;
  }
  kmData = { ct: (ct && ct.km) || [], cb: (cb && cb.combo) || [] };
  var dsCt = kmData.ct, dsCb = kmData.cb;
  var dangBat = dsCt.filter(function (x) { return x.bat; }).length;
  var cbBat = dsCb.filter(function (x) { return x.bat; }).length;

  var html = '<div class="card" style="padding:12px 14px;display:flex;flex-direction:row;gap:10px">' +
    '<div style="flex:1"><div style="font-size:12px;color:#98a2b3">CHƯƠNG TRÌNH</div>' +
    '<div style="font-size:19px;font-weight:800">' + dangBat + ' đang chạy</div>' +
    '<div style="font-size:12px;color:#98a2b3">' + dsCt.length + ' chương trình đã cấu hình</div></div>' +
    '<div style="flex:1;border-left:1px solid #eef0f4;padding-left:10px"><div style="font-size:12px;color:#98a2b3">COMBO</div>' +
    '<div style="font-size:19px;font-weight:800;color:#0f766e">' + cbBat + ' đang bán</div>' +
    '<div style="font-size:12px;color:#98a2b3">' + dsCb.length + ' combo đã phối</div></div></div>';

  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    kmTheChip('ct', '🎫 Tạo voucher') + kmTheChip('cb', '🧺 Combo') +
    kmTheChip('lo', '📮 Xuất danh sách mã voucher') + kmTheChip('bc', '📊 Báo cáo')) + '</div>';

  if (kmThe === 'ct') html += kmHtmlCt(dsCt);
  else if (kmThe === 'cb') html += kmHtmlCb(dsCb);
  else if (kmThe === 'lo') html += '<div class="card" id="kmLoBox" style="padding:6px 14px"><div class="emp" style="padding:22px"><div class="e1">⏳</div><div>Đang đọc lô mã...</div></div></div>';
  else html += '<div class="card" id="kmBcBox" style="padding:6px 14px"><div class="emp" style="padding:22px"><div class="e1">⏳</div><div>Đang cộng sổ...</div></div></div>';

  var b = frame('Khuyến mãi - combo', html, {
    fab: (kmThe === 'ct' || kmThe === 'cb'),
    onFab: function () { kmThe === 'cb' ? kmSheetCombo(null) : kmSheetCtkm(null); }
  });

  if (kmThe === 'lo') kmVeLo();
  if (kmThe === 'bc') kmVeBaoCao();

  b.onclick = function (e) {
    var t = e.target.closest('[data-kmthe]');
    if (t) { kmThe = t.getAttribute('data-kmthe'); return go(scrKhuyenMai, true); }
    t = e.target.closest('[data-kmloc]');
    if (t) { kmLocCt = t.getAttribute('data-kmloc'); return go(scrKhuyenMai, true); }
    t = e.target.closest('[data-kmbat]');
    if (t) return kmBatTat(t.getAttribute('data-kmbat'), t.getAttribute('data-loai'));
    t = e.target.closest('[data-kmx]');
    if (t) return kmSheetCtkm(t.getAttribute('data-kmx'));
    t = e.target.closest('[data-kmcb]');
    if (t) return kmSheetCombo(t.getAttribute('data-kmcb'));
    t = e.target.closest('[data-kmxlo]');
    if (t) return kmSheetXuatLo(t.getAttribute('data-kmxlo'));
    t = e.target.closest('[data-kmlo]');
    if (t) return kmSheetLo(t.getAttribute('data-kmlo'));
    t = e.target.closest('[data-kmgui]');
    if (t) return kmGuiLai(t.getAttribute('data-kmgui'));
  };
}

/* --- the Chuong trinh --- */
function kmHtmlCt(ds) {
  var LOC = [{ k: '', nhan: 'Tất cả' }, { k: 'bat', nhan: '● Đang chạy' }, { k: 'tat', nhan: '○ Đang tắt' }];
  KM_CACH.forEach(function (c) { LOC.push({ k: c.k, nhan: c.ic + ' ' + c.nhan }); });
  var loc = kmLocCt;
  var d2 = ds.filter(function (x) {
    if (!loc) return true;
    if (loc === 'bat') return !!x.bat;
    if (loc === 'tat') return !x.bat;
    return x.cach_thuc === loc;
  });
  var html = '<div class="card" style="padding:10px 12px">' + kmHangChip(
    LOC.map(function (c) { return posChipNut('data-kmloc="' + h(c.k) + '"', c.nhan, c.k === loc); }).join('')) + '</div>';
  html += '<div class="sec">Chương trình</div><div class="card" style="padding:6px 14px">';
  if (!d2.length) html += '<div class="emp" style="padding:24px"><div class="e1">🎫</div><div>Chưa có chương trình nào ở nhóm này.<br>Bấm nút <b>+</b> góc dưới để tạo.</div></div>';
  d2.forEach(function (x) {
    var c = kmNhanCach(x.cach_thuc);
    html += '<div style="display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #f6f7f9">' +
      '<span style="width:38px;height:38px;flex:none;border-radius:10px;background:' + (x.bat ? '#f0fdfa' : '#f6f7f9') + ';display:flex;align-items:center;justify-content:center;font-size:18px">' + c.ic + '</span>' +
      '<div data-kmx="' + h(x.name) + '" style="flex:1;min-width:0;cursor:pointer">' +
      '<div style="font-size:14.5px;font-weight:600">' + h(x.ten) + '</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px">' +
      kmChipNho(c.nhan, '#eef2ff', '#3730a3') +
      kmChipNho(kmMucGiam(x), '#fef3c7', '#92400e') +
      (x.cach_ma === 'Ma co dinh' ? kmChipNho('mã ' + h(x.ma_co_dinh), '#f0fdfa', '#0f766e') : '') +
      (x.cach_ma === 'Ma dung mot lan' ? kmChipNho('mã dùng 1 lần', '#f0fdfa', '#0f766e') : '') +
      (x.can_otp ? kmChipNho('🔐 cần OTP', '#fef2f2', '#b3261e') : '') +
      (x.bat && !x.dung_duoc ? kmChipNho(h(x.ly_do), '#fff7ed', '#9a3412') : '') +
      (x.da_dung ? kmChipNho('đã dùng ' + x.da_dung, '#f6f7f9', '#6b7280') : '') +
      '</div></div>' +
      posChipNut('data-kmbat="' + h(x.name) + '" data-loai="ct"', x.bat ? '● Bật' : '○ Tắt', !!x.bat) +
      '</div>';
  });
  html += '</div>';
  return html;
}

function kmChipNho(chu, nen, mau) {
  return '<span style="background:' + nen + ';color:' + mau + ';border-radius:999px;padding:2px 9px;font-size:11.5px;font-weight:600">' + chu + '</span>';
}

function kmMucGiam(x) {
  if (x.cach_thuc === 'Dong gia') return 'đồng giá ' + money(x.gia_dong) + 'đ';
  if (x.cach_thuc === 'Giam luy ke') return 'theo bậc';
  if (x.cach_thuc === 'Mua X tang Y' || x.cach_thuc === 'Tang mon') return 'tặng món';
  return x.kieu_giam === 'So tien' ? 'giảm ' + money(x.gia_tri) + 'đ' : 'giảm ' + num(x.gia_tri) + '%';
}

/* --- the Combo --- */
function kmHtmlCb(ds) {
  var html = '<div class="sec">Combo</div><div class="card" style="padding:6px 14px">';
  if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">🧺</div><div>Chưa phối combo nào.<br>Bấm nút <b>+</b> góc dưới để tạo.</div></div>';
  ds.forEach(function (x) {
    var mon = comboMoTa(x);
    html += '<div style="display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #f6f7f9">' +
      '<span style="width:38px;height:38px;flex:none;border-radius:10px;background:' + (x.bat ? '#f0fdfa' : '#f6f7f9') + ';display:flex;align-items:center;justify-content:center;font-size:18px">🧺</span>' +
      '<div data-kmcb="' + h(x.name) + '" style="flex:1;min-width:0;cursor:pointer">' +
      '<div style="font-size:14.5px;font-weight:600">' + h(x.ten) + '</div>' +
      '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' + mon + '</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px">' +
      kmChipNho('<s>' + money(x.gia_goc) + 'đ</s> → <b>' + money(x.gia_combo) + 'đ</b>', '#eef2ff', '#3730a3') +
      kmChipNho('khách tiết kiệm ' + money(x.tiet_kiem) + 'đ', '#fef3c7', '#92400e') +
      (x.can_otp ? kmChipNho('🔐 cần OTP', '#fef2f2', '#b3261e') : '') +
      (x.bat && !x.dung_duoc ? kmChipNho(h(x.ly_do), '#fff7ed', '#9a3412') : '') +
      '</div></div>' +
      posChipNut('data-kmbat="' + h(x.name) + '" data-loai="cb"', x.bat ? '● Bật' : '○ Tắt', !!x.bat) +
      '</div>';
  });
  html += '</div>';
  return html;
}

async function kmBatTat(ma, loai) {
  var ds = loai === 'cb' ? kmData.cb : kmData.ct;
  var x = ds.filter(function (y) { return y.name === ma; })[0] || {};
  try {
    await api(loai === 'cb' ? 'vagabond.khuyen_mai.bat_tat_combo' : 'vagabond.khuyen_mai.bat_tat_ctkm',
      { ma: ma, bat: x.bat ? 0 : 1 });
    toast(x.bat ? 'Đã tắt "' + (x.ten || ma) + '"' : 'Đã bật "' + (x.ten || ma) + '"');
    go(scrKhuyenMai, true);
  } catch (e) { toast((e && e.message) || 'Không đổi được'); }
}

/* --- the Lo ma voucher --- */
async function kmVeLo() {
  var box = document.getElementById('kmLoBox'); if (!box) return;
  var kq;
  try { kq = await api('vagabond.khuyen_mai.ds_lo', {}); }
  catch (e) { box.innerHTML = '<div class="emp" style="padding:22px"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'; return; }
  var ds = (kq && kq.lo) || [];
  var maLan = kmData.ct.filter(function (x) { return x.cach_ma === 'Ma dung mot lan'; });
  var html = '';
  if (!maLan.length) {
    html += '<div style="padding:12px 0;font-size:13px;color:#92400e;background:#fffbeb;border:1.5px solid #fcd34d;border-radius:9px;padding:11px 13px;margin:8px 0">' +
      'Chưa có chương trình nào để cách phát mã là <b>Mã dùng một lần</b>. Mở một chương trình rồi đổi cách phát mã, sau đó mới xuất lô được.</div>';
  } else {
    html += '<div style="padding:10px 0;font-size:12.5px;color:#6b7280;font-weight:700">XUẤT LÔ MÃ MỚI CHO CHƯƠNG TRÌNH</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:7px;padding-bottom:12px">' +
      maLan.map(function (x) { return posChipNut('data-kmxlo="' + h(x.name) + '"', '📮 ' + h(x.ten), false); }).join('') + '</div>';
  }
  if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">📮</div><div>Chưa xuất lô mã nào.</div></div>';
  ds.forEach(function (x) {
    var mau = x.trang_thai === 'Da gui' ? ['#f0fdfa', '#0f766e'] : (x.trang_thai === 'Loi gui' ? ['#fef2f2', '#b3261e'] : ['#fffbeb', '#92400e']);
    html += '<div style="padding:11px 0;border-bottom:1px solid #f6f7f9">' +
      '<div style="display:flex;align-items:center;gap:10px">' +
      '<div data-kmlo="' + h(x.name) + '" style="flex:1;min-width:0;cursor:pointer">' +
      '<div style="font-size:14.5px;font-weight:600">' + h(x.ten_ctkm || x.ctkm) + '</div>' +
      '<div style="font-size:12px;color:#98a2b3;margin-top:2px">' + h(x.name) + ' · ' + x.so_luong + ' mã · gửi ' + h(x.email_nhan) +
      (x.gui_cho ? ' · cho ' + h(x.gui_cho) : '') + '</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px">' +
      kmChipNho(x.trang_thai === 'Da gui' ? '✓ đã gửi mail' : (x.trang_thai === 'Loi gui' ? '⚠️ lỗi gửi mail' : '⏳ chờ gửi'), mau[0], mau[1]) +
      kmChipNho('đã dùng ' + (x.da_dung || 0) + '/' + x.so_luong, '#eef2ff', '#3730a3') +
      (x.han_dung ? kmChipNho('hạn ' + posNgayVn(x.han_dung), '#f6f7f9', '#6b7280') : '') +
      '</div></div>' +
      (x.trang_thai === 'Da gui' ? '' : posChipNut('data-kmgui="' + h(x.name) + '"', '📨 Gửi lại', false)) +
      '</div>' +
      (x.loi_gui ? '<div style="font-size:11.5px;color:#b3261e;margin-top:5px">' + h(x.loi_gui) + '</div>' : '') +
      '</div>';
  });
  box.innerHTML = html;
}

async function kmGuiLai(lo) {
  toast('Đang gửi lại...');
  try {
    var kq = await api('vagabond.khuyen_mai.gui_lai_lo', { lo: lo });
    toast(kq.da_gui ? 'Đã gửi lại ' + kq.so_luong + ' mã' : ('Vẫn lỗi: ' + (kq.loi || '')));
    go(scrKhuyenMai, true);
  } catch (e) { toast((e && e.message) || 'Không gửi được'); }
}

/* --- the Bao cao --- */
async function kmVeBaoCao() {
  var box = document.getElementById('kmBcBox'); if (!box) return;
  var kq;
  try { kq = await api('vagabond.khuyen_mai.bao_cao', {}); }
  catch (e) { box.innerHTML = '<div class="emp" style="padding:22px"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không tải được') + '</div></div>'; return; }
  var html = '<div style="display:flex;gap:10px;padding:12px 0;border-bottom:1px solid #f6f7f9">' +
    '<div style="flex:1"><div style="font-size:12px;color:#98a2b3">ĐÃ GIẢM ' + posNgayVn(kq.tu) + ' → ' + posNgayVn(kq.den) + '</div>' +
    '<div style="font-size:20px;font-weight:800;color:#b3261e">' + money(kq.tong_giam) + ' đ</div></div>' +
    '<div style="flex:1;border-left:1px solid #eef0f4;padding-left:10px"><div style="font-size:12px;color:#98a2b3">SỐ LƯỢT</div>' +
    '<div style="font-size:20px;font-weight:800">' + kq.so_luot + '</div></div></div>';

  html += '<div style="padding:12px 0 6px;font-size:12.5px;color:#6b7280;font-weight:700">THU NGÂN ĐÃ GIẢM NHIỀU NHẤT</div>';
  if (!kq.theo_nguoi.length) html += '<div style="padding:14px 0;color:#98a2b3;font-size:13px">Chưa có lượt khuyến mãi nào trong kỳ.</div>';
  kq.theo_nguoi.forEach(function (r, i) {
    html += '<div style="display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #f6f7f9">' +
      '<span style="width:26px;text-align:center;font-weight:800;color:' + (i === 0 ? '#b3261e' : '#98a2b3') + '">' + (i + 1) + '</span>' +
      '<div style="flex:1;min-width:0;font-size:14px">' + h(r.nguoi) + '</div>' +
      '<div style="text-align:right"><b>' + money(r.tien) + ' đ</b>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + r.so + ' lượt</div></div></div>';
  });

  html += '<div style="padding:14px 0 6px;font-size:12.5px;color:#6b7280;font-weight:700">CHƯƠNG TRÌNH TỐN NHẤT</div>';
  kq.theo_ct.forEach(function (r) {
    html += '<div style="display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #f6f7f9">' +
      '<div style="flex:1;min-width:0;font-size:14px">' + h(r.ten) + ' ' + kmChipNho(r.loai === 'Combo' ? 'combo' : 'CTKM', '#eef2ff', '#3730a3') + '</div>' +
      '<div style="text-align:right"><b>' + money(r.tien) + ' đ</b>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + r.so + ' lượt</div></div></div>';
  });
  html += '<div style="padding:12px 0;font-size:12px;color:#98a2b3;line-height:1.6">Bảng này để soi: một thu ngân bỗng nhiên giảm gấp nhiều lần người khác là có chuyện. Mọi lượt áp khuyến mãi đều ghi lại ai bấm, bill nào, lúc mấy giờ.</div>';
  box.innerHTML = html;
}

/* ---------- Sheet cau hinh mot chuong trinh ---------- */
function kmO(nhan, id, val, ph, kieu, mo) {
  return '<div style="margin-bottom:11px"><div style="font-size:12.5px;color:#6b7280;font-weight:700;margin-bottom:5px">' + nhan + '</div>' +
    '<input class="tin" id="' + id + '" type="' + (kieu || 'text') + '" value="' + h(val == null ? '' : val) + '" placeholder="' + h(ph || '') + '">' +
    (mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo + '</div>' : '') + '</div>';
}
function kmOta(nhan, id, val, ph, mo) {
  return '<div style="margin-bottom:11px"><div style="font-size:12.5px;color:#6b7280;font-weight:700;margin-bottom:5px">' + nhan + '</div>' +
    '<textarea class="tin" id="' + id + '" rows="3" placeholder="' + h(ph || '') + '" style="resize:vertical">' + h(val || '') + '</textarea>' +
    (mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo + '</div>' : '') + '</div>';
}
function kmV(id) { var o = document.getElementById(id); return o ? o.value.trim() : ''; }
function kmN(id) { var o = document.getElementById(id); return o ? (parseFloat(o.value) || 0) : 0; }

async function kmSheetCtkm(ma) {
  var km = null;
  if (ma) {
    try { var r = await api('vagabond.khuyen_mai.xem_ctkm', { ma: ma }); km = r.km; }
    catch (e) { toast((e && e.message) || 'Không mở được'); return; }
  }
  km = km || {
    cach_thuc: 'Giam tong hoa don', kieu_giam: 'Phan tram', pham_vi: 'Ca hoa don',
    doi_tuong: 'Moi khach', cach_ma: 'Khong can ma', cong_don: 1, uu_tien: 10, bat: 0,
    dong_mon: [], dong_bac: []
  };
  kmSua = JSON.parse(JSON.stringify(km));

  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  function ve() {
    var k = kmSua;
    var c = kmNhanCach(k.cach_thuc);
    /* Bam mot chip la ve lai ca to giay, ma to giay moi bat dau tu dong
       dau nen man hinh nhay vot len tren - anh Viet bao "bam chip nao man
       hinh cung bi cuon len" (12/08/2026). Nho cho dang doc truoc khi ve,
       ve xong dat lai. */
    var cuonCu = 0;
    var oCuonCu = box.querySelector('#kmCuon');
    if (oCuonCu) cuonCu = oCuonCu.scrollTop;
    var html = '<div class="shh"><b>' + (ma ? 'Sửa chương trình' : 'Chương trình mới') + '</b><div class="x">&times;</div></div>' +
      '<div id="kmCuon" style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 90px);max-height:78vh;overflow:auto">';

    if (ma) html += '<div style="font-size:12px;color:#98a2b3;margin-bottom:10px">Mã ' + h(k.name) + (k.da_dung ? ' · đã dùng ' + k.da_dung + ' lượt' : '') + '</div>';

    html += kmO('TÊN CHƯƠNG TRÌNH', 'kmTen', k.ten, 'Ví dụ: Giảm 15% cho khách VAGABONDER');

    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:14px 0 6px">CÁCH THỨC</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:6px">' +
      KM_CACH.map(function (x) { return posChipNut('data-kmc="' + x.k + '"', x.ic + ' ' + x.nhan, k.cach_thuc === x.k); }).join('') + '</div>' +
      '<div style="font-size:11.5px;color:#98a2b3;margin-bottom:12px;line-height:1.5">' + c.mo + '</div>';

    /* --- muc uu dai theo tung cach thuc --- */
    if (k.cach_thuc === 'Dong gia') {
      html += kmO('GIÁ ĐỒNG (đ)', 'kmGiaDong', k.gia_dong, '39000', 'number', 'Mọi món trong phạm vi kéo về mức giá này');
    } else if (k.cach_thuc === 'Giam luy ke') {
      html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:6px 0">CÁC BẬC</div>';
      (k.dong_bac || []).forEach(function (b, i) {
        html += '<div style="display:flex;gap:6px;align-items:center;margin-bottom:7px">' +
          '<input class="tin" data-bac="' + i + '" data-f="tu_tien" type="number" value="' + (b.tu_tien || '') + '" placeholder="từ (đ)" style="flex:2">' +
          '<input class="tin" data-bac="' + i + '" data-f="gia_tri" type="number" value="' + (b.gia_tri || '') + '" placeholder="giảm" style="flex:1">' +
          posChipNut('data-backi="' + i + '"', b.kieu_giam === 'So tien' ? 'đ' : '%', false) +
          posChipNut('data-bacxoa="' + i + '"', '×', false, true) + '</div>';
      });
      html += '<div style="margin-bottom:12px">' + posChipNut('data-bacthem="1"', '+ Thêm bậc', false) + '</div>';
    } else if (k.cach_thuc !== 'Mua X tang Y' && k.cach_thuc !== 'Tang mon') {
      html += '<div style="display:flex;gap:7px;margin-bottom:8px">' +
        posChipNut('data-kmkieu="Phan tram"', 'Giảm %', k.kieu_giam !== 'So tien') +
        posChipNut('data-kmkieu="So tien"', 'Giảm số tiền', k.kieu_giam === 'So tien') + '</div>' +
        kmO(k.kieu_giam === 'So tien' ? 'GIẢM (đ)' : 'GIẢM (%)', 'kmGiaTri', k.gia_tri, k.kieu_giam === 'So tien' ? '20000' : '10', 'number');
    }

    /* --- pham vi mon --- */
    if (k.cach_thuc === 'Giam tong hoa don' || k.cach_thuc === 'Giam gia mon' || k.cach_thuc === 'Dong gia') {
      html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">PHẠM VI MÓN</div>' +
        '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:8px">' +
        posChipNut('data-kmpv="Ca hoa don"', 'Cả hoá đơn', k.pham_vi === 'Ca hoa don') +
        posChipNut('data-kmpv="Nhom mon chi dinh"', 'Nhóm món', k.pham_vi === 'Nhom mon chi dinh') +
        posChipNut('data-kmpv="Mon chi dinh"', 'Món chỉ định', k.pham_vi === 'Mon chi dinh') + '</div>';
      if (k.pham_vi === 'Nhom mon chi dinh') {
        html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">NHÓM MÓN ÁP DỤNG</div>' +
          kmChipNhieu('data-kmnmon', (kmDm && kmDm.nhom_mon) || [], k.nhom_mon);
      }
    }

    /* --- danh sach mon --- */
    if (k.cach_thuc !== 'Giam tong hoa don' && k.cach_thuc !== 'Giam luy ke') {
      html += kmHtmlDongMon(k);
    } else if (k.pham_vi === 'Mon chi dinh') {
      html += kmHtmlDongMon(k);
    }

    /* --- dieu kien --- */
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:14px 0 6px">ĐIỀU KIỆN</div>' +
      kmO('HOÁ ĐƠN TỪ (đ, để trống là không cần)', 'kmHdTt', k.hd_toi_thieu, '0', 'number') +
      kmO('SỐ MÓN TỐI THIỂU', 'kmSlTt', k.sl_toi_thieu, '0', 'number');

    /* --- thoi gian --- */
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:14px 0 6px">THỜI GIAN</div>' +
      '<div style="display:flex;gap:8px">' +
      '<div style="flex:1">' + kmO('TỪ NGÀY', 'kmTuNgay', k.tu_ngay, '', 'date') + '</div>' +
      '<div style="flex:1">' + kmO('ĐẾN NGÀY', 'kmDenNgay', k.den_ngay, '', 'date') + '</div></div>' +
      '<div style="display:flex;gap:8px">' +
      '<div style="flex:1">' + kmO('GIỜ TỪ', 'kmGioTu', (k.gio_tu || '').toString().slice(0, 5), '', 'time') + '</div>' +
      '<div style="flex:1">' + kmO('GIỜ ĐẾN', 'kmGioDen', (k.gio_den || '').toString().slice(0, 5), '', 'time') + '</div></div>' +
      '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:4px 0 6px">THỨ TRONG TUẦN <span style="font-weight:400;color:#98a2b3">(không chọn = mọi ngày)</span></div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px">' +
      [['thu_2', 'T2'], ['thu_3', 'T3'], ['thu_4', 'T4'], ['thu_5', 'T5'], ['thu_6', 'T6'], ['thu_7', 'T7'], ['thu_cn', 'CN']]
        .map(function (t) { return posChipNut('data-kmthu="' + t[0] + '"', t[1], !!k[t[0]]); }).join('') + '</div>';

    /* --- kenh va quay --- */
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">KÊNH BÁN</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px">' +
      kmDsKenh().map(function (n) {
        return posChipNut('data-kmkenh="' + h(n) + '"', h(n), (k.kenh || '').split('\n').indexOf(n) >= 0);
      }).join('') + '</div>' +
      '<div style="font-size:11.5px;color:#98a2b3;margin-bottom:10px">Không chọn kênh nào = áp dụng mọi kênh.</div>' +
      '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">QUẦY</div>' +
      kmChipNhieu('data-kmquay', (kmDm && kmDm.quay) || KM_QUAY, k.quay) +
      '<div style="font-size:11.5px;color:#98a2b3;margin:-6px 0 10px">Không chọn quầy nào = áp dụng cả ba điểm bán.</div>';

    /* --- doi tuong --- */
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">ĐỐI TƯỢNG KHÁCH</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:8px">' +
      [['Moi khach', 'Mọi khách'], ['Theo hang khach', 'Theo hạng khách'], ['Theo nhom khach', 'Theo nhóm khách'],
       ['Khach chi dinh', 'Khách chỉ định'], ['Nhan vien', 'Nhân viên']]
        .map(function (d) { return posChipNut('data-kmdt="' + d[0] + '"', d[1], k.doi_tuong === d[0]); }).join('') + '</div>';
    if (k.doi_tuong === 'Theo hang khach') {
      html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">HẠNG ÁP DỤNG</div>' +
        kmChipNhieu('data-kmhang', (kmDm && kmDm.hang) || [], k.hang_khach);
    }
    if (k.doi_tuong === 'Theo nhom khach') {
      html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">NHÓM KHÁCH ÁP DỤNG</div>' +
        kmChipNhieu('data-kmnkh', (kmDm && kmDm.nhom_khach) || [], k.nhom_khach);
    }
    if (k.doi_tuong === 'Nhan vien') html += '<div style="font-size:11.5px;color:#98a2b3;margin-bottom:10px;line-height:1.5">Máy nhận diện qua số điện thoại trên hồ sơ nhân sự, không phải nhân viên tự khai.</div>';

    /* --- ma voucher --- */
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:14px 0 6px">CÁCH PHÁT MÃ</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:8px">' +
      [['Khong can ma', 'Không cần mã'], ['Ma co dinh', 'Mã cố định'], ['Ma dung mot lan', 'Mã dùng một lần']]
        .map(function (d) { return posChipNut('data-kmcm="' + d[0] + '"', d[1], k.cach_ma === d[0]); }).join('') + '</div>';
    if (k.cach_ma === 'Ma co dinh') html += kmO('MÃ CỐ ĐỊNH', 'kmMaCd', k.ma_co_dinh, 'VAGABOND10', 'text', 'Cashier gõ mã này khi tính tiền. Dùng bao nhiêu lần cũng được, chỉ bị chặn bởi hạn mức bên dưới.');
    if (k.cach_ma === 'Ma dung mot lan') html += kmO('HẠN DÙNG MẶC ĐỊNH CỦA MÃ', 'kmHanMa', k.han_ma, '', 'date', 'Lưu chương trình xong, qua thẻ <b>Lô mã</b> để xuất mã và gửi qua email.');

    /* --- chong gian lan --- */
    html += '<div style="font-size:12.5px;color:#b3261e;font-weight:700;margin:14px 0 6px">CHỐNG GIAN LẬN</div>' +
      '<div style="background:#fff7ed;border:1.5px solid #fed7aa;border-radius:9px;padding:11px 13px;margin-bottom:10px;font-size:12px;color:#9a3412;line-height:1.6">' +
      'Để 0 là không giới hạn. Nên đặt ít nhất trần giảm hoặc bắt buộc OTP với chương trình giảm sâu - nếu không, một thu ngân có thể bấm cả trăm lần trong ca cho người quen.</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:10px">' +
      posChipNut('data-kmotp="1"', '🔐 Bắt buộc OTP quản lý', !!k.can_otp) +
      posChipNut('data-kmcd="1"', '➕ Cho cộng dồn chương trình khác', !!k.cong_don) + '</div>' +
      kmO('TRẦN GIẢM MỖI HOÁ ĐƠN (đ)', 'kmTran', k.giam_toi_da, '0', 'number') +
      kmO('TỐI ĐA MỖI NGÀY (toàn hệ thống)', 'kmLanNgay', k.lan_moi_ngay, '0', 'number') +
      kmO('TỐI ĐA MỖI THU NGÂN MỖI NGÀY', 'kmLanCa', k.lan_moi_ca, '0', 'number') +
      kmO('TỐI ĐA MỖI SỐ ĐIỆN THOẠI KHÁCH', 'kmLanKhach', k.lan_moi_khach, '0', 'number') +
      kmO('TỔNG SỐ LƯỢT CẢ CHƯƠNG TRÌNH', 'kmTongLan', k.so_lan_toi_da, '0', 'number') +
      kmOta('GHI CHÚ', 'kmGhiChu', k.ghi_chu, '');

    html += '<div style="display:flex;gap:7px;margin:8px 0 4px">' +
      posChipNut('data-kmbatct="1"', k.bat ? '● Chương trình đang bật' : '○ Chương trình đang tắt', !!k.bat) + '</div>';

    html += '</div><div style="position:sticky;bottom:0;background:#fff;border-top:1px solid #eef0f4;padding:11px 14px calc(env(safe-area-inset-bottom,0px) + 11px);display:flex;gap:8px">' +
      '<button class="btn" id="kmLuu" style="flex:1">Lưu chương trình</button></div>';
    box.innerHTML = html;
    var oCuonMoi = box.querySelector('#kmCuon');
    if (oCuonMoi && cuonCu) oCuonMoi.scrollTop = cuonCu;
    noiSuKien();
  }

  function thu(f) {
    var k = kmSua;
    k.ten = kmV('kmTen') || k.ten;
    if (document.getElementById('kmGiaTri')) k.gia_tri = kmN('kmGiaTri');
    if (document.getElementById('kmGiaDong')) k.gia_dong = kmN('kmGiaDong');
    if (document.getElementById('kmNhomMon')) k.nhom_mon = kmV('kmNhomMon');
    if (document.getElementById('kmHdTt')) k.hd_toi_thieu = kmN('kmHdTt');
    if (document.getElementById('kmSlTt')) k.sl_toi_thieu = kmN('kmSlTt');
    if (document.getElementById('kmTuNgay')) k.tu_ngay = kmV('kmTuNgay');
    if (document.getElementById('kmDenNgay')) k.den_ngay = kmV('kmDenNgay');
    if (document.getElementById('kmGioTu')) k.gio_tu = kmV('kmGioTu');
    if (document.getElementById('kmGioDen')) k.gio_den = kmV('kmGioDen');
    if (document.getElementById('kmHang')) k.hang_khach = kmV('kmHang');
    if (document.getElementById('kmNhomKh')) k.nhom_khach = kmV('kmNhomKh');
    if (document.getElementById('kmMaCd')) k.ma_co_dinh = kmV('kmMaCd');
    if (document.getElementById('kmHanMa')) k.han_ma = kmV('kmHanMa');
    if (document.getElementById('kmTran')) k.giam_toi_da = kmN('kmTran');
    if (document.getElementById('kmLanNgay')) k.lan_moi_ngay = kmN('kmLanNgay');
    if (document.getElementById('kmLanCa')) k.lan_moi_ca = kmN('kmLanCa');
    if (document.getElementById('kmLanKhach')) k.lan_moi_khach = kmN('kmLanKhach');
    if (document.getElementById('kmTongLan')) k.so_lan_toi_da = kmN('kmTongLan');
    if (document.getElementById('kmGhiChu')) k.ghi_chu = kmV('kmGhiChu');
    box.querySelectorAll('[data-bac]').forEach(function (o) {
      var i = parseInt(o.getAttribute('data-bac'), 10);
      if (kmSua.dong_bac[i]) kmSua.dong_bac[i][o.getAttribute('data-f')] = parseFloat(o.value) || 0;
    });
  }

  function bat(sel, fn) {
    box.querySelectorAll(sel).forEach(function (o) {
      o.onclick = function () { thu(); fn(o); ve(); };
    });
  }

  function noiSuKien() {
    box.querySelector('.x').onclick = function () { ov.remove(); };
    bat('[data-kmc]', function (o) { kmSua.cach_thuc = o.getAttribute('data-kmc'); });
    bat('[data-kmkieu]', function (o) { kmSua.kieu_giam = o.getAttribute('data-kmkieu'); });
    bat('[data-kmpv]', function (o) { kmSua.pham_vi = o.getAttribute('data-kmpv'); });
    bat('[data-kmdt]', function (o) { kmSua.doi_tuong = o.getAttribute('data-kmdt'); });
    bat('[data-kmcm]', function (o) { kmSua.cach_ma = o.getAttribute('data-kmcm'); });
    bat('[data-kmthu]', function (o) { var t = o.getAttribute('data-kmthu'); kmSua[t] = kmSua[t] ? 0 : 1; });
    bat('[data-kmotp]', function () { kmSua.can_otp = kmSua.can_otp ? 0 : 1; });
    bat('[data-kmcd]', function () { kmSua.cong_don = kmSua.cong_don ? 0 : 1; });
    bat('[data-kmbatct]', function () { kmSua.bat = kmSua.bat ? 0 : 1; });
    bat('[data-kmkenh]', function (o) {
      var n = o.getAttribute('data-kmkenh');
      var ds = (kmSua.kenh || '').split('\n').filter(function (x) { return x.trim(); });
      var i = ds.indexOf(n); if (i >= 0) ds.splice(i, 1); else ds.push(n);
      kmSua.kenh = ds.join('\n');
    });
    bat('[data-kmquay]', function (o) { kmSua.quay = kmDoiDong(kmSua.quay, o.getAttribute('data-kmquay')); });
    bat('[data-kmhang]', function (o) { kmSua.hang_khach = kmDoiDong(kmSua.hang_khach, o.getAttribute('data-kmhang')); });
    bat('[data-kmnkh]', function (o) { kmSua.nhom_khach = kmDoiDong(kmSua.nhom_khach, o.getAttribute('data-kmnkh')); });
    bat('[data-kmnmon]', function (o) { kmSua.nhom_mon = kmDoiDong(kmSua.nhom_mon, o.getAttribute('data-kmnmon')); });
    bat('[data-bacthem]', function () { kmSua.dong_bac.push({ tu_tien: 0, kieu_giam: 'Phan tram', gia_tri: 0 }); });
    bat('[data-bacxoa]', function (o) { kmSua.dong_bac.splice(parseInt(o.getAttribute('data-bacxoa'), 10), 1); });
    bat('[data-backi]', function (o) {
      var i = parseInt(o.getAttribute('data-backi'), 10);
      kmSua.dong_bac[i].kieu_giam = kmSua.dong_bac[i].kieu_giam === 'So tien' ? 'Phan tram' : 'So tien';
    });
    bat('[data-monxoa]', function (o) { kmSua.dong_mon.splice(parseInt(o.getAttribute('data-monxoa'), 10), 1); });
    bat('[data-monvt]', function (o) {
      var i = parseInt(o.getAttribute('data-monvt'), 10);
      kmSua.dong_mon[i].vai_tro = kmSua.dong_mon[i].vai_tro === 'Dieu kien' ? 'Uu dai' : 'Dieu kien';
    });
    box.querySelectorAll('[data-monsl]').forEach(function (o) {
      o.onchange = function () {
        var i = parseInt(o.getAttribute('data-monsl'), 10);
        if (kmSua.dong_mon[i]) kmSua.dong_mon[i].so_luong = parseFloat(o.value) || 1;
      };
    });
    var tm = box.querySelector('[data-monthem]');
    if (tm) tm.onclick = function () {
      thu();
      kmChonMon(function (it) {
        var canDk = (kmSua.cach_thuc === 'Mua A giam B' || kmSua.cach_thuc === 'Mua X tang Y');
        var daCoDk = (kmSua.dong_mon || []).some(function (m) { return m.vai_tro === 'Dieu kien'; });
        kmSua.dong_mon.push({
          vai_tro: (canDk && !daCoDk) ? 'Dieu kien' : 'Uu dai',
          item_code: it.value, ten_mon: it.label, so_luong: 1,
          kieu_giam: (kmSua.cach_thuc === 'Mua X tang Y' || kmSua.cach_thuc === 'Tang mon') ? 'Tang mien phi' : '',
          gia_tri: 0
        });
        return 1;
      }, function () { ve(); });
    };
    box.querySelector('#kmLuu').onclick = async function () {
      thu();
      if (!kmSua.ten) { toast('Chương trình chưa có tên.'); return; }
      var nut = box.querySelector('#kmLuu'); nut.disabled = true; nut.textContent = 'Đang lưu...';
      try {
        await api('vagabond.khuyen_mai.luu_ctkm', { du_lieu: JSON.stringify(kmSua), ma: ma || '' });
        ov.remove();
        toast('Đã lưu chương trình');
        go(scrKhuyenMai, true);
      } catch (e) {
        nut.disabled = false; nut.textContent = 'Lưu chương trình';
        toast((e && e.message) || 'Không lưu được');
      }
    };
  }

  ve();
  ov.appendChild(box);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  document.body.appendChild(ov);
}

function kmHtmlDongMon(k) {
  var canDk = (k.cach_thuc === 'Mua A giam B' || k.cach_thuc === 'Mua X tang Y');
  var html = '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:14px 0 6px">MÓN' +
    (canDk ? ' <span style="font-weight:400;color:#98a2b3">(bấm chip vai trò để đổi Điều kiện ↔ Ưu đãi)</span>' : '') + '</div>';
  if (!(k.dong_mon || []).length) {
    html += '<div style="font-size:12.5px;color:#98a2b3;padding:8px 0">' +
      (canDk ? 'Chưa khai món nào. Cần ít nhất một món <b>Điều kiện</b> (khách phải mua) và một món <b>Ưu đãi</b>.'
             : 'Chưa khai món nào.') + '</div>';
  }
  (k.dong_mon || []).forEach(function (m, i) {
    html += '<div style="display:flex;gap:6px;align-items:center;margin-bottom:7px">' +
      (canDk || k.cach_thuc === 'Tang mon'
        ? posChipNut('data-monvt="' + i + '"', m.vai_tro === 'Dieu kien' ? 'Điều kiện' : 'Ưu đãi', m.vai_tro === 'Dieu kien') : '') +
      '<div style="flex:1;min-width:0;font-size:13.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + h(m.ten_mon || m.item_code) + '</div>' +
      '<input class="tin" data-monsl="' + i + '" type="number" value="' + (m.so_luong || 1) + '" style="width:64px;flex:none;text-align:center">' +
      posChipNut('data-monxoa="' + i + '"', '×', false, true) + '</div>';
  });
  html += '<div style="margin-bottom:8px">' + posChipNut('data-monthem="1"', '+ Thêm món', false) + '</div>';
  return html;
}

/* Mo bang chon mon dung chung cua quay. Dung lai dsItemsCache de khong
   phai tai lai danh muc mon lan nua. */
async function kmChonMon(onPick, onDong) {
  if (!dsItemsCache) {
    busy(true);
    try {
      dsItemsCache = await getList('Item', {
        filters: { is_sales_item: 1, disabled: 0, item_group: ['not in', ['Nguyên vật liệu Thô', 'Bán thành phẩm Bánh', 'Bán thành phẩm Nước', 'Nhân bán thành phẩm', 'Công cụ Dụng cụ', 'Bao bì', 'Văn phòng phẩm', 'Tài sản Cố định']] },
        fields: ['name', 'item_name', 'image', 'standard_rate', 'item_group'],
        limit_page_length: 0, order_by: 'item_name'
      });
    } catch (e) { busy(false); return toast('Không tải được danh mục món'); }
    busy(false);
  }
  posSheetMon(dsItemsCache.map(function (x) {
    return {
      value: x.name, label: x.item_name, icon: '🎂', img: x.image || '',
      gia: x.standard_rate || 0, nhom: x.item_group || '',
      phu: (x.standard_rate ? money(x.standard_rate) + ' đ' : 'chưa có giá') + ' · ' + x.name,
      tim: x.name
    };
  }), onPick, onDong);
}

function kmDsKenh() {
  return ['GrabFood', 'BeFood', 'GreenSM Food', 'ShopeeFood', 'Khách sỉ',
    'Tại chỗ - Trần Cao Vân', 'Tại chỗ - Nguyễn Văn Trỗi',
    'Mang về - Trần Cao Vân', 'Mang về - Nguyễn Văn Trỗi'];
}

/* ---------- Sheet cau hinh combo ---------- */
async function kmSheetCombo(ma) {
  var cb = null;
  if (ma) {
    cb = (kmData.cb || []).filter(function (x) { return x.name === ma; })[0];
    if (cb) cb = JSON.parse(JSON.stringify(cb));
  }
  cb = cb || { kieu: 'Gia tron goi', bat: 0, uu_tien: 10, dong: [], nhom: [], gioi_han_bill: 0 };
  cb.nhom = cb.nhom || [];
  cb.dong = cb.dong || [];
  var s = cb;

  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';

  /* Nhom mon cho khach chon. Moi nhom la mot dong trong bang s.nhom, co
     ten, chon toi thieu va toi da. Dong mon gan vao nhom bang TEN nhom;
     dong khong ghi ten nhom la mon bat buoc, luon vao bill. */
  function cbMonCuaNhom(ten) {
    return (s.dong || []).filter(function (d) { return String(d.nhom || '').trim() === ten; });
  }
  function cbNhom() {
    var ra = {};
    (s.nhom || []).forEach(function (g) {
      var ten = String(g.ten || '').trim();
      if (!ten) return;
      var ds = cbMonCuaNhom(ten);
      var toiDa = parseInt(g.chon_toi_da, 10) || 1;
      var toiThieu = parseInt(g.chon_toi_thieu, 10);
      if (isNaN(toiThieu) || toiThieu < 0) toiThieu = 0;
      ra[ten] = { toi_thieu: Math.min(toiThieu, toiDa), toi_da: toiDa, dong: ds, g: g };
    });
    return ra;
  }
  /* Tong gia le cua mot bo. datNhat = khach lay het suat toi da va toan mon
     dat nhat; nguoc lai la chi lay dung so toi thieu va toan mon re nhat.
     Phai khop y het cach may chu tinh. */
  function tongGoc(datNhat) {
    var t = 0;
    (s.dong || []).forEach(function (d) {
      if (!String(d.nhom || '').trim()) t += (d.gia_goc || 0) * (d.so_luong || 0);
    });
    var nh = cbNhom();
    Object.keys(nh).forEach(function (k) {
      var gia = nh[k].dong.map(function (d) { return (d.gia_goc || 0) * (d.so_luong || 0); });
      gia.sort(function (a, b) { return datNhat ? b - a : a - b; });
      var so = datNhat ? nh[k].toi_da : nh[k].toi_thieu;
      gia.slice(0, so).forEach(function (v) { t += v; });
    });
    return t;
  }
  function tinhTietKiem() {
    /* Tinh tren phuong an RE NHAT: bang gia dan cho khach ghi "tiet kiem X"
       thi X phai la con so khach luon duoc, chon kieu gi cung khong tut. */
    var g = tongGoc(false);
    if (s.kieu === 'Gia tron goi') return Math.max(0, g - (s.gia_combo || 0));
    if (s.kieu === 'Giam phan tram') return g * (s.gia_tri || 0) / 100;
    return Math.min(g, s.gia_tri || 0);
  }

  /* Mot dong mon trong bang cau hinh. Dung chung cho mon co san va mon
     nam trong nhom, chi khac cho co nut go khoi nhom hay khong. */
  function cbDongMon(i, tenNhom) {
    var d = (s.dong || [])[i];
    if (!d) return '';
    return '<div style="display:flex;gap:6px;align-items:center;margin-bottom:7px">' +
      '<div style="flex:1;min-width:0"><div style="font-size:13.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + h(d.ten_mon || d.item_code) + '</div>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + money(d.gia_goc) + 'đ/phần</div></div>' +
      '<input class="tin" data-cbsl="' + i + '" type="number" value="' + (d.so_luong || 1) + '" style="width:58px;flex:none;text-align:center;margin:0">' +
      '<input class="tin" data-cbg="' + i + '" type="number" value="' + (d.gia_goc || 0) + '" style="width:88px;flex:none;text-align:right;margin:0">' +
      posChipNut('data-cbxoa="' + i + '"', '×', false, true) + '</div>';
  }

  function ve() {
    var g = tongGoc(true), gMin = tongGoc(false), tk = tinhTietKiem();
    var cuonCu = 0;
    var oCuonCu = box.querySelector('#cbCuon');
    if (oCuonCu) cuonCu = oCuonCu.scrollTop;
    var html = '<div class="shh"><b>' + (ma ? 'Sửa combo' : 'Combo mới') + '</b><div class="x">&times;</div></div>' +
      '<div id="cbCuon" style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 90px);max-height:78vh;overflow:auto">' +
      '<div style="background:#f0fdfa;border:1.5px solid #7fe5f6;border-radius:9px;padding:11px 13px;margin-bottom:12px;font-size:12px;color:#0b7c93;line-height:1.6">' +
      'Khi tính tiền, cashier bấm combo thì máy <b>rã ra thành từng món thành phần</b> rồi đặt một dòng giảm giá bên dưới. Bill in ra chỉ thấy tên món thật, không in mã combo.</div>' +
      kmO('TÊN COMBO', 'cbTen', s.ten, 'Ví dụ: Combo sáng cà phê + bánh mì');

    /* ----- Mon co san: luon vao bill ----- */
    var monBB = [];
    (s.dong || []).forEach(function (d, i) { if (!String(d.nhom || '').trim()) monBB.push(i); });
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">MÓN CÓ SẴN TRONG COMBO' +
      ' <span style="font-weight:400;color:#98a2b3">(luôn vào bill)</span></div>';
    if (!monBB.length) html += '<div style="font-size:12.5px;color:#98a2b3;padding:6px 0">Chưa có món nào. Combo có thể chỉ gồm các nhóm cho khách chọn.</div>';
    monBB.forEach(function (i) { html += cbDongMon(i, ''); });
    html += '<div style="margin-bottom:14px">' + posChipNut('data-cbthem="1"', '+ Thêm món có sẵn', false) + '</div>';

    /* ----- Nhom mon cho khach chon ----- */
    var nhBang = cbNhom();
    var tenNh = Object.keys(nhBang);
    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">NHÓM MÓN CHO KHÁCH CHỌN</div>';
    if (!tenNh.length) {
      html += '<div style="background:#f0fdfa;border:1.5px solid #7fe5f6;border-radius:9px;padding:10px 12px;margin-bottom:10px;font-size:12px;color:#0b7c93;line-height:1.6">' +
        'Bấm <b>Tạo nhóm món</b> để cho khách chọn, ví dụ một nhóm "Món nước" chọn 1 trong 2, một nhóm "Bánh" chọn 1 trong 4. ' +
        'Combo có nhóm thì thu ngân bấm combo sẽ hiện hộp chọn món trước khi vào bill.</div>';
    }
    (s.nhom || []).forEach(function (g, gi) {
      var ten = String(g.ten || '').trim();
      var ds = ten ? cbMonCuaNhom(ten) : [];
      var toiDa = parseInt(g.chon_toi_da, 10) || 1;
      var toiThieu = parseInt(g.chon_toi_thieu, 10); if (isNaN(toiThieu)) toiThieu = 0;
      html += '<div style="border:1.5px solid #7fe5f6;background:#f7feff;border-radius:12px;padding:10px 11px;margin-bottom:10px">' +
        '<div style="display:flex;gap:6px;align-items:center;margin-bottom:8px">' +
        '<input class="tin" data-cbnten="' + gi + '" value="' + h(ten) + '" placeholder="Tên nhóm, ví dụ Món nước" style="flex:1;margin:0;font-weight:700">' +
        posChipNut('data-cbnxoa="' + gi + '"', '×', false, true) + '</div>' +
        '<div style="display:flex;gap:8px;margin-bottom:8px">' +
        '<div style="flex:1"><div style="font-size:11.5px;color:#6b7280;margin-bottom:3px">Chọn tối thiểu</div>' +
        '<input class="tin" data-cbntt="' + gi + '" type="number" min="0" value="' + toiThieu + '" style="width:100%;margin:0;text-align:center"></div>' +
        '<div style="flex:1"><div style="font-size:11.5px;color:#6b7280;margin-bottom:3px">Tối đa</div>' +
        '<input class="tin" data-cbntd="' + gi + '" type="number" min="1" value="' + toiDa + '" style="width:100%;margin:0;text-align:center"></div>' +
        '</div>' +
        '<div style="font-size:11.5px;color:#0b7c93;margin-bottom:8px;line-height:1.5">' +
        (ten
          ? (toiThieu === toiDa
            ? 'Khách chọn đúng <b>' + toiDa + '</b> món trong ' + ds.length + ' món dưới đây.'
            : 'Khách chọn từ <b>' + toiThieu + '</b> đến <b>' + toiDa + '</b> món trong ' + ds.length + ' món dưới đây.')
          : '<span style="color:#b45309">Đặt tên nhóm trước rồi mới thêm món vào được.</span>') +
        '</div>';
      ds.forEach(function (d) { html += cbDongMon(s.dong.indexOf(d), ten); });
      if (ten && !ds.length) html += '<div style="font-size:12.5px;color:#b45309;padding:4px 0 8px">Nhóm chưa có món nào.</div>';
      html += '<div>' + posChipNut('data-cbnthem="' + gi + '"', '+ Thêm món vào nhóm', false) + '</div>' +
        '</div>';
    });
    html += '<div style="margin-bottom:14px">' + posChipNut('data-cbntao="1"', '➕ Tạo nhóm món', false) + '</div>';

    /* Mon dang ghi ten nhom ma khong con nhom nao ten do: bao ngay o day,
       khong de may chu chan luc bam Luu. */
    var moCoi = [];
    (s.dong || []).forEach(function (d, i) {
      var n = String(d.nhom || '').trim();
      if (n && !nhBang[n]) moCoi.push(i);
    });
    if (moCoi.length) {
      html += '<div style="background:#fef2f2;border:1.5px solid #fecaca;border-radius:9px;padding:10px 12px;margin-bottom:12px;font-size:12.5px;color:#991b1b;line-height:1.6">' +
        moCoi.length + ' món đang ghi nhóm không còn tồn tại nên sẽ không bao giờ được chọn:<br>' +
        moCoi.map(function (i) { return '· ' + h(s.dong[i].ten_mon || s.dong[i].item_code) + ' (nhóm "' + h(s.dong[i].nhom) + '")'; }).join('<br>') +
        '<div style="margin-top:8px">' + posChipNut('data-cbmocoi="1"', 'Gỡ tên nhóm, cho thành món có sẵn', false) + '</div></div>';
      moCoi.forEach(function (i) { html += cbDongMon(i, ''); });
    }

    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">GIÁ COMBO</div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:8px">' +
      [['Gia tron goi', 'Giá trọn gói'], ['Giam phan tram', 'Giảm %'], ['Giam so tien', 'Giảm số tiền']]
        .map(function (d) { return posChipNut('data-cbkieu="' + d[0] + '"', d[1], s.kieu === d[0]); }).join('') + '</div>' +
      (s.kieu === 'Gia tron goi'
        ? kmO('GIÁ BÁN CỦA COMBO (đ)', 'cbGia', s.gia_combo, '', 'number')
        : kmO(s.kieu === 'Giam phan tram' ? 'GIẢM (%)' : 'GIẢM (đ)', 'cbGiaTri', s.gia_tri, '', 'number'));

    html += '<div style="background:#fef3c7;border:1.5px solid #fcd34d;border-radius:9px;padding:11px 13px;margin-bottom:12px;font-size:13px;color:#92400e">' +
      (gMin === g
        ? 'Tổng giá lẻ <b>' + money(g) + 'đ</b> → khách trả <b>' + money(g - tk) + 'đ</b>, tiết kiệm <b>' + money(tk) + 'đ</b>' +
          (g > 0 ? ' (' + num(Math.round(tk / g * 1000) / 10) + '%)' : '')
        : 'Khách chọn rẻ nhất: giá lẻ <b>' + money(gMin) + 'đ</b>, tiết kiệm <b>' + money(tk) + 'đ</b>.<br>' +
          'Khách chọn đắt nhất: giá lẻ <b>' + money(g) + 'đ</b>. Máy tính tiền giảm theo đúng món khách chọn.') +
      '</div>';

    html += '<div style="display:flex;gap:8px">' +
      '<div style="flex:1">' + kmO('TỪ NGÀY', 'cbTuNgay', s.tu_ngay, '', 'date') + '</div>' +
      '<div style="flex:1">' + kmO('ĐẾN NGÀY', 'cbDenNgay', s.den_ngay, '', 'date') + '</div></div>';

    html += '<div style="font-size:12.5px;color:#6b7280;font-weight:700;margin:8px 0 6px">QUẦY</div>' +
      kmChipNhieu('data-cbquay', (kmDm && kmDm.quay) || KM_QUAY, s.quay) +
      '<div style="font-size:11.5px;color:#98a2b3;margin:-6px 0 10px">Không chọn quầy nào = bán ở cả ba điểm.</div>';

    html += '<div style="font-size:12.5px;color:#b3261e;font-weight:700;margin:8px 0 6px">CHỐNG GIAN LẬN</div>' +
      '<div style="display:flex;gap:7px;margin-bottom:10px">' +
      posChipNut('data-cbotp="1"', '🔐 Bắt buộc OTP quản lý', !!s.can_otp) + '</div>' +
      kmO('TỐI ĐA MỖI HOÁ ĐƠN (0 = không giới hạn)', 'cbGhBill', s.gioi_han_bill, '0', 'number') +
      kmO('TỐI ĐA MỖI NGÀY', 'cbLanNgay', s.lan_moi_ngay, '0', 'number') +
      kmOta('MÔ TẢ', 'cbMoTa', s.mo_ta, '');

    html += '<div style="display:flex;gap:7px;margin:8px 0 4px">' +
      posChipNut('data-cbbat="1"', s.bat ? '● Combo đang bật' : '○ Combo đang tắt', !!s.bat) + '</div>';

    html += '</div><div style="position:sticky;bottom:0;background:#fff;border-top:1px solid #eef0f4;padding:11px 14px calc(env(safe-area-inset-bottom,0px) + 11px)">' +
      '<button class="btn" id="cbLuu" style="width:100%">Lưu combo</button></div>';
    box.innerHTML = html;
    var oCuonMoi = box.querySelector('#cbCuon');
    if (oCuonMoi && cuonCu) oCuonMoi.scrollTop = cuonCu;
    noi();
  }

  function thu() {
    s.ten = kmV('cbTen') || s.ten;
    if (document.getElementById('cbGia')) s.gia_combo = kmN('cbGia');
    if (document.getElementById('cbGiaTri')) s.gia_tri = kmN('cbGiaTri');
    if (document.getElementById('cbTuNgay')) s.tu_ngay = kmV('cbTuNgay');
    if (document.getElementById('cbDenNgay')) s.den_ngay = kmV('cbDenNgay');
    if (document.getElementById('cbGhBill')) s.gioi_han_bill = kmN('cbGhBill');
    if (document.getElementById('cbLanNgay')) s.lan_moi_ngay = kmN('cbLanNgay');
    if (document.getElementById('cbMoTa')) s.mo_ta = kmV('cbMoTa');
    box.querySelectorAll('[data-cbsl]').forEach(function (o) {
      var i = parseInt(o.getAttribute('data-cbsl'), 10);
      if (s.dong[i]) s.dong[i].so_luong = parseFloat(o.value) || 1;
    });
    box.querySelectorAll('[data-cbg]').forEach(function (o) {
      var i = parseInt(o.getAttribute('data-cbg'), 10);
      if (s.dong[i]) s.dong[i].gia_goc = parseFloat(o.value) || 0;
    });
    /* Doi ten nhom thi phai keo theo cac dong mon dang tro toi ten cu,
       khong thi mon bi mo coi ngay khi go xong chu cai dau tien. */
    box.querySelectorAll('[data-cbnten]').forEach(function (o) {
      var gi = parseInt(o.getAttribute('data-cbnten'), 10);
      var g = (s.nhom || [])[gi];
      if (!g) return;
      var cu = String(g.ten || '').trim();
      var moi = String(o.value || '').trim();
      if (moi === cu) return;
      g.ten = moi;
      (s.dong || []).forEach(function (d) { if (String(d.nhom || '').trim() === cu) d.nhom = moi; });
    });
    box.querySelectorAll('[data-cbntt]').forEach(function (o) {
      var gi = parseInt(o.getAttribute('data-cbntt'), 10);
      if (s.nhom[gi]) s.nhom[gi].chon_toi_thieu = Math.max(0, parseInt(o.value, 10) || 0);
    });
    box.querySelectorAll('[data-cbntd]').forEach(function (o) {
      var gi = parseInt(o.getAttribute('data-cbntd'), 10);
      if (s.nhom[gi]) s.nhom[gi].chon_toi_da = Math.max(1, parseInt(o.value, 10) || 1);
    });
  }

  function noi() {
    box.querySelector('.x').onclick = function () { ov.remove(); };
    function bat2(sel, fn) {
      box.querySelectorAll(sel).forEach(function (o) { o.onclick = function () { thu(); fn(o); ve(); }; });
    }
    bat2('[data-cbkieu]', function (o) { s.kieu = o.getAttribute('data-cbkieu'); });
    bat2('[data-cbxoa]', function (o) { s.dong.splice(parseInt(o.getAttribute('data-cbxoa'), 10), 1); });
    bat2('[data-cbotp]', function () { s.can_otp = s.can_otp ? 0 : 1; });
    bat2('[data-cbbat]', function () { s.bat = s.bat ? 0 : 1; });
    bat2('[data-cbquay]', function (o) { s.quay = kmDoiDong(s.quay, o.getAttribute('data-cbquay')); });
    box.querySelectorAll('[data-cbsl],[data-cbg],[data-cbnten],[data-cbntt],[data-cbntd]').forEach(function (o) { o.onchange = function () { thu(); ve(); }; });
    function themMonVao(tenNhom) {
      thu();
      kmChonMon(function (it) {
        s.dong.push({
          item_code: it.value, ten_mon: it.label, so_luong: 1, gia_goc: it.gia || 0,
          nhom: tenNhom || '', chon_trong_nhom: 0
        });
        return 1;
      }, function () { ve(); });
    }
    var tm = box.querySelector('[data-cbthem]');
    if (tm) tm.onclick = function () { themMonVao(''); };
    box.querySelectorAll('[data-cbnthem]').forEach(function (o) {
      o.onclick = function () {
        thu();
        var g = (s.nhom || [])[parseInt(o.getAttribute('data-cbnthem'), 10)];
        if (!g || !String(g.ten || '').trim()) { toast('Đặt tên nhóm trước đã.'); return ve(); }
        themMonVao(String(g.ten).trim());
      };
    });
    var nt = box.querySelector('[data-cbntao]');
    if (nt) nt.onclick = function () {
      thu();
      /* Ten mac dinh khac nhau de hai nhom moi khong dam ten nhau. */
      var i = (s.nhom || []).length + 1;
      var ten = 'Nhóm ' + i;
      while ((s.nhom || []).some(function (g) { return String(g.ten || '').trim() === ten; })) {
        i++; ten = 'Nhóm ' + i;
      }
      s.nhom.push({ ten: ten, chon_toi_thieu: 1, chon_toi_da: 1, mo_ta: '' });
      ve();
    };
    box.querySelectorAll('[data-cbnxoa]').forEach(function (o) {
      o.onclick = async function () {
        thu();
        var gi = parseInt(o.getAttribute('data-cbnxoa'), 10);
        var g = (s.nhom || [])[gi];
        if (!g) return;
        var ten = String(g.ten || '').trim();
        var ds = ten ? cbMonCuaNhom(ten) : [];
        if (ds.length) {
          var ok = await confirmSheet('Bỏ nhóm ' + (ten || 'mới') + '?',
            ds.length + ' món trong nhóm này sẽ thành món có sẵn, tức là luôn vào bill.',
            'Bỏ nhóm', true);
          if (!ok) return;
          ds.forEach(function (d) { d.nhom = ''; d.chon_trong_nhom = 0; });
        }
        s.nhom.splice(gi, 1);
        ve();
      };
    });
    var mc = box.querySelector('[data-cbmocoi]');
    if (mc) mc.onclick = function () {
      thu();
      var ten = {};
      (s.nhom || []).forEach(function (g) { ten[String(g.ten || '').trim()] = 1; });
      (s.dong || []).forEach(function (d) {
        var n = String(d.nhom || '').trim();
        if (n && !ten[n]) { d.nhom = ''; d.chon_trong_nhom = 0; }
      });
      ve();
    };
    box.querySelector('#cbLuu').onclick = async function () {
      thu();
      if (!s.ten) { toast('Combo chưa có tên.'); return; }
      if (!(s.dong || []).length) { toast('Combo phải có ít nhất một món.'); return; }
      var loiNh = '';
      var daTen = {};
      (s.nhom || []).forEach(function (g) {
        if (loiNh) return;
        var ten = String(g.ten || '').trim();
        if (!ten) { loiNh = 'Có nhóm món chưa đặt tên.'; return; }
        if (daTen[ten]) { loiNh = 'Nhóm "' + ten + '" bị khai hai lần.'; return; }
        daTen[ten] = 1;
        var ds = cbMonCuaNhom(ten);
        var toiDa = parseInt(g.chon_toi_da, 10) || 1;
        var toiThieu = parseInt(g.chon_toi_thieu, 10) || 0;
        if (!ds.length) { loiNh = 'Nhóm "' + ten + '" chưa có món nào.'; return; }
        if (toiThieu > toiDa) { loiNh = 'Nhóm "' + ten + '" bắt chọn tối thiểu ' + toiThieu + ' mà tối đa chỉ ' + toiDa + '.'; return; }
        if (toiDa > ds.length) { loiNh = 'Nhóm "' + ten + '" cho chọn tối đa ' + toiDa + ' món mà mới có ' + ds.length + ' món.'; return; }
        if (toiThieu === toiDa && toiDa === ds.length) {
          loiNh = 'Nhóm "' + ten + '" bắt khách lấy hết cả ' + ds.length + ' món thì không còn gì để chọn.';
        }
      });
      if (!loiNh) {
        (s.dong || []).forEach(function (d) {
          if (loiNh) return;
          var n = String(d.nhom || '').trim();
          if (n && !daTen[n]) loiNh = 'Món ' + (d.ten_mon || d.item_code) + ' đang ghi nhóm "' + n + '" mà không có nhóm nào tên đó.';
        });
      }
      if (loiNh) { toast(loiNh, 5000); return; }
      var nut = box.querySelector('#cbLuu'); nut.disabled = true; nut.textContent = 'Đang lưu...';
      try {
        await api('vagabond.khuyen_mai.luu_combo', { du_lieu: JSON.stringify(s), ma: ma || '' });
        ov.remove();
        toast('Đã lưu combo');
        go(scrKhuyenMai, true);
      } catch (e) {
        nut.disabled = false; nut.textContent = 'Lưu combo';
        toast((e && e.message) || 'Không lưu được');
      }
    };
  }

  ve();
  ov.appendChild(box);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  document.body.appendChild(ov);
}

/* ---------- Xuat lo ma voucher qua email ---------- */
function kmSheetXuatLo(ctkm) {
  var x = (kmData.ct || []).filter(function (y) { return y.name === ctkm; })[0] || {};
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>Xuất lô mã ưu đãi</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 14px)">' +
    '<div style="font-size:13px;color:#374151;margin-bottom:12px">Chương trình <b>' + h(x.ten || ctkm) + '</b></div>' +
    '<div style="background:#f0fdfa;border:1.5px solid #7fe5f6;border-radius:9px;padding:11px 13px;margin-bottom:12px;font-size:12px;color:#0b7c93;line-height:1.6">' +
    'Máy sinh đủ số mã <b>6 ký tự ngẫu nhiên khác nhau</b>, mỗi mã dùng được một lần, rồi gửi file CSV về email điền bên dưới. Danh sách này để gửi cho đối tác, brand collab hoặc khách.</div>' +
    kmO('SỐ LƯỢNG MÃ', 'loSl', 100, '100', 'number', 'Tối đa 5.000 mã một lô') +
    kmO('EMAIL NHẬN DANH SÁCH MÃ', 'loEmail', '', 'ten@congty.com', 'email', 'Ai thao tác thì điền email của mình, hoặc điền thẳng email đối tác') +
    kmO('GỬI CHO (đối tác, brand, khách)', 'loCho', '', 'Ví dụ: Brand ABC - collab tháng 9') +
    kmO('HẠN DÙNG CỦA LÔ', 'loHan', x.han_ma || '', '', 'date') +
    kmOta('GHI CHÚ', 'loGc', '', '') +
    '<button class="btn" id="loXuat" style="width:100%;margin-top:6px">Sinh mã và gửi email</button></div>';
  box.querySelector('.x').onclick = function () { ov.remove(); };
  box.querySelector('#loXuat').onclick = async function () {
    var sl = kmN('loSl'), em = kmV('loEmail');
    if (sl <= 0) { toast('Số lượng mã phải lớn hơn 0.'); return; }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(em)) { toast('Email chưa đúng định dạng.'); return; }
    var nut = box.querySelector('#loXuat'); nut.disabled = true; nut.textContent = 'Đang sinh ' + sl + ' mã...';
    try {
      var kq = await api('vagabond.khuyen_mai.xuat_lo', {
        ctkm: ctkm, so_luong: sl, email: em, gui_cho: kmV('loCho'),
        han_dung: kmV('loHan'), ghi_chu: kmV('loGc')
      });
      ov.remove();
      toast(kq.da_gui ? ('Đã sinh ' + kq.so_luong + ' mã và gửi về ' + kq.email) : ('Đã sinh mã nhưng gửi mail lỗi: ' + (kq.loi || '')));
      kmThe = 'lo';
      go(scrKhuyenMai, true);
    } catch (e) {
      nut.disabled = false; nut.textContent = 'Sinh mã và gửi email';
      toast((e && e.message) || 'Không xuất được');
    }
  };
  ov.appendChild(box);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  document.body.appendChild(ov);
}

async function kmSheetLo(lo) {
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>' + h(lo) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:14px"><div class="emp"><div class="e1">⏳</div><div>Đang đọc mã...</div></div></div>';
  box.querySelector('.x').onclick = function () { ov.remove(); };
  ov.appendChild(box);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  document.body.appendChild(ov);
  var kq;
  try { kq = await api('vagabond.khuyen_mai.ds_ma_cua_lo', { lo: lo }); }
  catch (e) { box.innerHTML = '<div class="shh"><b>' + h(lo) + '</b><div class="x">&times;</div></div><div style="padding:20px;color:#b3261e">' + h((e && e.message) || 'Lỗi') + '</div>'; return; }
  var ds = (kq && kq.ma) || [];
  var chuaDung = ds.filter(function (x) { return x.trang_thai === 'Chua dung'; }).length;
  var html = '<div class="shh"><b>' + h(lo) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 14px);max-height:76vh;overflow:auto">' +
    '<div style="font-size:13px;color:#374151;margin-bottom:10px">' + kq.tong_so + ' mã · <b>' + chuaDung + '</b> chưa dùng · ' + (ds.length - chuaDung) + ' đã dùng hoặc huỷ</div>' +
    '<div style="display:flex;flex-wrap:wrap;gap:6px">';
  ds.forEach(function (x) {
    var dung = x.trang_thai === 'Da dung', huy = x.trang_thai === 'Da huy';
    html += '<span title="' + (dung ? h(x.hoa_don || '') : '') + '" style="font-family:ui-monospace,monospace;font-size:13px;letter-spacing:.5px;border-radius:7px;padding:5px 9px;' +
      (dung ? 'background:#f6f7f9;color:#c3c8d4;text-decoration:line-through' : (huy ? 'background:#fef2f2;color:#fca5a5;text-decoration:line-through' : 'background:#f0fdfa;color:#0f766e;font-weight:700')) + '">' + h(x.name) + '</span>';
  });
  html += '</div>';
  if (kq.tong_so > ds.length) html += '<div style="font-size:12px;color:#98a2b3;margin-top:10px">Lô có ' + kq.tong_so + ' mã, đang hiện ' + ds.length + '. File CSV đầy đủ đã gửi qua email.</div>';
  html += '</div>';
  box.innerHTML = html;
  box.querySelector('.x').onclick = function () { ov.remove(); };
}


/* ================= PHAN HE BAO CAO (anh Viet 12/08/2026) =================

Mot cho de ban giam doc, quan ly sales, quan ly cua hang, ke toan va
marketing nhin so lieu CA BA DIEM BAN. Man nay khong tu tinh toan gi het:
moi con so deu do may chu tra ve (vagabond/bao_cao.py), nho vay so tren
app luon bang so trong so sach.

Moi bao cao deu tra ve cung mot hinh dang { cot, dong, cong, bieu_do } nen
man hinh chi viet MOT lan - them bao cao moi ben may chu la app tu hien,
khong phai sua giao dien.

Ba kieu xem theo y anh Viet: bang hang cot, bieu do thanh ngang, va the.
Bang hop de doi chieu, bieu do hop de nhin ty trong, the hop tren dien
thoai khi bang co nhieu cot qua man hinh. */

var bcKy = 'ngay';
var bcMoc = null;      /* mot ngay bat ky nam trong ky dang xem */
var bcTu = null, bcDen = null;   /* chi dung khi ky la tuy_chon */
var bcDiem = '';       /* rong la ca ba diem ban */
var bcXem = 'bang';
var bcMa = null;
var bcLocNguon = '', bcLocPt = '';

var BC_KY = [
  { k: 'ngay', nhan: 'Ngày' },
  { k: 'tuan', nhan: 'Tuần' },
  { k: 'thang', nhan: 'Tháng' },
  { k: 'quy', nhan: 'Quý' },
  { k: 'nam', nhan: 'Năm' },
  { k: 'tuy_chon', nhan: 'Tuỳ chọn' }
];
var BC_DIEM = [
  { ma: '', ten: 'Cả ba điểm' },
  { ma: 'SALES', ten: 'Sales Online' },
  { ma: 'TCV', ten: 'District 1' },
  { ma: 'NVHTN', ten: 'NVHTN' }
];

function bcThamSo() {
  var o = { ky: bcKy, diem: bcDiem };
  if (bcKy === 'tuy_chon') { o.tu = bcTu || today(); o.den = bcDen || today(); }
  else o.moc = bcMoc || today();
  return o;
}

/* Doi ky ma van giu dung ngay dang xem: dang xem thang 8 bam sang "Quy"
   thi ra quy 3, chu khong nhay ve hom nay. */
function bcDoiKy(k) {
  bcKy = k;
  if (!bcMoc) bcMoc = today();
}

/* Lui hoac toi mot ky. Lam o may khach cho nhanh, may chu van tu tinh lai
   dau ky cuoi ky nen khong so lech. */
function bcNhay(huong) {
  var d = new Date((bcMoc || today()) + 'T00:00:00');
  if (bcKy === 'ngay') d.setDate(d.getDate() + huong);
  else if (bcKy === 'tuan') d.setDate(d.getDate() + 7 * huong);
  else if (bcKy === 'thang') d.setMonth(d.getMonth() + huong);
  else if (bcKy === 'quy') d.setMonth(d.getMonth() + 3 * huong);
  else if (bcKy === 'nam') d.setFullYear(d.getFullYear() + huong);
  else return;
  bcMoc = d.toISOString().slice(0, 10);
}

function bcThanhKy() {
  var h1 = BC_KY.map(function (x) {
    return posChipNut('data-bcky="' + x.k + '"', x.nhan, bcKy === x.k);
  }).join('');
  var h2 = BC_DIEM.map(function (x) {
    return posChipNut('data-bcdiem="' + x.ma + '"', x.ten, bcDiem === x.ma);
  }).join('');
  var dieu = bcKy === 'tuy_chon'
    ? '<div style="display:flex;gap:8px;margin-top:8px">' +
      '<input class="tin" id="bcTu" type="date" value="' + h(bcTu || today()) + '" style="flex:1">' +
      '<input class="tin" id="bcDen" type="date" value="' + h(bcDen || today()) + '" style="flex:1">' +
      '</div>'
    : '<div style="display:flex;gap:7px;margin-top:8px">' +
      posChipNut('data-bcnhay="-1"', '◀ Kỳ trước', false) +
      posChipNut('data-bcnhay="0"', 'Hiện tại', false) +
      posChipNut('data-bcnhay="1"', 'Kỳ sau ▶', false) + '</div>';
  return '<div class="card" style="padding:11px 12px">' +
    kmHangChip(h1) + '<div style="height:7px"></div>' + kmHangChip(h2) + dieu + '</div>';
}

function bcNoiThanh(b, veLai) {
  b.onclick = function (e) {
    var t = e.target.closest('[data-bcky]');
    if (t) { bcDoiKy(t.getAttribute('data-bcky')); return veLai(); }
    t = e.target.closest('[data-bcdiem]');
    if (t) { bcDiem = t.getAttribute('data-bcdiem'); return veLai(); }
    t = e.target.closest('[data-bcnhay]');
    if (t) {
      var hg = parseInt(t.getAttribute('data-bcnhay'), 10);
      if (!hg) bcMoc = today(); else bcNhay(hg);
      return veLai();
    }
    t = e.target.closest('[data-bcmo]');
    if (t) { bcMa = t.getAttribute('data-bcmo'); return go(scrBaoCaoXem, true); }
    t = e.target.closest('[data-bcxem]');
    if (t) { bcXem = t.getAttribute('data-bcxem'); return veLai(); }
    t = e.target.closest('[data-bcnguon]');
    if (t) { bcLocNguon = t.getAttribute('data-bcnguon'); return veLai(); }
    t = e.target.closest('[data-bcpt]');
    if (t) { bcLocPt = t.getAttribute('data-bcpt'); return veLai(); }
  };
  ['bcTu', 'bcDen'].forEach(function (id) {
    var o = document.getElementById(id);
    if (o) o.onchange = function () {
      bcTu = document.getElementById('bcTu').value;
      bcDen = document.getElementById('bcDen').value;
      veLai();
    };
  });
}

/* ---------- man chinh: danh sach bao cao ---------- */
async function scrBaoCao() {
  frame('Báo cáo', '<div class="emp"><div class="e1">⏳</div><div>Đang cộng sổ ba điểm bán...</div></div>');
  var kq;
  try { kq = await api('vagabond.bao_cao.danh_sach', bcThamSo()); }
  catch (e) {
    frame('Báo cáo', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được báo cáo') + '</div></div>');
    return;
  }

  var html = bcThanhKy();

  html += '<div class="card" style="padding:14px">' +
    '<div style="font-size:12px;color:#98a2b3">TỔNG DOANH THU · ' + h(kq.nhan_ky) + '</div>' +
    '<div style="font-size:30px;font-weight:800;line-height:1.25">' + money(kq.tong_doanh_thu) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280">' + money(kq.so_hoa_don) + ' hoá đơn · bình quân ' + money(Math.round(kq.binh_quan)) + ' đ/hoá đơn</div>' +
    '<div style="height:10px"></div>' +
    kq.diem_ban.map(function (d) {
      var pc = kq.tong_doanh_thu ? d.tien / kq.tong_doanh_thu * 100 : 0;
      return '<div style="margin-bottom:9px">' +
        '<div style="display:flex;justify-content:space-between;font-size:13px">' +
        '<span><b>' + h(d.ten) + '</b> <span style="color:#a0a6b4">' + h(d.dia_chi) + '</span></span>' +
        '<b>' + money(d.tien) + ' đ</b></div>' +
        '<div style="height:7px;border-radius:99px;background:#eef0f5;overflow:hidden;margin-top:4px">' +
        '<div style="height:100%;width:' + Math.max(1, Math.round(pc)) + '%;background:#50DBF2"></div></div></div>';
    }).join('') + '</div>';

  var nhom = [];
  kq.bao_cao.forEach(function (b) {
    var g = null;
    nhom.forEach(function (x) { if (x.ten === b.nhom) g = x; });
    if (!g) { g = { ten: b.nhom, ds: [] }; nhom.push(g); }
    g.ds.push(b);
  });
  nhom.forEach(function (g) {
    html += '<div class="sec">' + h(g.ten) + '</div><div class="card">' +
      g.ds.map(function (b) {
        return '<div class="row" data-bcmo="' + h(b.ma) + '" style="display:flex;align-items:center;gap:11px;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
          '<div style="width:34px;height:34px;border-radius:9px;background:#f0fdfa;display:flex;align-items:center;justify-content:center;font-size:17px">' + b.ic + '</div>' +
          '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(b.ten) + '</b>' +
          '<div style="font-size:12px;color:#98a2b3">' + h(b.ma) + ' · ' + h(b.mo) + '</div></div>' +
          '<span style="color:#c3c8d4">›</span></div>';
      }).join('') + '</div>';
  });

  html += '<div style="text-align:center;color:#a0a6b4;font-size:11.5px;padding:8px 14px 2px;line-height:1.6">' +
    'Số liệu đọc thẳng từ hoá đơn đã ghi sổ, không qua bảng tổng hợp nên luôn khớp với sổ sách.</div>';

  var b = frame('Báo cáo', html);
  bcNoiThanh(b, function () { go(scrBaoCao, true); });
}

/* ---------- man xem mot bao cao ---------- */
function bcO(c, v) {
  if (c.kieu === 'tien') return money(Math.round(flt0(v))) + ' đ';
  if (c.kieu === 'so') return money(Math.round(flt0(v) * 100) / 100);
  if (c.kieu === 'phan_tram') return (Math.round(flt0(v) * 10) / 10) + '%';
  if (c.kieu === 'ngay') return posNgayVn(String(v || ''));
  return h(String(v == null ? '' : v));
}
function flt0(v) { var n = parseFloat(v); return isNaN(n) ? 0 : n; }

function bcVeBang(kq) {
  if (!kq.dong.length) return '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Kỳ này chưa có số liệu.</div></div></div>';
  var canPhai = { tien: 1, so: 1, phan_tram: 1 };
  var html = '<div class="card" style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:13px">' +
    '<thead><tr>' + kq.cot.map(function (c) {
      return '<th style="text-align:' + (canPhai[c.kieu] ? 'right' : 'left') + ';padding:10px 12px;background:#f8fafc;color:#6b7280;font-size:11.5px;font-weight:700;white-space:nowrap;position:sticky;top:0">' + h(c.nhan) + '</th>';
    }).join('') + '</tr></thead><tbody>';
  kq.dong.forEach(function (r, i) {
    html += '<tr style="border-top:1px solid #f2f4f7' + (i % 2 ? ';background:#fcfdfe' : '') + '">' +
      kq.cot.map(function (c, j) {
        return '<td style="text-align:' + (canPhai[c.kieu] ? 'right' : 'left') + ';padding:9px 12px;white-space:nowrap' + (j === 0 ? ';font-weight:600' : '') + '">' + bcO(c, r[c.k]) + '</td>';
      }).join('') + '</tr>';
  });
  if (kq.cong && Object.keys(kq.cong).length) {
    html += '<tr style="border-top:2px solid #e5e7eb;background:#f0fdfa;font-weight:800">' +
      kq.cot.map(function (c, j) {
        var v = j === 0 ? 'TỔNG' : (kq.cong[c.k] == null ? '' : bcO(c, kq.cong[c.k]));
        return '<td style="text-align:' + (canPhai[c.kieu] && j ? 'right' : 'left') + ';padding:10px 12px;white-space:nowrap">' + (j === 0 ? v : v) + '</td>';
      }).join('') + '</tr>';
  }
  return html + '</tbody></table></div>';
}

function bcVeBieuDo(kq) {
  var bd = kq.bieu_do;
  if (!bd) return '<div class="card"><div class="emp" style="padding:24px"><div class="e2">Báo cáo này không hợp để vẽ biểu đồ, xem dạng bảng nhé.</div></div></div>';
  var ds = kq.dong.slice(0, bd.so_dong || 15);
  if (!ds.length) return '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Kỳ này chưa có số liệu.</div></div></div>';
  var cot = null;
  kq.cot.forEach(function (c) { if (c.k === bd.gia_tri) cot = c; });
  var lon = 0;
  ds.forEach(function (r) { lon = Math.max(lon, flt0(r[bd.gia_tri])); });
  return '<div class="card" style="padding:14px">' + ds.map(function (r) {
    var v = flt0(r[bd.gia_tri]);
    var pc = lon ? Math.max(2, Math.round(v / lon * 100)) : 2;
    return '<div style="margin-bottom:11px">' +
      '<div style="display:flex;justify-content:space-between;gap:10px;font-size:13px">' +
      '<span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + h(String(r[bd.nhan] == null ? '' : r[bd.nhan])) + '</span>' +
      '<b style="white-space:nowrap">' + bcO(cot || { kieu: 'so' }, v) + '</b></div>' +
      '<div style="height:9px;border-radius:99px;background:#eef0f5;overflow:hidden;margin-top:4px">' +
      '<div style="height:100%;width:' + pc + '%;background:linear-gradient(90deg,#50DBF2,#0ea5b7)"></div></div></div>';
  }).join('') + '</div>';
}

function bcVeThe(kq) {
  if (!kq.dong.length) return '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Kỳ này chưa có số liệu.</div></div></div>';
  return '<div style="display:grid;gap:10px">' + kq.dong.map(function (r) {
    var dau = kq.cot[0];
    return '<div class="card" style="padding:12px 14px;margin:0">' +
      '<b style="font-size:14.5px">' + bcO(dau, r[dau.k]) + '</b>' +
      '<div style="display:grid;gap:4px;margin-top:7px">' +
      kq.cot.slice(1).map(function (c) {
        return '<div style="display:flex;justify-content:space-between;font-size:13px;color:#374151">' +
          '<span style="color:#98a2b3">' + h(c.nhan) + '</span><b>' + bcO(c, r[c.k]) + '</b></div>';
      }).join('') + '</div></div>';
  }).join('') + '</div>';
}

async function scrBaoCaoXem() {
  var ma = bcMa || 'BC01';
  frame('Báo cáo ' + ma, '<div class="emp"><div class="e1">⏳</div><div>Đang cộng sổ...</div></div>');
  var ts = bcThamSo();
  ts.ma = ma;
  if (bcLocNguon) ts.nguon = bcLocNguon;
  if (bcLocPt) ts.pt = bcLocPt;
  var kq;
  try { kq = await api('vagabond.bao_cao.chay', ts); }
  catch (e) {
    frame('Báo cáo ' + ma, '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không chạy được') + '</div></div>');
    return;
  }

  var html = bcThanhKy();
  html += '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">' + h(kq.ma) + ' · ' + h(kq.nhan_ky) + '</div>' +
    '<div style="font-size:19px;font-weight:800">' + kq.ic + ' ' + h(kq.ten) + '</div>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-top:2px">' + h(kq.mo) + '</div>' +
    '<div style="font-size:13px;color:#0f766e;margin-top:8px"><b>' + money(kq.tong_doanh_thu) + ' đ</b> doanh thu · ' + money(kq.so_hoa_don) + ' hoá đơn trong phạm vi đang lọc</div>' +
    '</div>';

  /* Chip loc nguon don va phuong thuc thanh toan: chi hien khi ky nay
     that su co nhieu hon mot gia tri, khoi bay chip vo ich. */
  if ((kq.nguon_loc || []).length > 1) {
    html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
      posChipNut('data-bcnguon=""', 'Mọi nguồn đơn', !bcLocNguon) +
      kq.nguon_loc.map(function (n) { return posChipNut('data-bcnguon="' + h(n) + '"', h(n), bcLocNguon === n); }).join('')
    ) + '</div>';
  }
  if ((kq.pt_loc || []).length > 1) {
    html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
      posChipNut('data-bcpt=""', 'Mọi phương thức', !bcLocPt) +
      kq.pt_loc.map(function (n) { return posChipNut('data-bcpt="' + h(n) + '"', h(n), bcLocPt === n); }).join('')
    ) + '</div>';
  }

  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    posChipNut('data-bcxem="bang"', '📋 Bảng', bcXem === 'bang') +
    posChipNut('data-bcxem="bieu_do"', '📊 Biểu đồ', bcXem === 'bieu_do') +
    posChipNut('data-bcxem="the"', '🗂️ Thẻ', bcXem === 'the')
  ) + '</div>';

  if (bcXem === 'bieu_do') html += bcVeBieuDo(kq);
  else if (bcXem === 'the') html += bcVeThe(kq);
  else html += bcVeBang(kq);

  if (kq.phu && (kq.phu.dong || []).length) {
    html += '<div class="sec">' + h(kq.phu.tieu_de) + '</div>' +
      bcVeBang({ cot: kq.phu.cot, dong: kq.phu.dong, cong: null });
  }

  var b = frame('Báo cáo ' + kq.ma, html, { footer: '<button class="btn" id="bcExcel">📥 Xuất Excel cho kế toán</button>' });
  bcNoiThanh(b, function () { go(scrBaoCaoXem, true); });

  var nx = document.getElementById('bcExcel');
  if (nx) nx.onclick = async function () {
    busy(true);
    try {
      var ts2 = bcThamSo(); ts2.ma = kq.ma;
      if (bcLocNguon) ts2.nguon = bcLocNguon;
      if (bcLocPt) ts2.pt = bcLocPt;
      var f = await api('vagabond.bao_cao.xuat_excel', ts2);
      busy(false);
      bcTaiVe(f.ten_file, f.b64);
      toast('Đã tải ' + f.ten_file);
    } catch (e) { busy(false); toast((e && e.message) || 'Không xuất được'); }
  };
}

/* Doi chuoi base64 may chu gui ve thanh file tren may nguoi dung. Lam o
   day chu khong mo tab moi: tren dien thoai mo tab la trinh duyet hoi
   "tai xuong?" hai lan, nhan vien tuong hong. */
function bcTaiVe(ten, b64) {
  var thoi = atob(b64);
  var so = new Uint8Array(thoi.length);
  for (var i = 0; i < thoi.length; i++) so[i] = thoi.charCodeAt(i);
  var blob = new Blob([so], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url; a.download = ten;
  document.body.appendChild(a); a.click();
  setTimeout(function () { URL.revokeObjectURL(url); a.remove(); }, 1500);
}


/* ========== DON MUA HANG, CONG NO PHAI TRA, HAI MAN HOA DON ==========
   (anh Viet 12/08/2026)

Bon man dung chung mot khuon: mot hang chip trang thai co dem so, mot o
tim, roi danh sach. Chip nao dang chon thi to mau; bam lai chip "Tất cả"
de bo loc.

Man nao cung doc so lieu song tu may chu, khong nho cache - ke toan mo ra
la thay dung tinh hinh luc do. */

/* Ngay dang ngan gon "11/08/2026", rong thi tra ve dau gach - posNgayVn
   co san tra ve ca thu trong tuan, dai qua cho danh sach, va no vo khi
   chuoi ngay rong. */
function ngayNgan(iso) {
  var p = String(iso || '').split('-');
  return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : '-';
}

/* Danh sach dai qua thi may chu chi tra ve 300 dong dau. KHONG duoc im
   lang cat bot: nguoi doc se tuong da xem het. Con so dem tren chip va so
   tong van tinh tren toan bo, chi rieng danh sach bi cat. */
function mkNhacCat(soCat, donVi) {
  if (!soCat) return '';
  return '<div style="margin-top:9px;background:#fff7ed;border:1.5px solid #fed7aa;border-radius:9px;padding:9px 11px;font-size:12.5px;color:#9a3412">' +
    'Danh sách bên dưới chỉ hiện 300 ' + donVi + ' mới nhất, còn <b>' + money(soCat) + '</b> ' + donVi +
    ' nữa chưa hiện. Thu hẹp khoảng ngày hoặc bấm một chip trạng thái để xem cho đủ. Các con số tổng ở trên vẫn tính đủ.</div>';
}

var poNhom = '', poNgay = 60, poTim = '', poXem = null;
var ktBanNhom = '', ktBanNgay = 30, ktBanQuay = '', ktBanTim = '';
var ktMuaNhom = '', ktMuaNgay = 60, ktMuaTim = '';

/* Hang chip co dem so, dung chung cho ca bon man. */
function mkChipNhom(ds, dem, dangChon, thuoc) {
  return kmHangChip(ds.map(function (n) {
    var so = (dem || {})[n.k];
    return posChipNut(thuoc + '="' + h(n.k) + '"',
      n.ic + ' ' + h(n.ten) + (so ? ' <b>' + so + '</b>' : ''), dangChon === n.k);
  }).join(''));
}

function mkChipNgay(ds, dangChon, thuoc) {
  return kmHangChip(ds.map(function (n) {
    return posChipNut(thuoc + '="' + n[0] + '"', h(n[1]), String(dangChon) === String(n[0]));
  }).join(''));
}

function mkOTim(id, gt, moTa) {
  return '<div class="card" style="padding:10px 12px">' +
    '<input class="tin" id="' + id + '" placeholder="' + h(moTa) + '" value="' + h(gt || '') + '"></div>';
}

/* ---------------- Don mua hang (PO) ---------------- */
async function scrDonMua() {
  frame('Đơn mua hàng', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc đơn mua hàng...</div></div>');
  var kq;
  try { kq = await api('vagabond.mua_hang.ds_po', { so_ngay: poNgay, tu_khoa: poTim, nhom: poNhom }); }
  catch (e) {
    frame('Đơn mua hàng', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  /* Loc theo chip lam o MAY CHU roi, o day chi ve ra. */
  var ds = kq.don || [];

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">ĐƠN MUA HÀNG ' + (poNgay ? h(poNgay) + ' NGÀY GẦN ĐÂY' : 'TẤT CẢ') + '</div>' +
    '<div style="font-size:24px;font-weight:800">' + money(kq.tong_tien) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280">' + money(kq.tong_dong) + ' đơn · đang xem ' + money(ds.length) + '</div>' +
    mkNhacCat(kq.bi_cat, 'đơn') + '</div>';

  html += '<div class="card" style="padding:10px 12px">' +
    mkChipNgay([[30, '30 ngày'], [60, '60 ngày'], [180, '6 tháng'], [0, 'Tất cả']], poNgay, 'data-pongay') + '</div>';
  html += '<div class="card" style="padding:10px 12px">' + mkChipNhom(kq.nhom, kq.dem, poNhom, 'data-ponhom') + '</div>';
  html += mkOTim('poTim', poTim, 'Tìm theo mã đơn hoặc tên nhà cung cấp...');

  if (!ds.length) {
    html += '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Không có đơn nào ở nhóm này.</div></div></div>';
  } else {
    html += '<div class="lst">' + ds.map(function (d) {
      var mau = { tre_hen: '#b3261e', cho_hoa_don: '#b45309', nhap: '#6b7280', xong: '#0f766e' }[d.nhom] || '#374151';
      var ten = '';
      (kq.nhom || []).forEach(function (n) { if (n.k === d.nhom) ten = n.ic + ' ' + n.ten; });
      return '<div class="shi" data-po="' + h(d.name) + '" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
        '<div style="flex:1;min-width:0">' +
        '<b style="font-size:14.5px">' + h(d.supplier_name || d.supplier) + '</b>' +
        '<div style="font-size:12px;color:#98a2b3">' + h(d.name) + ' · đặt ' + ngayNgan(d.ngay) +
        (d.hen ? ' · hẹn ' + ngayNgan(d.hen) : '') + '</div>' +
        '<div style="font-size:12px;color:' + mau + ';font-weight:600;margin-top:3px">' + h(ten) +
        (d.tre_ngay ? ' ' + d.tre_ngay + ' ngày' : '') +
        (d.nhom === 'nhan_mot_phan' ? ' · đã nhận ' + Math.round(d.per_received) + '%' : '') + '</div></div>' +
        '<b style="white-space:nowrap">' + money(d.grand_total) + ' đ</b></div>';
    }).join('') + '</div>';
  }

  var b = frame('Đơn mua hàng', html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-ponhom]');
    if (t) { poNhom = t.getAttribute('data-ponhom'); return go(scrDonMua, true); }
    t = e.target.closest('[data-pongay]');
    if (t) { poNgay = parseInt(t.getAttribute('data-pongay'), 10); return go(scrDonMua, true); }
    t = e.target.closest('[data-po]');
    if (t) { poXem = t.getAttribute('data-po'); return go(scrDonMuaXem, true); }
  };
  var o = document.getElementById('poTim');
  if (o) o.onchange = function () { poTim = o.value; go(scrDonMua, true); };
}

async function scrDonMuaXem() {
  frame('Đơn mua hàng', '<div class="emp"><div class="e1">⏳</div></div>');
  var d;
  try { d = await api('vagabond.mua_hang.xem_po', { name: poXem }); }
  catch (e) { frame('Đơn mua hàng', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>'); return; }

  var html = '<div class="card" style="padding:13px 14px;line-height:1.7">' +
    '<b style="font-size:15px">' + h(d.ten_ncc || d.ncc) + '</b>' +
    '<div style="font-size:12.5px;color:#6b7280">' + h(d.name) + ' · đặt ngày ' + ngayNgan(d.ngay) +
    (d.hen ? ' · hẹn giao ' + ngayNgan(d.hen) : '') + '</div>' +
    '<div style="font-size:13px;margin-top:6px">Đã nhận <b>' + Math.round(d.da_nhan) + '%</b> · đã lên hoá đơn <b>' + Math.round(d.da_hoa_don) + '%</b></div>' +
    '</div>';

  html += '<div class="sec">Mặt hàng</div><div class="card" style="padding:6px 14px">' +
    d.mon.map(function (m) {
      return '<div style="display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
        '<div style="flex:1;min-width:0">' + h(m.ten || m.ma) +
        '<div style="color:#a0a6b4;font-size:12px">đặt ' + money(m.sl) + ' ' + h(m.dvt || '') +
        ' · đã nhận ' + money(m.da_nhan) + ' · ' + money(m.gia) + ' đ</div></div>' +
        '<b style="white-space:nowrap">' + money(m.tien) + '</b></div>';
    }).join('') +
    '<div style="display:flex;justify-content:space-between;padding:9px 0;color:#5a6070"><span>Tiền hàng</span><span>' + money(d.tong_hang) + ' đ</span></div>' +
    (d.thue ? '<div style="display:flex;justify-content:space-between;padding:2px 0;color:#5a6070"><span>Thuế và phí</span><span>' + money(d.thue) + ' đ</span></div>' : '') +
    '<div style="display:flex;justify-content:space-between;padding:9px 0;font-size:16px"><b>Tổng cộng</b><b>' + money(d.tong) + ' đ</b></div></div>';

  html += '<div class="sec">Đã nối với</div><div class="card" style="padding:12px 14px;font-size:13.5px;line-height:1.8">' +
    '<div>Phiếu nhập kho: ' + (d.phieu_nhap.length ? '<b>' + d.phieu_nhap.map(h).join(', ') + '</b>' : '<span style="color:#b45309">chưa có phiếu nào</span>') + '</div>' +
    '<div>Hoá đơn mua: ' + (d.hoa_don.length ? '<b>' + d.hoa_don.map(h).join(', ') + '</b>' : '<span style="color:#b45309">chưa có hoá đơn nào</span>') + '</div>' +
    '</div>';

  frame('Đơn mua hàng', html);
}

/* ---------------- Cong no phai tra ---------------- */
var cntNcc = null;
async function scrNoPhaiTra() {
  frame('Công nợ phải trả', '<div class="emp"><div class="e1">⏳</div><div>Đang cộng sổ nợ nhà cung cấp...</div></div>');
  var kq;
  try { kq = await api('vagabond.mua_hang.cong_no_phai_tra', {}); }
  catch (e) {
    frame('Công nợ phải trả', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  var html = '<div class="card" style="padding:14px">' +
    '<div style="font-size:12px;color:#98a2b3">TỔNG CÒN PHẢI TRẢ</div>' +
    '<div style="font-size:28px;font-weight:800">' + money(kq.tong) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280">' + money(kq.so_ncc) + ' nhà cung cấp</div>' +
    (kq.tong_qua_han
      ? '<div style="margin-top:9px;background:#fef2f2;border:1.5px solid #fecaca;border-radius:9px;padding:10px 12px;font-size:13px;color:#b3261e">' +
        'Trong đó <b>' + money(kq.tong_qua_han) + ' đ</b> đã quá hạn trả.</div>'
      : '<div style="margin-top:9px;font-size:13px;color:#0f766e">Chưa có khoản nào quá hạn.</div>') +
    '</div>';

  if (!(kq.ncc || []).length) {
    html += '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🎉</div><div>Không nợ nhà cung cấp nào.</div></div></div>';
  } else {
    html += '<div class="sec">Nợ nhiều và quá hạn xếp lên đầu</div><div class="lst">' +
      kq.ncc.map(function (n) {
        return '<div class="shi" data-ncc="' + h(n.ncc) + '" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
          '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(n.ten) + '</b>' +
          '<div style="font-size:12px;color:#98a2b3">' + money(n.so_hd) + ' hoá đơn' +
          (n.han_gan_nhat ? ' · hạn gần nhất ' + ngayNgan(n.han_gan_nhat) : '') + '</div>' +
          (n.qua_han
            ? '<div style="font-size:12px;color:#b3261e;font-weight:600;margin-top:3px">Quá hạn ' + money(n.qua_han) + ' đ · ' + n.so_hd_qua_han + ' hoá đơn</div>'
            : '') + '</div>' +
          '<b style="white-space:nowrap">' + money(n.tien) + ' đ</b></div>';
      }).join('') + '</div>';
  }

  var b = frame('Công nợ phải trả', html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-ncc]');
    if (!t) return;
    var ma = t.getAttribute('data-ncc');
    var n = (kq.ncc || []).filter(function (x) { return x.ncc === ma; })[0];
    if (n) mkSheetNoNcc(n);
  };
}

function mkSheetNoNcc(n) {
  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';
  box.innerHTML = '<div class="shh"><b>' + h(n.ten) + '</b><div class="x">&times;</div></div>' +
    '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 16px);max-height:78vh;overflow:auto">' +
    '<div style="font-size:13px;color:#374151;margin:8px 0 12px">Còn nợ <b>' + money(n.tien) + ' đ</b> trên ' + money(n.so_hd) + ' hoá đơn' +
    (n.qua_han ? ', trong đó <b style="color:#b3261e">' + money(n.qua_han) + ' đ quá hạn</b>' : '') + '.</div>' +
    n.hd.map(function (x) {
      return '<div style="border:1.5px solid ' + (x.tre_ngay ? '#fecaca' : '#e5e7eb') + ';background:' + (x.tre_ngay ? '#fef2f2' : '#fff') + ';border-radius:10px;padding:10px 12px;margin-bottom:8px">' +
        '<div style="display:flex;justify-content:space-between;gap:10px">' +
        '<b style="font-size:13.5px">' + h(x.name) + '</b><b>' + money(x.con_no) + ' đ</b></div>' +
        '<div style="font-size:12px;color:#6b7280;margin-top:3px">' +
        (x.so_hd_ncc ? 'Số hoá đơn NCC ' + h(x.so_hd_ncc) + ' · ' : '') +
        'ngày ' + ngayNgan(x.ngay) + (x.han ? ' · hạn trả ' + ngayNgan(x.han) : '') +
        (x.tre_ngay ? ' · <b style="color:#b3261e">trễ ' + x.tre_ngay + ' ngày</b>' : '') + '</div>' +
        (x.tong !== x.con_no ? '<div style="font-size:12px;color:#98a2b3">Tổng hoá đơn ' + money(x.tong) + ' đ, đã trả ' + money(x.tong - x.con_no) + ' đ</div>' : '') +
        '</div>';
    }).join('') + '</div>';
  ov.appendChild(box); document.body.appendChild(ov);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  box.querySelector('.x').onclick = function () { ov.remove(); };
}

/* ---------------- Hoa don ban ra ---------------- */
async function scrHdBan() {
  frame('Hoá đơn bán ra', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc hoá đơn...</div></div>');
  var kq;
  try { kq = await api('vagabond.ke_toan.ds_hoa_don_ban', { so_ngay: ktBanNgay, quay: ktBanQuay, tu_khoa: ktBanTim, nhom: ktBanNhom }); }
  catch (e) {
    frame('Hoá đơn bán ra', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  var ds = kq.hd || [];

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">HOÁ ĐƠN BÁN RA · ' + ngayNgan(kq.tu) + ' - ' + ngayNgan(kq.den) + '</div>' +
    '<div style="font-size:24px;font-weight:800">' + money(kq.tong) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280">' + money(kq.tong_dong) + ' hoá đơn · đang xem ' + money(ds.length) +
    (kq.con_thu ? ' · còn phải thu ' + money(kq.con_thu) + ' đ' : '') + '</div>' +
    mkNhacCat(kq.bi_cat, 'hoá đơn') + '</div>';

  html += '<div class="card" style="padding:10px 12px">' +
    mkChipNgay([[7, '7 ngày'], [30, '30 ngày'], [90, '3 tháng'], [365, '1 năm']], ktBanNgay, 'data-ktbngay') + '</div>';
  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    [['', 'Cả ba điểm'], ['SALES', 'Sales Online'], ['TCV', 'District 1'], ['NVHTN', 'NVHTN']]
      .map(function (q) { return posChipNut('data-ktbquay="' + q[0] + '"', q[1], ktBanQuay === q[0]); }).join('')) + '</div>';
  html += '<div class="card" style="padding:10px 12px">' + mkChipNhom(kq.nhom, kq.dem, ktBanNhom, 'data-ktbnhom') + '</div>';
  html += mkOTim('ktBanTim', ktBanTim, 'Tìm theo mã phiếu, tên khách, số hoá đơn điện tử...');

  html += mkBangHd(ds, 'ban');
  var b = frame('Hoá đơn bán ra', html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-ktbnhom]');
    if (t) { ktBanNhom = t.getAttribute('data-ktbnhom'); return go(scrHdBan, true); }
    t = e.target.closest('[data-ktbngay]');
    if (t) { ktBanNgay = parseInt(t.getAttribute('data-ktbngay'), 10); return go(scrHdBan, true); }
    t = e.target.closest('[data-ktbquay]');
    if (t) { ktBanQuay = t.getAttribute('data-ktbquay'); return go(scrHdBan, true); }
    t = e.target.closest('[data-hdb]');
    if (t) return go(function () { scrDsView(t.getAttribute('data-hdb'), true); });
  };
  var o = document.getElementById('ktBanTim');
  if (o) o.onchange = function () { ktBanTim = o.value; go(scrHdBan, true); };
}

var TEN_DIEM_BAN = { SALES: 'Sales Online', TCV: 'District 1', NVHTN: 'NVHTN' };

function mkBangHd(ds, loai) {
  if (!ds.length) return '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Không có hoá đơn nào ở nhóm này.</div></div></div>';
  return '<div class="lst">' + ds.map(function (d) {
    if (loai === 'ban') {
      return '<div class="shi" data-hdb="' + h(d.name) + '" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
        '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(d.khach || 'Khách lẻ') + '</b>' +
        '<div style="font-size:12px;color:#98a2b3">' + h(d.name) + ' · ' + ngayNgan(d.posting_date) +
        ' · ' + h(TEN_DIEM_BAN[d.diem] || d.diem) + '</div>' +
        '<div style="font-size:12px;color:#6b7280;margin-top:3px">' +
        (d.custom_hddt_so ? 'HĐ ' + h(d.custom_hddt_so) + ' · ' + h(d.custom_hddt_trang_thai || '') : '<span style="color:#b45309">chưa xuất hoá đơn điện tử</span>') +
        (d.vgb_pt_thanh_toan ? ' · ' + h(d.vgb_pt_thanh_toan) : '') +
        (d.docstatus === 0 && !d.vgb_huy ? ' · <b style="color:#b45309">còn nháp</b>' : '') +
        (d.docstatus === 2 || d.vgb_huy ? ' · <b style="color:#b3261e">🚫 đã huỷ</b>' : '') +
        (d.vgb_huy && d.vgb_huy_ly_do ? ' <span style="color:#b3261e">(' + h(d.vgb_huy_ly_do) + ')</span>' : '') +
        (d.da_sua ? ' · <b style="color:#92400e">✏️ đã sửa</b>' : '') + '</div></div>' +
        '<div style="text-align:right;white-space:nowrap"><b>' + money(d.grand_total) + '</b>' +
        (d.docstatus === 1 && d.outstanding_amount > 0 ? '<div style="font-size:11.5px;color:#b3261e">còn ' + money(d.outstanding_amount) + '</div>' : '') +
        '</div></div>';
    }
    return '<div class="shi" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(d.supplier_name || d.supplier) + '</b>' +
      '<div style="font-size:12px;color:#98a2b3">' + h(d.name) + ' · ' + ngayNgan(d.posting_date) +
      (d.bill_no ? ' · số ' + h(d.bill_no) : '') + '</div>' +
      '<div style="font-size:12px;color:#6b7280;margin-top:3px">' +
      (d.vgb_huy ? '<b style="color:#b3261e">🚫 đã huỷ' + (d.vgb_huy_ly_do ? ' (' + h(d.vgb_huy_ly_do) + ')' : '') + '</b>'
        : d.docstatus === 0 ? '<b style="color:#b45309">còn nháp</b>'
        : d.docstatus === 2 ? '<b style="color:#b3261e">đã huỷ</b>'
          : d.outstanding_amount > 0
            ? (d.tre_ngay ? '<b style="color:#b3261e">quá hạn ' + d.tre_ngay + ' ngày</b>' : 'hạn trả ' + ngayNgan(d.due_date || ''))
            : '<span style="color:#0f766e">đã trả xong</span>') +
      (d.da_sua ? ' · <b style="color:#92400e">✏️ đã sửa</b>' : '') + '</div></div>' +
      '<div style="text-align:right;white-space:nowrap"><b>' + money(d.grand_total) + '</b>' +
      (d.docstatus === 1 && d.outstanding_amount > 0 ? '<div style="font-size:11.5px;color:#b3261e">còn ' + money(d.outstanding_amount) + '</div>' : '') +
      '</div></div>';
  }).join('') + '</div>';
}

/* ---------------- Hoa don mua vao ---------------- */
async function scrHdMua() {
  frame('Hoá đơn mua vào', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc hoá đơn...</div></div>');
  var kq;
  try { kq = await api('vagabond.ke_toan.ds_hoa_don_mua', { so_ngay: ktMuaNgay, tu_khoa: ktMuaTim, nhom: ktMuaNhom }); }
  catch (e) {
    frame('Hoá đơn mua vào', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  var ds = kq.hd || [];

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">HOÁ ĐƠN MUA VÀO · ' + ngayNgan(kq.tu) + ' - ' + ngayNgan(kq.den) + '</div>' +
    '<div style="font-size:24px;font-weight:800">' + money(kq.tong) + ' đ</div>' +
    '<div style="font-size:12.5px;color:#6b7280">' + money(kq.tong_dong) + ' hoá đơn · đang xem ' + money(ds.length) +
    (kq.con_no ? ' · còn nợ ' + money(kq.con_no) + ' đ' : '') + '</div>' +
    mkNhacCat(kq.bi_cat, 'hoá đơn') + '</div>';

  html += '<div class="card" style="padding:10px 12px">' +
    mkChipNgay([[30, '30 ngày'], [60, '60 ngày'], [180, '6 tháng'], [365, '1 năm']], ktMuaNgay, 'data-ktmngay') + '</div>';
  html += '<div class="card" style="padding:10px 12px">' + mkChipNhom(kq.nhom, kq.dem, ktMuaNhom, 'data-ktmnhom') + '</div>';
  html += mkOTim('ktMuaTim', ktMuaTim, 'Tìm theo mã phiếu, tên nhà cung cấp, số hoá đơn...');
  html += mkBangHd(ds, 'mua');

  var b = frame('Hoá đơn mua vào', html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-ktmnhom]');
    if (t) { ktMuaNhom = t.getAttribute('data-ktmnhom'); return go(scrHdMua, true); }
    t = e.target.closest('[data-ktmngay]');
    if (t) { ktMuaNgay = parseInt(t.getAttribute('data-ktmngay'), 10); return go(scrHdMua, true); }
  };
  var o = document.getElementById('ktMuaTim');
  if (o) o.onchange = function () { ktMuaTim = o.value; go(scrHdMua, true); };
}


/* ===== Cai dat: chuoi cuoi ngay theo tung diem ban (anh Viet 12/08/2026) =====

Truoc day muon doi gio chay hay bat tat mot chi nhanh la phai sua code roi
deploy. Nay bay het len app: bat tat tung diem ban, chon gio, va co nut chay
tay khi can.

Ba buoc chay LIEN NHAU trong mot lan: ghi so, phat hanh hoa don dien tu, roi
ky. Mac dinh 23:00 de xong truoc 23h30 - chi Dung so xuat sat 24h, lo nghen
mang la to hoa don lot sang ngay hom sau, sai luat ke toan. */

var cdData = null, cdGhiSo = [], cdHddt = [], cdBat = 1, cdGio = '23:00';

async function scrCaiDatCuoiNgay() {
  frame('Cuối ngày', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try { cdData = await api('vagabond.ban_hang.cai_dat_cuoi_ngay', {}); }
  catch (e) {
    frame('Cuối ngày', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  cdBat = cdData.bat ? 1 : 0;
  cdGio = cdData.gio || '23:00';
  cdGhiSo = (cdData.diem || []).filter(function (d) { return d.ghi_so; }).map(function (d) { return d.ma; });
  cdHddt = (cdData.diem || []).filter(function (d) { return d.hddt; }).map(function (d) { return d.ma; });
  cdVe();
}

function cdVe() {
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">CHUỖI CUỐI NGÀY</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Mỗi ngày một lần, máy chạy liền ba bước: <b>ghi sổ</b> hoá đơn còn nháp, <b>phát hành</b> hoá đơn điện tử, rồi <b>ký</b>. ' +
    'Đặt 23:00 thì cả ba xong trước 23h30, không lo nghẽn mạng làm hoá đơn lọt sang ngày hôm sau.</div></div>';

  html += '<div class="card" style="padding:11px 12px">' + kmHangChip(
    posChipNut('data-cdbat="1"', cdBat ? '● Đang bật' : '○ Đang tắt', !!cdBat)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px">Tắt thì không có gì tự chạy, kế toán ghi sổ và xuất hoá đơn bằng tay như cũ.</div></div>';

  html += '<div class="sec">Giờ chạy</div><div class="card" style="padding:11px 12px">' +
    kmHangChip(['22:00', '22:30', '23:00', '23:15'].map(function (g) {
      return posChipNut('data-cdgio="' + g + '"', g, cdGio === g);
    }).join('')) +
    '<div style="display:flex;gap:8px;align-items:center;margin-top:9px">' +
    '<span style="font-size:12.5px;color:#6b7280">Giờ khác:</span>' +
    '<input class="tin" id="cdGioTay" type="time" value="' + h(cdGio) + '" style="flex:1;max-width:170px"></div></div>';

  html += '<div class="sec">Tự ghi sổ hoá đơn còn nháp</div><div class="card">' +
    (cdData.diem || []).map(function (d) {
      var on = cdGhiSo.indexOf(d.ma) >= 0;
      return cdDong('cdgs', d, on, d.ma === 'SALES'
        ? 'Đơn online Pancake và các sàn'
        : 'Bill bán tại quầy');
    }).join('') + '</div>';

  html += '<div class="sec">Tự xuất hoá đơn điện tử</div><div class="card">' +
    (cdData.diem || []).map(function (d) {
      var on = cdHddt.indexOf(d.ma) >= 0;
      return cdDong('cdhd', d, on, 'Nguồn đơn: ' + h((d.nguon || []).join(', ')));
    }).join('') + '</div>' +
    '<div style="font-size:11.5px;color:#98a2b3;padding:2px 14px 8px;line-height:1.6">' +
    'Chỉ hoá đơn <b>đã ghi sổ</b> mới được phát hành. Điểm bán nào chưa bật thì hoá đơn nằm yên trong hệ thống, không sang cơ quan thuế.</div>';

  // Cong tac goc nam ben m-invoice. Hai noi bat tat khac nhau chinh la cai
  // da gay ra vu 37 hoa don hom 10/08, nen o day phai noi thang trang thai
  // cua no chu khong de nguoi dung doan.
  if (!cdData.bat_hddt_chung || !cdData.bat_ky_chung) {
    html += '<div class="card" style="padding:12px 14px;background:#fff7ed;border:1px solid #fed7aa">' +
      '<b style="font-size:13.5px;color:#9a3412">Khoá gốc bên m-invoice đang chặn</b>' +
      '<div style="font-size:12.5px;color:#7c2d12;line-height:1.6;margin-top:3px">' +
      (!cdData.bat_hddt_chung
        ? 'Cấu hình m-invoice đang tắt phát hành, nên dù bật ở đây máy vẫn không đẩy hoá đơn nào sang cơ quan thuế.'
        : 'Cấu hình m-invoice đang tắt ký hàng loạt, nên hoá đơn sẽ phát hành rồi nằm ở trạng thái Chờ ký.') +
      ' Báo kế toán mở lại trong phần cài đặt m-invoice nếu muốn chạy đủ chuỗi.</div></div>';
  }

  if (cdData.nhat_ky) {
    html += '<div class="sec">Lần chạy gần nhất</div><div class="card" style="padding:12px 14px;font-size:13px;color:#374151;line-height:1.6">' +
      h(cdData.nhat_ky) + '</div>';
  }

  var b = frame('Cuối ngày', html, {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="cdChay" style="margin:0;flex:1">▶️ Chạy ngay</button>' +
      '<button class="btn" id="cdLuu" style="margin:0;flex:1">Lưu cấu hình</button></div>'
  });

  b.onclick = function (e) {
    var t = e.target.closest('[data-cdbat]');
    if (t) { cdBat = cdBat ? 0 : 1; return cdVe(); }
    t = e.target.closest('[data-cdgio]');
    if (t) { cdGio = t.getAttribute('data-cdgio'); return cdVe(); }
    t = e.target.closest('[data-cdgs]');
    if (t) { cdBoThem(cdGhiSo, t.getAttribute('data-cdgs')); return cdVe(); }
    t = e.target.closest('[data-cdhd]');
    if (t) { cdBoThem(cdHddt, t.getAttribute('data-cdhd')); return cdVe(); }
  };
  var og = document.getElementById('cdGioTay');
  if (og) og.onchange = function () { cdGio = og.value || cdGio; cdVe(); };

  document.getElementById('cdLuu').onclick = cdLuu;
  document.getElementById('cdChay').onclick = cdChay;
}

function cdDong(thuoc, d, on, mo) {
  return '<div ' + thuoc + '="' + h(d.ma) + '" style="display:flex;align-items:center;gap:11px;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
    '<div style="width:44px;height:26px;border-radius:99px;background:' + (on ? '#0d9488' : '#d5d9e0') + ';position:relative;flex:none;transition:background .15s">' +
    '<div style="position:absolute;top:3px;left:' + (on ? '21px' : '3px') + ';width:20px;height:20px;border-radius:50%;background:#fff;transition:left .15s"></div></div>' +
    '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(d.ten) + '</b>' +
    '<div style="font-size:11.5px;color:#98a2b3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + mo + '</div></div>' +
    '<span style="font-size:12.5px;font-weight:700;color:' + (on ? '#0f766e' : '#a0a6b4') + '">' + (on ? 'BẬT' : 'TẮT') + '</span></div>';
}

function cdBoThem(ds, ma) {
  var i = ds.indexOf(ma);
  if (i >= 0) ds.splice(i, 1); else ds.push(ma);
}

async function cdLuu() {
  busy(true);
  try {
    cdData = await api('vagabond.ban_hang.luu_cai_dat_cuoi_ngay', {
      bat: cdBat, gio: cdGio, ghi_so: JSON.stringify(cdGhiSo), hddt: JSON.stringify(cdHddt)
    });
    busy(false);
    toast('Đã lưu. Cuối ngày chạy lúc ' + (cdData.gio || cdGio) + '.', 3500);
    go(scrCaiDatCuoiNgay, true);
  } catch (e) { busy(false); window.alert((e && e.message) || 'Không lưu được'); }
}

async function cdChay() {
  if (!window.confirm('Chạy ngay chuỗi cuối ngày cho hôm nay?\n\nMáy sẽ ghi sổ hoá đơn còn nháp, phát hành hoá đơn điện tử rồi ký. Việc này không lùi lại được.')) return;
  busy(true);
  try {
    cdData = await api('vagabond.ban_hang.chay_cuoi_ngay_ngay_bay_gio', {});
    busy(false);
    window.alert(cdData.nhat_ky || 'Đã chạy xong.');
    go(scrCaiDatCuoiNgay, true);
  } catch (e) { busy(false); window.alert((e && e.message) || 'Chạy lỗi'); }
}


/* ===== Cai dat: danh sach diem ban (anh Viet 12/08/2026) =====

Truoc day ba diem ban duoc khai o BA CHO trong ma nguon, con dat ten khac
nhau cho cung mot diem. Mo chi nhanh thu tu la sua code roi deploy. Nay
khai o day, ca he doc chung mot noi. */

var dbDs = null, dbSuaDuoc = 0, dbMo = null, dbMoi = 0, dbNguonCoSan = [];

async function scrDiemBan() {
  frame('Điểm bán', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try {
    var kq = await api('vagabond.diem_ban.danh_sach', {});
    dbDs = kq.diem || []; dbSuaDuoc = kq.sua_duoc ? 1 : 0; dbNguonCoSan = kq.nguon_co_san || dbNguonCoSan;
  } catch (e) {
    frame('Điểm bán', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  dbVe();
}

function dbVe() {
  /* Them mot dong roi bam Back thi dong rong con nam lai trong bo nho, man
     danh sach ve mot the trong nhin rat kho hieu. Don o day. */
  if (dbMoi) { dbDs = (dbDs || []).filter(function (x) { return !!x.ma; }); dbMoi = 0; }
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">ĐIỂM BÁN</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Khai ở đây một lần, cả hệ dùng chung: màn tính tiền, chuỗi cuối ngày, khuyến mãi và báo cáo. ' +
    'Mở chi nhánh mới chỉ cần thêm một dòng, không phải sửa phần mềm.</div></div>';

  html += '<div class="card">' + (dbDs || []).map(function (d, i) {
    var phu = [];
    if (d.quay) phu.push('quầy ' + h(d.quay)); else phu.push('đơn online');
    if (d.dia_chi) phu.push(h(d.dia_chi));
    return '<div data-dbmo="' + i + '" style="display:flex;align-items:center;gap:11px;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
      '<div style="width:42px;height:42px;border-radius:11px;flex:none;background:' + (d.bat ? '#ecfdf5' : '#f3f4f6') +
      ';display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:' + (d.bat ? '#047857' : '#9ca3af') + '">' + h(d.ma) + '</div>' +
      '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(d.ten) + '</b>' +
      '<div style="font-size:11.5px;color:#98a2b3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + phu.join(' · ') + '</div>' +
      '<div style="font-size:11.5px;color:#6b7280;margin-top:2px">' + (d.nguon || []).length + ' nguồn đơn</div></div>' +
      '<span style="font-size:12px;font-weight:700;color:' + (d.bat ? '#0f766e' : '#a0a6b4') + '">' + (d.bat ? 'ĐANG DÙNG' : 'ĐÃ TẮT') + '</span>' +
      '<span style="color:#c8ccd4">›</span></div>';
  }).join('') + '</div>';

  html += '<div style="font-size:11.5px;color:#98a2b3;padding:8px 14px;line-height:1.6">' +
    'Điểm bán đã có hoá đơn thì không xoá được, chỉ tắt. Số liệu cũ vẫn xem lại được trong báo cáo.</div>';

  var b = frame('Điểm bán', html, dbSuaDuoc ? {
    footer: '<button class="btn gh" id="dbThem" style="margin:0">➕ Thêm điểm bán</button>'
  } : null);

  b.onclick = function (e) {
    var t = e.target.closest('[data-dbmo]');
    if (t) { dbMo = +t.getAttribute('data-dbmo'); go(scrDiemBanSua); }
  };
  var n = document.getElementById('dbThem');
  if (n) n.onclick = function () {
    dbDs.push({ ma: '', ten: '', ten_ngan: '', quay: '', dia_chi: '', mst: '', ky_hieu: '', nguon: [], bat: 1, thu_tu: dbDs.length + 1 });
    dbMo = dbDs.length - 1;
    dbMoi = 1;
    go(scrDiemBanSua);
  };
}

function scrDiemBanSua() {
  var d = (dbDs || [])[dbMo];
  if (!d) return go(scrDiemBan, true);
  var moi = !d.ma;
  var o = function (nhan, id, gt, mo, kieu) {
    return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="font-size:12px;color:#6b7280;margin-bottom:4px">' + nhan + '</div>' +
      '<input class="tin" id="' + id + '" type="' + (kieu || 'text') + '" value="' + h(gt || '') + '" style="width:100%;margin:0">' +
      (mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo + '</div>' : '') + '</div>';
  };

  var html = '<div class="card">' +
    o('Mã điểm bán', 'dbMa', d.ma, 'Chữ không dấu và số, ví dụ SALES, TCV, NVHTN. Mã đi vào báo cáo nên đặt xong thì đừng đổi.') +
    o('Tên đầy đủ', 'dbTen', d.ten, 'Hiện trên màn Cài đặt và chuỗi cuối ngày.') +
    o('Tên ngắn', 'dbTenNgan', d.ten_ngan, 'Hiện trên chip và cột báo cáo cho gọn.') +
    o('Địa chỉ', 'dbDiaChi', d.dia_chi) +
    o('Mã số thuế chi nhánh', 'dbMst', d.mst, 'Để trống thì dùng mã số thuế công ty.') +
    o('Ký hiệu hoá đơn điện tử', 'dbKyHieu', d.ky_hieu, 'Để trống thì dùng ký hiệu chung.') +
    '</div>';

  /* Khong cho nhap ma quay rieng: ca he quy hoa don ve diem ban bang cach
     doc vgb_quay roi tra theo MA DIEM. De hai thu lech nhau la bao cao ra
     dong 0 dong con doanh thu that gom vao mot khoa khong ten. */
  html += '<div class="sec">Loại điểm bán</div><div class="card" style="padding:11px 12px">' +
    kmHangChip(
      posChipNut('data-dbloai="1"', '🏬 Bán tại quầy', !!d.co_quay) +
      posChipNut('data-dbloai="0"', '🛵 Nhận đơn online', !d.co_quay)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    (d.co_quay
      ? 'Mã quầy dùng đúng mã điểm bán là <b>' + h(d.ma || '(chưa đặt mã)') + '</b>.'
      : 'Đơn online không mang mã quầy. Cả hệ chỉ có <b>một</b> điểm nhận đơn online.') +
    '</div></div>';

  html += '<div class="sec">Nguồn đơn thuộc điểm bán này</div><div class="card" style="padding:12px">' +
    dbChipNguon(d) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:10px;line-height:1.6">' +
    'Một nguồn chỉ được thuộc một điểm bán - gán cho hai nơi là hoá đơn điện tử xuất hai lần. ' +
    'Nguồn đang thuộc điểm khác thì hiện mờ, bấm vào máy nói rõ nó đang ở đâu.</div></div>';

  html += '<div class="card" style="padding:11px 12px">' + kmHangChip(
    posChipNut('data-dbbat="1"', d.bat ? '● Đang dùng' : '○ Đã tắt', !!d.bat)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px">Tắt thì điểm bán không hiện ở màn tính tiền và chuỗi cuối ngày nữa, nhưng số liệu cũ vẫn còn nguyên trong báo cáo.</div></div>';

  var b = frame(moi ? 'Điểm bán mới' : ('Điểm bán ' + d.ma), html, {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="dbBo" style="margin:0;flex:0 0 34%;color:#b3261e;border-color:#fecaca">Bỏ dòng này</button>' +
      '<button class="btn" id="dbLuu" style="margin:0;flex:1">💾 Lưu</button></div>'
  });

  b.onclick = async function (e) {
    if (e.target.closest('[data-dbbat]')) { dbDoc(); d.bat = d.bat ? 0 : 1; return go(scrDiemBanSua, true); }
    var t = e.target.closest('[data-dbloai]');
    if (t) { dbDoc(); d.co_quay = t.getAttribute('data-dbloai') === '1' ? 1 : 0; return go(scrDiemBanSua, true); }
    t = e.target.closest('[data-dbng]');
    if (t) {
      dbDoc();
      if (dbBamNguon(t.getAttribute('data-dbng'), d)) go(scrDiemBanSua, true);
      return;
    }
    if (e.target.closest('[data-dbngmoi]')) {
      dbDoc();
      var v = await promptSheet('Tên nguồn đơn mới',
        'Gõ đúng từng chữ như nguồn đơn ghi trên hoá đơn, ví dụ Tại chỗ - Quận 4');
      if (v === null) return;
      v = v.trim();
      if (!v) return;
      if ((d.nguon || []).indexOf(v) >= 0) return toast('Nguồn này đã có sẵn rồi.');
      if (dbBamNguon(v, d)) go(scrDiemBanSua, true);
      return;
    }
  };
  /* Phai boc lai: gan thang dbLuu thi onclick truyen su kien vao tham so
     daBo, luon truthy, dbDoc() khong bao gio chay - bam Luu la mat sach
     thay doi ma man hinh van bao "Da luu". */
  document.getElementById('dbLuu').onclick = function () { dbLuu(); };
  document.getElementById('dbBo').onclick = async function () {
    var ok = await confirmSheet('Bỏ điểm bán ' + (d.ma || 'mới') + '?',
      'Nếu điểm này đã có hoá đơn thì máy chủ sẽ chặn - lúc đó anh chị tắt nó đi thay vì bỏ.', 'Bỏ dòng này', true);
    if (!ok) return;
    dbDs.splice(dbMo, 1);
    dbLuu(1);
  };
}

function dbDoc() {
  var d = (dbDs || [])[dbMo];
  if (!d) return;
  var v = function (id) { var e = document.getElementById(id); return e ? e.value.trim() : ''; };
  d.ma = v('dbMa').toUpperCase();
  d.ten = v('dbTen');
  d.ten_ngan = v('dbTenNgan');
  d.quay = d.co_quay ? d.ma : '';
  d.dia_chi = v('dbDiaChi');
  d.mst = v('dbMst');
  d.ky_hieu = v('dbKyHieu');
  /* Nguon don gio la chip bam chon, khong con o go tay - dbDoc chi hut
     may o input, khong duoc dung vao d.nguon. */
  d.nguon = d.nguon || [];
}

async function dbLuu(daBo) {
  if (!daBo) dbDoc();
  busy(true);
  try {
    var kq = await api('vagabond.diem_ban.luu', { diem: JSON.stringify(dbDs) });
    dbDs = kq.diem || []; dbSuaDuoc = kq.sua_duoc ? 1 : 0; dbNguonCoSan = kq.nguon_co_san || dbNguonCoSan;
    busy(false);
    toast('Đã lưu danh sách điểm bán.', 3000);
    dbMoi = 0;
    back();
  } catch (e) {
    busy(false);
    /* May chu chan thi phai doc lai danh sach that, khong de man hinh giu
       ban sai trong bo nho roi lan sau luu de len. */
    window.alert((e && e.message) || 'Không lưu được');
    /* May chu chan thi doc lai danh sach that. Khong quay ve ngay: nguoi
       dung con dang sua do, phai o lai de sua tiep cho dung. */
    try {
      var lai = await api('vagabond.diem_ban.danh_sach', {});
      dbDs = lai.diem || []; dbSuaDuoc = lai.sua_duoc ? 1 : 0; dbNguonCoSan = lai.nguon_co_san || dbNguonCoSan;
      if (dbMo >= dbDs.length) dbMo = Math.max(0, dbDs.length - 1);
    } catch (e2) { }
    go(scrDiemBanSua, true);
  }
}


/* ===== Cai dat: khoa so theo ngay (anh Viet 12/08/2026) =====

Hoc tu Fabi muc 3.7. Truoc day hoa don da ghi so van sua duoc vo thoi han
mien co ma OTP - nghia la so lieu thang truoc, da nop thue, da doi soat
voi ngan hang, van doi duoc ma khong ai hay. */

var ksData = null, ksNgay = 0, ksDen = '';

async function scrKhoaSo() {
  frame('Khoá sổ', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try { ksData = await api('vagabond.chung_tu.cai_dat_khoa_so', {}); }
  catch (e) {
    frame('Khoá sổ', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  ksNgay = ksData.so_ngay || 0;
  ksDen = ksData.den || '';
  ksVe();
}

function ksVe() {
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">KHOÁ SỔ</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Chứng từ của ngày đã khoá thì không ghi sổ, không huỷ, không sửa được nữa - ' +
    'trên app hay trên máy tính đều vậy. Cần sửa một tờ cũ thì kế toán mở khoá riêng tờ đó, ' +
    'máy ghi lại lý do và tên người mở.</div></div>';

  if (ksData.ngay_khoa) {
    html += '<div class="card" style="padding:12px 14px;background:#ecfdf5;border:1px solid #a7f3d0">' +
      '<b style="font-size:14.5px;color:#047857">🔒 Đang khoá đến hết ' + ngayNgan(ksData.ngay_khoa) + '</b>' +
      '<div style="font-size:12.5px;color:#065f46;margin-top:3px;line-height:1.6">' +
      'Mọi chứng từ từ ngày đó trở về trước đều đã chốt.</div></div>';
  } else {
    html += '<div class="card" style="padding:12px 14px;background:#fff7ed;border:1px solid #fed7aa">' +
      '<b style="font-size:14.5px;color:#9a3412">⚠️ Chưa khoá gì</b>' +
      '<div style="font-size:12.5px;color:#7c2d12;margin-top:3px;line-height:1.6">' +
      'Hoá đơn của tháng trước vẫn sửa và huỷ được như thường.</div></div>';
  }

  html += '<div class="sec">Tự khoá sau bao nhiêu ngày</div><div class="card" style="padding:11px 12px">' +
    kmHangChip([
      { v: 0, t: 'Không khoá' }, { v: 3, t: '3 ngày' }, { v: 7, t: '7 ngày' },
      { v: 15, t: '15 ngày' }, { v: 31, t: '31 ngày' }
    ].map(function (x) {
      return posChipNut('data-ksn="' + x.v + '"', x.t, ksNgay === x.v);
    }).join('')) +
    '<div style="display:flex;gap:8px;align-items:center;margin-top:9px">' +
    '<span style="font-size:12.5px;color:#6b7280">Số ngày khác:</span>' +
    '<input class="tin" id="ksNgayTay" type="number" min="0" max="3650" value="' + ksNgay + '" style="flex:1;max-width:120px">' +
    '</div>' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    'Đặt 3 ngày nghĩa là hôm nay không đụng được vào chứng từ của 3 ngày trước trở về trước. ' +
    'Đủ để kế toán xử lý sai sót trong tuần mà vẫn chặn việc sửa số của kỳ đã chốt.</div></div>';

  html += '<div class="sec">Mốc khoá cứng</div><div class="card" style="padding:11px 12px">' +
    '<input class="tin" id="ksDenTay" type="date" value="' + h(ksDen) + '" max="' + ksHomQua() + '" style="width:100%;margin:0">' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    'Dùng sau khi chốt sổ một kỳ: đặt ngày cuối kỳ vào đây thì kỳ đó khoá vĩnh viễn, ' +
    'không trôi theo ngày như ô trên. Để trống nếu chưa cần.</div></div>';

  if (ksData.so_to_dang_mo) {
    html += '<div class="card" style="padding:12px 14px;background:#fef2f2;border:1px solid #fecaca">' +
      '<b style="font-size:14px;color:#991b1b">Đang có ' + ksData.so_to_dang_mo + ' hoá đơn được mở khoá</b>' +
      '<div style="font-size:12.5px;color:#7f1d1d;margin-top:3px;line-height:1.6">' +
      'Sửa xong nhớ đóng lại, không thì mấy tờ đó vẫn sửa được mãi.</div></div>';
  }

  html += '<div style="font-size:11.5px;color:#98a2b3;padding:8px 14px;line-height:1.6">' +
    'Áp dụng cho: ' + h((ksData.loai || []).join(', ')) + '.</div>';

  var b = frame('Khoá sổ', html, ksData.sua_duoc ? {
    footer: '<button class="btn" id="ksLuu" style="margin:0">💾 Lưu cấu hình khoá sổ</button>'
  } : null);

  b.onclick = function (e) {
    var t = e.target.closest('[data-ksn]');
    if (t) { ksDoc(); ksNgay = +t.getAttribute('data-ksn'); ksVe(); }
  };
  var n = document.getElementById('ksLuu');
  if (n) n.onclick = function () { ksLuu(); };
}

function ksHomQua() {
  /* Moc cung khong duoc dat vao hom nay: dat vao la khoa luon so cua hom
     nay, quay khong chot duoc bill nao. */
  var d = new Date(); d.setDate(d.getDate() - 1);
  var s2 = function (n) { return (n < 10 ? '0' : '') + n; };
  return d.getFullYear() + '-' + s2(d.getMonth() + 1) + '-' + s2(d.getDate());
}

function ksDoc() {
  var a = document.getElementById('ksNgayTay');
  var c = document.getElementById('ksDenTay');
  if (a && a.value !== '') ksNgay = Math.max(0, Math.min(3650, +a.value || 0));
  if (c) ksDen = c.value || '';
}

async function ksLuu() {
  ksDoc();
  var nhac = ksNgay === 0 && !ksDen
    ? 'Bỏ khoá hoàn toàn? Hoá đơn của mọi ngày sẽ sửa và huỷ được lại như cũ.'
    : 'Khoá sổ' + (ksNgay ? ' sau ' + ksNgay + ' ngày' : '') + (ksDen ? ', mốc cứng ' + ngayNgan(ksDen) : '') + '?';
  var ok = await confirmSheet('Lưu cấu hình khoá sổ', nhac + '\nÁp dụng ngay cho cả app lẫn máy tính.', 'Lưu', ksNgay === 0 && !ksDen);
  if (!ok) return;
  busy(true);
  try {
    ksData = await api('vagabond.chung_tu.luu_khoa_so', { so_ngay: ksNgay, den: ksDen });
    ksNgay = ksData.so_ngay || 0; ksDen = ksData.den || '';
    busy(false);
    toast(ksData.ngay_khoa ? ('Đã khoá đến hết ' + ngayNgan(ksData.ngay_khoa)) : 'Đã bỏ khoá sổ.', 3500);
    ksVe();
  } catch (e) { busy(false); window.alert((e && e.message) || 'Không lưu được'); }
}


/* ===== Cai dat: phuong thuc thanh toan (anh Viet 12/08/2026) =====

Truoc day mot phuong thuc phai khai o SAU cho trong ma nguon: bang tham
chieu, danh sach cho quay, danh sach cho don online, hai danh sach tien
chua ve, va bang ma gui co quan thue. Them mot may ca the moi la sua sau
cho roi deploy - quen mot cho thi lech so ma khong ai bao loi ngay. */

var ptDs = null, ptSuaDuoc = 0, ptTienVe = [], ptMo = null, ptMoi = 0;

async function scrPtThanhToan() {
  frame('Phương thức thanh toán', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try {
    var kq = await api('vagabond.pt_thanh_toan.danh_sach', {});
    ptDs = kq.pt || []; ptSuaDuoc = kq.sua_duoc ? 1 : 0; ptTienVe = kq.tien_ve || [];
  } catch (e) {
    frame('Phương thức thanh toán', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  ptVe();
}

function ptNhanTienVe(k) {
  for (var i = 0; i < ptTienVe.length; i++) if (ptTienVe[i].k === k) return ptTienVe[i].ten;
  return k;
}

function ptVe() {
  if (ptMoi) { ptDs = (ptDs || []).filter(function (x) { return !!x.ten; }); ptMoi = 0; }
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">PHƯƠNG THỨC THANH TOÁN</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Khai ở đây một lần, cả hệ dùng chung: màn tính tiền tại quầy, đơn online, màn chốt ca ' +
    'và mã hình thức thanh toán gửi sang cơ quan thuế.</div></div>';

  html += '<div class="card">' + (ptDs || []).map(function (d, i) {
    var noi = [];
    if (d.quay) noi.push('quầy');
    if (d.online) noi.push('đơn online');
    if (!noi.length) noi.push('theo nguồn đơn của sàn');
    return '<div data-ptmo="' + i + '" style="display:flex;align-items:center;gap:11px;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
      (d.lg
        ? '<img src="' + h(d.lg) + '" style="width:38px;height:38px;object-fit:contain;flex:none" onerror="this.style.visibility=\'hidden\'">'
        : '<div style="width:38px;height:38px;flex:none;display:flex;align-items:center;justify-content:center;font-size:22px">' + (d.ic || '💳') + '</div>') +
      '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(d.ten) + '</b>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + noi.join(' · ') +
      (d.bat ? ' · bắt buộc nhập mã' : '') + '</div>' +
      '<div style="font-size:11.5px;color:#6b7280;margin-top:2px">' + h(ptNhanTienVe(d.tien_ve)) +
      (d.minvoice ? ' · thuế ' + h(d.minvoice) : '') + '</div></div>' +
      '<span style="font-size:12px;font-weight:700;color:' + (d.dung ? '#0f766e' : '#a0a6b4') + '">' + (d.dung ? 'ĐANG DÙNG' : 'ĐÃ TẮT') + '</span>' +
      '<span style="color:#c8ccd4">›</span></div>';
  }).join('') + '</div>';

  html += '<div style="font-size:11.5px;color:#98a2b3;padding:8px 14px;line-height:1.6">' +
    'Phương thức đã có hoá đơn thì không bỏ khỏi danh sách được, chỉ tắt. Hoá đơn cũ vẫn đọc được.</div>';

  var b = frame('Phương thức thanh toán', html, ptSuaDuoc ? {
    footer: '<button class="btn gh" id="ptThem" style="margin:0">➕ Thêm phương thức</button>'
  } : null);

  b.onclick = function (e) {
    var t = e.target.closest('[data-ptmo]');
    if (t) { ptMo = +t.getAttribute('data-ptmo'); go(scrPtSua); }
  };
  var n = document.getElementById('ptThem');
  if (n) n.onclick = function () {
    ptDs.push({ ten: '', lg: '', ic: '💳', quay: 1, online: 0, bat: 0, nhan: '', vd: '', mau: '', loi: '', tien_ve: 'ngay', minvoice: 'CK', dung: 1, thu_tu: ptDs.length + 1 });
    ptMo = ptDs.length - 1; ptMoi = 1;
    go(scrPtSua);
  };
}

function scrPtSua() {
  var d = (ptDs || [])[ptMo];
  if (!d) return go(scrPtThanhToan, true);
  var o = function (nhan, id, gt, mo) {
    return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="font-size:12px;color:#6b7280;margin-bottom:4px">' + nhan + '</div>' +
      '<input class="tin" id="' + id + '" value="' + h(gt || '') + '" style="width:100%;margin:0">' +
      (mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo + '</div>' : '') + '</div>';
  };

  var html = '<div class="card">' +
    o('Tên phương thức', 'ptTen', d.ten, 'Tên này ghi thẳng vào từng hoá đơn, đặt xong thì đừng đổi.') +
    o('Đường dẫn logo', 'ptLg', d.lg, 'Để trống thì dùng biểu tượng bên dưới.') +
    o('Biểu tượng', 'ptIc', d.ic, 'Dùng khi không có logo.') +
    '</div>';

  html += '<div class="sec">Hiện ở đâu</div><div class="card" style="padding:11px 12px">' +
    kmHangChip(
      posChipNut('data-ptq="1"', '🏬 Màn tính tiền tại quầy', !!d.quay) +
      posChipNut('data-pto="1"', '🛵 Đơn online', !!d.online)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    'Tắt cả hai nghĩa là phương thức này đi theo nguồn đơn của sàn, không hiện ra cho ai chọn tay.</div></div>';

  html += '<div class="sec">Tiền về lúc nào</div><div class="card" style="padding:11px 12px">' +
    kmHangChip(ptTienVe.map(function (x) {
      return posChipNut('data-pttv="' + h(x.k) + '"', x.ten, d.tien_ve === x.k);
    }).join('')) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    'Màn Chốt ca tách riêng hai loại sau để thu ngân đếm tiền mặt không bị lệch.</div></div>';

  html += '<div class="sec">Mã tham chiếu đối soát</div><div class="card">' +
    '<div style="padding:11px 12px;border-bottom:1px solid #f2f4f7">' +
    kmHangChip(posChipNut('data-ptbat="1"', d.bat ? '● Bắt buộc nhập' : '○ Không bắt buộc', !!d.bat)) + '</div>' +
    o('Nhãn ô nhập', 'ptNhan', d.nhan, 'Câu hiện trên màn cho thu ngân biết phải gõ gì.') +
    o('Ví dụ', 'ptVd', d.vd) +
    o('Mẫu kiểm định dạng', 'ptMau', d.mau, 'Để trống thì không kiểm. Gõ sai mẫu thì máy chặn ngay lúc lưu cấu hình.') +
    o('Câu báo khi sai dạng', 'ptLoi', d.loi) +
    '</div>';

  html += '<div class="sec">Gửi sang cơ quan thuế</div><div class="card" style="padding:11px 12px">' +
    kmHangChip(['TM', 'CK', 'TM/CK', ''].map(function (m) {
      return posChipNut('data-ptmi="' + m + '"', m || 'Không gửi', (d.minvoice || '') === m);
    }).join('')) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    'TM là tiền mặt, CK là chuyển khoản. Ghi sai thì tờ hoá đơn điện tử sai hình thức thanh toán.</div></div>';

  html += '<div class="card" style="padding:11px 12px">' +
    kmHangChip(posChipNut('data-ptdung="1"', d.dung ? '● Đang dùng' : '○ Đã tắt', !!d.dung)) + '</div>';

  var b = frame(d.ten ? ('Sửa ' + d.ten) : 'Phương thức mới', html, {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="ptBo" style="margin:0;flex:0 0 34%;color:#b3261e;border-color:#fecaca">Bỏ dòng này</button>' +
      '<button class="btn" id="ptLuu" style="margin:0;flex:1">💾 Lưu</button></div>'
  });

  b.onclick = function (e) {
    var t;
    if (e.target.closest('[data-ptq]')) { ptDoc(); d.quay = d.quay ? 0 : 1; return go(scrPtSua, true); }
    if (e.target.closest('[data-pto]')) { ptDoc(); d.online = d.online ? 0 : 1; return go(scrPtSua, true); }
    if (e.target.closest('[data-ptbat]')) { ptDoc(); d.bat = d.bat ? 0 : 1; return go(scrPtSua, true); }
    if (e.target.closest('[data-ptdung]')) { ptDoc(); d.dung = d.dung ? 0 : 1; return go(scrPtSua, true); }
    t = e.target.closest('[data-pttv]');
    if (t) { ptDoc(); d.tien_ve = t.getAttribute('data-pttv'); return go(scrPtSua, true); }
    t = e.target.closest('[data-ptmi]');
    if (t) { ptDoc(); d.minvoice = t.getAttribute('data-ptmi'); return go(scrPtSua, true); }
  };
  document.getElementById('ptLuu').onclick = function () { ptLuu(); };
  document.getElementById('ptBo').onclick = async function () {
    var ok = await confirmSheet('Bỏ phương thức ' + (d.ten || 'mới') + '?',
      'Nếu phương thức này đã có hoá đơn thì máy chủ sẽ chặn - lúc đó anh chị tắt nó đi thay vì bỏ.', 'Bỏ dòng này', true);
    if (!ok) return;
    ptDs.splice(ptMo, 1);
    ptLuu(1);
  };
}

function ptDoc() {
  var d = (ptDs || [])[ptMo];
  if (!d) return;
  var v = function (id) { var e = document.getElementById(id); return e ? e.value.trim() : null; };
  var g;
  if ((g = v('ptTen')) !== null) d.ten = g;
  if ((g = v('ptLg')) !== null) d.lg = g;
  if ((g = v('ptIc')) !== null) d.ic = g;
  if ((g = v('ptNhan')) !== null) d.nhan = g;
  if ((g = v('ptVd')) !== null) d.vd = g;
  if ((g = v('ptMau')) !== null) d.mau = g;
  if ((g = v('ptLoi')) !== null) d.loi = g;
}

async function ptLuu(daBo) {
  if (!daBo) ptDoc();
  busy(true);
  try {
    var kq = await api('vagabond.pt_thanh_toan.luu', { pt: JSON.stringify(ptDs) });
    ptDs = kq.pt || []; ptSuaDuoc = kq.sua_duoc ? 1 : 0;
    busy(false);
    toast('Đã lưu phương thức thanh toán.', 3000);
    ptMoi = 0;
    back();
  } catch (e) {
    busy(false);
    window.alert((e && e.message) || 'Không lưu được');
    try {
      var lai = await api('vagabond.pt_thanh_toan.danh_sach', {});
      ptDs = lai.pt || []; ptSuaDuoc = lai.sua_duoc ? 1 : 0;
      if (ptMo >= ptDs.length) ptMo = Math.max(0, ptDs.length - 1);
    } catch (e2) { }
    go(scrPtSua, true);
  }
}

/* ---------- Cai dat: Quyen tai quay (anh Viet 12/08/2026) ----------
   Hoc theo ba muc quyen bo mon cua Fabi. Man nay chi doi mot cai cong
   tac, nhung doi no la doi cach ca quay lam viec nen phai noi that ro
   moi muc nghia la gi, va noi luon dieu gi KHONG doi. */
var qqData = null, qqChon = '';

async function scrQuyenQuay() {
  frame('Quyền tại quầy', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try { qqData = await api('vagabond.quyen_quay.cai_dat', {}); }
  catch (e) {
    frame('Quyền tại quầy', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  qqChon = qqData.muc || 'duyet';
  qqVe();
}

function qqVe() {
  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">QUYỀN BỎ MÓN CỦA THU NGÂN</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Mốc để tính là lúc bấm <b>In tạm tính</b>: từ đó trở đi tờ phiếu đã nằm trong tay ' +
    'khách, món biến mất khỏi bill là lệch với tờ khách đang cầm.</div></div>';

  html += '<div class="card">' + (qqData.ds || []).map(function (x) {
    var on = qqChon === x.k;
    return '<div data-qqm="' + h(x.k) + '" style="display:flex;gap:11px;padding:13px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer;background:' + (on ? '#f0fdfa' : '#fff') + '">' +
      '<div style="flex:none;font-size:19px;line-height:1.2;color:' + (on ? '#0f766e' : '#c8ccd4') + '">' + (on ? '◉' : '○') + '</div>' +
      '<div style="flex:1;min-width:0">' +
      '<b style="font-size:14.5px;color:' + (on ? '#0f766e' : '#101828') + '">' + h(x.ten) + '</b>' +
      '<div style="font-size:12.5px;color:#6b7280;margin-top:3px;line-height:1.6">' + h(x.mo) + '</div>' +
      '</div></div>';
  }).join('') + '</div>';

  html += '<div class="card" style="padding:12px 14px;background:#f8fafc">' +
    '<div style="font-size:12px;color:#98a2b3">MỨC NÀO CŨNG KHÔNG ĐỔI</div>' +
    '<div style="font-size:12.5px;color:#475467;line-height:1.7;margin-top:4px">' +
    '· Huỷ nguyên một bill vẫn luôn cần mã OTP của quản lý ca.<br>' +
    '· Hoá đơn đã ghi sổ thì không sửa được món ở quầy, mức nào cũng vậy.<br>' +
    '· Mọi lần sửa đều ghi lại tên người sửa vào lịch sử hoá đơn.<br>' +
    '· Quản lý tự thao tác thì không phải gõ mã.</div></div>';

  var b = frame('Quyền tại quầy', html, qqData.sua_duoc ? {
    footer: '<button class="btn" id="qqLuu" style="margin:0">💾 Lưu mức quyền</button>'
  } : null);

  if (!qqData.sua_duoc) return;
  b.onclick = function (e) {
    var t = e.target.closest('[data-qqm]');
    if (t) { qqChon = t.getAttribute('data-qqm'); return qqVe(); }
  };
  document.getElementById('qqLuu').onclick = function () { qqLuu(); };
}

async function qqLuu() {
  busy(true);
  try {
    qqData = await api('vagabond.quyen_quay.luu', { muc_moi: qqChon });
    qqChon = qqData.muc || 'duyet';
    CFGBH = null; /* man tinh tien phai doc lai muc quyen moi */
    busy(false);
    toast('Đã lưu mức quyền tại quầy.', 3000);
    qqVe();
  } catch (e) {
    busy(false);
    window.alert((e && e.message) || 'Không lưu được');
  }
}

/* ---------- Chip chon nguon don cho man Diem ban (anh Viet 12/08/2026) ----------
   Truoc day la o go tay tung dong. Go thieu mot dau la nguon do khong khop
   voi hoa don nao ca, ma khong ai bao loi - hoa don cu the nam ngoai moi
   diem ban, cuoi ngay khong ai ghi so cho no. */
/* Nguon nay dang thuoc diem nao. Tinh tren danh sach dang sua trong bo nho
   chu khong tinh tren ban may chu doc luc mo man: go mot nguon khoi diem A
   roi gan sang diem B la viec rat thuong, ban cu se chan nham. */
function dbChuNguon(v, d) {
  var ds = dbDs || [];
  for (var i = 0; i < ds.length; i++) {
    if (ds[i] === d) continue;
    if ((ds[i].nguon || []).indexOf(v) >= 0) return ds[i].ma || '(chưa đặt mã)';
  }
  return '';
}

function dbChipNguon(d) {
  var dang = (d.nguon || []).slice();
  var co = (dbNguonCoSan || []).slice();

  /* Goi y "Tai cho - X" va "Mang ve - X" theo ten diem, chi cho diem co
     quay. Hai nguon nay sinh theo ten nen khong nam san trong bang mau. */
  if (d.co_quay) {
    var ten = (d.ten_ngan || d.ten || '').trim();
    if (ten) {
      ['Tại chỗ - ' + ten, 'Mang về - ' + ten].forEach(function (g) {
        if (!co.some(function (x) { return x.v === g; })) {
          co.push({ v: g, lg: '', ic: g.indexOf('Tại chỗ') === 0 ? '🏬' : '🥡' });
        }
      });
    }
  }
  /* Nguon dang gan cho diem nay ma bang tra chua co (vua go tay xong) */
  dang.forEach(function (n) {
    if (!co.some(function (x) { return x.v === n; })) co.push({ v: n, lg: '', ic: '🧾' });
  });

  var html = co.map(function (x) {
    var on = dang.indexOf(x.v) >= 0;
    /* Nguon dang thuoc diem KHAC thi hien mo, bam vao bao ro no o dau.
       Chan o day cho nguoi dung thay ngay, con may chu van kiem lai. */
    var chu = dbChuNguon(x.v, d);
    var ket = !on && !!chu;
    var vien = on ? '#0d9488' : (ket ? '#e5e7eb' : '#d7dce5');
    var nen = on ? '#0d9488' : (ket ? '#f8fafc' : '#fff');
    var mau = on ? '#fff' : (ket ? '#a0a6b4' : '#374151');
    var anh = x.lg
      ? '<img src="' + h(x.lg) + '" style="height:17px;border-radius:3px;background:#fff;padding:1px 2px" onerror="this.style.display=\'none\'">'
      : '<span style="font-size:15px">' + (x.ic || '🧾') + '</span>';
    return '<button data-dbng="' + h(x.v) + '" style="display:inline-flex;align-items:center;gap:7px;' +
      'border:1.5px solid ' + vien + ';background:' + nen + ';color:' + mau +
      ';border-radius:999px;padding:8px 14px;font-size:13.5px;font-weight:' + (on ? '800' : '600') +
      ';cursor:pointer;white-space:nowrap;line-height:1.2">' + anh + h(x.v) +
      (ket ? '<span style="font-size:11px;font-weight:600"> · ' + h(chu) + '</span>' : '') + '</button>';
  }).join('');

  html += '<button data-dbngmoi="1" style="display:inline-flex;align-items:center;gap:6px;border:1.5px dashed #b9c0cc;' +
    'background:#fff;color:#475467;border-radius:999px;padding:8px 14px;font-size:13.5px;font-weight:600;' +
    'cursor:pointer;white-space:nowrap;line-height:1.2">➕ Nguồn khác</button>';

  return kmHangChip(html) +
    (dang.length
      ? ''
      : '<div style="font-size:12px;color:#b45309;margin-top:9px;font-weight:600">Chưa chọn nguồn nào. Điểm bán không có nguồn thì không nhận được hoá đơn nào.</div>');
}

/* Bam mot chip nguon: gan vao diem dang sua, hoac go ra. */
function dbBamNguon(v, d) {
  var i = (d.nguon || []).indexOf(v);
  if (i >= 0) { d.nguon.splice(i, 1); return 1; }
  var chu = dbChuNguon(v, d);
  if (chu) {
    toast('Nguồn "' + v + '" đang thuộc điểm ' + chu + '. Gỡ khỏi điểm đó trước rồi hãy gán sang đây.', 5000);
    return 0;
  }
  d.nguon = (d.nguon || []).concat([v]);
  return 1;
}

/* ---------- Cai dat: Hang thanh vien (anh Viet 12/08/2026) ----------
   Ba hang chay tu dong theo chi tieu (EXPLORER, VOYAGER, VAGABONDER) va
   cac hang gan tay (AMBASSADOR, FAMILY). Moi hang co muc giam gia va ty le
   tich diem rieng; 1 diem = 1 dong, giu dung quy uoc cu ben Fabi de khach
   khong phai doi thoi quen. */
var htData = null, htDs = [], htMo = null, htMoi = 0, htSuaDuoc = 0;

async function scrHangKhach() {
  frame('Hạng thành viên', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc bảng hạng...</div></div>');
  try {
    htData = await api('vagabond.khach_hang.cai_dat_hang', {});
    htDs = htData.hang || []; htSuaDuoc = htData.sua_duoc ? 1 : 0;
  } catch (e) {
    frame('Hạng thành viên', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  htVe();
}

function htTien(n) { return money(n) + ' đ'; }

function htVe() {
  var theoCt = htDs.filter(function (x) { return (x.loai || 'Theo chi tieu') === 'Theo chi tieu'; });
  var moc = {}, trung = '';
  theoCt.forEach(function (x) {
    var k = String(x.chi_tieu_tu || 0);
    if (moc[k]) trung = moc[k] + ' và ' + x.ten_hang;
    moc[k] = x.ten_hang;
  });

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">HẠNG THÀNH VIÊN</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Hạng <b>theo chi tiêu</b> máy tự xét lại mỗi đêm theo tiền khách đã mua trong kỳ. ' +
    'Hạng <b>gán tay</b> thì máy không bao giờ đụng vào: nhân viên, đại sứ, người nhà.</div></div>';

  if (trung) {
    html += '<div class="card" style="padding:12px 14px;background:#fef2f2;border:1px solid #fecaca">' +
      '<b style="font-size:14.5px;color:#b42318">⚠️ Chưa chạy xét lại được</b>' +
      '<div style="font-size:12.5px;color:#7f1d1d;margin-top:3px;line-height:1.6">' +
      'Hạng ' + h(trung) + ' đang cùng một mức chi tiêu nên máy không biết xếp khách vào đâu. ' +
      'Đặt mốc khác nhau cho từng hạng rồi lưu lại.</div></div>';
  }

  html += '<div class="card">' + htDs.map(function (d, i) {
    var tay = (d.loai || 'Theo chi tieu') === 'Gan tay';
    var phu = [];
    if (tay) phu.push('gán tay');
    else phu.push('từ ' + htTien(d.chi_tieu_tu || 0));
    if (d.giam_gia) phu.push('giảm ' + d.giam_gia + '%');
    phu.push(d.tich_diem ? ('tích ' + d.tich_diem + '%') : 'không tích điểm');
    return '<div data-htmo="' + i + '" style="display:flex;align-items:center;gap:11px;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
      '<div style="width:34px;height:34px;flex:none;border-radius:10px;display:flex;align-items:center;justify-content:center;' +
      'background:' + (tay ? '#fef3c7' : '#ccfbf1') + ';font-size:17px">' + (tay ? '✋' : '📈') + '</div>' +
      '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(d.ten_hang) + '</b>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + h(phu.join(' · ')) + '</div>' +
      '<div style="font-size:11.5px;color:#6b7280;margin-top:2px">' + money(d.so_khach || 0) + ' khách</div></div>' +
      '<span style="font-size:12px;font-weight:700;color:' + (d.bat ? '#0f766e' : '#a0a6b4') + '">' + (d.bat ? 'ĐANG DÙNG' : 'ĐÃ TẮT') + '</span>' +
      '<span style="color:#c8ccd4">›</span></div>';
  }).join('') + '</div>';

  html += '<div style="font-size:11.5px;color:#98a2b3;padding:8px 14px;line-height:1.6">' +
    money(htData.chua_xep || 0) + ' khách chưa xếp hạng. Tích điểm tính trên giá trị hoá đơn, 1 điểm bằng 1 đồng.</div>';

  html += '<div class="card" style="padding:12px 14px">' +
    '<button class="btn gh" id="htXet" style="margin:0">🔁 Xét lại hạng hàng loạt</button>' +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:8px;line-height:1.6">' +
    'Xem trước ai lên ai xuống rồi mới áp. Máy không đụng vào khách đang đeo hạng gán tay.</div></div>';

  var b = frame('Hạng thành viên', html, htSuaDuoc ? {
    footer: '<button class="btn gh" id="htThem" style="margin:0">➕ Thêm hạng</button>'
  } : null);

  b.onclick = function (e) {
    var t = e.target.closest('[data-htmo]');
    if (t) { htMo = +t.getAttribute('data-htmo'); go(scrHangSua); }
  };
  document.getElementById('htXet').onclick = function () { go(scrXetLaiHang); };
  var n = document.getElementById('htThem');
  if (n) n.onclick = function () {
    htDs.push({ ten_hang: '', thu_tu: htDs.length + 1, loai: 'Theo chi tieu', giam_gia: 0, tich_diem: 0, chi_tieu_tu: 0, so_thang_xet: 12, bat: 1, mo_ta: '', so_khach: 0 });
    htMo = htDs.length - 1; htMoi = 1;
    go(scrHangSua);
  };
}

function scrHangSua() {
  var d = (htDs || [])[htMo];
  if (!d) return go(scrHangKhach, true);
  var tay = (d.loai || 'Theo chi tieu') === 'Gan tay';
  var o = function (nhan, id, gt, mo, kieu) {
    return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="font-size:12px;color:#6b7280;margin-bottom:4px">' + nhan + '</div>' +
      '<input class="tin" id="' + id + '" type="' + (kieu || 'text') + '" value="' + h(gt == null ? '' : gt) + '" style="width:100%;margin:0">' +
      (mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo + '</div>' : '') + '</div>';
  };

  var html = '<div class="card">' +
    o('Tên hạng', 'htTen', d.ten_hang, 'Tên này in lên bill và hiện cho khách. Đặt xong thì đừng đổi.') +
    o('Thứ tự', 'htThuTu', d.thu_tu, 'Nhỏ là hạng thấp.', 'number') +
    '</div>';

  html += '<div class="sec">Cách lên hạng</div><div class="card" style="padding:11px 12px">' +
    kmHangChip(
      posChipNut('data-htloai="Theo chi tieu"', '📈 Theo chi tiêu', !tay) +
      posChipNut('data-htloai="Gan tay"', '✋ Gán tay', tay)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    (tay
      ? 'Máy không bao giờ tự gán hay tự gỡ hạng này. Dùng cho nhân viên, đại sứ, người nhà.'
      : 'Mỗi đêm máy tính lại tiền khách đã mua trong kỳ rồi xếp hạng theo mốc bên dưới.') +
    '</div></div>';

  if (!tay) {
    html += '<div class="card">' +
      o('Chi tiêu từ (đ)', 'htChiTieu', d.chi_tieu_tu, 'Khách mua đủ mức này trong kỳ thì lên hạng. Hạng thấp nhất để 0.', 'number') +
      o('Kỳ xét (tháng)', 'htThang', d.so_thang_xet, 'Anh Việt chốt 12 tháng: hạng xét lại theo chu kỳ chứ không giữ vĩnh viễn.', 'number') +
      '</div>';
  }

  html += '<div class="sec">Quyền lợi</div><div class="card">' +
    o('Giảm giá (%)', 'htGiam', d.giam_gia, 'Áp cho mọi hoá đơn của khách hạng này.', 'number') +
    o('Tích điểm (%)', 'htDiem', d.tich_diem, htGoiYDiem(d), 'number') +
    o('Mô tả quyền lợi', 'htMoTa', d.mo_ta, 'Câu này hiện cho khách xem trên trang thành viên.') +
    '</div>';

  html += '<div class="card" style="padding:11px 12px">' +
    kmHangChip(posChipNut('data-htbat="1"', d.bat ? '● Đang dùng' : '○ Đã tắt', !!d.bat)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px">Tắt thì hạng này không nhận khách mới nữa, khách cũ vẫn giữ nguyên hạng.</div></div>';

  var b = frame(d.ten_hang ? ('Hạng ' + d.ten_hang) : 'Hạng mới', html, htSuaDuoc ? {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="htBo" style="margin:0;flex:0 0 34%;color:#b3261e;border-color:#fecaca">Bỏ hạng này</button>' +
      '<button class="btn" id="htLuu" style="margin:0;flex:1">💾 Lưu</button></div>'
  } : null);

  b.onclick = function (e) {
    var t = e.target.closest('[data-htloai]');
    if (t) { htDoc(); d.loai = t.getAttribute('data-htloai'); return go(scrHangSua, true); }
    if (e.target.closest('[data-htbat]')) { htDoc(); d.bat = d.bat ? 0 : 1; return go(scrHangSua, true); }
  };
  if (!htSuaDuoc) return;
  document.getElementById('htLuu').onclick = function () { htLuu(); };
  document.getElementById('htBo').onclick = async function () {
    var ok = await confirmSheet('Bỏ hạng ' + (d.ten_hang || 'mới') + '?',
      'Hạng đang có khách thì máy chủ sẽ chặn - lúc đó anh chị tắt nó đi thay vì bỏ.', 'Bỏ hạng này', true);
    if (!ok) return;
    htDs.splice(htMo, 1);
    htLuu(1);
  };
}

/* Dong goi y ngay duoi o Tich diem, giong Fabi: go % xong thay ngay mot hoa
   don 500.000 d thi khach duoc bao nhieu diem. */
function htGoiYDiem(d) {
  var p = htSo(d.tich_diem);
  if (!p) return '1 điểm bằng 1 đồng. Để 0 là hạng này không tích điểm.';
  return 'Hoá đơn 500.000 đ được <b>' + money(Math.round(500000 * p / 100)) + ' điểm</b>. 1 điểm bằng 1 đồng.';
}
/* Rieng cho man Hang thanh vien: nhan ca dau phay thap phan vi o nhap la
   type=number nhung ban phim dien thoai VN hay ra dau phay. KHONG dat ten
   flt0 - ten do da co san hai cho trong file, dinh nghia them mot cai nua
   la de len ca hai, doi hanh vi cua nhung cho khong lien quan. */
function htSo(v) { var n = parseFloat(String(v == null ? '' : v).replace(',', '.')); return isNaN(n) ? 0 : n; }

function htDoc() {
  var d = (htDs || [])[htMo];
  if (!d) return;
  var v = function (id) { var e = document.getElementById(id); return e ? e.value.trim() : null; };
  var g;
  if ((g = v('htTen')) !== null) d.ten_hang = g;
  if ((g = v('htThuTu')) !== null) d.thu_tu = parseInt(g, 10) || 0;
  if ((g = v('htChiTieu')) !== null) d.chi_tieu_tu = htSo(g);
  if ((g = v('htThang')) !== null) d.so_thang_xet = parseInt(g, 10) || 12;
  if ((g = v('htGiam')) !== null) d.giam_gia = htSo(g);
  if ((g = v('htDiem')) !== null) d.tich_diem = htSo(g);
  if ((g = v('htMoTa')) !== null) d.mo_ta = g;
}

async function htLuu(daBo) {
  if (!daBo) htDoc();
  busy(true);
  try {
    htData = await api('vagabond.khach_hang.luu_hang', { hang: JSON.stringify(htDs) });
    htDs = htData.hang || []; htSuaDuoc = htData.sua_duoc ? 1 : 0;
    busy(false);
    toast('Đã lưu bảng hạng thành viên.', 3000);
    htMoi = 0;
    back();
  } catch (e) {
    busy(false);
    window.alert((e && e.message) || 'Không lưu được');
    try {
      var lai = await api('vagabond.khach_hang.cai_dat_hang', {});
      htData = lai; htDs = lai.hang || []; htSuaDuoc = lai.sua_duoc ? 1 : 0;
      if (htMo >= htDs.length) htMo = Math.max(0, htDs.length - 1);
    } catch (e2) { }
    go(scrHangSua, true);
  }
}

/* ---------- Xet lai hang hang loat ---------- */
var xlData = null;

async function scrXetLaiHang() {
  frame('Xét lại hạng', '<div class="emp"><div class="e1">⏳</div><div>Đang tính chi tiêu của cả tiệm...</div></div>');
  try { xlData = await api('vagabond.khach_hang.xet_lai', { ap: 0, so_khach: 400 }); }
  catch (e) {
    frame('Xét lại hạng', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không chạy được') + '</div></div>');
    return;
  }
  xlVe();
}

function xlVe() {
  var doi = xlData.doi || [];
  var html = '';
  if (xlData.loi_nhac) {
    html += '<div class="card" style="padding:12px 14px;background:#fef2f2;border:1px solid #fecaca">' +
      '<b style="font-size:14.5px;color:#b42318">⚠️ Chưa chạy được</b>' +
      '<div style="font-size:12.5px;color:#7f1d1d;margin-top:3px;line-height:1.6">' + h(xlData.loi_nhac) + '</div></div>';
    frame('Xét lại hạng', html);
    return;
  }

  /* Lay so dem tu may chu: may chu dem tren toan bo tap, con "doi" o day
     chi la phan dau da bi cat de man hinh khong treo. */
  var len = xlData.so_len == null ? doi.filter(function (x) { return x.len; }).length : xlData.so_len;
  var xuong = xlData.so_xuong == null ? Math.max(0, (xlData.tong || 0) - len) : xlData.so_xuong;
  html += '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">KẾT QUẢ XÉT LẠI</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Tính theo tiền khách đã mua trong <b>' + (xlData.so_thang || 12) + ' tháng</b> gần nhất. ' +
    'Có <b>' + money(xlData.tong || 0) + ' khách</b> lệch hạng: ' + money(len) + ' lên, ' +
    money(xuong) + ' xuống. Khách đeo hạng gán tay không bị đụng tới.</div></div>';

  if (!doi.length) {
    html += '<div class="emp"><div class="e1">✅</div><div>Không ai lệch hạng. Bảng hạng đang khớp với chi tiêu thật.</div></div>';
    frame('Xét lại hạng', html);
    return;
  }

  html += '<div class="card">' + doi.map(function (x) {
    return '<div style="display:flex;align-items:center;gap:10px;padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
      '<div style="flex:none;font-size:17px">' + (x.len ? '⬆️' : '⬇️') + '</div>' +
      '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(x.ten) + '</b>' +
      '<div style="font-size:11.5px;color:#98a2b3">' + htTien(x.tien) + ' trong kỳ</div></div>' +
      '<div style="text-align:right;font-size:12px">' +
      '<span style="color:#98a2b3">' + h(x.tu || 'chưa xếp') + '</span><br>' +
      '<b style="color:' + (x.len ? '#0f766e' : '#b45309') + '">' + h(x.sang) + '</b></div></div>';
  }).join('') + '</div>';

  if ((xlData.tong || 0) > doi.length) {
    html += '<div style="font-size:11.5px;color:#b45309;padding:8px 14px;font-weight:600">' +
      'Màn hình chỉ hiện ' + money(doi.length) + ' khách đầu, nhưng bấm áp là đổi đủ cả ' + money(xlData.tong) + ' khách.</div>';
  }

  var b = frame('Xét lại hạng', html, htSuaDuoc ? {
    footer: '<button class="btn" id="xlAp" style="margin:0">Áp cho ' + money(xlData.tong || 0) + ' khách</button>'
  } : null);
  var n = document.getElementById('xlAp');
  if (n) n.onclick = async function () {
    var ok = await confirmSheet('Đổi hạng cho ' + money(xlData.tong || 0) + ' khách?',
      'Hạng cũ không lưu lại ở đâu để quay về. Xem kỹ danh sách trên rồi hãy bấm.', 'Áp hạng mới', true);
    if (!ok) return;
    busy(true);
    try {
      var kq = await api('vagabond.khach_hang.xet_lai', { ap: 1, so_khach: 1 });
      busy(false);
      toast('Đã đổi hạng cho ' + money(kq.da_ap || 0) + ' khách.', 4000);
      back();
    } catch (e) { busy(false); window.alert((e && e.message) || 'Không áp được'); }
  };
}


/* ---------- Cai dat: Tai khoan nhan chuyen khoan (anh Viet 12/08/2026) ----------

   Truoc day so tai khoan nam trong ma nguon: mot tai khoan ao MBBank cho
   ca ba diem ban va moi nguon don. Ke toan doc sao ke thi moi giao dich do
   ve mot cho, muon biet tien cua quay nao phai lan theo noi dung chuyen
   khoan - ma noi dung la thu thu ngan go tay, go thieu la mat dau.

   Nay khai duoc tai khoan RIENG cho tung nguon don. Nguon nao chua khai
   thi dung tai khoan mac dinh, tuc chay y nhu cu. */
var tkData = null, tkMo = -1, tkMoi = 0;

async function scrTaiKhoan() {
  frame('Tài khoản nhận tiền', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc cấu hình...</div></div>');
  try { tkData = await api('vagabond.tai_khoan.danh_sach', {}); }
  catch (e) {
    frame('Tài khoản nhận tiền', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  tkVe();
}

/* Muc dich dac biet nhu phieu doi no khai chung bang voi nguon don, nhung
   phai hien ra bang chu nguoi doc hieu chu khong phai ma noi bo. */
function tkNhan(v) {
  var ds = (tkData && tkData.nguon) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].v === v) return ds[i].nhan || v;
  return v;
}
function tkIcon(v) {
  var ds = (tkData && tkData.nguon) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].v === v) return ds[i].ic || '🏦';
  return '🏦';
}
function tkMoTa(v) {
  var ds = (tkData && tkData.nguon) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].v === v) return ds[i].mo || '';
  return '';
}

function tkTenNh(ma) {
  var ds = (tkData && tkData.ngan_hang) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].bin === ma || ds[i].ma === ma) return ds[i].ten;
  return ma || '';
}

function tkOSelect(id, chon) {
  var ds = (tkData && tkData.ngan_hang) || [];
  var op = '<option value="">- Chọn ngân hàng -</option>';
  for (var i = 0; i < ds.length; i++) {
    var v = ds[i].bin;
    var on = (chon === ds[i].bin || chon === ds[i].ma) ? ' selected' : '';
    op += '<option value="' + h(v) + '"' + on + '>' + h(ds[i].ten) + '</option>';
  }
  return '<select class="tin" id="' + id + '" style="width:100%;margin:0">' + op + '</select>';
}

function tkONhap(nhan, id, gt, mo) {
  return '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
    '<div style="font-size:12px;color:#6b7280;margin-bottom:4px">' + nhan + '</div>' +
    '<input class="tin" id="' + id + '" value="' + h(gt || '') + '" style="width:100%;margin:0">' +
    (mo ? '<div style="font-size:11.5px;color:#98a2b3;margin-top:4px;line-height:1.5">' + mo + '</div>' : '') + '</div>';
}

function tkVe() {
  var md = (tkData && tkData.mac_dinh) || {};
  var ds = (tkData && tkData.theo_nguon) || [];
  var sua = tkData && tkData.sua_duoc;

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">TÀI KHOẢN NHẬN CHUYỂN KHOẢN</div>' +
    '<div style="font-size:14px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Mọi mã QR chuyển khoản của hệ sinh từ đây: màn tính tiền tại quầy, màn nhập đơn tay, ' +
    'chi tiết đơn Sales, phiếu tạm tính in cho khách và phiếu đòi công nợ.<br>' +
    'Khai tài khoản ảo riêng cho từng nguồn đơn thì sao kê ngân hàng tự tách sẵn, ' +
    'kế toán không phải lần theo nội dung chuyển khoản nữa. Tiền vẫn về tài khoản chính.</div></div>';

  html += '<div class="sec">Tài khoản mặc định</div><div class="card">' +
    '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
    '<div style="font-size:12px;color:#6b7280;margin-bottom:4px">Ngân hàng</div>' +
    tkOSelect('tkMdBank', md.bank || '') + '</div>' +
    tkONhap('Số tài khoản', 'tkMdStk', md.stk, 'Tài khoản ảo MB Bank cũng điền vào đây.') +
    tkONhap('Tên chủ tài khoản', 'tkMdTen', md.ten, 'Viết không dấu, đúng như ngân hàng đang ghi.') +
    '</div>' +
    '<div style="font-size:11.5px;color:#98a2b3;padding:8px 14px;line-height:1.6">' +
    'Nguồn đơn nào chưa khai riêng thì tiền về tài khoản này.</div>';

  html += '<div class="sec">Tài khoản riêng theo nguồn đơn</div>';
  if (!ds.length) {
    html += '<div class="card" style="padding:14px;font-size:13.5px;color:#6b7280;line-height:1.6">' +
      'Chưa khai nguồn nào. Cả hệ đang dùng chung tài khoản mặc định.</div>';
  } else {
    html += '<div class="card">' + ds.map(function (t, i) {
      return '<div data-tkmo="' + i + '" style="display:flex;align-items:center;gap:11px;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
        '<div style="width:34px;flex:none;text-align:center;font-size:20px">' + h(tkIcon(t.nguon)) + '</div>' +
        '<div style="flex:1;min-width:0"><b style="font-size:14.5px">' + h(tkNhan(t.nguon)) + '</b>' +
        '<div style="font-size:11.5px;color:#6b7280;margin-top:2px">' + h(tkTenNh(t.bank)) + ' · ' + h(t.stk || 'chưa có số') + '</div></div>' +
        '<span style="font-size:12px;font-weight:700;color:' + (t.dung ? '#0f766e' : '#a0a6b4') + '">' + (t.dung ? 'ĐANG DÙNG' : 'ĐÃ TẮT') + '</span>' +
        '<span style="color:#c8ccd4">›</span></div>';
    }).join('') + '</div>';
  }

  var b = frame('Tài khoản nhận tiền', html, sua ? {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="tkThem" style="margin:0;flex:0 0 44%">➕ Thêm nguồn</button>' +
      '<button class="btn" id="tkLuuMd" style="margin:0;flex:1">💾 Lưu</button></div>'
  } : null);

  b.onclick = function (e) {
    var t = e.target.closest('[data-tkmo]');
    if (t) { tkDocMd(); tkMo = +t.getAttribute('data-tkmo'); go(scrTaiKhoanSua); }
  };
  var nt = document.getElementById('tkThem');
  if (nt) nt.onclick = function () {
    tkDocMd();
    tkData.theo_nguon.push({ nguon: '', bank: md.bank || '', stk: '', ten: md.ten || '', dung: 1 });
    tkMo = tkData.theo_nguon.length - 1; tkMoi = 1;
    go(scrTaiKhoanSua);
  };
  var nl = document.getElementById('tkLuuMd');
  if (nl) nl.onclick = function () { tkDocMd(); tkLuu(); };
}

function tkDocMd() {
  if (!tkData) return;
  var v = function (id) { var o = document.getElementById(id); return o ? String(o.value).trim() : null; };
  var g;
  if ((g = v('tkMdBank')) !== null) tkData.mac_dinh.bank = g;
  if ((g = v('tkMdStk')) !== null) tkData.mac_dinh.stk = g;
  if ((g = v('tkMdTen')) !== null) tkData.mac_dinh.ten = g;
}

function scrTaiKhoanSua() {
  var t = ((tkData || {}).theo_nguon || [])[tkMo];
  if (!t) return go(scrTaiKhoan, true);
  var nguon = (tkData.nguon || []);

  var html = '<div class="sec">Nguồn đơn</div><div class="card" style="padding:11px 12px">' +
    kmHangChip(nguon.map(function (n) {
      /* Nguon da khai o dong KHAC thi khong cho chon lai o day: hai dong
         cung mot nguon la khong ai biet dong nao dang co hieu luc. */
      var ban = 0;
      (tkData.theo_nguon || []).forEach(function (x, i) { if (i !== tkMo && x.nguon === n.v) ban = 1; });
      if (ban) return '';
      return posChipNut('data-tkng="' + h(n.v) + '"', (n.lg ? '' : (n.ic || '🧾') + ' ') + h(n.nhan || n.v), t.nguon === n.v);
    }).join('')) +
    (t.nguon
      ? (tkMoTa(t.nguon) ? '<div style="font-size:12px;color:#0b7c93;margin-top:8px;line-height:1.5">' + h(tkMoTa(t.nguon)) + '</div>' : '')
      : '<div style="font-size:12px;color:#b45309;margin-top:8px">Chọn nguồn đơn trước đã.</div>') +
    '</div>';

  html += '<div class="sec">Tài khoản nhận tiền của nguồn này</div><div class="card">' +
    '<div style="padding:11px 14px;border-bottom:1px solid #f2f4f7">' +
    '<div style="font-size:12px;color:#6b7280;margin-bottom:4px">Ngân hàng</div>' +
    tkOSelect('tkBank', t.bank || '') + '</div>' +
    tkONhap('Số tài khoản', 'tkStk', t.stk, 'Dán đúng số tài khoản ảo MB Bank cấp cho nguồn này.') +
    tkONhap('Tên chủ tài khoản', 'tkTen', t.ten, 'Để trống thì lấy tên của tài khoản mặc định.') +
    '</div>';

  html += '<div class="card" style="padding:11px 12px">' +
    kmHangChip(posChipNut('data-tkdung="1"', t.dung ? '● Đang dùng' : '○ Đã tắt', !!t.dung)) +
    '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px;line-height:1.6">' +
    'Tắt dòng này thì nguồn đó quay về dùng tài khoản mặc định.</div></div>';

  var b = frame(t.nguon ? ('Tài khoản cho ' + tkNhan(t.nguon)) : 'Nguồn mới', html, {
    footer: '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="tkBo" style="margin:0;flex:0 0 34%;color:#b3261e;border-color:#fecaca">Bỏ dòng này</button>' +
      '<button class="btn" id="tkLuu" style="margin:0;flex:1">💾 Lưu</button></div>'
  });

  b.onclick = function (e) {
    var x = e.target.closest('[data-tkng]');
    if (x) { tkDocDong(); t.nguon = x.getAttribute('data-tkng'); return go(scrTaiKhoanSua, true); }
    if (e.target.closest('[data-tkdung]')) { tkDocDong(); t.dung = t.dung ? 0 : 1; return go(scrTaiKhoanSua, true); }
  };
  document.getElementById('tkLuu').onclick = function () {
    tkDocDong();
    if (!t.nguon) return toast('Chọn nguồn đơn trước đã.');
    tkLuu();
  };
  document.getElementById('tkBo').onclick = async function () {
    var ok = await confirmSheet('Bỏ tài khoản riêng của ' + (t.nguon ? tkNhan(t.nguon) : 'nguồn mới') + '?',
      'Nguồn này sẽ quay về dùng tài khoản mặc định. Giao dịch cũ trong sao kê giữ nguyên.', 'Bỏ dòng này', true);
    if (!ok) return;
    tkData.theo_nguon.splice(tkMo, 1);
    tkLuu(1);
  };
}

function tkDocDong() {
  var t = ((tkData || {}).theo_nguon || [])[tkMo];
  if (!t) return;
  var v = function (id) { var o = document.getElementById(id); return o ? String(o.value).trim() : null; };
  var g;
  if ((g = v('tkBank')) !== null) t.bank = g;
  if ((g = v('tkStk')) !== null) t.stk = g;
  if ((g = v('tkTen')) !== null) t.ten = g;
}

async function tkLuu(daBo) {
  busy(true);
  try {
    var kq = await api('vagabond.tai_khoan.luu', {
      mac_dinh: JSON.stringify(tkData.mac_dinh || {}),
      theo_nguon: JSON.stringify(tkData.theo_nguon || [])
    });
    tkData = kq;
    tkMoi = 0;
    busy(false);
    toast('Đã lưu tài khoản nhận tiền.', 3000);
    /* Cau hinh ban hang dang nam trong bo nho cua app, khong nap lai thi
       man tinh tien van sinh QR vao tai khoan cu cho den luc tai lai trang. */
    CFGBH = null;
    try { await cfgBanHang(); } catch (e2) { }
    if (daBo || tkMo >= 0) { tkMo = -1; return back(); }
    tkVe();
  } catch (e) {
    busy(false);
    window.alert((e && e.message) || 'Không lưu được');
  }
}


/* ---------- Combo co nhom mon cho khach chon (De feedback 12/08/2026) ----------

   Fabi cho tao "nhom" trong combo: 1 mon nuoc trong 2 mon nuoc da cai, 1
   banh trong 4 banh. Thu ngan bam combo thi phai hien hop chon mon truoc,
   chon xong bam OK moi do vao bill - chu khong duoc do thang ca sau mon
   vao hoa don.

   Dong nao khong ghi ten nhom van la mon BAT BUOC, luon vao bill. Combo
   cu khai truoc day khong co nhom nao nen chay y nhu truoc, khong hien
   hop chon. */

function comboKhoa(ma, chon) {
  return ma + '|' + (chon || []).map(function (x) { return x.nhom + '>' + x.item_code; }).sort().join(',');
}

/* Hop chon mon cua combo. xong(chon) duoc goi khi nguoi dung bam OK. */
function posSheetChonCombo(c, xong) {
  var nhom = c.nhom_ds || [];
  if (!nhom.length) { xong([]); return; }
  var da = {};
  nhom.forEach(function (g) { da[g.ten] = []; });

  var ov = document.createElement('div'); ov.className = 'sh';
  var box = document.createElement('div'); box.className = 'shb';

  function gTT(g) { var v = parseInt(g.toi_thieu, 10); return isNaN(v) ? (g.chon || 1) : v; }
  function gTD(g) { var v = parseInt(g.toi_da, 10); return isNaN(v) || v < 1 ? (g.chon || 1) : v; }
  function duSo() {
    for (var i = 0; i < nhom.length; i++) {
      var n = (da[nhom[i].ten] || []).length;
      if (n < gTT(nhom[i]) || n > gTD(nhom[i])) return 0;
    }
    return 1;
  }

  function ve() {
    var html = '<div class="shh"><b>' + h(c.ten) + '</b><div class="x">&times;</div></div>' +
      '<div style="padding:4px 14px calc(env(safe-area-inset-bottom,0px) + 90px);max-height:76vh;overflow:auto">' +
      '<div style="font-size:12.5px;color:#6b7280;line-height:1.6;margin-bottom:10px">Khách chọn món trong từng nhóm, bấm OK thì máy mới đổ vào hoá đơn.</div>';

    if ((c.bat_buoc || []).length) {
      html += '<div style="font-size:12px;color:#6b7280;font-weight:700;margin:6px 0 6px">CÓ SẴN TRONG COMBO</div>' +
        '<div style="font-size:13.5px;color:#374151;line-height:1.8;margin-bottom:12px">' +
        (c.bat_buoc || []).map(function (m) { return num(m.so_luong) + '× ' + h(m.ten_mon || m.item_code); }).join('<br>') +
        '</div>';
    }

    nhom.forEach(function (g, gi) {
      var chon = da[g.ten] || [];
      var tt = gTT(g), td = gTD(g);
      var xong2 = chon.length >= tt && chon.length <= td;
      html += '<div style="font-size:12px;font-weight:700;margin:12px 0 7px;color:' + (xong2 ? '#0f766e' : '#b45309') + '">' +
        h(g.ten).toUpperCase() + ' · ' + (tt === td ? 'chọn ' + td + ' món' : 'chọn từ ' + tt + ' đến ' + td + ' món') +
        ' <span style="font-weight:600">(' + chon.length + '/' + td + ')</span></div>' +
        (g.mo_ta ? '<div style="font-size:12px;color:#6b7280;margin:-3px 0 7px">' + h(g.mo_ta) + '</div>' : '') +
        '<div style="display:flex;flex-direction:column;gap:7px">';
      (g.mon || []).forEach(function (m, mi) {
        var on = chon.indexOf(m.item_code) >= 0;
        html += '<div data-cbg="' + gi + '" data-cbm="' + mi + '" style="display:flex;align-items:center;gap:10px;border:1.5px solid ' +
          (on ? '#0d9488' : '#e5e7eb') + ';background:' + (on ? '#ccfbf1' : '#fff') +
          ';border-radius:10px;padding:10px 12px;cursor:pointer">' +
          '<span style="font-size:17px">' + (on ? '✅' : '⬜') + '</span>' +
          '<div style="flex:1;min-width:0"><div style="font-size:14px;font-weight:' + (on ? '700' : '600') + '">' + h(m.ten_mon || m.item_code) + '</div>' +
          '<div style="font-size:11.5px;color:#98a2b3">' + num(m.so_luong) + ' phần · giá lẻ ' + money(m.gia_goc) + ' đ</div></div></div>';
      });
      html += '</div>';
    });

    html += '</div><div style="position:sticky;bottom:0;background:#fff;border-top:1px solid #eef0f4;padding:11px 14px calc(env(safe-area-inset-bottom,0px) + 11px)">' +
      '<button class="btn" id="cbcOk" style="width:100%"' + (duSo() ? '' : ' disabled') + '>' +
      (duSo() ? 'OK, thêm vào hoá đơn' : 'Chọn đủ món rồi mới bấm được') + '</button></div>';
    box.innerHTML = html;
    noi();
  }

  function noi() {
    box.querySelector('.x').onclick = function () { ov.remove(); };
    box.querySelectorAll('[data-cbg]').forEach(function (o) {
      o.onclick = function () {
        var g = nhom[+o.getAttribute('data-cbg')];
        var m = (g.mon || [])[+o.getAttribute('data-cbm')];
        if (!g || !m) return;
        var ds = da[g.ten] || [];
        var td = gTD(g);
        var i = ds.indexOf(m.item_code);
        if (i >= 0) ds.splice(i, 1);
        else if (ds.length >= td) {
          if (td === 1) {
            /* Nhom chi cho mot mon: bam mon khac la doi luon, khoi bat thu
               ngan bo tick roi tick lai. */
            ds.length = 0; ds.push(m.item_code);
          } else {
            toast('Nhóm ' + g.ten + ' chỉ được chọn tối đa ' + td + ' món. Bỏ bớt một món rồi chọn lại.', 3200);
            return;
          }
        } else ds.push(m.item_code);
        da[g.ten] = ds;
        ve();
      };
    });
    var ok = box.querySelector('#cbcOk');
    if (ok) ok.onclick = function () {
      if (!duSo()) return;
      var chon = [];
      nhom.forEach(function (g) {
        (da[g.ten] || []).forEach(function (ma) { chon.push({ nhom: g.ten, item_code: ma }); });
      });
      ov.remove();
      xong(chon);
    };
  }

  ve();
  ov.appendChild(box);
  ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
  document.body.appendChild(ov);
}


/* ---------- Cai dat: Danh muc san pham (anh Viet 12/08/2026) ----------

   Man Item goc cua ERPNext hon 80 truong, mo ra khong biet bat dau tu dau.
   Ket qua thay trong du lieu that: 1.428 ma hang, 33 tien to, 27 ma khong
   theo khuon nao, va ca ma ERPNext tu sinh kieu "9ZKKL9YXG7BU".

   Man nay chi hoi BAY thu. Ma hang, ba co mua/ban/ton kho va don vi tinh
   thi may tu dat theo LOAI HANG. */
var dmCai = null, dmVe = null, dmTre = null, dmVuaTao = null, dmNangCao = 0;

async function scrDanhMuc() {
  frame('Danh mục sản phẩm', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc danh mục...</div></div>');
  if (!dmCai) {
    try { dmCai = await api('vagabond.danh_muc.cai_dat', {}); }
    catch (e) {
      dmCai = null;
      frame('Danh mục sản phẩm', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
      return;
    }
  }
  if (!dmVe) dmVe = { nhom: '', loai: 'thanh_pham', ten: '', quy_cach: '', gia: '', bep: '', mo_ta: '', dvt: '', tien_to: '' };
  dmDraw();
}

function dmLoai(k) {
  var ds = (dmCai && dmCai.loai) || [];
  for (var i = 0; i < ds.length; i++) if (ds[i].k === k) return ds[i];
  return ds[0] || { ten: '', mua: 0, ban: 1, ton: 1 };
}

function dmDraw(giuCuon) {
  var s = dmVe, l = dmLoai(s.loai);
  var xin = 'width:100%;box-sizing:border-box;padding:10px 11px;border:1.5px solid #e5e7eb;border-radius:9px;font-size:15px;font-family:inherit';
  var nhan = function (t, phu) {
    return '<div style="font-size:12px;color:#6b7280;margin:12px 0 5px;font-weight:700">' + t +
      (phu ? ' <span style="font-weight:400;color:#98a2b3">' + phu + '</span>' : '') + '</div>';
  };

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">MỞ MÃ HÀNG MỚI</div>' +
    '<div style="font-size:13.5px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Chỉ điền bảy ô. Mã hàng, đơn vị tính và ba cờ mua - bán - tồn kho thì máy tự đặt theo loại hàng.</div></div>';

  html += '<div class="card" style="padding:4px 14px 14px">';

  html += nhan('1. NHÓM MÓN');
  html += '<select id="dmNhom" style="' + xin + '"><option value="">- Chọn nhóm -</option>' +
    ((dmCai && dmCai.nhom) || []).map(function (n) {
      return '<option value="' + h(n.ten) + '"' + (s.nhom === n.ten ? ' selected' : '') + '>' + h(n.ten) + '</option>';
    }).join('') + '</select>';

  html += nhan('2. LOẠI HÀNG');
  html += kmHangChip(((dmCai && dmCai.loai) || []).map(function (x) {
    return posChipNut('data-dmloai="' + h(x.k) + '"', x.ten, s.loai === x.k);
  }).join(''));
  html += '<div style="font-size:11.5px;color:#98a2b3;margin-top:6px;line-height:1.5">' + h(l.mo || '') + '</div>';
  html += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:7px">' +
    dmCo('Cho mua', l.mua) + dmCo('Cho bán', l.ban) + dmCo('Quản lý tồn kho', l.ton) + '</div>';

  html += nhan('3. TÊN MẶT HÀNG');
  html += '<input id="dmTen" value="' + h(s.ten) + '" placeholder="Ví dụ: Bánh mì bơ tỏi" style="' + xin + '">';

  html += nhan('4. QUY CÁCH HOẶC SIZE', l.ban ? '(gắn vào tên món)' : '(ghi xuống mô tả)');
  html += '<input id="dmQc" value="' + h(s.quy_cach) + '" placeholder="Ví dụ: 110 gram, size 16cm, hộp 8 cái" style="' + xin + '">';

  html += nhan('5. GIÁ BÁN (đ)', l.ban ? '' : '(loại này không bán, để trống)');
  html += '<input id="dmGia" inputmode="numeric" value="' + h(s.gia) + '" placeholder="0" style="' + xin + '">';

  if (dmCai && dmCai.co_bep) {
    html += nhan('6. BẾP HOẶC VỊ TRÍ', '(nếu khác mặc định của nhóm)');
    html += '<input id="dmBep" value="' + h(s.bep) + '" placeholder="Để trống là theo nhóm món" style="' + xin + '">';
  }

  html += nhan((dmCai && dmCai.co_bep ? '7' : '6') + '. MÔ TẢ NGẮN', '(nếu đã có)');
  html += '<textarea id="dmMoTa" rows="2" placeholder="Để trống thì máy lấy tên món" style="' + xin + '">' + h(s.mo_ta) + '</textarea>';

  html += '<div style="margin-top:12px">' +
    posChipNut('data-dmnc="1"', dmNangCao ? '▾ Ẩn phần nâng cao' : '▸ Phần nâng cao', false) + '</div>';
  if (dmNangCao) {
    html += nhan('ĐƠN VỊ TÍNH GỐC', '(để trống là theo nhóm)');
    html += '<input id="dmDvt" value="' + h(s.dvt) + '" placeholder="' + h((dmKq && dmKq.dvt_goi_y) || 'Cái') + '" style="' + xin + '">';
    html += nhan('TIỀN TỐ MÃ', '(để trống là theo nhóm)');
    html += '<input id="dmTt" value="' + h(s.tien_to) + '" placeholder="' + h((dmKq && dmKq.tien_to) || 'VD BAWS') + '" style="text-transform:uppercase;' + xin + '">';
  }
  html += '</div>';

  html += '<div id="dmXem"></div>';

  var b = frame('Danh mục sản phẩm', html, (dmCai && dmCai.tao_duoc) ? {
    footer: '<button class="btn" id="dmTao" style="margin:0">➕ Tạo mã hàng</button>'
  } : null);

  b.onclick = function (e) {
    var t = e.target.closest('[data-dmloai]');
    if (t) { dmDoc(); dmVe.loai = t.getAttribute('data-dmloai'); return dmDraw(); }
    if (e.target.closest('[data-dmnc]')) { dmDoc(); dmNangCao = dmNangCao ? 0 : 1; return dmDraw(); }
  };
  ['dmTen', 'dmQc'].forEach(function (id) {
    var o = document.getElementById(id);
    if (o) o.oninput = function () { dmDoc(); dmHoiXem(); };
  });
  var on = document.getElementById('dmNhom');
  if (on) on.onchange = function () { dmDoc(); dmHoiXem(); dmDraw(); };
  var nt = document.getElementById('dmTao');
  if (nt) nt.onclick = function () { dmTao(0); };
  dmVeXem();
  dmHoiXem();
}

function dmCo(ten, on) {
  return '<span style="display:inline-block;background:' + (on ? '#ccfbf1' : '#f3f4f6') + ';color:' + (on ? '#0f766e' : '#9ca3af') +
    ';border-radius:999px;padding:3px 11px;font-size:12px;font-weight:700">' + (on ? '✓ ' : '✕ ') + ten + '</span>';
}

function dmDoc() {
  var v = function (id) { var o = document.getElementById(id); return o ? o.value : null; };
  var g;
  if ((g = v('dmNhom')) !== null) dmVe.nhom = g;
  if ((g = v('dmTen')) !== null) dmVe.ten = g;
  if ((g = v('dmQc')) !== null) dmVe.quy_cach = g;
  if ((g = v('dmGia')) !== null) dmVe.gia = g;
  if ((g = v('dmBep')) !== null) dmVe.bep = g;
  if ((g = v('dmMoTa')) !== null) dmVe.mo_ta = g;
  if ((g = v('dmDvt')) !== null) dmVe.dvt = g;
  if ((g = v('dmTt')) !== null) dmVe.tien_to = String(g || '').toUpperCase();
}

var dmKq = null;
function dmHoiXem() {
  if (dmTre) clearTimeout(dmTre);
  dmTre = setTimeout(async function () {
    var s = dmVe;
    if (!s.nhom && String(s.ten || '').trim().length < 3) { dmKq = null; return dmVeXem(); }
    try {
      dmKq = await api('vagabond.danh_muc.xem_truoc', {
        nhom: s.nhom, loai: s.loai, ten: s.ten, quy_cach: s.quy_cach
      });
    } catch (e) { dmKq = null; }
    dmVeXem();
  }, 320);
}

function dmVeXem() {
  var o = document.getElementById('dmXem');
  if (!o) return;
  var html = '';

  if (dmVuaTao) {
    html += '<div class="card" style="padding:14px;background:#f0fdf4;border:1.5px solid #86efac">' +
      '<div style="font-size:12px;color:#15803d;font-weight:800">VỪA MỞ XONG</div>' +
      '<div style="font-size:18px;font-weight:800;margin-top:3px">' + h(dmVuaTao.ma) + '</div>' +
      '<div style="font-size:13.5px;color:#374151;margin-top:2px">' + h(dmVuaTao.ten) + '</div>' +
      '<div style="font-size:12px;color:#6b7280;margin-top:3px">' + h(dmVuaTao.nhom) + ' · ' + h(dmVuaTao.dvt) +
      (dmVuaTao.gia_ban ? ' · ' + money(dmVuaTao.gia_ban) + ' đ' : ' · chưa có giá bán') + '</div>' +
      '<button class="btn gh" id="dmPan" style="margin-top:10px">🔄 Đồng bộ mã này sang Pancake</button>' +
      '<div id="dmPanBao" style="font-size:12.5px;color:#374151;margin-top:7px;line-height:1.5"></div></div>';
  }

  var k = dmKq;
  if (k) {
    html += '<div class="card" style="padding:13px 14px">' +
      '<div style="font-size:12px;color:#98a2b3;font-weight:700">MÁY SẼ ĐẶT</div>' +
      '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:5px">' +
      '<span style="font-size:13px;color:#6b7280">Mã hàng</span>' +
      '<b style="font-size:16px">' + h(k.ma_du_kien || 'chưa đoán được') + '</b></div>' +
      '<div style="display:flex;justify-content:space-between;gap:12px;margin-top:5px">' +
      '<span style="font-size:13px;color:#6b7280;flex:none">Tên món</span>' +
      '<b style="font-size:13.5px;text-align:right">' + h(k.ten_day_du || '') + '</b></div>' +
      (k.dvt_goi_y ? '<div style="display:flex;justify-content:space-between;margin-top:5px">' +
        '<span style="font-size:13px;color:#6b7280">Đơn vị tính</span><b style="font-size:13.5px">' + h(k.dvt_goi_y) + '</b></div>' : '') +
      '<div style="font-size:11.5px;color:#98a2b3;margin-top:7px">Số cuối chỉ là dự kiến. Máy cấp số thật lúc bấm Tạo.</div></div>';

    (k.canh_bao || []).forEach(function (c) {
      html += '<div class="card" style="padding:12px 14px;background:#fffbeb;border:1.5px solid #fcd34d;font-size:13px;color:#92400e;line-height:1.6">⚠️ ' + h(c) + '</div>';
    });

    if ((k.trung || []).length) {
      var nang = (k.trung || []).filter(function (x) { return x.muc >= 3; }).length;
      html += '<div class="card" style="padding:12px 14px;border:1.5px solid ' + (nang ? '#fecaca' : '#e5e7eb') + ';background:' + (nang ? '#fef2f2' : '#fff') + '">' +
        '<div style="font-size:12px;font-weight:800;color:' + (nang ? '#991b1b' : '#6b7280') + '">' +
        (nang ? '⚠️ ĐÃ CÓ MÓN TRÙNG TÊN' : 'MÓN GẦN GIỐNG ĐÃ CÓ') + '</div>' +
        '<div style="font-size:12px;color:#6b7280;margin:4px 0 8px;line-height:1.6">' +
        'Mở thêm mã cho món đã có là tồn kho bị tách vụn, báo cáo bán chạy bị chia nhỏ, ' +
        'và về sau gộp lại phải kéo theo mọi hoá đơn đã trỏ tới.</div>' +
        (k.trung || []).map(function (x) {
          return '<div style="display:flex;gap:9px;align-items:baseline;padding:6px 0;border-top:1px solid #f2f4f7">' +
            '<b style="font-size:12.5px;flex:none">' + h(x.ma) + '</b>' +
            '<div style="flex:1;min-width:0"><div style="font-size:13px">' + h(x.ten) + '</div>' +
            '<div style="font-size:11.5px;color:#98a2b3">' + h(x.nhom) + ' · ' + h(x.vi_sao) + (x.tat ? ' · đã khoá' : '') + '</div></div></div>';
        }).join('') + '</div>';
    }
  }
  o.innerHTML = html;

  var np = document.getElementById('dmPan');
  if (np) np.onclick = async function () {
    var bao = document.getElementById('dmPanBao');
    np.disabled = true; np.textContent = 'Đang đẩy sang Pancake...';
    try {
      var r = await api('vagabond.danh_muc.day_sang_pancake', { item_code: dmVuaTao.ma });
      if (bao) bao.textContent = (r && r.thong_bao) || 'Xong.';
    } catch (e) {
      if (bao) bao.textContent = (e && e.message) || 'Không đẩy được sang Pancake.';
    }
    np.disabled = false; np.textContent = '🔄 Đồng bộ mã này sang Pancake';
  };
}

async function dmTao(boQuaTrung) {
  dmDoc();
  var s = dmVe;
  if (!s.nhom) return toast('Chọn nhóm món trước đã.');
  if (String(s.ten || '').trim().length < 3) return toast('Gõ tên mặt hàng giúp em.');
  busy(true);
  var r;
  try {
    r = await api('vagabond.danh_muc.tao', {
      nhom: s.nhom, loai: s.loai, ten: s.ten, quy_cach: s.quy_cach,
      gia_ban: String(s.gia || '').replace(/[^0-9]/g, ''),
      bep: s.bep, mo_ta: s.mo_ta, dvt: s.dvt, tien_to: s.tien_to,
      bo_qua_trung: boQuaTrung ? 1 : 0
    });
  } catch (e) {
    busy(false);
    var msg = (e && e.message) || 'Không tạo được';
    if (!boQuaTrung && msg.indexOf('Đã có mã') === 0) {
      var ok = await confirmSheet('Món này đã có mã rồi', msg, 'Vẫn tạo mã mới', true);
      if (ok) return dmTao(1);
      return;
    }
    window.alert(msg);
    return;
  }
  busy(false);
  dmVuaTao = r;
  /* Xoa o nhap de go tiep mon sau, giu lai nhom va loai hang: nguoi ta hay
     mo mot loat ma cung nhom trong mot luot. */
  dmVe.ten = ''; dmVe.quy_cach = ''; dmVe.gia = ''; dmVe.mo_ta = '';
  dmKq = null;
  toast('Đã mở mã ' + r.ma);
  dmDraw();
}


/* ---------- Doi chieu hoa don mua (Uyen 12/08/2026) ----------

   Uyen noi phieu xong bam Luu ma trang thai khong doi, vi con thieu nut
   Gui nam o cho khac tren man Desk. Man nay gop hai buoc thanh mot nut. */
var dcmNgay = 60, dcmNhom = '', dcmTim = '', dcmPhieu = [], dcmSs = null;

async function scrDoiChieuMua() {
  frame('Đối chiếu hoá đơn mua', '<div class="emp"><div class="e1">⏳</div><div>Đang đọc hoá đơn...</div></div>');
  var kq;
  try { kq = await api('vagabond.doi_chieu_mua.danh_sach', { so_ngay: dcmNgay, nhom: dcmNhom, tu_khoa: dcmTim }); }
  catch (e) {
    frame('Đối chiếu hoá đơn mua', '<div class="emp"><div class="e1">🔒</div><div>' + h((e && e.message) || 'Không mở được') + '</div></div>');
    return;
  }
  var ds = kq.hd || [];

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">ĐỐI CHIẾU HOÁ ĐƠN MUA · ' + ngayNgan(kq.tu) + ' - ' + ngayNgan(kq.den) + '</div>' +
    '<div style="font-size:13.5px;color:#374151;line-height:1.6;margin-top:4px">' +
    'Chọn một hoá đơn nhà cung cấp còn nháp, máy tìm phiếu nhập kho khớp và chỉ ra chỗ lệch. ' +
    'Một nút <b>Khớp và ghi sổ</b> làm cả hai việc: nối phiếu rồi ghi sổ.</div>' +
    mkNhacCat(kq.bi_cat, 'hoá đơn') + '</div>';

  html += '<div class="card" style="padding:10px 12px">' +
    mkChipNgay([[30, '30 ngày'], [60, '60 ngày'], [90, '3 tháng'], [365, '1 năm']], dcmNgay, 'data-dcmngay') + '</div>';
  html += '<div class="card" style="padding:10px 12px">' + kmHangChip(
    (kq.nhom || []).map(function (n) {
      var so = (kq.dem || {})[n.k] || 0;
      if (!so && n.k) return '';
      return posChipNut('data-dcmnhom="' + h(n.k) + '"', n.ic + ' ' + n.ten + ' ' + so, dcmNhom === n.k);
    }).join('')) + '</div>';
  html += mkOTim('dcmTim', dcmTim, 'Tìm theo mã phiếu, tên nhà cung cấp, số hoá đơn NCC...');

  if (!ds.length) {
    html += '<div class="card"><div class="emp" style="padding:26px"><div class="e1">🫙</div><div>Không có hoá đơn nào ở nhóm này.</div></div></div>';
  } else {
    html += '<div class="lst">' + ds.map(function (d) {
      return '<div class="shi" data-dcm="' + h(d.name) + '" style="display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer">' +
        '<div style="flex:1;min-width:0"><b style="font-size:14px">' + h(d.supplier_name || d.supplier) + '</b>' +
        '<div style="font-size:12px;color:#98a2b3">' + h(d.name) + ' · ' + ngayNgan(d.posting_date) +
        (d.bill_no ? ' · HĐ NCC ' + h(d.bill_no) : '') + '</div>' +
        '<div style="margin-top:4px">' + dcmChip(d) + '</div></div>' +
        '<div style="text-align:right;white-space:nowrap"><b>' + money(d.grand_total) + '</b></div></div>';
    }).join('') + '</div>';
  }

  var b = frame('Đối chiếu hoá đơn mua', html);
  b.onclick = function (e) {
    var t = e.target.closest('[data-dcmngay]');
    if (t) { dcmNgay = parseInt(t.getAttribute('data-dcmngay'), 10); return go(scrDoiChieuMua, true); }
    t = e.target.closest('[data-dcmnhom]');
    if (t) { dcmNhom = t.getAttribute('data-dcmnhom'); return go(scrDoiChieuMua, true); }
    t = e.target.closest('[data-dcm]');
    if (t) { var nm = t.getAttribute('data-dcm'); dcmPhieu = []; dcmSs = null; return go(function () { scrDcmXem(nm); }); }
  };
  var o = document.getElementById('dcmTim');
  if (o) o.onchange = function () { dcmTim = o.value; go(scrDoiChieuMua, true); };
}

function dcmChip(d) {
  var the = function (bg, fg, chu) {
    return '<span style="display:inline-block;background:' + bg + ';color:' + fg + ';font-size:12px;font-weight:700;border-radius:999px;padding:3px 10px;margin:2px 5px 0 0;white-space:nowrap">' + chu + '</span>';
  };
  if (d.nhom === 'xong') return the('#dcfce7', '#166534', '✅ Đã ghi sổ');
  if (d.nhom === 'huy') return the('#fee2e2', '#991b1b', '🚫 Đã huỷ');
  if (d.nhom === 'cho_ghi_so') return the('#dbeafe', '#1e40af', '📒 Đã nối phiếu, chờ ghi sổ');
  if (d.nhom === 'khong_thay') return the('#f3f4f6', '#4b5563', '❓ Không thấy phiếu nhập nào');
  if (d.nhom === 'lech') {
    return the('#fee2e2', '#991b1b', '⚠️ Lệch ' + money(Math.abs(d.lech || 0)) + ' đ') +
      the('#f3f4f6', '#4b5563', d.so_phieu_goi_y + ' phiếu gợi ý');
  }
  return the('#fef3c7', '#92400e', '🔍 Chờ đối chiếu') + the('#f3f4f6', '#4b5563', (d.so_phieu_goi_y || 0) + ' phiếu gợi ý');
}

async function scrDcmXem(name) {
  frame('Đối chiếu ' + name, '<div class="emp"><div class="e1">⏳</div></div>');
  var kq;
  try { kq = await api('vagabond.doi_chieu_mua.xem', { name: name }); }
  catch (e) { frame('Đối chiếu', '<div class="emp"><div class="e1">⚠️</div><div>' + h((e && e.message) || 'Không đọc được') + '</div></div>'); return; }
  var d = kq.hd || {};
  var gy = kq.goi_y || [];

  /* Lan dau mo: tick san. Hoa don da noi phieu tu truoc thi tick DUNG may
     phieu do, chua noi gi thi tick phieu may chấm điểm cao nhất. Người
     dùng vẫn bỏ tick hoặc chọn thêm phiếu khác được. */
  if (!dcmPhieu.length) {
    if ((kq.phieu_da_noi || []).length) dcmPhieu = kq.phieu_da_noi.slice();
    else if (gy.length) dcmPhieu = [gy[0].name];
  }

  async function veSoSanh() {
    var o = document.getElementById('dcmSs');
    if (!o) return;
    if (!dcmPhieu.length) { o.innerHTML = '<div class="card" style="padding:14px;font-size:13px;color:#6b7280">Chọn ít nhất một phiếu nhập để đối chiếu.</div>'; return; }
    o.innerHTML = '<div class="card" style="padding:14px;font-size:13px;color:#6b7280">Đang đối chiếu...</div>';
    try { dcmSs = await api('vagabond.doi_chieu_mua.so_sanh', { name: name, phieu: JSON.stringify(dcmPhieu) }); }
    catch (e) { o.innerHTML = '<div class="card" style="padding:14px;font-size:13px;color:#b3261e">' + h((e && e.message) || 'Không đối chiếu được') + '</div>'; return; }
    var s = dcmSs;
    var html = '<div class="card" style="padding:13px 14px;background:' + (s.khop ? '#f0fdf4' : '#fffbeb') + ';border:1.5px solid ' + (s.khop ? '#86efac' : '#fcd34d') + '">' +
      '<div style="display:flex;justify-content:space-between"><span style="font-size:13px;color:#374151">Tiền hàng trên hoá đơn</span><b>' + money(s.tien_hd) + ' đ</b></div>' +
      '<div style="display:flex;justify-content:space-between;margin-top:4px"><span style="font-size:13px;color:#374151">Tiền hàng trên phiếu nhập</span><b>' + money(s.tien_pnk) + ' đ</b></div>' +
      '<div style="display:flex;justify-content:space-between;margin-top:6px;padding-top:6px;border-top:1px solid rgba(0,0,0,.08)">' +
      '<b style="font-size:13.5px;color:' + (s.khop ? '#15803d' : '#92400e') + '">' + (s.khop ? '✅ Khớp' : '⚠️ Lệch') + '</b>' +
      '<b style="color:' + (s.khop ? '#15803d' : '#92400e') + '">' + (s.lech_tien ? money(s.lech_tien) + ' đ' : '0 đ') + '</b></div>' +
      (s.khop ? '' : '<div style="font-size:12px;color:#92400e;margin-top:6px;line-height:1.5">Lệch dưới ' + money(s.nguong_lech) + ' đ thì máy vẫn coi là khớp, vì đó thường là làm tròn thuế.</div>') +
      '</div>';

    html += '<div class="sec">Từng món</div><div class="card">';
    (s.dong || []).forEach(function (r) {
      var lech = Math.abs(r.lech_sl) > 0.0001 || Math.abs(r.lech_gia) > 0.5 || !r.co_phieu;
      html += '<div style="padding:10px 14px;border-bottom:1px solid #f2f4f7;background:' + (lech ? '#fef2f2' : '#fff') + '">' +
        '<div style="font-size:13.5px;font-weight:600">' + h(r.item_name || r.item_code) + '</div>' +
        '<div style="display:flex;justify-content:space-between;gap:10px;font-size:12px;color:#6b7280;margin-top:3px">' +
        '<span>Hoá đơn ' + num(r.sl_hd) + ' × ' + money(r.gia_hd) + '</span>' +
        '<span>' + (r.co_phieu ? 'Phiếu nhập ' + num(r.sl_pnk) + ' × ' + money(r.gia_pnk) : '<b style="color:#b3261e">không có trong phiếu</b>') + '</span></div>' +
        (Math.abs(r.lech_sl) > 0.0001 ? '<div style="font-size:12px;color:#b3261e;margin-top:2px">Lệch số lượng ' + num(r.lech_sl) + '</div>' : '') +
        (r.co_phieu && Math.abs(r.lech_gia) > 0.5 ? '<div style="font-size:12px;color:#b3261e;margin-top:2px">Lệch đơn giá ' + money(r.lech_gia) + ' đ</div>' : '') +
        '</div>';
    });
    html += '</div>';

    if ((s.thua || []).length) {
      html += '<div class="sec">Có trong phiếu nhập mà hoá đơn không nhắc tới</div>' +
        '<div class="card" style="padding:12px 14px;font-size:13px;color:#92400e;line-height:1.7">' +
        'Hàng đã về kho mà tờ hoá đơn này không tính tiền. Có thể nhà cung cấp xuất hoá đơn làm nhiều lần, cũng có thể chọn nhầm phiếu.<br>' +
        (s.thua || []).map(function (x) { return '· ' + h(x.item_name || x.item_code) + ' · ' + num(x.sl_pnk) + ' · ' + money(x.tien_pnk) + ' đ'; }).join('<br>') +
        '</div>';
    }
    o.innerHTML = html;
  }

  var html = '<div class="card" style="padding:13px 14px">' +
    '<div style="font-size:12px;color:#98a2b3">HOÁ ĐƠN NHÀ CUNG CẤP</div>' +
    '<b style="font-size:17px">' + h(d.supplier_name || d.supplier) + '</b>' +
    '<div style="font-size:12.5px;color:#6b7280;margin-top:3px">' + h(d.name) + ' · ' + ngayNgan(d.posting_date) +
    (d.bill_no ? ' · số ' + h(d.bill_no) : '') + '</div>' +
    '<div style="display:flex;justify-content:space-between;margin-top:8px"><span style="font-size:13px;color:#374151">Tổng hoá đơn</span><b style="font-size:16px">' + money(d.grand_total) + ' đ</b></div>' +
    '<div style="margin-top:6px">' + dcmChip({ nhom: kq.nhom, so_phieu_goi_y: gy.length }) + '</div></div>';

  if (d.docstatus === 1) {
    html += '<div class="card" style="padding:14px;background:#f0fdf4;border:1.5px solid #86efac;font-size:13.5px;color:#15803d;line-height:1.6">' +
      '✅ Hoá đơn này đã ghi sổ xong. Công nợ còn ' + money(d.outstanding_amount) + ' đ.</div>';
    frame('Đối chiếu ' + name, html);
    return;
  }

  if (cint0(d.update_stock)) {
    html += '<div class="card" style="padding:14px;background:#fef2f2;border:1.5px solid #fecaca;font-size:13.5px;color:#991b1b;line-height:1.6">' +
      'Hoá đơn này đang bật <b>Cập nhật tồn kho</b>. Nối thêm vào phiếu nhập nữa là hàng vào kho hai lần, nên em chưa nối được. Nhờ anh chị tắt ô đó bên Desk rồi quay lại.</div>';
    frame('Đối chiếu ' + name, html);
    return;
  }

  html += '<div class="sec">Phiếu nhập kho của nhà cung cấp này</div>';
  if (!gy.length) {
    html += '<div class="card" style="padding:14px;font-size:13.5px;color:#6b7280;line-height:1.7">' +
      'Không thấy phiếu nhập kho nào còn chưa được hoá đơn nào lấy, mà lại trùng món với hoá đơn này.<br>' +
      'Thường là do hàng chưa được nhập kho, hoặc phiếu nhập còn đang nháp chưa ghi sổ.</div>';
  } else {
    html += '<div class="card">' + gy.map(function (p) {
      var on = dcmPhieu.indexOf(p.name) >= 0;
      return '<div data-dcmp="' + h(p.name) + '" style="display:flex;align-items:center;gap:10px;padding:11px 14px;border-bottom:1px solid #f2f4f7;cursor:pointer;background:' + (on ? '#f0fdfa' : '#fff') + '">' +
        '<span style="font-size:18px">' + (on ? '✅' : '⬜') + '</span>' +
        '<div style="flex:1;min-width:0"><b style="font-size:13.5px">' + h(p.name) + '</b>' +
        '<div style="font-size:11.5px;color:#98a2b3">' + ngayNgan(p.ngay) + ' · ' + p.so_mon + ' món, trùng ' + p.so_mon_trung +
        (p.da_hoa_don ? ' · đã hoá đơn ' + num(Math.round(p.da_hoa_don)) + '%' : '') + '</div></div>' +
        '<b style="white-space:nowrap;font-size:13px">' + money(p.tien) + '</b></div>';
    }).join('') + '</div>';
  }

  html += '<div id="dcmSs"></div>';

  var foot = '';
  if (kq.lam_duoc && gy.length) {
    foot = '<div style="display:flex;gap:8px">' +
      '<button class="btn gh" id="dcmNoi" style="margin:0;flex:0 0 38%">🔗 Chỉ nối phiếu</button>' +
      '<button class="btn" id="dcmXong" style="margin:0;flex:1">✅ Khớp và ghi sổ</button></div>';
  }
  var b = frame('Đối chiếu ' + name, html, foot ? { footer: foot } : {});
  b.onclick = function (e) {
    var t = e.target.closest('[data-dcmp]');
    if (!t) return;
    var ma = t.getAttribute('data-dcmp');
    var i = dcmPhieu.indexOf(ma);
    if (i >= 0) dcmPhieu.splice(i, 1); else dcmPhieu.push(ma);
    go(function () { scrDcmXem(name); }, true);
  };
  veSoSanh();

  async function chay(ghiSo) {
    if (!dcmPhieu.length) return toast('Chọn phiếu nhập trước đã.');
    if (ghiSo && dcmSs && !dcmSs.khop) {
      var ok = await confirmSheet('Hoá đơn và phiếu nhập đang lệch',
        'Chênh ' + money(dcmSs.lech_tien) + ' đ.\nGhi sổ bây giờ là ghi công nợ và giá vốn theo con số của hoá đơn.\n\nChắc chắn thì bấm tiếp.',
        'Vẫn ghi sổ', true);
      if (!ok) return;
    }
    busy(true);
    var r;
    try { r = await api('vagabond.doi_chieu_mua.noi_phieu', { name: name, phieu: JSON.stringify(dcmPhieu), ghi_so: ghiSo ? 1 : 0 }); }
    catch (e) { busy(false); window.alert((e && e.message) || 'Không nối được'); return; }
    busy(false);
    toast(r.da_ghi_so ? 'Đã nối phiếu và ghi sổ ' + name : 'Đã nối phiếu. Bấm "Khớp và ghi sổ" khi muốn ghi sổ.', 4000);
    if (r.da_ghi_so) { dcmPhieu = []; dcmSs = null; return go(scrDoiChieuMua, true); }
    go(function () { scrDcmXem(name); }, true);
  }
  var n1 = document.getElementById('dcmNoi');
  if (n1) n1.onclick = function () { chay(0); };
  var n2 = document.getElementById('dcmXong');
  if (n2) n2.onclick = function () { chay(1); };
}

function cint0(v) { var n = parseInt(v, 10); return isNaN(n) ? 0 : n; }

})();


