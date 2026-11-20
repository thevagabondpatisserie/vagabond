# PR 0: thống kê trước khi đổi giao diện (việc Nghệ sĩ công nghệ)

Ngày 20/11/2026. Nền: main `2ae8e6a35` (v677). PR này KHÔNG đổi một dòng nào của app: không sửa `bep/`, không sửa `app_bep.js`, không tăng APPVER, không thêm dòng `patches.txt`.

## Tóm tắt cho anh Việt

- **Vấn đề.** Muốn đổi giao diện cả app một lần thì phải biết chính xác app có bao nhiêu màn, màn nào dùng chung khung nào, và hiện có những cổng kiểm nào.
- **Việc đã làm.** Ghép bản 3 với phụ lục Codex và sáu điểm anh chốt thành bản 4 (`dac-ta-ban-4.md`). Viết công cụ đếm màn và kiểu hiển thị, chạy ra danh mục 280 màn chia sẵn theo PR 1 đến 5.
- **Kết quả anh sẽ thấy.** Chưa có gì đổi trên app. Từ PR sau, "đạt bao nhiêu phần trăm" được tính trên danh mục này.
- **Anh cần quyết.** Chưa cần quyết gì để làm tiếp PR 1. Bốn điểm ở "Bảng vấn đề gộp" là bằng chứng từ mã, em sẽ xử lý trong PR 1 và trình anh bằng ảnh hoặc ca kiểm; riêng dòng V4 (các trang nằm ngoài app) cần anh cho biết có đưa vào đợt này không, khi nào tiện.

## Các tệp của PR

| Tệp | Nội dung |
|---|---|
| `docs/ui-nghe-si/dac-ta-ban-4.md` | Đặc tả bản 4, thay bản 3 và phụ lục |
| `docs/ui-nghe-si/danh-muc-man.md` | Danh mục màn, hộp thoại, nhóm PR, thành phần chung, trạng thái cần kiểm (máy sinh) |
| `docs/ui-nghe-si/thong-ke-kieu.md` | Số đếm màu, emoji, cỡ chữ, bo góc, khoảng cách, kiểu viết trong thẻ (máy sinh) |
| `docs/ui-nghe-si/pr0-bao-cao.md` | Tệp này |
| `cong_cu/thong_ke_ui_nghe_si.py` | Công cụ thống kê, có `--kiem` |
| `vagabond/khung/kiem_thu/thu_thong_ke_ui_nghe_si.py` | 10 ca kiểm cho công cụ, đã đăng ký trong `chay.py` |
| `.github/workflows/kiem-thu.yml`, `bench-tich-hop.yml` | Thêm nhánh `ui-nghe-si` để PR con được CI kiểm (xem V1) |

## Con số chính

- 82 phần mã trong `bep/` (bản 3 ghi 83 vì tính cả tệp hướng dẫn DOC-DAU-TIEN.md).
- 280 hàm màn. Chia: PR 1 nền 8; PR 2 Bán hàng và Quầy 72; PR 3 Kho, Sản xuất, Thu mua 82; PR 4 Kế toán, Tài chính 44; PR 5 Marketing và còn lại 69; chưa xếp 5 (hai màn khuôn danh sách dùng chung, hai màn nộp quỹ, một hàm mẫu in).
- 13 hộp thoại dùng chung, 83 hàm tự dựng bảng trượt riêng.
- 8.401 chỗ viết kiểu thẳng trong thẻ. 7.750 lần dùng mã màu hex với 584 màu khác nhau (bộ chuẩn mới có khoảng 25 màu).
- 4.059 khai báo cỡ chữ, 2.791 lần ngoài 8 cỡ chuẩn, trong đó 1.691 lần dưới 13.
- 904 khai báo bo góc, 711 lần ngoài 6 mức.
- 5.555 giá trị px lẻ (không chia hết cho 4) trong padding, margin, gap.
- 2.954 emoji và ký hiệu hình, 244 ký tự khác nhau (bảng gốc của đặc tả mới phủ khoảng 45). Con số này gồm cả chuỗi tin gửi đi và mẫu in, là phần KHÔNG được thay.
- Phần nặng nhất theo số kiểu trong thẻ: 11 khách và hợp đồng (661), 17 cài đặt (479), 13 khuyến mãi (353), 19 hồ sơ thanh toán (342), 16 mua hàng (341).

## Cách danh mục xếp màn vào PR

