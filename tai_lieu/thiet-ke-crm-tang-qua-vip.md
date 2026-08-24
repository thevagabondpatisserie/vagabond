# Đặc tả thiết kế: phân hệ CRM và luồng "Tặng quà khách VIP"

Bản chốt thiết kế, chưa viết code. Anh Việt duyệt xong mới dựng.

Nguồn dữ liệu thật đã đọc: bảng tính của chị Loan Anh, 5 sheet, 347 dòng.
Nguồn code đã soi: `zalo.py`, `viec_can_lam.py`, `giao_viec.py`, `diem_han.py`,
`lib.py`, `hop_qua.py`, `khach_hang.py`, `02-trang-chu.js`, và
`erpnext/selling/doctype/customer/customer.json` nhánh version-16.

---

## 0. Bốn quyết định nền, ĐANG CHỜ ANH VIỆT XÁC NHẬN

Trong đề bài, bốn ô quyết định vẫn còn nguyên chữ mẫu
`[Điền quyết định của anh, VD: ...]`, chưa được điền. Em KHÔNG dừng lại chờ,
mà tạm lấy đúng bốn phương án ví dụ làm giả định để thiết kế chạy tiếp. Anh
đọc lại và sửa nếu khác ý:

| # | Câu hỏi | Giả định đang dùng | Chỗ nó chạm vào thiết kế |
|---|---|---|---|
| 1 | Gán người phụ trách cho khách lẻ | Để trống, việc vô chủ dồn về Sales Manager | Mục 2.3, trường `khach_cua`; mục 5 bước 3 |
| 2 | Cảnh báo dị ứng | Chờ bếp khai xong danh mục, chưa làm | Không dựng ô dị ứng trong đợt này, xem mục 8 |
| 3 | Lead và Opportunity | Chỉ bật Lead, không dùng Opportunity | Không đụng tới trong đợt này, xem mục 8 |
| 4 | Ngưỡng Sales tự quyết đền bù | Dưới 500.000đ tự quyết, trên thì xin duyệt | Không thuộc luồng tặng quà, xem mục 8 |

Chỉ có quyết định 1 thực sự ảnh hưởng tới luồng tặng quà. Ba cái còn lại nằm
ngoài phạm vi đợt này và em ghi lại ở mục 8 để không rơi.

---

## 1. Thiết kế đọc ra từ dữ liệu thật, không đọc ra từ đề bài

Bốn điều bảng tính nói mà đề bài không nói, và cả bốn đều đổi thiết kế:

**1.1. "Khách của ai" và "Phụ trách" là HAI cột khác nhau, không phải một.**
Cột "Khách của" chỉ có ba giá trị: Chị Thảo, Anh Việt, Anh Felix. Đó là người
GIỮ QUAN HỆ. Cột "Phụ trách" chỉ có hai giá trị: Sales, Marketing. Đó là bộ
phận ĐI LÀM. Gộp hai cột thành một trường là mất hẳn một chiều thông tin, và
lúc chia việc thì máy không biết bắn cho ai.

**1.2. Hai trục trạng thái đã tách nhau sẵn trong dữ liệu.** Dòng "Nam Le"
có Process = "Đã Liên Hệ" đồng thời Status = "Đã tặng". Dòng "Anh Quân" có
Process = "Đã Liên Hệ", ghi chú "hẹn lại sau Tết", Status vẫn trống. Hai
trục này chạy độc lập thật, không phải hai bước nối tiếp của một trục.

**1.3. Lời chúc có luật xưng hô theo phân loại khách.** Ô NOTE trong sheet
Tết Bính Ngọ ghi nguyên văn:

> Nhóm nghệ sỹ cú pháp ghi thay chữ Anh/Chị bằng chữ Nghệ sỹ.
> Nhóm hoa hậu cú pháp ghi thay chữ Anh/Chị bằng chữ Hoa Hậu/Á Hậu/Nam Vương.
> Các nhóm khác cú pháp sẽ tuỳ theo title (Đạo diễn, Nhà Thiết Kế, Doanh nhân).

Nghĩa là biến trong mẫu lời chúc KHÔNG chỉ có tên khách. Phải có thêm biến
xưng hô, và xưng hô suy ra từ phân loại chứ không gõ tay từng dòng.

**1.4. Phân loại khách là danh mục SỐNG, không phải hằng số trong code.**
Giá trị thật đang có: Nghệ sĩ, Nhóm Hoa Hậu, Influencer, Nhóm Kinh Doanh,
Cigar & Bar. Riêng "Cigar & Bar" chỉ mới xuất hiện ở mùa Trung thu 2026, tức
là danh mục này còn đẻ tiếp. Viết cứng vào một ô Select là mỗi mùa lại phải
deploy một lần.

---

## 2. Schema

### 2.1. Vì sao KHÔNG nhét danh sách khách vào một bảng con

Đề bài gợi ý một DocType `Vagabond Tang Qua VIP` quản lý cả chiến dịch. Nếu
làm đúng như vậy thì danh sách khách phải là bảng con của nó. Nhưng yêu cầu
"cho phép chọn nhiều món quà trong cùng một lần tặng" lại đòi mỗi khách có
bảng quà riêng, tức là bảng con nằm trong bảng con.

**Frappe không cho bảng con chứa bảng con.** Đây là chặn cứng của khung, không
lách được. Cộng thêm hai lý do nghiệp vụ:

- ToDo của Frappe trỏ vào một chứng từ thật qua `reference_name`. Dòng bảng
  con không phải chứng từ, nên không giao việc đích danh cho nó được. Mà "tự
  động chia việc" chính là yêu cầu số 3 của anh.
- Một dòng trong bảng tính là một việc có vòng đời riêng: liên hệ, hẹn giờ,
  giao, xác nhận. Nó là chứng từ chứ không phải một ô dữ liệu.

Nên tách làm ba tầng, cộng hai danh mục:

```
Vagabond Dot Tang Qua          (đợt: Tết Bính Ngọ 2026, Trung thu 2026...)
    |
    +-- Vagabond Tang Qua VIP  (MỘT phiếu = MỘT khách nhận quà)
            |
            +-- Vagabond Tang Qua VIP Mon   (bảng con: các món trong lần tặng)

Vagabond Nhom Khach VIP        (danh mục phân loại: Nghệ sĩ, Nhóm Hoa Hậu...)
Vagabond Mau Loi Chuc          (danh mục mẫu lời chúc có biến)
```

