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
    with patch.object(frappe.db,"get_value",side_effect=lambda dt,n,f,**kw: None if f==bs.O_BO else n) as lock, patch.object(frappe,"get_doc",side_effect=giao), \
            patch.object(bs,"con_lai",side_effect=phan), patch.object(bs,"luu") as luu:
        g=bs.chon(doc,ds,100,"ra",lambda g:"",ghi=True)
        la("khóa A B trước phiếu",[x.args[:2] for x in lock.call_args_list if x.kwargs.get("for_update")],[("Bank Transaction","A"),("Bank Transaction","B"),(doc.doctype,"APP")])
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
    with patch.object(frappe.db,"get_value",side_effect=lambda dt,n,f,**kw: None if f==bs.O_BO else n), patch.object(frappe,"get_doc",side_effect=lambda dt,ma,**kw:a if ma=="A" else b), \
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


@ca("#476 lỗi ghi bằng chứng sau giữ tiền phải hoàn lại phần giữ trước khi tự dò tiếp")
def _():
    from unittest.mock import patch, Mock
    import frappe
    from vagabond import bo_sao_ke_luong as bl, doi_soat_sepay as dss
    d=frappe._dict(doctype="Vagabond De Nghi Chi",name="TTNB",trang_thai="Cho chi",vgb_bo_sao_ke=None)
    d.add_comment=Mock(side_effect=frappe.ValidationError("Lỗi ghi bằng chứng"))
    b=dict(doctype=d.doctype,truong_gd="ma_giao_dich",chieu="ra",so_tien=lambda d:100)
    g=frappe._dict(name="BT",withdrawal=100)
    state={"giu":False}
    def chon(*a,**kw):state["giu"]=True;return g
    def rollback(**kw):state["giu"]=False
    with patch.object(dss,"kiem_quyen_luong",return_value=b),patch.object(frappe,"get_doc",return_value=d), \
            patch.object(frappe,"generate_hash",return_value="test476",create=True), \
            patch.object(frappe.db,"savepoint",create=True),patch.object(frappe.db,"rollback",side_effect=rollback,create=True) as lui, \
            patch.object(frappe.db,"commit",create=True) as commit,patch.object(frappe.db,"set_value"), \
            patch.object(bl.bs,"chon",side_effect=chon):
        nem("vẫn trả lỗi",lambda:bl.khop("ttnb","TTNB",[dict(name="BT",phan_bo=100)]),frappe.ValidationError)
        la("không giữ mồ côi",state["giu"],False)
        la("rollback đúng phạm vi",lui.call_args.kwargs,{"save_point":"bo_sao_ke_test476"})
        la("không commit lỗi",commit.call_count,0)


@ca("#476 chờ đối chiếu sau dựa trên phân bổ lõi, không dựa trên mã gõ hoặc lý do đã lưu")
def _():
    from unittest.mock import patch
    import frappe
    from vagabond import ho_so_tt as hs
    from vagabond.chip_ho_so_tt import chip_cua_dong
    d=frappe._dict(name="APP",trang_thai=hs.TT_DA_TRA,vgb_tt_ly_do_som="SePay chậm",dong=[dict(so_tien=100)],da_tam_ung=0,con_lai=100,ma_giao_dich="MA-KHONG-DU")
    with patch.object(hs,"_do_chinh_xac",return_value=2),patch.object(hs,"_but_toan_cua_ho_so",return_value=[dict(doctype="Payment Entry",name="PE")]), \
            patch.object(frappe,"get_all",return_value=[frappe._dict(allocated_amount=60)]) as rows:
        la("mã có nhưng còn thiếu",hs._cho_doi_chieu_sau(d),True)
        rows.return_value=[frappe._dict(allocated_amount=60),frappe._dict(allocated_amount=40)]
        la("đủ lõi mới hết chờ",hs._cho_doi_chieu_sau(d),False)
        d.vgb_tt_ly_do_som=""
        la("không tự nhận là ngoại lệ",hs._cho_doi_chieu_sau(d),False)
    la("chip độc lập với trạng thái duyệt","cho_doi_chieu_sau" in chip_cua_dong(dict(trang_thai=hs.TT_DA_TRA,cho_doi_chieu_sau=True)),True)
    la("hủy không giục đối chiếu",chip_cua_dong(dict(trang_thai="Huy",cho_doi_chieu_sau=True)),[])


@ca("#476 APP có dòng đúng tổng cộng lệnh cùng mã thì không tự bỏ qua phần dư")
def _():
    from unittest.mock import patch
    import frappe
    from vagabond import doi_chieu_app as dc
    d=frappe._dict(name="APP.26.10.019",vgb_bo_sao_ke=None,ma_giao_dich=None)
    ds=[frappe._dict(name="A",bank_account="MB",withdrawal=100,description=d.name,reference_number=""),
        frappe._dict(name="B",bank_account="MB",withdrawal=20,description=d.name,reference_number="")]
    def rows(dt,**kw):return ["MB"] if dt=="Bank Account" else ds
    with patch.object(dc,"_nguon",return_value=("CTY","112",100)),patch.object(frappe,"get_all",side_effect=rows), \
            patch.object(frappe,"get_doc",side_effect=lambda dt,n:next(r for r in ds if r.name==n)), \
            patch("vagabond.bo_sao_ke_db.con_lai",side_effect=lambda g,*a,**k:g.withdrawal), \
            patch("vagabond.bo_sao_ke_db.chon") as chon:
        la("không tự chọn dòng A rồi coi đủ",dc.chon(d),None)
        la("không đi tiếp cửa ghi một dòng",chon.call_count,0)


