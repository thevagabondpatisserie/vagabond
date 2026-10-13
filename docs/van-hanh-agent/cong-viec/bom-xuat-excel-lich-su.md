# Công thức (BOM): xuất Excel trên app, lịch sử chỉnh sửa, sổ tay

Anh Việt giao ngày 13/10/2026. Claude lead và rà, Codex viết code trên nhánh này.
Nền: main `42cb9fb9a` (APPVER 592).

## Yêu cầu của anh Việt

1. Khải xuất được BOM ra Excel. Khải là kế toán kiêm quản lý sản xuất.
2. Làm nút Xuất Excel ngay trên app.
3. Đưa hướng dẫn vào sổ tay. Câu thật Khải hỏi trợ lý: "hướng dẫn tôi xuất file BOM ra excel", trợ lý trả lời "chưa có tài liệu".
4. Linh (bếp) và Khải cùng nhập BOM, nên cần thấy lịch sử: ai sửa công thức nào, sửa cái gì, lúc nào, để truy cứu.

## Số liệu thật (đọc trên site 13/10, chỉ đọc)

**Quyền.**
- Khải (`khai.lam193@gmail.com`) có các vai: Accounts Manager, Accounts User, Manufacturing User, Stock Manager, Stock User, Item Manager, `VGB - Quản lý công thức`, Kiểm kê viên, Mua hàng R&D, Bộ phận đặt hàng.
- Linh (`lethilinh051996@gmail.com`) có các vai: Manufacturing Manager, Manufacturing User, Bếp phó, Kiểm kê viên, Mua hàng R&D, Bộ phận đặt hàng.

**BOM chưa vai nào có quyền Export**, kể cả Manufacturing Manager; chỉ System Manager xuất được. BOM không có Custom DocPerm nào. Không tạo Custom DocPerm cho BOM, vì Custom DocPerm thay toàn bộ quyền chuẩn của doctype.

**Lịch sử.**
- Doctype BOM đã bật `track_changes`, site có 615 bản ghi Version của BOM. Lịch sử từ trước đọc được ngay, không cần chạy lại gì.
- Version có nhiễu: mỗi lần lưu, bảng `exploded_items` (BOM Explosion Item) bị dựng lại, nên hiện ra như thêm dòng mới.
- Ngày 12 và 13/10 Khải sửa liên tục trên các BOM đã ghi sổ (ví dụ BOM-BTPB00023-002, BOM-BTPB00080-002).

**Đường ghi KHÔNG sinh Version** (đi bằng `db.set_value`):
- `cong_thuc.ghi_so` đổi mặc định/hoạt động của bản cũ và bản mới;
- `don_bep.py` dòng 198 và 318 đến 321;
- `doi_dvt_bom.py` dòng 453;
- `ton_chang.py` dòng 538;
- `bo_ao.py` dòng 221.

## Việc cần làm, theo thứ tự

### 1. Xuất Excel công thức trên app (màn Danh mục công thức)

**Nút "Xuất Excel" trên danh sách.**
- Xuất đúng các công thức đang lọc: tab, trạng thái, ô tìm, chặng. Mặc định chỉ bản đang dùng.
- Mỗi dòng Excel là một dòng nguyên liệu, gồm các cột:
  - món: mã món, tên món;
  - công thức: mã BOM, trạng thái (Nháp, Đang dùng, Bản cũ, Đã huỷ), số lượng ra, đơn vị;
  - nguyên liệu: mã NVL, tên NVL, số lượng, đơn vị, đơn giá, thành tiền;
  - giá vốn: tổng giá vốn công thức, giá vốn một đơn vị;
  - người: người tạo, người sửa cuối, ngày sửa cuối.
- Đầu tệp có một dòng ghi bộ lọc, giờ xuất và người xuất.

**Nút "Xuất Excel" trong chi tiết một công thức.** Cùng các cột trên, chỉ công thức đó.

**Quyền.**
- Kiểm ở máy chủ: chỉ vai trong `cong_thuc._vai_ghi_so()` được xuất (Manufacturing Manager, System Manager, Giám đốc, AP Giám đốc, VGB - Quản lý công thức). Khải và Linh đều nằm trong bộ này.
- Người khác không thấy nút. Gọi thẳng API thì bị chặn với câu báo tiếng Việt.
- Không đổi DocPerm trên Desk.