### 2.2. Vagabond Dot Tang Qua

Đợt tặng. Mỗi mùa một bản ghi. Đây là chỗ chốt số lượng và ngân sách, thay
cho bảng "CHỐT SỐ LƯỢNG THEO LOẠI BÁNH" đang tự tính trong sheet.

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `ma_dot` | Data, autoname, read only | `TQ-2026-TET`, `TQ-2026-TRUNGTHU` |
| `ten_dot` | Data, bắt buộc | `Tặng bánh Trung thu 2026 - khách VIP` |
| `dip` | Link -> Vagabond Nhom Dip | Tết, Trung thu, Giáng sinh, Sinh nhật, Khác |
| `nam` | Int | |
| `trang_thai_dot` | Select | `Nháp` / `Đang chạy` / `Đã đóng` |
| `mau_loi_chuc_md` | Link -> Vagabond Mau Loi Chuc | Mẫu mặc định cho cả đợt |
| `ngan_sach` | Currency | Để 0 là không đặt trần |
| `tu_ngay`, `den_ngay` | Date | Khung ngày giao của đợt |
| `ghi_chu` | Small Text | |
| `nguoi_tao` | Link -> User, read only | |

Không cất số liệu tổng hợp vào đây. Tổng số hộp, số khách đã tặng đều tính
lại từ các phiếu con lúc mở màn, theo QT-19 máy chủ chốt số.

### 2.3. Vagabond Tang Qua VIP

Phiếu tặng cho một khách. Đây là DocType chính, một dòng bảng tính là một
bản ghi ở đây.

**Khối nhận diện khách**

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `dot` | Link -> Vagabond Dot Tang Qua, bắt buộc | |
| `khach` | Link -> Customer | KHÔNG bắt buộc, lý do ngay dưới bảng |
| `ten_khach` | Data, bắt buộc | Tên hiện trên thiệp và trên vận đơn |
| `phan_loai` | Link -> Vagabond Nhom Khach VIP, bắt buộc | Ô chọn theo QT-31 |
| `title_rieng` | Data | `Đạo diễn`, `Nhà Thiết Kế`... đè lên xưng hô mặc định |
| `don_vi` | Data | `ELLE Tạp Chí`, `Manki Coffee`, `Leica` |

`khach` để trống được, và đây là chỗ dễ làm sai nhất. Trong dữ liệu thật,
phần lớn người nhận CHƯA phải khách trong hệ: nhạc sĩ Nguyễn Văn Chung, Hồ
Ngọc Hà, Soobin Hoàng Sơn đều không có mã Customer. Bắt buộc `khach` là ép
Sales đẻ ra hàng chục Customer rác chỉ để gửi được một hộp bánh, và rác đó
sẽ chui vào báo cáo hạng khách của `khach_hang.py`.

Đổi lại, khi `khach` CÓ điền thì máy kéo về `account_manager` và số điện
thoại đã sạch của khách đó, khỏi gõ lại.

**Khối người phụ trách**

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `khach_cua` | Link -> User | Người giữ quan hệ. `fetch_from: khach.account_manager`, cho sửa đè |
| `bo_phan_lam` | Select, bắt buộc | `Sales` / `Marketing` |
| `nguoi_lam` | Link -> User | Người cụ thể đi làm. Để trống thì giao cả nhóm |

`Customer.account_manager` là trường có sẵn của ERPNext, kiểu Link tới User,
đã đối chiếu trong `erpnext/selling/doctype/customer/customer.json` nhánh
version-16 dòng 187 tới 191. Không cần tự đẻ trường mới.

Theo quyết định 1 ở mục 0: `khach_cua` để trống được. Phiếu vô chủ thì màn
Việc cần làm dồn về nhóm Sales Manager, xem mục 5.

**Khối liên hệ, phần khó nhất**

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `sdt_tho` | Data | NGUYÊN VĂN ô người ta gõ, giữ lại không đụng vào |
| `sdt` | Data, read only | Số đã bóc sạch, dạng `0xxxxxxxxx`. Máy ghi, người không sửa |
| `sdt_loai` | Select, read only | `Di động` / `Cố định` / `Không đọc được` |
| `nguoi_nghe_may` | Data, read only | `Na (Trợ Lý)`, `chị Linh quản gia` |
| `chinh_chu` | Check, read only | 0 nghĩa là số của trợ lý, quản gia, bảo vệ |
| `canh_bao_sdt` | Small Text, read only | Câu nói rõ vì sao chưa dùng được số này |
| `dia_chi` | Small Text | |
| `gio_giao` | Data | `T4 13/12 trước 16g`, giữ dạng chữ vì thực tế người ta ghi vậy |

Bốn trường read only đều do hàm bóc số sinh ra, mô tả ở mục 4.

**Khối quà và lời chúc**

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `mon` | Table -> Vagabond Tang Qua VIP Mon, bắt buộc | Danh sách quà |
| `mau_loi_chuc` | Link -> Vagabond Mau Loi Chuc | Mặc định lấy từ đợt |
| `loi_chuc` | Text, read only | Máy dựng từ mẫu, hiện ra để đọc lại |
| `loi_chuc_sua_tay` | Text | Chỉ điền khi cần khác mẫu. Có điền thì cái này thắng |

Vì sao `loi_chuc` read only và tách riêng ô sửa tay: yêu cầu của anh là lời
chúc dạng mẫu, không gõ tay 100%. Nhưng dữ liệu thật có ca "Nghệ sĩ Hồ Ngọc
Hà 3 hộp, cô Hương, cô Thuỷ, chị HNH" với ghi chú "Viết 3 thiệp khác nhau".
Bịt hẳn đường sửa tay là Sales quay lại dùng Excel. Nên mở một ô riêng, và
nhìn vào phiếu là biết ngay dòng nào đi theo mẫu, dòng nào đã bẻ.

**Khối hai trục trạng thái**