@ca("#476 gọi phân bổ lõi theo phần giữ, không đưa toàn bộ số dư vào lượt của một phiếu")
def _():
    from unittest.mock import patch
    import frappe
    from vagabond import bo_sao_ke_db as bs
    d=frappe._dict(doctype="Vagabond Ho So TT",name="APP",vgb_bo_sao_ke=None)
    caps=[];links={}
    class G:
        def __init__(self,name):self.name=name;self.unallocated_amount=100;self.flags=frappe._dict()
        def add_payment_entries(self,rows):pass
        def allocate_payment_entries(self):
            # Hợp đồng của lõi: số dư tại đầu hàm là hạn mức lượt này.
            caps.append(self.unallocated_amount)
            links[self.name]=[frappe._dict(doctype="Payment Entry",name="PE",tien=self.unallocated_amount)]
        def save(self,**kw):pass
    gs=[G("A"),G("B")]
    bo=frappe._dict(flags=frappe._dict(bo_sao_ke=gs,dong=[dict(name="A",phan_bo=40),dict(name="B",phan_bo=40)]))
    with patch.object(frappe.db,"get_value",return_value=1),patch.object(bs,"luu"), \
            patch.object(bs,"_loi",side_effect=lambda name:links.get(name,[])):
        bs.noi(d,bo,[dict(doctype="Payment Entry",name="PE")])
    la("chỉ cấp 40 mỗi lần dù BT còn 100",caps,[40,40])


@ca("#476 tự dò không ghép nguồn 141 thiếu chủ vào lệnh công ty cùng mã")
def _():
    from unittest.mock import patch
    import frappe
    from vagabond import bo_sao_ke_luong as bl, doi_soat_sepay as dss
    b=dict(doctype="Vagabond De Nghi Chi",ma_do=lambda d:"TTNB-26-10-00001",chieu="ra")
    rows=[dict(name="A",bank_account="MB-THIEU-CHU",description="TTNB-26-10-00001",withdrawal=100),
        dict(name="B",bank_account="MB-CTY",description="TTNB-26-10-00001",withdrawal=100)]
    with patch.object(dss,"_ban",return_value=b),patch.object(frappe,"get_doc",side_effect=lambda dt,ma:frappe._dict(rows[0]) if dt=='Bank Transaction' else {}), \
            patch.object(dss,"_loi_giao_dich",side_effect=lambda b,r:"Sai nguồn chi" if r["bank_account"]=="MB-THIEU-CHU" else ""), \
            patch.object(dss,"ly_do_tai_khoan_sepay",return_value=""),patch.object(bl,"_khop") as khop:
        k=bl.tu_dong_mot("ttnb","TTNB",rows)
        la("không nhận bộ nguồn sai",k['ok'],0)
        la("nêu nguồn sai để người kiểm",k['vi_sao'],'Sai nguồn chi')
        la("không ghép sai bộ 200",khop.call_count,0)


@ca('#476 bỏ bộ: quyền, APP liên quan và bút toán sống đều chặn trước khi nhả')
def _():
    from unittest.mock import patch
    import frappe
    from vagabond import bo_sao_ke_luong as bl, doi_soat_sepay as dss
    import json
    d=frappe._dict(doctype='Vagabond De Nghi Chi',name='T',trang_thai='Da chi',ho_so_tt='',
        vgb_bo_sao_ke=json.dumps({'dong':[{'name':'A','phan_bo':60},{'name':'B','phan_bo':40}],
            'chung_tu':[{'doctype':'Payment Entry','name':'PE'}]}),add_comment=lambda *a:None)
    b={'doctype':d.doctype,'truong_gd':'ma_gd'}
    with patch.object(dss,'kiem_quyen_luong',return_value=b),patch.object(frappe,'get_doc',return_value=d), \
         patch.object(bl,'duoc_bo',return_value=False) as quyen,patch.object(frappe.db,'get_value',return_value=1) as status, \
         patch.object(bl.bs,'luu') as luu,patch.object(bl.bs,'_loi',return_value=[]) as noi,patch.object(frappe.db,'set_value') as ghi:
        nem('chặn quyền',lambda:bl.bo('ttnb','T'),frappe.ValidationError)
        quyen.return_value=True;d.ho_so_tt='APP'
        nem('chặn APP',lambda:bl.bo('ttnb','T'),frappe.ValidationError)
        d.ho_so_tt='';nem('chặn bút toán',lambda:bl.bo('ttnb','T'),frappe.ValidationError)
        status.return_value=2;noi.return_value=[frappe._dict(doctype='Payment Entry',name='PE')]
        nem('chặn liên kết chưa gỡ',lambda:bl.bo('ttnb','T'),frappe.ValidationError)
        la('chưa nhả',luu.call_count,0);la('chưa đổi phiếu',ghi.call_count,0)
        noi.return_value=[];bl.bo('ttnb','T')
        la('bỏ cả bộ',luu.call_args.args[1],[])
        la('về đúng bước',ghi.call_args.args[2]['trang_thai'],'Hoan tat')


@ca('#476 APP dẫn chứng TTNB chỉ bỏ chiếm toàn BT khi đúng chủ và đúng dòng')
def _():
    import json
    import frappe
    from unittest.mock import patch
    from vagabond import doi_chieu_app as dc, doi_soat_sepay as dss
    g=frappe._dict(name='BT',reference_number='FT',flags=frappe._dict(for_update=True))
    d=frappe._dict(name='TTNB-MOI',doctype='Vagabond De Nghi Chi')
    def chu(owner='APP-CU',bank='BT',co_bo=True,bo_moi=True):
        meta=json.dumps({'dong':[dict(name=bank,phan_bo=60)],'chung_tu':[]}) if co_bo else ''
        with patch.object(frappe.db,'sql',side_effect=[[],[('APP-CU','TTNB-CU',meta,owner)]]), \
             patch.object(dss,'nap_so'),patch.object(dss,'MO_DUN_KHAI',()),patch.object(dss,'_SO',{}):
            return dc._chu_khac(g,d,bo=bo_moi)
    la('APP chỉ dẫn chứng phần đã giữ',chu(),'')
    la('sai chủ không bỏ qua',chu(owner='APP-KHAC'),'APP-CU')
    la('sai giao dịch không bỏ qua',chu(bank='BT-KHAC'),'APP-CU')
    la('liên kết cũ không bộ vẫn độc quyền',chu(co_bo=False),'APP-CU')
    la('cửa cũ không kiểm phần vẫn chặn',chu(bo_moi=False),'APP-CU')


