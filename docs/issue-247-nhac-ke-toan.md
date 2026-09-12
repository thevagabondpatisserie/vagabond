# Issue 247: lời nhắc cấn cọc

Theo guide Claude 5624135668/5624176215: hai màn lập hồ sơ và chi công ty hiện chữ thụ động "Cấn cọc do kế toán thực hiện" khi có đối tượng cấn và người lập không có vai FIN. Người có quyền vẫn thấy nút, không thấy lời nhắc thừa. Không đổi VAI_FIN hoặc quyền máy chủ.

Ca DOM mở cả hai màn với hai nhóm quyền: trước sửa đỏ thiếu lời nhắc, sau sửa 48/48 đạt. Chưa UAT trên site thật. v486 dành sau PR 291 v484 và PR 292 v485; tích hợp phải giữ cả patch, dựng lại bundle và kiểm SHA tích hợp.
