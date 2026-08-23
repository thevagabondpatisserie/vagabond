# Đọc trước khi sửa một dòng nào

Tệp này dành cho MỌI trợ lý lập trình làm việc trên repo này: Roo Code,
Claude Code, Cline, Gemini CLI, Cursor, hoặc người mới. Đọc hết rồi hãy gõ.

Đây là hệ đang chạy thật của một tiệm bánh: có tiền, có kho, có hoá đơn
điện tử gửi cơ quan thuế. Một lỗi ở đây không phải là một bug, nó là một
ca bán hàng sai số hoặc một kho lệch không đối chiếu lại được.

---

## 1. Bốn điều chống ghi đè, bắt buộc

Repo này được nhiều phiên làm song song và độc lập, không phiên nào nhìn
thấy phiên nào. Đã mất code thật hai lần vì đúng lý do này.

**Điều 1. Không code trên nền cũ.** Mở phiên là chạy:

```
git fetch origin
git log origin/main -n 5 --oneline
git status -sb
```

Không dựa vào trí nhớ về cấu trúc tệp. Riêng `vagabond/public/js/app_bep.js`
thì không bao giờ được tin bản trong đầu, vì đó là tệp máy ghép ra.

**Điều 2. Đồng bộ khắt khe ngay trước khi đẩy.** Ngay trước lúc push, chạy
lại `git fetch origin` và `git log origin/main -n 3`. Có commit mới thì
`git pull --rebase origin main`. Không `push --force`, không ghi đè.

**Điều 3. Kiểm chéo trước khi deploy.** Hai phép kiểm bắt buộc:

```
python3 dung_app_bep.py --kiem
sh kiem_truoc_deploy.sh
```

Mã trả về 0 mới được deploy. Số phiên bản app chỉ được tăng, không bao giờ
được lùi:

```
grep APPVER vagabond/public/js/bep/12-van-don.js
tail -2 vagabond/patches.txt
```

**Điều 4. Ưu tiên Pull Request.** Tạo nhánh, push, mở PR để git tự quét
xung đột. Chỉ commit thẳng vào `main` khi không còn cách nào khác.

**Gặp xung đột thì DỪNG.** Hai phiên cùng sửa một hàm thì mô tả xung đột
cho anh Việt, không tự chọn giữ bên nào.

---

## 2. App `/bep` nằm trong MỘT vỏ hàm

Toàn bộ app điện thoại nằm trong `vagabond/public/js/bep/`, gồm các phần
đánh số. `00-nen.js` mở vỏ hàm bằng `(function () {` và **`99-dong-vo.js`
đóng lại** bằng `})();`. `dung_app_bep.py` nối các phần theo thứ tự tên tệp
thành `app_bep.js`.

Ba hệ quả không được quên:

- **Phần mới thêm phải mang số nhỏ hơn 99.** Ghép sau phần đóng vỏ thì
  đoạn đó nằm ngoài vỏ hàm, không thấy `frame`, `api`, `go`, và màn hình
  của nó chết ngay khi bấm. Chuyện này đã xảy ra thật tối 20/08/2026 với
  `24-phantom.js`. `dung_app_bep.py` nay tự chặn, nhưng đừng để nó phải
  chặn.
- **`node --check` trên một phần riêng lẻ sẽ báo lỗi cú pháp.** Đó là cố
  ý. Chỉ kiểm trên tệp ghép.
- **KHÔNG sửa tay vào `app_bep.js`.** Sửa trong `bep/` rồi chạy
  `python3 dung_app_bep.py`. Phép `--kiem` đối chiếu từng byte và sẽ bắt
  được.

Không có framework, không có build step, không có React. Màn hình là các
hàm `scr...` gọi `frame(tiêu_đề, html, tuỳ_chọn)` và điều hướng bằng
`go(hàm)`. **Đừng đề nghị viết lại bằng React.** Đó không phải là cải
tiến, đó là bỏ đi hai năm.

---

## 3. Quy ước viết code của repo này

- **Tên hàm, biến, tệp: tiếng Việt không dấu.** `chia_theo_lo`,
  `cau_thieu_lo`, `scrDonChungTuThu`. Không đặt tên tiếng Anh.
- **Chú thích và chuỗi hiện ra màn hình: tiếng Việt có dấu.** Chú thích
  phải nói **VÌ SAO**, không nói lại cái code đã nói. Đầu mỗi tệp mới là
  một đoạn kể lại sự cố hoặc nhu cầu đã sinh ra tệp đó.
