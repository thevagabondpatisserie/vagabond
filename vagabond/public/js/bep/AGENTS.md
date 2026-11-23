# Luật riêng của app /bep (vỏ hàm, chuẩn màn hình 2b)

Áp cho mọi tệp trong thư mục này. Nghiệm thu màn hình theo [2c](/docs/van-hanh-agent/nghiem-thu-va-ra.md), cổng giao diện E2 trong instruction project.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 147 tới 295. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## 2. App `/bep` nằm trong MỘT vỏ hàm

Toàn bộ app điện thoại nằm trong `vagabond/public/js/bep/`, gồm các phần
đánh số. `00-nen.js` mở vỏ hàm bằng `(function () {` và **`99-dong-vo.js`
đóng lại** bằng `})();`. `dung_app_bep.py` nối các phần theo thứ tự tên tệp
thành `app_bep.js`.

Ba hệ quả không được quên:

- **Phần mới thêm phải mang số nhỏ hơn 99.** Ghép sau phần đóng vỏ thì
  đoạn đó nằm ngoài vỏ hàm, không thấy `frame`, `api`, `go`, và màn hình
  của nó chết ngay khi bấm. Chuyện này đã xảy ra thật tối 20/08/2026 với
  `24-phantom.js`. `dung_app_bep.py` nay tự chặn, nhưng đừng để nó phải
  chặn.
- **`node --check` trên một phần riêng lẻ sẽ báo lỗi cú pháp.** Đó là cố
  ý. Chỉ kiểm trên tệp ghép.
- **KHÔNG sửa tay vào `app_bep.js`.** Sửa trong `bep/` rồi chạy
  `python3 dung_app_bep.py`. Phép `--kiem` đối chiếu từng byte và sẽ bắt
  được.
- **Màn lập phiếu mới phải có bản nháp tự lưu (v533).** Khai một dòng
  `sdKhai` và một dòng `sdBoc` trong `48-ban-soan-do.js`. Phần 48 bọc lại
  `api`, `frame`, `vgbGomNhom` và các hàm màn lúc nạp, nên nó phải đứng sau
  mọi phần có màn lập phiếu. Màn dựng trạng thái ngay trong hàm của nó thì
  thêm móc `sdGhep` ngay sau chỗ dựng.

Không có framework, không có build step, không có React. Màn hình là các
hàm `scr...` gọi `frame(tiêu_đề, html, tuỳ_chọn)` và điều hướng bằng
`go(hàm)`. **Đừng đề nghị viết lại bằng React.** Đó không phải là cải
tiến, đó là bỏ đi hai năm.

**Ngoại lệ đã duyệt: web KHÁCH dựng lại bằng Vue (anh Việt chốt 11/10/2026).**
Luật "không framework" ở trên là cho app nội bộ `/bep`, giữ nguyên. Riêng web
khách (đặt bánh, biên nhận, thành viên, đặt bàn, chính sách, màn hình khách,
trình biên tập web) chuyển sang Vue 3, mã ở `vagabond/public/web_vue/`:
- Vue để thẳng trong repo (`web_vue/lib/`), KHÔNG thêm bước build vào Frappe
  Cloud. Mô đun ES nạp qua import map; chạy `python3 cong_cu/ma_bam_web_vue.py`
  sau mỗi lần sửa để đóng dấu `?v=` (ca `thu_web_vue.py` chặn nếu quên).
- Giao diện giữ ĐÚNG Rocca đã duyệt: dùng lại nguyên CSS, cùng thẻ và lớp. Đổi
  giao diện thì so ảnh với bản cũ (`cong_cu/xem_thu_web_vue.py`) trước khi bàn giao.
- Mọi con số trên màn là computed từ MỘT nguồn trong kho (`banh/kho-banh.js`),
  không viết hàm "vẽ lại". Phép thuần ở `kho/thuan.js`, ca hành vi node ở
  `hanh_vi/web_vue_banh.mjs` chạy kho thật với Vue thật.
- Chữ marketing qua `t(khoá, mặc định)`, khoá phải có trong sổ nhãn và mặc định
  trùng sổ nhãn. Không `v-html`, không `innerHTML`.
- Bản Vue chạy song song ở `/web_moi/...` tới đêm tráo; trang cũ vẫn là trang
  khách dùng cho tới khi anh Việt duyệt tráo.

---

## 2b. Nguyên tắc thiết kế màn hình app, bắt buộc (anh Việt duyệt 03/09/2026)

Anh Việt đã yêu cầu nhiều lần, lần cuối 03/09/2026 với ảnh hai màn xuất kho
"rất thô sơ, không đồng bộ với giao diện đẹp của app". Bản đầy đủ nằm ở
project doc `nguyen-tac-thiet-ke-man-hinh-app-va-de-xuat-kho-theo-sap`. Mười
chín điều dưới đây (cùng điều 20 cho web chính) là bắt buộc cho MỌI màn mới và MỌI màn sửa; ca kiểm
`thu_nguyen_tac_man_hinh.py` canh những điều soi được bằng chuỗi.

