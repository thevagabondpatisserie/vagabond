# Issue225: PKT hàng tặng cũ và bảo vệ HĐĐT

Nền main17ec12f/v450 đã deploy theo Claude/anh Việt. Codex code, Claude
review/bench/merge/deploy. Không triển khai lại450. PR này không sửa PR231.

## Chốt nghiệp vụ và số lẻ còn cần duyệt

Chị Dung chốt VAT64182; PKT mới Nợ5111 9.648.148, Nợ64182 771.852,
Có131 10.420.000. Dòng Có131 phải có Customer đúng khách HDB và
reference_type Sales Invoice, reference_name HDB-26-09-00710.

Theo bằng chứng5580723960, GL SI thực Có5111 9.648.148,14,
Có33311 771.851,85, Có6428 0,01. Chỉ ba dòng tròn sẽ để lại doanh thu0,14
và6428 0,01. Đề xuất riêng CHỜ chị Dung duyệt: bổ sung vào PKT thay thế
Nợ5111 0,14; Nợ6428 0,01; Có33311 0,15. Sau đủ sáu dòng, gộp SI vàPKT
chỉ còn Nợ64182 771.852 / Có33311 771.852. Không sửa tiền trên SI/HĐĐT.
Hàm thay mặc định từ chối khi chưa xác nhận riêng ba dòng lẻ.

Không đổi tk_chi_phi_qua_tang64181 thành64182: chi phí quà chung và VAT
là hai khoản khác nhau. hang_tang_so_cai hiện đã chọn64182 cho VAT.
Giá vốn vẫn thiếu, không tự tạo SLE hoặc ghi Có155 khi kho chưa có bằng chứng.

## Nguyên nhân và cách sửa liên kết

Dòng PKT cũ đã mất reference sau Unreconcile nên Có131 chưa tất toán HDB.
Không suy từ ghi chú chữ rằng Payment Ledger đã liên kết.

Báo cáo API liên kết trước huỷ không chứng minh Unreconcile chặn cancel:
ERPNext de59166 journal_entry.py on_cancel đặt Unreconcile Payment và
Unreconcile Payment Entries trong ignore_linked_doctypes; Document chạy
on_cancel trước check_no_back_links_exist. Không cần huỷ Unreconcile.
Link HDB.vgb_but_toan_tang tới PKT cũ là liên kết do app cần cập nhật.

Công cụ doi_chieu_tang_cu chỉ xử cặp00710/00012 qua các cửa công khai trong
module (không whitelist). ban_xem chỉ đọc, trả GL/PLE/link/số dư và hash.
Hàm thay cần hash đúng ảnh hiện tại, duyệt số lẻ, quyền kế toán trưởng,
khóa SI/JE. Kiểm GL đúng bằng chứng, công nợ đủ, không phân bổ mới, không
có kho. Trong một savepoint: gỡ đúng Link SI, core cancel PKT, insert/submit
PKT amended_from cũ, Có131 reference đúngSI, nối SI tớiPKT mới, kiểm còn nợ0.
Mọi lỗi rollback toàn bộ; không commit bên trong; không ignore_links,
không huỷ SI/Unreconcile, không sửa4 tờ khác. Retry sau thành công dừng để
đối chiếu thay vì sinh bù. Caller chịu commit sau khi kiểm lại kết quả.

## Bảo vệ HĐĐT

Sales Invoice.before_cancel kiểm dấu HĐĐT từ DB bằng locking read; payload
xoá dấu rồi cancel vẫn bị chặn. before_save và before_update_after_submit
chặn huỷ mềm và xoá toàn bộ dấu qua save. Giữ hook chống trùng Pancake.
Đường danh_dau_huy dùng db.set_value gọi cùng guard trước ghi. Xem trước
huỷ hàng loạt cũng dùng tiêu chí này, kể cả Chờ ký/ID/chờ đối chiếu.
Không bảo vệ khỏi SQL quản trị trực tiếp, không tuyên bố đã có cơ chế huỷ
HĐĐT thay thế; cần quy trình chuyên biệt khi có nhu cầu đó.

## Claude review và nghiệm thu

- Chạy gate/CI đúng SHA cuối; code sản xuất231 không nằm trongPR này.
- Bench đúng core site: hai ca bao_ve_hddt225; SI chưa có HĐĐT vẫn cancel;
  SI có dấu giả trên chứng từ thử không cancel hoặc huỷ mềm, GL không đổi.
- Thử thay PKT bằng chứng từ MỚI trong savepoint, không dùng mã chứng từ
  thật trên bench có dữ liệu vận hành. Kiểm Unreconcile còn nguyên,
  PKT cũ cancelled, amended_from, Link hai chiều, PLE phân bổ đúngSI,
  outstanding0; GL cuối chỉ64182/33311, không SLE.
- Gây lỗi sau cancel và sau submit mới: rollback giữ Link/PKT/GL/PLE ban đầu;
  hai phiên cùng sửa; hash cũ bị chặn; retry không thêm phiếu.
- Chưa chạy bench tại máy Codex. Không thực hiện dữ liệu cũ chỉ vì CI xanh.
- Chị Dung duyệt ba dòng lẻ trước thực hiện. Chạy ban_xem trên site đọc
  lại, đối chiếu mã băm rồi mới dùng thay. Bench execute có thể commit ở
  caller; phải xem rõ giao dịch/lệnh hoàn chỉnh trước chạy, không thử trên site.
- Đọc riêng bốn SI còn lại, không nhân bút toán00710 sang cả nhóm.

## Kiểm tại Codex

Gate RC0,2634 ca tầng khung đạt; bundle khớp nguồn, không đổi JS hoặcAPPVER.
Đã thêm4 ca tích hợp: huỷ thật có dấu CQT, huỷ mềm cóID, dựng cặp lịch sử
rồi Unreconcile/thay PKT, gây lỗi saucancel để kiểmrollback. Chưa chạy bench.
Factory chỉ giả bản đồGL lịch sử trên SI thử mới; cancel/submit/PLE dùng lõi.
Review chéo phát hiện và đã sửa keyhook trùng, lockingread và hậu kiểmGL
thực để precision không âm thầm nuốt0,14/0,15/0,01. Snapshot gồmPLE đi/đến,
có sort ổn định. kiem_nam_to chỉ đọcGL từng tờ, không nhân bút toán cố định.

Bản này chưa chốt số release; Claude phối hợp vớiPR231 khi phát hành, số
phải lớn hơn450, giữ toàn bộpatch đã có. Không lấyAPPVER450 làm deploy mới.

Cập nhật trước push: main đã lên83d6aba (mergePR231/v451). Đã merge nền
mới vào nhánh này, giữ đầy đủ sản xuất/patch451; gate chạy lại RC0,2644ca
đạt. Bản release củaPR225 phải lớn hơn451 nếu không có bản khác chen vào.
Review chéo cuối không còn blocker đọc code để mởDraft; bench và duyệt
ba dòng lẻ vẫn là điều kiện trước xử lý chứng từ thật.