@ca('#476 APP từ chối hoặc hủy nhả bộ dù mã giao dịch không đổi')
def _():
    import frappe
    from unittest.mock import patch
    from vagabond import doi_chieu_app as dc, bo_sao_ke_db as bs, ho_so_tt as hs
    class Doc(frappe._dict):
        def get_doc_before_save(self):return frappe._dict(trang_thai='Da duyet',ma_giao_dich='BT')
        def add_comment(self,*a):pass
    for state in ('Tu choi','Huy'):
        d=Doc(name='APP',trang_thai=state,ma_giao_dich='BT')
        with patch.object(bs,'doc_hien_tai',return_value={'dong':[dict(name='BT',phan_bo=100)]}), \
             patch.object(dc,'_kiem_bo') as bo,patch.object(hs,'_kiem') as quyen:
            dc.kiem_luu(d)
            la('nhả đúng bộ',bo.call_args.args if bo.called else None,(d,'BT'));la('xóa mã cùng lượt',d.ma_giao_dich,'')
            la('qua quyền tương ứng',quyen.call_count,1)
        d.ma_giao_dich='BT'
        with patch.object(bs,'doc_hien_tai',return_value={'dong':[dict(name='BT',phan_bo=100)]}), \
             patch.object(dc,'_kiem_bo',side_effect=frappe.ValidationError('bút toán sống')),patch.object(hs,'_kiem'):
            nem('chưa nhả khi còn bút toán',lambda:dc.kiem_luu(d),frappe.ValidationError)
            la('mã còn nguyên',d.ma_giao_dich,'BT')


@ca("#476 P2 chủ giữ đọc bằng khóa chính BT, không quét bảng phiếu")
def _():
    import json
    from unittest.mock import patch
    import frappe
    from vagabond import bo_sao_ke_db as bs
    plan=bo("Vagabond Ho So TT/APP",600)
    chu=plan.pop("chu")
    with patch.object(frappe.db,"get_value",return_value=json.dumps({chu:plan})) as doc, \
            patch.object(frappe.db,"sql",side_effect=AssertionError("Không được quét bảng phiếu")):
        la("chủ đúng",bs._cac_bo("BT",khoa=True),[dict(plan,chu=chu)])
        la("đúng khóa chính",doc.call_args.args,("Bank Transaction","BT",bs.O_CHU))
        la("current read",doc.call_args.kwargs,{"for_update":True})


@ca("#476 P2 bộ đổi trong khi đợi khóa phải thử lại, không xin BT mới sau phiếu")
def _():
    import json
    from unittest.mock import patch
    import frappe
    from vagabond import bo_sao_ke_db as bs
    cu=json.dumps(dict(dong=[dict(name="B",phan_bo=10)],chung_tu=[]))
    moi=json.dumps(dict(dong=[dict(name="A",phan_bo=10)],chung_tu=[]))
    def doc(dt,n,f,**kw):
        return n if dt=="Bank Transaction" else moi if kw.get("for_update") else cu
    with patch.object(frappe.db,"get_value",side_effect=doc) as lay:
        nem("bộ thay đổi",lambda:bs.khoa_phieu("Vagabond Ho So TT","APP"))
        la("chỉ khóa B trước phiếu",[(c.args[0],c.args[1]) for c in lay.call_args_list if c.kwargs.get("for_update")],
            [("Bank Transaction","B"),("Vagabond Ho So TT","APP")])


@ca("#476 P2 sao kê không có chủ giữ thoát sớm, payload nháp không giả chủ")
def _():
    from unittest.mock import patch
    import frappe
    from vagabond import bo_sao_ke_db as bs
    class D(dict):
        name="BT"
        def set(self,k,v):self[k]=v
        def is_new(self):return self.get("moi",False)
    doc=D()
    with patch.object(frappe.db,"get_value",return_value=None), \
            patch.object(bs,"_loi",side_effect=AssertionError("BT trống không đọc phân bổ")):
        bs.bao_ve_bt(doc)
        la("trống",doc[bs.O_CHU],None)
    for moi in (True,False):
        doc=D(moi=moi,vgb_chu_bo_sao_ke="giả")
        with patch.object(frappe.db,"get_value",return_value="chủ thật"):
            bs.bao_ve_chu_bt(doc)
        la("nguồn máy chủ",doc[bs.O_CHU],None if moi else "chủ thật")


@ca("#476 P2 ghi sổ và hủy PE hoàn tiền khóa bộ trước khóa Document")
def _():
    import frappe
    from unittest.mock import patch
    from vagabond import bo_sao_ke_document as mod
    vet=[]
    class Goc:
        name='PE'
        flags={'for_update':True}
        def get(self,k):return 'HT-GIA'
        def is_new(self):return False
        def _save(self,*a,**kw):vet.append('luu-loi')
        def load_from_db(self):vet.append('doc-loi')
    class D(mod.KhoaBoHoanTien,Goc):pass
    with patch.object(frappe.db,'get_value',return_value='HT-THAT'), \
            patch.object(mod,'khoa_phieu',side_effect=lambda dt,ma:vet.append((dt,ma))):
        D().load_from_db();D()._save()
    la('khóa trước cả hai cửa',vet,[('Vagabond Hoan Tien','HT-THAT'),'doc-loi',('Vagabond Hoan Tien','HT-THAT'),'luu-loi'])


