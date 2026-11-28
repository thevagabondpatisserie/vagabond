# Đề xuất chuyển Nhân sự từ iPOS HRM sang app Vagabond

Bản 28/11/2026, cập nhật trưa 28/11 theo trả lời của anh Việt. Chưa có code. Đi chung PR với đề xuất hoa hồng (`docs/de-xuat-chinh-sach-hoa-hong-11-2026.md`) vì giờ công và hồ sơ nhân viên ở đây là đầu vào của phiếu KPI.

Repo công khai: tên người trong ảnh vẽ là tên giả, giờ giấc là ví dụ. Không ghi tên wifi, mã thiết bị, lương của ai.

## 1. Tóm tắt cho anh Việt

- **Vấn đề:** chấm công, xếp lịch, đơn từ đang nằm ở iPOS HRM, tách khỏi ERP, chia hai app (nhân viên và quản lý), hơn 45 ô chức năng. Giờ công cho thưởng phải nạp tay.
- **Việc sẽ làm:** dùng Frappe HR làm phần máy phía sau (hồ sơ, ca, lượt chấm, bảng công, phép). Màn bấm hằng ngày đặt trong mục **Nhân sự** của app Vagabond: **một app, thêm 7 ô** (6 ô làm việc và ô Cài đặt nhân sự). Tài khoản quản lý tự thấy thêm ô duyệt, không cần app thứ hai.
- **Kết quả sẽ thấy:** nhân viên chấm công bằng một nút; quản lý duyệt mọi loại yêu cầu ở một chỗ; kế toán khoá bảng công tháng và xuất gửi bên làm lương; phiếu KPI tự lấy giờ công.
- **Anh đã chốt (27 và 28/11):** dùng Frappe HR thay iPOS HRM; màn nhân viên làm trong app Vagabond; tối giản, một app cho cả nhân viên và quản lý; lương giai đoạn đầu vẫn để bên làm lương tính, ERP chỉ xuất bảng công; chấm công kiểm wifi công ty cộng định vị; khuôn mặt làm trước bước lưu ảnh, tự so ảnh làm sau; danh sách nhân viên lấy trước từ danh sách tài khoản; 6 ô theo phương án A; câu chữ theo bản vẽ 2.
- **Anh chốt thêm 28/11:** giữ y ba cách tính của iPOS ở mục 4; Xin đi muộn, Xin về sớm tối đa 3 lần mỗi tháng và tự sửa được trong Cài đặt; đường mạng các điểm có địa chỉ cố định; mẫu văn bản đồng ý dùng ảnh khuôn mặt do Claude soạn (`mau-dong-y-du-lieu-cham-cong.md`); danh sách nhân viên lấy từ iPOS HRM.
- **Còn chờ anh:** xem mục 8.

## 2. Bảy ô mới trong mục Nhân sự

![Mục Nhân sự sau khi thêm 6 ô](anh/0-sau-o-nhan-su.jpg)

| Ô | Ai thấy | Việc |
|---|---|---|
| Chấm công | Mọi người | Vào ca, ra ca bằng một nút. Cũng là nút lớn ở Trang chủ |
| Lịch làm việc | Mọi người | Ca của tôi, phép còn, gửi yêu cầu theo từng ca |
| Duyệt | Quản lý trở lên | Mọi yêu cầu chờ duyệt ở một danh sách |
| Xếp lịch | Quản lý trở lên | Xếp ca theo tuần cho điểm mình quản |
| Bảng chấm công | Quản lý xem điểm mình; Kế toán khoá kỳ và xuất | Theo dõi trong ngày, tổng hợp công tháng |
| Nhân viên | Kế toán, giám đốc | Hồ sơ, điểm làm, bộ phận, người duyệt yêu cầu, nhóm thưởng |
| Cài đặt nhân sự | Kế toán, giám đốc | Mọi cài đặt ở mục 7 (anh Việt chốt 28/11: mọi phần đều tự cài được) |

Năm ô đang có (Tuyển dụng, Duyệt KPI và hoa hồng, Bảng chỉ tiêu và bậc hoa hồng, Điểm KPI của tôi, Hoa hồng giới thiệu) giữ nguyên.

## 3. Màn bên trong (bản vẽ 2)

