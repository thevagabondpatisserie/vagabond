# Thư viện ngoài, không sửa tay

Các tệp thư viện trong thư mục này là bản gốc lấy nguyên từ npm, KHÔNG sửa một byte
nào. Muốn nâng cấp thì tải lại từ npm rồi thay cả tệp, đừng vá tay.

| Tệp | Gói npm | Phiên bản | Giấy phép | sha256 |
|---|---|---|---|---|
| `qz-tray.js` | `qz-tray` | 2.2.4 | LGPL-2.1-only | `38651f7fe2aa3667e39b2459af3387d6c665afe75533d2af27993391fd0338c7` |
| `html2canvas.min.js` | `html2canvas` | 1.4.1 | MIT | `e87e550794322e574a1fda0c1549a3c70dae5a93d9113417a429016838eab8cb` |
| `qrcode.js` | `qrcode-generator` | 2.0.4 | MIT | `79ec86f82856005b1c887905cfccfcfbec3821ca61c7fd5a952faa5f778f791c` |

Cách lấy lại đúng bản này:

```
npm pack qz-tray@2.2.4        # package/qz-tray.js
npm pack html2canvas@1.4.1    # package/dist/html2canvas.min.js
npm pack qrcode-generator@2.0.4   # package/dist/qrcode.js
```

## Vì sao để trong repo chứ không gọi CDN

Trang `/bep` là một bản ghi Web Page nằm trong cơ sở dữ liệu, git không quản.
Thêm một thẻ script vào đó là sửa dữ liệu ngoài git, không có lịch sử để
khôi phục. Nên hai thư viện này nằm trong repo và được `27-in-ngam.js` nạp
lúc chạy từ `/assets/vagabond/js/vendor/`. Không đụng bản ghi Web Page nào.

Thêm nữa quầy thu ngân in bill cả ngày: phụ thuộc một CDN ngoài nghĩa là
mất mạng ra ngoài là mất luôn đường in ngầm.

## Vì sao mã QR vẽ tại máy (22/09/2026)

Bill quầy từng in dòng "quét mã QR để nhập thông tin xuất hoá đơn" mà không
có mã QR (bill HDB-26-09-04366, Dễ báo). Ảnh QR khi đó tải từ
api.qrserver.com: mạng ra ngoài chập chờn là ảnh không về kịp, trong khi chữ
vẫn in. Nay `qrcode.js` vẽ mã ngay trên máy quầy thành ảnh nhúng trong tờ in,
không gọi mạng, nên có chữ là có mã.