| Trường | Kiểu | Mặc định |
|---|---|---|
| `tt_tang` | Select: `Chưa tặng` / `Đã tặng` | `Chưa tặng` |
| `ngay_tang` | Date | |
| `tt_lien_he` | Select: `Chưa liên hệ` / `Đã liên hệ` | `Chưa liên hệ` |
| `ngay_lien_he` | Datetime, read only | Máy đóng dấu lúc đổi trạng thái |
| `huy` | Check | Huỷ mềm theo QT-20, không xoá bản ghi |
| `ly_do_huy` | Small Text | |
| `ghi_chu` | Small Text | |

Hai trục hoàn toàn không ràng buộc nhau. Không có luật kiểu "phải liên hệ
xong mới được tặng", vì dữ liệu thật đã có dòng tặng rồi mà chưa từng liên
hệ, và ngược lại.

`huy` là ô riêng chứ không thêm giá trị vào `tt_tang`, để hai trục trạng thái
giữ đúng hai giá trị anh chốt, và để số liệu "đã tặng bao nhiêu" không bị một
trạng thái thứ ba làm loãng.

**Còn hỏi anh Việt:** dữ liệu thật có hai tình huống chưa có chỗ đứng, là
"Đã chuyển D1" (hộp đã chuyển sang chi nhánh Quận 1 chờ khách ghé lấy) và
"Jin đã tặng" (người khác tặng hộ). Em ĐANG ép cả hai về `Đã tặng` và để
người nhập ghi rõ trong ghi chú. Anh muốn tách hẳn thành trạng thái riêng
thì báo, vì đổi sau khi đã nhập vài trăm dòng thì phải rà lại từng dòng.

### 2.4. Vagabond Tang Qua VIP Mon (bảng con)

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `mon` | Link -> Item, bắt buộc, in_list_view | Ô chọn theo QT-31 |
| `ten_mon` | Data, read only, fetch_from `mon.item_name` | |
| `so_luong` | Int, mặc định 1, in_list_view | |
| `don_vi` | Data, read only | |
| `gia_von` | Currency, read only | Máy tính lại ở máy chủ, dùng để cộng ngân sách đợt |
| `ghi_chu_mon` | Data | `Làm cờ gắn lên bánh luôn khi giao` |

Món là Link tới Item chứ không phải ô gõ. Trong bảng tính hiện có bốn cách
viết cho cùng một thứ: "Hộp bánh Floral Serpent 2025", "2026", "2027",
"2028", trong đó ba cái sau là gõ nhầm khi kéo chuột xuống. Ô gõ tự do là
đúng cái đẻ ra chuyện đó.

Bảng này KHÔNG ghi sổ kho và không sinh bút toán trong đợt này. Xuất kho quà
tặng đi đường riêng, xem mục 8.

### 2.5. Vagabond Nhom Khach VIP (danh mục phân loại)

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `ten_nhom` | Data, autoname, unique | `Nghệ sĩ`, `Nhóm Hoa Hậu`, `Cigar & Bar` |
| `xung_ho` | Data, bắt buộc | Chữ thay cho `Anh/Chị` trong lời chúc |
| `xung_ho_phu` | Data | `Á Hậu`, `Nam Vương` cho nhóm hoa hậu |
| `uu_tien` | Int | Thứ tự hiện trên app |
| `con_dung` | Check, mặc định 1 | Tắt thay cho xoá, theo QT-20 |

Nạp sẵn đúng năm nhóm đang có thật trong bảng tính, cộng "Khách sỉ" và
"Khách VIP mua nhiều" đọc ra từ hai sheet cũ. Marketing thêm nhóm mới ngay
trên app, không cần deploy.

### 2.6. Vagabond Mau Loi Chuc (danh mục mẫu)

| Trường | Kiểu | Ghi chú |
|---|---|---|
| `ma_mau` | Data, autoname | `LC-TET-2026` |
| `ten_mau` | Data | |
| `dip` | Link -> Vagabond Nhom Dip | Lọc mẫu theo dịp lúc chọn |
| `noi_dung` | Text, bắt buộc | Có biến, xem ngay dưới |
| `con_dung` | Check, mặc định 1 | |

Biến cho phép, đúng bốn cái, không nhiều hơn:

- `{xung_ho}` lấy từ `title_rieng` của phiếu, không có thì lấy `xung_ho` của
  nhóm, vẫn không có thì rơi về `Anh/Chị`.
- `{ten_khach}` lấy từ `ten_khach`.
- `{don_vi}` lấy từ `don_vi`, trống thì cả cụm chứa biến bị bỏ đi cả câu.
- `{nam}` lấy từ `dot.nam`.

Mẫu Tết Bính Ngọ chép nguyên từ bảng tính, thành:

```
CUNG CHÚC TÂN XUÂN

Mến gửi {xung_ho} {ten_khach},

Chút phong vị ngọt lành cho ngày khởi xuân Bính Ngọ {nam}.
Cầu chúc {xung_ho} cùng gia đình một năm mới An Nhiên - Tự Tại - Cát Tường.
Mong những khoảnh khắc sum vầy thêm phần thi vị!

Tâm ý,
The Vagabond Patisserie
```

Hàm dựng lời chúc là hàm THUẦN, đặt trên `import frappe` trong tệp
`tang_qua.py`, để bộ kiểm thử tầng khung chạy được mà không cần site.

---

## 3. Giao diện trên app

Không dựng React. App `/bep` nằm trong một vỏ hàm, màn hình là các hàm `scr`
gọi `frame(tiêu_đề, html, tuỳ_chọn)` và điều hướng bằng `go(hàm)`. Phần mới
đi vào một tệp `vagabond/public/js/bep/32-crm-tang-qua.js`, số nhỏ hơn 99,
rồi chạy `python3 dung_app_bep.py` để ghép lại. Không sửa tay `app_bep.js`.

### 3.1. Ô lớn mới trên trang chủ

Thêm một phân hệ `CRM` vào `VGB_NHOM` trong `02-trang-chu.js`, đứng ngay sau
`Bán hàng`:

```
{ k: 'CRM', ten: 'CRM khách VIP', icon: '💝', keys: ['TQV', 'DMNKV', 'DMLC'] }
```

Ba ô bên trong:

