/* Kiem banh ngay v3 - them Cho chot + ten khach (y Loan Anh 01/08); truoc do v2 - them tab cac ngay ke tiep (01/08: anh Viet yeu cau,
   de bep gom san xuat truoc; banh HSD 3 ngay, lam truoc ra dong roi do glaze).
   Chay trong truong `javascript` cua Web Page /kiem-banh.
   Boot trong window load - bai hoc CSRF tu app /bep. */
(function () {
	var DL = null, DANG_SUA = null, VE_TRUOC = null, NGAY_CHON = null;
	var BTP = {}; // ma -> {so_btp, con_nhan} tu bang BTP cua bep
	var BTP_SUA = false; // chi bep duoc sua (server quyet qua quyen_btp)
	var SO_NGAY = 4; // hom nay + 3 ngay ke

	function ngayISO(d) {
		return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
	}
	function homNay() { return ngayISO(new Date()); }
	function fmtVN(iso) { return iso.slice(8, 10) + "/" + iso.slice(5, 7) + "/" + iso.slice(0, 4); }
	function fmtNgan(iso) { return iso.slice(8, 10) + "/" + iso.slice(5, 7); }

	function API(m, b) {
		var h = { "Content-Type": "application/json", "Accept": "application/json" };
		var tk = window.csrf_token || (window.frappe && frappe.csrf_token);
		if (tk && tk !== "None") h["X-Frappe-CSRF-Token"] = tk;
		return fetch("/api/method/vagabond.kiem_banh." + m, {
			method: "POST", headers: h, credentials: "same-origin",
			body: JSON.stringify(b || {})
		}).then(function (r) {
			if (r.status === 403 || r.status === 401) {
				location.href = "/login?redirect-to=/kiem-banh"; throw new Error("login");
			}
			return r.json().then(function (j) {
				if (!r.ok) {
					var loi = j.exception || "Loi he thong";
					try { loi = JSON.parse(JSON.parse(j._server_messages)[0]).message; } catch (e) {}
					throw new Error(loi);
				}
				return j.message;
			});
		});
	}

	function bao(t, xau) {
		var el = document.getElementById("kb-bao");
		el.textContent = t; el.className = xau ? "loi" : "";
		if (t) setTimeout(function () { if (el.textContent === t) el.textContent = ""; }, 4000);
	}

	function veChips() {
		var g = document.getElementById("kb-chips");
		var t = new Date(); t.setHours(0, 0, 0, 0);
		var h = "";
		for (var i = 0; i < SO_NGAY; i++) {
			var d = new Date(t); d.setDate(t.getDate() + i);
			var iso = ngayISO(d);
			h += '<button class="kb-chip' + (iso === NGAY_CHON ? " on" : "") + '" data-ngay="' + iso + '">'
				+ (i === 0 ? "Hôm nay " : "") + fmtNgan(iso) + "</button>";
		}
		g.innerHTML = h;
		document.getElementById("kb-ngay-to").textContent = fmtVN(NGAY_CHON);
		// Chot ngay chi danh cho HOM NAY - ngay mai chua ban xong thi chot gi.
		var laHomNay = NGAY_CHON === homNay();
		document.getElementById("kb-chot").style.display = laHomNay ? "" : "none";
	}

	function chonNgay(iso) {
		NGAY_CHON = iso; DL = null; VE_TRUOC = null; DANG_SUA = null;
		veChips();
		document.getElementById("kb-luoi").innerHTML = '<div class="kb-trong">Đang tải ngày ' + fmtVN(iso) + "...</div>";
		API("dong_bo", { ngay: iso }).then(nhan).catch(function () { taiLai(true); });
	}

	function nhan(m) {
		// Chong dua nhau: nguoi dung vua doi tab ngay thi bo qua ket qua cu.
		if (!m || m.ngay !== NGAY_CHON) return;
		DL = m;
		document.getElementById("kb-luc").textContent =
			m.dong_bo_luc ? "Đồng bộ Pancake lúc " + m.dong_bo_luc.slice(11, 16) : "Chưa đồng bộ";
		var chot = m.tinh_trang === "Da chot";
		if (chot) document.getElementById("kb-chot").style.display = "none";
		document.getElementById("kb-dachot").style.display = chot ? "" : "none";
		ve();
	}

	function taiLai() { return API("bang", { ngay: NGAY_CHON }).then(nhan).catch(function (e) { bao(e.message, true); }); }

	function nsxLui(n) {
		var d = new Date(NGAY_CHON + "T00:00:00");
		d.setDate(d.getDate() - n);
		return ("0" + d.getDate()).slice(-2) + "/" + ("0" + (d.getMonth() + 1)).slice(-2);
	}
	function fmtNSX(iso) { if (!iso) return ""; return iso.slice(8, 10) + "/" + iso.slice(5, 7); }

	function ve() {
		var g = document.getElementById("kb-luoi");
		/* Dang go do trong o thi khong ve lai, ve lai la mat so dang go. */
		var dangGo = document.getElementById("kb-inp");
		if (DANG_SUA !== null && dangGo && document.activeElement === dangGo) return;
		var khoa = JSON.stringify([NGAY_CHON, DL && DL.dong, DANG_SUA, BTP, BTP_SUA]);
		if (khoa === VE_TRUOC && g.childElementCount) return;
		VE_TRUOC = khoa;
		if (!DL || !DL.dong.length) {
			g.innerHTML = '<div class="kb-trong">Ngày ' + fmtVN(NGAY_CHON) + ' chưa có đơn nào và chưa có dòng nào.<br>Bấm Đồng bộ để kéo đơn từ Pancake, hoặc Thêm mã cho bánh bếp định làm.</div>';
			return;
		}
		var h = "";
		DL.dong.slice().sort(function (a, b) { return a.ma_hang < b.ma_hang ? -1 : 1; })
			.forEach(function (d) {
				var ban = d.co_the_ban;
				h += '<div class="kb-the">'
					+ '<div class="kb-ten">'
					+ (d.hinh ? '<img src="' + d.hinh + '" loading="lazy" alt="">' : '<i class="kb-noimg"></i>')
					+ '<b>' + d.ma_hang + '</b><span>' + (d.ten_banh || "") + "</span>" + nutXoa(d) + "</div>"
					+ '<div class="kb-so">'
					+ o(d, "ton_d1", "Tồn " + (fmtNSX(d.nsx_d1) || nsxLui(1)), d.ton_d1, true)
					+ o(d, "ton_d2", "Tồn " + (fmtNSX(d.nsx_d2) || nsxLui(2)), d.ton_d2, true)
					+ o(d, "ton_cu", d.nsx_cu ? "Tồn " + fmtNSX(d.nsx_cu) : "Tồn cũ hơn", d.ton_cu, true)
					+ o(d, "sx", "Bếp làm " + NGAY_CHON.slice(8, 10) + "/" + NGAY_CHON.slice(5, 7), d.sx, true)
					+ o(d, "da_dat", "Đã đặt", d.da_dat, false)
					+ o(d, "phat_sinh", "Phát sinh", d.phat_sinh, false)
					+ oKhach("Khách phát sinh", d.ten_khach_ps)
					+ oCho(d.cho_chot)
					+ oKhach("Khách chờ", d.ten_khach_cho)
					+ oKhac(d.don_khac)
					+ oKhach('Đơn kênh khác', d.ten_khach_khac)
					+ '<div class="kb-o kb-ban ' + (ban < 0 ? "am" : (ban ? "duong" : "")) + '"><label>BÁN ĐƯỢC</label><b>' + ban + "</b></div>"
					+ oBTP(d.ma_hang, "so_btp", "BTP sẵn")
					+ oBTP(d.ma_hang, "so_decor", "Đủ decor")
					+ oGiaoMai(d.ma_hang)
					+ oNhan2(d.ma_hang)
					+ "</div></div>";
			});
		g.innerHTML = h;
		ganInput();
		ganXoa(g);
	}

	/* Dau x go mot dong go nham. Chi hien khi ca dong chua co so nao, nen
	   khong the lo tay lam mat so cua bep hay cua sales. Han bao 03/08/2026:
	   so co hai dong rac la BAWC00025 va mot dong ten dung "BAWC". */
	function trongTron(d) {
		return !(d.ton_cu || d.ton_d2 || d.ton_d1 || d.sx || d.da_dat || d.phat_sinh || d.cho_chot || d.don_khac);
	}

	function nutXoa(d) {
		if (!trongTron(d)) return "";
		return '<button type="button" data-xoa="' + d.ma_hang + '" title="Xoa ma go nham"'
			+ ' style="margin-left:auto;border:0;background:transparent;color:#b23;'
			+ 'font-size:18px;line-height:1;padding:2px 8px;cursor:pointer">&#10005;</button>';
	}

	function ganXoa(g) {
		if (g.__daGanXoa) return;
		g.__daGanXoa = 1;
		g.addEventListener("click", function (e) {
			var n = e.target && e.target.closest ? e.target.closest("[data-xoa]") : null;
			if (!n) return;
			e.preventDefault();
			e.stopPropagation();
			var ma = n.getAttribute("data-xoa");
			if (!window.confirm("Xoá mã " + ma + " khỏi bảng ngày " + fmtVN(NGAY_CHON) + "?")) return;
			API("xoa_dong", { ngay: NGAY_CHON, ma_hang: ma })
				.then(function () { taiLai(); bao("Đã xoá " + ma); })
				.catch(function (e2) { bao(e2.message, true); });
		});
	}

	function o(d, truong, nhan, gt, sua) {
		var id = d.ma_hang + "|" + truong;
		if (DANG_SUA === id) {
			return '<div class="kb-o dang"><label>' + nhan + '</label>'
				+ '<input id="kb-inp" type="number" min="0" inputmode="numeric" value="' + (gt || 0) + '">' + nutOK() + '</div>';
		}
		return '<div class="kb-o' + (sua ? " sua" : "") + '" data-id="' + id + '">'
			+ "<label>" + nhan + "</label><b>" + (gt || 0) + "</b></div>";
	}

	function chuSach(t) {
		return String(t || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
	}
	function oKhach(nhan, ds) {
		return '<div class="kb-o khach"><label>' + nhan + '</label><div>' + (chuSach(ds) || "&nbsp;") + '</div></div>';
	}
	function oCho(gt) {
		return '<div class="kb-o cho' + (gt ? " co" : "") + '"><label>Chờ chốt</label><b>' + (gt || 0) + '</b></div>';
	}
	/* Banh ban qua Grab, Shopee, khach si, quay - khong di qua Pancake nen
	   khong co don Pancake de dem. May dem thang tu hoa don ban ra trong
	   ngay (08/08/2026, y Loan Anh - truoc day phai tao mot don Pancake gia
	   de tru so, thanh ra mot khach hai bill). */
	function oKhac(gt) {
		return '<div class="kb-o khac' + (gt ? ' co' : '') + '"><label>Kênh khác</label><b>' + (gt || 0) + '</b></div>';
	}


	function nutOK() {
		/* Dien thoai can mot nut chot so ro rang - khong the trong cho blur. */
		return '<button type="button" id="kb-ok" aria-label="Chot so" style="margin-left:6px;'
			+ 'min-width:40px;height:34px;border:0;border-radius:8px;background:#16a34a;'
			+ 'color:#fff;font-size:17px;line-height:1;font-weight:700;vertical-align:middle">\u2713</button>';
	}

	function ganInput() {
		/* Tren dien thoai su kien blur hay khong ban ra: nguoi dung go xong roi de
		   nguyen do, hoac luoi bi ve lai lam mat o input truoc khi blur kip chay.
		   So vua go bi mat, man hinh ve lai so cu nen bep thay nhu la "nhap so nao
		   cung nhay ve 0". Nen chot so theo 5 duong: nut OK, phim Enter, su kien
		   change, go xong 3 giay tu luu, va blur. */
		var inp = document.getElementById("kb-inp");
		if (!inp || inp.__daGan) return;
		inp.__daGan = 1;
		var hen = null;
		var hoan = function () { if (hen) { clearTimeout(hen); hen = null; } };
		inp.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); hoan(); luuO(); } });
		inp.addEventListener("input", function () { hoan(); hen = setTimeout(function () { hen = null; luuO(); }, 3000); });
		inp.addEventListener("change", function () { hoan(); luuO(); });
		inp.addEventListener("blur", function () { hoan(); luuO(); });
	}

	function luuO() {
		var inp = document.getElementById("kb-inp");
		if (!inp || DANG_SUA === null) return;
		var phan = DANG_SUA.split("|"), ma = phan[0], truong = phan[1];
		var gt = parseInt(inp.value || "0", 10);
		DANG_SUA = null;
		if (truong === "so_btp" || truong === "so_decor") { luuBTP(ma, gt, truong); return; }
		API("luu_o", { ngay: NGAY_CHON, ma_hang: ma, truong: truong, gia_tri: gt })
			.then(function () { return taiLai(); })
			.catch(function (e) { bao(e.message, true); taiLai(); });
	}

	function ganSuKien() {
		document.getElementById("kb-chips").addEventListener("click", function (ev) {
			var c = ev.target.closest(".kb-chip"); if (!c) return;
			chonNgay(c.getAttribute("data-ngay"));
		});
		document.getElementById("kb-luoi").addEventListener("click", function (ev) {
			if (ev.target.closest("#kb-ok")) { luuO(); return; }
			var oEl = ev.target.closest(".kb-o.sua");
			if (!oEl) return;
			if (DL && DL.tinh_trang === "Da chot") { bao("Ngày này đã chốt sổ, không sửa nữa", true); return; }
			DANG_SUA = oEl.getAttribute("data-id");
			ve();
			var inp = document.getElementById("kb-inp");
			if (inp) { inp.focus(); inp.select(); ganInput(); }
		});
		document.getElementById("kb-dongbo").onclick = function () {
			bao("Đang kéo đơn từ Pancake...");
			API("dong_bo", { ngay: NGAY_CHON }).then(function (m) { nhan(m); bao("Đã đồng bộ xong"); })
				.catch(function (e) { bao(e.message, true); });
		};
		document.getElementById("kb-them").onclick = kbChonMon;
		var nTuVan = document.getElementById("kb-tuvan");
		if (nTuVan) nTuVan.onclick = kbTuVan;
		document.getElementById("kb-chot").onclick = function () {
			if (!window.confirm("Chốt sổ hôm nay? Số còn lại sẽ chuyển thành tồn đầu ngày mai và bảng hôm nay bị khoá.")) return;
			bao("Đang chốt ngày...");
			API("chot_ngay", { ngay: NGAY_CHON }).then(function () { taiLai(); bao("Đã chốt. Tồn đã chuyển sang ngày mai."); })
				.catch(function (e) { bao(e.message, true); });
		};
	}

	/* ---- Bang chon mon va bang tu van (anh Viet 03/08/2026) ----
	   Nut "Them ma" truoc day bat go tay vao window.prompt: sales tren dien
	   thoai go nham ma hoai, ma go nham thi server chan nhung van mat cong.
	   Gio mo bang tim co ten, ma va anh - giong bang chon mon luc chot doanh
	   thu ben /bep. Nut "Banh con ban" tra loi cau hoi sales hoi nhieu nhat:
	   gio nay con con gi de tu van cho khach. */

	function kbEsc(s) {
		return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
			.replace(/>/g, "&gt;").replace(/"/g, "&quot;");
	}

	function kbAnh(url, chu) {
		if (url) {
			return '<img src="' + kbEsc(url) + '" loading="lazy" style="width:46px;height:46px;'
				+ 'border-radius:8px;object-fit:cover;flex:0 0 46px;background:#f3f3f3">';
		}
		return '<div style="width:46px;height:46px;border-radius:8px;background:#f3f3f3;display:flex;'
			+ 'align-items:center;justify-content:center;flex:0 0 46px;font-size:22px">' + (chu || "🎂") + '</div>';
	}

	function kbLop(tieuDe) {
		var ov = document.createElement("div");
		ov.style.cssText = "position:fixed;left:0;top:0;right:0;bottom:0;background:rgba(0,0,0,.45);"
			+ "z-index:9999;display:flex;align-items:flex-end;justify-content:center";
		var box = document.createElement("div");
		box.style.cssText = "background:#fff;width:100%;max-width:560px;max-height:88vh;"
			+ "border-radius:16px 16px 0 0;display:flex;flex-direction:column;overflow:hidden";
		box.innerHTML = '<div style="padding:13px 16px;border-bottom:1px solid #eee;display:flex;'
			+ 'align-items:center;justify-content:space-between;gap:10px">'
			+ '<b style="font-size:16px">' + kbEsc(tieuDe) + '</b>'
			+ '<span data-dong="1" style="font-size:28px;line-height:1;color:#999;cursor:pointer;'
			+ 'padding:0 6px">&times;</span></div>';
		ov.appendChild(box);
		ov.dongLai = function () { if (ov.parentNode) ov.parentNode.removeChild(ov); };
		ov.onclick = function (e) {
			if (e.target === ov || (e.target.getAttribute && e.target.getAttribute("data-dong"))) ov.dongLai();
		};
		document.body.appendChild(ov);
		ov.hop = box;
		return ov;
	}

	function kbChonMon() {
		if (DL && DL.tinh_trang === "Da chot") {
			bao("Ngày này đã chốt sổ, không thêm mã nữa", true);
			return;
		}
		var ov = kbLop("Thêm bánh cho ngày " + fmtVN(NGAY_CHON));
		var oTim = document.createElement("div");
		oTim.style.cssText = "padding:10px 16px 6px";
		oTim.innerHTML = '<input id="kb-ptim" placeholder="Gõ tên hoặc mã bánh" autocomplete="off" '
			+ 'style="width:100%;height:46px;padding:0 12px;border:1px solid #ddd;border-radius:10px;'
			+ 'font-size:16px;box-sizing:border-box">';
		var ds = document.createElement("div");
		ds.style.cssText = "flex:1;overflow:auto;padding:2px 8px 18px;min-height:240px";
		ov.hop.appendChild(oTim);
		ov.hop.appendChild(ds);

		var tmr = null, phienChay = 0;
		function nhanTrong(t) {
			ds.innerHTML = '<div style="padding:26px 10px;text-align:center;color:#999">' + kbEsc(t) + '</div>';
		}
		function veDs(rs) {
			if (!rs.length) { nhanTrong("Không thấy mã nào khớp"); return; }
			ds.innerHTML = rs.map(function (r) {
				return '<div data-ma="' + kbEsc(r.ma) + '" data-co="' + (r.da_co ? 1 : 0) + '" '
					+ 'style="display:flex;align-items:center;gap:10px;padding:9px 8px;'
					+ 'border-bottom:1px solid #f2f2f2;cursor:pointer' + (r.da_co ? ';opacity:.45' : '') + '">'
					+ kbAnh(r.anh)
					+ '<div style="flex:1;min-width:0">'
					+ '<div style="font-weight:600;font-size:15px">' + kbEsc(r.ten || r.ma) + '</div>'
					+ '<div style="font-size:12.5px;color:#888">' + kbEsc(r.ma)
					+ (r.da_co ? " · đã có trong bảng" : "") + '</div></div></div>';
			}).join("");
		}
		function chay(q) {
			phienChay++;
			var phien = phienChay;
			nhanTrong("Đang tìm...");
			API("tim_mon", { tu_khoa: q, ngay: NGAY_CHON })
				.then(function (rs) { if (phien === phienChay) veDs(rs || []); })
				.catch(function (e) { if (phien === phienChay) nhanTrong(e.message || "Lỗi tìm mã"); });
		}
		ds.onclick = function (ev) {
			var n = ev.target.closest("[data-ma]");
			if (!n) return;
			if (n.getAttribute("data-co") === "1") { bao("Mã này đã có trong bảng rồi", true); return; }
			var ma = n.getAttribute("data-ma");
			ov.dongLai();
			bao("Đang thêm " + ma + "...");
			API("them_dong", { ngay: NGAY_CHON, ma_hang: ma })
				.then(function () { taiLai(); bao("Đã thêm " + ma); })
				.catch(function (e) { bao(e.message, true); });
		};
		var inp = oTim.firstChild;
		inp.oninput = function () {
			clearTimeout(tmr);
			var v = inp.value.trim();
			tmr = setTimeout(function () { chay(v); }, 280);
		};
		chay("");
		setTimeout(function () { inp.focus(); }, 60);
	}

	function kbTuVan() {
		if (!DL || !DL.dong || !DL.dong.length) { bao("Chưa có dữ liệu ngày này", true); return; }
		var conBan = [], maiGiao = [], het = [];
		DL.dong.forEach(function (d) {
			var b = BTP[d.ma_hang] || {};
			var o = {
				ma: d.ma_hang, ten: d.ten_banh || d.ma_hang, anh: d.hinh || "",
				ban: d.co_the_ban || 0,
				cho: d.cho_chot || 0,
				mai: Math.max(0, b.giao_mai || 0),
				btp: b.con_nhan || 0
			};
			if (o.ban > 0) conBan.push(o);
			else if (o.mai > 0) maiGiao.push(o);
			else het.push(o);
		});
		function sapXep(a) { a.sort(function (x, y) { return (y.ban - x.ban) || (y.mai - x.mai); }); }
		/* Sales de nghi 06/08/2026: gom cac size cua cung mot loai banh lai voi nhau.
		   Truoc day xep thuan theo so con ban nen 12cm va 16cm cua cung mot banh nam
		   cach xa nhau, sales phai do mat tim va de bo sot size. */
		function kbTachTen(t) {
			t = String(t || "");
			var m = t.match(/^(.*?)[,\s]*\bsize\b\s*(.*)$/i);
			if (!m) return { goc: t.trim(), size: "" };
			return { goc: (m[1] || "").replace(/[,\s]+$/, "").trim(), size: (m[2] || "").trim() };
		}
		function kbCoSize(s2) { var m = String(s2 || "").match(/\d+/); return m ? parseInt(m[0], 10) : 999; }
		function kbGomNhom(ds, kieu) {
			var nhom = [], viTri = {};
			ds.forEach(function (o) {
				var t = kbTachTen(o.ten);
				if (!(t.goc in viTri)) { viTri[t.goc] = nhom.length; nhom.push({ goc: t.goc, ds: [], ban: 0, mai: 0 }); }
				var n = nhom[viTri[t.goc]];
				n.ds.push({ o: o, size: t.size });
				n.ban += o.ban || 0; n.mai += o.mai || 0;
			});
			nhom.sort(function (x, y) {
				return (y.ban - x.ban) || (y.mai - x.mai) || x.goc.localeCompare(y.goc, "vi");
			});
			return nhom.map(function (n) {
				n.ds.sort(function (x, y) { return kbCoSize(x.size) - kbCoSize(y.size); });
				var dau = '<div style="padding:10px 8px 1px;font-weight:700;font-size:14.5px;color:#111">'
					+ kbEsc(n.goc) + (n.ds.length > 1 ? ' <span style="font-weight:600;font-size:12px;color:#888">'
					+ n.ds.length + ' size</span>' : '') + '</div>';
				return dau + n.ds.map(function (x) {
					var ban = {};
					for (var k in x.o) ban[k] = x.o[k];
					if (x.size) ban.ten = "Size " + x.size;
					return dongMon(ban, kieu);
				}).join("");
			}).join("");
		}
		sapXep(conBan); sapXep(maiGiao); sapXep(het);

		var ov = kbLop("Bánh còn bán ngày " + fmtVN(NGAY_CHON));
		var than = document.createElement("div");
		than.style.cssText = "flex:1;overflow:auto;padding:0 8px 20px";
		ov.hop.appendChild(than);

		function dongMon(o, kieu) {
			var phu = "";
			if (kieu === "ban") {
				phu = "Bán được <b>" + o.ban + "</b>"
					+ (o.cho ? ' · <span style="color:#c47f00">' + o.cho + " đang giữ chỗ</span>" : "")
					+ (o.mai ? ' · mai giao thêm ' + o.mai : "");
			} else if (kieu === "mai") {
				phu = 'Hôm nay hết · <b style="color:#0a7">nhận giao mai ' + o.mai + "</b>";
			} else {
				phu = "Hết hàng" + (o.cho ? " · " + o.cho + " đang giữ chỗ" : "");
			}
			return '<div style="display:flex;align-items:center;gap:10px;padding:9px 8px;'
				+ 'border-bottom:1px solid #f2f2f2' + (kieu === "het" ? ';opacity:.5' : '') + '">'
				+ kbAnh(o.anh)
				+ '<div style="flex:1;min-width:0">'
				+ '<div style="font-weight:600;font-size:15px">' + kbEsc(o.ten) + '</div>'
				+ '<div style="font-size:12.5px;color:#666">' + phu + '</div>'
				+ '<div style="font-size:11.5px;color:#aaa">' + kbEsc(o.ma) + '</div></div>'
				+ (kieu === "ban" ? '<div style="font-size:22px;font-weight:800;color:#0a7;min-width:34px;'
					+ 'text-align:right">' + o.ban + '</div>' : '') + '</div>';
		}
		function nhomHtml(ten, mau, ds, kieu) {
			if (!ds.length) return "";
			return '<div style="padding:11px 8px 5px;font-weight:700;font-size:13px;color:' + mau + '">'
				+ kbEsc(ten) + " (" + ds.length + ")</div>"
				+ kbGomNhom(ds, kieu);
		}
		var tong = 0;
		conBan.forEach(function (o) { tong += o.ban; });
		than.innerHTML = '<div style="padding:12px 8px 4px;font-size:13.5px;color:#555">'
			+ 'Còn <b>' + tong + '</b> cái của <b>' + conBan.length + '</b> mã bán được hôm nay. '
			+ 'Số này đã trừ đơn đã chốt và đơn đang giữ chỗ.</div>'
			+ '<div style="padding:0 8px 9px;font-size:12.5px;color:#0a7;line-height:1.45">'
			+ 'Đúng danh sách này đang hiện cho khách ở <a href="https://order.thevagabondpatisserie.com/banh" target="_blank" style="color:#0a7">order.thevagabondpatisserie.com</a>. '
			+ 'Bấm “Thêm mã” là bánh lên web ngay, khỏi báo ai.</div>'
			+ nhomHtml("CÒN BÁN HÔM NAY", "#0a7", conBan, "ban")
			+ nhomHtml("HÔM NAY HẾT, NHẬN GIAO NGÀY MAI", "#c47f00", maiGiao, "mai")
			+ nhomHtml("HẾT HÀNG", "#999", het, "het");
	}

	function oBTP(ma, truong, nhan) {
		truong = truong || "so_btp"; nhan = nhan || "BTP sẵn";
		var b = BTP[ma] || {};
		var gt = b[truong] || 0;
		var id = ma + "|" + truong;
		if (DANG_SUA === id) {
			return '<div class="kb-o dang"><label>' + nhan + '</label><input id="kb-inp" type="number" min="0" inputmode="numeric" value="' + gt + '">' + nutOK() + '</div>';
		}
		if (!BTP_SUA) {
			return '<div class="kb-o"><label>' + nhan + '</label><b>' + gt + "</b></div>";
		}
		return '<div class="kb-o sua" data-id="' + id + '"><label>' + nhan + '</label><b>' + gt + "</b></div>";
	}

	function oGiaoMai(ma) {
		var b = BTP[ma];
		var gm = b ? (b.giao_mai || 0) : 0;
		return '<div class="kb-o kb-nh2 ' + (gm > 0 ? "duong" : (gm < 0 ? "am" : "")) + '"><label>CÒN NHẬN MAI</label><b>' + gm + "</b></div>";
	}

	function oNhan2(ma) {
		var b = BTP[ma];
		var cn = b ? b.con_nhan : 0;
		return '<div class="kb-o kb-nh2 ' + (cn > 0 ? "duong" : (cn < 0 ? "am" : "")) + '"><label>CÒN NHẬN 3 NGÀY</label><b>' + cn + "</b></div>";
	}

	function loiMayChu(t) {
		try {
			var j = JSON.parse(t);
			var sm = j._server_messages ? JSON.parse(j._server_messages) : [];
			if (sm.length) { var m = JSON.parse(sm[0]); if (m && m.message) return String(m.message).replace(/<[^>]+>/g, ""); }
			if (j.exception) { var p = String(j.exception).split(": "); return p.length > 1 ? p.slice(1).join(": ") : String(j.exception); }
		} catch (e) { }
		return "Máy chủ không nhận số, anh chị chụp màn hình báo giúp em";
	}

	function luuBTP(ma, gt, truong) {
		truong = truong || "so_btp";
		var h = { "Content-Type": "application/json", "Accept": "application/json" };
		var tk = window.csrf_token || (window.frappe && frappe.csrf_token);
		if (tk && tk !== "None") h["X-Frappe-CSRF-Token"] = tk;
		fetch("/api/method/vagabond.btp." + (truong === "so_decor" ? "luu_decor" : "luu_btp"), { method: "POST", headers: h, credentials: "same-origin",
			body: JSON.stringify(truong === "so_decor" ? { ma_hang: ma, so_decor: gt } : { ma_hang: ma, so_btp: gt }) })
			.then(function (r) { if (!r.ok) { return r.text().then(function (t) { throw new Error(loiMayChu(t)); }); } return r.json(); })
			.then(function () { taiBTP(); })
			.catch(function (e) { bao(e.message, true); taiBTP(); });
	}

	function taiBTP() {
		var h = { "Content-Type": "application/json", "Accept": "application/json" };
		var tk = window.csrf_token || (window.frappe && frappe.csrf_token);
		if (tk && tk !== "None") h["X-Frappe-CSRF-Token"] = tk;
		fetch("/api/method/vagabond.btp.bang_btp", { method: "POST", headers: h, credentials: "same-origin", body: "{}" })
			.then(function (r) { return r.json(); })
			.then(function (j) {
				var m = j.message; if (!m) return;
				var moi = {};
				(m.dong || []).forEach(function (x) { moi[x.ma_hang] = x; });
				BTP = moi;
				var el = document.getElementById("kb-btp-luc");
				if (el) el.textContent = m.cap_nhat_luc
					? "BTP bếp cập nhật " + m.cap_nhat_luc.slice(8, 10) + "/" + m.cap_nhat_luc.slice(5, 7) + " " + m.cap_nhat_luc.slice(11, 16)
					: "BTP chưa có số";
				ve();
			}).catch(function () {});
	}

	function taiQuyenBTP() {
		var h = { "Content-Type": "application/json", "Accept": "application/json" };
		var tk = window.csrf_token || (window.frappe && frappe.csrf_token);
		if (tk && tk !== "None") h["X-Frappe-CSRF-Token"] = tk;
		fetch("/api/method/vagabond.btp.quyen_btp", { method: "POST", headers: h, credentials: "same-origin", body: "{}" })
			.then(function (r) { return r.json(); })
			.then(function (j) { BTP_SUA = !!(j.message && j.message.sua); ve(); })
			.catch(function () {});
	}

	function boot() {
		NGAY_CHON = homNay();
		ganSuKien();
		veChips();
		API("dong_bo", { ngay: NGAY_CHON }).then(nhan).catch(function () {}).then(function () { taiLai(); });
		/* 10 giay doc bang, 30 giay ep keo Pancake cho NGAY DANG XEM.
		   May chu tu chan neu vua dong bo trong 12 giay - nhieu may cung mo
		   khong doi Pancake. Nut "Dong bo" chi la du phong. */
		taiQuyenBTP();
		taiBTP();
		/* Chi tai lai khi khong ai dang go. Truoc day vong nay chay vo dieu kien,
		   ve lai luoi va xoa mat o input bep dang go do - mat so vua nhap. */
		setInterval(function () { if (DANG_SUA === null) taiBTP(); }, 30000);
		setInterval(function () { if (DANG_SUA === null) taiLai(); }, 10000);
		setInterval(function () {
			if (DANG_SUA !== null) return;
			API("dong_bo", { ngay: NGAY_CHON }).then(nhan).catch(function () {});
		}, 30000);
	}
	if (document.readyState === "complete") boot();
	else window.addEventListener("load", boot);
})();