Công cụ đọc bảng nhóm trang chủ (`VGB_NHOM`) và bảng định tuyến (`vgbGo`), rồi đi theo các lời gọi giữa các hàm: mỗi màn về nhóm có đường đi ngắn nhất từ một ô trang chủ. Nhóm về PR theo bản 4 mục 1.

Giới hạn, ghi thật:

- Đọc tĩnh, không chạy app. Màn có tiêu đề dựng bằng biến ghi "(động)".
- Cột Thành phần, Hộp thoại, Trạng thái và Vai đọc cả thân màn lẫn các hàm vẽ phụ màn gọi (sâu tối đa 4 tầng, không sang màn khác), vì nhiều màn dựng nội dung qua hàm phụ (Codex chỉ ở vòng 1: scrDanhMuc, scrKhachChiTiet). Máy thà ghi dư còn hơn ghi sót. Ô ghi "chưa xác định" (hiện 1 màn) phải coi là chịu ảnh hưởng của mọi khung chung.
- Màn mở được từ hai nhóm (ví dụ Công nợ phải thu có ở Bán hàng và Kế toán) chỉ đứng ở MỘT PR, PR đến trước. PR sau đụng khung chung vẫn phải kiểm lại theo cột Thành phần.
- Cột vai chỉ là vai nhắc tên trong thân hàm màn. Bảng "màn x quyền" theo luật rút gọn của bản 4 mục 6 (chỉ nhân ở nơi giao diện khác theo quyền) lập ở PR 1 cùng máy chụp, vì phải chạy app với từng vai mới biết chỗ nào khác thật.
- Danh mục và thống kê đổi theo mã. Mỗi báo cáo PR ghi SHA lúc sinh; chạy `python3 cong_cu/thong_ke_ui_nghe_si.py --kiem` để biết bản trong docs còn khớp mã không.

## Cổng kiểm hiện có

| Cổng | Chạy ở đâu | Bắt được gì | Liên quan việc này |
|---|---|---|---|
| `vagabond/khung/kiem_thu/chay.py` (6.537 ca, 412 tệp ca) | máy làm việc, CI | phép thuần nghiệp vụ, luật màn soi bằng chuỗi | phải xanh ở cả hai chế độ ui-b |
| `hanh_vi/chay.js` (130 tệp ca node, DOM giả) | CI, cổng 10 | chuỗi bấm thật trên màn | DOM giả không có CSS: không bắt được xếp lớp, tràn, màu |
| `dung_app_bep.py --kiem` | CI, cổng 9 | tệp ghép lệch nguồn | PR con đụng bep/ phải dựng lại tệp ghép |
| `kiem_truoc_deploy.sh` (10 công đoạn) | máy làm việc | cú pháp, định tuyến, đường dẫn, phiên bản | giữ nguyên |
| `kiem_dinh_tuyen.py`, `sinh_duong.py` | cổng 7, 8 | ô trang chủ chết, bảng đường lệch | khung trang chủ mới phải giữ `data-go` |
| Bench CI (`bench-tich-hop.yml`) | CI | ERPNext thật: quyền, ghi sổ, nâng cấp | công tắc ở PR 1 phải qua đây |
| `do_vung_bam_565.js`, `do_khung_tim_642.js` | chạy tay, Playwright | vùng bấm thật 44, khung ô tìm | mẫu cho máy đo của PR 1 |
| `gia_lap_trang.js` | cổng 10 một phần, chạy tay | nạp cả app vào node | dùng để dựng màn với API giả |
| `cong_cu/chup_*.cjs` (bài đăng, chi phí, giá vốn) | chạy tay | ảnh từng màn ở 390 | mỗi màn một kịch bản riêng, chưa có máy chụp chung |
| `anh-web.yml` | CI | so ảnh trang KHÁCH với main | chỉ trang khách, app /bep chưa có |
| `thu_nguyen_tac_man_hinh.py`, `thu_card_khong_la_flex.py`, `thu_chip_man_vagabond.py` | trong chay.py | luật AGENTS 2b soi bằng chuỗi | lớp mới không được làm đỏ các ca này |

Còn thiếu, PR 1 phải dựng: máy chụp chung cho app /bep chạy theo danh mục (ba khung và WebKit); kiểm khai báo cho phần `html.ui-b`; máy đo tương phản và phông thực dùng; ảnh chuẩn chế độ tắt so với main; dữ liệu thử có kiểm soát cho từng màn.

## Tài nguyên còn thiếu