- **Tách phần thuần và phần cần Frappe.** Đặt các hàm không đụng cơ sở dữ
  liệu lên đầu tệp, dưới tiêu đề `# phần thuần`, rồi mới `import frappe`.
  Bộ kiểm thử tầng khung chạy được phần thuần mà không cần site.
- **Tiền tố cho mỗi màn.** Kiểm và chạm tên trước khi đặt tiền tố mới, để
  không đụng tên hàm của phần khác.
- **Không dùng dấu em dash hay en dash** trong bất kỳ nội dung nào, kể cả
  chú thích và chuỗi hiển thị. Chỉ dùng dấu gạch ngang thường.

---

## 4. Các quy tắc nghiệp vụ đã chốt

- **QT-19. Máy chủ chốt số.** Mọi con số tiền và số lượng đều tính lại ở
  máy chủ. Màn hình chỉ hiển thị, không được là nguồn của sự thật.
- **QT-20. Không xoá vĩnh viễn.** Huỷ mềm, đóng, gỡ liên kết - giữ nguyên
  vết để tra lại. Không `delete_doc` trên dữ liệu nghiệp vụ.
- **QT-24. Câu báo lỗi phải nói việc làm tiếp.** "Không đủ hàng" là câu
  hỏng. "Kho Pastry còn thiếu 78 Gram men tươi, kho Baker đang còn 13.000,
  anh chị chuyển kho rồi bấm lại" mới là câu đạt.
- **QT-28. Kiểm tên trước khi đặt tiền tố mới.**
- **QT-31. Chọn từ danh mục thì phải là Ô CHỌN, không được là ô gõ.**
  Tên gọi trong phiên làm việc: `SKILL_BANK_ROUTING`. Anh Việt chốt
  23/08/2026, sau khi cùng một lỗi quay lại lần thứ hai.

  Mọi trường mà giá trị hợp lệ đến từ một danh mục có sẵn - ngân hàng,
  nhà cung cấp, kho, tài khoản sổ cái, loại chứng từ - đều phải là ô chọn
  có tìm nhanh, trỏ thẳng vào danh mục đó. **Tuyệt đối không dùng ô nhập
  tự do.** Ô gõ tự do sinh ra rác trong cơ sở dữ liệu và làm hỏng đồng bộ.

  Riêng ngân hàng thì danh mục là 581 dòng Napas trong
  `vagabond/du_lieu/napas.json`, một nguồn duy nhất. Màn hình gọi
  `nhChon()`, máy chủ gọi `ngan_hang.chuan_hoa_hoac_bao()` ngay trước khi
  ghi vào bất kỳ ô `Link -> Bank` nào.

  Vì sao phải chặn ở CẢ HAI tầng chứ không chỉ sửa giao diện: sửa giao
  diện là hết lỗi hôm nay, nhưng một màn khác mai mốt lại dựng một ô
  `Data` là lỗi quay lại y nguyên. Đã quay lại đúng như vậy hai lần:
  17/08/2026 gõ "MB", 22/08/2026 gõ "VietinBank", cùng một câu báo lỗi
  "Không tìm thấy Ngan hang". Tầng máy chủ mới là tầng giữ được dữ liệu
  sạch, vì nó đúng kể cả khi một phiên khác viết lại màn hình.

  Ca kiểm `thu_dinh_tuyen_ngan_hang.py` soi mã nguồn `bep/` và sẽ đỏ nếu
  có ai dựng lại một ô nhập tự do cho ngân hàng.
- **Không dùng AI hay công cụ tự động đọc tệp của khách để ghi đè số liệu
  xuống cơ sở dữ liệu.** Đọc để trình ra cho người xác nhận thì được.
- **Hoá đơn điện tử đã gửi cơ quan thuế là vùng cấm.** Không tự động sửa,
  không tự động huỷ, không tự động gửi lại. Rất khó sửa chữa.

---

## 5. Soi mã nguồn gốc trước khi can thiệp vào lõi

**Không có tài liệu nào tốt bằng chính mã nguồn.** Quy tắc này sinh ra ngày
21/08/2026, sau khi cả tiệm không nhập được hàng vì một hook đúng đề bài
nhưng sai với luật của ERPNext.

Trước khi viết bất kỳ hook, lớp thay thế hay bản vá nào can thiệp vào các
doctype lõi của ERPNext - **Kế toán (GL Entry, Journal Entry, Payment
Entry), Tồn kho (Stock Ledger Entry, Bin, Stock Entry), Mua (Purchase
Receipt, Purchase Invoice, Purchase Order), Bán (Sales Invoice, Delivery
Note, Sales Order)** - bắt buộc làm hai bước sau, không được bỏ:

**Bước 1. Kéo mã nguồn gốc về máy.** Đúng nhánh mà site đang chạy:

```
mkdir -p /tmp/reference_repos
git clone --depth 1 -b version-16 https://github.com/frappe/frappe.git   /tmp/reference_repos/frappe
git clone --depth 1 -b version-16 https://github.com/frappe/erpnext.git  /tmp/reference_repos/erpnext
```

Đây là repo công khai, `--depth 1` nên chỉ mất chừng nửa phút. Số nhánh
phải khớp với phiên bản đang chạy, đọc ở Frappe Cloud, đừng đoán.

**Bước 2. Đọc thẳng vào hàm kiểm tra, trước khi đề xuất giải pháp.** Các
tệp phải soi tuỳ chỗ mình định chạm:

| Chạm vào | Đọc tệp |
|---|---|
| Bút toán, sổ cái | `erpnext/accounts/general_ledger.py`, `erpnext/accounts/doctype/gl_entry/gl_entry.py`, `erpnext/accounts/party.py` |
| Công nợ, cấn trừ | `erpnext/accounts/utils.py` (`get_payment_ledger_entries`), `erpnext/accounts/doctype/payment_entry/` |
| Chứng từ mua, bán | `erpnext/controllers/accounts_controller.py`, `erpnext/controllers/buying_controller.py`, `erpnext/controllers/selling_controller.py` |
| Tồn kho | `erpnext/stock/stock_ledger.py`, `erpnext/controllers/stock_controller.py` |
| Cơ chế nền | `frappe/model/document.py`, `frappe/database/database.py` |

Cách dò nhanh một câu báo lỗi thật đã gặp trên màn hình:

```
grep -rn "Receivable / Payable" --include=*.py /tmp/reference_repos/erpnext
grep -rn "def validate_" -A 12 /tmp/reference_repos/erpnext/accounts/doctype/gl_entry/gl_entry.py
```

**Câu phải tự hỏi và phải trả lời được bằng trích dẫn mã nguồn:** không
phải "code của mình có đúng không", mà **"hệ lõi có CHO PHÉP làm việc này
không"**. Hai câu đó khác nhau, và ngày 21/08/2026 mình chỉ hỏi câu thứ
nhất.

Ví dụ thật, chép nguyên từ `erpnext/accounts/party.py`:

```python
def validate_account_party_type(self):
	if self.party_type and self.party:
		account_type = frappe.get_cached_value("Account", self.account, "account_type")
		if account_type and (account_type not in ["Receivable", "Payable", "Equity"]):
			frappe.throw(_("Party Type and Party can only be set for Receivable / Payable account..."))
```

Mười một dòng này, đọc mất ba mươi giây, đáng lẽ đã tiết kiệm được một
buổi chiều cả tiệm không nhập được hàng.

Đọc xong thì **chép đoạn điều kiện vào chú thích đầu hàm của mình**, kèm
đường dẫn tệp. Sáu tháng nữa ERPNext đổi luật thì người sau còn biết chỗ
mà đối chiếu.

---

## 6. Bộ kiểm thử, HAI TẦNG

### Tầng một: kiểm thử phép thuần, chạy tay không

```
python3 vagabond/khung/kiem_thu/chay.py -im   # tầng khung, hơn 300 ca
python3 kiem_diem_otp.py                      # hơn 2000 ca
python3 kiem_phien_ban.py
sh kiem_truoc_deploy.sh                        # cổng 8 công đoạn
```

Chạy được ở mọi nơi, kể cả máy chạy CI của GitHub: không Frappe, không
site, không thư viện mạng. Ca kiểm nào kéo theo `requests` là ca kiểm đặt
sai chỗ. Tái hiện môi trường CI ngay tại máy:

```
mkdir -p /tmp/chanreq
printf 'raise ImportError("gia lap CI")\n' > /tmp/chanreq/requests.py
PYTHONPATH=/tmp/chanreq python3 vagabond/khung/kiem_thu/chay.py -im
```

Thêm tính năng thì thêm ca kiểm cho nó, trong cùng lần sửa. Ca kiểm phải
chốt lại **cái bẫy đã làm hỏng**, không chỉ chốt đường đi đúng. Đọc các ca
sẵn có để thấy văn phong: mỗi ca có một câu tiếng Việt nói rõ nó giữ điều
gì.

### Tầng hai: KIỂM THỬ TÍCH HỢP, bắt buộc với sổ cái và tồn kho

