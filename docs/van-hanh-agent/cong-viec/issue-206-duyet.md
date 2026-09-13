# Bản đề xuất phần lệnh sản xuất để anh Việt duyệt

Bản này theo trao đổi mới nhất: giữ lô và FEFO, thay hướng bỏ toàn bộ Batch/FIFO trước đó. Code thử trên PR302; chưa merge/deploy hoặc đổi cấu hình site.

## Đề nghị chốt

1. Giữ Batch cho nguyên liệu, bán thành phẩm, thành phẩm để máy tự chia số lượng, giữ tem và tra lịch sử.
2. Với dòng chưa có lô/gói do Vagabond tự chọn, hàng còn hạn: chọn HSD gần nhất trước, dù nhập sau. Một lô thiếu thì lấy tiếp lô khác trong đúng kho. Lô không có HSD xếp sau lô có HSD. Không chọn theo chữ/số trong mã lô. Dòng đã có gói hoặc chọn lô tay được giữ nguyên; thứ tự Desk tự sinh gói theo Stock Settings chưa được ca này chứng minh.
3. HSD không chặn thao tác sản xuất và phiếu kho khi công tắc chặn tắt; lô quá hạn có cảnh báo lưu trên phiếu. Đề xuất giữ ưu tiên hàng còn hạn trước, lô quá hạn chỉ dùng khi thiếu phần còn hạn, như cơ chế hiện có. Không tự đưa hàng quá hạn lên đầu FEFO.
4. Máy cấp mã `LO-yymmdd-nnnnnn`, ví dụ `LO-260913-000751`. Ngày là ngày tạo theo giờ site; đuôi tăng liên tục. Nhân viên không phải nhớ mẫu hoặc tự đếm. Giữ mã/lịch sử cũ.
5. Tách mã lô nội bộ với số lô NCC. Số lô NCC/HSD bao bì là thông tin nhập thực tế, không thay HSD thật bằng ngày nhập cộng số ngày chỉ để đổi thứ tự chọn. Cần rà trường và màn nhận trước khi làm phần này.
6. Giữ chặn thiếu tồn thật, sai kho, sai đơn vị, sai serial và lô đã bị người dùng vô hiệu hoá. Giữ cách tính giá vốn hiện tại; không tự bật cờ giá bình quân toàn site trong PR này.

## Code thử đã có trong PR

- Giữ nguyên FEFO; thêm ca Work Order/Stock Entry thật chứng minh nhập sau, hạn gần thì xuất trước.
- Mở rộng cơ chế cảnh báo HSD từ bốn luồng sản xuất sang phiếu Stock Entry nhập/xuất/chuyển kho. Khi chốt bật: phiếu nhập vẫn bị chặn hết hạn theo core; phiếu xuất/chuyển chỉ cảnh báo như core, không tạo chặn HSD mới. Ba loại được bổ sung kiểm lô vô hiệu hoá, độc lập công tắc HSD. Không tự tắt chốt trên site bằng patch.
- Câu cảnh báo dùng chung cho nhập và xuất, không ghi nhầm đã xuất trên phiếu nhập. Giữ tương thích ghi chú cũ khi lưu lại.
- Ca nhập kho vào lô quá hạn: ghi sổ, cảnh báo, huỷ trả tồn. Ba ca chia lô và giá vốn cũ đã bench đạt; bổ sung bất biến theo review Claude.

## Chưa được coi là xong toàn bộ

- Cửa nhận mua hàng `nhan_hang.py` còn chốt bắt nhập HSD/cận hạn riêng; chưa đổi trong bản thử Stock Entry này. Phiếu mua/bán không dùng chung lớp StockEntry. Cần code và ca thật cho từng cửa trước khi hứa mọi chứng từ không chặn HSD.
- Chưa bổ sung giao diện số lô NCC, chưa nghiệm thu tem trên máy in thật.
- Kho nguyên liệu từng bếp, thay Elle/Pauls/Bacardi/ISC, sửa Gelatine Mass, cấu trúc BTP cấp1/cấp2 và chống bấm hoàn tất trùng còn là các mục riêng của issue206. Không đổi mã/danh mục hàng loạt trong PR này.
- Bench SHA mới và Claude review phải đạt; anh Việt duyệt bản cuối rồi mới ghép đợt deploy. Không đóng issue206 chỉ vì PR302 xanh.
