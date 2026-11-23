# Quy ước viết code và cách làm việc mong đợi

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 360 tới 376. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## 3. Quy ước viết code của repo này

- **Tên hàm, biến, tệp: tiếng Việt không dấu.** `chia_theo_lo`,
  `cau_thieu_lo`, `scrDonChungTuThu`. Không đặt tên tiếng Anh.
- **Chú thích và chuỗi hiện ra màn hình: tiếng Việt có dấu.** Chú thích
  phải nói **VÌ SAO**, không nói lại cái code đã nói. Đầu mỗi tệp mới là
  một đoạn kể lại sự cố hoặc nhu cầu đã sinh ra tệp đó.
- **Tách phần thuần và phần cần Frappe.** Đặt các hàm không đụng cơ sở dữ
  liệu lên đầu tệp, dưới tiêu đề `# phần thuần`, rồi mới `import frappe`.
  Bộ kiểm thử tầng khung chạy được phần thuần mà không cần site.
- **Tiền tố cho mỗi màn.** Kiểm và chạm tên trước khi đặt tiền tố mới, để
  không đụng tên hàm của phần khác.
- **Không dùng dấu em dash hay en dash** trong bất kỳ nội dung nào, kể cả
  chú thích và chuỗi hiển thị. Chỉ dùng dấu gạch ngang thường.

---

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 618 tới 630. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## 8. Cách làm việc mong đợi

Đọc trước khi sửa. Sửa nhỏ, sửa đúng chỗ gốc thay vì vá ở ba nơi. Khi hai
đường cùng chạy được thì chọn đường mà sáu tháng nữa đọc lại vẫn hiểu.

Không đoán. Số liệu thật đọc được từ site thì đi đọc, đừng ước lượng. Một
câu "khoảng chừng" trong repo này là một lần đối chiếu kho sai.

Không im lặng nuốt lỗi. Nuốt lỗi là cách hệ này mất 26 đơn mua hàng hồi
16/08 mà không ai biết cho tới khi Uyên đi hỏi.

---

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ CLAUDE.md dòng 257 tới 275. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Cách viết code trong repo này

- Tách phép THUẦN (không chạm Frappe) khỏi phần chạm hệ, để kiểm thử được không
  cần site.
- Mọi tính năng mới phải có ca kiểm trong `vagabond/khung/kiem_thu/` và đăng ký
  trong `chay.py`.
- Thêm hàm có `@frappe.whitelist()` thì PHẢI thêm tên vào
  `vagabond/khung/kiem_thu/thu_cua_ngo.py`. Quên là hàm cũ mất quyền gọi mà không
  có lớp nào báo.
- Hook đặt trên `"*"` là cực kỳ nguy hiểm, nó áp lên mọi doctype kể cả hạ tầng
  Frappe. Ngày 16/08/2026 một hook như vậy làm cả tiệm không gửi được email suốt
  bốn ngày.
- `APPVER` trong `vagabond/public/js/bep/12-van-don.js` chỉ được TĂNG. Đọc
  `origin/main` ngay trước khi đặt số.
- `vagabond/patches.txt` phải thêm dòng mới mỗi lần phát hành, giữ nguyên mọi
  dòng cũ của phiên khác.
- `app_bep.js` là tệp máy ghép ra từ `vagabond/public/js/bep/`. Nguồn sự thật là
  thư mục `bep/`.
