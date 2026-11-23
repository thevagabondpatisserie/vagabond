# Luật cũ đã thay (giữ nguyên văn để tra)

Các đoạn dưới đây đã được thay bằng luật gốc [AGENTS.md](/AGENTS.md) theo đề xuất [#607](/docs/van-hanh-agent/de-xuat-gon-luat-22-11-2026.md), anh Việt chốt 22/11/2026: Claude viết code, Codex rà; mời rà bằng `@codex review`; năm nhãn bàn giao; bảo vệ nhánh main. Chỗ nào dưới đây trái với luật gốc thì luật gốc thắng.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 1 tới 9. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Quy tắc chung cập nhật 17/11/2026

Mục 2b, 2c và H10 là nguồn chung về giao diện, nghiệm thu và review cho cả
Codex lẫn Claude. Các mục này ưu tiên hướng dẫn cũ mâu thuẫn cùng chủ đề
trong repo và trong skill. Chỉ dẫn trực tiếp của anh Việt và instruction
project do anh dán luôn thắng; ai thấy hai nguồn mâu thuẫn thì ghi trong bàn
giao để anh chốt một nguồn. Phạm vi anh giao quyết định ai làm, ai duyệt và
quyền phát hành.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 49 tới 91. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Cửa vào chung từ 12/10/2026

Đọc [Instruction chung](/INSTRUCTION_VAGABOND.md) trước. Quy trình nhận việc,
commit, push, bàn giao cloud và model ở tài liệu đó là nguồn chuẩn; mục cũ
mâu thuẫn bên dưới không được dùng để bỏ bước push hoặc quay về Astra low.

## Quy tắc hiệu lực 16/09/2026

Đọc [quy tắc chung](/docs/van-hanh-agent/van-hanh-chung.md). Sáu thay đổi đã
được anh Việt duyệt; mục đó ưu tiên các luật cũ mâu thuẫn về model/tag/vòng.

## Quy tắc mới 14/09/2026: tiết kiệm token và gọi bot đúng việc

Đọc [quy tắc dùng chung](/docs/van-hanh-agent/tiet-kiem-token.md). Mục này thay
luật 13/09 yêu cầu mọi comment đều tag đối ứng: chỉ tag khi có yêu cầu hành
động. Review dùng `@claude review delta <FULL_HEAD_SHA>`, ghi SHA đã review,
base, phạm vi và bằng chứng. Nếu đạt thì chốt SHA không tag lại; có finding
cần sửa mới tag Codex. Không review trùng, không tự tạo lịch polling chờ sửa.
Giữ nguyên quyền, owner và cổng phát hành; đây chưa phải khóa chi phí bằng máy.

# Đọc trước khi sửa một dòng nào

Tệp này dành cho MỌI trợ lý lập trình làm việc trên repo này: Roo Code,
Claude Code, Cline, Gemini CLI, Cursor, hoặc người mới. Đọc hết rồi hãy gõ.

Đây là hệ đang chạy thật của một tiệm bánh: có tiền, có kho, có hoá đơn
điện tử gửi cơ quan thuế. Một lỗi ở đây không phải là một bug, nó là một
ca bán hàng sai số hoặc một kho lệch không đối chiếu lại được.

## Đầu phiên: đọc quy ước và bài học chung

Trước khi sửa, đọc hết tệp này, `tai_lieu/INSTRUCTION_VAGABOND.md` và
`docs/bai-hoc-su-co.md`; dùng `rg --files docs` rồi tìm từ khoá nghiệp vụ
trong `docs/` để đọc tài liệu liên quan. Áp dụng cả phiên local lẫn cloud.
Không tạo bản bài học riêng cho Codex rồi để lệch bản của Claude.

Cuối phiên có công việc thực chất, bổ sung bài học mới đã có bằng chứng vào
`docs/bai-hoc-su-co.md` trong PR đang làm: triệu chứng, nguyên nhân, cách phòng
và Issue/PR nguồn. Không thêm mục trùng; không ghi bí mật hoặc dữ liệu cá nhân.
Nhật ký chi tiết local vẫn theo mục 10. Nếu cloud không có thư mục nhật ký
trên máy anh Việt, ghi bàn giao trên PR và nói rõ chưa cập nhật nhật ký local;
không tạo database hoặc giả nhận đã ghi trên máy.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 687 tới 727. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## 10. Phân công cập nhật 12/10/2026 - ưu tiên so với mọi phân công cũ

Codex viết code, kiểm thử, tích hợp bench trên SHA, sửa qua review, tự push
lên nhánh PR và bàn giao. Claude là lead: chốt hướng, giao việc, rà độc lập.
Merge và deploy chỉ khi anh Việt cho phép trong phiên, cho đúng PR đó; người
được cho phép tự làm và kiểm site thật. Đọc `tai_lieu/INSTRUCTION_VAGABOND.md`
đầu phiên; bản 12/10/2026 thay phân công 09/09/2026.

### 10b. Claude lead: tự giao việc, không chờ anh Việt nhắc

- Rà xong một bản Codex đẩy lên, Claude tự đăng ngay lệnh cho bước kế tiếp
  trên đúng PR: có lỗi thì `@codex fix` kèm finding, số liệu tái hiện, tệp,
  ca kiểm và tiêu chí đạt; đạt mà PR còn giai đoạn thì giao giai đoạn kế; đạt
  và đủ cổng thì báo anh Việt duyệt, hoặc tự merge/deploy nếu đã được phép.
- Anh Việt báo lỗi: Claude đọc dữ liệu thật trên site để khoanh nguyên nhân,
  rồi giao Codex trên PR đang mở cùng phạm vi, không mở PR mới. Lỗi cấu hình
  hay dữ liệu thì nói rõ ai làm gì trong Cài đặt, không giao sửa code.
- Mỗi lệnh có: PR và SHA nền, số liệu thật, việc theo thứ tự, ca kiểm bắt
  buộc, nhắc tự push và bàn giao `[ĐÃ SỬA XONG]` hoặc `[BỊ CHẶN]` kèm khối
  telegram-tomtat, câu chốt không merge, không deploy.
- Trước khi báo trạng thái PR, kiểm SHA nhánh trên GitHub và comment mới nhất
  của Codex. Không kết luận "chưa đẩy" hay "đã xong" khi chưa kiểm remote.
- Codex bàn giao một vòng sửa thì câu chốt là "không merge, không deploy, mời
  Claude rà".

Quyền deploy không bỏ cổng kiểm hoặc cho phép sửa chứng từ cũ/HĐĐT thật.
Xung đột phiên bản/patch đơn thuần: giữ đủ hai bên, tăng số và dựng bundle;
xung đột logic chưa rõ thì mô tả phương án, không âm thầm bỏ code.

**Đẩy code là một phần của hoàn thành (anh Việt chốt 12/10/2026).** Làm xong
bản sửa phải tự đẩy ngay lên nhánh GitHub của PR, không chờ ai nhắc; bàn giao
chỉ được tính khi SHA đã có trên GitHub. Codex cloud không có quyền đẩy không
được báo "đã xong": comment phải có dòng đầu `[BỊ CHẶN]` và khối
`telegram-tomtat` nói rõ "bản sửa nằm ở cloud, chưa lên GitHub". Codex local
thấy bản cloud chưa đẩy phải tự gom nguyên diff, kiểm và đẩy, không chờ anh Việt.

Trước phản hồi cuối mỗi phiên thực chất, cập nhật Markdown tại workspace
`/Users/jin/Documents/ChatGPT/ERP/nhat-ky-du-an/`, gồm mục lục, nhật ký phiên
và bài học. Đọc mẫu trong instruction. Không thêm database cho nhật ký.
Bàn giao file cho anh Việt bằng link mobile khi có thể, giữ bản local.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ CLAUDE.md dòng 1 tới 10. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Quy tắc dùng chung cập nhật 17/11/2026

Đọc [AGENTS.md](/AGENTS.md), mục 2b và 2c,
về giao diện, luồng nghiệp vụ và bằng chứng nghiệm thu;
[H10](/AGENTS.md#h10-trách-nhiệm-của-người-rà) về review và H3/H5/H8.1.
Đây là nguồn chung ưu tiên hướng dẫn cũ mâu thuẫn cùng chủ đề trong repo và
trong skill. Chỉ dẫn trực tiếp của anh Việt và instruction project do anh dán
luôn thắng; ai thấy hai nguồn mâu thuẫn thì ghi trong bàn giao để anh chốt
một nguồn. Instruction project quản lý công cụ và nơi ghi chép của phiên.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ CLAUDE.md dòng 35 tới 93. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Cửa vào chung từ 12/10/2026

Đọc [Instruction chung](/INSTRUCTION_VAGABOND.md) trước khi giao việc hoặc review.
Dùng cùng quy trình cloud/desktop, cùng SHA remote và mặc định Astra medium
cho Codex; không suy việc bot đã nhận là bản sửa đã lên GitHub.

## Quy tắc hiệu lực 16/09/2026

Đọc [quy tắc chung](/docs/van-hanh-agent/van-hanh-chung.md). Sáu thay đổi đã
được anh Việt duyệt; mục đó ưu tiên các luật cũ mâu thuẫn về model/tag/vòng.

## Quy tắc mới 14/09/2026: tiết kiệm token và gọi bot đúng việc

Đọc [quy tắc dùng chung](/docs/van-hanh-agent/tiet-kiem-token.md). Mục này thay
luật 13/09 yêu cầu mọi comment đều tag đối ứng: chỉ tag khi có yêu cầu hành
động. Review dùng `@claude review delta <FULL_HEAD_SHA>`, ghi SHA đã review,
base, phạm vi và bằng chứng. Nếu đạt thì chốt SHA không tag lại; có finding
cần sửa mới tag Codex. Không review trùng, không tự tạo lịch polling chờ sửa.
Giữ nguyên quyền, owner và cổng phát hành; đây chưa phải khóa chi phí bằng máy.

# CLAUDE.md

Hướng dẫn cho Claude khi chạy trong repo này, kể cả khi chạy trên GitHub Actions.
Tệp này chỉ giữ những luật hay bị quên nhất. Chi tiết nằm trong hai tệp bắt buộc
đọc dưới đây.

## ĐỌC BẮT BUỘC TRƯỚC DÒNG CODE ĐẦU TIÊN

Chạy đúng ba lệnh này trước khi sửa bất cứ tệp nào, kể cả khi thấy việc nhỏ:

```
cat AGENTS.md
cat docs/bai-hoc-su-co.md
ls docs/
```

- `AGENTS.md` là quy ước kỹ thuật của repo: cấu trúc app `/bep`, nguyên tắc thiết
  kế màn hình, quy ước viết code, các quy tắc nghiệp vụ đã chốt, bộ kiểm thử hai
  tầng, trình tự deploy, cách phối hợp với Codex. Không đọc nó là chắc chắn làm
  sai một quy ước nào đó.
- `docs/bai-hoc-su-co.md` là các sự cố ĐÃ XẢY RA THẬT và cách phòng. Mỗi mục là
  một lần mất code, mất email, hoặc một ca kiểm xanh mà lỗi vẫn lên production.
  Đọc để không lặp lại, vì mọi lỗi trong đó đều từng lọt qua cổng kiểm.
- `ls docs/` để thấy các tài liệu chuyên đề. Trước khi sửa một mảng nghiệp vụ,
  `grep -rl <từ khoá>  docs/ AGENTS.md` để xem mảng đó đã có ghi chép chưa.

Nhật ký làm việc đầy đủ theo từng phiên nằm ngoài repo, trong Claude Project
"Vận hành - Operation", nên bản chạy trên GitHub không đọc được. Những bài học
còn giá trị lâu dài đã được rút về `docs/bai-hoc-su-co.md`. Vì vậy: khi phát hiện
một cái bẫy mới mà hai tệp trên chưa ghi, THÊM một mục ngắn vào
`docs/bai-hoc-su-co.md` ngay trong PR đang làm. Đó là cách bản chạy trên GitHub
tích luỹ kinh nghiệm.

## Bối cảnh

The Vagabond Pâtisserie, tiệm bánh ở TP HCM. Repo này là app ERPNext v16 đang chạy
thật cho cửa hàng. Chủ repo là anh Việt. Hai agent cùng làm trên repo: Claude và
Codex (`@codex`). Ngôn ngữ làm việc là tiếng Việt.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ CLAUDE.md dòng 187 tới 206. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Claude là lead (anh Việt chốt 12/10/2026)

Codex viết code; Claude chốt hướng, giao việc và rà độc lập. Không viết code
chồng vào nhánh Codex đang làm. Rà xong một bản (đạt hay không đạt) thì TỰ
đăng ngay lệnh cho bước kế tiếp trên đúng PR, không đứng chờ anh Việt nhắc.
Anh Việt báo lỗi thì đọc dữ liệu thật trên site, khoanh nguyên nhân rồi giao
Codex trên PR đang mở cùng phạm vi. Chi tiết ở AGENTS.md mục 10b và
`tai_lieu/INSTRUCTION_VAGABOND.md` mục 1.

## Ba việc tuyệt đối không làm

1. KHÔNG merge Pull Request, KHÔNG deploy lên Frappe Cloud khi anh Việt chưa
   cho phép trong phiên, kể cả khi mọi cổng đều xanh. Anh đã cho phép cho
   đúng PR nào thì tự merge, deploy theo mục 7 AGENTS.md và kiểm site thật;
   quyền không suy ra cho PR khác.
2. KHÔNG đề xuất sửa hay xoá dữ liệu quá khứ đã ghi sổ, nhất là hoá đơn điện tử
   đã gửi cơ quan thuế. Phát hiện sai sót thì LIỆT KÊ ra, không tự sửa.
3. KHÔNG sửa Server Script trên Desk. Thứ đó nằm trong cơ sở dữ liệu, git không
   quản, mất là không khôi phục được.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ CLAUDE.md dòng 290 tới 296. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Quy ước trình bày

Không dùng dấu em dash hay en dash trong bất kỳ nội dung nào, chỉ dùng dấu gạch
ngang thường. Áp dụng cho mọi comment, mọi tệp soạn ra, mọi nội dung ghi vào
ERPNext.
