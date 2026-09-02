/* Kiem banh ngay v3 - them Cho chot + ten khach (y Loan Anh 01/08); truoc do v2 - them tab cac ngay ke tiep (01/08: anh Viet yeu cau,
   de bep gom san xuat truoc; banh HSD 3 ngay, lam truoc ra dong roi do glaze).
   Chay trong truong `javascript` cua Web Page /kiem-banh.
   Boot trong window load - bai hoc CSRF tu app /bep. */
(function () {
	var DL = null, DANG_SUA = null, VE_TRUOC = null, NGAY_CHON = null;
	var NGHI_DEN = 0;   // moc thoi gian duoc phep goi dong bo lai
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

	/* Luoi chan cuoi cung: khong bao gio de mot khoa API di ra man hinh.
	   May chu da giau roi (vagabond/lib.giau_khoa), day la lop thu hai,
	   phong khi loi den tu mot duong khac chua qua cho do.
	   Ngay 26/08/2026 Sales chup duoc mot man hinh co ca khoa Pancake. */
	function sach(t) {
		return String(t == null ? "" : t)
			.replace(/(api_key|access_token|token|key)=[^&\s"']+/gi, "$1=***");
	}

	/* Loi cua thu vien mang dai loang ngoang va khong noi ai phai lam gi.
	   Bat lay may dang hay gap, doi thanh mot cau nguoi doc hieu duoc. */
	function loiNguoiDoc(t) {
		var x = sach(t);
		if (/403|Forbidden/i.test(x)) {
			return "Pancake đang từ chối lượt gọi. Thường do nhiều máy cùng mở màn "
				+ "kiểm bánh, đợi vài phút là hết. Số dưới đây là của lần đồng bộ trước.";
		}
		if (/401|Unauthorized/i.test(x)) return "Pancake không nhận khoá API. Báo anh Việt dán lại khoá.";
		if (/50\d|Server Error/i.test(x)) return "Máy chủ Pancake đang trục trặc. Lát nữa thử lại.";
		if (/Timeout|timed out|Connection/i.test(x)) return "Không nối được Pancake. Kiểm tra mạng rồi thử lại.";
		return x.length > 160 ? "Chưa kéo được đơn từ Pancake. Lát nữa thử lại." : x;
	}

	function bao(t, xau) {
		var el = document.getElementById("kb-bao");
		el.textContent = sach(t); el.className = xau ? "loi" : "";
		if (t) setTimeout(function () { if (el.textContent === sach(t)) el.textContent = ""; }, 4000);
	}

	/* Dong canh bao NAM LAI tren man, khong tu tat sau bon giay nhu bao().
	   So dang bay la so cu thi phai noi ro chung nao no con cu, chu khong
	   nhap nhay mot cai roi bien mat. */
	function baoDai(t) {
		var el = document.getElementById("kb-canh");
		if (!el) return;
		if (!t) { el.textContent = ""; el.style.display = "none"; return; }
		el.textContent = sach(t);
		el.style.display = "";
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
		/* May chu bao chua keo duoc don: bay canh bao va NGHI dung bang do,
		   khong dap cua Pancake ba muoi giay mot lan vao cai cua dang dong. */
		if (m.loi) {
			baoDai("⚠ " + m.loi);
			NGHI_DEN = Date.now() + Math.max(Number(m.cho_giay) || 0, 60) * 1000;
		} else {
			baoDai("");
			NGHI_DEN = 0;
		}
		document.getElementById("kb-luc").textContent =
			m.dong_bo_luc ? "Đồng bộ Pancake lúc " + m.dong_bo_luc.slice(11, 16) : "Chưa đồng bộ";
		var chot = m.tinh_trang === "Da chot";
		if (chot) document.getElementById("kb-chot").style.display = "none";
		document.getElementById("kb-dachot").style.display = chot ? "" : "none";
		ve();
	}

	function taiLai() {
		return API("bang", { ngay: NGAY_CHON }).then(nhan)
			.catch(function (e) { bao(loiNguoiDoc(e.message), true); });
	}

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
					+ '<b>' + d.ma_hang + '</b><span>' + (d.ten_banh || "") + "</span>" + nutWeb(d) + nutXoa(d) + "</div>"
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
		ganWeb(g);
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

	/* Cong tac tam ngung ban mot ma tren web dat banh.

	   Anh Viet 27/08/2026: *"co vai truong hop bat kha khang, con ton nhung
	   phai tat, khong ban duoc hom do"*.

	   Nut noi ro NGAY BAN LAI chu khong chi noi "dang tat". Ban truoc luu mot
	   o co / khong thi tat xong tat mai: hom sau bep lam duoc, so ton len, ma
	   web van khong hien, va khong ai nho ra la hom kia co nguoi bam tat.
	   Ban nay tat den het ngay dang xem, sang hom sau tu ban lai. */
	function nutWeb(d) {
		var tat = !!d.tat_web;
		var den = d.tat_web_den || "";
		var nhan = tat ? "Tắt bán web" : "Đang bán web";
		var tip = tat
			? ("Không hiện trên web đặt bánh đến hết " + (den ? fmtVN(den) : "hôm nay")
				+ ". Bấm để cho bán lại ngay.")
			: "Đang hiện trên web đặt bánh theo số bán được. Bấm để tạm ngừng bán hết ngày "
				+ fmtVN(NGAY_CHON) + ".";
		return '<button type="button" class="kb-web' + (tat ? " tat" : "") + '"'
			+ ' data-web="' + d.ma_hang + '" data-tat="' + (tat ? 1 : 0) + '"'
			+ ' title="' + tip.replace(/"/g, "&quot;") + '">'
			+ (tat ? "&#9679; " : "&#9675; ") + nhan + "</button>";
	}

	function ganWeb(g) {
		if (g.__daGanWeb) return;
		g.__daGanWeb = 1;
		g.addEventListener("click", function (e) {
			var n = e.target && e.target.closest ? e.target.closest("[data-web]") : null;
			if (!n) return;
			e.preventDefault();
			e.stopPropagation();
			var ma = n.getAttribute("data-web");
			var dangTat = n.getAttribute("data-tat") === "1";
			/* Tat la mot quyet dinh co hau qua tien bac: khach dang xem web se
			   khong dat duoc ma do nua. Hoi mot cau, va noi ro bao gio ban lai. */
			if (!dangTat && !window.confirm(
				"Tạm ngừng bán " + ma + " trên web đến hết ngày " + fmtVN(NGAY_CHON)
				+ "?\n\nKho vẫn giữ nguyên số tồn, chỉ web không hiện mã này. "
				+ "Sang ngày hôm sau tự bán lại.")) return;
			n.disabled = true;
			API("tat_ban_web_dat", { ma_hang: ma, tat: dangTat ? 0 : 1, den_ngay: NGAY_CHON })
				.then(function (r) {
					VE_TRUOC = null;
					taiLai();
					bao(r && r.tat
						? ("Đã tạm ngừng bán " + ma + " trên web đến hết " + fmtVN(r.den_ngay))
						: ("Đã cho bán lại " + ma + " trên web"));
				})
				.catch(function (e2) { n.disabled = false; bao(loiNguoiDoc(e2.message), true); });
		});
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
			.catch(function (e) { bao(loiNguoiDoc(e.message), true); taiLai(); });
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
			/* Bam tay thi BO ky nghi: nguoi dung dang dung truoc man hinh va
			   co chu dinh, khac han vong tu dong chay ngam. */
			NGHI_DEN = 0;
			API("dong_bo", { ngay: NGAY_CHON })
				.then(function (m) { nhan(m); if (!m || !m.loi) bao("Đã đồng bộ xong"); })
				.catch(function (e) { baoDai("⚠ " + loiNguoiDoc(e.message)); });
		};
		document.getElementById("kb-them").onclick = kbChonMon;
		var nTuVan = document.getElementById("kb-tuvan");
		if (nTuVan) nTuVan.onclick = kbTuVan;
		document.getElementById("kb-chot").onclick = function () {
			if (!window.confirm("Chốt sổ hôm nay? Số còn lại sẽ chuyển thành tồn đầu ngày mai và bảng hôm nay bị khoá.")) return;
			bao("Đang chốt ngày...");
			API("chot_ngay", { ngay: NGAY_CHON }).then(function () { taiLai(); bao("Đã chốt. Tồn đã chuyển sang ngày mai."); })
				.catch(function (e) { bao(loiNguoiDoc(e.message), true); });
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
				.catch(function (e) { bao(loiNguoiDoc(e.message), true); });
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
			.catch(function (e) { bao(loiNguoiDoc(e.message), true); taiBTP(); });
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
		/* NANG TU 30 LEN 120 GIAY (26/08/2026).

		   Moi lan dong bo la HAI luot keo don, moi luot den muoi trang. Ba
		   may sales mo cung luc, ba muoi giay mot lan, ca ngay - Pancake tra
		   403 la phai, va do dung la loi Sales bao hom nay. Hai phut van tuoi
		   chan chan cho mot bang kiem banh, va bang van tu tai lai moi muoi
		   giay tu co so du lieu nen so bep vua go van len ngay.

		   Them ky nghi: may chu vua bao bi tu choi thi khong goi nua cho het
		   nghi, khong dap cua deu tay vao cai cua dang dong. */
		setInterval(function () {
			if (DANG_SUA !== null) return;
			if (NGHI_DEN && Date.now() < NGHI_DEN) return;
			API("dong_bo", { ngay: NGAY_CHON }).then(nhan).catch(function () {});
		}, 120000);
	}
	if (document.readyState === "complete") boot();
	else window.addEventListener("load", boot);
})();

/* ------------------------------------------------------------------
   Kiem kho theo diem ban - hai tab moi "Kiem banh 9 TCV" va "Kiem banh
   NVHTN" (anh Viet 02/09/2026). Tab tu sinh tu danh sach diem ban co
   quay, nen mo them chi nhanh la co them tab, khong phai sua ma nguon.

   Vi sao la mot khoi rieng chu khong xen vao khoi tren: bang tren dem
   banh cua BEP theo ngay giao, nguon so la don Pancake; bang nay dem
   banh trong TU cua MOT QUAY, nguon so la hoa don ban ra. Hai phep dem
   khac nhau, tron chung mot khoi la som muon cung lay nham so.
   ------------------------------------------------------------------ */
(function () {
	var DIEM = [], DIEM_CHON = "", NGAY = null, DL = null, DANG_SUA = null;
	var SO_NGAY = 3;   // hom nay va hai ngay truoc, de doi chieu nguoc
	var HEN_TIM = null, NHIP = null;

	function ngayISO(d) {
		return d.getFullYear() + "-" + ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
	}
	function fmtNgan(iso) { return iso.slice(8, 10) + "/" + iso.slice(5, 7); }
	function h(t) {
		return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) {
			return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
		});
	}

	function API(m, b) {
		var hd = { "Content-Type": "application/json", "Accept": "application/json" };
		var tk = window.csrf_token || (window.frappe && frappe.csrf_token);
		if (tk && tk !== "None") hd["X-Frappe-CSRF-Token"] = tk;
		return fetch("/api/method/vagabond.kiem_kho." + m, {
			method: "POST", headers: hd, credentials: "same-origin",
			body: JSON.stringify(b || {})
		}).then(function (r) {
			if (r.status === 403 || r.status === 401) {
				location.href = "/login?redirect-to=/kiem-banh"; throw new Error("login");
			}
			return r.json().then(function (j) {
				if (!r.ok) {
					var loi = j.exception || "Lỗi hệ thống";
					try { loi = JSON.parse(JSON.parse(j._server_messages)[0]).message; } catch (e) {}
					throw new Error(loi);
				}
				return j.message;
			});
		});
	}

	/* Luoi chan khoa API cua rieng khoi nay. Khoi tren co mot cai giong
	   het, va co y giong het: hai khoi la hai pham vi ham khac nhau, dung
	   chung mot ham la phai keo ca hai ra ngoai IIFE - luc do bat ky ma
	   nao tren trang cung goi duoc. Ngay 26/08/2026 Sales chup duoc mot
	   man hinh co ca khoa Pancake, nen cho nay khong duoc thoang. */
	function sachKK(t) {
		return String(t == null ? "" : t)
			.replace(/(api_key|access_token|token|key)=[^&\s"']+/gi, "$1=***");
	}

	function loiKK(e) {
		var x = sachKK(e && e.message);
		if (/403|Forbidden/i.test(x)) return "Anh chị không có quyền làm việc này.";
		if (/50\d|Server Error/i.test(x)) return "Máy chủ đang trục trặc. Lát nữa thử lại.";
		if (/Timeout|timed out|Connection|Failed to fetch/i.test(x)) return "Không nối được máy chủ. Kiểm tra mạng rồi thử lại.";
		return x.length > 160 ? "Chưa lưu được. Lát nữa thử lại." : x;
	}

	function bao(t, xau) {
		var el = document.getElementById("kk-bao");
		if (!el) return;
		el.textContent = sachKK(t); el.className = xau ? "loi" : "";
		if (t) setTimeout(function () { if (el.textContent === sachKK(t)) el.textContent = ""; }, 4000);
	}

	/* ---------------------------------------------------------- tab */

	function veTabs() {
		var g = document.getElementById("kb-tabs");
		if (!g) return;
		var x = '<button class="kb-tab' + (DIEM_CHON ? "" : " on") + '" data-diem="">Kiểm bánh ngày</button>';
		DIEM.forEach(function (d) {
			x += '<button class="kb-tab' + (DIEM_CHON === d.ma ? " on" : "") + '" data-diem="'
				+ h(d.ma) + '">Kiểm bánh ' + h(d.ten) + "</button>";
		});
		g.innerHTML = x;
	}

	function chonTab(ma) {
		DIEM_CHON = ma || "";
		veTabs();
		var goc = document.getElementById("kb-goc"), kk = document.getElementById("kk");
		if (!goc || !kk) return;
		goc.style.display = DIEM_CHON ? "none" : "";
		kk.style.display = DIEM_CHON ? "" : "none";
		try { sessionStorage.setItem("kk_tab", DIEM_CHON); } catch (e) {}
		if (DIEM_CHON) {
			var d = DIEM.filter(function (x) { return x.ma === DIEM_CHON; })[0];
			document.getElementById("kk-diem-to").textContent = d ? d.ten : DIEM_CHON;
			an_them();
			if (!NGAY) NGAY = ngayISO(new Date());
			veChips(); tai();
		}
	}

	function veChips() {
		var g = document.getElementById("kk-chips");
		var t = new Date(); t.setHours(0, 0, 0, 0);
		var x = "";
		for (var i = 0; i < SO_NGAY; i++) {
			var d = new Date(t); d.setDate(t.getDate() - i);
			var iso = ngayISO(d);
			x += '<button class="kb-chip' + (iso === NGAY ? " on" : "") + '" data-ngay="' + iso + '">'
				+ (i === 0 ? "Hôm nay " : "") + fmtNgan(iso) + "</button>";
		}
		g.innerHTML = x;
	}

	/* --------------------------------------------------------- bang */

	function tai() {
		if (!DIEM_CHON) return Promise.resolve();
		return API("bang", { diem: DIEM_CHON, ngay: NGAY }).then(function (m) {
			DL = m; ve();
		}).catch(function (e) { bao(loiKK(e), true); });
	}

	function o(d, truong, nhan, gt, sua, lop) {
		var dang = DANG_SUA && DANG_SUA.ma === d.ma_hang && DANG_SUA.truong === truong;
		var c = "kb-o" + (lop ? " " + lop : "") + (sua ? " sua" : "") + (dang ? " dang" : "");
		var trong = '<b>' + (gt === "" ? "·" : h(gt)) + "</b>";
		if (dang) trong = '<input id="kk-inp" type="number" inputmode="numeric" value="' + h(gt) + '">';
		return '<div class="' + c + '" data-ma="' + h(d.ma_hang) + '" data-truong="' + truong + '">'
			+ "<label>" + h(nhan) + "</label>" + trong + "</div>";
	}

	function ve() {
		var g = document.getElementById("kk-luoi");
		if (!DL) { g.innerHTML = ""; return; }
		document.getElementById("kk-phu").textContent =
			DL.tinh_trang === "Da chot" ? "Ngày này đã chốt sổ" : "Đang bán";
		document.getElementById("kk-dachot").style.display = DL.sua_duoc ? "none" : "";
		document.getElementById("kk-them").style.display = DL.sua_duoc ? "" : "none";
		document.getElementById("kk-chot").style.display = DL.sua_duoc ? "" : "none";
		if (!DL.dong.length) {
			g.innerHTML = '<div class="kb-trong">Bảng của ngày này chưa có dòng nào.<br>'
				+ 'Bấm "Thêm mã" để đưa món vào bảng, hoặc cứ bán bình thường - '
				+ 'máy tự thêm dòng cho bánh ngay khi có hoá đơn đầu tiên.</div>';
			return;
		}
		var sua = !!DL.sua_duoc, x = "";
		DL.dong.forEach(function (d) {
			x += '<div class="kb-the"><div class="kb-ten">'
				+ "<b>" + h(d.ma_hang) + "</b><span>" + h(d.ten_banh) + "</span>"
				/* Dong may tu them vi thay co ban ra ma chua ai khai ton. Man
				   tinh tien chua ve chip con/het cho mon nay, va nguoi doc bang
				   can biet ngay vi sao. */
				+ (d.theo_doi ? "" : '<span class="kk-chuakhai">chưa khai tồn</span>')
				+ (sua && !d.ton_dau && !d.tong_nhap && !d.da_ban && !d.hong && !d.dieu_chinh
					? '<button class="kb-web" data-xoa="' + h(d.ma_hang) + '">Xoá dòng</button>' : "")
				+ '</div><div class="kk-so">';
			x += o(d, "ton_dau", "Tồn đầu", d.ton_dau, sua);
			for (var i = 0; i < d.nhap.length; i++) {
				x += o(d, "nhap_" + (i + 1), "Đợt " + (i + 1), d.nhap[i], sua);
			}
			x += o(d, "da_ban", "Đã bán", d.da_ban, false);
			x += o(d, "hong", "Hỏng", d.hong, sua);
			x += o(d, "dieu_chinh", "Đ/chỉnh", d.dieu_chinh, sua);
			x += o(d, "co_the_ban", "CÒN", d.co_the_ban, false, "con" + (d.co_the_ban < 0 ? " am" : ""));
			x += o(d, "kiem_tay", "Kiểm tay", d.da_kiem ? d.kiem_tay : "", sua, d.da_kiem ? "" : "chuakiem");
			x += o(d, "lech", "Lệch", d.da_kiem ? d.lech : "", false, "lech" + (d.da_kiem && d.lech ? " co" : ""));
			x += "</div></div>";
		});
		g.innerHTML = x;
		ganInput();
	}

	function ganInput() {
		var inp = document.getElementById("kk-inp");
		if (!inp) return;
		inp.focus(); inp.select();
		var hen = null;
		var hoan = function () { if (hen) { clearTimeout(hen); hen = null; } };
		inp.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); hoan(); luu(); } });
		inp.addEventListener("input", function () { hoan(); hen = setTimeout(function () { hen = null; luu(); }, 3000); });
		inp.addEventListener("change", function () { hoan(); luu(); });
		inp.addEventListener("blur", function () { hoan(); luu(); });
	}

	function luu() {
		if (!DANG_SUA) return;
		var inp = document.getElementById("kk-inp");
		var gt = inp ? inp.value : "";
		var s = DANG_SUA; DANG_SUA = null;
		API("luu_o", { diem: DIEM_CHON, ngay: NGAY, ma_hang: s.ma, truong: s.truong, gia_tri: gt })
			.then(function () { return tai(); })
			.catch(function (e) { bao(loiKK(e), true); tai(); });
	}

	/* ------------------------------------------------------- them ma */

	function an_them() {
		var hop = document.getElementById("kk-them-hop");
		if (hop) { hop.style.display = "none"; document.getElementById("kk-goiy").innerHTML = ""; }
	}

	function goiY() {
		var tu = document.getElementById("kk-tim").value;
		var g = document.getElementById("kk-goiy");
		if (String(tu || "").trim().length < 2) { g.innerHTML = ""; return; }
		API("tim_mon", { diem: DIEM_CHON, ngay: NGAY, tu_khoa: tu }).then(function (ds) {
			if (!ds || !ds.length) { g.innerHTML = '<div class="kb-phu">Không tìm thấy mã nào.</div>'; return; }
			g.innerHTML = ds.map(function (d) {
				return '<button data-them="' + h(d.ma_hang) + '"><b>' + h(d.ma_hang) + "</b> · "
					+ h(d.ten_banh) + "</button>";
			}).join("");
		}).catch(function (e) { bao(loiKK(e), true); });
	}

	/* ------------------------------------------------------ su kien */

	function ganSuKien() {
		document.getElementById("kb-tabs").addEventListener("click", function (ev) {
			var n = ev.target.closest("button[data-diem]");
			if (n) chonTab(n.getAttribute("data-diem"));
		});
		document.getElementById("kk-chips").addEventListener("click", function (ev) {
			var n = ev.target.closest("button[data-ngay]");
			if (!n) return;
			NGAY = n.getAttribute("data-ngay"); DANG_SUA = null; veChips(); tai();
		});
		document.getElementById("kk-luoi").addEventListener("click", function (ev) {
			var xo = ev.target.closest("button[data-xoa]");
			if (xo) {
				var ma = xo.getAttribute("data-xoa");
				API("xoa_dong", { diem: DIEM_CHON, ngay: NGAY, ma_hang: ma })
					.then(function () { bao("Đã xoá " + ma); return tai(); })
					.catch(function (e) { bao(loiKK(e), true); });
				return;
			}
			var n = ev.target.closest(".kb-o.sua");
			if (!n || !DL || !DL.sua_duoc) return;
			DANG_SUA = { ma: n.getAttribute("data-ma"), truong: n.getAttribute("data-truong") };
			ve();
		});
		document.getElementById("kk-them").onclick = function () {
			var hop = document.getElementById("kk-them-hop");
			var mo = hop.style.display === "none";
			hop.style.display = mo ? "" : "none";
			if (mo) { document.getElementById("kk-tim").value = ""; document.getElementById("kk-goiy").innerHTML = ""; document.getElementById("kk-tim").focus(); }
		};
		document.getElementById("kk-tim").addEventListener("input", function () {
			if (HEN_TIM) clearTimeout(HEN_TIM);
			HEN_TIM = setTimeout(goiY, 300);
		});
		document.getElementById("kk-goiy").addEventListener("click", function (ev) {
			var n = ev.target.closest("button[data-them]");
			if (!n) return;
			API("them_dong", { diem: DIEM_CHON, ngay: NGAY, ma_hang: n.getAttribute("data-them") })
				.then(function () { an_them(); bao("Đã thêm vào bảng"); return tai(); })
				.catch(function (e) { bao(loiKK(e), true); });
		});
		document.getElementById("kk-chot").onclick = function () {
			if (!confirm("Chốt sổ ngày này? Số còn lại sẽ chuyển thành tồn đầu ngày mai.")) return;
			API("chot", { diem: DIEM_CHON, ngay: NGAY })
				.then(function () { bao("Đã chốt. Tồn đã chuyển sang ngày mai."); return tai(); })
				.catch(function (e) { bao(loiKK(e), true); });
		};
	}

	function boot() {
		if (!document.getElementById("kb-tabs")) return;
		API("diem_ds").then(function (ds) {
			DIEM = ds || [];
			if (!DIEM.length) { document.getElementById("kb-tabs").style.display = "none"; return; }
			ganSuKien();
			var cu = "";
			try { cu = sessionStorage.getItem("kk_tab") || ""; } catch (e) {}
			if (cu && !DIEM.filter(function (d) { return d.ma === cu; }).length) cu = "";
			chonTab(cu);
			if (NHIP) clearInterval(NHIP);
			NHIP = setInterval(function () {
				if (DIEM_CHON && !DANG_SUA && document.visibilityState === "visible") tai();
			}, 60000);
		}).catch(function () {
			var g = document.getElementById("kb-tabs");
			if (g) g.style.display = "none";
		});
	}

	if (document.readyState === "complete") boot();
	else window.addEventListener("load", boot);
})();
