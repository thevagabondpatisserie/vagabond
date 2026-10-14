"""A1: số dư chọn trước ghi sổ. Chưa thay ca cửa app và tranh chấp bench."""
from vagabond.bo_sao_ke import doc_bo, phan_con
from vagabond.khung.kiem_thu.nen import ca, la, nem


def bo(chu, tien, pe=None):
    return {"chu": chu, "dong": [{"name": "BT", "phan_bo": tien}],
            "chung_tu": [{"doctype": "Payment Entry", "name": pe}] if pe else []}


def loi(pe, tien):
    return {"doctype": "Payment Entry", "name": pe, "tien": tien}


@ca("#595 một sao kê chia hai phiếu, phần giữ chưa ghi sổ cũng tiêu tiền")
def _():
    la("còn 400", phan_con(1000, [], [bo("APP1", 600)], "BT"), 400)
    la("hết", phan_con(1000, [], [bo("APP1", 600), bo("APP2", 400)], "BT"), 0)
    la("retry APP1", phan_con(1000, [], [bo("APP1", 600), bo("APP2", 400)], "BT", "APP1"), 600)


@ca("#595 chuyển phần giữ thành phân bổ lõi không trừ tiền hai lần")
def _():
    bs = [bo("APP1", 600, "PE1")]
    for tien in (0, 200, 600):
        la("còn không đổi", phan_con(1000, [loi("PE1", tien)], bs, "BT"), 400)
        la("retry không tự chặn", phan_con(1000, [loi("PE1", tien)], bs, "BT", "APP1"), 1000)
    la("phiếu thứ hai ghi hết", phan_con(1000, [loi("PE1",600),loi("PE2",400)],
        bs+[bo("APP2",400,"PE2")], "BT"), 0)


@ca("#595 phân bổ ngoài APP vẫn giảm số dư, chứng từ huỷ trả lại phần lõi")
def _():
    la("chứng từ ngoài", phan_con(1000, [loi("PE-OUT",250)], [bo("APP1",600)], "BT"), 150)
    la("huỷ lõi còn giữ đến lúc người bỏ", phan_con(1000, [], [bo("APP1",600,"PE1")], "BT"), 400)
    la("đã bỏ giữ", phan_con(1000, [], [], "BT"), 1000)


@ca("#595 dữ liệu phân bổ hỏng không được biến thành tiền trống")
def _():
    for v in ([], False, 0, '{', {}, {"dong":None,"chung_tu":[]}, {"dong":[],"chung_tu":{}},
              {"dong":[{"name":"BT","phan_bo":"NaN"}],"chung_tu":[]}):
        nem("từ chối bộ hỏng",lambda:doc_bo(v),ValueError)
    la("bộ chưa có",doc_bo(None),{"dong":[],"chung_tu":[]})
    for v in (-1,"NaN","Infinity"):
        nem("lõi không âm hoặc vô hạn",lambda:phan_con(1000,[loi("PE",v)],[],"BT"),ValueError)


@ca("#595 trùng chủ/chứng từ không được cộng lại phần tiền của chính mình")
def _():
    for bs in ([bo("A",500),bo("A",500)], [bo("A",500,"PE"),bo("B",500,"PE")]):
        nem("trùng",lambda:phan_con(1000,[loi("PE",500)],bs,"BT","A"),ValueError)
    nem("trùng dòng lõi",lambda:phan_con(1000,[loi("PE",200),loi("PE",200)],[],"BT"),ValueError)
    b=bo("A",500,"PE"); b["chung_tu"]*=2
    nem("chứng từ trùng trong bộ",lambda:phan_con(1000,[],[b],"BT"),ValueError)


@ca("#595 dữ liệu vượt tiền phải báo lỗi chứ không âm thầm trả 0")
def _():
    for core, bs in (([loi("PE",1100)],[]), ([],[bo("A",1100)]),
                     ([],[bo("A",600),bo("B",500)]), ([loi("PE",600)],[bo("A",500,"PE")])):
        nem("vượt phân bổ",lambda:phan_con(1000,core,bs,"BT"),ValueError)


@ca("#595 tiền lẻ giữ chính xác qua hai bước, không làm tròn để chiếm thêm")
def _():
    la("số lẻ",phan_con("1000.75",[loi("PE","600.25")],[bo("A","600.25","PE")],"BT"),400.5)


@ca("#595 tự đề xuất đúng cả bộ cùng mã APP, không lấy dòng chỉ giống số tiền")
def _():
    from vagabond.bo_sao_ke import de_xuat_bo
    ds = [dict(name="A",tien=450000000,bank_account="MB",chieu="ra",description="CK APP2610019"),
          dict(name="B",tien=264138056,bank_account="MB",chieu="ra",reference_number="APP.26.10.019"),
          dict(name="C",tien=714138056,bank_account="MB",chieu="ra",description="CK APP26100190")]
    kq=de_xuat_bo(ds,"APP.26.10.019",714138056,"MB","ra")
    la("đủ",kq["ket_qua"],"du")
    la("chỉ A B",[d["name"] for d in kq["dong"]],["A","B"])
    la("thiếu",de_xuat_bo(ds[:1],"APP.26.10.019",714138056,"MB","ra")["thieu"],264138056)
    la("không chọn một tổ hợp vừa đủ khi dư mã",de_xuat_bo(ds+[
        dict(ds[0],name="D")],"APP.26.10.019",714138056,"MB","ra")["ket_qua"],"thua")