| Ô | Nhãn | Phụ đề |
|---|---|---|
| `TQV` | Tặng quà khách VIP | Lên danh sách, chia việc, theo dõi đã tặng và đã liên hệ |
| `DMNKV` | Nhóm khách VIP | Nghệ sĩ, hoa hậu, influencer, đối tác. Thêm nhóm mới |
| `DMLC` | Mẫu lời chúc | Soạn mẫu có biến tên khách, dùng lại mỗi mùa |

Ô `TQV` mang phù hiệu đếm số phiếu chưa liên hệ, cùng cách các ô khác đang
làm. Con số đó nhìn vào là biết còn bao nhiêu người chưa ai gọi.

Ô CRM chỉ hiện với Sales, Marketing, quản lý và giám đốc. Chặn thật nằm ở
máy chủ, giao diện chỉ ẩn cho đỡ rối.

### 3.2. Bốn màn hình

```
scrTqvDot        Danh sách đợt tặng
   -> scrTqvDs       Danh sách khách trong một đợt   (màn xương sống)
        -> scrTqvSua     Form một phiếu
        -> scrTqvNhanh   Thêm nhanh nhiều khách
```

**scrTqvDot.** Thẻ mỗi đợt: tên, dịp, khung ngày, và ba con số đã tặng trên
tổng, đã liên hệ trên tổng, tổng số hộp. Nút `+ Đợt mới` ở chân màn.

**scrTqvDs, màn xương sống.** Ba tầng lọc, dùng lại đúng lớp `vtb` và `vt`
đã có sẵn trong app:

- Tầng 1, chip trạng thái: `Tất cả` / `Chưa liên hệ` / `Chưa tặng` /
  `Đã tặng` / `Số điện thoại lỗi`. Mỗi chip kèm số đếm.
- Tầng 2, chip phân loại: nạp từ danh mục nhóm khách, chỉ hiện nhóm có dòng.
- Tầng 3, ô tìm theo tên khách hoặc số điện thoại.

Mỗi dòng là một thẻ `vxr`:

```
+---------------------------------------------------------------+
| Nhạc sĩ Nguyễn Văn Chung                     [Nghệ sĩ]        |
| Hộp Quà Tết "Cá Ngựa Du Xuân" x1                              |
| Chị Thảo  -  Sales  -  0908255045                             |
| [Chưa liên hệ]  [Chưa tặng]                                   |
+---------------------------------------------------------------+
```

Hai nhãn trạng thái ở dòng cuối là HAI NÚT BẤM ĐƯỢC, đổi trạng thái ngay tại
chỗ, không phải mở form. Đây là chỗ tiết kiệm thời gian lớn nhất: người trực
điện thoại gọi xong 60 cuộc thì bấm 60 lần, chứ không mở và đóng 60 cái form.
Bấm là gọi thẳng máy chủ, máy chủ trả về trạng thái mới, màn vẽ lại một dòng.

Dòng nào số điện thoại chưa bóc được thì viền đỏ, kèm một dòng chữ đỏ nói rõ
việc phải làm, ví dụ `Ô số ghi hai số khác nhau, nhờ anh chị chọn giúp một
số`. Theo QT-24, câu báo lỗi phải nói việc làm tiếp.

**scrTqvSua, form một phiếu.** Xếp theo đúng thứ tự người ta làm việc, không
theo thứ tự trong cơ sở dữ liệu:

```
1. KHÁCH
   [Chọn khách trong hệ]   <- ô chọn, tìm nhanh; bỏ qua được
   Tên khách        [____________________]
   Phân loại        [ô chọn: Nghệ sĩ ▾]
   Title riêng      [____________________]  (Đạo diễn, Nhà Thiết Kế...)
   Đơn vị           [____________________]

2. AI LO
   Khách của        [ô chọn người ▾]   <- tự điền từ khách, sửa đè được
   Bộ phận làm      ( ) Sales   ( ) Marketing
   Người làm        [ô chọn người ▾]   (để trống thì giao cả nhóm)

3. LIÊN HỆ
   Số điện thoại    [0972741266 - Na (Trợ Lý)_____]
   -> khung xanh:  Đã đọc ra 0972741266, di động.
                   Người nghe máy: Na (Trợ Lý).
                   Đây KHÔNG phải số chính chủ, tin nhắn tự động đã khoá.
   Địa chỉ          [____________________]
   Giờ giao         [____________________]

4. QUÀ
   + Thêm món
   [ô chọn món ▾]  [số lượng]  [x]
   [ô chọn món ▾]  [số lượng]  [x]

5. LỜI CHÚC
   Mẫu              [ô chọn mẫu ▾]
   -> khung xám hiện lời chúc đã ráp tên thật, đọc lại được ngay
   [ ] Sửa tay lời chúc này
   (tick vào mới hiện ô soạn)

6. TRẠNG THÁI
   Tặng      ( ) Chưa tặng   ( ) Đã tặng      Ngày tặng [__/__]
   Liên hệ   ( ) Chưa liên hệ ( ) Đã liên hệ
   Ghi chú   [____________________]

[ Lưu ]
[ Lưu và thêm khách tiếp theo ]
```

Khung xanh ở mục 3 là điểm mấu chốt của cả màn: người nhập THẤY NGAY máy đọc
ra số gì, chứ không phải lưu xong rồi mới biết máy hiểu sai. Gõ tới đâu bóc
tới đó, không đợi bấm Lưu.

**scrTqvNhanh, thêm nhanh.** Dán cả cột từ bảng tính vào một ô rộng, mỗi dòng
một khách, các cột cách nhau bằng dấu tab. Máy bóc ra, hiện bảng xem trước có
đánh dấu dòng nào lỗi, người xác nhận rồi mới ghi.

Đây là đường DUY NHẤT để nhập hàng loạt, và nó tuân đúng luật đã chốt trong
AGENTS.md: máy đọc tệp của khách để TRÌNH RA cho người xác nhận thì được, ghi
thẳng xuống cơ sở dữ liệu thì không.

---

## 4. Bóc số điện thoại

### 4.1. Đã chạy thử `lib.sdt()` trên dữ liệu thật, và kết quả khác đề bài

