/* PR474: hàm thuần dùng BIN do máy chủ cấp từ tai_khoan.NGAN_HANG.
   Cùng kết quả với qr_chuyen_khoan.py; không tự cắt nội dung đối soát. */
var VgbQr = (function () {
  function crc16(s) {
    var crc = 0xFFFF;
    for (var i=0;i<s.length;i++) {
      crc ^= s.charCodeAt(i) << 8;
      for(var j=0;j<8;j++) crc=((crc<<1)^((crc&0x8000)?0x1021:0))&0xFFFF;
    }
    return crc.toString(16).toUpperCase().padStart(4,'0');
  }
  function truong(ma,s) {
    if(s.length>99) throw Error('Nội dung chuyển khoản quá dài để tạo mã QR. Vui lòng chuyển tay với đầy đủ nội dung.');
    return ma+String(s.length).padStart(2,'0')+s;
  }
  function chuoi(d) {
    if(d.qr_text) return String(d.qr_text);
    if(d.tien == null || String(d.tien).trim() === '') throw Error('Số tiền không hợp lệ để tạo mã QR.');
    var bin=String(d.bin||'').trim(),stk=String(d.stk||'').trim(),so=Number(d.tien == null ? 0 : d.tien);
    if(!/^[0-9]{6}$/.test(bin)) throw Error('Thiếu hoặc sai mã BIN ngân hàng. Kiểm tra tài khoản nhận tiền.');
    if(!/^[A-Za-z0-9]{1,34}$/.test(stk)) throw Error('Thiếu hoặc sai số tài khoản nhận tiền. Kiểm tra tài khoản trước khi chuyển.');
    if(!Number.isFinite(so)||so<0||Math.round(so)>9999999999999) throw Error('Số tiền không hợp lệ để tạo mã QR.');
    so=Math.round(so);
    var nd=String(d.noi_dung||'').replace(/đ/g,'d').replace(/Đ/g,'D').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
    if(/[^\x20-\x7e]/.test(nd)) throw Error('Nội dung có ký tự chưa hỗ trợ trong mã QR. Vui lòng chuyển tay.');
    var tk=truong('00',bin)+truong('01',stk);
    var ra='0002010102'+(so?'12':'11')+truong('38','0010A000000727'+truong('01',tk)+'0208QRIBFTTA')+'5303704';
    if(so) ra+=truong('54',String(so));
    ra+='5802VN';
    if(nd) ra+=truong('62',truong('08',nd));
    ra+='6304';return ra+crc16(ra);
  }
  function tao(d) {
    try {
      var nd=chuoi(d);
      if(typeof qrcode!=='function') throw Error('Chưa tải được thư viện mã QR. Vui lòng tải lại trang hoặc chuyển tay.');
      var cu=qrcode.stringToBytes;
      var q;
      try {
        qrcode.stringToBytes=qrcode.stringToBytesFuncs['UTF-8'];
        q=qrcode(0,'M');q.addData(nd,'Byte');q.make();
      } finally { qrcode.stringToBytes=cu; }
      return {chuoi:nd,anh:'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(q.createSvgTag({cellSize:5,margin:20,scalable:true})),loi:''};
    } catch(e) { return {chuoi:'',anh:'',loi:e.message||'Không vẽ được mã QR. Vui lòng chuyển tay.'}; }
  }
  return {chuoi:chuoi,crc16:crc16,tao:tao};
})();