**Cách làm.**
- Dùng lại `frappe.utils.xlsxutils.make_xlsx` như `bao_cao.xuat_excel`.
- Số là ô số; mã giữ dạng chữ.
- Thêm hàm whitelisted mới vào `thu_cua_ngo.py`.

### 2. Lịch sử chỉnh sửa công thức (dùng lõi, không thêm DocType)

**Nguồn dữ liệu:**
- Version của BOM;
- owner và creation;
- chuỗi bản trước qua `custom_ban_truoc`;
- Comment cho các đường không sinh Version;
- Deleted Document khi bỏ bản nháp.

**Dịch Version thành câu tiếng Việt.** Ví dụ:
- "Thêm Whipping cream Lescure 600 ML"
- "Đổi Đường 120 thành 150 G"
- "Bỏ ..."
- "Đổi số lượng ra 1 thành 2"
- "Ghi sổ, thay bản BOM-...-001"
- "Huỷ"

Bỏ `exploded_items` và các trường hệ thống tự tính khỏi câu hiển thị.

**Hai chỗ xem.**
- **Trong chi tiết công thức:** mục "Lịch sử chỉnh sửa", mới nhất trước. Mỗi dòng: giờ, tên đầy đủ người sửa, các câu thay đổi. Xem được cả chuỗi bản trước.
- **Màn mới "Nhật ký sửa công thức":** lọc theo người, món, khoảng ngày (mặc định 7 ngày). Bấm vào dòng nào thì mở đúng công thức đó. Thêm chỗ đặt trên sidebar desktop.

**Quyền xem lịch sử:** cùng bộ vai được xem công thức (`_vai_xem`).

**Các đường `db.set_value` kể ở trên.**
- `cong_thuc.ghi_so`: ghi thêm Comment trên BOM mới và bản cũ.
- Đường nào còn lại không ghi được lịch sử thì liệt kê thật trong bàn giao. Không giả là đã có.

### 3. Sổ tay

Thêm hai mục vào `vagabond/so_tay/san-xuat.md`, viết theo `_quy-uoc.md`:
- **"Xuất công thức (BOM) ra Excel".** Từ khoá: xuất BOM, xuất excel công thức, tải BOM, export BOM, định mức ra excel, file BOM.
- **"Xem ai đã sửa công thức".** Từ khoá: lịch sử BOM, ai sửa BOM, nhật ký công thức, truy vết, sửa công thức lúc nào.

## Ca kiểm bắt buộc

1. **Quyền theo người thật.**
   - Bộ vai của Khải và của Linh (như trên) xuất được.
   - Bếp phó, Quầy Bar, Stock User gọi thẳng API bị chặn.
   - Nút ẩn với người không quyền: ca hành vi trong node, dùng `gia_lap_trang.js` hoặc bộ DOM giả sẵn có.
2. **Excel.**
   - Số dòng bằng tổng dòng nguyên liệu của đúng tập đang lọc; bộ lọc trạng thái đổi thì số dòng đổi theo.
   - Ô số là số; mã giữ chữ; có dòng bộ lọc ở đầu.
3. **Lịch sử.**
   - Dùng một Version có hình dạng như site: có `added` dòng `exploded_items` cộng `changed` số lượng một dòng `items`.
   - Kết quả phải ra đúng câu tiếng Việt và không có dòng nào từ `exploded_items`.
   - Ghi sổ qua `cong_thuc.ghi_so` có dòng lịch sử.
4. **Trợ lý.** Câu "hướng dẫn tôi xuất file BOM ra excel" tìm ra đúng mục sổ tay mới.
5. **Đột biến** theo điều 17, báo đúng số bắt được.

## Ràng buộc

- Không sửa hay xoá dữ liệu BOM cũ.
- Không hook trên "*".
- Không Custom DocPerm cho BOM.
- Không dấu em dash hay en dash.
- APPVER chỉ tăng: hiện main là 592. Đọc main và các nhánh mở ngay trước khi đặt số.
- Thêm dòng patch cuối `patches.txt`, giữ các dòng cũ. Dựng lại `app_bep.js` từ `bep/`.
- Theo INSTRUCTION_VAGABOND: tự đẩy lên nhánh này, đọc lại SHA remote, bàn giao bằng `[ĐÃ SỬA XONG]` hoặc `[BỊ CHẶN]` kèm khối telegram-tomtat và `@claude review <SHA>`.
- Không merge, không deploy.