Em chạy đúng hàm `lib.sdt()` hiện hành trên 18 ô số điện thoại lấy nguyên
văn từ bảng tính. Kết quả:

| Ô nguyên văn | `lib.sdt()` trả về | Đánh giá |
|---|---|---|
| `0972741266 - Na (Trợ Lý)` | `0972741266` | Số đúng, NHƯNG là số trợ lý |
| `093 2554338 (chị Linh quản gia)` | `0932554338` | Số đúng, là số quản gia |
| `Hoàng Phương Nam +84 90 8415976` | `0908415976` | Đúng |
| `0 96 3149900` | `0963149900` | Đúng |
| `028 39322722 gặp chị Thư` | rỗng | MẤT SỐ, đây là số bàn |
| `02839322722 (Số bàn người giúp việc)` | rỗng | MẤT SỐ |
| `25 hộp cho Sen Vàng... liên hệ: 0903015001 - Thi` | rỗng | MẤT SỐ |
| `Gửi bảo vệ cho anh Bình hoặc alo chị Hương 0908280338` | `0908280338` | **SAI NGƯỜI** |
| `bấm chuông` | rỗng | Đúng, vốn không có số |

Nên nói lại cho đúng: `lib.sdt()` không hỏng. Nó bóc được phần lớn ca rác
thông thường, và khi không chắc thì trả rỗng chứ không đoán bừa, đúng như
chú thích trong `lib.py` dặn. Vấn đề nằm ở ba chỗ khác:

**Một, nó mất số cố định.** Bảng đầu số di động không có `028`, nên mọi số
bàn đều thành rỗng. Trong dữ liệu thật có ít nhất hai khách chỉ để lại số
bàn. Với hai người đó, hệ thống sẽ mãi mãi báo "chưa có số".

**Hai, nó mất số nằm trong câu.** Ô nào có thêm chữ số khác, ví dụ số lượng
hộp hay ngày tháng, là tổng số chữ số vượt chín và hàm trả rỗng.

**Ba, và đây mới là chỗ nguy hiểm, nó trả về số ĐÚNG của NGƯỜI KHÁC.** Ô
`Gửi bảo vệ cho anh Bình hoặc alo chị Hương 0908280338` cho ra một số hợp lệ
hoàn hảo, không cờ, không cảnh báo. Cùng kiểu đó là số trợ lý và số quản gia.
Nếu về sau nối vào ZNS, hệ thống sẽ gửi "Kính chúc anh Lâm Thành Kim..." vào
máy trợ lý của anh ấy. Đó không phải lỗi kỹ thuật, đó là một sự cố thương
hiệu với đúng nhóm khách mà cả đợt quà này sinh ra để chăm.

Kết luận đúng như anh yêu cầu, nhưng vì lý do khác đề bài nêu: PHẢI bóc sạch
TRƯỚC, và `lib.sdt()` chỉ được dùng ở bước cuối, trên một mẩu chuỗi đã cô lập.

### 4.2. Tệp mới `vagabond/sdt_boc.py`, phần thuần

Không `import frappe`. Chạy được trong bộ kiểm thử tầng khung của CI, không
cần site.

```
BAO_KHONG_CHINH_CHU = (
    "trợ lý", "tro ly", "quản gia", "quan gia", "thư ký", "thu ky",
    "bảo vệ", "bao ve", "nhân viên", "nhan vien", "quản lý", "quan ly",
    "giúp việc", "giup viec", "tài xế", "tai xe", "mẹ", "chồng", "vợ",
)

DAU_CO_DINH = ("024", "028", "0232", ...)   # đầu số vùng, khai đủ, không đoán

def boc(tho):
    """Bóc một ô số điện thoại rác. THUẦN, không đụng cơ sở dữ liệu.

    Trả về dict:
        sdt          '0xxxxxxxxx' hoặc rỗng
        loai         'di_dong' | 'co_dinh' | ''
        nguoi_nghe   'Na (Trợ Lý)' hoặc rỗng
        chinh_chu    1 hoặc 0
        canh_bao     câu nói rõ phải làm gì, rỗng nếu sạch
        tho          giữ nguyên đầu vào
    """

    # 1. Chuẩn hoá bề mặt. Đổi mọi dấu gạch lạ về gạch thường, gộp khoảng
    #    trắng. KHÔNG bỏ chữ, vì chữ chính là chỗ đọc ra ai nghe máy.

    # 2. Dò TỪNG MẨU số trên chuỗi GỐC, chưa ép chữ số.
    #    Đây là điểm khác căn bản với lib._chin_so: hàm kia ép cả ô thành
    #    một dãy chữ số rồi mới xét, nên một ô có hai số hay có ngày tháng
    #    là hỏng. Ở đây tách mẩu trước, xét sau.
    #
    #    Khuôn: (?:\+?84|0)[\d][\d .\- ]{6,14}\d
    #    Quét hết, giữ cả vị trí bắt đầu và kết thúc của từng mẩu.

    # 3. Với mỗi mẩu, gọi lib.sdt() trên RIÊNG mẩu đó.
    #    Ra số thì là di động. Không ra thì thử bảng đầu số cố định.
    #    Vẫn không ra thì bỏ mẩu.

    # 4. Không mẩu nào hợp lệ:
    #       canh_bao = "Chưa đọc ra số điện thoại trong ô này. Nhờ anh chị
    #                   gõ lại số vào ô, hoặc để trống nếu khách không cho số."
    #       trả về sdt rỗng.

    # 5. Hai mẩu trở lên hợp lệ và KHÁC NHAU:
    #       KHÔNG tự chọn. Lấy mẩu đầu làm gợi ý nhưng đặt cờ:
    #       canh_bao = "Ô này có 2 số: 0913112345 và 0908280338. Nhờ anh chị
    #                   chọn giúp số của chính khách rồi gõ lại một số thôi."
    #       chinh_chu = 0
    #
    #    Vì sao không tự chọn mẩu đầu: ô thật
    #    "Gửi bảo vệ cho anh Bình hoặc alo chị Hương 0908280338" chỉ có MỘT
    #    số, mà số đó là của chị Hương. Máy không có cách nào biết. Đoán
    #    đúng chín lần và sai một lần vẫn là một khách VIP nhận tin nhắn
    #    chúc mừng tên người khác.

    # 6. Đúng một mẩu: lấy phần chữ NGAY SAU mẩu đó (và nếu trống thì phần
    #    chữ ngay trước) làm nguoi_nghe. Gọt các dấu dẫn - ( ) : và các từ
    #    dẫn "gặp", "gọi", "alo", "liên hệ".
    #       '0972741266 - Na (Trợ Lý)'        -> 'Na (Trợ Lý)'
    #       '093 2554338 (chị Linh quản gia)' -> 'chị Linh quản gia'
    #       'Hoàng Phương Nam +84 90 8415976' -> 'Hoàng Phương Nam'

    # 7. nguoi_nghe khớp BAO_KHONG_CHINH_CHU thì chinh_chu = 0 và
    #    canh_bao = "Số này là của %s, không phải số chính chủ. Tin nhắn tự
    #                động đã khoá, nhờ anh chị gọi tay." % nguoi_nghe

    # 8. loai == 'co_dinh' thì chinh_chu giữ nguyên nhưng
    #    canh_bao = "Đây là số bàn, không gửi được tin nhắn Zalo. Nhờ anh
    #                chị gọi tay."
```

