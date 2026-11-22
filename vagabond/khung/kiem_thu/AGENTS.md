# Luật riêng của bộ kiểm thử tầng một

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 512 tới 537. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## 6. Bộ kiểm thử, HAI TẦNG

### Tầng một: kiểm thử phép thuần, chạy tay không

```
python3 vagabond/khung/kiem_thu/chay.py -im   # tầng khung, hơn 300 ca
python3 kiem_diem_otp.py                      # hơn 2000 ca
python3 kiem_phien_ban.py
sh kiem_truoc_deploy.sh                        # cổng 8 công đoạn
```

Chạy được ở mọi nơi, kể cả máy chạy CI của GitHub: không Frappe, không
site, không thư viện mạng. Ca kiểm nào kéo theo `requests` là ca kiểm đặt
sai chỗ. Tái hiện môi trường CI ngay tại máy:

```
mkdir -p /tmp/chanreq
printf 'raise ImportError("gia lap CI")\n' > /tmp/chanreq/requests.py
PYTHONPATH=/tmp/chanreq python3 vagabond/khung/kiem_thu/chay.py -im
```

Thêm tính năng thì thêm ca kiểm cho nó, trong cùng lần sửa. Ca kiểm phải
chốt lại **cái bẫy đã làm hỏng**, không chỉ chốt đường đi đúng. Đọc các ca
sẵn có để thấy văn phong: mỗi ca có một câu tiếng Việt nói rõ nó giữ điều
gì.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ CLAUDE.md dòng 228 tới 256. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Cổng kiểm bắt buộc trước khi bàn giao

PR đổi màn hình phải đạt bảng kiểm và chuỗi thao tác ở AGENTS.md mục 2c.5.
Bàn giao ghi màn đã kiểm, vai, SHA, kích thước, ảnh có CSS và phần chưa đạt.
PR chỉ tài liệu ghi cổng giao diện không áp dụng. Sau triển khai áp mục 2c.6
và chuẩn bị bản tin việc cần làm theo bộ phận cho anh Việt.

```
python3 vagabond/khung/kiem_thu/chay.py -im
python3 dung_app_bep.py --kiem
sh kiem_truoc_deploy.sh
```

PR đụng trang khách (web_vue, www, web_order, trang/banh.html) chạy thêm hai
bộ mà chay.py không gồm nhưng CI có (bài học v663):

```
node cong_cu/kiem_web_vue_dom.cjs
python3 cong_cu/ra_nut_web.py
```

Và giả lập CI tay không, vì máy chạy CI không có sẵn `requests`:

```
mkdir -p /tmp/chanreq
printf 'raise ImportError("gia lap CI")\n' > /tmp/chanreq/requests.py
PYTHONPATH=/tmp/chanreq python3 vagabond/khung/kiem_thu/chay.py -im
```

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ CLAUDE.md dòng 276 tới 289. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Ca kiểm có thể tự che mất lỗi

Ca kiểm phải dựng ĐÚNG chuỗi thao tác của khách, không gọi thêm hàm nào "cho
chắc", vì hàm đó có thể chữa lỗi ngay trước khi ca kiểm kịp nhìn.

Dò chuỗi trong mã nguồn KHÔNG phải là kiểm thử. Mã chạy trên trình duyệt thì nạp
cả trang vào node bằng `vagabond/khung/kiem_thu/gia_lap_trang.js`.

Chạy đột biến xong phải đọc trung thực. Nếu 5 đột biến chỉ bắt được 2 thì viết là
2 kèm giải thích, không làm tròn thành 5 trên 5.

Ba mục trên là bản rút gọn. Lý do đầy đủ và ca thật nằm trong
`docs/bai-hoc-su-co.md`, đọc trước khi viết ca kiểm.
