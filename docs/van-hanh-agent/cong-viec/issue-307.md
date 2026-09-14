# Issue 307: BTP hạch toán 1552 theo ô Chặng, giữ một kho

- Nguồn: issue #307 (con của #206), anh Việt duyệt 13/09/2026 sau trao đổi
  với Khải. Điều phối lại 14/09/2026 11:45: chia hai PR.
- Owner tích hợp/sửa: Codex local (anh Việt giao 14/09); Claude review. Nhánh `claude/issue-307-20260914-0450`, nền main
  `6886899d` (sau v491). PR A là bản này; PR B (hai báo cáo, bench) làm sau.
- Mục tiêu PR A: hai ô cấu hình, hook validate Item, patch nạp một lần,
  ca thuần, APPVER 492. Không đổi cờ thật, không đụng chứng từ, không nới
  `gac_tk_kho.py`.
- Bổ sung 14/09/2026 chiều (anh Việt chốt trên PR #316): lưới đỡ theo
  nhóm món, ô điền tay trên hồ sơ món, báo cáo cổng bật cờ, ca kiểm.

## Bằng chứng lõi (anh Việt đối chiếu trực tiếp de591661, 14/09/2026)

- `erpnext/controllers/stock_controller.py:248-250`: cờ trên Company, ô
  `enable_item_wise_inventory_account`.
- `stock_controller.py:258-270` `get_inventory_account_dict`: cờ bật thì
  lấy theo món, không có thì throw "Please set default inventory account
  for item {0}, or their item group or brand." KHÔNG quay về kho.
- `stock_controller.py:2528-2571`: ba nấc Item Default, Item Group
  Default, Brand; ô tên `default_inventory_account` (khớp
  `TRUONG_ITEM_DEFAULT`).
- `erpnext/setup/doctype/item_group/item_group.py:87-97`: chỉ đọc đúng
  nhóm trên hồ sơ, KHÔNG leo nhóm cha. Vì vậy lưới đỡ gán cho từng nhóm lá.

## Lưới đỡ theo nhóm món: bảng dự kiến CHỜ ĐỌC TỪ SITE

Phiên GitHub Actions không đọc được site nên chưa liệt kê được tên nhóm
lá và tài khoản thật; KHÔNG suy từ trí nhớ. `vagabond/luoi_do_nhom.py`
chỉ ghim ba chữ nhóm gốc (Mua vào, Bán ra, Sản xuất), nhánh con bắt đầu
bằng "Bán thành phẩm", và ba số hiệu 152, 1551, ô BTP cấp 1. Người có
bench (Codex local hoặc anh Việt) chạy lệnh CHỈ ĐỌC sau rồi dán bảng lên
PR #316 để anh Việt và Khải duyệt TRƯỚC khi merge:

```
bench --site erpnext-qwy-acq.s.frappe.cloud execute vagabond.luoi_do_nhom.xem_bang
```

Bảng có cột: nhóm lá, số món theo tồn, gốc, nhánh, tài khoản đang có,
hành động (gan/giu/bo_qua), tài khoản dự kiến, lý do. Patch
`luoi_do_nhom_307` chỉ ghi đúng các dòng `gan` của bảng này; nhóm có tài
khoản khai tay thì `giu`; số hiệu không có đúng một tài khoản chi tiết còn
dùng thì `bo_qua` kèm lý do, không đoán. Nhóm không có món theo tồn (đang
dùng) thì không xuất hiện.

Nếu bảng đọc từ site cho thấy tên nhóm gốc khác ba chữ trên (ví dụ có dấu
khác hoặc gọi tên khác), sửa ba hằng `GOC_*` trong `luoi_do_nhom.py` rồi
chạy lại lệnh, không sửa dữ liệu tay.

## Ô điền tay trên hồ sơ món

Ô `custom_tk_ton_kho_tay` "Tài khoản tồn kho (điền tay)" (Link Account)
ngay dưới ô Chặng, là GƯƠNG của ô `default_inventory_account` trên dòng
Item Default của công ty; cột đó cũng hiện trong lưới Item Default với
cùng nhãn (Property Setter, dựng lại mỗi migrate qua `tai_khoan_btp.dung`).
Luật ưu tiên khi lưu món (phép thuần `doc_o_tay`, `quyet_dinh`,
`gia_tri_cuoi`):

1. Người đổi ô gương so với bản trong DB: ý người thắng dòng Item Default,
   kể cả xoá trắng để bỏ tài khoản riêng. Áp cho MỌI món, không chỉ BTP.
2. Chặng đổi: máy ghi đè theo chặng mới và ghi comment trên món.
3. Chặng không đổi: tôn trọng giá trị điền tay.
4. Xoá chặng: chỉ xoá khi giá trị đang có đúng bằng giá trị máy điền cho
   chặng cũ; khác đi (hoặc cấu hình trống nên máy chưa từng điền) thì giữ.

## Báo cáo cổng bật cờ

Script Report "Mon theo ton chua co tai khoan" (tên không dấu vì Frappe lấy
tên làm thư mục mô đun; cột và câu chữ có dấu), vai Accounts, Stock
Manager, System Manager. Liệt kê món `is_stock_item=1` đang dùng mà cả
ba nấc món, nhóm (đúng nhóm lá), nhãn hiệu đều trống, kèm nhóm và tồn hiện
tại từ Bin. Bước tay bắt buộc ngày cắt: kế toán chỉ bật cờ khi báo cáo
này RỖNG.

## Bản chốt nghiệp vụ

Giữ MỘT kho. Ô "Chặng bán thành phẩm" trên hồ sơ món quyết tài khoản tồn
kho ghi vào Item Default của công ty:

| Ô Chặng | Điều kiện | Tài khoản |
|---|---|---|
| BTP sơ cấp (cấp 1) | is_stock_item=1, mã BTPB/BTPN/NBTP | ô "Tài khoản tồn kho BTP cấp 1" |
| BTP sẵn sàng (cấp 2) | như trên | ô "Tài khoản tồn kho BTP cấp 2" |
| BTP thành phần, trống | không áp | theo kho như cũ |

Đổi chặng: máy ghi đè và ghi chú vào comment món. Chặng không đổi mà kế
toán đã khai tay khác: giữ. Xoá chặng: xoá tài khoản khai riêng. Hai ô
cấu hình trống: chỉ nhắc màu vàng, không chặn lưu. Khải chốt 1552 chung
hay tách 15521/15522 thì chỉ đổi hai ô, không đổi code.

## Đoạn nguồn lõi đã đối chiếu và phần CHƯA đối chiếu được

Đã có trong repo (vagabond/hang_tang_kho.py:27-31, ERPNext de591661,
erpnext/controllers/stock_controller.py):

```
get_inventory_account_map: if self.use_item_inventory_account:
    return self.get_item_wise_inventory_account_map()
return get_warehouse_account_map(self.company)
```

Cờ đọc trên site 08/09/2026 (tai_lieu/issue-206-tai-khoan-chi-phi.md:10-11):
Company Vagabond `enable_item_wise_inventory_account=0`, tức cờ nằm trên
Company.

Hai điểm chưa đối chiếu ở phiên sáng 14/09 đã được anh Việt đối chiếu
trực tiếp (mục Bằng chứng lõi ở trên): tên ô đúng là
`default_inventory_account`, và lõi KHÔNG fallback theo kho khi cờ bật.
Hook vẫn kiểm meta trước khi ghi và patch vẫn dừng migrate nếu ô không có,
làm hàng rào cho lần nâng lõi sau.

## Kết quả có bằng chứng

- `vagabond/tai_khoan_btp.py`: phần thuần `chang_ap_dung`, `quyet_dinh`,
  `loi_tai_khoan`, `chon_mac_dinh`; phần Frappe `ap_dung`, `khi_luu_mon`,
  `kiem_o_cau_hinh`.
- Vagabond Settings: mục "Tài khoản tồn kho bán thành phẩm theo món" với
  hai ô Link Account, validate lọc Stock, chi tiết, còn dùng, VND.
- hooks.py: thêm `vagabond.tai_khoan_btp.khi_luu_mon` vào Item validate.
- Patch `vagabond.patches.tai_khoan_btp_307`: trỏ mặc định 1552 nếu site có
  đúng một tài khoản con 1552 còn dùng; nạp cho món theo tồn đã khai chặng;
  ghi thẳng Item Default, không save() Item để không kích validate khác trên
  dữ liệu cũ. `patches.txt` thêm dòng patch và `dong_bo_cau_truc #v492`.
- Ca thuần `thu_tai_khoan_btp_307.py` (12 ca) và `thu_luoi_do_nhom_307.py`
  (7 ca), đăng ký trong `chay.py`: chọn tài khoản theo nhóm gốc, nhóm không
  leo cha, giữ khai tay trên nhóm và trên món, báo cáo rỗng và không rỗng,
  idempotent.
- `vagabond/luoi_do_nhom.py` (phần thuần + `xem_bang`, `ap_dung`), patch
  `vagabond.patches.luoi_do_nhom_307`, báo cáo
  `vagabond/vagabond/report/mon_theo_ton_chua_co_tai_khoan/`.
- Cổng kiểm: phiên Actions chiều 14/09 không được phép chạy python3, nên
  bằng chứng là CI của PR trên SHA cuối; ghi trong comment PR.

## Các bước tay của kế toán ngày cắt (đề nghị 01/10/2026)

1. Khải điền cấp 1 hoặc cấp 2 cho từng mã BTP theo tồn (báo cáo "BTP theo
   tồn chưa khai chặng" ở PR B); lưu món là hook tự ghi tài khoản. Món cần
   tài khoản riêng khác luật thì điền ô "Tài khoản tồn kho (điền tay)".
2. Mở báo cáo "Mon theo ton chua co tai khoan": phải RỖNG. Còn dòng thì
   khai ở món (ô điền tay) hoặc ở nhóm lá (Item Group Default) rồi mở lại.
3. Chị Dung chốt "Số dư BTP tại ngày cắt" (PR B) và lập bút toán kết chuyển
   từ tài khoản kho cũ sang 1552 đúng ngày; máy không tự sinh bút toán.
4. Trên Company Vagabond bật `enable_item_wise_inventory_account` đúng ngày
   cắt, sau khi số dư đã chốt và báo cáo bước 2 rỗng. Không đưa vào patch.
5. Kiểm một lệnh sản xuất thật ra BTP có Nợ 1552, và một phiếu nhập NVL có
   Nợ 152 theo nhóm; không đạt thì tắt cờ và báo trên issue.

## Còn lại và bàn giao

- Chờ Khải: 1552 chung hay tách 15521/15522 (chỉ đổi hai ô).
- Chờ chị Dung: ngày cắt.
- Chờ người có bench: chạy `vagabond.luoi_do_nhom.xem_bang` trên site, dán
  bảng lên PR #316 cho anh Việt và Khải duyệt trước khi merge; nếu tên nhóm
  gốc khác ba chữ đã ghim thì sửa hằng `GOC_*` rồi chạy lại.
- PR B: hai Script Report cho Khải và chị Dung, toàn bộ ca bench mục 6 của
  đặc tả, thêm ca "món chỉ có tài khoản ở nhóm" ghi sổ đúng khi cờ bật;
  chạy hai lượt `chung_tu_con_sot=[]`, `so_luong_lech={}`.
- Chưa cập nhật nhật ký local trên máy anh Việt (phiên cloud).

## Codex tiếp quản sau 1c8f8871 (14/09)

- Sửa validator: lấy công ty mặc định độc lập với Account; hai ô cấu hình phải cùng công ty đó. Patch tìm 1552 cũng lọc đúng công ty.
- Ca hồi quy gọi kiem_o_cau_hinh thật với DB giả, không chỉ gọi loi_tai_khoan. Chứng minh Account Demo bị chặn và Account đúng công ty được nhận.
- Đã đo chỉ đọc site và đăng comment5662316882. 22 nhóm có món theo tồn (gồm cả disabled); cần đo lại đúng filter disabled=0 của báo cáo trước duyệt mapping. Nhánh Mua vào có công cụ, tài sản, dịch vụ; không duyệt gán tất cả152. Còn nhóm Demo và ngoài cây. Phép đọc Account loại Stock chưa thấy1552.
- Khải tự phân loại món. Chưa bật cờ, chưa sửa Account hoặc Item live.
- Chưa sẵn sàng merge: còn kiểm mapping/manual account/report và bench GL trên SHA cuối. Không dùng báo cáo rỗng làm đủ bằng chứng tài khoản hợp lệ hay cho phép bật cờ.

## Delta đang làm theo comment5663898833

Đã sửa bảng 152/153, Nhân bán thành phẩm và bỏ qua Demo; Item hook thiếu công ty mặc định chỉ nhắc. Còn hook lưu Settings, đổi món dịch vụ/tài sản chưa có SLE và bench GL hai lượt; chưa đủ cổng merge. Phiên bản cuối493 sau PR318v492.

Bổ sung local: lưu Settings nạp lại nhóm BTP và món đã chọn chặng, dùng cấu hình vừa lưu. Patch chỉ bỏ theo tồn của tài sản/dịch vụ chưa có SLE; báo cáo cổng giữ các món đã có SLE cho Khải. Đã nối ba ca GL thật (món/nhóm/cờ tắt); hai ca phantom một/nhiều cấp hiện hữu tiếp tục chạy trong bench. Chưa có kết quả bench SHA mới.

## Bảng đã đọc trực tiếp site ngày14/09/2026

Nguồn Console chỉ đọc Item Group, Item (is_stock_item=1, gồm cả mã disabled), Account và Item Default. Chưa áp dữ liệu. Tài khoản1552 chưa có trên site; không tự tạo. Khải phân loại món sau.

| Nhóm lá/nhánh | Món theo tồn | Tài khoản dự kiến hoặc xử lý |
|---|---:|---|
| Nguyên vật liệu Thô | 370 | 152 |
| Bao bì | 45 | 152 |
| Công cụ Dụng cụ | 263 | 153 |
| Văn phòng phẩm | 24 | 153 |
| Tài sản Cố định | 13 | Không gán; chỉ bỏ tồn nếu chưa từng có SLE |
| Dịch vụ | 1 | Không gán; chỉ bỏ tồn nếu chưa từng có SLE |
| Bán thành phẩm Bánh | 12 | tk_ton_btp_cap1; trống thì bỏ qua và nhắc |
| Bán thành phẩm Nước | 26 | tk_ton_btp_cap1; trống thì bỏ qua và nhắc |
| Nhân bán thành phẩm | 64 | tk_ton_btp_cap1; trống thì bỏ qua và nhắc |
| Bánh khô | 19 | 1551 |
| Bánh lạnh | 50 | 1551 |
| Bánh nướng | 47 | 1551 |
| Bánh ổ sinh nhật | 106 | 1551 |
| Bánh Wholesale | 19 | 1551 |
| Hộp bánh theo mùa | 20 | 1551 |
| Phụ kiện cho bánh | 5 | 1551 |
| Topping cho món bánh | 6 | 1551 |
| Khuyến mãi dạng Combo | 10 | 1551 theo nhánh Bán ra đã duyệt |
| Khoá học Sonneto | 1 | 1551 theo nhánh Bán ra đã duyệt |
| Thành phẩm dưới Sản xuất | 0 | 1551 khi có nhóm/món phù hợp |
| Chưa phân loại | 1 | Không gán |
| Uncategory | 1 | Không gán |
| Demo Item Group | 10 | Không gán |

Tổng nhánh Bán ra đang theo tồn:283. Các nhóm còn lại không có món theo tồn trong phép đo. Công ty chính có152,153,1551 hợp lệ; cả hai công ty đang tắt enable_item_wise_inventory_account. Các dòng mặc định nhóm đã đọc đang trống tài khoản tồn kho. Số món này là ảnh chụp khi đo, không dùng để ghi đè dữ liệu lúc migrate; patch đọc lại site và giữ tài khoản khai tay.

Bench721c782 dừng khi cài app: Single mới coi ô trống là đổi, on_update đòi công ty trước khi setup xong. Đây là lỗi hook đã sửa bằng bỏ qua khi cả hai tài khoản đều trống, có ca tái hiện. Chưa tới GL, không báo GL đỏ hoặc xanh cho lượt này.

## Lượt nền 14/09 20:39

Bench48ffd469 chạy219ca,217đạt/2đỏ ở cảhai lượt, rollback sạch. Ca nhóm đã ghi/huỷGL đạt; hai ca món riêng/cờ tắt chưa tới GL vì fixture thêm Item Default trùng công ty. Đã sửa dùng dòng do Item.insert tạo, không thêm trùng. Lõi item.py validate_item_defaults chặn nhiều dòng cùng công ty. ChờbenchSHA mới; không sửa production.