Ba luật xuyên suốt, viết ra để người sau không nới lỏng:

1. **Không bao giờ đoán.** Không chắc thì trả rỗng kèm câu bảo phải làm gì.
2. **Không bao giờ sửa `sdt_tho`.** Ô người ta gõ giữ nguyên vĩnh viễn, để
   sáu tháng sau còn tra lại được máy đã hiểu sai chỗ nào.
3. **Bóc lại được không giới hạn lần.** Chạy lần thứ mười trên cùng một ô
   phải ra cùng một kết quả, để vá luật xong thì quét lại cả sổ được.

Điểm gọi: hook `validate` của phiếu, mỗi lần `sdt_tho` đổi. Cộng một hàm quét
lại toàn bộ để chạy tay sau khi sửa bảng đầu số.

### 4.3. Ca kiểm bắt buộc

Đặt trong `vagabond/khung/kiem_thu/thu_sdt_boc.py`, chạy ở CI. Nạp thẳng 18
ô nguyên văn ở bảng mục 4.1 làm dữ liệu kiểm, cộng ca ô hai số. Ca kiểm này
là thứ giữ cho luật không bị nới ra sau này.

---

## 5. Chia việc qua màn Việc cần làm, tám bước

Làm đủ tám, thiếu một bước là việc không tới tay ai hoặc chip bấm vào rỗng.

**Bước 1. Thêm vào `LOAI_PHIEU` trong `viec_can_lam.py`.**

```
("tang_qua", "Tặng quà khách VIP", "🎁"),
```

Đặt sau `kiem_ke` và trước `ycmh`. Thứ tự trong danh sách chính là thứ tự
chip trên màn.

**Bước 2. Khai vai trong `MA_TRAN`.**

```
"tang_qua": VAI_SALES | VAI_MARKETING | VAI_QUAN_LY | VAI_GIAM_DOC,
```

`viec_can_lam.py` hiện chưa có `VAI_SALES` và `VAI_MARKETING`, phải thêm hai
tập vai mới. `VAI_SALES` lấy theo bộ đã dùng nhất quán khắp repo là
`{"Sales User", "Sales Manager", "Bộ phận đặt hàng"}`.

**Đây là chỗ em phải hỏi anh Việt trước khi code.** Cả repo hiện KHÔNG có
vai nào tên Marketing. Chú thích trong chính `viec_can_lam.py` dặn "tên vai
lấy từ site thật, không bịa". Nên trước khi dựng, cần anh cho biết bộ phận
Marketing đang mang vai gì trên hệ, hoặc chốt tạo một vai mới tên
`VGB - Marketing`. Bịa một tên vai ở đây là nguyên nhóm Marketing mở màn ra
thấy trống trơn mà không ai hiểu vì sao.

**Bước 3. Viết hàm `_viec_tang_qua(vai, nguoi)`.**

Gom hai loại việc, đúng hai trục trạng thái:

```
def _viec_tang_qua(vai, nguoi):
    """Phiếu tặng quà đang chờ người này. Hai trục, hai nhóm việc riêng."""

    # Chỉ lấy phiếu của đợt ĐANG CHẠY. Đợt đã đóng mà còn hiện lên là mỗi
    # mùa sau lại đội thêm một lớp việc chết không ai dọn.

    # Nhóm 1: chưa liên hệ  -> tt 'chua_lien_he'
    # Nhóm 2: đã liên hệ mà chưa tặng, và ngày giao đã tới hoặc đã qua
    #         -> tt 'tre_hen' nếu quá ngày, 'chua_tang' nếu đúng ngày
    #
    # Bỏ hẳn phiếu có huy = 1.

    # Lọc theo người, theo quyết định 1 ở mục 0:
    #   - Có Sales Manager hoặc Giám đốc: thấy hết trong đợt.
    #   - Không: chỉ thấy phiếu mình là khach_cua hoặc nguoi_lam, cộng
    #     phiếu của bộ phận mình mà chưa ai nhận.
    #   - Phiếu VÔ CHỦ, tức khach_cua trống và nguoi_lam trống: dồn về
    #     nhóm Sales Manager. Không để rơi vào khoảng không.
```

Trần lấy 60 dòng cho đồng nhịp với các hàm `_viec_*` khác.

**Bước 4. Nối vào danh sách `nguon` trong `danh_sach()`.**

```
("tang_qua", lambda: _viec_tang_qua(vai, nguoi)),
```

**Bước 5. Thêm nhãn vào `NHAN_TT`.**

```
"chua_lien_he": "chưa liên hệ",
"chua_tang": "chưa tặng",
```

Không thêm `tre_hen`, đã có sẵn và dùng chung.

**Bước 6. Thêm màu vào `MAU_TT`.**

```
"chua_lien_he": "#c77700",    # cam, giống các trạng thái chờ người làm
"chua_tang": "#7a4bbf",       # tím, giống 'cho_lam'
```

**Bước 7. Khai giao việc thật trong `giao_viec.py`.**

