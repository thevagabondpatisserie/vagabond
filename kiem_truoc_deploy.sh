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
#  10. Bo ca kiem hanh vi man ho so tt    - chay that chuoi bam tren DOM gia
#
# Cong doan 2 va 10 chay bang node, nen node la DIEU KIEN BAT BUOC va duoc
# kiem ngay dau script. Thieu node thi dung luon, khong chay tiep roi bao
# "duoc phep deploy" trong khi mot ca kiem bat buoc chua he chay.
#
# Cong doan 4 quan trong hon ve ngoai cua no: khai bao man nap duoc nghia la
# LoiKhaiBao khong bat duoc gi, tuc khong co man nao se vo luc nguoi dung mo.

set -e
cd "$(dirname "$0")"

echo "=============================================="
echo " CONG KIEM TRA TRUOC DEPLOY - Vagabond"
echo "=============================================="
echo ""

# NODE LA DIEU KIEN BAT BUOC, kiem NGAY DAU chu khong doi toi cong doan 10.
#
# Codex neu vong nam tren PR #211, va neu dung: truoc do cong doan 2 ghi "BO
# QUA neu khong co node" con cong doan 10 lai goi node thang duoi `set -e`.
# Nghia la may khong co node thi chay toi cong 10 moi vo, sau khi da in ra
# chin dong xanh - vua mat cong chay lai, vua de nguoi doc tuong chin cong
# doan kia da du dieu kien deploy.
#
# Bo ca kiem HANH VI la ca kiem BAT BUOC, khong duoc lang le bo qua roi bao
# "duoc phep deploy". Thieu node thi dung ngay tai day, va noi ro viec ke tiep.
if ! command -v node > /dev/null 2>&1; then
	echo "DUNG: may nay khong co node."
	echo ""
	echo "  Cong doan 2 (doc lai app_bep.js) va cong doan 10 (bo ca kiem hanh"
	echo "  vi man ho so thanh toan) deu chay bang node. Hai cong doan do la"
	echo "  bat buoc, khong duoc bo qua roi bao la du dieu kien deploy."
	echo ""
	echo "  Cai node roi chay lai:"
	echo "    Debian/Ubuntu   sudo apt-get install -y nodejs"
	echo "    macOS           brew install node"
	echo "  Kiem lai bang:  node --version"
	echo ""
	echo "  May chay CI cua GitHub co san node, nen day chi la viec cua may"
	echo "  dang ngoi. Chua cai duoc thi DUNG bam Deploy, doi CI xanh da."
	exit 1
fi
echo "Node: $(node --version). Du dieu kien chay cong doan 2 va 10."
echo ""

echo "[1/10] Bien dich Python..."
python3 -m compileall -q vagabond > /dev/null
echo "      xong, khong loi cu phap."

echo "[2/10] Doc lai JavaScript cua app..."
node --check vagabond/public/js/app_bep.js
echo "      xong, $(grep -c '' vagabond/public/js/app_bep.js) dong doc duoc."

echo "[3/10] Bo kiem thu tang khung..."
python3 vagabond/khung/kiem_thu/chay.py -im

echo "[4/10] Bo kiem thu phien ban bao gia..."
python3 kiem_phien_ban.py

echo "[5/10] Bo kiem thu tru diem tai quay..."
python3 kiem_diem_otp.py

echo "[6/10] Nap thu khai bao cac man danh sach..."
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

echo "[7/10] Kiem dinh tuyen: the nao cung phai bam duoc..."
python3 kiem_dinh_tuyen.py

echo "[8/10] Doi chieu bang duong dan ben JS voi danh muc ben Python..."
python3 sinh_duong.py --kiem

echo "[9/10] Doi chieu app_bep.js voi cac phan trong bep/..."
python3 dung_app_bep.py --kiem

# Cong doan 10 CHAY THAT chuoi bam tren man hinh, bang mot DOM gia viet tay.
# Chin cong doan tren chi doc ma nguon; rieng cong nay ban su kien nhu nguoi
# that go va bam. Codex neu tren PR #207: do chuoi trong ma nguon khong chung
# minh duoc hanh vi. May CI co node vi cong doan 2 da dung `node --check`.
echo "[10/10] Bo ca kiem HANH VI (DOM gia)..."
node vagabond/khung/kiem_thu/hanh_vi/thue_don_mua_227.js
node vagabond/khung/kiem_thu/hanh_vi/tai_khoan_dich_vu_252.js
node vagabond/khung/kiem_thu/hanh_vi/sua_pkt_tang.js
node vagabond/khung/kiem_thu/hanh_vi/doi_chieu_app_247.js
node vagabond/khung/kiem_thu/hanh_vi/coc_app_247.js
node vagabond/khung/kiem_thu/hanh_vi/tham_chieu_tien_267.js
node vagabond/khung/kiem_thu/hanh_vi/chay.js
# Trang /kiem-banh: chuoi go o Huy. Codex doi tren PR #218 mot ca chay that
# chuoi bam - go - cho phan hoi - kiem so, chu khong do chuoi. Dat o day chu
# khong de chay tay: mot ca kiem khong nam trong cong la mot ca kiem se quen.
node vagabond/khung/kiem_thu/hanh_vi/kiem_banh.js
# Chay lai o hai mui gio doi nhau (UTC+14 va UTC-11): bat ca kiem nao lay ngay
# theo UTC trong khi trang lay ngay dia phuong. Codex bat tren PR #223: bo ca
# tung xanh o may UTC nhung hong 7/7 khi may o mui gio da sang ngay khac.
TZ=Pacific/Kiritimati node vagabond/khung/kiem_thu/hanh_vi/kiem_banh.js
TZ=Pacific/Pago_Pago node vagabond/khung/kiem_thu/hanh_vi/kiem_banh.js
# Man tao lenh san xuat (#206, PR #215).
node vagabond/khung/kiem_thu/hanh_vi/kiem_san_xuat_206.js
node vagabond/khung/kiem_thu/hanh_vi/chay_san_xuat.js
node vagabond/khung/kiem_thu/hanh_vi/mac_dinh_phieu_sx.js

# Man "Nhan hang" dieu chuyen noi bo. Truoc 06/09/2026 man nay tu chon lo o
# trinh duyet va giau mat lo qua han, bep bi bao thieu hang trong khi kho con.
node vagabond/khung/kiem_thu/hanh_vi/chay_nhan_hang.js

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
echo " Cong muoi cong doan o day chi chay PHEP THUAN. Ngay 21/08/2026 no"
echo " tra ve 0 trong khi ca tiem khong nhap kho duoc, vi ERPNext tu choi"
echo " cai ma minh dinh vao dong so cai. Chi bo kiem tich hop hoi duoc cau"
echo " do. Doc AGENTS.md muc 6."

node vagabond/khung/kiem_thu/hanh_vi/van_don_237.js

node vagabond/khung/kiem_thu/hanh_vi/thanh_vien_245.cjs
