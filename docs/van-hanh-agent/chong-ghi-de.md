# Chống ghi đè giữa các phiên

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 103 tới 146. Luật gốc: [AGENTS.md](/AGENTS.md). -->

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
merge main vào nhánh PR đã công bố, theo lệnh trên PR. Không rebase nhánh chung,
không `push --force`, không ghi đè.

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
