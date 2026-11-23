# Luật chung cho mọi agent trên repo vagabond

Luật gốc dùng chung cho Claude và Codex, anh Việt chốt 22/11/2026 (đề xuất trong [#607](docs/van-hanh-agent/de-xuat-gon-luat-22-11-2026.md)). CLAUDE.md ở gốc chỉ dẫn về tệp này.

Luật riêng của từng phần mã nằm trong AGENTS.md (và CLAUDE.md) của thư mục đó. Quy trình dài đọc khi cần, theo bản đồ cuối tệp. Luật cũ đã thay được giữ nguyên văn ở [luat-cu.md](docs/van-hanh-agent/luat-cu.md).

## Bối cảnh
- Repo này là app ERPNext v16 đang chạy thật cho The Vagabond Pâtisserie (TP HCM). Hệ có tiền, có kho, có hoá đơn điện tử gửi cơ quan thuế.
- Chủ repo là anh Việt. Hai agent cùng làm trên repo: Claude và Codex.
- Ngôn ngữ làm việc là tiếng Việt có dấu.
- Repo để công khai.

## Thứ tự ưu tiên khi hai nguồn khác nhau
1. Chỉ dẫn trực tiếp mới nhất của anh Việt.
2. Instruction project anh dán cho phiên.
3. Tệp này và AGENTS.md/CLAUDE.md của thư mục đang sửa.
4. Tài liệu trong `docs/` và skill.

Thấy mâu thuẫn thì ghi trong bàn giao để anh chốt một nguồn, không tự chọn.

## Phân vai (anh Việt chốt 15/10, xác nhận 22/11/2026)
- Claude viết code và điều phối.
- Codex rà PR và góp ý.
- Anh Việt duyệt.
- Mỗi phạm vi một người ghi code; không sửa chồng nhánh người khác đang làm. Claim và preflight theo [vgb-control-tower/README.md](vgb-control-tower/README.md).

Merge và deploy chỉ khi anh cho phép trong phiên, cho đúng PR đó, và Codex đã rà đạt. Quyền không suy ra cho PR khác. Nhánh main có bảo vệ: PR chỉ merge được khi check `kiem-thu` và `bench` xanh và nhánh đã cập nhật với main. Không tìm cách vượt bảo vệ nhánh.

## Tuyệt đối không
1. Merge hoặc deploy khi anh chưa cho phép trong phiên.
2. Đề xuất sửa hay xoá dữ liệu quá khứ đã ghi sổ, nhất là hoá đơn điện tử. Thấy sai thì liệt kê cho anh.
3. Sửa Server Script trên Desk (không có lịch sử, mất không khôi phục được).
4. Đưa dữ liệu thật (tên, số tài khoản, số thẻ, mã giao dịch, mã số thuế, số điện thoại khách) hay bí mật (token, mật khẩu, khoá) vào repo, kể cả trong ca kiểm. Dùng dữ liệu giả cùng dạng. Ca bench không được đụng bản ghi thật trên site ([luật bench](vagabond/khung/kiem_that/AGENTS.md)).
5. Đặt hook trên `"*"` mà không chừa hạ tầng Frappe (16/08 cả tiệm mất email bốn ngày).
6. Force push, viết đè nhánh hay tệp của phiên khác.

## Đầu phiên
```
git fetch origin
git log origin/main -n 10 --oneline
git status -sb
grep APPVER vagabond/public/js/bep/12-van-don.js && tail -3 vagabond/patches.txt
```
- Đứng trên hoặc bằng `origin/main` rồi mới sửa. Không dựa vào trí nhớ về cấu trúc tệp.
- Đọc AGENTS.md (hoặc CLAUDE.md) của thư mục sắp sửa.
- Tìm bài học của mảng đó: `grep -n <từ khoá> docs/bai-hoc-su-co.md`, rồi chỉ đọc mục liên quan, không đọc cả tệp. `grep -rl <từ khoá> docs/` trước khi sửa một nghiệp vụ.
- GitHub là trạng thái hiện tại; ghi chú cũ không phải bằng chứng.

## Phiên bản, bản vá, sổ tay
- Đặt số theo `origin/main` đọc ngay trước khi đặt:
  - `APPVER` trong `vagabond/public/js/bep/12-van-don.js` chỉ tăng;
  - mỗi lần phát hành thêm một dòng `vagabond.patches.dong_bo_cau_truc #vNNN` vào `vagabond/patches.txt`, giữ mọi dòng cũ ([luật bản vá](vagabond/patches/AGENTS.md)).
- Hai PR đang mở có thể cùng đặt một số. PR merge sau phải nâng số mới.
- Mỗi APPVER có mục `## vNNN` trong `vagabond/so_tay/_phien-ban.md` và mục sổ tay tương ứng. Bản sửa ngầm ghi `- Không đổi thao tác: <lý do>`.
- `app_bep.js` là tệp máy ghép từ `vagabond/public/js/bep/`. Sửa nguồn rồi chạy `python3 dung_app_bep.py`.
- Sửa tài liệu không cần số phiên bản.

## Viết code
- Tách phép thuần (không chạm Frappe) khỏi phần chạm hệ. Tính năng mới có ca kiểm trong `vagabond/khung/kiem_thu/`, đăng ký trong `chay.py`.
- Chạm ghi sổ, kho, quyền thì có ca bench trong `vagabond/khung/kiem_that/`.
- Cổng kế toán (H10.5, bắt buộc): đổi thuế, giá vốn, thanh toán thì ca bench đối chiếu chứng từ nguồn tới số tiền, chiều Nợ/Có và đúng tài khoản. Mọi đường mới có thể ghi sổ phải chỉ ra thao tác duyệt của kế toán hoặc chính sách tự động anh Việt đã duyệt. Bench xanh chưa đủ để bàn giao một đường ghi sổ mới. Chi tiết: [nghiem-thu-va-ra.md](docs/van-hanh-agent/nghiem-thu-va-ra.md).
- Thêm `@frappe.whitelist()` thì thêm tên vào `vagabond/khung/kiem_thu/thu_cua_ngo.py`.
- Cùng một con số tính ở nhiều nơi thì gom về một hàm.
- Giá trị 0, chuỗi rỗng, False người dùng chọn đọc bằng `is None`, không bằng `or mặc định`.
- Quy ước đầy đủ: [quy-uoc-code.md](docs/van-hanh-agent/quy-uoc-code.md). Quy tắc nghiệp vụ đã chốt: [docs/nghiep-vu/](docs/nghiep-vu/quy-tac-da-chot.md).

## Cổng kiểm trước bàn giao
```
python3 vagabond/khung/kiem_thu/chay.py -im
python3 dung_app_bep.py --kiem
sh kiem_truoc_deploy.sh
```
- Giả lập CI không có `requests`: xem [luật kiểm thử](vagabond/khung/kiem_thu/AGENTS.md). Trang khách có thêm bộ riêng: xem [luật trang khách](vagabond/public/web_vue/AGENTS.md).
- Màn hình và luồng nghiệp vụ: nghiệm thu theo 2c, người rà theo H10, cùng trong [nghiem-thu-va-ra.md](docs/van-hanh-agent/nghiem-thu-va-ra.md).
- Chạy pyflakes trên tệp Python đã đụng.
- Đột biến: cố tình làm hỏng chỗ vừa sửa, ghi đúng số bắt được.
- Bench CI đỏ thì đọc đúng ca đỏ trước khi kết luận.
- Chốt chặn tự động `cong_cu/chot_chan.py` chạy trong CI. Nó kiểm APPVER lùi, mất dòng patches.txt, em dash, dữ liệu thật và bí mật trên dòng thêm mới. Từ ngày `CHAN_TU` ghi trong tệp đó, lỗi làm đỏ CI; trước ngày đó chỉ cảnh báo.

## Làm việc với bên rà
- Gọi bằng comment trên đúng PR, không trong issue.
- Lệnh:
  - `@codex review` chỉ để rà;
  - muốn Codex sửa thì `@codex fix <finding, PR, SHA, phạm vi, ca hồi quy>`, rồi fetch nhánh kiểm có commit mới chưa.
- Tự rà theo [sổ mẫu lỗi](docs/van-hanh-agent/so-mau-loi.md) trước khi gọi. Sửa theo loại lỗi: quét cả PR tìm mọi chỗ cùng loại, sửa trong một lượt đẩy.
- Luật dừng: cùng một finding đã gọi 3 vòng trong 24 giờ mà không có bằng chứng mới thì không gọi nữa; viết ngắn chỗ bất đồng, mời anh phân xử.
- Không trả lời comment chỉ cảm ơn. Không tự hẹn giờ chờ bên kia.
- Chi tiết lệnh và xác nhận bàn giao: [lam-viec-voi-codex.md](docs/van-hanh-agent/lam-viec-voi-codex.md).

## Bàn giao
- Một comment trên PR. Dòng đầu là một trong năm nhãn: `[CẦN DUYỆT]`, `[BỊ CHẶN]`, `[ĐÃ ĐẨY - CHỜ KIỂM]`, `[SẴN SÀNG DEPLOY]`, `[ĐÃ DEPLOY]`. Không dùng `[ĐÃ SỬA XONG]`.
- Comment ghi:
  - SHA cuối và SHA nền;
  - tự rà;
  - kết quả kiểm;
  - việc chưa làm;
  - đúng một khối `telegram-tomtat` (tối đa hai câu nghiệp vụ);
  - câu chốt không merge, không deploy.
- Kiểm biên nhận Telegram cho đúng comment. Chi tiết: [ban-giao.md](docs/van-hanh-agent/ban-giao.md), [thong-bao-telegram.md](docs/thong-bao-telegram.md).
- Chỉ tính bàn giao khi SHA đã có trên GitHub.
- Sau deploy: kiểm site thật, đăng `[ĐÃ DEPLOY]` theo [mau-tin-phat-hanh.md](docs/mau-tin-phat-hanh.md), soạn tin việc cần làm theo bộ phận cho anh. Chi tiết: [deploy.md](docs/van-hanh-agent/deploy.md).

## Trình bày
- Không dùng em dash, en dash ở bất kỳ đâu (comment, tệp, nội dung ghi vào ERPNext); chỉ dùng gạch ngang thường.
- Issue, PR, comment viết tiếng Việt có dấu, mở đầu bằng tóm tắt nghiệp vụ.
- Chữ trên màn hình, sổ tay, tin nhắn theo [quy tắc chữ ERP](docs/quy-tac-chu-erp.md): đúng thuật ngữ, không gọi tên người.

## Bản đồ tài liệu
| Cần | Đọc |
|---|---|
| App /bep, vỏ hàm, chuẩn màn hình (mục cũ 2, 2b) | [vagabond/public/js/bep/AGENTS.md](vagabond/public/js/bep/AGENTS.md) |
| Trang khách | [vagabond/public/web_vue/AGENTS.md](vagabond/public/web_vue/AGENTS.md) |
| Ca kiểm khung (mục cũ 6, tầng một) | [vagabond/khung/kiem_thu/AGENTS.md](vagabond/khung/kiem_thu/AGENTS.md) |
| Ca bench (mục cũ 6, tầng hai) | [vagabond/khung/kiem_that/AGENTS.md](vagabond/khung/kiem_that/AGENTS.md) |
| Bản vá | [vagabond/patches/AGENTS.md](vagabond/patches/AGENTS.md) |
| Nghiệm thu, người rà (mục cũ 2c, H10) | [docs/van-hanh-agent/nghiem-thu-va-ra.md](docs/van-hanh-agent/nghiem-thu-va-ra.md) |
| Chống ghi đè (mục cũ 1) | [docs/van-hanh-agent/chong-ghi-de.md](docs/van-hanh-agent/chong-ghi-de.md) |
| Claim, preflight chống sửa chồng | [vgb-control-tower/README.md](vgb-control-tower/README.md) |
| Quy ước code (mục cũ 3, 8) | [docs/van-hanh-agent/quy-uoc-code.md](docs/van-hanh-agent/quy-uoc-code.md) |
| Quy tắc nghiệp vụ, soi mã lõi (mục cũ 4, 5) | [docs/nghiep-vu/](docs/nghiep-vu/quy-tac-da-chot.md) |
| Deploy, email phát hành (mục cũ 7, 11) | [docs/van-hanh-agent/deploy.md](docs/van-hanh-agent/deploy.md) |
| Làm việc với Codex (mục cũ 9, 9b) | [docs/van-hanh-agent/lam-viec-voi-codex.md](docs/van-hanh-agent/lam-viec-voi-codex.md) |
| Sổ mẫu lỗi Codex | [docs/van-hanh-agent/so-mau-loi.md](docs/van-hanh-agent/so-mau-loi.md) |
| Telegram, bàn giao cloud | [docs/van-hanh-agent/ban-giao.md](docs/van-hanh-agent/ban-giao.md) |
| Quy trình chung, cloud, mẫu bàn giao | [INSTRUCTION_VAGABOND.md](INSTRUCTION_VAGABOND.md), [docs/van-hanh-agent/README.md](docs/van-hanh-agent/README.md) |
| Bài học sự cố | [docs/bai-hoc-su-co.md](docs/bai-hoc-su-co.md) (grep theo từ khoá) |
| Luật cũ đã thay | [docs/van-hanh-agent/luat-cu.md](docs/van-hanh-agent/luat-cu.md) |
