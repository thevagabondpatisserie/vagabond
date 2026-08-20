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
- **Không dùng AI hay công cụ tự động đọc tệp của khách để ghi đè số liệu
  xuống cơ sở dữ liệu.** Đọc để trình ra cho người xác nhận thì được.
- **Hoá đơn điện tử đã gửi cơ quan thuế là vùng cấm.** Không tự động sửa,
  không tự động huỷ, không tự động gửi lại. Rất khó sửa chữa.

---

## 5. Bộ kiểm thử

```
python3 vagabond/khung/kiem_thu/chay.py -im   # tầng khung, hơn 240 ca
python3 kiem_diem_otp.py                      # hơn 2000 ca
python3 kiem_phien_ban.py
sh kiem_truoc_deploy.sh                        # cổng 8 công đoạn
```

Thêm tính năng thì thêm ca kiểm cho nó, trong cùng lần sửa. Ca kiểm phải
chốt lại **cái bẫy đã làm hỏng**, không chỉ chốt đường đi đúng. Đọc các ca
sẵn có để thấy văn phong: mỗi ca có một câu tiếng Việt nói rõ nó giữ điều
gì.

---

## 6. Deploy

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

## 7. Cách làm việc mong đợi

Đọc trước khi sửa. Sửa nhỏ, sửa đúng chỗ gốc thay vì vá ở ba nơi. Khi hai
đường cùng chạy được thì chọn đường mà sáu tháng nữa đọc lại vẫn hiểu.

Không đoán. Số liệu thật đọc được từ site thì đi đọc, đừng ước lượng. Một
câu "khoảng chừng" trong repo này là một lần đối chiếu kho sai.

Không im lặng nuốt lỗi. Nuốt lỗi là cách hệ này mất 26 đơn mua hàng hồi
16/08 mà không ai biết cho tới khi Uyên đi hỏi.
