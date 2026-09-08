"""#227 v448: vá lại kịch bản nạp sau vòng 3 review Codex (phân trang phải hết kết quả).

Bench đã chạy minvoice_v447 (bản 39a47f8) được nhận diện qua BAM_BAN_CU rồi
vá lên bản mới; site chưa migrate thì v447 và v448 cùng ra một bản.
"""


def execute():
	from vagabond.minvoice_kich_ban import dong_bo

	dong_bo()