Thêm nhánh cho doctype mới vào `_ai_phai_lam(doc)`, để phiếu sinh ra là ô
Assigned To trên Desk có tên người thật và chuông bắn đi được. Giao theo
NHÓM chứ không theo một cái tên, đúng luật đã ghi ở đầu tệp đó: viết cứng
một tên thì ai nghỉ phép là cả chuỗi tắc.

```
if dt == "Vagabond Tang Qua VIP":
    if doc.get("huy") or doc.get("tt_lien_he") == "Đã liên hệ":
        return ([], "")
    nguoi = [doc.nguoi_lam] if doc.get("nguoi_lam") else _nguoi_theo_vai(...)
    return (nguoi, "%s: %s chờ liên hệ trước khi tặng quà"
                   % (doc.name, doc.get("ten_khach") or ""))
```

Cộng một dòng `doc_events` trong `hooks.py` để `khi_sinh_phieu` chạy.

**Bước 8. Khai giao diện trong `02-trang-chu.js`.**

Ba chỗ, thiếu một chỗ là ô bấm vào không đi đâu:

- Thẻ ô trong `scrHome`, dựng có điều kiện theo vai.
- Nhóm `CRM` trong `VGB_NHOM` như mục 3.1.
- Đường dẫn trong `VGB_DUONG`: `'tang-qua-vip': 'TQV'`, cộng nhánh
  `if (k === 'TQV') return go(scrTqvDot);` trong `vgbGo`.

Đi qua `vgbGo` chứ không gọi `go()` thẳng. Bỏ qua cửa này là ô mất địa chỉ,
và đó đúng là lỗi anh Việt báo ngày 24/08 với phân hệ Kế toán.

---

## 6. Zalo, vá lỗ hổng và hai lớp khoá

### 6.1. Lỗ hổng hiện tại, đã kiểm chứng

`vagabond/zalo.py` hiện KHÔNG có một chữ nào về `vagabond_kiem_that`. Đã
grep toàn tệp. Trong khi `thong_bao.py` dòng 168 thì có, và ca kiểm
`thu_kiem_that.py` dòng 75 đang canh giữ đúng tệp đó.

Nghĩa là: chạy bộ kiểm thử tích hợp trên site thật lúc này thì chuông đẩy bị
chặn, còn tin ZNS thì bay ra ngoài thật. Ba đường đang gọi `zalo.gui_tin` là
`dang_nhap.py` dòng 66, `diem_otp.py` dòng 265, `thanh_toan.py` dòng 219.
Đường thứ ba gửi tin yêu cầu thanh toán cho khách. Một lần chạy kiểm thử là
một lần khách thật nhận tin đòi tiền cho một đơn không có thật.

Chỗ vá đúng là ở `gui_tin`, KHÔNG phải ở từng nơi gọi. Vá ở một chỗ thì cả
ba đường được che ngay, và đường thứ tư mai mốt ai đó viết cũng được che sẵn.

```
def gui_tin(c, sdt84, template_id, du_lieu, dau_vet=None):
    # Bộ kiểm thử tích hợp đang chạy thì TUYỆT ĐỐI không gửi ra ngoài.
    # Điểm lưu của cơ sở dữ liệu lùi lại được một chứng từ ảo, nhưng không
    # lùi lại được một tin nhắn đã nằm trong máy khách thật. Cùng lý do và
    # cùng cách làm với thong_bao.gui. Xem khung/kiem_that/nen.py.
    if frappe.flags.get("vagabond_kiem_that"):
        return False, "đang chạy kiểm thử tích hợp"
    ...
```

Trả về `(False, ...)` chứ không ném lỗi, để giữ đúng giao kèo đã ghi ở đầu
hàm: Zalo từ chối thì cho bên gọi tự quyết, không làm hỏng cả nghiệp vụ.

Cộng một ca kiểm vào `thu_kiem_that.py`, chép đúng khuôn ca đang canh
`thong_bao.py`:

```
@ca("kiem that: duong gui ZNS phai ton trong co cam gui ra ngoai")
def _zalo_ton_trong_co():
    ...
    dung("zalo.gui_tin đọc cờ kiểm thật",
        'frappe.flags.get("vagabond_kiem_that")' in nguon)
```

Không có ca kiểm thì sáu tháng nữa một phiên khác dọn code sẽ gỡ mất, y như
lý do tệp `thu_kiem_that.py` sinh ra.

### 6.2. Ba lớp khoá riêng cho tin nhắn tặng quà

Cờ kiểm thật là lớp chung. Luồng tặng quà cần thêm ba lớp nữa, vì nhóm khách
này là nhóm sai một lần là mất.

**Lớp 1, không có đường tự động.** Không cronjob nào được gửi ZNS tặng quà.
Chỉ gửi khi có người bấm nút, trên một phiếu cụ thể, và người bấm được đóng
dấu tên vào phiếu.

**Lớp 2, cổng bốn điều kiện.** Đủ cả bốn mới cho gửi:

```
def _duoc_gui_zns(p):
    """Phiếu này có được gửi tin không. THUẦN. Trả về (được, vì sao không)."""
    if not p.sdt:            return 0, "chưa đọc ra số điện thoại"
    if p.sdt_loai != "di_dong": return 0, "số bàn không nhận được tin Zalo"
    if not p.chinh_chu:      return 0, "số này là của %s" % p.nguoi_nghe_may
    if p.huy:                return 0, "phiếu đã huỷ"
    return 1, ""
```

Nút gửi trên app MỜ ĐI khi không đủ điều kiện, và hiện luôn câu vì sao ngay
dưới nút. Không để người ta bấm rồi mới báo hỏng.

**Lớp 3, không gửi hai lần.** Ô `zns_da_gui` đóng dấu thời điểm và mã theo
dõi. Đã có dấu thì nút khoá, muốn gửi lại phải mở khoá có lý do. Trong dữ
liệu thật có ô ghi `0917055639 - Thùy Duyên` và một ô khác ghi
`0917055639 - Thùy Duyên.`, khác nhau đúng một dấu chấm. Không chống trùng
thì đó là hai tin gửi vào cùng một máy.

