# Quy tắc nghiệp vụ đã chốt

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 377 tới 446. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## 4. Các quy tắc nghiệp vụ đã chốt

- **QT-19. Máy chủ chốt số.** Mọi con số tiền và số lượng đều tính lại ở
  máy chủ. Màn hình chỉ hiển thị, không được là nguồn của sự thật.
- **QT-20. Không xoá vĩnh viễn.** Huỷ mềm, đóng, gỡ liên kết - giữ nguyên
  vết để tra lại. Không `delete_doc` trên dữ liệu nghiệp vụ.
- **QT-24. Câu báo lỗi phải nói việc làm tiếp.** "Không đủ hàng" là câu
  hỏng. "Kho Pastry còn thiếu 78 Gram men tươi, kho Baker đang còn 13.000,
  anh chị chuyển kho rồi bấm lại" mới là câu đạt.
- **QT-28. Kiểm tên trước khi đặt tiền tố mới.**
- **QT-31. Chọn từ danh mục thì phải là Ô CHỌN, không được là ô gõ.**
  Tên gọi trong phiên làm việc: `SKILL_BANK_ROUTING`. Anh Việt chốt
  23/08/2026, sau khi cùng một lỗi quay lại lần thứ hai.

  Mọi trường mà giá trị hợp lệ đến từ một danh mục có sẵn - ngân hàng,
  nhà cung cấp, kho, tài khoản sổ cái, loại chứng từ - đều phải là ô chọn
  có tìm nhanh, trỏ thẳng vào danh mục đó. **Tuyệt đối không dùng ô nhập
  tự do.** Ô gõ tự do sinh ra rác trong cơ sở dữ liệu và làm hỏng đồng bộ.

  Riêng ngân hàng thì danh mục là 581 dòng Napas trong
  `vagabond/du_lieu/napas.json`, một nguồn duy nhất. Màn hình gọi
  `nhChon()`, máy chủ gọi `ngan_hang.chuan_hoa_hoac_bao()` ngay trước khi
  ghi vào bất kỳ ô `Link -> Bank` nào.

  Vì sao phải chặn ở CẢ HAI tầng chứ không chỉ sửa giao diện: sửa giao
  diện là hết lỗi hôm nay, nhưng một màn khác mai mốt lại dựng một ô
  `Data` là lỗi quay lại y nguyên. Đã quay lại đúng như vậy hai lần:
  17/08/2026 gõ "MB", 22/08/2026 gõ "VietinBank", cùng một câu báo lỗi
  "Không tìm thấy Ngan hang". Tầng máy chủ mới là tầng giữ được dữ liệu
  sạch, vì nó đúng kể cả khi một phiên khác viết lại màn hình.

  Ca kiểm `thu_dinh_tuyen_ngan_hang.py` soi mã nguồn `bep/` và sẽ đỏ nếu
  có ai dựng lại một ô nhập tự do cho ngân hàng.
- **Không dùng AI hay công cụ tự động đọc tệp của khách để ghi đè số liệu
  xuống cơ sở dữ liệu.** Đọc để trình ra cho người xác nhận thì được.
- **Người mua không có mã số thuế Việt Nam (anh Việt chốt 08/10/2026, #456).**
  Công đoàn, trường, hội và khách nước ngoài xuất hoá đơn được mà không cần
  MST: màn Chi tiết đơn Sales có nút "Không có MST Việt Nam", bắt buộc tên và
  địa chỉ ghi đúng như khách đưa. Mã số thuế nước ngoài (nếu có) ghi kèm sau
  tên dạng `TÊN (MST nước ngoài: X)`, không ghi vào ô MST. Máy chủ `luu_xhd`
  vốn đã nhận tên không MST; tờ m-invoice đi vào `inv_buyerDisplayName`, ô
  mã số thuế để trống. Nút "Công ty / HKD" vẫn bắt buộc MST 10/12/13 số.
- **Hoá đơn điện tử đã gửi cơ quan thuế là vùng cấm.** Không tự động sửa,
  không tự động huỷ, không tự động gửi lại. Rất khó sửa chữa.
- **Trang Vagabond Settings: Desk và app luôn đủ cả hai (anh Việt 04/10/2026).**
  *"Mỗi lần em thêm gì trong trang này thì phải thêm cả trên bản desk và bản
  app."* Màn app "Cài đặt lõi và API" (`bep/51-cai-dat-loi.js`) KHÔNG giữ danh
  sách ô: máy chủ (`vagabond/cai_dat_loi.py`) đọc cấu trúc doctype, gồm cả
  Custom Field, rồi gửi xuống. Thêm ô vào trang (JSON hoặc TRUONG_MOI) là app
  tự có, nhưng phải tự kiểm ba việc:
  1. Ô kiểu mới mà `ep_kieu` chưa biết thì app không sửa được: thêm nhánh và ca kiểm.
  2. Ô cần hộp chọn riêng (như ngân hàng, nhóm Zalo) thì làm cả hai bên; phần
     dùng chung (nhãn, giải thích, chip tình trạng, tóm tắt, tìm) đặt trong
     `public/js/cai_dat_loi_chung.js`, không chép sang từng bên.
  3. Ô chỉ đọc trên Desk mà app phải ghi được thì khai trong
     `GHI_QUA_HOP_CHON` / `GHI_QUA_HOP_CHON_TRANG`, đừng bỏ read_only.
  Khoá bí mật không bao giờ gửi xuống máy. Ca chốt: `thu_cai_dat_loi_570.py`
  (app phủ đủ mọi ô Desk, đúng tab, đúng mục) và `hanh_vi/cai_dat_loi_570.js`.
- **Ưu đãi trên website: ERP là nguồn duy nhất (anh Việt 09/10/2026).**
  *"Anh muốn erp là nguồn duy nhất, các nơi khác chỉ việc đồng bộ theo thôi."*
  Ưu đãi tạo, sửa, bật tắt trong Chương trình khuyến mãi (mục Website). Trang
  khách đọc thẳng từ đó; màn biên tập web chỉ XEM, máy chủ chặn ghi khối
  ưu đãi gõ tay. Đặt bánh trên web dùng CHUNG `khuyen_mai.tinh` của quầy, không
  viết bộ tính riêng. Luật "dùng được trên web" có hai bản (`ly_do_khong_web`
  ở Python và `kmLyDoWeb` ở app) và ca chốt đối chiếu hai bản trên cùng bảng
  ca; sửa một bên phải sửa bên kia. Mã dùng một lần phải giữ (khoá hàng, đặt
  Đã dùng) TRƯỚC khi gửi Pancake. Ca chốt: `thu_uu_dai_web_589.py`.

---
