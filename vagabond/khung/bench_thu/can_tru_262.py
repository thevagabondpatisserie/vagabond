"""#265: giữ khóa nguồn ở kết nối A, worker B timeout rồi thử lại đúng một JE.

Có commit thật, chỉ chạy trên site CI dùng một lần qua hàng rào _mo.
Hai phép riêng cho timeout và deadlock chu kỳ, không giả lập ngoại lệ DB.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import time
from unittest.mock import patch
import frappe
from vagabond.khung.bench_thu.kho_tang_243 import _mo, _dong, _dung


def _con(ten, tep, che_do):
    _mo()
    try:
        from vagabond import can_tru_san as ct
        frappe.db.sql('set session innodb_lock_wait_timeout=' + ('20' if che_do == 'deadlock' else '2'))
        goc = ct._doc_nguon
        def doc_nguon(*args, **kwargs):
            Path(tep + '.ready').touch()
            return goc(*args, **kwargs)
        kq = {'pid': os.getpid(), 'connection': frappe.db.sql('select connection_id()')[0][0]}
        try:
            with patch.object(ct, '_doc_nguon', doc_nguon):
                ct.xu_ly_nen(ten)
            frappe.db.commit()
            kq['ket_qua'] = 'xong'
        except Exception as e:
            kq.update(ket_qua=type(e).__name__, nguyen_nhan=type(e.__cause__).__name__)
            frappe.db.rollback()
        Path(tep).write_text(json.dumps(kq))
    finally:
        _dong()


def chay(che_do):
    root = Path(os.environ['VGB_ARTIFACTS'])
    tep = root / ('can-tru-262-con-' + che_do + '-' + str(os.getpid()) + '.json')
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
        if che_do == 'deadlock':
            # Giữ thêm dòng nguồn để giao dịch A nặng hơn worker chỉ giữ phiếu.
            # MariaDB chọn nạn nhân, assertion dưới bắt nếu không chạm đúng worker.
            frappe.db.sql('select name from `tabPurchase Invoice Item` where parent=%s for update',(pi.name,))
            frappe.db.sql('select name from `tabSales Invoice` where name=%s for update',(si.name,))
            frappe.db.sql('select name from `tabSales Invoice Item` where parent=%s for update',(si.name,))
        ket_noi = frappe.db.sql('select connection_id()')[0][0]
        p = subprocess.Popen([sys.executable,'-m','vagabond.khung.bench_thu.can_tru_262','--con',so.name,str(tep),che_do])
        if che_do == 'deadlock':
            han = time.monotonic() + 30
            while not Path(str(tep)+'.ready').exists():
                _dung(p.poll() is None,'Worker hỏng trước khi khóa phiếu')
                if time.monotonic() > han:
                    raise TimeoutError('Worker chưa giữ khóa phiếu')
                time.sleep(0.02)
            # B giữ phiếu rồi đợi PI của A; A đợi phiếu của B tạo chu kỳ thật.
            frappe.db.sql('set session innodb_lock_wait_timeout=20')
            frappe.db.sql('select name from `tabVagabond Can Tru San` where name=%s for update',(so.name,))
        _dung(p.wait(timeout=40)==0,'Worker con phải trả bằng chứng')
        con = json.loads(tep.read_text())
        _dung(con['connection'] != ket_noi and con['pid'] != os.getpid(),'Hai kết nối DB và tiến trình khác nhau')
        _dung(con['ket_qua']=='RetryBackgroundJobError','Timeout thật phải chuyển sang lỗi retry')
        _dung(con['nguyen_nhan']==('QueryDeadlockError' if che_do=='deadlock' else 'QueryTimeoutError'),'Nguyên nhân phải là lỗi khóa SQL thật đúng ca')
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
        kq.update(dat=True,che_do=che_do,con=con,connection=ket_noi,phieu=so.name,but_toan=je)
    except Exception:
        kq['loi'] = traceback.format_exc()
        raise
    finally:
        if p and p.poll() is None:
            p.kill(); p.wait()
        _dong()
        (root/('can-tru-262-'+che_do+'.json')).write_text(json.dumps(kq,ensure_ascii=False,indent=2))
        print(json.dumps(kq,ensure_ascii=False),flush=True)


if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--con':
        _con(*sys.argv[2:])
    else:
        chay('timeout')
        chay('deadlock')