**Một câu để anh Việt quyết.** Em đề nghị đợt đầu KHÔNG bật ZNS tặng quà,
chỉ dựng sẵn cổng và để tắt. Lý do: mẫu ZNS phải được Zalo duyệt trước, và
bộ tham số của mẫu do người tạo mẫu đặt tên, gửi sai tên một tham số là Zalo
từ chối cả tin. Hàm `zalo.thu_mau()` đã có sẵn để đọc bộ tham số của một mẫu
mà không tốn tin nào. Cứ đối chiếu xong rồi hẵng bật.

---

## 7. Van an toàn cho nhịp quét đêm

Nhịp quét mỗi đêm một lần, tìm phiếu chưa liên hệ mà ngày giao đã cận, rồi
nhắc người phụ trách.

```
from vagabond.diem_han import GIOI_HAN_MOT_DEM   # 3000, một nguồn duy nhất

def quet_dem(chay_that=0):
    """Rà phiếu tặng quà chưa liên hệ. MẶC ĐỊNH CHẠY THỬ.

    Cùng khuôn với diem_han: mặc định không ghi gì, phải truyền chay_that=1.
    """
    ds = <phiếu chưa liên hệ, đợt đang chạy, ngày giao trong 3 ngày tới>

    if len(ds) > GIOI_HAN_MOT_DEM:
        # DỪNG LẠI, không chạy tiếp. Cả tiệm tặng nhiều nhất chừng trăm hộp
        # một mùa; chạm tới ba nghìn nghĩa là bộ lọc đã hỏng chứ không phải
        # tự nhiên đông khách. Âm thầm chạy tiếp là ba nghìn cái chuông.
        <ghi log, gửi thư báo cho quản lý, thoát>
        return {"dung": 1, "so_dong": len(ds), "vi_sao": "vượt trần một đêm"}

    if not chay_that:
        return {"chay_thu": 1, "se_nhac": len(ds)}   # chỉ đếm, không bắn
    ...
```

Ba điều chép nguyên tinh thần của `diem_han.py`:

- **Mặc định chạy thử.** Phải truyền `chay_that=1` mới thật sự nhắc.
- **Trần cứng, chạm là dừng và báo người.** Không âm thầm chạy tiếp.
- **Một phiếu một đêm một lần nhắc.** Chạy lại không nhắc hai lần.

Trần 3000 dùng chung hằng số của `diem_han` để chỉ có một chỗ chỉnh. Nhưng
với luồng này 3000 là trần chống thảm hoạ, không phải trần vận hành. Em đề
nghị thêm một trần mềm riêng, khoảng 200, chạm thì vẫn chạy nhưng ghi log
để có người nhìn. Chờ anh Việt chốt con số.

Nhịp đặt trong `scheduler_events` của `hooks.py`, giờ 6 sáng chứ không phải
nửa đêm: đây là việc nhắc người đi làm, nhắc lúc 2 giờ sáng thì tới 8 giờ
thông báo đã trôi mất trong danh sách.

---

## 8. Nằm ngoài phạm vi đợt này

Ghi ra để không rơi, không phải để làm ngay:

1. **Cảnh báo dị ứng.** Theo quyết định 2, chờ bếp khai xong danh mục nguyên
   liệu gây dị ứng. Chỗ móc sau này đã có sẵn: bảng con `mon` đã trỏ Item, và
   Item là chỗ khai dị ứng.
2. **Lead và Opportunity.** Theo quyết định 3, chỉ bật Lead. Trong đợt này
   không đụng tới cả hai.
3. **Ngưỡng đền bù 500.000đ.** Thuộc luồng khiếu nại, không thuộc luồng tặng
   quà. Làm riêng.
4. **Xuất kho quà tặng và giá vốn.** Bảng con `mon` hiện chỉ ghi nhận, chưa
   trừ kho, chưa sinh bút toán. Ghi sổ kho là chạm vào tồn kho lõi ERPNext,
   và theo mục 5 của AGENTS.md thì phải soi `stock_ledger.py` trước. Việc đó
   xứng đáng một đợt riêng.
5. **Nhập lại lịch sử ba mùa cũ.** Bảng tính có ba sheet cũ: Tết Ất Tỵ 2025,
   Trung thu 2025, Giáng sinh 2025. Nhập lại được, nhưng phải qua màn xem
   trước có người xác nhận, không nhập thẳng.

---

## 9. Việc cần anh Việt quyết trước khi em code

1. Xác nhận hoặc sửa bốn quyết định ở mục 0, hiện đang chạy bằng giả định.
2. Bộ phận Marketing đang mang vai gì trên hệ, hay tạo vai mới. Mục 5 bước 2.
3. "Đã chuyển D1" và "người khác tặng hộ" có cần trạng thái riêng không, hay
   gộp vào "Đã tặng" như em đang thiết kế. Mục 2.3.
4. Đợt đầu có bật tin nhắn Zalo tặng quà không. Em đề nghị TẮT. Mục 6.2.
5. Trần mềm cho nhịp quét đêm, em đề nghị 200. Mục 7.

---

## 10. Thứ tự dựng, nếu anh duyệt

Chia lô nhỏ, mỗi lô đứng một mình được, để nếu phải dừng giữa chừng thì thứ
đã dựng vẫn dùng được.

| Lô | Nội dung | Vì sao đứng trước |
|---|---|---|
| 1 | Vá cờ kiểm thật vào `zalo.py` cộng ca kiểm | Độc lập hoàn toàn, vá một lỗ đang mở, không đợi gì cả |
| 2 | `sdt_boc.py` cộng bộ ca kiểm 18 ô thật | Phần thuần, chạy được ở CI, chưa cần site |
| 3 | Năm DocType và danh mục nạp sẵn | |
| 4 | Máy chủ: `tang_qua.py`, dựng lời chúc, cổng gửi tin | |
| 5 | Tám bước Việc cần làm cộng giao việc | Cần lô 3 và 4 xong |
| 6 | Màn hình app `32-crm-tang-qua.js` | |
| 7 | Nhịp quét đêm | Bật sau cùng, sau khi số liệu đã sạch |

Lô 1 em có thể làm ngay hôm nay, không cần chờ chốt thiết kế, vì nó chỉ vá
một lỗ đang mở chứ không thêm tính năng gì.
