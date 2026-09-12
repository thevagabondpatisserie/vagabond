"""#245: không nhận lịch ngoài cấu hình hoặc số khách/điện thoại không hợp lệ."""
import ast
from datetime import datetime
from pathlib import Path
from vagabond.khung.kiem_thu.nen import ca, dung, la

s = Path(__file__).resolve().parents[2] / 'dat_ban.py'
cay = ast.parse(s.read_text())
phan = []
for nut in cay.body:
    if isinstance(nut, ast.Import) and any(x.name == 'frappe' for x in nut.names):
        break
    phan.append(nut)
ns = {}; exec(compile(ast.Module(body=phan, type_ignores=[]), str(s), 'exec'), ns)
chuan = ns['chuan_hoa']
cau = dict(bat=True, co_so='TCV', khung_gio=['10:00','14:00'], toi_da_khach=8, toi_da_ngay=30)
nd = dict(ten='Khách kiểm thử',sdt='0912345678',co_so='TCV',ngay='2026-09-10',gio='10:00',so_khach=2,ghi_chu='')
luc = datetime(2026,9,9,9)

@ca('Đặt bàn web: chuẩn hóa số và giữ nguyên yêu cầu nguồn')
def thu_dung():
    moi = dict(nd, sdt='+84 912 345 678')
    ra = chuan(moi,cau,luc)
    la('Chuẩn hóa số điện thoại',ra['sdt'],'0912345678')
    la('Không sửa đầu vào',moi['sdt'],'+84 912 345 678')

@ca('Đặt bàn web: chặn lịch cũ, quá xa, ngoài giờ và ngoài cơ sở')
def thu_chan():
    for ten,gia in [('ngay','2026-09-08'),('ngay','2026-12-10'),('gio','03:00'),('co_so','SALES'),('so_khach',0),('so_khach',9),('so_khach',2.5),('sdt','090'),('ten',''),('ghi_chu','x'*1001)]:
        chan = False
        try: chuan(dict(nd,**{ten:gia}),cau,luc)
        except ValueError: chan = True
        dung('Chặn '+ten+' '+str(gia)[:30],chan)
    chan=False
    try: chuan(nd,dict(cau,bat=False),luc)
    except ValueError: chan=True
    dung('Tắt lịch không nhận yêu cầu',chan)

@ca('Đặt bàn web: đúng mốc trước một giờ vẫn phải chọn giờ muộn hơn')
def thu_moc():
    chan=False
    try: chuan(dict(nd,ngay='2026-09-09'),cau,luc)
    except ValueError: chan=True
    dung('Chặn ngay sát hạn nhận',chan)
