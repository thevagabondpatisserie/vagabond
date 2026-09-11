"""#265: giữ khóa nguồn ở kết nối A, worker B timeout rồi thử lại đúng một JE.

Có commit thật, chỉ chạy trên site CI dùng một lần qua hàng rào _mo.
Không thay thế ca deadlock chu kỳ: phép này chứng minh lock wait timeout.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import frappe
from vagabond.khung.bench_thu.kho_tang_243 import _mo, _dong, _dung


def _con(ten, tep):
    _mo()
    try:
        from vagabond import can_tru_san as ct
        frappe.db.sql('set session innodb_lock_wait_timeout=2')
        kq = {'pid': os.getpid(), 'connection': frappe.db.sql('select connection_id()')[0][0]}
        try:
            ct.xu_ly_nen(ten)
            frappe.db.commit()
            kq['ket_qua'] = 'xong'
        except Exception as e:
            kq.update(ket_qua=type(e).__name__, nguyen_nhan=type(e.__cause__).__name__)
            frappe.db.rollback()
        Path(tep).write_text(json.dumps(kq))
    finally:
        _dong()


def chay():
    root = Path(os.environ['VGB_ARTIFACTS'])
    tep = root / ('can-tru-262-con-' + str(os.getpid()) + '.json')
    p = None
    kq = {'dat': False}
    _mo()
    try:
        from vagabond import can_tru_san as ct
        from vagabond.khung.kiem_that.thu_can_tru_262 import _phieu
        so, pi, si = _phieu()
        frappe.db.set_value('Sales Invoice',si.name,'custom_hddt_so','')
        so.submit()
        frappe.db.set_value('Sales Invoice',si.name,'custom_hddt_so','KIEM-262')
        frappe.db.commit()
        # Giữ PI thật trước khi chạy worker; worker khóa phiếu riêng rồi đợi PI này.
        frappe.db.sql('select name from `tabPurchase Invoice` where name=%s for update',(pi.name,))
        ket_noi = frappe.db.sql('select connection_id()')[0][0]
        p = subprocess.Popen([sys.executable,'-m','vagabond.khung.bench_thu.can_tru_262','--con',so.name,str(tep)])
        _dung(p.wait(timeout=40)==0,'Worker con phải trả bằng chứng')
        con = json.loads(tep.read_text())
        _dung(con['connection'] != ket_noi and con['pid'] != os.getpid(),'Hai kết nối DB và tiến trình khác nhau')
        _dung(con['ket_qua']=='RetryBackgroundJobError','Timeout thật phải chuyển sang lỗi retry')
        _dung(con['nguyen_nhan']=='QueryTimeoutError','Nguyên nhân phải là timeout SQL thật')
        frappe.db.rollback()
        so.reload(); pi.reload(); si.reload()
        _dung(so.trang_thai=='Chờ đối soát' and not so.but_toan,'Timeout không đóng dấu lỗi nghiệp vụ')
        _dung(frappe.db.count('Journal Entry',{'vgb_can_tru_san':so.name})==0,'Không JE dở sau timeout')
        _dung(float(pi.outstanding_amount)==200000 and float(si.outstanding_amount)==1000000,'Công nợ không đổi sau timeout')
        ct.xu_ly_nen(so.name)
        frappe.db.commit()
        so.reload(); pi.reload(); si.reload()
        je = so.but_toan
        _dung(bool(je) and so.trang_thai=='Đã cấn trừ','Hết khóa thì thử lại thành công')
        _dung(float(pi.outstanding_amount)==0 and float(si.outstanding_amount)==800000,'Công nợ sau thử lại đúng')
        _dung(ct.thu_bu(so.name)==je,'Retry tiếp trả cùng JE')
        _dung(frappe.db.count('Journal Entry',{'vgb_can_tru_san':so.name,'docstatus':1})==1,'Chỉ một JE ghi sổ')
        kq.update(dat=True,con=con,connection=ket_noi,phieu=so.name,but_toan=je)
    except Exception:
        kq['loi'] = traceback.format_exc()
        raise
    finally:
        if p and p.poll() is None:
            p.kill(); p.wait()
        _dong()
        (root/'can-tru-262.json').write_text(json.dumps(kq,ensure_ascii=False,indent=2))
        print(json.dumps(kq,ensure_ascii=False),flush=True)


if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--con':
        _con(*sys.argv[2:])
    else:
        chay()
