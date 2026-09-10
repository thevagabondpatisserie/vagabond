# -*- coding: utf-8 -*-
"""Canh giao dien Chi dot nay va Can coc cua Issue #247."""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la


GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _js(ten):
	return io.open(os.path.join(GOI, "public", "js", "bep", ten), encoding="utf-8").read()


def _doan(src, dau, cuoi):
	i = src.index(dau)
	return src[i:src.index(cuoi, i + len(dau))]


@ca("#247 UX Chi dot nay dung dung lop chung va checkbox that")
def _lop_dung_cho():
	nen = _js("00-nen.js")
	man = _js("19-ho-so-tt.js")
	for cu in ('class="hub-i"', 'class="hub-t"', 'class="t1"', 'class="t2"'):
		la("khong con lop khong co CSS %s" % cu, cu in man, False)
	la("khong con nhet o toan man vao nhan Chi dot nay",
		'<label>Chi đợt này<input class="tin"' in man, False)
	for moi in (".otd{", ".tik{", ".hub.chon{"):
		dung("co lop chung %s" % moi, moi in nen)
	dung("dung checkbox that", 'type="checkbox" class="tik" data-hstick=' in man)
	dung("co duong nhap nhanh Chi het", 'data-hshet=' in man)
	dung("man Chi cong ty cung co Chi het", 'data-huhet=' in man)
	la("khong con id dem chon khong su dung", 'id="hsDemChon"' in man, False)
	dung("o Chi dot nay nghe input bang addEventListener",
		"b.addEventListener('input', function (e)" in man)


@ca("#247 UX sao ke hoan ung dung checkbox va mau chon chung")
def _sao_ke_hoan_ung_dong_bo():
	man = _js("19-ho-so-tt.js")
	doan = _doan(man, "async function scrHuSepay(", "\n/* Sua mot khoan chi.")
	dung("co checkbox that cho giao dich sao ke", 'type="checkbox" class="tik" data-hugdtick=' in doan)
	la("khong con mau xanh ngoai bang mau trong man sao ke", "#dbeafe" in doan.lower(), False)
	la("khong con ky tu checkbox gia", "☑️" in doan or "⬜" in doan, False)


@ca("#247 UX cot chu va o tien giu hai luat co gian can phai")
def _luat_co_gian_va_can_tien():
	nen = _js("00-nen.js")
	# Hai dong nay co y canh theo mau NGUYEN VEN. Dot bien bo dung phan
	# chiu luc phai lam ca nay do, khong duoc xanh vi tim thay mot lop rong.
	dung("cot chu co gian dung mot lan",
		nen.count(".hub .ht{flex:1;min-width:0}") == 1)
	dong = [x for x in nen.splitlines() if x.startswith(".otd .ow input{")]
	dung("chi co mot luat o tien trong dong", len(dong) == 1)
	dung("o tien can phai", len(dong) == 1 and "text-align:right" in dong[0])


@ca("#247 UX cac nut long trong dong duoc chan truoc su kien ca dong")
def _thu_tu_su_kien():
	src = _js("19-ho-so-tt.js")
	than = _doan(src, "var b = frame(tenMan, html, { footer: foot });", "var dangHien = function () {")
	i_tick = than.index("var n = e.target.closest('[data-hstick]')")
	i_het = than.index("var n = e.target.closest('[data-hshet]')")
	i_bth = than.index("var n = e.target.closest('[data-hsbth]')")
	i_hang = than.index("var r = e.target.closest('[data-hsh]')")
	dung("tick roi Chi het roi Ban the hien roi moi toi ca dong",
		i_tick < i_het < i_bth < i_hang)


@ca("#247 UX Can coc va Noi sao ke dung danh sach, tom tat va trang thai rong")
def _danh_sach_can_coc():
	src = _js("19-ho-so-tt.js")
	la("khong con dung nut lon cho tung khoan coc",
		'class="btn gh" data-hscoc' in src, False)
	la("khong con dung nut lon cho tung dong sao ke",
		'class="btn gh" data-cocgd' in src, False)
	for chu in (
		'class="li" data-hscoc=', 'class="li" data-cocgd=',
		'Hoá đơn đã chọn', 'Cần cấn', 'Cọc còn',
		'<div class="emp"><div class="e1">🏦</div>',
		'<div class="emp"><div class="e1">🔍</div>',
		'-webkit-line-clamp:2'):
		dung("co mau giao dien %s" % chu, chu in src)
	dung("chip cọc dùng lớp trạng thái xanh và vàng",
		"'<div style=\"margin-top:5px\"><span class=\"st ' + (san ? 'g' : 'w') + '\">'" in src)
	la("không gán object ngược vào element.style",
		"nut.style = nut.style || {}" in src, False)


@ca("#247 UX khoa dong Can coc truoc await de chan bam hai lan")
def _khoa_truoc_await():
	src = _js("19-ho-so-tt.js")
	for dau, cuoi in (
		("async function hsChonCanCoc(", "\nasync function hsThuLaiCanCoc("),
		("async function hsChonSaoKeCoc(", "\nfunction hsDocTienDot(")):
		than = _doan(src, dau, cuoi)
		dung("khoa truoc xac nhan cua %s" % dau,
			than.index("hsKhoaDongCoc(nut, true)") < than.index("await xacNhan("))
		dung("mo khoa khi loi", "hsKhoaDongCoc(nut, false)" in than)
