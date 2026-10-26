# Định hướng CRM Vagabond: mùa Giáng sinh, Tết và về sau

Bản nháp ngày 26/10/2026 do Claude soạn theo yêu cầu anh Việt, để Codex góp ý trước khi anh Việt chốt bản cuối.

## Tóm tắt

Vagabond đang có 44.850 hồ sơ khách, trong đó 43.204 khách có số điện thoại. Từ Fabi còn lưu lịch sử mua 39,9 tỷ đồng. Nhưng app chưa có cách chọn đúng nhóm khách rồi gửi họ một lời mời.

CRM nên đi đúng con đường mà SAP Emarsys, Klaviyo và Toast đều đi:

1. Một hồ sơ khách gom mọi kênh.
2. Tự chia nhóm theo hành vi mua.
3. Gửi chiến dịch đúng nhóm.
4. Đo doanh thu từng chiến dịch mang về.

Đề xuất làm ba đợt:

1. **Trước 01/12, mùa Giáng sinh (v613):**
    - Hồ sơ khách 360.
    - Phân nhóm tự động.
    - Danh sách chiến dịch để Sales gọi và nhắn.
    - Mã ưu đãi riêng cho từng chiến dịch, để đo doanh thu.
    - Ô ghi nhận khách đồng ý nhận tin.
2. **Trước 15/12, mùa quà Tết doanh nghiệp (v614).** Tết Đinh Mùi rơi vào 06/02/2027.
    - Theo dõi khách doanh nghiệp từ lúc liên hệ tới lúc chốt đơn.
    - Tin Zalo tự động: chúc sinh nhật, cảm ơn sau khi mua, nhắc đặt quà Tết cho khách năm ngoái.
3. **Sau Tết:**
    - Dự đoán lần mua kế tiếp của khách.
    - Cổng thành viên để khách tự cập nhật sinh nhật và quyền nhận tin.

Nên làm trước với nhóm **4.446 khách mua lần cuối trong mùa lễ năm ngoái (12/2025 tới 02/2026) và chưa quay lại**. Họ đã từng tin Vagabond đúng vào dịp này, nên gọi lại họ rẻ hơn nhiều so với tìm khách mới.

## Hiện trạng: nhiều dữ liệu, ít công cụ khai thác

Số liệu đọc trên site thật ngày 26/10/2026.

| Phần | Đang có | Còn thiếu |
| --- | --- | --- |
| Hồ sơ khách | 44.850 khách, 43.204 khách có SĐT. 1.602 khách doanh nghiệp và quà tặng. Lịch sử Fabi từ 04/2021 của 41.423 khách, 13.592 khách mua từ hai lần trở lên. | Chỉ 291 khách có ngày sinh, 10 khách có email, 839 khách có mã Zalo. Chưa xem được khách hay mua món gì, mua vào dịp nào. |
| Hạng khách | 6 hạng, xét lại mỗi đêm. Có 181 VOYAGER, 106 VAGABONDER, 8 FAMILY và AMBASSADOR. | Hạng chỉ đo mức chi tiêu. Không cho biết khách đang rời đi hay mới tới. |
| Điểm, trả trước, ưu đãi | Tích và tiêu điểm có OTP Zalo. Số dư trả trước. 7 kiểu ưu đãi, voucher riêng từng khách. | Mã ưu đãi chưa gắn với chiến dịch, nên không biết tin nào mang về đơn nào. |
| CRM tặng quà VIP | Đợt tặng theo dịp, danh sách khách, lời chúc theo mẫu, trạng thái đã tặng và đã liên hệ. Hiện có 34 phiếu. | Nút gửi Zalo cho khách mới có phần kiểm điều kiện, chưa có phần gửi. |
| Kênh nhắn khách | Zalo ZNS cho OTP và đòi tiền. Email xác nhận đặt bàn, hoá đơn, báo giá. | Không gửi hàng loạt được. Không có ô đồng ý hay từ chối nhận tin. |
| Cổng thành viên web | Đăng nhập bằng OTP Zalo, xem hạng, điểm, đơn Pancake. | Khách không tự khai sinh nhật, sở thích hay quyền nhận tin được. |

