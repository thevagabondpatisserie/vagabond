/* Minh hoạ thumbnail khoá học Sonneto: tranh vẽ mặt cắt kiểu bản vẽ bếp, nền graphite, chú thích số đo. Dùng tạm tới khi có ảnh chụp thật. */
window.THUMBS = (function () {
  var M = 'font-family="JetBrains Mono, monospace" font-size="10" letter-spacing="1.2" fill="#ebe8e1" fill-opacity=".62"';
  function frame(inner, id, tint) {
    return '<svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" role="img">' +
      '<defs><radialGradient id="bg' + id + '" cx="50%" cy="58%" r="70%"><stop offset="0" stop-color="' + tint + '"/><stop offset="1" stop-color="#0d0e0f"/></radialGradient>' +
      '<pattern id="gr' + id + '" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="4" fill="none"/><circle cx="1" cy="1" r=".45" fill="#ebe8e1" fill-opacity=".035"/></pattern></defs>' +
      '<rect width="400" height="300" fill="url(#bg' + id + ')"/><rect width="400" height="300" fill="url(#gr' + id + ')"/>' + inner + '</svg>';
  }

  /* 1. Croissant cắt đôi: vỏ nâu, ruột tổ ong theo vòng cung */
  function croissant() {
    var holes = '', rings = [[0.28, 7], [0.46, 9], [0.63, 11], [0.8, 13]];
    rings.forEach(function (r, ri) {
      for (var i = 0; i < r[1]; i++) {
        var a = Math.PI * (0.08 + 0.84 * (i + 0.5) / r[1]);
        var x = 200 - Math.cos(a) * 128 * r[0], y = 226 - Math.sin(a) * 92 * r[0];
        var w = 5 + ri * 2.2 + ((i * 7) % 3), h = 3 + ri * 1.3 + ((i * 5) % 2);
        holes += '<ellipse cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" rx="' + w + '" ry="' + h + '" transform="rotate(' + (Math.atan2(-Math.sin(a), -Math.cos(a)) * 180 / Math.PI + 90).toFixed(0) + ' ' + x.toFixed(1) + ' ' + y.toFixed(1) + ')" fill="#5b3a1a" fill-opacity=".55" stroke="#c99a55" stroke-width=".8"/>';
      }
    });
    var layers = '';
    for (var k = 1; k < 9; k++) layers += '<path d="M' + (200 - 128 * k / 9) + ' 226 A' + (128 * k / 9) + ' ' + (92 * k / 9) + ' 0 0 1 ' + (200 + 128 * k / 9) + ' 226" fill="none" stroke="#c99a55" stroke-opacity=".5" stroke-width=".7"/>';
    return frame(
      '<defs><linearGradient id="crust" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7a4518"/><stop offset=".6" stop-color="#b8732e"/><stop offset="1" stop-color="#d79a4f"/></linearGradient>' +
      '<radialGradient id="crumb" cx="50%" cy="100%" r="100%"><stop offset="0" stop-color="#f5e3b8"/><stop offset="1" stop-color="#e2bf7c"/></radialGradient></defs>' +
      '<ellipse cx="200" cy="234" rx="170" ry="10" fill="#000" fill-opacity=".45"/>' +
      '<rect x="20" y="228" width="360" height="6" fill="#2a2018"/>' +
      '<path d="M54 226 A146 108 0 0 1 346 226 Z" fill="url(#crust)"/>' +
      '<path d="M66 226 A134 98 0 0 1 334 226 Z" fill="url(#crumb)"/>' + layers + holes +
      '<path d="M54 226 A146 108 0 0 1 346 226" fill="none" stroke="#3b2210" stroke-width="2"/>' +
      '<line x1="292" y1="132" x2="330" y2="78" stroke="#ebe8e1" stroke-opacity=".4"/><line x1="330" y1="78" x2="380" y2="78" stroke="#ebe8e1" stroke-opacity=".4"/>' +
      '<text x="334" y="72" ' + M + '>27 LỚP</text>' +
      '<text x="24" y="40" ' + M + '>MẶT CẮT · CROISSANT</text>', 'c', '#3a2a1a');
  }

  /* 2. Lát entremets: đế, nhân, mousse, gương chảy */
  function entremets() {
    var x = 104, w = 192;
    var L = [[214, 22, '#7a4a24'], [184, 30, '#8e2a3a'], [118, 66, '#efe2cc'], [100, 18, '#2c1610']];
    var s = '<ellipse cx="200" cy="244" rx="150" ry="9" fill="#000" fill-opacity=".5"/><rect x="40" y="236" width="320" height="4" fill="#24201c"/>';
    L.forEach(function (l) { s += '<rect x="' + x + '" y="' + l[0] + '" width="' + w + '" height="' + l[1] + '" fill="' + l[2] + '"/>'; });
    /* chấm bánh quy trên đế */
    for (var i = 0; i < 26; i++) s += '<circle cx="' + (x + 6 + (i * 37) % (w - 12)) + '" cy="' + (220 + (i * 13) % 16) + '" r="1.3" fill="#c48a52"/>';
    /* bọt khí mousse */
    for (var j = 0; j < 18; j++) s += '<circle cx="' + (x + 10 + (j * 53) % (w - 20)) + '" cy="' + (126 + (j * 29) % 54) + '" r="' + (0.8 + (j % 3) * 0.5) + '" fill="#d8c8ac"/>';
    /* gương chảy */
    s += '<path d="M' + x + ' 100 h' + w + ' v14 q-8 0 -10 14 q-2 10 -6 0 q-4 -12 -22 -14 h-50 q-10 2 -12 22 q-3 12 -7 0 q-3 -20 -18 -22 h-30 q-8 0 -10 10 q-3 8 -6 0 q-3 -10 -21 -10 z" fill="#2c1610"/>';
    s += '<path d="M' + (x + 10) + ' 104 h70" stroke="#ebe8e1" stroke-opacity=".35" stroke-width="2" stroke-linecap="round"/>';
    s += '<rect x="' + x + '" y="100" width="' + w + '" height="136" fill="none" stroke="#000" stroke-opacity=".35"/>';
    var tags = [[104, 'GƯƠNG 32°C'], [150, 'MOUSSE'], [198, 'NHÂN'], [226, 'ĐẾ SABLÉ']];
    tags.forEach(function (t) { s += '<line x1="300" y1="' + t[0] + '" x2="318" y2="' + t[0] + '" stroke="#ebe8e1" stroke-opacity=".4"/><text x="322" y="' + (t[0] + 3) + '" ' + M + '>' + t[1] + '</text>'; });
    s += '<text x="24" y="40" ' + M + '>LÁT CẮT · ENTREMETS</text>';
    return frame(s, 'e', '#2c2226');
  }

  /* 3. Thẻ công thức có giá vốn */
  function giavon() {
    var rows = [['Bột T55', '1.000 g', '18.500'], ['Bơ lá 82%', '560 g', '134.400'], ['Đường', '120 g', '2.880'], ['Men tươi', '40 g', '2.400'], ['Trứng quét', '150 g', '6.750']];
    var s = '<g transform="rotate(-4 200 160)"><rect x="96" y="58" width="214" height="196" fill="#000" fill-opacity=".45" transform="translate(6 8)"/>' +
      '<rect x="96" y="58" width="214" height="196" fill="#ebe8e1"/>' +
      '<text x="112" y="84" font-family="Cormorant Garamond, serif" font-size="19" fill="#151718">Croissant · 40 chiếc</text>' +
      '<line x1="112" y1="94" x2="294" y2="94" stroke="#151718" stroke-opacity=".3"/>';
    rows.forEach(function (r, i) {
      var y = 114 + i * 20;
      s += '<text x="112" y="' + y + '" font-family="Be Vietnam Pro, sans-serif" font-size="10.5" fill="#151718">' + r[0] + '</text>' +
        '<text x="226" y="' + y + '" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="9.5" fill="#151718" fill-opacity=".7">' + r[1] + '</text>' +
        '<text x="294" y="' + y + '" text-anchor="end" font-family="JetBrains Mono, monospace" font-size="9.5" fill="#151718">' + r[2] + '</text>';
    });
    s += '<line x1="112" y1="210" x2="294" y2="210" stroke="#151718"/>' +
      '<text x="112" y="230" font-family="JetBrains Mono, monospace" font-size="9" letter-spacing="1" fill="#151718" fill-opacity=".7">GIÁ VỐN / CHIẾC</text>' +
      '<text x="294" y="232" text-anchor="end" font-family="Cormorant Garamond, serif" font-size="22" fill="#8a5a1e">4.123đ</text></g>' +
      '<text x="24" y="40" ' + M + '>BẢNG TÍNH · GIÁ VỐN</text>';
    return frame(s, 'g', '#23272a');
  }

  /* 4. Nhìn từ trên: ly cà phê và canelé */
  function cafe() {
    var fl = '', n = 16, cx = 284, cy = 170;
    for (var i = 0; i < n; i++) {
      var a = i / n * Math.PI * 2, a2 = (i + 0.5) / n * Math.PI * 2;
      fl += (i ? 'L' : 'M') + (cx + Math.cos(a) * 46).toFixed(1) + ' ' + (cy + Math.sin(a) * 46).toFixed(1) + ' Q' + (cx + Math.cos(a2) * 54).toFixed(1) + ' ' + (cy + Math.sin(a2) * 54).toFixed(1) + ' ' + (cx + Math.cos(a + Math.PI * 2 / n) * 46).toFixed(1) + ' ' + (cy + Math.sin(a + Math.PI * 2 / n) * 46).toFixed(1);
    }
    return frame(
      '<defs><radialGradient id="crema" cx="45%" cy="40%" r="60%"><stop offset="0" stop-color="#c58b52"/><stop offset=".7" stop-color="#8a5328"/><stop offset="1" stop-color="#5a3216"/></radialGradient>' +
      '<radialGradient id="can" cx="40%" cy="38%" r="65%"><stop offset="0" stop-color="#b8662a"/><stop offset=".7" stop-color="#6e3412"/><stop offset="1" stop-color="#3a1a08"/></radialGradient></defs>' +
      '<circle cx="138" cy="176" r="92" fill="#000" fill-opacity=".4"/><circle cx="132" cy="168" r="92" fill="#e6e1d6"/><circle cx="132" cy="168" r="80" fill="none" stroke="#cfc8b8"/>' +
      '<path d="M206 152 q34 -4 36 18 q0 20 -34 18" fill="none" stroke="#e6e1d6" stroke-width="12" stroke-linecap="round"/>' +
      '<circle cx="132" cy="168" r="62" fill="#f1ede4"/><circle cx="132" cy="168" r="54" fill="url(#crema)"/>' +
      '<path d="M132 196 C104 176 104 150 120 148 C128 147 132 154 132 160 C132 154 136 147 144 148 C160 150 160 176 132 196 Z" fill="#f3e6cf" fill-opacity=".92"/>' +
      '<circle cx="288" cy="176" r="62" fill="#000" fill-opacity=".4"/><circle cx="284" cy="170" r="62" fill="#e6e1d6"/>' +
      '<path d="' + fl + 'Z" fill="url(#can)"/><circle cx="284" cy="170" r="13" fill="#2a1206"/>' +
      '<text x="24" y="40" ' + M + '>BÁN KÈM · CÀ PHÊ</text>' +
      '<text x="232" y="262" ' + M + '>CANELÉ · 55 G</text>', 'f', '#2a241e');
  }
  return { croissant: croissant(), entremets: entremets(), giavon: giavon(), cafe: cafe() };
})();