1. **Dùng khung có sẵn, không tự vẽ.** `frame`, `card`, hàng chip, bottom
   sheet, `anhMon`, `toast`, `confirmSheet`, khuôn danh sách B3. Không viết
   HTML form thô. Màn mới phải giống màn Hoá đơn hôm nay và Tính tiền.
2. **Chọn là tìm. Không xổ danh sách để kéo.** Ô chọn có hơn 8 lựa chọn thì
   mở bottom sheet có ô tìm (`sheet(..., searchable)`, `sheetTimKhach`,
   `scrXkChonHang`), hàng hoá có thêm nút quét mã. TUYỆT ĐỐI không dùng
   `<select>`. Dưới 8 lựa chọn thì dùng hàng chip. Giá trị đang chọn hiện
   dạng thẻ (ảnh, tên đậm, dòng phụ xám, mũi tên), chạm vào là mở sheet.
3. **Ba hàng chip trên mọi màn danh sách** (anh Việt chốt 17/11/2026):
   trạng thái có đếm số, nhóm hoặc nguồn, khoảng ngày. Chip đang chọn tô đậm.
   Hàng chip cuộn ngang. Trên từng dòng có chip trạng thái: xanh xong, vàng
   chờ, đỏ cần xử, xám huỷ; màu luôn đi kèm chữ. Chip thêm ngoài ba hàng này
   phải hợp với tính năng của màn: chip tiến độ (bước mấy trên mấy) chỉ dùng
   cho màn theo dõi việc nhiều bước, không gắn cho đủ. Ngoại lệ bỏ ba hàng
   chip chỉ cho sheet chọn dưới 8 lựa chọn; ghi lý do trong bàn giao. Tránh
   lặp cùng ý ở chip, tiêu đề và dòng phụ.
4. **Chỗ nào có tên món thì có ảnh món** qua `anhMon(url)`; chưa có ảnh thì
   ô 🍰 giữ hàng. Ảnh thật từ danh mục, không ô chữ cái thay ảnh. Khách và
   nhà cung cấp có logo thì hiện logo, không thì biểu tượng nhóm. Ảnh cùng
   loại có kích thước thống nhất và giữ chỗ khi tải, lỗi hoặc thiếu ảnh;
   tải theo phần đang xem để danh sách dài vẫn thao tác được.
5. **Ô tìm nhanh ở đầu mọi danh sách,** gõ là lọc, có mã thì có nút quét.
6. **Thẻ tóm tắt đầu màn danh sách:** số phiếu, tổng tiền, chia theo trạng
   thái và nguồn; bấm số là lọc; đang lọc thì có thanh "Tổng theo bộ lọc".
7. **Trạng thái phụ chỉ đúng việc cần làm:** đang tải; chưa có dữ liệu với
   nút tạo cho người có quyền; lọc ra rỗng với cách bỏ lọc; thiếu quyền;
   tải lỗi với cách thử lại. Trang khách có thể ẩn khối chưa có nội dung.
   Màn quản trị phải giúp người phụ trách biết tạo gì, ở đâu để khối xuất hiện.
8. **Nút hành động:** một nút chính to dính đáy, nói rõ việc; nút phụ dạng
   viền; nút nguy hiểm màu đỏ và hỏi `confirmSheet`; không có nút xoá vĩnh
   viễn chứng từ (QT-20). Bấm xong phải có phản hồi.
9. **Mặc định thông minh và nhớ lựa chọn** (kho, điểm bán, quầy, ca) theo tài
   khoản và lần chọn gần nhất, ở mọi màn.
10. **Dòng hàng trong phiếu:** ảnh, tên đậm, dòng phụ (mã, đơn vị, tồn, lô
    hoặc hạn dùng), ô số lượng có nút trừ cộng và bàn phím số; vượt tồn thì
    viền đỏ tại chỗ; tổng cập nhật ngay khi gõ.
11. **Dấu vết trên mọi phiếu:** ai lập, ai ghi sổ, lúc nào, chip "Đã sửa N
    lần". Câu lý do treo lấy từ MỘT nguồn phía máy chủ (QT-19).
12. **Mọi tính năng có ở mọi màn cùng loại:** dựng cho một màn tính tiền thì
    có ở mọi màn tính tiền; dựng cho một màn phiếu kho thì có ở mọi màn phiếu
    kho (ảnh chứng từ, ghi chú, chip trạng thái, dấu vết, tìm hàng).
13. **Chạm và cuộn:** nút, chip, dòng cao ít nhất 44 điểm; không cuộn ngang
    cả trang; chừa vùng an toàn đáy máy; chữ tối thiểu 13 điểm.
