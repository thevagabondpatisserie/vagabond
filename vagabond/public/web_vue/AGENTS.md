# Luật riêng của trang khách

Áp cho trang khách: `vagabond/public/web_vue/` (banh, kho, trang, si), `vagabond/public/web_order/`, `vagabond/www/`, `vagabond/trang/`. Không đặt AGENTS.md trong `vagabond/www/`, vì Frappe phát mọi tệp trong thư mục đó thành trang web công khai.

- Trang đặt bánh của khách là thevagabondpatisserie.com/banh. app.thevagabondpatisserie.com/banh không phải trang khách.
- chay.py KHÔNG gồm các bộ kiểm riêng của trang khách mà CI có (bài học v663). Sửa trang khách thì chạy thêm:
  ```
  node cong_cu/kiem_web_vue_dom.cjs
  python3 cong_cu/ra_nut_web.py
  python3 cong_cu/ma_bam_web_vue.py
  ```
  Lệnh cuối đóng lại mã băm trang. Chạy sau mỗi lần sửa tệp trang, kể cả vòng sửa cuối.
- Chuẩn màn hình và nút theo [2b](/vagabond/public/js/bep/AGENTS.md), nghiệm thu theo [2c](/docs/van-hanh-agent/nghiem-thu-va-ra.md). Chụp ảnh bằng Playwright ở 390 px và mở ảnh ra nhìn trước khi bàn giao.
- Lỗi hiển thị anh Việt chụp trên site thật: đọc computed style của phần tử lỗi và một phần tử đẹp cạnh bên trên site thật rồi so (bài học v636).
- Thêm chế độ mới cho một màn: rà mọi v-if, điều kiện ẩn theo biến chế độ (bài học v663).
