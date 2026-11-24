"""Dữ liệu thử dựng bằng CHÍNH hàm máy chủ của app trên bản giả lập Frappe (nen.gia_lap), để công cụ
rà giao diện (ra_muc.cjs) có lời đáp đúng hình dạng thay vì "rỗng". Không nối site, không đọc dữ liệu
thật: bản giả lập không có bản ghi, nên danh sách thường rỗng, cài đặt lấy giá trị mặc định trong mã.
Bỏ qua kiểm quyền (hàm tên có kiem_quyen). Hàm nào lỗi trên bản giả lập thì ghi lỗi, không đoán.

    python3 cong_cu/ui_b/du_lieu_that.py <gốc repo> '["vagabond.ban_hang.cau_hinh_ban_hang", ...]'
"""
import sys, json, importlib
sys.path.insert(0, sys.argv[1])
from vagabond.khung.kiem_thu import nen
nen.gia_lap()
ra = {}
for ten in json.loads(sys.argv[2]):
    mo, ham = ten.rsplit('.', 1)
    try:
        m = importlib.import_module(mo)
        for k in dir(m):
            if 'kiem_quyen' in k or k.startswith('_can_quyen') or k.startswith('_chan_'):
                try: setattr(m, k, lambda *a, **kw: None)
                except Exception: pass
        f = getattr(m, ham)
        f = getattr(f, '__wrapped__', f)
        r = f()
        json.dumps(r, default=str)
        ra[ten] = {'ok': 1, 'message': r}
    except Exception as e:
        ra[ten] = {'ok': 0, 'loi': type(e).__name__ + ': ' + str(e)[:120]}
sys.stdout.write(json.dumps(ra, ensure_ascii=False, default=str))
