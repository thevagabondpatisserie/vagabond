# Issue #472: kiểm kê đếm 0

Owner: Codex. Nhánh `codex/472-kiem-ke-zero`, nền
`42cb9fb9a9310c2c7a03d9e2f19e26dd17dd0375`. PR riêng, ưu tiên trước #471.
Không sửa phiếu/tồn lịch sử; không merge hoặc deploy trong lượt này.

## Nguyên nhân và thay đổi

- `mo_phieu` che tồn bằng None khi đếm mù; `kkSave` ép thành 0 rồi gửi
  `frappe.client.save`. Hook trước validate nay giữ ảnh chụp cũ theo dòng/mã/kho;
  dòng mới lấy Bin ở máy chủ. Không lấy số tồn do trình duyệt tự gửi.
- `kkpSubmit` lọc số đếm/tồn dương làm mất dòng đã đếm 0. Nay gửi đủ dòng đã
  đếm, hộp xác nhận đếm rõ bao nhiêu món đặt về 0.
- Cửa `kiem_ke.ghi_so` kiểm quyền, khoá phiếu, lấy mã/kho/số đếm từ DB,
  insert/submit Stock Reconciliation và đóng phiếu trong một giao dịch.
  Gọi lại trả phiếu đã có. Lỗi đóng phiếu hoàn tác phần ghi sổ.
- Đối chiếu tồn do ERPNext quyết định ở posting_date/time. Core bench
  `de591661b9ba0bd3f62ac25b99b5c85c723515f6`,
  `erpnext/stock/doctype/stock_reconciliation/stock_reconciliation.py`,
  `remove_items_with_no_change`: gọi `get_stock_balance_for`, bỏ dòng không
  đổi, ném `EmptyStockReconciliationItemsError` khi không còn dòng.
  Chỉ bắt đúng exception này lúc insert: đóng phiếu không tạo PKK giả.
  Không nuốt lỗi submit hay dùng ảnh chụp cũ để lọc dòng.

## Kiểm và ranh giới

- Ca DOM thật chạy hàm app: lưu số 0, chốt chờ duyệt, mở ghi sổ, payload
  có qty 0; nhánh no-op có câu báo rõ. Ca giá vốn #401 vẫn giữ ngày giờ chung.
- Đột biến khôi phục bộ lọc cũ: 1/1 đột biến bị bắt, script exit 1;
  khôi phục bản sửa thì script exit 0. Đây là số đột biến, không phải tổng assertion.
- Ca khung: ảnh chụp server không bị payload null/0/999 ghi đè.
- Ba ca bench mới: số 0/SLE/GL/huỷ/retry; không đổi/không nháp sót;
  lỗi đóng phiếu/rollback/retry. Chờ kết quả CI, không nhận đã đạt từ mock.
- Chưa kiểm UI hoặc thay dữ liệu trên site thật. Các phiếu lịch sử nêu ở issue
  chỉ là báo cáo Claude, chưa đo lại trong lượt này; giữ nguyên.

## Phát hành

APPVER 593, đúng một dòng patch #v593 sau main 592. Vì #472 được ưu tiên
trước, PR #471 đang dùng 593 cần đồng bộ và đặt số mới trước tích hợp sau này.
Không gộp #471 vào PR này. SHA/check cuối ghi ở comment bàn giao trên PR.

## Bench vòng 1

Run 38392937139, SHA 703c7d3a6fce3298f356309cfee9ed10ff647e48:
399/402 đạt cả hai lượt, không chứng từ sót, không lệch tồn. Ba ca #472
đều lỗi dựng fixture `No module named frappe.core.doctype.phieu_kiem_ke`,
chưa tới logic ghi sổ. Bench nền chưa dựng hai DocType site-only; staging
trước đây chỉ dựng chúng sau bộ tích hợp. Đưa nguyên hai cấu trúc trong
`staging/cau_truc_cu.json` vào nen_bench trước migrate, giữ kiểm từng trường/
quyền khi staging tái dùng. Không đổi schema production, không bỏ ca đỏ.