@ca('#476 ghi từng PE tiền vào: chia qua hai BT, giữ PE nháp và retry không nhân đôi')
def _():
    from unittest.mock import patch
    import json
    import frappe
    from vagabond import bo_sao_ke_db as bs
    doc=frappe._dict(doctype='Vagabond Cong No',name='CN',vgb_bo_sao_ke='payload không được tin')
    b={'dong':[dict(name='A',phan_bo=40),dict(name='B',phan_bo=60)],
       'chung_tu':[dict(doctype='Payment Entry',name=n) for n in ('PE1','PE2')]}
    ps={n:frappe._dict(name=n,docstatus=1 if n=='PE1' else 0,payment_type='Receive',
        party_type='Customer',company='CTY',paid_to='112',paid_to_account_currency='VND',received_amount=t)
        for n,t in [('PE1',60),('PE2',40)]}
    links={'A':[],'B':[]};calls=[]
    gs={}
    for ma,t in [('A',40),('B',60)]:
        g=frappe._dict(name=ma,bank_account='BA',docstatus=1,currency='VND',deposit=t+30,withdrawal=0,
            unallocated_amount=t+30,flags=frappe._dict())
        def add(rows,g=g):g.moi=rows[0]['payment_name'];calls.append((g.name,g.moi))
        def allocate(g=g):
            used=sum(r.tien for rows in links.values() for r in rows if r.name==g.moi)
            lay=min(g.unallocated_amount,ps[g.moi].received_amount-used)
            if lay>0:links[g.name].append(frappe._dict(doctype='Payment Entry',name=g.moi,tien=lay))
            g.unallocated_amount=g.deposit-sum(r.tien for r in links[g.name])
        g.add_payment_entries=add;g.allocate_payment_entries=allocate;g.save=lambda **kw:None
        gs[ma]=g
    def value(dt,name,field,**kw):
        if dt=='Bank Account':return dict(account='112',company='CTY',is_company_account=1,disabled=0)
        return json.dumps(b)
    with patch.object(bs,'khoa_phieu'),patch.object(frappe.db,'get_value',side_effect=value), \
            patch.object(frappe,'get_doc',side_effect=lambda dt,ma,**kw:ps[ma] if dt=='Payment Entry' else gs[ma]), \
            patch.object(bs,'_loi',side_effect=lambda ma:links[ma]):
        la('PE1 đủ60',bs.noi_tung_phieu_thu(doc,'PE1')['tien'],60)
        la('A40 B20',[[r.tien for r in links[ma]] for ma in ('A','B')],[[40],[20]])
        la('PE2 còn nháp',ps['PE2'].docstatus,0)
        la('PE1 retry',bs.noi_tung_phieu_thu(doc,'PE1')['tien'],60)
        la('retry không thêm lõi',len(calls),2)
        nem('nháp không được nối',lambda:bs.noi_tung_phieu_thu(doc,'PE2'),frappe.ValidationError)
        ps['PE2'].docstatus=1
        la('PE2 đủ40',bs.noi_tung_phieu_thu(doc,'PE2')['tien'],40)
        la('B đủ60',sum(r.tien for r in links['B']),60)
        nem('PE ngoài bộ bị chặn',lambda:bs.noi_tung_phieu_thu(doc,'PE-OUT'),frappe.ValidationError)
        ps['PE2'].paid_to='KHAC'
        nem('không đổi tài khoản',lambda:bs.noi_tung_phieu_thu(doc,'PE2'),frappe.ValidationError)


@ca('#476 chủ PE từ DB: không tin payload, bộ thiếu PE phải lỗi, khóa trước đọc bộ')
def _():
    import frappe,json
    from unittest.mock import patch
    from vagabond import bo_sao_ke_thu as m
    b={'dong':[dict(name='BT',phan_bo=100)],'chung_tu':[dict(doctype='Payment Entry',name='PE')]}
    vet=[]
    def value(dt,ma,f,**kw):
        vet.append((dt,kw.get('for_update',False)))
        return 'CN' if dt=='Payment Entry' else json.dumps(b)
    with patch.object(frappe.db,'get_value',side_effect=value),patch.object(m.bs,'khoa_phieu',side_effect=lambda *a:vet.append('khoa')):
        la('chủ DB',m.chu('PE',khoa=True),'CN')
        la('khóa trước đọc metadata',vet,[('Payment Entry',False),'khoa',('Vagabond Cong No',True)])
        nem('PE ngoài CT không tin link riêng',lambda:m.chu('PE-GIA'),frappe.ValidationError)
    class D(dict):
        name='PE'
        def is_new(self):return True
        def set(self,k,v):self[k]=v
    d=D(vgb_bo_cong_no='CN-GIA')
    with patch.object(m,'chu',side_effect=AssertionError('phiếu mới không lấy chủ payload')):
        m.bao_ve(d)
    la('bỏ chủ giả',d[m.O_CHU],None)


@ca('#476 bộ thu khóa trước cả load PE và save, không dựa cờ máy khách')
def _():
    from unittest.mock import patch
    from vagabond.bo_sao_ke_document import KhoaBoThu
    from vagabond import bo_sao_ke_thu as m
    import frappe
    vet=[]
    class Goc:
        name='PE';flags={'for_update':True}
        def get(self,k):return None
        def is_new(self):return False
        def load_from_db(self):vet.append('core-load')
        def _save(self,*a,**k):vet.append('core-save')
    class D(KhoaBoThu,Goc):pass
    with patch.object(m,'chu',side_effect=lambda ma,khoa=False:vet.append((ma,khoa))), patch.object(frappe,'get_all',return_value=[]):
        D().load_from_db();D()._save()
    la('đủ hai cửa',vet,[('PE',True),'core-load',('PE',True),'core-save'])


@ca('#476 PE thuộc bộ không sửa khách, hóa đơn, tiền bằng payload trực tiếp')
def _():
    import frappe
    from unittest.mock import patch
    from vagabond import bo_sao_ke_thu as m
    class D(frappe._dict):
        def is_new(self):return False
        def set(self,k,v):self[k]=v
        def get_doc_before_save(self):return cu
    cu=D(name='PE',party='KH1',received_amount=100,
        references=[frappe._dict(reference_doctype='Sales Invoice',reference_name='SI1',allocated_amount=100)])
    with patch.object(m,'chu',return_value='CN-THAT'):
        d=D(cu);d[m.O_CHU]='CN-GIA';m.bao_ve(d)
        la('chỉ chủ DB',d[m.O_CHU],'CN-THAT')
        for k,v in [('party','KH2'),('received_amount',200),('references',[
                frappe._dict(reference_doctype='Sales Invoice',reference_name='SI2',allocated_amount=100)])]:
            d=D(cu);d[k]=v
            nem('không đổi '+k,lambda:m.bao_ve(d),frappe.ValidationError)


