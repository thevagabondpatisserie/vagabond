"""#245: dữ liệu editor không thể mang mã chạy hoặc ghi nhầm trường giá."""
import copy
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.noi_dung_web import chuan_hoa, MAC_DINH


def bi_chan(nd):
    try:
        chuan_hoa(nd)
    except (ValueError, TypeError):
        return True
    return False


@ca("Web editor: chỉ nhận khối nội dung, không nhận giá hay mã thực thi")
def thu_du_lieu_la():
    for truong in ("gia", "html", "javascript", "onerror"):
        nd = copy.deepcopy(MAC_DINH)
        nd["khoi"][-1][truong] = "1"
        dung(truong, bi_chan(nd))


@ca("Web editor: chặn URL thực thi, URL lược scheme và ảnh riêng tư")
def thu_url():
    for url in ("javascript:alert(1)", "data:text/html,hi", "//evil.com/a", "/\\evil.com/a", "https://a.com/\nhi", "http://a.com", "https://u:p@a.com"):
        for truong in ("anh", "lien_ket"):
            nd = copy.deepcopy(MAC_DINH)
            nd["khoi"][-1][truong] = url
            dung(url, bi_chan(nd))
    for url in ("/private/files/a.jpg", "/files/a.svg"):
        nd = copy.deepcopy(MAC_DINH)
        nd["khoi"][-1]["anh"] = url
        dung(url, bi_chan(nd))


@ca("Web editor: giữ khối ẩn, thứ tự, tiếng Việt và không sửa dữ liệu nguồn")
def thu_giu_noi_dung():
    nd = copy.deepcopy(MAC_DINH)
    nd["khoi"].reverse()
    nd["khoi"][-1]["hien"] = False
    ra = chuan_hoa(nd)
    la("Giữ nguyên nội dung", ra, nd)
    ra["khoi"][-1]["tieu_de"] = "Đã sửa"
    dung("Không sửa dữ liệu gốc", nd["khoi"][-1]["tieu_de"] != "Đã sửa")


@ca("Web editor: chặn mã trùng, quá nhiều khối, kiểu dữ liệu và chuỗi quá dài")
def thu_gioi_han():
    for nd in ({"khoi": MAC_DINH["khoi"] * 2}, {"khoi": MAC_DINH["khoi"] * 16}, {"khoi": {}}, {"khoi": [None]}, {"khoi": [], "gia": 1}):
        dung("Chặn cấu trúc sai", bi_chan(nd))
    for truong, v in (("hien", "false"), ("noi_dung", "a" * 4001), ("id", "<script>"), ("loai", "html"), ("anh", 123)):
        nd = copy.deepcopy(MAC_DINH); nd["khoi"][-1][truong] = v
        dung("Chặn trường sai: " + truong, bi_chan(nd))


@ca("Web editor: vị trí khối là khe trong trang order, không nhận selector tùy ý")
def thu_vi_tri():
    nd = copy.deepcopy(MAC_DINH)
    for vi_tri in ('dau_trang', 'today', 'order', 'store', 'season', 'cuoi_trang'):
        nd['khoi'][-1]['vi_tri'] = vi_tri
        la('Giữ vị trí '+vi_tri, chuan_hoa(nd)['khoi'][-1]['vi_tri'], vi_tri)
    nd['khoi'][-1]['vi_tri'] = '#checkout'
    dung('Chặn khe tùy ý', bi_chan(nd))