Từ 08/2026 tới nay ERP ghi 12.582 hoá đơn. Pancake mang về 2.851 khách có tên và SĐT. Phần lớn đơn tại quầy và đơn app giao hàng không gắn được với một khách cụ thể.

Các trường riêng của Vagabond trên Khách hàng (hạng, điểm, sinh nhật...) đang nằm trên site nhưng chưa được khai trong mã nguồn. Đợt 1 phải khai lại để không mất khi cài lại.

## Các hệ thống hàng đầu làm gì, Vagabond lấy gì

| Hệ thống | Điểm mạnh | Vagabond lấy gì |
| --- | --- | --- |
| [SAP Emarsys](https://www.sap.com/products/crm/emarsys/features.html) | Nối dữ liệu ERP, bán tại cửa hàng và bán online về một hồ sơ. Marketer tự phân nhóm, không cần IT. Gửi đa kênh. Dùng hạng và điểm ngay trong nội dung tin. | Hồ sơ gộp Fabi, ERP, Pancake. Sales tự lọc nhóm trên app. Tin nhắn chèn sẵn hạng và điểm của khách. |
| [Klaviyo](https://www.klaviyo.com/uk/features/segmentation) | Nhóm theo RFM. Dự đoán nguy cơ rời đi và lần mua tới. Nhóm tự cập nhật. Có bảng đo hiệu quả từng nhóm. | Bảng RFM tính lại mỗi đêm. Nhóm "sắp rời đi" và "đã ngủ". Đo doanh thu theo nhóm. |
| [Toast Guest CRM](https://pos.toasttab.com/products/guest-crm) | Gộp đơn, lượt ghé, đặt bàn vào một hồ sơ. Chỉ ra khách chi nhiều nhất và khách lâu không quay lại. Gửi ưu đãi kéo khách cũ. | Gộp cả đặt bàn web vào hồ sơ. Lập danh sách khách cũ cần kéo lại cho mùa lễ. |

RFM là cách chấm khách theo ba câu hỏi: mua gần đây không, mua có thường xuyên không, chi bao nhiêu.

Bài học cho một tiệm khoảng 20 người:

- **Nhóm nhỏ, đúng người, thắng gửi đại trà.** Klaviyo nêu ví dụ Ruffwear tăng 49% lượt bấm nhờ chia nhóm RFM.
- **Mỗi chiến dịch phải đo được tiền.** Cách rẻ nhất là một mã ưu đãi riêng cho chiến dịch, cộng một nhóm nhỏ cố ý không gửi để so sánh.
- **Người làm việc chính là Sales, không phải máy.** Ở quy mô này, danh sách gọi điện và nhắn Zalo cá nhân có kịch bản sẵn hiệu quả hơn mua một nền tảng gửi tự động đắt tiền.

## Đề xuất: bốn lớp CRM

Bốn lớp nối thành một vòng:

```
Nguồn dữ liệu đã có (Fabi, quầy, Pancake, web, đặt bàn, tặng quà VIP)
  -> 1. Hồ sơ khách 360 -> 2. Phân nhóm tự động -> 3. Chiến dịch -> 4. Đo doanh thu
                                   ^                                     |
                                   +----- kết quả quay về chỉnh nhóm ----+
```

| Lớp | Tính năng | Người dùng thấy gì | Đợt |
| --- | --- | --- | --- |
| 1. Hồ sơ 360 | Gộp lịch sử Fabi, hoá đơn ERP, đơn Pancake, đặt bàn vào một hồ sơ, theo SĐT | Món hay mua, dịp đã mua (Trung thu, Giáng sinh, Tết, sinh nhật), kênh mua, người nhận quà | 1 |
| 1. Hồ sơ 360 | Nhật ký liên hệ | Sales ghi "đã gọi, khách hẹn tuần sau" ngay trên hồ sơ | 1 |
| 1. Hồ sơ 360 | Đồng ý nhận tin theo từng kênh, sinh nhật | Quầy hỏi khi tích điểm. Web có ô đồng ý. Cổng thành viên cho khách tự sửa. | 1 (quầy, web), 3 (cổng) |
| 2. Phân nhóm | RFM tính lại mỗi đêm, chia 5 nhóm: trung thành, mới, sắp rời đi, đã ngủ, chỉ mua theo mùa | Chip nhóm trên danh sách khách, bấm là lọc | 1 |
| 2. Phân nhóm | Bộ lọc lưu lại được, theo món đã mua, dịp, hạng, kênh, khu vực, thời gian chưa mua | Ví dụ: "đã mua Entremet mùa Giáng sinh 2025, chưa mua lại từ 03/2026" | 1 |
| 3. Chiến dịch | Chiến dịch gồm: nhóm khách, nội dung giới thiệu món có ảnh, kênh, mã ưu đãi riêng, hạn | Danh sách chia cho từng Sales, có kịch bản gọi, bấm để gọi, bấm để chép tin Zalo | 1 |
| 3. Chiến dịch | Gửi hàng loạt qua Zalo OA và email, chỉ cho khách đã đồng ý | Xem trước tin và số người sẽ nhận. Mỗi khách tối đa hai tin mỗi tháng. | 2 |
| 3. Chiến dịch | Kịch bản tự động: chúc sinh nhật trước 7 ngày, cảm ơn sau khi mua, nhắc đặt quà Tết cho khách năm ngoái, gọi lại khách 90 ngày chưa mua | Bật tắt từng kịch bản trong Cài đặt | 2 |
| 3. Chiến dịch | Khách doanh nghiệp quà Tết: liên hệ, gửi catalogue, báo giá, chốt đơn | Bảng theo dõi mỗi công ty đang ở bước nào, nối với màn Báo giá đã có | 2 |
| 4. Đo doanh thu | Đếm đơn dùng mã chiến dịch, và đơn của khách trong nhóm trong 14 ngày sau khi gửi | Doanh thu, số đơn, tỉ lệ quay lại của từng chiến dịch | 1 |
| 4. Đo doanh thu | Giữ 10% nhóm làm đối chứng, không gửi tin | Doanh thu do chiến dịch thật sự mang về, trừ phần khách đằng nào cũng mua | 2 |
| Cả bốn lớp | Dự đoán ngày mua kế tiếp, gợi ý món theo lịch sử mua | Mỗi tuần một danh sách "khách sắp tới lượt mua" | 3 |

## Lịch triển khai

| Việc | Từ | Tới |
| --- | --- | --- |
| Đợt 1 (v613): hồ sơ, nhóm, chiến dịch gọi, đo | 27/10/2026 | 28/11/2026 |
| Sales gọi trước 4.446 khách mùa lễ cũ (danh sách xuất tạm) | 28/10/2026 | 14/11/2026 |
| Đợt 2 (v614): tin tự động, khách doanh nghiệp | 30/11/2026 | 15/12/2026 |
| Chiến dịch Giáng sinh | 01/12/2026 | 24/12/2026 |
| Mùa quà Tết doanh nghiệp | 15/12/2026 | 25/01/2027 |
| Tết Đinh Mùi | 06/02/2027 | |
| Đợt 3: dự đoán, cổng thành viên | 15/02/2027 | 31/03/2027 |

Mỗi đợt vẫn qua Codex rà và chờ anh Việt cho lệnh deploy.

## Đồng ý nhận tin, chi phí kênh gửi và rủi ro

- **Luật.**
    - [Điều 21 Nghị định 13/2023](https://hethongphapluat.com/nghi-dinh-13-2023-nd-cp-ve-bao-ve-du-lieu-ca-nhan/dieu-21): chỉ được dùng dữ liệu khách để quảng cáo khi khách đồng ý và biết rõ nội dung, cách thức, tần suất. Doanh nghiệp phải chứng minh được điều đó.
    - [Luật Bảo vệ dữ liệu cá nhân 2025](https://luatvietan.vn/nhung-diem-moi-cua-luat-bao-ve-du-lieu-ca-nhan-2025-so-voi-nghi-dinh-13-2023-nd-cp.html): hiệu lực từ 01/01/2026, thay Nghị định 13. Luật nói rõ im lặng không phải là đồng ý. Tổ chức vi phạm có thể bị phạt tới 3 tỷ đồng.
    - Câu chữ xin đồng ý cần chị Dung hoặc luật sư rà lại.
- **Trong app.**
    - Lưu đồng ý theo từng kênh (Zalo, email, gọi điện), kèm ngày và nơi khách đồng ý.
    - Khách từ chối thì máy loại khỏi mọi chiến dịch.
    - Khách chưa có ghi nhận đồng ý thì chỉ được gọi hỏi thăm, không gửi tin hàng loạt.
- **Zalo.**
    - [Tin ZNS](https://pos.manual.nhanh.vn/pos/cai-dat/gui-zalo-zns/cac-loai-tin-cua-oa) giá 250 đồng một tin thường. ZNS chỉ dùng cho tin giao dịch và chăm sóc, mẫu phải qua duyệt. Tin khuyến mãi thuần không đi đường này.
    - Tin quảng bá đi bằng broadcast tới người đã quan tâm OA. [Theo hướng dẫn của Zalo](https://oa.zalo.me/home/documents/guides/cau-hoi-thuong-gap-tin-broadcast), OA đăng ký từ 01/06/2026 phải ở gói Tăng trưởng hoặc Toàn diện mới gửi được; gói Cơ bản và Tiêu chuẩn không có broadcast. Mỗi người quan tâm nhận tối đa 4 tin miễn phí mỗi tháng và 1 tin mỗi ngày; tin mẫu ZBS quảng cáo cũng ăn vào hạn mức này. OA gói cũ (Dùng thử, Nâng cao, Premium) còn hạn thì vẫn được 4 tin mỗi tháng.
    - Việc phải làm trước chiến dịch Giáng sinh: kiểm OA của Vagabond đang ở gói nào. Nếu chưa đủ gói thì tính phí nâng gói (bài viết bên thứ ba ghi khoảng 2,5 triệu đồng mỗi năm cho gói Tăng trưởng, cần đối chiếu [bảng giá chính thức](https://zalo.solutions/oa/pricing)), hoặc lên kế hoạch tháng 12 chỉ bằng gọi điện và nhắn Zalo cá nhân.
    - Tin sau bán (Follow Up) đòi OA đạt 50.000 tin ZNS và có từ 5 cửa hàng trở lên. Vagabond chưa đủ điều kiện.
    - Vì vậy cần bắt đầu kéo khách quan tâm OA ngay từ bây giờ.
- **Rủi ro.**
    - Gửi dày thì khách chặn OA. Đặt trần mỗi khách tối đa hai tin quảng bá mỗi tháng.
    - Số điện thoại từ Fabi có thể đã đổi chủ. Lượt gọi đầu tiên cũng là dịp làm sạch danh sách.

## Anh Việt cần chốt

- [ ] Thứ tự ba đợt đã đúng ưu tiên chưa? Hay anh muốn đưa phần khách doanh nghiệp quà Tết lên trước Giáng sinh?
- [ ] Ai chạy chiến dịch hằng ngày? Ai được xem số chi tiêu của từng khách?
- [ ] Vagabond có Zalo OA nào đang có người quan tâm không, khoảng bao nhiêu người, và OA đang ở gói nào? Có đồng ý nâng gói để gửi broadcast không?
- [ ] Anh duyệt câu chữ xin đồng ý nhận tin ở quầy và trên web. Có cần luật sư rà không?
- [ ] Ngân sách ưu đãi mùa lễ cho khách cũ là bao nhiêu?
- [ ] Có cho Sales gọi trước 4.446 khách mùa lễ năm ngoái bằng danh sách xuất tạm không?

Đầu mối thảo luận: issue #502. Tệp này là bản nháp để Codex góp ý; bản cuối sẽ thay vào đây sau khi anh Việt duyệt.