## Bàn giao desktop 13/10/2026, chưa hoàn tất việc 4

- Owner Codex, nhánh `codex/bom-xuat-excel-lich-su`, nền `bf7d2716c` trên main `42cb9fb9a`.
- Đã lấy lại nguyên diff cloud từ task `task_e_6acddc9cdb68832e8c7a333b10a212b8` bằng `codex cloud diff`. Không tuyên bố có object commit cloud trong lịch sử nhánh. Bỏ riêng thay đổi phiên bản/patch theo lệnh mới nhất của anh Việt; bundle dựng lại.
- BOM: Excel có cả lọc hướng dẫn và không cắt 1200 công thức khi xuất; bù Comment qua `lich_su_bom.dat_bom` cho bốn mô đun ghi trực tiếp; đọc Deleted Document của BOM bằng snapshot, không gọi lại BOM đã xoá. Đường màn hình đăng ký ở `duong_app.py`, không sửa bảng JS sinh tay.
- Core Frappe `f33ac3f00ab818e21b25ddbec93efb653fd9aa1b`: `version.get_diff` ghi row_changed bằng `(fieldname, index, child.name, changed)`; `delete_doc.add_to_deleted_document` lưu `doc.as_json()`. Mock đã sửa đúng hình dạng; qty đổi vẫn lấy được tên/UOM của dòng còn tồn tại. Dòng không còn metadata hiện mã dòng, không đoán tên.
- 15 nhóm kiểm BOM, DOM 0/1/nhiều/tải/lỗi/bản xoá. Fixture Chrome dùng CSS thật ở 390x844: 10 trạng thái không tràn ngang. Đây là fixture, không phải UAT site thật. Năm đột biến BOM đều bị bắt, mỗi lần một nhóm đỏ.
- Việc 4 mới có `khop_sao_ke.xet_bo` thuần và 4 nhóm kiểm: số thật Adecco do Claude cung cấp, lỗi từng dòng, phân bổ theo phần còn, số không hữu hạn. Ba đột biến bộ tiền bị bắt, mỗi lần một nhóm đỏ. CHƯA gắn vào bất kỳ cửa ghi thật nào; không nhận các ca này là đủ 10 ca yêu cầu.
- Core ERPNext `de591661b9ba0bd3f62ac25b99b5c85c723515f6`, `BankTransaction.allocate_payment_entries`: phần phân bổ lấy `min(allocable_amount, remaining_amount)`. Chưa có bench chứng minh PE phân bổ qua hai BT ở SHA này.
- Chưa làm xong việc 4: lưu bộ chọn và chỗ giữ theo số tiền; khoá đồng thời ở mọi luồng; các callback APP/TTNB/hoàn tiền/công nợ; UI chọn nhiều; đường Accounts Manager ghi kèm lý do; bỏ cả bộ; sổ tay và 10 nhóm kiểm/bench. Không ghép JSON vào Data 140 ký tự rồi coi là đã lưu đủ. Không nới `_chu_khac` trước khi cửa giữ chỗ chung đã hoàn chỉnh.
- Ca cũ APP.26.09.009 chỉ là thông tin Claude cung cấp, chưa sửa dữ liệu.
- Lệnh mới nhất của anh Việt ưu tiên: KHÔNG đặt số phiên bản, KHÔNG thêm patch, giữ APPVER592 trên riêng nhánh này; chưa gom v594, không merge/deploy.

- Cổng local trên cây code cuối: tầng khung 4463/4463; CI chặn requests 4463/4463; `dung_app_bep.py --kiem` khớp; `kiem_truoc_deploy.sh` exit 0 với Node24 và PYTHONPYCACHEPREFIX tạm. Hai ca nén PDF #247 không chạy do máy thiếu pypdf, không tính vào số đạt. Lượt shell đầu thiếu cache prefix dừng ở compileall, đã chạy lại đủ cổng. Chưa có bench/CI GitHub của SHA #469 mới lúc ghi bàn giao.
