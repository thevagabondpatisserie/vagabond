# Issue 307: BTP hạch toán 1552 theo ô Chặng, giữ một kho

- Nguồn: issue #307 (con của #206), anh Việt duyệt 13/09/2026 sau trao đổi
  với Khải. Điều phối lại 14/09/2026 11:45: chia hai PR.
- Owner `claude[bot]`, nhánh `claude/issue-307-20260914-0450`, nền main
  `6886899d` (sau v491). PR A là bản này; PR B (hai báo cáo, bench) làm sau.
- Mục tiêu PR A: hai ô cấu hình, hook validate Item, patch nạp một lần,
  ca thuần, APPVER 492. Không đổi cờ thật, không đụng chứng từ, không nới
  `gac_tk_kho.py`.

## Bản chốt nghiệp vụ

Giữ MỘT kho. Ô "Chặng bán thành phẩm" trên hồ sơ món quyết tài khoản tồn
kho ghi vào Item Default của công ty:

| Ô Chặng | Điều kiện | Tài khoản |
|---|---|---|
| BTP sơ cấp (cấp 1) | is_stock_item=1, mã BTPB/BTPN/NBTP | ô "Tài khoản tồn kho BTP cấp 1" |
| BTP sẵn sàng (cấp 2) | như trên | ô "Tài khoản tồn kho BTP cấp 2" |
| BTP thành phần, trống | không áp | theo kho như cũ |

Đổi chặng: máy ghi đè và ghi chú vào comment món. Chặng không đổi mà kế
toán đã khai tay khác: giữ. Xoá chặng: xoá tài khoản khai riêng. Hai ô
cấu hình trống: chỉ nhắc màu vàng, không chặn lưu. Khải chốt 1552 chung
hay tách 15521/15522 thì chỉ đổi hai ô, không đổi code.

## Đoạn nguồn lõi đã đối chiếu và phần CHƯA đối chiếu được

Đã có trong repo (vagabond/hang_tang_kho.py:27-31, ERPNext de591661,
erpnext/controllers/stock_controller.py):

```
get_inventory_account_map: if self.use_item_inventory_account:
    return self.get_item_wise_inventory_account_map()
return get_warehouse_account_map(self.company)
```

Cờ đọc trên site 08/09/2026 (tai_lieu/issue-206-tai-khoan-chi-phi.md:10-11):
Company Vagabond `enable_item_wise_inventory_account=0`, tức cờ nằm trên
Company.

CHƯA đối chiếu được trong phiên này: máy GitHub Actions không ra được mạng
(git clone, gh api, WebFetch đều bị chặn), nên chưa dán được nguyên văn
`get_item_wise_inventory_account_map` và chưa xác nhận hai điều:

1. Tên ô trên Item Default mà lõi đọc. Code đặt ở một hằng duy nhất
   `tai_khoan_btp.TRUONG_ITEM_DEFAULT = "default_inventory_account"`.
2. Lõi có fallback theo tài khoản kho khi cờ bật mà món không khai không.

Lớp bảo vệ trong lúc chờ: hook kiểm `frappe.get_meta("Item Default")` trước
khi ghi, ô không có thì chỉ báo và ghi Error Log, không chặn lưu món; patch
`tai_khoan_btp_307` ném lỗi dừng migrate nếu ô không có. Người có bench
(Codex local, checkout pinned de591661) đối chiếu hai điểm trên trước khi
merge; nếu lõi không có fallback thì dừng theo đặc tả, không viết lớp đè.

## Kết quả có bằng chứng

- `vagabond/tai_khoan_btp.py`: phần thuần `chang_ap_dung`, `quyet_dinh`,
  `loi_tai_khoan`, `chon_mac_dinh`; phần Frappe `ap_dung`, `khi_luu_mon`,
  `kiem_o_cau_hinh`.
- Vagabond Settings: mục "Tài khoản tồn kho bán thành phẩm theo món" với
  hai ô Link Account, validate lọc Stock, chi tiết, còn dùng, VND.
- hooks.py: thêm `vagabond.tai_khoan_btp.khi_luu_mon` vào Item validate.
- Patch `vagabond.patches.tai_khoan_btp_307`: trỏ mặc định 1552 nếu site có
  đúng một tài khoản con 1552 còn dùng; nạp cho món theo tồn đã khai chặng;
  ghi thẳng Item Default, không save() Item để không kích validate khác trên
  dữ liệu cũ. `patches.txt` thêm dòng patch và `dong_bo_cau_truc #v492`.
- Ca thuần `thu_tai_khoan_btp_307.py` (11 ca), đăng ký trong `chay.py`.
- Cổng kiểm: ghi trong comment PR kèm SHA.

## Các bước tay của kế toán ngày cắt (đề nghị 01/10/2026)

1. Khải điền cấp 1 hoặc cấp 2 cho từng mã BTP theo tồn (báo cáo "BTP theo
   tồn chưa khai chặng" ở PR B); lưu món là hook tự ghi tài khoản.
2. Chị Dung chốt "Số dư BTP tại ngày cắt" (PR B) và lập bút toán kết chuyển
   từ tài khoản kho cũ sang 1552 đúng ngày; máy không tự sinh bút toán.
3. Trên Company Vagabond bật `enable_item_wise_inventory_account` đúng ngày
   cắt, sau khi số dư đã chốt. Không đưa vào patch.
4. Kiểm một lệnh sản xuất thật ra BTP có Nợ 1552; không đạt thì tắt cờ và
   báo trên issue.

## Còn lại và bàn giao

- Chờ Khải: 1552 chung hay tách 15521/15522 (chỉ đổi hai ô).
- Chờ chị Dung: ngày cắt.
- Chờ người có bench: đối chiếu `TRUONG_ITEM_DEFAULT` và fallback theo kho
  với lõi de591661, dán nguyên văn lên PR.
- PR B: hai Script Report và toàn bộ ca bench mục 6 của đặc tả, chạy hai
  lượt `chung_tu_con_sot=[]`, `so_luong_lech={}`.
- Chưa cập nhật nhật ký local trên máy anh Việt (phiên cloud).