14. **Số liệu và ngôn ngữ:** tiền có dấu chấm nghìn và chữ đ, khối lượng qua
    `kl()`, ngày dd/mm, giờ HH:MM, tiếng Việt có dấu, không dấu gạch dài.
15. **Có ca kiểm giữ nguyên tắc.** Số ô `<select` trong từng tệp `bep/` chỉ
    được GIẢM so với mốc ghi trong `thu_nguyen_tac_man_hinh.py`; tệp mới
    không được có ô nào. Nguyên tắc không có ca kiểm thì ba tuần sau lại bị bỏ.
16. **Danh sách phải lọc đúng phạm vi trước khi bày ra.** Trước khi đổ một
    bảng dùng chung ra màn hình, hỏi "bảng này có chứa dòng của bên khác
    không". Bank Account chứa tài khoản nhà cung cấp và khách; Contact và
    Address chứa khách; Item chứa cả nguyên liệu lẫn thành phẩm. Bày nhầm
    phạm vi thì màn dài gấp mười và người dùng hết tin số. Ca kiểm phải chốt
    phạm vi bằng một phép đếm, không chỉ bằng chuỗi. Sự cố v495, màn Khớp
    SePay thủ công liệt kê hơn sáu chục tài khoản của nhà cung cấp.
17. **Khối chỉ để đọc không được lấn chỗ của khối để bấm.** Cảnh báo, giải
    thích, danh sách ngoài lề: tối đa hai dòng; dài hơn thì thu về một dòng
    đếm số, bấm mới mở, và đặt XUỐNG DƯỚI khối hành động. Không bao giờ nối
    một danh sách không rõ độ dài bằng join rồi in thẳng: luôn là đếm số,
    vài mục đầu, rồi "và N nữa". Ở 390x844, thứ người dùng đến để bấm phải
    nằm trong màn đầu khi có ít nhất một dòng.
18. **Nhãn trên chip và trên dòng phải gọn.** Chip tối đa khoảng 16 ký tự
    nhìn thấy; tên dài rút thành mã ngắn cộng bốn số cuối, ví dụ "MB · 0615",
    tên đầy đủ đọc được khi chạm hoặc mở chi tiết trên điện thoại; title
    chỉ bổ sung cho desktop. Hàng chip cuộn ngang chừa lề hai bên. Tên món
    dài phải giữ phần giúp phân biệt món, cho xuống dòng khi cần.
19. **Chữ trên màn theo [quy tắc chữ ERP](/docs/quy-tac-chu-erp.md)** (anh
    Việt duyệt 14/11/2026). Không gọi tên người, chỉ gọi bộ phận hoặc chức
    danh (Kế toán, kế toán trưởng, Thu mua, Bếp, giám đốc, quản trị hệ
    thống). Một việc một chữ: Lưu nháp, Gửi + bộ phận, Duyệt, Trả lại, Ghi
    sổ, Hoàn tất, Huỷ chứng từ, Xoá. Gọi phần mềm là "hệ thống". Không viết
    tắt NCC, BTP, BOM trên nhãn. Chọn chữ theo mẫu chứng từ Thông tư 99,
    rồi chữ tiệm đang dùng, rồi Odoo và MISA; không lấy bản dịch máy của
    ERPNext. Ca kiểm `thu_quy_tac_chu_657.py` chặn tên người.
20. **Mọi nội dung trên web chính sửa được trong trình biên tập** (anh Việt
    chốt 21/11/2026). Chữ khách thấy đi qua `t('khoá', 'mặc định')` và có
    trong sổ nhãn `web_order/chu-mac-dinh.json`. Ảnh nhỏ của trang (mẫu cờ,
    thiệp, phụ kiện, nến số...) là một ô ảnh trong cùng sổ (cờ `"anh": true`),
    trang gọi `anhWeb('khoá', ảnh có sẵn)`, ảnh có sẵn khai trong
    `ANH_O_MAC_DINH` (web_vue/banh/du-lieu.js); Marketing thay ở thẻ Trang và
    chữ, nhóm Ảnh trên trang. Ảnh món, banner, ưu đãi, sự kiện sửa ở thẻ
    riêng của chúng. Ngoại lệ duy nhất: logo thương hiệu và logo đơn vị thanh
    toán. Thêm ô, chữ hay ảnh mới mà không vào trình biên tập là chưa xong;
    ca "luật mọi ảnh trên web chính" trong `hanh_vi/web_vue_banh.mjs` đỏ khi
    có `<img :src>` gắn cứng mới.

Khi giao việc có đổi màn hình, dùng
[skill dẫn giao diện](/.agents/skills/vagabond-uxui-giao-viec/SKILL.md) để ghi
thứ tự khối, nhãn, thành phần dùng lại và trạng thái dữ liệu. Mục 2c quy định
bằng chứng trước bàn giao và sau triển khai. Người làm chủ động dùng màn
mẫu đã duyệt để hoàn thiện phần mô tả còn thiếu trong phạm vi được giao.