@ca("#595 bộ cùng mã sai chiều/tài khoản/đã giữ không được tự coi đủ")
def _():
    from vagabond.bo_sao_ke import de_xuat_bo
    a=dict(name="A",tien=600,bank_account="MB",chieu="ra",description="TTNB-26-10-00001")
    b=dict(a,name="B",tien=400)
    for doi in ({"bank_account":"ACB"},{"chieu":"vao"},{"chu_cu":"APP-CU"},{"con_lai":0}):
        kq=de_xuat_bo([a,dict(b,**doi)],"TTNB-26-10-00001",1000,"MB","ra")
        la("lỗi cả bộ",kq["ket_qua"],"loi")


@ca("#476 cửa chọn bộ dùng tổng máy chủ, khóa BT theo tên rồi mới đọc phần còn")
def _():
    from unittest.mock import patch
    import frappe
    from vagabond import bo_sao_ke_db as bs
    doc=frappe._dict(doctype="Vagabond Ho So TT",name="APP",vgb_bo_sao_ke=None)
    ds=[dict(name="B",phan_bo=40),dict(name="A",phan_bo=60)]
    def giao(dt,ma,**kw):
        return frappe._dict(name=ma,docstatus=1,currency="VND",withdrawal=60 if ma=="A" else 40,
            deposit=0,bank_account="MB",date="2026-10-14",reference_number=ma)
    def phan(g,d,khoa=False):
        la("current read",khoa,True)
        return g.withdrawal
    with patch.object(frappe.db,"get_value",return_value="TEN") as lock, patch.object(frappe,"get_doc",side_effect=giao), \
            patch.object(bs,"con_lai",side_effect=phan), patch.object(bs,"luu") as luu:
        g=bs.chon(doc,ds,100,"ra",lambda g:"",ghi=True)
        la("khóa phiếu rồi A B",[x.args[:2] for x in lock.call_args_list],[(doc.doctype,"APP"),("Bank Transaction","A"),("Bank Transaction","B")])
        la("tổng đúng",g.withdrawal,100)
        la("lưu một bộ",luu.call_count,1)
        luu.reset_mock()
        nem("không tin payload đủ nhưng tổng phiếu khác",lambda:bs.chon(doc,ds,101,"ra",lambda g:"",ghi=True))
        la("không ghi bộ thiếu",luu.call_count,0)


@ca("#476 cửa bộ kiểm nguồn, chiều, tài khoản, khả dụng trước lưu")
def _():
    from unittest.mock import patch
    import frappe
    from vagabond import bo_sao_ke_db as bs
    doc=frappe._dict(doctype="Vagabond Ho So TT",name="APP",vgb_bo_sao_ke=None)
    a=frappe._dict(name="A",docstatus=1,currency="VND",withdrawal=60,deposit=0,bank_account="MB",date="2026-10-14",reference_number="A")
    b=frappe._dict(a,name="B",withdrawal=40)
    ds=[dict(name="A",phan_bo=60),dict(name="B",phan_bo=40)]
    with patch.object(frappe.db,"get_value",return_value="TEN"), patch.object(frappe,"get_doc",side_effect=lambda dt,ma,**kw:a if ma=="A" else b), \
            patch.object(bs,"con_lai",return_value=100) as con, patch.object(bs,"luu") as luu:
        for cot,v in (("docstatus",0),("currency","USD"),("bank_account","ACB"),("deposit",40)):
            cu=b[cot];b[cot]=v
            nem(cot,lambda:bs.chon(doc,ds,100,"ra",lambda g:"",ghi=True));b[cot]=cu
        nem("nguồn bị từ chối",lambda:bs.chon(doc,ds,100,"ra",lambda g:"Nguồn sai",ghi=True))
        con.return_value=20
        nem("mới bị giữ bởi người khác",lambda:bs.chon(doc,ds,100,"ra",lambda g:"",ghi=True))
        la("không lượt sai nào ghi",luu.call_count,0)


@ca("#476 ghi Desk không được giả phần giữ dù ô read_only bị đưa vào payload")
def _():
    from unittest.mock import patch
    import frappe
    from vagabond import bo_sao_ke_db as bs
    class D(dict):
        doctype="Vagabond Ho So TT";name="APP"
        def is_new(self):return False
        def set(self,k,v):self[k]=v
    doc=D(vgb_bo_sao_ke='giả')
    with patch.object(frappe.db,"get_value",return_value='bộ đã kiểm'):
        bs.bao_ve(doc)
    la("giữ bản máy chủ",doc[bs.O_BO],'bộ đã kiểm')


@ca("#476 bỏ giữ lưu NULL để cửa một dòng cũ vẫn nhận đúng chủ")
def _():
    from unittest.mock import patch
    import frappe
    from vagabond import bo_sao_ke_db as bs
    class D(dict):
        doctype="Vagabond Ho So TT";name="APP"
        def set(self,k,v):self[k]=v
    d=D()
    with patch.object(frappe.db,"set_value") as ghi:
        bs.luu(d,[])
        la("NULL",ghi.call_args.args[-1],None)
        la("đọc lại không còn giữ",bs.doc_hien_tai(d),dict(dong=[],chung_tu=[]))