- Tệp phông Be Vietnam Pro và Doto chưa có trong repo (`vagabond/public/` chưa có thư mục phông cho app).
- Bộ SVG Lucide chưa có trong repo.
- Bốn hình hoạ tiết vũ trụ: chưa lấy. PR 1 lấy từ design system; không lấy được thì hỏi anh file zip.
- Hai ô trang chủ mở trang ngoài app: `/kiem-banh` (KBD) và `/btp` (BTPO).

## Bảng vấn đề gộp (bằng chứng từ mã)

| Mã | Bằng chứng | Ảnh hưởng tới bản 4 | Hướng xử lý |
|---|---|---|---|
| V1 | Ba workflow CI chỉ chạy cho PR vào `main` (`branches: [main]`) | PR con vào `ui-nghe-si` sẽ không có CI nào chạy, trái yêu cầu giữ đủ cổng | PR này thêm `ui-nghe-si` vào `kiem-thu.yml` và `bench-tich-hop.yml`. Khi gộp về main ở PR 6 thì bỏ lại |
| V2 | `/bep` là Web Page của Frappe: thân trang chỉ có `<div id="vgb"></div>`, `vagabond/trang/bep.js` gắn thẻ script nạp `app_bep.js?t=<giờ>` sau khi trang đã dựng; toàn bộ CSS nằm trong `00-nen.js` và được chèn lúc JS chạy | Hiện chưa có chỗ nào để máy chủ gắn `ui-b` lên thẻ html theo từng tài khoản, và CSS đến SAU lần vẽ đầu. Mục 2 "quyết định trước lần vẽ đầu" cần một đường trả HTML theo người dùng (không qua bộ nhớ đệm trang của Frappe) và CSS nền nạp trong head | PR 1 thiết kế và chứng minh trên bench. Không cần anh quyết, đây là việc kỹ thuật |
| V3 | Cả app chỉ có MỘT khai báo `@media (min-width...)` (màn Bài đăng). Không có bố cục máy tính | Khung 1366x768 hiện là bản điện thoại kéo giãn | Đúng như anh chốt: trình JPEG bố cục máy tính quầy ở PR 1 |
| V4 | Trong `vagabond/trang/` có các trang nghiệp vụ nằm NGOÀI `app_bep.js`: kiem-banh, btp, kho-moi, kho-v2, in-tem, cuon-ma, ong-trang, suc-khoe, sop-san-xuat. Hai trang đầu mở từ ô trang chủ | Nhân viên bấm ô "Kiểm bánh" sẽ từ giao diện mới nhảy sang trang giao diện cũ, tức thấy nửa cũ nửa mới ngay trong một luồng | Cần anh cho biết: đưa hai trang kiem-banh và btp vào đợt này (thêm vào PR 2 và PR 3), hay chấp nhận để sau. Các trang còn lại không mở từ app nên đề nghị để ngoài |
| V5 | `12-van-don.js` có `@import` phông từ Google (Cormorant Garamond, Inter) và `66-goi-mon-tai-ban.js` khai Vagabond Sans, Barlow | Nếu đây là phiếu in và trang cho khách thì nằm ngoài phạm vi (mẫu in không đổi); nếu vẽ trong app thì trái luật "không còn phông nào khác" | PR 2 xác minh từng chỗ, ghi vào bảng ngoại lệ nếu là mẫu in |
| V6 | Còn 27 thẻ `<select>` trong app, trong khi AGENTS 2b.2 cấm | Không thuộc việc đổi lớp hiển thị; thay ô chọn là đổi cách thao tác | Để nguyên trong đợt này, chỉ áp kiểu mới cho ô. Liệt kê ở từng PR nhóm để anh giao riêng nếu muốn |

## Tệp đang giữ

PR 0 không giữ tệp nguồn nào của `bep/`. Đụng ba tệp dùng chung: `vagabond/khung/kiem_thu/chay.py` (thêm một dòng đăng ký ca) và hai workflow (mỗi tệp đổi một hoặc hai dòng).

## Việc chưa làm

- Bảng "màn x quyền" đã rút gọn và trạng thái từng màn chạy thật: làm ở PR 1 cùng máy chụp.
- Phân loại 2.954 emoji theo "lớp vẽ" hay "nội dung gửi đi, mẫu in": làm ở PR 1 (bảng đối chiếu đầy đủ).
- Bảng ánh xạ màu theo vai trò: làm ở PR 1 cho khung chung, PR 2 đến 5 cho từng nhóm màn.
- Xếp tay 5 màn chưa xếp.