@ca('#476 cửa bộ vẫn thấy chủ công nợ cũ nhiều mã, không chiếm lại cả bộ mới')
def _():
    import frappe
    from unittest.mock import patch
    from vagabond import doi_soat_sepay as dss, bo_sao_ke_db as bs
    so={'cong_no':{'doctype':'Vagabond Cong No','truong_gd':'ma_gd','ten_man':'công nợ','loc_chiem':{}}}
    def ds(dt,**kw):
        if dt=='Vagabond Cong No':
            return [frappe._dict(name='CU',ma_gd='BT1\nREF1',vgb_bo_sao_ke=None),
                    frappe._dict(name='MOI',ma_gd='BT2',vgb_bo_sao_ke='đã có giữ ở BT')]
        return []
    with patch.object(dss,'_SO',so),patch.object(dss,'nap_so'),patch.object(frappe,'get_all',side_effect=ds), \
            patch.object(bs,'_cac_bo',side_effect=AssertionError('phần giữ được kiểm riêng bằng con_lai')):
        r=dss.chu_cua_giao_dich(['BT1','BT2'],cho_bo=True)
        la('cũ nhiều mã vẫn giữ BT1',r,{'BT1':'công nợ CU'})
    with patch.object(dss,'nap_so',side_effect=RuntimeError('registry lỗi')):
        nem('cửa ghi không nuốt lỗi đọc chủ',lambda:dss.chu_cua_giao_dich(['BT'],cho_bo=True),RuntimeError)


@ca('#476 công nợ kỳ mới không chọn lại phần giữ của kỳ trước')
def _():
    import frappe
    from unittest.mock import patch
    from vagabond import bo_sao_ke_thu as m
    d=frappe._dict(name='CN',tong_tien=100,da_thu=60)
    k={'rows':[{'name':'A'},{'name':'B','dung_duoc':0,'vi_sao_khong':'Sai chiều tiền'}]}
    with patch.object(m.bs,'doc_hien_tai',return_value={'dong':[{'name':'A','phan_bo':60}]}), \
            patch.object(frappe,'get_doc',side_effect=lambda dt,ma:frappe._dict(name=ma)), \
            patch.object(m,'kiem_nguon',return_value=''),patch.object(m.bs,'con_lai',return_value=100):
        r=m.ung_vien(d,k)
    la('chỉ còn thu40',r['so_tien'],40)
    la('A giữ60 không được lấy lại',r['rows'][0]['con_lai'],40)
    la('B chưa dùng còn100',r['rows'][1]['con_lai'],100)
    la('màn nhiều dòng',r['chon_bo'],1)

    la('không xóa lỗi nguồn cũ',r['rows'][1]['vi_sao_khong'],'Sai chiều tiền')
    la('dòng sai vẫn bị chặn',r['rows'][1]['dung_duoc'],0)


@ca('#476 tự dò công nợ: cùng mã đủ hai lệnh qua cửa bộ, thử lại bỏ tiền cũ')
def _():
    import frappe
    from unittest.mock import patch
    from vagabond import bo_sao_ke_thu as m
    d=frappe._dict(name='CN',ma_phieu='DNTT-26-10-00001',tong_tien=100,da_thu=0,ma_gd='',trang_thai='Cho thu')
    def gd(dt,ma):return frappe._dict(name=ma,bank_account='BA',description=d.ma_phieu,reference_number=ma,
        deposit=60 if ma=='A' else 40,withdrawal=0,docstatus=1,currency='VND')
    with patch.object(m.bs,'doc_hien_tai',return_value={'dong':[]}),patch.object(frappe,'get_doc',side_effect=gd), \
            patch.object(m,'kiem_nguon',return_value=''),patch.object(m.bs,'con_lai',side_effect=lambda g,doc:g.deposit), \
            patch.object(m,'khop',return_value={'ok':1}) as ghi:
        la('đủ thì ghi',m.tu_dong(d,['B','A'])['ok'],1)
        la('cả hai BT',ghi.call_args.args[1],[dict(name='A',phan_bo=60),dict(name='B',phan_bo=40)])
        ma_lan=ghi.call_args.args[3];m.tu_dong(d,['A','B'])
        la('cùng bộ cùng mã retry',ghi.call_args.args[3],ma_lan)
        ghi.reset_mock();d.ma_gd='A\nB';d.da_thu=100
        la('không nhận lại',m.tu_dong(d,['A','B'])['da_lam_roi'],1)
        la('không ghi lại',ghi.call_count,0)


@ca('#476 tự dò công nợ không tự lấy một phần, không cộng khác tài khoản hoặc chủ cũ')
def _():
    import frappe
    from unittest.mock import patch
    from vagabond import bo_sao_ke_thu as m
    d=frappe._dict(name='CN',ma_phieu='DNTT-26-10-00001',tong_tien=100,da_thu=0,ma_gd='',trang_thai='Cho thu')
    a=frappe._dict(name='A',bank_account='BA',description=d.ma_phieu,reference_number='A',deposit=60,withdrawal=0,docstatus=1,currency='VND')
    b=frappe._dict(a);b.update(name='B',deposit=40,bank_account='KHAC')
    with patch.object(m.bs,'doc_hien_tai',return_value={'dong':[]}),patch.object(frappe,'get_doc',side_effect=lambda dt,ma:a if ma=='A' else b), \
            patch.object(m,'kiem_nguon',return_value='') as kiem,patch.object(m.bs,'con_lai',side_effect=lambda g,doc:g.deposit), \
            patch.object(m,'khop',return_value={'ok':1}) as ghi:
        la('thiếu không gán',m.tu_dong(d,['A'])['ok'],0)
        la('khác tài khoản không gán',m.tu_dong(d,['A','B'])['ok'],0)
        b.bank_account='BA';kiem.return_value='Còn chủ cũ'
        la('chủ cũ không gán',m.tu_dong(d,['A','B'])['ok'],0)
        la('không viết trạng thái giả',ghi.call_count,0)