| Ảnh | Màn |
|---|---|
| ![](anh/1-man-cham-cong.jpg) | **Chấm công.** Nút tự đổi Vào ca / Ra ca. Ba điều kiện hiện trước khi bấm: Wifi công ty, Đúng vị trí, Thiết bị đúng. Thiếu điều kiện nào thì hiện đỏ kèm cách xử lý. Dòng "Quên chấm ra" bấm vào mở sẵn Bổ sung công |
| ![](anh/2-man-chup-anh.jpg) | **Chụp ảnh khi chấm.** Lần đầu chụp ảnh đăng ký, quản lý duyệt. Đổi điện thoại thì gửi quản lý duyệt thiết bị mới |
| ![](anh/3-man-lich-lam-viec.jpg) | **Lịch làm việc.** Phép năm còn và hạn mức tháng ở đầu màn. Mỗi ca một dòng có nhãn màu kèm chữ. Lọc Tuần này, Tuần sau, Cả tháng, Yêu cầu của tôi |
| ![](anh/4-man-gui-yeu-cau.jpg) | **Chạm vào ca:** 6 loại yêu cầu (Xin nghỉ ca, Xin đi muộn, Xin về sớm, Đổi ca, Nhờ làm thay, Bổ sung công), chọn bằng nút bấm, chỉ gõ lý do |
| ![](anh/5-man-duyet.jpg) | **Duyệt.** Ba hàng lọc (trạng thái có đếm, loại yêu cầu, khoảng ngày). Thẻ đủ thông tin để quyết: phép còn, hạn mức, lý do, cảnh báo ca thiếu người. Từ chối bắt ghi lý do |
| ![](anh/6-man-xep-lich.jpg) | **Xếp lịch.** Chọn điểm làm và bộ phận, xếp theo từng ngày, chấm đỏ báo ngày còn ca thiếu người. Chép tuần trước, Gửi lịch cả tuần |
| ![](anh/7-man-bang-cham-cong.jpg) | **Bảng chấm công.** Hôm nay, Tuần, Tháng. Người cần chú ý đứng đầu. Kế toán khoá kỳ, xuất gửi bên làm lương |
| ![](anh/8-man-nhan-vien.jpg) | **Nhân viên.** Danh sách có ô tìm, lọc trạng thái và điểm làm. Hồ sơ chỉ giữ thứ cần dùng. Cho nghỉ việc hỏi lại kèm hậu quả |

## 4. Giữ theo cách iPOS HRM của tiệm đang chạy

Đọc trực tiếp trên iPOS HRM ngày 28/11/2026, chỉ xem, không sửa.

- **Tên gọi:** Đi muộn, Về sớm, Quên chấm vào, Quên chấm ra, Nghỉ phép, Nghỉ không phép, Ca phát sinh, Trùng thiết bị. Tên sáu loại yêu cầu giữ như iPOS.
- **Ca gắn theo bộ phận:** Phục vụ có Full Sáng 06:00 - 14:30, Full Tối 12:30 - 21:00, Part Sáng, Part Tối; bếp có Pastry 1, Pastry 2, Baker 1, Baker 2. Khai lại y như vậy.
- **Loại ngày nghỉ:** 8 loại đang dùng (phép năm theo nhóm, nghỉ không lương, nghỉ lễ). Mỗi loại có tổng ngày và hạn mức tháng; khai lại y như vậy.
- **Cách tính đang bật, giữ nguyên (anh chốt 28/11):**
  - làm nhiều chi nhánh;
  - hai ca nối tiếp thì tự vào ca sau;
  - chấm khi chưa có lịch thì thành Ca phát sinh, chờ duyệt;
  - giờ quản lý sửa được dùng để tính công;
  - báo quản lý khi nhân viên vào ca, ra ca.
- **Khác iPOS, theo ý anh:** iPOS đang tắt "Chấm công khuôn mặt" và "Chỉ được phép chấm công bằng thiết bị đã đăng ký". Bản mới bật cả hai.
- **Chưa đưa vào đợt này:** Xoay ca, Xin ra ngoài trong ca, Ứng lương, Lương, Hợp đồng, Giao việc, Truyền thông nội bộ.
- **Điểm làm:** trên iPOS chỉ Thanh Niên đang hoạt động; District 1 và bếp Nguyễn Văn Trỗi đang ngưng. Hai điểm này sẽ chấm công lần đầu, không có số iPOS để so lúc chạy song song.

