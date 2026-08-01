from frappe.model.document import Document


class KiemBanhNgay(Document):
	def validate(self):
		# "Co the ban" TINH o day, khong tin so tu ngoai gui vao.
		# Ton dau mang dau CONG (chot voi anh Viet 01/08): banh hom qua van
		# ban duoc, theo doi NSX de uu tien day hang cu di truoc.
		for d in self.dong:
			d.co_the_ban = (
				(d.ton_cu or 0)
				+ (d.ton_d2 or 0)
				+ (d.ton_d1 or 0)
				+ (d.sx or 0)
				- (d.da_dat or 0)
				- (d.phat_sinh or 0)
			)
