# -*- coding: utf-8 -*-
"""v657: trang app biết máy chủ đã có bản mới và tải lại.

Dễ báo 14/11/2026: phiếu tạm tính HDB-26-11-02668 in 13:11 có mã QR chỉ còn
một góc. Dựng lại đúng phiếu bằng mã trước v655 (ảnh SVG co giãn, html2canvas
phóng to rồi cắt) ra y hệt ảnh; bằng mã hiện tại (ảnh điểm inQrAnh) ra đủ ô.
Máy quầy chạy bản cũ vì trang mở từ hôm trước, app không biết có bản mới.

Ca kiểm chạy THẬT tệp 73-ban-moi.js trong node với trang giả, không dò chuỗi.
"""

import io
import json
import os
import re
import subprocess

from vagabond import hddt_bu
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _goc():
	return os.path.dirname(os.path.dirname(os.path.abspath(hddt_bu.__file__)))


def _doc(rel):
	return io.open(os.path.join(_goc(), rel), encoding="utf-8").read()


def _appver():
	return int(re.search(r"var APPVER = '(\d+)'", _doc("vagabond/public/js/bep/12-van-don.js")).group(1))


@ca("v657 bản mới: máy chủ đọc đúng số APPVER của tệp nguồn đang cài")
def _may_chu():
	from vagabond import phien_ban_app as p
	dung("tệp nguồn có thật", os.path.exists(p.TEP_APPVER))
	la("số bản máy chủ trả về", p.doc_so(), _appver())
	la("cửa hien_tai trả đúng số", p.hien_tai(), {"appver": _appver()})
	la("tệp không có thì -1, không lỗi", p.doc_so("/khong/co/tep.js"), -1)


_NODE = r"""
var vm = require('vm'), fs = require('fs');
function moi(o) {
  var ss = {}, nav = [], the = {};
  var c = {
    APPVER: o.appver, S: o.S, hardNav: function () { nav.push(1); },
    sessionStorage: { getItem: function (k) { return k in ss ? ss[k] : null; }, setItem: function (k, v) { ss[k] = String(v); } },
    document: { hidden: false, addEventListener: function () {},
      getElementById: function (id) { return the[id] || null; },
      createElement: function () { return { setAttribute: function () {}, set innerHTML(v) { this._h = v; } }; },
      body: { appendChild: function (d) { the[d.id] = d; the.vgbBanMoiTai = {}; } } },
    setInterval: function () {}, Date: Date, parseInt: parseInt, isFinite: isFinite, String: String
  };
  c.scrHome = function () {};
  if (o.trangChu) c.S.stack = [c.scrHome];
  vm.createContext(c);
  vm.runInContext(fs.readFileSync(TEP, 'utf8'), c);
  c.nav = nav; c.the = the; c.ss = ss;
  return c;
}
var kq = {};
var a = moi({ appver: '656', S: { stack: [], draft: null }, trangChu: 1 });
kq.can = [a.banMoiCanTai('656', 657), a.banMoiCanTai('657', 657), a.banMoiCanTai('657', -1), a.banMoiCanTai('657', 'x'), a.banMoiCanTai('657', 658)];
kq.trangChu = a.banMoiXuLy(657); kq.trangChuNav = a.nav.length; kq.trangChuDai = !!a.the.vgbBanMoi;
// Tải lại xong mà mã vẫn cũ (cùng phiên thẻ): không tải lặp, chỉ hiện dải.
kq.lan2 = a.banMoiXuLy(657); kq.lan2Nav = a.nav.length; kq.lan2Dai = !!a.the.vgbBanMoi;
var b = moi({ appver: '656', S: { stack: [function () {}, function () {}], draft: null } });
kq.dangLam = b.banMoiXuLy(657); kq.dangLamNav = b.nav.length; kq.dangLamDai = !!b.the.vgbBanMoi;
// Mở một màn từ trang chủ: trang chủ nằm dưới đáy chồng, màn đang làm ở trên.
var g = moi({ appver: '656', S: { stack: [], draft: null }, trangChu: 1 });
g.S.stack.push(function () {});
kq.trenTrangChu = g.banMoiXuLy(657); kq.trenTrangChuNav = g.nav.length;
var d = moi({ appver: '656', S: { stack: [], draft: { items: [1] } }, trangChu: 1 });
kq.phieuDo = d.banMoiXuLy(657); kq.phieuDoNav = d.nav.length;
var e = moi({ appver: '657', S: { stack: [], draft: null }, trangChu: 1 });
kq.bangNhau = e.banMoiXuLy(657); kq.bangNhauNav = e.nav.length; kq.bangNhauDai = !!e.the.vgbBanMoi;
var f = moi({ appver: '656', S: { stack: [], draft: null }, trangChu: 1 });
kq.mayChuLoi = f.banMoiXuLy(undefined);
process.stdout.write(JSON.stringify(kq));
"""


@ca("v657 bản mới: trang chủ thì tự tải lại một lần, đang làm thì chỉ hiện dải báo")
def _trang():
	tep = os.path.join(_goc(), "vagabond", "public", "js", "bep", "73-ban-moi.js")
	r = subprocess.run(["node", "-e", "var TEP=%s;%s" % (json.dumps(tep), _NODE)],
		capture_output=True, text=True, timeout=60)
	dung("node chạy được: " + r.stderr[-300:], r.returncode == 0)
	if r.returncode:
		return
	k = json.loads(r.stdout)
	la("so số bản", k["can"], [True, False, False, False, True])
	la("trang chủ, máy chủ mới hơn: tự tải lại", [k["trangChu"], k["trangChuNav"], k["trangChuDai"]], ["tai", 1, False])
	la("tải rồi mà vẫn cũ: không tải lặp, hiện dải", [k["lan2"], k["lan2Nav"], k["lan2Dai"]], ["bao", 1, True])
	la("đang làm một màn: không tự tải, hiện dải", [k["dangLam"], k["dangLamNav"], k["dangLamDai"]], ["bao", 0, True])
	la("màn mở chồng lên trang chủ: không tự tải", [k["trenTrangChu"], k["trenTrangChuNav"]], ["bao", 0])
	la("phiếu soạn dở ở trang chủ: không tự tải", [k["phieuDo"], k["phieuDoNav"]], ["bao", 0])
	la("cùng số bản: không làm gì", [k["bangNhau"], k["bangNhauNav"], k["bangNhauDai"]], ["giu", 0, False])
	la("máy chủ không trả số: không làm gì", k["mayChuLoi"], "giu")


@ca("v657 bản mới: dải báo có nút cao 44 điểm, chữ theo quy tắc chữ")
def _dai():
	js = _doc("vagabond/public/js/bep/73-ban-moi.js")
	dung("nút Tải lại cao 44", "min-height:44px" in js and "🔄 Tải lại</button>" in js)
	dung("gọi phần mềm là hệ thống", "Hệ thống đã có bản app mới" in js)
	dung("hỏi thẳng máy chủ, không qua api() để không bật màn đăng nhập",
		"fetch('/api/method/vagabond.phien_ban_app.hien_tai" in js)