## 5. Kỹ thuật

- **Wifi công ty:** app chạy trên trình duyệt nên không đọc được tên wifi như app iPOS. Máy chủ kiểm lượt chấm có đi ra từ địa chỉ mạng cố định của điểm làm hay không (anh xác nhận các điểm có địa chỉ cố định, 28/11). Định vị trong bán kính điểm làm là lớp dự phòng. Địa chỉ mạng khai trong Cài đặt nhân sự, ở mục Điểm làm; không ghi vào repo.
- **Thiết bị đúng:** ghi nhớ điện thoại lần đầu; đổi máy thì quản lý duyệt.
- **Khuôn mặt:** đợt đầu lưu ảnh kèm lượt chấm để quản lý xem lại; đợt sau mới tự so ảnh, sau khi thử độ chính xác trên điện thoại thật. Ảnh khuôn mặt là dữ liệu cá nhân nhạy cảm: cần văn bản nhân viên đồng ý, ảnh không để ở chỗ công khai.
- **Frappe HR:** site đang chạy Frappe 16 và ERPNext 16, chưa cài Frappe HR, chưa có hồ sơ nhân viên. Cài thử trên bản thử trước, không đụng site thật cho tới khi anh cho phép.
- **Hồ sơ đầu tiên:** lấy từ danh sách nhân viên đang làm trên iPOS HRM (61 người, đọc ngày 28/11): mã nhân viên, tên, bộ phận, điểm làm, loại nhân viên, ngày vào; ghép với tài khoản đang có trong app. Ai chưa có tài khoản, hoặc thiếu điểm làm, người duyệt, thì hiện nhãn "Thiếu hồ sơ". Danh sách có tên thật nên chỉ nạp thẳng vào site, không lưu trong repo.
- **Cài đặt nhân sự** (chỉ giám đốc và kế toán): hạn mức Xin đi muộn, Xin về sớm mỗi tháng (mặc định 3, sửa được; đặt 0 nghĩa là không cho xin, khác với để trống); điểm làm kèm địa chỉ mạng và bán kính định vị; ca; loại nghỉ.
- **Nối với hoa hồng:** giờ công trong bảng chấm công là nguồn cho F11 (chia quỹ theo giờ công) và F7 (thưởng hiệu quả theo ngày công) của đề xuất hoa hồng, thay cho bảng nạp tay.

## 6. Lộ trình

| Đợt | Việc | Kết quả anh thấy |
|---|---|---|
| 1. Nền | Cài Frappe HR (cần anh cho phép deploy). Hồ sơ nhân viên, điểm làm, ca, loại nghỉ | Ô Nhân viên có danh sách người |
| 2. Lịch và chấm công | Xếp lịch, Chấm công (wifi, định vị, thiết bị, ảnh) | Chạy thử ở Thanh Niên, song song iPOS |
| 3. Yêu cầu và Duyệt | Sáu loại yêu cầu, ô Duyệt, báo Zalo nhóm bộ phận | Bỏ được đơn từ trên iPOS |
| 4. Bảng chấm công | Bảng công tháng, khoá kỳ, xuất cho bên làm lương; nối giờ công vào phiếu KPI | So bảng công ERP với iPOS cùng một kỳ |
| 5. Tắt iPOS HRM | Chỉ khi một kỳ lương chạy song song khớp | Một hệ thống |

Nguyên tắc: không chép lượt chấm cũ từ iPOS sang; chỉ nhập số ngày phép còn tại ngày chuyển. Mỗi đợt một PR, Codex rà, anh duyệt mới lên site.

## 7. Cài đặt nhân sự

Anh Việt chốt tối 28/11: mọi phần đều phải tự cài được, có ô Cài đặt trong mục Nhân sự, tham khảo Cài đặt của iPOS HRM. Em đọc đủ 6 thẻ Cài đặt, form Thêm mới ca làm việc và màn Quy trình phê duyệt của iPOS (chỉ xem, không lưu).