@ca('#476 PE nháp hủy của bộ không phục hồi qua Desk hoặc nút Gỡ hủy')
def _():
    import frappe
    from unittest.mock import patch
    from vagabond import bo_sao_ke_thu as m,chung_tu as ct
    class D(frappe._dict):
        def is_new(self):return False
        def set(self,k,v):self[k]=v
        def get_doc_before_save(self):return cu
    cu=D(name='PE',vgb_huy=1,vgb_bo_cong_no='CN',references=[])
    d=D(cu);d['vgb_huy']=0
    with patch.object(m,'chu',return_value='CN'):
        nem('Desk không phục hồi chủ cũ',lambda:m.bao_ve(d),frappe.ValidationError)
    with patch.object(frappe,'get_doc',return_value=cu),patch.object(ct,'_kiem_quyen_huy'),patch.object(frappe.db,'set_value') as ghi:
        nem('nút Gỡ hủy không phục hồi chủ cũ',lambda:ct.bo_danh_dau_huy('Payment Entry','PE'),frappe.ValidationError)
        la('không ghi khi bị từ chối',ghi.call_count,0)


@ca('#476 bỏ bộ CN: nháp sống không nhả, nháp hủy nhả nhưng giữ chủ lịch sử')
def _():
    import frappe
    from unittest.mock import patch
    from vagabond import bo_sao_ke_thu as m,thu_tien as tt
    b={'dong':[dict(name='BT',phan_bo=100)],'chung_tu':[dict(doctype='Payment Entry',name='PE')]}
    d=frappe._dict(doctype='Vagabond Cong No',name='CN',da_thu=100,ma_gd='BT\nREF',
        trang_thai='Da thu du',save=lambda **k:None,add_comment=lambda *a:None)
    pe=frappe._dict(docstatus=0,vgb_huy=0)
    def value(dt,ma,f,**kw):return pe if dt=='Payment Entry' else 'REF'
    with patch.object(tt,'la_ke_toan',return_value=True),patch.object(m.bs,'khoa_phieu'), \
         patch.object(frappe,'get_doc',return_value=d),patch.object(m.bs,'doc_hien_tai',return_value=b), \
         patch.object(frappe.db,'get_value',side_effect=value),patch.object(m.bs,'_loi',return_value=[]), \
         patch.object(m.bs,'luu') as luu,patch.object(frappe.db,'set_value') as ghi:
        nem('nháp sống',lambda:m.bo('CN'),frappe.ValidationError)
        pe['docstatus']=1;pe['vgb_huy']=1
        nem('ghi sổ dù có cờ hủy vẫn sống',lambda:m.bo('CN'),frappe.ValidationError)
        la('chưa nhả',luu.call_count,0)
        pe['docstatus']=0;m.bo('CN')
        la('nhả cả bộ',luu.call_args.args[1],[])
        la('không xóa chủ của nháp hủy',ghi.call_count,0)
        la('trả khoản thu trên phiếu',d.da_thu,0)


@ca('#476 PE khóa cả SI cũ và mới theo tên trước khóa Document')
def _():
    from unittest.mock import patch
    import frappe
    from vagabond.bo_sao_ke_document import KhoaBoThu
    from vagabond import bo_sao_ke_thu as m
    from types import SimpleNamespace as S
    vet=[]
    class Goc:
        name='PE';flags={'for_update':True}
        def is_new(self):return False
        def get(self,k):return [S(reference_doctype='Sales Invoice',reference_name='SI-B')]
        def _save(self,*a,**k):vet.append('PE')
    class D(KhoaBoThu,Goc):pass
    with patch.object(m,'chu',side_effect=lambda *a,**k:vet.append('BT-chu')), \
         patch.object(frappe,'get_all',return_value=['SI-A']), \
         patch.object(frappe.db,'get_value',side_effect=lambda dt,ten,*a,**kw:vet.append((ten,kw.get('for_update')))):
        D()._save()
    la('không đảo PE trước SI',vet,['BT-chu',('SI-A',True),('SI-B',True),'PE'])


@ca('#476 cấp quỹ đọc phần còn lại chung, không giấu BT mới dùng một phần')
def _():
    import frappe
    from unittest.mock import patch
    from vagabond import bo_sao_ke_cap as cap, bo_sao_ke_db as bs, tam_ung_app as tu, doi_soat_sepay as dss
    gs={n:frappe._dict(name=n,deposit=100,withdrawal=0,payment_entries=[]) for n in ('A','B')}
    kq={'rows':[{'name':n,'dung_duoc':1} for n in gs], 'tai_khoan_sepay':[dict(ma='MB'),dict(ma='KHAC')]}
    with patch.object(tu,'_quyen') as quyen,patch.object(tu,'_quy'), \
            patch.object(dss,'danh_sach_chon',return_value=kq) as doc, \
            patch.object(frappe,'get_doc',side_effect=lambda dt,n:gs[n]), \
            patch.object(bs,'_cac_bo',side_effect=lambda n,k=False:[bo('Journal Entry/CU',60 if n=='A' else 100)]):
        # Kế hoạch giữ phải chỉ đúng tên BT đang xét.
        with patch.object(bs,'_cac_bo',side_effect=lambda n,k=False:[{'chu':'Journal Entry/CU','dong':[dict(name=n,phan_bo=60 if n=='A' else 100)],'chung_tu':[]}]):
            r=cap.ung_vien('MB',40,tai_khoan='KHAC')
        la('A còn40',r['rows'][0]['con_lai'],40)
        la('B hết không cho chọn',r['rows'][1]['dung_duoc'],0)
        la('chọn bộ',r['chon_bo'],1)
        la('không đổi tài khoản quỹ từ chip',doc.call_args.args[5],'MB')
        la('đúng một chip',r['tai_khoan_sepay'],[dict(ma='MB')])
        la('kiểm quyền',quyen.call_count,1)


