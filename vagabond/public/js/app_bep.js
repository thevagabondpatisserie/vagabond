/* The Vagabond Patisserie - App nghiep vu (mobile). Built for ERPNext v16 portal. */

(function () {
'use strict';

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
.lbw{color:#c07800}.hw{padding:0 14px 12px}.hl{font-size:12px;color:#8a8f9c;margin-bottom:6px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;line-height:1.35}.hbd{font-size:11px;font-weight:700;color:#0B7C93;background:#E4F9FD;border-radius:6px;padding:2px 7px;white-space:nowrap}.hin{display:flex;align-items:center;justify-content:space-between;width:100%;max-width:100%;min-width:0;-webkit-appearance:none;appearance:none;border:1.5px solid #dfe3ec;border-radius:12px;height:48px;padding:0 12px;font-size:16px;font-weight:600;text-align:left;background:#fff;color:#16181d;outline:0;font-family:inherit}.hin::-webkit-date-and-time-value{text-align:left;margin:0;padding:0;min-width:0;flex:1 1 auto}.hin::-webkit-calendar-picker-indicator{opacity:.5;margin:0;padding:0;flex:0 0 auto}.hin.ed{border-color:#0FB5CE;background:#f4fdff}.hn{font-size:11px;color:#9aa0ad;margin-top:5px;line-height:1.4}.hn.ed{color:#0B7C93;font-weight:600}
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
    inp.setAttribute('style', 'position:absolute;left:0;top:0;width:100%;height:100%;opacity:0;margin:0;padding:0;border:0;background:none');
    var ov = document.createElement('span');
    ov.style.cssText = 'pointer-events:none';
    w.appendChild(ov);
    var ve = function () { ov.textContent = inp.value ? dmy(inp.value) : 'dd/mm/yyyy'; };
    ve();
    inp.addEventListener('input', ve);
    inp.addEventListener('change', ve);
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

function frame(title, bodyHtml, opt) {
  opt = opt || {};
  /* Tieu de tab trinh duyet theo man hinh, liec tab biet ngay dang o dau */
  try { document.title = (title && title !== APPNAME) ? title + ' · Vagabond' : APPNAME; } catch (e) { }
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
  return document.getElementById('vgbBody');
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
      card('\ud83d\udcb5', 'Doanh thu Sales', 'Đơn online của sales: Pancake, Grab, Be', dsn, 'DS') + card('📑', 'Hợp đồng Event', 'Catering, teabreak, bánh thiết kế theo hợp đồng', 0, 'HDG') + '</div>';
  }
  if (isSales() || hasRole('Shipper') || hasRole('Accounts User') || hasRole('Purchase User')) {
    html += '<div class="sec">Giao hàng</div><div class="card">'
      + card('🛵', 'Vận đơn', 'Shipper giao bánh, book xe, chi phí xăng xe', 0, 'VD')
      + '</div>';
  }
  html += '<div class="sec">Khác</div><div class="card">' +
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
    if (k === 'HDG') return go(scrHopDong);
    if (k === 'VD') return go(scrVanDon);
    if (k === 'RND') return go(scrRndList);
    if (k === 'ACC') return go(scrAccount);
    go(function () { scrMRList(TYPES[k]); });
  };
  vgbGomNhom();
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
  { k: 'DH', ten: 'Đặt hàng', icon: '🛒', keys: ['Purchase', 'Transfer', 'RND', 'PAY'] },
  { k: 'SX', ten: 'Sản xuất', icon: '🧑‍🍳', keys: ['Manufacture', 'KIT', 'MFG', 'BTPO'] },
  { k: 'NK', ten: 'Nhập kho', icon: '📥', keys: ['RCV'] },
  { k: 'XK', ten: 'Xuất kho', icon: '📤', keys: ['XKH', 'XKD'] },
  { k: 'KK', ten: 'Kiểm kê', icon: '🧮', keys: ['KK', 'STOCK'] },
  { k: 'BH', ten: 'Bán hàng', icon: '🎂', keys: ['KBD', 'DS', 'HDG'] },
  { k: 'GH', ten: 'Giao hàng', icon: '🚚', keys: ['VD'] },
  { k: 'KHAC', ten: 'Khác', icon: '⚙️', keys: ['ACC'] }
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
  if (k === 'HDG') return go(scrHopDong);
  if (k === 'VD') return go(scrVanDon);
  if (k === 'RND') return go(scrRndList);
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
  if (d.docstatus === 0) {
    if (d.duoc_duyet) nut += '<button class="vxb" id="vxGhi">Ghi sổ phiếu này</button>';
    if (d.la_cua_toi || d.duoc_duyet) nut += '<button class="vxb o" id="vxXoa">Xoá bản nháp</button>';
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
    this.disabled = true;
    try {
      await api('vagabond.xuat_kho.xoa_ban_nhap', { name: name });
      toast('Đã xoá bản nháp.');
      back();
    } catch (e) {
      this.disabled = false;
      toast(e.message || 'Không xoá được.');
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
function rndBlank() {
  return { ten_hang: '', so_luong: '', link_tham_khao: '', yeu_cau_them: '', can_hoa_don: 0, trang_thai_dong: 'Chưa mua', ncc: '', sdt_ncc: '', gia: 0, ghi_chu_mua: '' };
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
          (L.can_hoa_don ? '<br>Cần hoá đơn VAT' : '') + '</div>' +
          rndLbl('Trạng thái dòng này') + rndSeg('trang_thai_dong', ['Chưa mua', 'Đã mua', 'Không mua được'], L.trang_thai_dong) +
          rndLbl('Nhà cung cấp tìm được') + rndInp('rl_ncc', 'Tên farm, shop, nhà cung cấp', L.ncc) +
          rndLbl('Điện thoại nhà cung cấp') + rndInp('rl_sdt', 'Số để lần sau gọi lại', L.sdt_ncc) +
          rndLbl('Giá mua thực tế (đồng)') + rndInp('rl_gia', '0', L.gia, 1) +
          rndLbl('Ghi chú của người mua') + rndTa('rl_gcm', 'MOQ bao nhiêu, có xuất hoá đơn không, giao mấy ngày...', L.ghi_chu_mua, 3);
      } else {
        b += rndLbl('Tên hàng cần mua') + rndInp('rl_ten', 'vd: Dứa MD2, chất bảo quản...', L.ten_hang) +
          rndLbl('Số lượng cần') + rndInp('rl_sl', 'vd: 20 kg, 2 thùng, 5 hộp', L.so_luong) +
          rndLbl('Link tham khảo (nếu có)') + rndTa('rl_link', 'Dán link Shopee, website, bài đăng...', L.link_tham_khao, 2) +
          rndLbl('Yêu cầu thêm') + rndTa('rl_yc', 'Hỏi MOQ, quy cách đóng gói, cần giao trước ngày nào...', L.yeu_cau_them, 3) +
          rndLbl('Có cần hoá đơn VAT không') + rndSeg('can_hoa_don', ['Cần hoá đơn', 'Không cần'], L.can_hoa_don ? 'Cần hoá đơn' : 'Không cần');
      }
      b += '<button class="btn" data-y>Lưu</button>';
      if (!isNew && mode !== 'buy') b += '<button class="btn dg" data-del style="margin-top:9px">Xoá dòng này</button>';
      b += '<button class="btn gh" data-n style="margin-top:9px">Huỷ</button></div>';
      ov.innerHTML = b;
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
      '<span class="st ' + s.c + '">' + h(s.t) + '</span></div>';
  }
  var body = '<div class="rcvh">Phiếu này dành cho <b>hàng mua về test</b>: không tạo mã, không theo dõi tồn kho. Ghi rõ tên hàng, số lượng và link tham khảo để bạn thu mua khỏi phải hỏi lại. Mua xong bấm <b>Hoàn thành phiếu</b>.</div>';
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
  if (!rnd.newf) rnd.newf = { muc_dich: '', ngay_can: '', ghi_chu: '', items: [] };
  var f = rnd.newf;
  function draw() {
    var body = '<div class="rcvh">Gom tất cả thứ cần mua để test vào <b>một phiếu</b> theo từng đợt, khỏi nhắn lẻ tẻ qua Lark. Hàng này không nhập kho và không tạo mã.</div>' +
      '<div class="card">' +
      '<div class="fld" data-m><div class="fi">🧪</div><div class="ft"><div class="fl">Mục đích / dự án</div><div class="fv' + (f.muc_dich ? '' : ' ph') + '">' + h(f.muc_dich || 'Bắt buộc - vd: Test bánh dứa MD2') + '</div></div><div class="fc">&#8250;</div></div>' +
      '<div class="fld" data-d><div class="fi">📅</div><div class="ft"><div class="fl">Ngày cần hàng</div><div class="fv' + (f.ngay_can ? '' : ' ph') + '">' + h(f.ngay_can ? dmy(f.ngay_can) : 'Chưa chọn') + '</div></div><div class="fc">&#8250;</div></div>' +
      '<div class="fld" data-g><div class="fi">📝</div><div class="ft"><div class="fl">Ghi chú chung</div><div class="fv' + (f.ghi_chu ? '' : ' ph') + '">' + h(f.ghi_chu || 'Không bắt buộc') + '</div></div><div class="fc">&#8250;</div></div>' +
      '</div>';
    body += '<div class="sec">Hàng cần mua (' + f.items.length + ')</div>';
    if (f.items.length) {
      body += '<div class="lst">' + f.items.map(function (it, i) {
        return '<div class="li" data-i="' + i + '"><div class="lt">' +
          '<div class="l1">' + h(it.ten_hang) + '</div>' +
          '<div class="l2">' + h(it.so_luong || 'chưa ghi số lượng') +
          (it.can_hoa_don ? ' · cần hoá đơn VAT' : '') +
          (it.link_tham_khao ? ' · có link' : '') + '</div></div>' +
          '<span class="fc" style="color:#c3c8d4;font-size:22px">&#8250;</span></div>';
      }).join('') + '</div>';
    } else {
      body += '<div class="emp"><div class="e1">🛒</div><div class="e2">Chưa có dòng nào.<br>Bấm nút bên dưới để thêm hàng.</div></div>';
    }
    body += '<div style="padding:4px 14px 10px"><button class="btn gh" id="rndAdd">+ Thêm hàng cần mua</button></div>';
    var b = frame('Yêu cầu mua hàng test', body, { footer: '<button class="btn" id="rndSave">Gửi yêu cầu</button>' });
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
    var chua = (doc.items || []).filter(function (x) { return x.trang_thai_dong === 'Chưa mua'; }).length;
    var body = '<div class="card" style="padding:13px 14px">' +
      '<div style="display:flex;align-items:center;gap:9px;margin-bottom:7px">' +
      '<b style="font-size:16.5px;flex:1">' + h(doc.muc_dich || doc.name) + '</b>' +
      '<span class="st ' + s.c + '">' + h(s.t) + '</span></div>' +
      '<div style="font-size:13.5px;color:#6b7280;line-height:1.7">' + h(doc.name) +
      (doc.ngay_can ? '<br>Cần hàng ngày ' + h(dmy(doc.ngay_can)) : '') +
      (doc.nguoi_yeu_cau ? '<br>Người yêu cầu: ' + h(doc.nguoi_yeu_cau) : '') +
      (doc.nguoi_mua ? '<br>Người mua: ' + h(doc.nguoi_mua) : '') +
      (doc.ghi_chu ? '<br>Ghi chú: ' + h(doc.ghi_chu) : '') +
      '<br>Tổng tiền đã mua: <b>' + rndMoney(tong()) + 'đ</b>' +
      '</div></div>';

    body += '<div class="sec">Hàng cần mua (' + (doc.items || []).length + ')</div><div class="lst">' +
      (doc.items || []).map(function (it, i) {
        var ls = RNDLS[it.trang_thai_dong] || RNDLS['Chưa mua'];
        var sub = h(it.so_luong || 'chưa ghi số lượng');
        if (it.can_hoa_don) sub += ' · cần hoá đơn VAT';
        if (it.ncc) sub += '<br>NCC: ' + h(it.ncc) + (it.sdt_ncc ? ' · ' + h(it.sdt_ncc) : '');
        if (it.gia) sub += '<br>Giá: ' + rndMoney(it.gia) + 'đ';
        if (it.yeu_cau_them) sub += '<br>' + h(it.yeu_cau_them);
        if (it.link_tham_khao) sub += '<br><span style="color:#0B7C93;word-break:break-all">' + h(it.link_tham_khao) + '</span>';
        if (it.ghi_chu_mua) sub += '<br>Người mua: ' + h(it.ghi_chu_mua);
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

    var ft = '';
    if (live) {
      ft = '<button class="btn" id="rndDone">Hoàn thành phiếu' + (chua ? ' (' + chua + ' dòng chưa mua)' : '') + '</button>';
      if (mine) ft += '<button class="btn gh" id="rndCancel" style="margin-top:9px">Huỷ phiếu</button>';
    }
    var b = frame('Phiếu mua test', body, ft ? { footer: ft } : {});
    b.onclick = function (e) {
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
var dsLoc = 'tat_ca';
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
    '</div>';
  html += '<div class="card" style="padding:12px 14px">' +
    '<div style="display:flex;justify-content:space-between"><span>Chưa chốt</span><b>' + money(d.tong_nhap) + ' đ · ' + nhap.length + ' đơn</b></div>' +
    '<div style="display:flex;justify-content:space-between;margin-top:6px"><span>Đã chốt</span><b style="color:#0a8a4a">' + money(d.tong_chot) + ' đ · ' + (rows.length - nhap.length) + ' đơn</b></div>' +
    (d.dong_bo_luc ? '<div style="color:#a0a6b4;font-size:12px;margin-top:6px">Máy tự đồng bộ Pancake 30 phút một lần · lần cuối ' + h(d.dong_bo_luc) + '</div>' : '') + '</div>';
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
  var DSLOC = {
    tat_ca: { nhan: 'Tất cả', loc: function () { return true; } },
    chua_pt: { nhan: 'Chưa chọn thanh toán', loc: function (r) { return r.docstatus === 0 && !r.vgb_pt_thanh_toan; } },
    chua_tien: { nhan: 'Chuyển khoản chưa về tiền', loc: function (r) { return r.vgb_pt_thanh_toan === 'Chuyển khoản' && !r.sepay_du; } },
    du_tien: { nhan: 'Đã đủ tiền', loc: function (r) { return !!r.sepay_du; } },
    chua_hddt: { nhan: 'Chưa có HĐĐT', loc: function (r) { return r.docstatus === 1 && !r.custom_hddt_so; } }
  };
  if (!DSLOC[dsLoc]) dsLoc = 'tat_ca';
  html += '<div class="card" style="padding:10px 12px;display:flex;gap:6px;flex-wrap:wrap">' +
    Object.keys(DSLOC).map(function (k) {
      var n = rows.filter(DSLOC[k].loc).length;
      var on = k === dsLoc;
      return '<button class="dsloc" data-loc="' + k + '" style="padding:6px 10px;border-radius:999px;font-size:12px;font-family:inherit;border:1.5px solid ' +
        (on ? '#0d9488;background:#ccfbf1;color:#0f766e;font-weight:bold' : '#e5e7eb;background:#fff;color:#374151') + '">' +
        DSLOC[k].nhan + ' ' + n + '</button>';
    }).join('') + '</div>';
  var loc = rows.filter(DSLOC[dsLoc].loc);
  html += '<div class="sec">Đơn trong ngày · bấm vào đơn để xem chi tiết</div><div class="card">';
  if (!rows.length) html += '<div class="emp" style="padding:24px"><div class="e1">🌤️</div><div>Chưa có đơn nào. Bấm Đồng bộ để kéo từ Pancake, hoặc dấu ➕ để nhập tay đơn Grab, Be.</div></div>';
  else if (!loc.length) html += '<div class="emp" style="padding:24px"><div class="e1">✅</div><div>Không có đơn nào thuộc nhóm <b>' + DSLOC[dsLoc].nhan + '</b>.</div></div>';
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
  if (di) di.onchange = function () { if (di.value && di.value <= today()) { dsNgay = di.value; dsLoc = 'tat_ca'; go(scrDoanhSo, true); } };
  Array.prototype.forEach.call(document.querySelectorAll('.dsloc'), function (el) {
    el.onclick = function () { dsLoc = el.getAttribute('data-loc'); go(scrDoanhSo, true); };
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
function veOMtc(pt, idO, idNhan) {
  var q = quyPt(pt) || {};
  var o = document.getElementById(idO), nh = document.getElementById(idNhan);
  if (!o) return;
  var hien = !!(q.nhan || q.bat);
  o.parentElement.style.display = hien ? '' : 'none';
  o.placeholder = (q.nhan || 'Mã tham chiếu') + (q.vd ? ' - vd ' + q.vd : '');
  o.style.borderColor = q.bat && !o.value.trim() ? '#f59e0b' : '#e5e7eb';
  if (nh) nh.innerHTML = q.bat ? '<b style="color:#b45309">Bắt buộc</b> để đối soát tự động' : (pt === 'Chuyển khoản' ? 'SePay tự khớp, để trống cũng được' : 'Không bắt buộc');
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
    html += '<div style="border:1.5px solid #e5e7eb;border-radius:10px;padding:10px;margin-top:10px">'
    + '<div id="dsvMtcNhan" style="font-size:12px;color:#6b7280;margin-bottom:6px"></div>'
    + '<input id="dsvMtc" placeholder="Mã tham chiếu" value="' + xesc(d.vgb_ma_tham_chieu) + '" style="width:100%;box-sizing:border-box;padding:9px 10px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:14px;font-family:inherit">'
    + '<div style="font-size:12px;color:#6b7280;margin-top:8px">Đối soát thanh toán: '
    + (d.vgb_ghi_chu_doi_soat ? xesc(d.vgb_ghi_chu_doi_soat) : '<span style="color:#9ca3af">chưa có, chờ máy đối soát</span>')
    + '</div></div>';
  html += '<div id="dsvSepay" style="border:1.5px solid #e5e7eb;border-radius:10px;padding:10px;margin-top:10px;font-size:13px;color:#6b7280">Đang tìm giao dịch SePay của đơn này...</div>';
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
    + '<input id="xhdMst" inputmode="numeric" placeholder="Mã số thuế (10 hoặc 13 số)" value="' + xesc(d.vgb_xhd_mst) + '" style="' + xin + '">'
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
    if (ptWrap) ptWrap.addEventListener('click', function () { setTimeout(function () { veOMtc(DSV_PT, 'dsvMtc', 'dsvMtcNhan'); }, 0); });
  veOMtc(DSV_PT, 'dsvMtc', 'dsvMtcNhan');
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
  var c1 = document.getElementById('dsvChot');
  if (c1) c1.onclick = async function () {
    if (!DSV_PT && !window.confirm('Chưa chọn phương thức thanh toán. Vẫn ghi sổ chứ?')) return;
    if (!window.confirm('Ghi sổ hoá đơn cho đơn #' + (d.custom_pancake_display_id || '') + '? Số sẽ vào doanh thu chính thức.')) return;
    busy(true);
    try { await luuXhd(d.name); await api('vagabond.ban_hang.chot_mot_don', { si_name: d.name, pt: DSV_PT, ma_tham_chieu: mtcGiaTri() }); busy(false); toast('Đã ghi sổ ' + d.name); }
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
  if (!dsTay) dsTay = { nguon: 'GrabFood', ma: '', ten: '', sdt: '', giam: '', ship: '', pt: '', mtc: '', mon: [] };
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
    '</div>';
  html += '<div class="sec">Món trong đơn</div><div class="card" style="padding:6px 14px">';
  if (!dsTay.mon.length) html += '<div style="padding:14px 0;color:#a0a6b4">Chưa có món nào, bấm Thêm món.</div>';
  dsTay.mon.forEach(function (m, i) {
    html += '<div style="display:flex;flex-direction:row;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f0f2f6">' +
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
    };
  });
  dstVeMtc();
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
    dsTay.mon.push({ item_code: o.value, ten: o.label, qty: sl, rate: gia });
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
      pt: dsTay.pt || '', ma_tham_chieu: dsTay.mtc || '',
      items: JSON.stringify(dsTay.mon.map(function (m) { return { item_code: m.item_code, qty: m.qty, rate: m.rate }; })),
      giam_gia: giam, phi_ship: ship
    });
    busy(false); toast('Đã lưu đơn nháp'); dsTay = null;
  } catch (e) { busy(false); return window.alert((e && e.message) || 'Lưu lỗi'); }
  go(scrDoanhSo, true);
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
  var html = '<div class="card" style="padding:12px 14px;display:flex;flex-direction:row;align-items:center;gap:10px">' +
    '<input type="date" class="hin" id="vdDate" value="' + vdNgay + '" style="flex:1;margin:0">' +
    '<button class="btn gh" id="vdLoc" style="flex:1;margin:0;width:auto">' + h(vdLoc || 'Tất cả') + ' ▾</button></div>';
  if (isSales() || vdLaKeToan()) html += '<button class="btn gh" id="vdDongBo" style="margin:0 0 10px">🔄 Đồng bộ đơn Pancake</button>';
  var ICON = { 'Chờ giao': '📦', 'Đang giao': '🛵', 'Đã giao': '✅', 'Không giao được': '⚠️', 'Huỷ': '⛔' };
  if (chonMode) html += '<div class="sec" style="color:#0369a1">' + (window.vdChonDe === 'in' ? 'ĐANG CHỌN ĐƠN ĐỂ IN' : 'ĐANG GỘP CHUYẾN') + ' - BẤM VÀO TỪNG ĐƠN ĐỂ CHỌN</div>';
  else html += '<div class="sec">' + ds.length + ' vận đơn · bấm vào để xử lý</div>';
  html += vdChipsHtml();
  html += '<div class="card">';
  if (!ds.length) html += '<div class="emp" style="padding:24px"><div class="e1">🛵</div><div>Chưa có vận đơn nào cho ngày này.</div></div>';
  ds.forEach(function (r) {
    var daChon = chonMode && window.vdChon[r.name];
    var d2 = (r.tag_gio ? '\u{1F552} ' + h(r.tag_gio) + ' · ' : (r.gio_giao ? r.gio_giao + ' · ' : '')) + (r.phuong ? h(vdPhuongNgan(r.phuong)) + ' · ' : '') + h(r.kenh) + (r.shipper ? ' · ' + h(vdTen(r.shipper)) : '') + (r.chuyen ? ' · 🧺' + h(r.chuyen) : '') + ' · ' + h(r.trang_thai);
    html += '<div class="hub" data-vd="' + h(r.name) + '" data-tt="' + h(r.trang_thai) + '"' + (daChon ? ' style="background:#dbeafe"' : '') + '><div class="hi">' + (daChon ? '☑️' : (ICON[r.trang_thai] || '📦')) + '</div>' +
      '<div class="ht"><div class="h1">' + (r.ma_don ? '#' + h(r.ma_don) + ' · ' : '') + h(r.khach || 'Khách lẻ') + '</div>' +
      '<div class="h2">' + d2 + '</div>' +
      '<div class="h2">' + h((r.dia_chi || '').slice(0, 70)) + '</div>' +
      (r.mon_tat ? '<div class="h2" style="color:#7a5b2e">🎂 ' + h(r.mon_tat) + '</div>' : '') + vdHuyHieu(r) + '</div>' +
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
      try { si = await getList('Sales Invoice', { fields: ['name', 'customer_name', 'grand_total', 'remarks', 'custom_pancake_display_id'], filters: { posting_date: ['>=', vdTay.ngay || today()], docstatus: ['<', 2] }, limit_page_length: 100, order_by: 'creation desc' }); }
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

var APPVER = '80';
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
function vdTuLamMoi() {
  if (vdDaGanLamMoi) return;
  vdDaGanLamMoi = 1;
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden && vdDangOManDS()) go(scrVanDon, true);
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
function vdHuyHieu(r) {
  var t = [];
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

})();