Luật chung cho mọi cài đặt:
- Chỉ giám đốc và kế toán sửa được.
- Mỗi lần sửa ghi người sửa, giờ sửa, giá trị cũ và mới.
- Cài đặt ảnh hưởng tới công hoặc thưởng áp dụng từ kỳ sau, không đổi số của kỳ đang chạy.
- Số 0 và ô để trống là hai giá trị khác nhau, ghi rõ trên từng ô (ví dụ hạn mức 0 là không cho gửi, để trống là không giới hạn).
- Địa chỉ mạng chỉ hiện "Đã khai", không hiện số.

| Ảnh | Nhóm |
|---|---|
| ![](anh/cd1-tong-quan.jpg) | **Tổng quan:** ô thứ 7 và màn Cài đặt nhân sự, 9 nhóm có nhãn màu (đã khai, thiếu, chưa khai) và ô tìm |
| ![](anh/cd2-cham-cong.jpg) | **Chấm công** |
| ![](anh/cd3-yeu-cau-duyet.jpg) | **Yêu cầu và duyệt** |
| ![](anh/cd4-bo-phan-diem-lam.jpg) | **Bộ phận và thưởng, Điểm làm:** 5 câu về người phụ trách thành 5 ô cài đặt |
| ![](anh/cd5-ca-loai-nghi.jpg) | **Ca làm việc, Loại nghỉ** |
| ![](anh/cd6-chung-xep-lich-bang-cong.jpg) | **Chung, Xếp lịch, Bảng công** |

Danh sách ô và mặc định. Mặc định lấy đúng giá trị iPOS của tiệm ngày 28/11, trừ dòng ghi "mới":

| Nhóm | Ô | Mặc định |
|---|---|---|
| Chung | Tiền tố mã nhân viên | NV |
| Chung | Làm và chấm công nhiều điểm | Bật |
| Chung | Ca qua đêm | Tắt |
| Chung | Giữ mã cũ khi nhân viên quay lại | Tắt |
| Chung | Tự chuyển nghỉ việc khi không chấm công N ngày liên tục | Tắt |
| Chung | Nhân viên tự gửi xin nghỉ việc | Bật |
| Điểm làm | Địa chỉ, vị trí, địa chỉ mạng công ty (bấm lấy tự động khi đang ở tiệm) | Khai mỗi điểm |
| Điểm làm | Bán kính cho phép chấm | 100 m |
| Điểm làm | Phụ trách quầy (hưởng mức phụ trách quỹ đội 3.4, là người duyệt mặc định của điểm) | Chưa chọn |
| Điểm làm | Đang hoạt động | Theo iPOS |
| Ca | Điểm, bộ phận áp dụng; giờ ca; nghỉ giữa ca | Theo 8 ca trên iPOS |
| Ca | Được phép đi muộn, về sớm (phút) | 0 |
| Ca | Cần chấm ra; tính tăng ca | Bật; tắt |
| Ca | Cách tính giờ làm | Theo giờ ca |
| Ca | Hệ số công (mới) | 1 |
| Xếp lịch | Khoá lịch tuần sau từ thứ, giờ | Tắt |
| Xếp lịch | Hai ca nối tiếp tự vào ca sau | Bật |
| Xếp lịch | Tự duyệt ca phát sinh đủ giờ vào, ra | Tắt |
| Chấm công | Cách kiểm: Wifi công ty + Định vị / chỉ Wifi công ty / chỉ định vị | Wifi công ty + Định vị |
| Chấm công | Chấm ở điểm khác cùng công ty | Bật |
| Chấm công | Chấm ngoài vị trí thì chờ duyệt | Tắt |
| Chấm công | Chụp ảnh khuôn mặt (mới) | Bật; người không đồng ý thì quản lý xác nhận từng lượt |
| Chấm công | Chỉ chấm trên thiết bị đã đăng ký (mới) | Bật |
| Chấm công | Giữ ảnh chấm công (mới) | 6 tháng |
| Chấm công | Chấm vào sớm nhất trước giờ ca; chấm ra muộn nhất sau giờ ca | 60 phút; 60 phút |
| Chấm công | Cảnh báo khi chấm xa điểm làm quá | 50 m |
| Chấm công | Tính công theo giờ ca khi đi muộn, về sớm (trong mức, quá mức) cho toàn thời gian và bán thời gian: 8 công tắc | Tắt cả 8 |
| Chấm công | Dùng giờ quản lý sửa để tính công | Bật |
| Chấm công | Báo khi vào ca, ra ca (chọn người nhận) | Bật; Giám đốc, Quản lý điểm |
| Chấm công | Báo khi đi muộn, về sớm (Zalo nhóm bộ phận) | Tắt |
| Yêu cầu và duyệt | Mỗi loại: cho gửi, tối đa mỗi tháng, gửi trước giờ ca ít nhất, số cấp duyệt, người duyệt mỗi cấp, người nhận báo khi xong | Theo iPOS: Đổi ca, Nhờ làm thay 2 cấp, còn lại 1 cấp |
| Yêu cầu và duyệt | Xin đi muộn, Xin về sớm: tối đa mỗi tháng | 3 lần (anh chốt) |
| Yêu cầu và duyệt | Xoay ca, Xin ra ngoài trong ca | Tắt |
| Loại nghỉ | Có lương (mới), số ngày mỗi năm, tối đa mỗi tháng, chuyển năm sau (mới), áp dụng cho, áp dụng từ | Theo 8 loại trên iPOS |
| Bộ phận và thưởng | Nhóm thưởng của bộ phận: Sales, Marketing, Quản lý cửa hàng, Quầy và bar, Bếp, Hỗ trợ, Không hưởng | Theo bảng ghép mục 3.9 đề xuất hoa hồng |
| Bộ phận và thưởng | Người phụ trách và tối đa số người phụ trách | Chưa chọn; 1 người |
| Nhân viên (hồ sơ) | Nhóm thưởng riêng của từng người, đè lên nhóm của bộ phận | Để trống = theo bộ phận |
| Bảng công | Kỳ công (mới) | Hàng tháng, ngày 1 |
| Bảng công | Quản lý sửa công sau khi hết tuần; sửa sau khi khoá kỳ | 1 ngày; 0 ngày |
| Bảng công | Mẫu xuất cho bên làm lương (mới) | Mẫu bên làm lương đang nhận |

