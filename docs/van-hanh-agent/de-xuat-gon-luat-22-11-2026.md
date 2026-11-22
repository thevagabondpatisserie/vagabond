# Đề xuất gọn luật agent và chốt chặn tự động (22/11/2026)

## Tóm tắt cho anh Việt

- **Vấn đề.** Mỗi phiên Claude hoặc Codex phải đọc khoảng 4.800 dòng luật: CLAUDE.md, AGENTS.md, INSTRUCTION_VAGABOND.md, 4 tệp vận hành agent và 3.207 dòng bài học sự cố, cộng instruction của project. Luật chồng theo ngày (14/09, 16/09, 12/10, 15/10, 17/11) và có chỗ đá nhau, nhất là chuyện ai viết code, ai rà. Nhiều luật quan trọng chỉ dựa vào việc agent tự nhớ, trong khi nhánh main chưa có lớp bảo vệ nào, nên PR vẫn merge được khi bench đỏ.
- **Việc đề xuất.**
  1. Gom về một bộ luật gốc ngắn (khoảng 120 dòng) dùng chung cho cả Claude lẫn Codex. Quy ước riêng của từng phần mã đặt ở CLAUDE.md của thư mục đó. Quy trình dài chuyển thành tài liệu tra khi cần.
  2. Đổi các luật "phải nhớ" thành chốt chặn máy tự kiểm trong CI, kèm bảo vệ nhánh main.
- **Kết quả sẽ thấy.** Phiên nào cũng đọc ít hơn mà làm đúng hơn. Lỗi như hai PR cùng đặt v675, hay dữ liệu sao kê thật lọt vào ca kiểm, bị máy chặn ngay trên PR thay vì chờ Codex hoặc anh phát hiện.
- **Anh cần chốt.** Bốn câu hỏi ở mục 4. Sau đó em làm theo lộ trình ở mục 5. PR này chỉ có tài liệu, chưa đổi luật đang chạy.

Bản nháp bộ luật gốc: [ban-nhap-luat-goc.md](ban-nhap-luat-goc.md).

