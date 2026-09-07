# #227: rà lịch sử và nguyên nhân lỗi quay lại

Ngày 08/09/2026. Đã lập chỉ mục toàn văn 543 Markdown anh Việt cung cấp,
đọc sâu nhóm mua hàng, HĐĐT, trứng, BOM và các sự cố lặp. Không coi mọi
khẳng định trong tài liệu là hiện trạng đã được xác minh. Kho nguyên bản
và công cụ tra cứu giữ trong workspace, không đưa dữ liệu nội bộ lên PR.

## Quả và PCS: đã xác minh trên site

- `v301-trung-sang-qua-va-huong-dan-che-bien.md` và
  `v309-sua-cong-thuc-trung-va-doi-dvt.md` ghi đổi đơn vị dòng BOM sang Quả,
  giữ đơn vị kho PCS. v309 ghi 98 dòng BOM đang dùng đã đổi; đó là số lịch sử,
  chưa kiểm lại toàn bộ BOM hiện nay. Phiếu kho/hoá đơn cũ không được đổi.
- Đọc Item NVLT00041 trực tiếp ngày 07/09: stock_uom PCS, Quả = 1, PCS = 1.
  Gram hiện 0,017 trên màn hình có làm tròn, không lấy số hiển thị đó để sửa hệ số.
- Màn đối chiếu HDM-26-08-00186: hoá đơn số 94 có 2.400 Quả; ba phiếu
  PNK-2026-00147, PNK-2026-00131, PNK-2026-00173 cộng 2.400 PCS.
  Chính màn hình xác nhận cùng lượng kho. Không có bằng chứng cần khai lại
  đơn vị cho ca này. Không đổi PCS toàn hệ thống, không sửa chứng từ cũ.
- PR thêm ca chạy `_noi` với Quả/PCS và hệ số 1: đủ ba phiếu, giữ lượng
  2.400 và tiền 5.520.000. Đây là test biên DB giả, không phải lần ghi sổ thật.

## Đã sửa trong PR: dấu hoá đơn điều chỉnh giảm

Tài liệu `v350-nan-dau-hoa-don-am-va-don-mon-nuoc.md` mô tả chuẩn hoá dấu
ở lần nhập đầu. Nhưng `_dung_dong_tai_cho`, `ghim_lai_theo_goc`,
`du_kien_tong` chưa truyền dấu cả tờ vào cùng hàm dựng dòng.

Tái hiện nguồn qty=-2, rate=-100, amount=-200: đường dựng lại trước sửa
ra tiền dòng +200 rồi giảm 400 để tổng vẫn -200. Tổng đúng che cấu trúc sai.
Ngoài ra, thay đổi của Codex tại e6a4f33 dùng `-abs` cho mọi chiết khấu đã
làm tờ trả -200, giảm 20 thành -220 thay vì -180. Đây là hồi quy của PR,
không quy trách nhiệm cho tác giả tài liệu.

Đã truyền dấu trên cả ba đường, cân cùng chiều với tổng nguồn, giữ đơn giá
dương, lượng/giảm đúng dấu. Chuẩn hoá trước cửa tổng khớp để ca qty=2,
rate=-100 không thoát sớm. Thêm test lưu/dựng lặp và test tích hợp PI trả
với GL VAT đảo chiều. Ca tích hợp mới chưa chạy: cần bench của Claude.
Core đối chiếu: ERPNext de59166 `controllers/sales_and_purchase_return.py`,
`validate_return` chỉ kiểm returned items khi có return_against; không dựa
vào core để tự phát hiện mọi sai dấu trên phiếu độc lập.

## Lỗi khác đã xác nhận, chưa sửa trong PR này

1. **Đối chiếu nhiều giá hiển thị gây hiểu nhầm.** `doi_chieu_mua.so_sanh`
   cộng lượng mọi dòng PR nhưng lấy rate của dòng đầu. Trên ca trứng,
   màn hiện 2.400 PCS x 2.300 trong khi tổng PR là 5.460.000, lệch HĐ
   60.000. Cần hiển thị từng phiếu/đơn giá hoặc ghi rõ giá bình quân;
   đồng thời phân bổ dòng đối chiếu để không tính trọn lượng PR lặp lại
   cho từng dòng PI đã chia. Chưa kết luận nguyên nhân chênh 60.000 trên
   từng chứng từ vì chưa đọc hết từng dòng PR.
2. **Công cụ đổi BOM báo lại dòng đã đổi.** `doi_dvt_bom.can_doi` so uom
   với stock_uom. Quả khác PCS nên vẫn trả True, dù Quả chính là đích muốn
   chuyển. Tài liệu Sable đã ghi triệu chứng này. Sửa điều kiện theo đơn
   vị đích và hệ số, có test chạy lại không đề nghị đổi; không chạy lại
   migration trên BOM để chữa một lỗi của công cụ báo cáo.
3. **Công cụ phiên bản trái mô tả giữ lịch sử.** `dat_phien_ban.dat_patch`
   lọc bỏ các dòng `dong_bo_cau_truc #v...` cũ, trong khi docstring nói
   giữ nguyên mọi dòng patch cũ. Không phải mọi loại patch đều bị xoá.
   Cần thống nhất chính sách giữ lịch sử, sửa helper và test bằng tệp tạm;
   không chạy helper trên patches.txt thật trước khi sửa.

## Điều lịch sử cần kiểm thêm, chưa coi là lỗi hiện tại

- Tài liệu Sable chốt sau cùng 60 g/quả, thay các giả định 50/63 trước đó;
  từng có BOM cũ còn active và một draft PCS bị scanner chỉ nhìn Gram bỏ sót.
  Cần kiểm BOM active/default và Work Order hiện tại trước khi sửa dữ liệu.
- v350 ghi đã gỡ ánh xạ nước sai nhưng còn phiếu nháp chưa dựng lại; v417
  học lại mã người chọn và giữ mã cũ khi dựng. Cần thử xem mã sai còn trên
  nháp có được học lại hay không. Hiện mới là nghi vấn, chưa tái hiện.
- Tài liệu 43 Client Script ngoài Git chỉ là kiểm kê lịch sử. Cần snapshot
  hiện tại để biết hook/script nào còn chồng lên cùng trường.

## Cách tránh lặp ở PR sau

- Tra lịch sử theo mã hàng, lỗi, doctype; ghi quyết định cuối cùng và bằng
  chứng hôm nay. Không dùng số test xanh hoặc câu “đã deploy” cũ thay log mới.
- Một quy tắc chuyển dữ liệu phải dùng chung ở nhập đầu, dựng lại, lưu Desk,
  nối phiếu và submit. Test cả thao tác lặp; tổng đúng chưa đủ, phải chốt
  lượng kho, hệ số, giá, giảm, thuế và liên kết chứng từ.
- Case v318/v319/v322 cho thấy giá mặc định/thuế có thể nạp lại sau hook.
  Chạy hết lifecycle Frappe rồi đọc lại DB/GL, không chỉ kiểm object trước save.
- Fixture giả chứng minh phép tính; bench chứng minh core chấp nhận. Ghi rõ
  cả hai kết quả. Test async phải await và phải đỏ trên bản lỗi.
- Người dùng giữ luồng đơn giản; không thêm thao tác “kế hoạch chi”. Kho
  sản xuất chưa sẵn sàng, Kiểm bánh vẫn là theo dõi thực tế theo quyết định
  hiện tại. Không lấy SOP cũ để tự bật trừ kho hay sửa hàng loạt danh mục.
