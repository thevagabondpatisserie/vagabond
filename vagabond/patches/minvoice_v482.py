"""Đưa cờ hoãn phát hành vào hook đã đối chiếu trên production, không gọi HTTP."""


def execute():
	from vagabond.minvoice_sau_ghi_so import dong_bo
	dong_bo()
