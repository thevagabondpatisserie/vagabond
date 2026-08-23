/* BTP banh o - bep nhap so BTP cho finish, sales xem CON NHAN.
   Chay trong truong `javascript` cua Web Page /btp. Boot trong window load. */
(function () {
	var DL = null, DANG_SUA = null, VE_TRUOC = null;

	function API(m, b) {
		var h = { "Content-Type": "application/json", "Accept": "application/json" };
		var tk = window.csrf_token || (window.frappe && frappe.csrf_token);
		if (tk && tk !== "None") h["X-Frappe-CSRF-Token"] = tk;
		return fetch("/api/method/vagabond.btp." + m, {
			method: "POST", headers: h, credentials: "same-origin",
			body: JSON.stringify(b || {})
		}).then(function (r) {
			if (r.status === 403 || r.status === 401) {
				location.href = "/login?redirect-to=/btp"; throw new Error("login");
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
		var el = document.getElementById("bt-bao");
		el.textContent = t; el.className = xau ? "loi" : "";
		if (t) setTimeout(function () { if (el.textContent === t) el.textContent = ""; }, 4000);
	}

	function chuSach(t) {
		return String(t || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
	}

	function ve() {
		var g = document.getElementById("bt-luoi");
		var khoa = JSON.stringify([DL && DL.dong, DANG_SUA]);
		if (khoa === VE_TRUOC && g.childElementCount) return;
		VE_TRUOC = khoa;
		if (!DL || !DL.dong.length) {
			g.innerHTML = '<div class="bt-trong">Chưa có mã nào.<br>Bấm "Đổ mã từ bảng kiểm" để lấy sẵn danh sách bánh đang bán, hoặc "Thêm mã" từng cái.</div>';
			return;
		}
		var h = "";
		DL.dong.slice().sort(function (a, b) { return a.ma_hang < b.ma_hang ? -1 : 1; })
			.forEach(function (d) {
				var oBtp = DANG_SUA === d.ma_hang
					? '<div class="bt-o dang"><label>BTP sẵn</label><input id="bt-inp" type="number" min="0" value="' + (d.so_btp || 0) + '"></div>'
					: '<div class="bt-o sua" data-id="' + d.ma_hang + '"><label>BTP sẵn</label><b>' + (d.so_btp || 0) + "</b></div>";
				h += '<div class="bt-the"><div class="bt-ten">'
					+ (d.hinh ? '<img src="' + d.hinh + '" loading="lazy" alt="">' : '<i class="bt-noimg"></i>')
					+ "<b>" + d.ma_hang + "</b><span>" + chuSach(d.ten_banh) + "</span></div>"
					+ '<div class="bt-so">' + oBtp
					+ '<div class="bt-o"><label>Đơn đang giữ</label><b>' + (d.dang_giu || 0) + "</b></div>"
					+ '<div class="bt-o bt-nhan ' + (d.con_nhan > 0 ? "duong" : (d.con_nhan < 0 ? "am" : "")) + '"><label>CÒN NHẬN</label><b>' + d.con_nhan + "</b></div>"
					+ "</div></div>";
			});
		g.innerHTML = h;
	}

	function nhan(m) {
		if (!m) return;
		DL = m;
		document.getElementById("bt-luc").textContent =
			m.cap_nhat_luc ? "Bếp cập nhật " + m.cap_nhat_luc.slice(8, 10) + "/" + m.cap_nhat_luc.slice(5, 7) + " lúc " + m.cap_nhat_luc.slice(11, 16) : "Chưa có số";
		ve();
	}

	function taiLai() { return API("bang_btp", {}).then(nhan).catch(function (e) { bao(e.message, true); }); }

	function luuO() {
		var inp = document.getElementById("bt-inp");
		if (!inp || DANG_SUA === null) return;
		var ma = DANG_SUA, gt = parseInt(inp.value || "0", 10);
		DANG_SUA = null;
		API("luu_btp", { ma_hang: ma, so_btp: gt })
			.then(nhan)
			.catch(function (e) { bao(e.message, true); taiLai(); });
	}

	/* ---- Bang chon mon cho nut "Them ma" (anh Viet 03/08/2026) ----
	   Truoc day nut nay bat go tay vao window.prompt: bep go nham ma hoai,
	   go nham thi server chan nhung van mat cong. Gio mo bang tim co ten, ma
	   va anh - giong bang chon mon ben /kiem-banh. Nguon tim la
	   vagabond.kiem_banh.tim_mon nen goi thang, khong qua API() cua /btp. */

	function btEsc(s) {
		return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
			.replace(/>/g, "&gt;").replace(/"/g, "&quot;");
	}

	function btTimMon(q) {
		var h = { "Content-Type": "application/json", "Accept": "application/json" };
		var tk = window.csrf_token || (window.frappe && frappe.csrf_token);
		if (tk && tk !== "None") h["X-Frappe-" + "CSRF-" + "Token"] = tk;
		return fetch("/api/method/vagabond.kiem_banh.tim_mon", {
			method: "POST", headers: h, credentials: "same-origin",
			body: JSON.stringify({ tu_khoa: q || "" })
		}).then(function (r) {
			return r.json().then(function (j) {
				if (!r.ok) throw new Error(j.exception || "Lỗi tìm mã");
				return j.message || [];
			});
		});
	}

	function btAnh(url) {
		if (url) {
			return '<img src="' + btEsc(url) + '" loading="lazy" style="width:46px;height:46px;'
				+ 'border-radius:8px;object-fit:cover;flex:0 0 46px;background:#f3f3f3">';
		}
		return '<div style="width:46px;height:46px;border-radius:8px;background:#f3f3f3;display:flex;'
			+ 'align-items:center;justify-content:center;flex:0 0 46px;font-size:22px">🎂</div>';
	}

	function btLop(tieuDe) {
		var ov = document.createElement("div");
		ov.style.cssText = "position:fixed;left:0;top:0;right:0;bottom:0;background:rgba(0,0,0,.45);"
			+ "z-index:9999;display:flex;align-items:flex-end;justify-content:center";
		var box = document.createElement("div");
		box.style.cssText = "background:#fff;width:100%;max-width:560px;max-height:88vh;"
			+ "border-radius:16px 16px 0 0;display:flex;flex-direction:column;overflow:hidden";
		box.innerHTML = '<div style="padding:13px 16px;border-bottom:1px solid #eee;display:flex;'
			+ 'align-items:center;justify-content:space-between;gap:10px">'
			+ '<b style="font-size:16px">' + btEsc(tieuDe) + '</b>'
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

	function btChonMon() {
		var daCo = {};
		((DL && DL.dong) || []).forEach(function (d) { daCo[d.ma_hang] = 1; });
		var ov = btLop("Thêm mã vào bảng BTP");
		var oTim = document.createElement("div");
		oTim.style.cssText = "padding:10px 16px 6px";
		oTim.innerHTML = '<input id="bt-ptim" placeholder="Gõ tên hoặc mã bánh" autocomplete="off" '
			+ 'style="width:100%;height:46px;padding:0 12px;border:1px solid #ddd;border-radius:10px;'
			+ 'font-size:16px;box-sizing:border-box">';
		var ds = document.createElement("div");
		ds.style.cssText = "flex:1;overflow:auto;padding:2px 8px 18px;min-height:240px";
		ov.hop.appendChild(oTim);
		ov.hop.appendChild(ds);

		var tmr = null, phienChay = 0;
		function nhanTrong(t) {
			ds.innerHTML = '<div style="padding:26px 10px;text-align:center;color:#999">' + btEsc(t) + '</div>';
		}
		function veDs(rs) {
			if (!rs.length) { nhanTrong("Không thấy mã nào khớp"); return; }
			ds.innerHTML = rs.map(function (r) {
				var co = daCo[r.ma] ? 1 : 0;
				return '<div data-ma="' + btEsc(r.ma) + '" data-co="' + co + '" '
					+ 'style="display:flex;align-items:center;gap:10px;padding:9px 8px;'
					+ 'border-bottom:1px solid #f2f2f2;cursor:pointer' + (co ? ';opacity:.45' : '') + '">'
					+ btAnh(r.anh)
					+ '<div style="flex:1;min-width:0">'
					+ '<div style="font-weight:600;font-size:15px">' + btEsc(r.ten || r.ma) + '</div>'
					+ '<div style="font-size:12.5px;color:#888">' + btEsc(r.ma)
					+ (co ? " · đã có trong bảng" : "") + '</div></div></div>';
			}).join("");
		}
		function chay(q) {
			phienChay++;
			var phien = phienChay;
			nhanTrong("Đang tìm...");
			btTimMon(q)
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
			API("them_ma_btp", { ma_hang: ma })
				.then(function (m) { nhan(m); bao("Đã thêm " + ma); })
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


	function boot() {
		document.getElementById("bt-luoi").addEventListener("click", function (ev) {
			var o = ev.target.closest(".bt-o.sua");
			if (!o) return;
			DANG_SUA = o.getAttribute("data-id");
			ve();
			var inp = document.getElementById("bt-inp");
			if (inp) {
				inp.focus(); inp.select();
				inp.addEventListener("keydown", function (e) { if (e.key === "Enter") inp.blur(); });
				inp.addEventListener("blur", luuO);
			}
		});
				document.getElementById("bt-them").onclick = btChonMon;
		document.getElementById("bt-gieo").onclick = function () {
			bao("Đang đổ mã từ bảng kiểm...");
			API("gieo_tu_kiem_banh", {})
				.then(function (m) { return taiLai().then(function () { bao("Đã thêm " + m.them + " mã"); }); })
				.catch(function (e) { bao(e.message, true); });
		};
		taiLai();
		setInterval(function () { if (DANG_SUA === null) taiLai(); }, 15000);
	}
	if (document.readyState === "complete") boot();
	else window.addEventListener("load", boot);
})();