Năm câu về người phụ trách hôm 28/11 giờ thành ô cài đặt, anh tự chọn trên app, không cần sửa code:

| Câu | Ô cài đặt |
|---|---|
| 9 người Văn phòng thuộc bộ phận nào | Nhóm thưởng trên hồ sơ từng người |
| 3 người Marketing ai hưởng hoa hồng Marketing | Nhóm thưởng trên hồ sơ từng người |
| Mỗi bộ phận mấy người phụ trách | Tối đa người phụ trách và chọn người, ở Bộ phận và thưởng |
| Thanh Niên ai phụ trách quầy | Phụ trách quầy, ở Điểm làm |
| Bảo vệ, tạp vụ có thưởng không | Nhóm thưởng của bộ phận = Không hưởng |

Không đưa vào đợt này: thẻ Hợp đồng và Lương, bảo hiểm của iPOS; "Phải hoàn thành công việc của ca để chấm ra" vì chưa làm Giao việc. Cài đặt hoa hồng (mốc, tỷ lệ, trần) giữ ở màn Bảng chỉ tiêu và bậc hoa hồng đang có.

## 8. Câu hỏi

**Cho anh Việt**
Đã chốt 28/11: giữ y ba cách tính của iPOS; hạn mức 3 lần mỗi tháng, sửa trong Cài đặt; địa chỉ mạng cố định; Claude soạn mẫu đồng ý.

1. Đọc và duyệt mẫu `mau-dong-y-du-lieu-cham-cong.md`. Đây là bản Claude soạn, không phải ý kiến luật sư; anh nên nhờ người có chuyên môn pháp lý xem lại trước khi cho nhân viên ký.
2. Người không đồng ý chụp ảnh: em đề xuất cho chấm công không ảnh, quản lý xác nhận lượt chấm (mẫu mục 5). Anh đồng ý cách này?

**Cho Codex**
- Rà luồng: có chỗ nào một yêu cầu bị duyệt hai lần, hoặc ca bị xếp trùng người, khi hai quản lý cùng thao tác?
- Rà quyền: quản lý chỉ thấy điểm mình; kế toán, giám đốc thấy mọi điểm; nhân viên chỉ thấy của mình.
- Rà chuyển đổi: chạy song song iPOS một kỳ lương có đủ để phát hiện lệch công không?