Cơ sở: tài liệu 27 trang của Anthropic về cách các startup dùng Claude Code
(https://assets.claude.com/054519a5658ddeee3cf9791eda1a36f4455ad842.pdf), mục "Trust, but Verify" và checklist cuối:
- luật bất di bất dịch ở tệp gốc, quy ước riêng ở tệp theo thư mục;
- skill dùng chung trong repo;
- hook làm cổng cứng, chạy bất kể model quyết định gì;
- vòng lặp có điều kiện dừng.

## 1. Hiện trạng đo được (main f8c11c91)

| Tệp | Dòng | Ghi chú |
|---|---|---|
| CLAUDE.md | 346 | 5 lớp "quy tắc hiệu lực" theo ngày chồng lên phần gốc |
| AGENTS.md | 780 | cùng 5 lớp đó chép lại, cộng quy ước kỹ thuật |
| INSTRUCTION_VAGABOND.md | 141 | ghi "Codex viết code" |
| docs/van-hanh-agent/*.md | 364 | 4 tệp |
| docs/bai-hoc-su-co.md | 3.207 | 168 mục, xếp theo thời gian, lẫn chung và riêng từng mảng |

CLAUDE.md bắt đầu phiên bằng `cat AGENTS.md` và `cat docs/bai-hoc-su-co.md`, tức nạp gần như toàn bộ chữ ở trên mỗi phiên.

## 2. Mâu thuẫn đang có

| # | Chủ đề | Nguồn A | Nguồn B | Thực tế gần đây |
|---|---|---|---|---|
| M1 | Ai viết code | CLAUDE.md "Claude là lead (12/10)", AGENTS.md mục 10, INSTRUCTION_VAGABOND.md mục 1, tai_lieu/INSTRUCTION_VAGABOND.md đầu tệp, van-hanh-chung.md mục 2: Codex viết code, Claude rà | CLAUDE.md và AGENTS.md đầu tệp "Phân công 15/10": Codex rà, Claude sửa. Instruction project 18/11 mục B: Claude viết code, Codex rà | PR #590 tới #605: Claude viết, Codex rà |
| M2 | Lệnh mời rà | `@claude review delta <SHA>` (14/09, INSTRUCTION mục 6, van-hanh-chung mục 3) | `@codex review` (CLAUDE.md, instruction project H9) | Claude viết thì gọi `@codex review` |
| M3 | Ai bấm deploy | AGENTS.md mục 7: "Không bao giờ để trợ lý tự động bấm" | CLAUDE.md: anh cho phép đúng PR thì tự merge, deploy | Claude deploy khi anh cho phép (18/11) |
| M4 | Bộ nhãn | `[ĐÃ SỬA XONG]`, `[SẴN SÀNG DEPLOY]` (CLAUDE.md phần Telegram) | `[ĐÃ ĐẨY - CHỜ KIỂM]` (INSTRUCTION mục 3, instruction project H9); 15/10 cấm gọi review xong là `[ĐÃ SỬA XONG]` | Dùng `[CẦN DUYỆT]`, `[BỊ CHẶN]`, `[ĐÃ DEPLOY]` |
| M5 | Đường đẩy code | Instruction project mục C: "git push luôn hỏng, đẩy qua trình duyệt" | Phiên 19/11 đẩy thẳng bằng git được | git push chạy |
| M6 | Đầu phiên đọc gì | `cat` toàn bộ AGENTS.md và bài học | van-hanh-chung mục 4: tra theo nghiệp vụ, không nạp toàn bộ | Mỗi phiên tự chọn |

M5 nằm trong instruction project do anh dán, nên em chỉ ghi lại để anh sửa bên project.

Đính chính sau lượt rà của Codex: bản đầu có mục M7 ghi `vgb-control-tower/` không có trong repo. Ghi vậy là sai, thư mục có thật và là đầu mối claim, preflight chống sửa chồng; bộ luật mới giữ đường dẫn tới nó. Hai tệp INSTRUCTION (gốc và `tai_lieu/`) có vai khác nhau: một tệp là quy trình chung, một tệp là nghiệp vụ. Chúng chỉ dính M1.

## 3. Bố cục mới: ba tầng

**Tầng 1. Một bộ luật gốc cho cả hai agent.**
- AGENTS.md là bản duy nhất, khoảng 120 dòng (bản nháp kèm theo).
- CLAUDE.md gốc chỉ còn dòng `@AGENTS.md`: Claude Code nạp tệp được dẫn bằng `@`. Codex đọc AGENTS.md theo mặc định. Hai agent đọc đúng một nội dung, hết cảnh chép hai nơi rồi lệch nhau.
- Chỉ giữ: bối cảnh, thứ tự ưu tiên nguồn, phân vai, việc tuyệt đối không làm, đầu phiên, luật phiên bản, cổng kiểm, gọi bên kia, bàn giao, trình bày, bản đồ tài liệu.

**Tầng 2. CLAUDE.md theo thư mục.** Claude Code tự nạp khi sửa tệp trong thư mục đó. Codex đọc được AGENTS.md lồng nhau, nên mỗi thư mục có một AGENTS.md cùng nội dung, với CLAUDE.md là dòng `@AGENTS.md`.

| Thư mục | Lấy từ | Nội dung chính |
|---|---|---|
| `vagabond/public/js/bep/` | AGENTS.md mục 2, 2b; phần màn của 2c | Vỏ hàm, app_bep.js ghép, APPVER, chuẩn màn hình, cổng giao diện, gia_lap_trang.js |
| `vagabond/public/web_vue/` (banh, kho, trang, si), `vagabond/public/web_order/`, `vagabond/www/` | Bài học v663, cổng trang khách, AGENTS.md mục 2 phần trang khách | Hai bộ kiểm CI có mà chay.py không có, mã băm trang, tên miền trang khách |
| `vagabond/khung/kiem_thu/` | AGENTS.md mục 6 tầng một; CLAUDE.md "ca kiểm tự che lỗi" | Đăng ký chay.py, thu_cua_ngo, CI không requests, đột biến đọc trung thực |
| `vagabond/khung/kiem_that/` | AGENTS.md mục 6 tầng hai, H10.5 | Bench, ca không đụng dữ liệu thật (bài học #592), dữ liệu giả, cổng kế toán H10.5 |
| `vagabond/patches/` | Bài học "thiếu dòng patch", v674 Singles | patches.txt, bản vá phải có ca bench chạy execute() |
| Mô đun kế toán, kho | AGENTS.md mục 4, 5 | Quy tắc nghiệp vụ đã chốt theo mảng, soi mã lõi trước khi can thiệp |

**Tầng 3. Quy trình tra khi cần.** Gồm nghiệm thu và trách nhiệm người rà (AGENTS.md 2c, H10, hướng dẫn H3/H5/H8.1, chuyển nguyên văn sang `docs/van-hanh-agent/nghiem-thu-va-ra.md`), làm việc với Codex, bàn giao cloud, Telegram, deploy, email phát hành. Mỗi quy trình một tệp trong `docs/van-hanh-agent/` (hoặc skill trong `.agents/skills/`, nơi đã có 2 skill). Tầng 1 chỉ giữ một dòng dẫn tới.
- Skill hiện chỉ nằm trong tài khoản Claude của anh ("thiết kế tiện lợi", "chống ghi đè", "thông báo phát hành") chép vào `.agents/skills/`, để Codex và bot GitHub cùng đọc.
- Bài học sự cố chia theo mảng thành `docs/bai-hoc/<mảng>.md`. `docs/bai-hoc-su-co.md` còn là mục lục, mỗi mục một dòng. Đầu phiên chỉ đọc mảng mình sửa.

**Nguyên tắc chuyển.** Không xoá chữ nào: mọi đoạn bị bỏ khỏi tầng 1 được chuyển nguyên văn sang tầng 2 hoặc 3, rồi mới bỏ. Đoạn mâu thuẫn thì giữ bản anh chốt ở mục 4, bản kia chuyển vào `docs/van-hanh-agent/luat-cu.md` kèm ngày thay.

## 4. Anh cần chốt

1. **Phân vai (M1).** Em đề xuất theo thực tế và instruction 18/11: Claude viết code và điều phối, Codex rà PR, anh duyệt. Bỏ phân công 12/10.
2. **Lệnh mời rà (M2).** Theo câu 1: Claude gọi `@codex review`, kèm `@codex fix` khi muốn Codex sửa. Lệnh `@claude review delta` chỉ dùng khi Codex là người viết.
3. **Bộ nhãn (M4).** Em đề xuất đúng năm nhãn:
   - `[CẦN DUYỆT]`
   - `[BỊ CHẶN]`
   - `[ĐÃ ĐẨY - CHỜ KIỂM]`
   - `[SẴN SÀNG DEPLOY]`
   - `[ĐÃ DEPLOY]`

   Bỏ `[ĐÃ SỬA XONG]`, vì dễ hiểu lầm là đã rà đạt. Cần sửa bộ lọc Telegram theo.
4. **Bảo vệ nhánh main.** Việc này cần anh bấm, vì chỉ chủ repo có quyền. Vào Settings, Branches, thêm luật cho `main`:
   - bắt buộc check `kiem-thu` và `bench` xanh;
   - bắt buộc nhánh cập nhật với main trước khi merge.

   Đổi lại, mỗi PR phải chờ bench khoảng 25 phút trước khi merge. Nếu anh muốn nhanh hơn, có thể chỉ bắt buộc `kiem-thu` và giữ bench như hiện nay.

## 5. Chốt chặn tự động

Một tệp kiểm `cong_cu/chot_chan.py`, chạy chung ở ba nơi: bước mới trong `kiem-thu.yml` trên mọi PR, `kiem_truoc_deploy.sh`, và hook trước commit của Claude Code (`.claude/settings.json`, chỉ chạy phần nhanh). Codex không có hook tương đương, nên CI là lớp chặn chung cho cả hai.

| # | Luật đang dựa vào trí nhớ | Chốt chặn | Đã có? |
|---|---|---|---|
| C1 | Thêm hàm whitelist phải đăng ký | `thu_cua_ngo.py` | Có |
| C2 | Mỗi APPVER có mục sổ tay | `thu_so_tay_phien_ban_645` | Có |
| C3 | app_bep.js khớp bep/ | `dung_app_bep.py --kiem` | Có |
| C4 | APPVER chỉ tăng | So APPVER của PR với APPVER trên nhánh nền: lùi là đỏ. PR đổi code app mà bằng số trên main cũng đỏ | Chưa |
| C5 | Hai PR không cùng số phiên bản | C4 cộng luật "nhánh cập nhật với main" ở mục 4.4: PR nào merge sau phải lên số mới. Ca 19/11 (#592 và #594 cùng v675) sẽ bị chặn tự động | Chưa |
| C6 | Giữ mọi dòng patches.txt của phiên khác | Mọi dòng của patches.txt trên nền phải còn trong PR; dòng `dong_bo_cau_truc` mới không trùng dòng đã có | Chưa |
| C7 | Không em dash, en dash | Dò trên các dòng THÊM MỚI của diff (md, py, js, json, html) | Chưa |
| C8 | Dữ liệu thật không vào repo công khai | Dò dòng thêm mới trong ca kiểm và tài liệu: dãy số dài kiểu số tài khoản, số thẻ, mã số thuế, số điện thoại, email người thật. Có danh sách chuỗi giả được phép (000000..., KT...). Ca #592 ngày 19/11 sẽ bị chặn | Chưa |
| C9 | Không đưa bí mật vào repo | Dò mẫu token (ghp_, sk-, khoá API, chuỗi Bearer) trên dòng thêm mới | Chưa |
| C10 | Không xoá code phiên khác | Cảnh báo (không chặn) khi PR xoá nhiều dòng ở tệp nằm ngoài phạm vi khai trong mô tả PR | Chưa, chỉ cảnh báo |
| C11 | Merge khi cổng xanh | Bảo vệ nhánh main (mục 4.4) | Chưa, cần anh bấm |

Mỗi chốt chặn có ca kiểm riêng, dựng đúng tình huống từng xảy ra (đỏ trên tình huống cũ, xanh khi sửa), đăng ký trong chay.py.

Luật vẫn để agent tự giữ, vì máy khó kiểm đúng: luật dừng 3 vòng với Codex, sửa theo loại lỗi, không đề xuất sửa dữ liệu quá khứ, không sửa Server Script trên Desk.

## 6. Lộ trình

| PR | Nội dung | Rủi ro |
|---|---|---|
| A (PR này) | Tài liệu đề xuất và bản nháp luật gốc | Không đổi hành vi |
| B | Áp bố cục ba tầng theo mục 3: AGENTS.md gốc gọn, CLAUDE.md gốc `@AGENTS.md`, tệp theo thư mục, chuyển nguyên văn phần dài, sửa đường dẫn chết. Kèm bảng đối chiếu từng đoạn cũ đã đi đâu | Chỉ tài liệu |
| C | `cong_cu/chot_chan.py` (C4 tới C10), ca kiểm, bước CI, hook Claude Code | Có thể chặn nhầm. Chạy chế độ cảnh báo 3 ngày rồi mới chặn |
| D | Anh bật bảo vệ nhánh (C11) | Merge chậm hơn |
| E | Chia bài học theo mảng, chép skill vào `.agents/skills/` | Chỉ tài liệu |

Mỗi PR một lượt Codex rà. Không PR nào cần deploy, trừ khi C thêm ca kiểm vào chay.py, mà việc đó cũng không đổi hành vi app.