**Tầng một không bao giờ chứng minh được rằng hệ lõi chấp thuận việc mình
làm.** Ngày 21/08/2026 nó trả về 0 trong khi cả tiệm không nhập được hàng:
hàm `gan_doi_tac` chạy đúng răm rắp, chỉ có điều ERPNext từ chối cái nó
vừa điền. Mock và unit test thuần mù trước loại lỗi đó.

Nên: **mọi thay đổi chạm tới GL Entry hoặc Stock Ledger Entry tuyệt đối
không được chỉ có unit test.** Bắt buộc có ca kiểm tích hợp trong
`vagabond/khung/kiem_that/`, và ca đó phải:

1. Dựng chứng từ thật (Purchase Receipt, Stock Entry, Sales Invoice...).
2. Gọi `insert()` rồi `submit()` **ghi thẳng xuống cơ sở dữ liệu**, để
   ERPNext chạy trọn chuỗi validation của nó.
3. **Frappe hay ERPNext ném lỗi thì ca kiểm ĐỎ**, kèm nguyên văn câu lỗi.
4. Đọc lại sổ cái vừa sinh ra và chốt từng điều kiện mình cần.

Chạy nó trên site thật:

```
bench --site <site> execute vagabond.khung.kiem_that.cua.chay
```

hoặc gọi cửa `vagabond.khung.kiem_that.cua.chay` từ Desk. Chỉ giám đốc và
System Manager mở được.

**Ba lớp bảo vệ dữ liệu thật, không được gỡ cái nào:**

- **Điểm lưu.** Mỗi ca chạy trong một `frappe.db.savepoint`, xong thì
  `frappe.db.rollback(save_point=...)`. Chứng từ ảo tồn tại thật lúc chạy
  rồi biến mất hoàn toàn.
- **Khoá tay lái giao dịch.** `frappe.db._disable_transaction_control` bật
  suốt lúc chạy, để một lời gọi `commit()` lạc trong hook nào đó không ghi
  chứng từ ảo vào sổ thật. Ca kiểm tự gọi `commit` là phá hỏng cả tầng
  này, và có ca kiểm tầng khung dò bằng AST để chặn.
- **Cấm gửi ra ngoài.** Cờ `frappe.flags.vagabond_kiem_that` bật suốt lúc
  chạy; `thong_bao.gui` đọc cờ đó rồi im lặng. Điểm lưu lùi được một dòng
  cơ sở dữ liệu, không lùi được một cái chuông đã kêu trên điện thoại
  người thật.

Kết quả trả về có hai khoá **phải luôn rỗng**: `chung_tu_con_sot` và
`so_luong_lech`. Không rỗng nghĩa là có chứng từ thử nằm lại trong sổ
thật, phải đi dọn ngay và báo anh Việt, không được bỏ qua.

**Không ca kiểm tích hợp nào được chạm tới hoá đơn điện tử đã gửi cơ quan
thuế, và không ca nào được sửa dữ liệu quá khứ.**

---

## 7. Deploy

Chỉ anh Việt hoặc phiên đang trực tiếp làm mới được bấm deploy. Không bao
giờ để trợ lý tự động bấm.

Frappe Cloud, bench `bench-44405`, site `erpnext-qwy-acq.s.frappe.cloud`,
app thật ở `https://app.thevagabondpatisserie.com/bep`.

Trình tự: Apps, dấu "...", **Fetch Latest Updates trước**, rồi Update
Available, chỉ tích app Vagabond, Next, **phải tích cả site** ở bước Select
sites to update (có tích thì migrate mới chạy), Deploy and update site.
Chờ khoảng năm phút.

Deploy xong **phải kiểm trên site thật**, không chỉ tin trạng thái Success:
Patch Log đã có số phiên bản mới chưa, và bấm thử đúng cái màn vừa sửa.
Trạng thái Success không nói được rằng màn hình bấm được.

---

## 8. Cách làm việc mong đợi

Đọc trước khi sửa. Sửa nhỏ, sửa đúng chỗ gốc thay vì vá ở ba nơi. Khi hai
đường cùng chạy được thì chọn đường mà sáu tháng nữa đọc lại vẫn hiểu.

Không đoán. Số liệu thật đọc được từ site thì đi đọc, đừng ước lượng. Một
câu "khoảng chừng" trong repo này là một lần đối chiếu kho sai.

Không im lặng nuốt lỗi. Nuốt lỗi là cách hệ này mất 26 đơn mua hàng hồi
16/08 mà không ai biết cho tới khi Uyên đi hỏi.
