# Nguồn core cho review #302

ERPNext de591661b9ba0bd3f62ac25b99b5c85c723515f6, stock/doctype/batch/batch.py. Đọc từ checkout pinned dùng chung bench. Batch.validate chỉ gọi item_has_batch_enabled và set_batchwise_valuation. before_save mới gọi set_expiry_date:

```python
	def before_save(self):
		self.set_expiry_date()

	def set_expiry_date(self):
		has_expiry_date, shelf_life_in_days = frappe.db.get_value(
			"Item", self.item, ["has_expiry_date", "shelf_life_in_days"]
		)

		if not self.expiry_date and has_expiry_date and shelf_life_in_days:
			if (
				not self.manufacturing_date
				and self.reference_doctype in ["Stock Entry", "Purchase Receipt", "Purchase Invoice"]
				and self.reference_name
			):
				self.manufacturing_date = frappe.db.get_value(
					self.reference_doctype, self.reference_name, "posting_date"
				)

			if self.manufacturing_date:
				self.expiry_date = add_days(self.manufacturing_date, shelf_life_in_days)

		if has_expiry_date and not self.expiry_date:
			frappe.throw(
				msg=_("Please set {0} for Batched Item {1}, which is used to set {2} on Submit.").format(
					frappe.bold(_("Shelf Life in Days")),
					get_link_to_form("Item", self.item),
					frappe.bold(_("Batch Expiry Date")),
				),
				title=_("Expiry Date Mandatory"),
			)

```

serial_and_batch_bundle.py: get_reserved_batches_for_pos gom (batch_no, warehouse), qty *= -1; get_reserved_batches_for_sre dùng (-1 * Sum(qty - delivered_qty)), gom cùng khóa. Vòng vét cộng số âm vào tồn thô, không trừ lần hai. Có ca hành vi core trả50 tốt, SLE có100 lô tắt, POS giữ20/SRE giữ30: còn50 lô tắt.

Không phục hồi nuốt lỗi đọc tồn: chưa đọc đủ số giữ thì không có căn cứ cấp hàng. Đây là thực thi điều kiện không cho âm tồn, không cần đổi nghiệp vụ hay tắt guard. Runtime chỉ áp bảy purpose được duyệt; không thay controller chung.

Cấp tên Batch ở API: gọi bộ cấp số trước insert để qua Batch.autoname khi Item.create_new_batch=0. before_naming lúc insert thấy batch_id đã có nên ghi cờ người đặt, dat_ten_lo không cấp lần hai; không tiêu hai số. Ca thật kiểm dữ liệu Batch sau nhận.
