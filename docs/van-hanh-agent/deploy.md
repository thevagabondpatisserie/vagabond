# Deploy, sổ tay phát hành, email sau phát hành

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 587 tới 617. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## 7. Deploy

Chỉ anh Việt hoặc phiên đang trực tiếp làm mới được bấm deploy. Không bao
giờ để trợ lý tự động bấm.

Frappe Cloud, bench `bench-44405`, site `erpnext-qwy-acq.s.frappe.cloud`,
app thật ở `https://app.thevagabondpatisserie.com/bep`.

Trình tự: Apps, dấu "...", **Fetch Latest Updates trước**, rồi Update
Available, chỉ tích app Vagabond, Next, **phải tích cả site** ở bước Select
sites to update (có tích thì migrate mới chạy), Deploy and update site.
Chờ khoảng năm phút.

Deploy xong **phải kiểm trên site thật**, không chỉ tin trạng thái Success:
Patch Log đã có số phiên bản mới chưa, và bấm thử đúng cái màn vừa sửa.
Trạng thái Success không nói được rằng màn hình bấm được.

**Mỗi bản deploy phải kèm hướng dẫn trong sổ tay** (anh Việt chốt 08/11/2026).
Sổ tay đã từng đứng ở v631 trong khi app lên v644: nhân viên hỏi trợ lý về
OnePay, gọi món tại bàn, Biên tập menu thì trợ lý không biết. Trong CÙNG PR:

1. Thêm hoặc sửa mục trong `vagabond/so_tay/<chương>.md` theo khuôn
   `vagabond/so_tay/_quy-uoc.md` (bảng Ai dùng, nút `[[...]]` đúng chữ trên app).
2. Ghi bản vào `vagabond/so_tay/_phien-ban.md`: mục `## vNNN` liệt kê đúng tên
   các mục vừa thêm hoặc sửa. Bản chỉ sửa lỗi ngầm thì ghi một dòng
   `- Không đổi thao tác: <lý do>`.
3. Ca `thu_so_tay_phien_ban_645` chặn bàn giao khi APPVER chưa có mục ở đó.
4. Bản tin `[ĐÃ DEPLOY]` nêu tên mục sổ tay để nhân viên mở đọc.

---

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ CLAUDE.md dòng 220 tới 227. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Mỗi bản deploy kèm sổ tay (anh Việt chốt 08/11/2026)

Bản nào lên site cũng phải có hướng dẫn trong sổ tay của app, ngay trong PR đó:
mục mới hoặc sửa trong `vagabond/so_tay/`, và tên mục ghi dưới `## vNNN` của
`vagabond/so_tay/_phien-ban.md` (bản sửa lỗi ngầm: một dòng
`- Không đổi thao tác: <lý do>`). Ca `thu_so_tay_phien_ban_645` chặn bàn giao
nếu thiếu. Chi tiết ở AGENTS.md mục 7.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 728 tới 737. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## 11. Email sau phát hành (anh Việt yêu cầu 09/09/2026)

Sau mỗi deploy thành công và kiểm site thật, tự áp dụng skill
[Email phát hành](/.agents/skills/vagabond-email-phat-hanh/SKILL.md): soạn email
ngắn, xưng hệ thống, dùng branding chung, chọn đúng nhân sự liên quan.
Mặc định nháp; gửi theo quyền anh Việt đã cấp, không suy ra quyền gửi từ quyền
deploy. Lưu bằng chứng gửi để không lặp. Khi sửa template phải kiểm mobile
không tràn ngang và desktop; không nhận browser preview là kiểm Outlook thật.
