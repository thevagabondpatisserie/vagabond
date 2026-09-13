# Issue287 - khôi phục Telegram và bản tin bộ phận

Owner Codex, nhánh codex/287-khoi-phuc-telegram, nền dad6b224 (v489).
Anh Việt giao làm issue287 ngày14/09. Đặc tả5654964136, lưu ý Claude5654965612.

## Hiện trạng đã kiểm

Đã mở đúng pending legacy bằng PUT SHA giữcursor/seen, commit trạng thái
98181bf70bb9c4249ad66f9690b583cde9eb9556. Run34772786863 và34773104175 mỗi
lượt gửi30tin. Đã thấy entityrelease dad6b224 trongstate: bản tin489 đã có
biên nhận theo sender hiện hành. Pending giữa lượt đang chạy chưa phải lỗi.

## Sửa trong PR

- ghi_luc tách at sự kiện; chờ10phút, gửi lại tối đa1lần có nhãn. Lần2 vẫn
  mất phản hồi: giữcan_doi_chieu, cho tin khác đi tiếp, không nhận đã gửi.
- Log message_id và lưu receipt trước seen. RetryPUT chỉ cùngSHA; đọc đúng
  nội dung đãghi thì nhận thành công, xung đột không ghi đè.
- Kênh nhóm tùy chọn cócursor/pending/seen/entity riêng trongbo_phan. Chỉ
  release hợp lệ được gửi nhóm; không code/CI/linkGitHub. Nhóm mới từmốc bật.
- Ghép nhóm bằng mã do chính chủprivate đãghép gửi; artifactciphertext,
  không thêm quyền/lịch, không đổi secretprivate. Chưa có nhóm thật đểghép.

## Kiểm

59 ca Telegram (bao gồm mã hoá fixture), đều đạt. Ba đột biến đồnghồ,
receipt,lọc nhóm đều bị bắt. Bundle v489 khớp1495f56c, predeployrc0 trên
runtimePython/Nodebundled. KhôngsửaERP,khôngcầnbenchkếtoán/khochoPRnày.
Chờ CI và Claude review SHA trên PR; chưa merge bản sender mới, chưa bật nhóm.
