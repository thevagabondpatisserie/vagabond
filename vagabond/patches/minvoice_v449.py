"""#227 v449: kịch bản nạp đối chiếu theo id vì Pancake của tiệm không trả display_id.

Phát hiện trên site ngay sau deploy v448 (08/09/2026): mọi đơn đều báo
"không tìm được đơn Pancake". Bản v448 trên site được nhận diện qua
BAM_BAN_CU rồi vá lên bản mới; dấu hết kết quả dùng total_pages Pancake trả về.
"""


def execute():
	from vagabond.minvoice_kich_ban import dong_bo

	dong_bo()