@ca('#476 cửa cấp quỹ cũ và bộ đều vào cùng hàm, giữ mã retry')
def _():
    from unittest.mock import patch
    from vagabond import bo_sao_ke_cap as cap,tam_ung_app as tu
    with patch.object(cap,'ghi',return_value={'name':'JE'}) as ghi:
        r=tu.ghi_nhan_cap('[{"name":"A","phan_bo":40}]','111','NQ',40,'LAN')
        la('ra JE',r['name'],'JE')
        la('chuyển đủ tham số',ghi.call_args.args,('[{"name":"A","phan_bo":40}]','111','NQ',40,'LAN'))


@ca('#476 cấp quỹ hủy chỉ giải phóng bộ của khoản cấp, không bỏ nguồn cấn')
def _():
    import frappe
    from unittest.mock import patch
    from vagabond import bo_sao_ke_cap as cap,bo_sao_ke_db as bs
    d=frappe._dict(vgb_cap_ung_bt='BT',vgb_bo_sao_ke='{"dong":[{"name":"BT","phan_bo":40}],"chung_tu":[]}')
    with patch.object(bs,'luu') as luu:
        cap.sau_huy(d);la('gọi đường chung',luu.call_count,1);la('xóa bộ',luu.call_args.args[1],[])
        d['vgb_cap_ung_bt']=None;cap.sau_huy(d);la('không chạm cấn',luu.call_count,1)


@ca('#476 công nợ tự dò SQL vẫn lấy mã DNTT có dấu gạch')
def _():
    import frappe,re
    from unittest.mock import patch
    from vagabond.khung.kiem_thu.thu_cong_no_571 import _nap_cong_no
    cn=_nap_cong_no()
    def sql(query,args,**kw):
        # SQL regexp phải nhận cả nguyên dạng và mã ngân hàng bỏ dấu.
        mau=args[0]
        return [frappe._dict(name='BT',description='TT DNTT-26-10-00001',reference_number='FT',deposit=100,withdrawal=0)] if re.search(mau,'TT DNTT-26-10-00001') else []
    with patch.object(frappe.db,'sql',side_effect=sql):
        r=cn._sepay_cn('DNTT-26-10-00001')
        la('tìm đúng sao kê',r.get('gd'),['BT']);la('tiền nguồn',r.get('nhan'),100)


@ca('#476 hợp đồng một cửa: không ghi chỗ giữ ngoài DB chung, không so tiền từng dòng ở adapter')
def _():
    import ast,re
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    sai=[]
    for p in root.glob('*.py'):
        if p.name=='bo_sao_ke_db.py':continue
        for n in ast.walk(ast.parse(p.read_text())):
            if not isinstance(n,ast.Call) or not isinstance(n.func,ast.Attribute) or n.func.attr not in ('set_value','db_set','set'):continue
            args=n.args+(list(k.value for k in n.keywords))
            # Trường ẩn phải được ghi cùng chỉ mục chủ BT trong một transaction.
            for a in args:
                if any((isinstance(x,ast.Constant) and x.value in ('vgb_bo_sao_ke','vgb_chu_bo_sao_ke')) or
                       (isinstance(x,ast.Attribute) and x.attr in ('O_BO','O_CHU') and isinstance(x.value,ast.Name) and x.value.id=='bs')
                       for x in ast.walk(a)):
                    sai.append(p.name+':'+str(n.lineno))
    la('một cửa ghi giữ',sai,[])
    for file in ('doi_chieu_app.py','doi_soat_sepay.py','de_nghi_chi.py','hoan_tien.py','cong_no.py','tam_ung_app.py'):
        tree=ast.parse((root/file).read_text())
        bad=[]
        for n in ast.walk(tree):
            if not isinstance(n,(ast.Compare,ast.BinOp)):continue
            text=ast.unparse(n)
            if "xet_bo(" in text:continue
            if re.search(r'\b(withdrawal|deposit)\b',text) and re.search(r'\b(tien|can)\b',text) and (
                    isinstance(n,ast.BinOp) and isinstance(n.op,ast.Sub) or
                    isinstance(n,ast.Compare) and any(isinstance(op,ast.Eq) for op in n.ops)):
                bad.append(text)
        la('không so lẻ '+file,bad,[])


def _cap_cu_mo_phong(je_theo_lan):
    """Dựng đúng chuỗi cửa cấp quỹ cũ một BT: tra JE theo mã lần rồi lập JE mới.

    je_theo_lan: {lan: (tên JE, docstatus)}. Trả (lỗi, mã lần dùng cho JE mới).
    """
    import frappe, hashlib
    from unittest.mock import patch
    from vagabond import bo_sao_ke_cap as cap, tam_ung_app as tu
    class Dung(Exception): pass
    moi = {}
    class JE(dict):
        __getattr__ = dict.get
        def __init__(self): super().__init__(flags=frappe._dict())
        def set(self, k, v): self[k] = v
        def append(self, *a, **k): pass
        def insert(self, **k): moi['lan'] = self.get(cap.O_LAN); raise Dung()
        def __setattr__(self, k, v): self[k] = v
    bt = frappe._dict(name='BT', deposit=100, bank_account='MB', date='2026-10-14')
    def get_value(dt, flt_, field=None, *a, **k):
        if dt == 'Bank Transaction':
            return {'name': 'BT', 'bank_account': 'MB', 'date': '2026-10-14'}.get(field, 'BT')
        if dt == 'Journal Entry' and isinstance(flt_, dict) and cap.O_LAN in flt_:
            r = je_theo_lan.get(flt_[cap.O_LAN])
            if not r: return None
            return frappe._dict(name=r[0], docstatus=r[1]) if isinstance(field, (list, tuple)) else r[0]
        return None
    def get_doc(dt, n=None, **k):
        if dt == 'Bank Transaction': return bt
        if dt == 'Account': return frappe._dict(company='C', is_group=0, disabled=0, account_currency='VND', account_number='1111', name='1111')
        if dt == 'Journal Entry':
            ten = n
            st = next(v[1] for v in je_theo_lan.values() if v[0] == ten)
            return frappe._dict(name=ten, docstatus=st, vgb_bo_sao_ke=None, vgb_nq_tham_chieu='', total_debit=100,
                accounts=[frappe._dict(account='1111', credit_in_account_currency=100)])
        raise AssertionError(dt)
    loi = None
    with patch.object(tu, '_quyen'), patch.object(tu, '_quy', return_value=(None, frappe._dict(company='C', name='141'))), \
            patch.object(frappe.db, 'get_value', side_effect=get_value), patch.object(frappe.db, 'savepoint'), \
            patch.object(frappe.db, 'rollback'), patch.object(frappe.db, 'exists', return_value=True), \
            patch.object(frappe, 'get_doc', side_effect=get_doc), patch.object(frappe, 'new_doc', side_effect=lambda dt: JE()), \
            patch.object(frappe, 'generate_hash', create=True, return_value='abcd1234'):
        try:
            cap.ghi('BT', '1111')
        except Dung:
            pass
        except Exception as e:
            loi = str(e)
    return loi, moi.get('lan'), hashlib.sha256(('MB|cu:BT').encode()).hexdigest()


