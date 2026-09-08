# Issue225: PKT hàng tặng cũ và bảo vệ HĐĐT

Nền main17ec12f/v450 đã deploy theo Claude/anh Việt. Codex code, Claude
review/bench/merge/deploy. Không triển khai lại450. PR này không sửa PR231.

## Chốt nghiệp vụ mới nhất của chị Dung

Một PKT thay thế gồm đúng năm dòng, không tạo phiếu riêng cho số lẻ:

| Tài khoản | Nợ | Có |
|---|---:|---:|
| 5111 | 9.648.148,14 | 0 |
| 64182 | 771.852 | 0 |
| 6428 | 0,01 | 0 |
| 131 | 0 | 10.420.000 |
| 33311 | 0 | 0,15 |
| Tổng | 10.420.000,15 | 10.420.000,15 |

Đã được anh Việt chuyển xác nhận của chị Dung; KHÔNG chờ duyệt lại phần
số lẻ. Dòng Có131 có Customer đúng khách, reference_type Sales Invoice,
reference_name HDB-26-09-00710. Sau đảo đủ PKT cũ, gộp SI vàPKT mới chỉ
còn Nợ64182 771.852 / Có33311 771.852; 5111/6428/131 về0. Giữ nguyên SI
và HĐĐT12165. Bản xem trước và mã băm dùng đúng năm dòng này.

Không đổi tk_chi_phi_qua_tang64181 thành64182: chi phí quà chung và VAT
khác nhau. hang_tang_so_cai đã chọn64182 cho VAT. Giá vốn vẫn cần chứng
từ kho thật, PR này không tự tạo SLE hoặc ghi Có155.

## Yêu cầu làm tròn Sales Invoice cho lần sau, đưa vào review

Chị Dung mô tả gốc số lẻ: tính thuế từng dòng rồi ép tổng qua6428; đề nghị
Sales Invoice VND làm tròn đến đồng để khớp M-Invoice. Ghi nhận yêu cầu,
CHƯA đổi cài đặt toàn hệ trongPR này.

Bằng chứng code: hang_tang_so_cai.chia_thue hiện phân bổ gross và làm tròn
số trước thuế/VAT theo đồng, kiem_thue_gui so từng dòng/tổng với payload.
Đây là đường hàng tặng MỚI; năm tờ cũ có vgb_tang_so_cai=0 không qua nó.

Không chỉ tắt hai số lẻ trong System Settings/Currency: Frappe
model/meta.py get_field_precision dùng currency_precision/định dạng tiền
cho Currency fields; JournalEntry cũng gọi d.precision khi tính Nợ/Có.
Đổi toàn hệ có thể làm mất0,01/0,15 trong chính phiếu sửa. Chỉ đổi hiển thị
cũng không chứng minh số GL hoặc payload đã đổi đúng. Không làm tròn đơn
giá nguyên liệu/quy đổi hay ép mọi hoá đơn mua về một mức thuế.

Claude kiểm chỉ đọc precision thực của Sales Invoice/Item/Taxes, Journal
Entry Account, Currency VND, System Settings và Property Setter. Trên
bench so dòng/tổng SI -> GL -> payload M-Invoice với đơn nhiều dòng,
chiết khấu, giá đã gồm VAT, thuế8/10 riêng. Chốt cách làm tròn ở đúng
luồng SI với cùng quy tắc phân bổ của M-Invoice, giữ tổng từng dòng bằng
tổng đầu phiếu. Nếu còn lệch ở luồng mới, trả fixture và đường mã để Codex
sửa tiếp trước nghiệm thu phần này; không coi thayPKT cũ đã hoàn tất yêu
cầu làm tròn SI nói chung.

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
- Chị Dung đã duyệt năm dòng gồm số lẻ. Chạy ban_xem trên site đọc
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
Review chéo trước không còn blocker đọc code để mởDraft; vẫn cần bench
trước xử lý chứng từ thật. Xác nhận năm dòng mới thay yêu cầu chờ duyệt số lẻ.
