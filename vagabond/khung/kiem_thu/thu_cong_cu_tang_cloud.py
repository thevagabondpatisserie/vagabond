"""#225: cửa Cloud chỉ cho kế toán trưởng, không đổi payload/nuốt lỗi lõi."""
from types import SimpleNamespace
from unittest.mock import patch
import importlib.util
from pathlib import Path
import sys
from vagabond.khung.kiem_thu.nen import ca, la


@ca("#225 Cloud: Guest/thu ngân/Accounts User không đọc hoặc thay, Manager mới qua")
def _quyen():
	from vagabond import doi_chieu_tang_cu as loi
	class LoiQuyen(Exception):
		pass
	def nem(*a):
		raise LoiQuyen()
	def mo(**kw):
		def gan(fn):
			fn.metodos = kw["methods"]
			return fn
		return gan
	vai = []
	gia = SimpleNamespace(session=SimpleNamespace(user="Guest"), PermissionError=LoiQuyen,
		get_roles=lambda: vai, throw=nem, whitelist=mo)
	p = Path(__file__).resolve().parents[2] / "cong_cu_tang_cu.py"
	spec = importlib.util.spec_from_file_location("thu_cua_cloud225", p)
	mod = importlib.util.module_from_spec(spec)
	goi = []
	with patch.dict(sys.modules, {"frappe": gia}), patch.object(loi, "ban_xem", lambda: goi.append("xem") or {}), patch.object(loi, "thay", lambda h: goi.append(h) or {"chua_commit": True, "pkt_moi": "JE-MOI"}):
		spec.loader.exec_module(mod)
		la("ghi chỉ POST", mod.thay.metodos, ["POST"])
		for user, roles in [("Guest", ["System Manager"]), ("thu", ["Sales User"]), ("kt", ["Accounts User"])]:
			gia.session.user, vai = user, roles
			for fn, args in ((mod.xem, ()), (mod.thay, ("hash",))):
				try:
					fn(*args)
				except LoiQuyen:
					pass
				else:
					raise AssertionError("lọt quyền")
		la("chưa gọi lõi", goi, [])
		for role in ("Accounts Manager", "System Manager"):
			gia.session.user, vai = "sep", [role]
			mod.xem()
			la("kết quả POST", mod.thay("hash-da-xem"), {"ok": 1, "pkt_moi": "JE-MOI"})
		la("giữ đúng hash", goi, ["xem", "hash-da-xem", "xem", "hash-da-xem"])
		def hong(h):
			raise ValueError("hash đã cũ")
		with patch.object(loi, "thay", hong):
			try:
				mod.thay("cu")
			except ValueError:
				pass
			else:
				raise AssertionError("không được nuốt lỗi rồi báo thành công")