@ca('#477 Codex P2: cửa cấp quỹ cũ ghi lại được sau khi JE cũ đã hủy, không đụng mã unique của JE hủy')
def _():
    import hashlib
    from vagabond.khung.kiem_thu.nen import dung
    lan0 = hashlib.sha256(('MB|cu:BT').encode()).hexdigest()
    # Chuỗi khách: ghi một lần (JE-1), kế toán hủy JE-1, bấm ghi lại đúng dòng sao kê đó.
    loi, lan, _ = _cap_cu_mo_phong({lan0: ('JE-1', 2)})
    la('không còn bị chặn vì JE đã hủy', loi, None)
    dung('JE mới dùng mã lần khác JE đã hủy (trường unique)', bool(lan) and lan != lan0)
    # Hủy lần hai: chuỗi mã tiếp tục, vẫn ghi được và không trùng hai mã cũ.
    lan1 = hashlib.sha256((lan0 + '|JE-1').encode()).hexdigest()
    loi2, lan2, _ = _cap_cu_mo_phong({lan0: ('JE-1', 2), lan1: ('JE-2', 2)})
    la('hủy hai lần vẫn ghi được', loi2, None)
    dung('mã lần thứ ba khác hai mã cũ', lan2 not in (lan0, lan1))
    # Mất phản hồi sau khi đã ghi JE-2 còn hiệu lực: bấm lại không lập JE thứ hai.
    loi3, lan3, _ = _cap_cu_mo_phong({lan0: ('JE-1', 2), lan1: ('JE-2', 1)})
    la('retry gặp JE còn hiệu lực thì không lập mới', (loi3, lan3), (None, None))


@ca("#477 Codex: tự dò gặp một dòng cùng mã không dùng được thì không tự khớp phần còn lại")
def _():
    from unittest.mock import patch
    import frappe
    from vagabond import bo_sao_ke_luong as bl, bo_sao_ke_db as bs, doi_soat_sepay as dss
    from vagabond.khung.kiem_thu.nen import dung
    # Chuỗi Codex nêu: cùng mã TTNB có dòng A sai nguồn và dòng B hợp lệ đúng bằng số phiếu.
    b=dict(doctype="Vagabond De Nghi Chi",ma_do=lambda d:"TTNB-26-10-00001",chieu="ra",so_tien=lambda d:100)
    rows=[dict(name="A",bank_account="MB-THIEU-CHU",description="TTNB-26-10-00001",withdrawal=100,deposit=0),
        dict(name="B",bank_account="MB-CTY",description="TTNB-26-10-00001",withdrawal=100,deposit=0)]
    theo_ten={r["name"]:frappe._dict(r,reference_number="") for r in rows}
    with patch.object(dss,"_ban",return_value=b), \
            patch.object(frappe,"get_doc",side_effect=lambda dt,ma:theo_ten[ma] if dt=='Bank Transaction' else frappe._dict(name=ma)), \
            patch.object(bl,"kiem",side_effect=lambda loai,b,doc,g:"Sai nguồn chi" if g.bank_account=="MB-THIEU-CHU" else ""), \
            patch.object(bs,"con_lai",return_value=100),patch.object(bl,"_khop") as khop:
        k=bl.tu_dong_mot("ttnb","TTNB",rows)
        la("không tự khớp bộ rút gọn",khop.call_count,0)
        la("trả về để kế toán xem",k['ok'],0)
        dung("nêu đúng dòng và lý do","A: Sai nguồn chi" in k['vi_sao'])
        dung("liệt kê cả hai dòng cùng mã","A" in k['giao_dich'] and "B" in k['giao_dich'])


@ca("#477 Codex: chờ đối chiếu sau không tính JE cấn tạm ứng vào phần đã đối chiếu")
def _():
    from unittest.mock import patch
    import frappe
    from vagabond import ho_so_tt as hs
    d=frappe._dict(name="APP",trang_thai=hs.TT_DA_TRA,vgb_tt_ly_do_som="Lệnh 2 chưa về",dong=[dict(so_tien=600)],
        da_tam_ung=0,con_lai=600,vgb_can_ung="JE-CU")
    bo=[dict(doctype="Journal Entry",name="JE-CU"),dict(doctype="Payment Entry",name="PE")]
    phan={"JE-CU":400,"PE":200}
    with patch.object(hs,"_do_chinh_xac",return_value=2),patch.object(hs,"_but_toan_cua_ho_so",return_value=bo), \
            patch.object(frappe,"get_all",side_effect=lambda dt,filters=None,**k:[frappe._dict(allocated_amount=phan[filters["payment_entry"]])]):
        la("400 cấn tạm ứng + 200 sao kê của 600 vẫn chờ",hs._cho_doi_chieu_sau(d),True)
        phan["PE"]=600
        la("đủ 600 sao kê thật mới hết chờ",hs._cho_doi_chieu_sau(d),False)
