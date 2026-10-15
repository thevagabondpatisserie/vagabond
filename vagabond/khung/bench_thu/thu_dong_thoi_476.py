"""Hai tiến trình đọc cùng SI, rồi tranh lập PE qua cửa công nợ thật.

B giữ snapshot trước khi A lập/ghi sổ PE. Chỉ hàng rào thời gian là giả;
SQL, chứng từ, phân bổ và commit đều chạy trên bench dùng một lần.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from unittest.mock import patch
import frappe
from vagabond.khung.bench_thu.kho_tang_243 import _mo, _dong, _dung
from vagabond.khung.bench_thu.do_khoa_476 import cho


def con(vai, folder):
    folder = Path(folder)
    cfg = json.loads((folder / 'cfg.json').read_text())
    _mo()
    ket = {'vai': vai, 'pid': os.getpid()}
    try:
        from vagabond import cong_no as cn
        frappe.db.sql('set session innodb_lock_wait_timeout=15')
        if vai == 'B':
            # Establish RR snapshot before A inserts its PE.
            frappe.db.get_value('Sales Invoice', cfg['si'], 'outstanding_amount')
            (folder / 'B.snapshot').touch()
            cho(folder, 'A.holds')
        else:
            cho(folder, 'B.snapshot')
        ham = frappe.db.get_value
        def get_value(dt, ten=None, *a, **kw):
            if vai == 'B' and dt == 'Sales Invoice' and ten == cfg['si'] and kw.get('for_update'):
                (folder / 'B.waiting').touch()
            return ham(dt, ten, *a, **kw)
        t = time.monotonic()
        with patch.object(frappe.db, 'get_value', get_value):
            r = cn.khop_tay(cfg['phieu'][vai], cfg['tien'], dong=json.dumps([
                {'name': cfg['bt'][vai], 'phan_bo': cfg['tien']}]), ma_lan='race476'+vai)
        if vai == 'A':
            if cfg['buoc'] == 'ghi_so':
                from vagabond.khung.kiem_that.thu_phieu_thu_unc_534 import _Tep
                from vagabond import thu_tien as tt
                with _Tep() as tep:
                    tt.ghi_so_phieu_thu(r['pe'], unc=[tep.file_url])
            (folder / 'A.holds').touch()
            cho(folder, 'B.waiting')
            time.sleep(2)
        frappe.db.commit()
        ket.update(dat=True, pe=r['pe'], giay=time.monotonic()-t)
    except Exception as e:
        frappe.db.rollback()
        ket.update(dat=False, loai=type(e).__name__, loi=str(e), traceback=traceback.format_exc(),
                   giay=time.monotonic()-t if 't' in locals() else None)
    finally:
        _dong()
        (folder / (vai+'.json')).write_text(json.dumps(ket,ensure_ascii=False,indent=2))


def mot_ca(buoc):
    folder=Path(os.environ['VGB_ARTIFACTS'])/('thu-dong-thoi-476-'+buoc)
    folder.mkdir()
    _mo()
    try:
        from vagabond.khung.kiem_that.thu_gom_phap_nhan_576 import _nen,_hd,_khach,_phieu
        from vagabond.khung.kiem_that.thu_khop_tay_gop_571 import _gd
        from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_cong_ty_moi
        from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _tk_ngan_hang
        from vagabond import sepay
        cty,tk,_=_nen()
        si=_hd(tk,cty,100000,_khach('race476'))
        ba=_tai_khoan_cong_ty_moi(_tk_ngan_hang(cty))
        sepay.them_tai_khoan(ba.bank_account_no,ba.name)
        cfg={'buoc':buoc,'si':si.name,'tien':float(si.outstanding_amount),'phieu':{},'bt':{}}
        for v in ('A','B'):
            cfg['phieu'][v]=_phieu([si],si.customer).name
            cfg['bt'][v]=_gd(ba.name,cfg['tien']).name
        frappe.db.commit()
    finally:
        _dong()
    (folder/'cfg.json').write_text(json.dumps(cfg))
    ps=[]
    try:
        for v in ('A','B'):
            ps.append(subprocess.Popen([sys.executable,'-m',__spec__.name,'--con',v,str(folder)]))
        for p in ps:
            _dung(p.wait(timeout=70)==0,'Tiến trình trả bằng chứng')
        ket={v:json.loads((folder/(v+'.json')).read_text()) for v in ('A','B')}
        _dung(ket['A']['dat'],'Người đầu hoàn tất: '+str(ket))
        b=ket['B']
        _dung(not b['dat'] and b['loai']=='ValidationError','Người sau bị chặn nghiệp vụ: '+str(b))
        _dung('không còn nợ' in b['loi'] or 'nháp phủ đủ' in b['loi'],'Câu tiếng Việt đúng lý do: '+str(b))
        _dung(b['giay']>=1.5,'Thật sự đã chờ khóa SI')
        _mo()
        try:
            from vagabond import bo_sao_ke_db as bs
            doc=frappe.get_doc('Vagabond Cong No',cfg['phieu']['B'])
            _dung(not bs.doc_hien_tai(doc)['dong'] and not doc.da_thu,'Thua không để chỗ giữ/đã thu dở')
            pe=frappe.get_all('Payment Entry Reference',filters={'reference_doctype':'Sales Invoice',
                'reference_name':cfg['si'],'parenttype':'Payment Entry'},pluck='parent')
            _dung(set(pe)=={ket['A']['pe']},'Chỉ một PE phủ hóa đơn')
        finally:
            _dong()
        return ket
    finally:
        for p in ps:
            if p.poll() is None:p.kill();p.wait()


def chay():
    ket={}
    try:
        for buoc in ('nhap','ghi_so'):
            ket[buoc]=mot_ca(buoc)
            print('TRANH SI PE '+json.dumps(ket[buoc],ensure_ascii=False),flush=True)
    finally:
        (Path(os.environ['VGB_ARTIFACTS'])/'thu-dong-thoi-476.json').write_text(json.dumps(ket,ensure_ascii=False,indent=2))


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--con':con(*sys.argv[2:])
    else:chay()
