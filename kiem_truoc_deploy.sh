#!/bin/sh
# Cong kiem tra bat buoc TRUOC MOI LAN DEPLOY (anh Viet chot 15/08/2026).
#
#     sh kiem_truoc_deploy.sh
#
# Ma tra ve 0 nghia la duoc phep deploy. Khac 0 la KHONG duoc bam Deploy
# tren Frappe Cloud, du chi mot cong doan hong.
#
# Vi sao co tep nay
# -----------------
# Truoc day moi thu deu thu thang tren he dang ban hang. Loi bill in lai
# cong trung diem hom 13/08 lot toi tan luc chay that moi thay. Nay moi lan
# deploy phai qua bon cong doan may kiem, khong dua vao tri nho cua ai.
#
# Sau cong doan, hong mot cai la dung ngay:
#   1. Python bien dich duoc het           - bat loi cu phap, loi thut dong
#   2. JavaScript cua app doc duoc         - bat dau ngoac thieu, dau phay thua
#   3. Bo kiem thu tang khung xanh het     - bat loi tinh tien, dem, cat dong
#   4. Bo kiem thu phien ban bao gia       - bat bo dem so to bi vong -vN pha
#   5. Bo kiem thu tru diem tai quay       - bat tran diem, quy doi, cau bao loi
#   6. Khai bao man danh sach nap duoc     - bat typo kieu cot, thieu quyen
#   7. Moi the tren app deu bam duoc         - bat the chet, thieu nhanh dinh tuyen
#   8. app_bep.js khop voi cac phan bep/   - bat ai sua tay vao tep may sinh
#
# Cong doan 4 quan trong hon ve ngoai cua no: khai bao man nap duoc nghia la
# LoiKhaiBao khong bat duoc gi, tuc khong co man nao se vo luc nguoi dung mo.

set -e
cd "$(dirname "$0")"

echo "=============================================="
echo " CONG KIEM TRA TRUOC DEPLOY - Vagabond"
echo "=============================================="
echo ""

echo "[1/8] Bien dich Python..."
python3 -m compileall -q vagabond > /dev/null
echo "      xong, khong loi cu phap."

echo "[2/8] Doc lai JavaScript cua app..."
if command -v node > /dev/null 2>&1; then
	node --check vagabond/public/js/app_bep.js
	echo "      xong, $(grep -c '' vagabond/public/js/app_bep.js) dong doc duoc."
else
	echo "      BO QUA: may nay khong co node. Nho kiem tay truoc khi day."
fi

echo "[3/8] Bo kiem thu tang khung..."
python3 vagabond/khung/kiem_thu/chay.py -im

echo "[4/8] Bo kiem thu phien ban bao gia..."
python3 kiem_phien_ban.py

echo "[5/8] Bo kiem thu tru diem tai quay..."
python3 kiem_diem_otp.py

echo "[6/8] Nap thu khai bao cac man danh sach..."
python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from vagabond.khung.kiem_thu import nen
nen.gia_lap()
from vagabond.khung import ds
for ma in sorted(ds.NGUON_BANG):
	b = ds.lay_bang(ma)
	print("      %-4s %-22s %d cot, %d bo loc, tran %d"
		% (ma, b["ten"], len(b["cot"]), len(b["loc"]), b["tran"]))
PY

echo "[7/8] Kiem dinh tuyen: the nao cung phai bam duoc..."
python3 kiem_dinh_tuyen.py

echo "[8/8] Doi chieu app_bep.js voi cac phan trong bep/..."
python3 dung_app_bep.py --kiem

echo ""
echo "=============================================="
echo " DAT HET tang khung. Duoc phep deploy."
echo "=============================================="
echo ""
echo " CON MOT CONG NUA, MAY NAY KHONG CHAY DUOC:"
echo " Neu lan sua nay cham toi GL Entry hoac Stock Ledger Entry thi"
echo " BAT BUOC chay bo kiem thu TICH HOP tren site that sau khi deploy:"
echo ""
echo "   bench --site <site> execute vagabond.khung.kiem_that.cua.chay"
echo "   hoac goi API vagabond.khung.kiem_that.cua.chay tu Desk"
echo ""
echo " Cong tam cong doan o day chi chay PHEP THUAN. Ngay 21/08/2026 no"
echo " tra ve 0 trong khi ca tiem khong nhap kho duoc, vi ERPNext tu choi"
echo " cai ma minh dinh vao dong so cai. Chi bo kiem tich hop hoi duoc cau"
echo " do. Doc AGENTS.md muc 6."
