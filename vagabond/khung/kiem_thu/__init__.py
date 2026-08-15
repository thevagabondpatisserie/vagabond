"""Bo kiem thu cua tang khung (A6, anh Viet duyet 15/08/2026).

Cach chay, dung mot lenh, khong can site, khong can Frappe, khong can cai
them goi nao:

    python3 vagabond/khung/kiem_thu/chay.py

Chay het thi in ra so ca dat va so ca hong. Hong mot ca la lenh tra ve ma
loi khac 0, de sau nay ghep vao buoc truoc khi deploy.

Vi sao co bo nay
----------------
218 ham API dung toi tien va ton kho, va truoc hom nay co DUNG 0 bai kiem
thu. Loi bill in lai cong trung diem hom 13/08 khong nam o cho goi co so
du lieu, no nam o mot phep cong. Nhung phep cong do nam lan trong ham co
goi frappe nen muon thu lai phai dung ca mot site, vi kho thu nen khong ai
thu, va vi khong ai thu nen no lot toi tay khach.

Bo nay khong tham vong phu 218 ham. No phu dung phan da tach thuan duoc:
phep dem, phep loc, phep cong, phep cat dong, va luat xep trang thai cua
hai man mau. Do la nhung cho ma sai mot chut la sai tien.

Cac tep
-------
    nen.py           bo chay nho va ban gia lap Frappe toi thieu
    thu_tinh.py      tang thuan trong khung/tinh.py
    thu_hop_dong.py  cac chan khai bao trong khung/hop_dong.py
    thu_luat.py      luat xep trang thai cua hai man mau
    thu_ds.py        xuyen suot: khung phai ra y het duong cu
    chay.py          diem vao

Luat cua bo kiem thu
--------------------
  1. Khong them thu vien ngoai. Khong pytest, khong unittest cho ruom -
     mot bo chay 60 dong la du va ai doc cung hieu.
  2. Moi ca phai chay duoc mot minh, khong phu thuoc thu tu.
  3. Khong dung toi co so du lieu that. Mot ca kiem thu lam hong du lieu
     that con te hon la khong co ca kiem thu nao.
  4. Ten ca viet bang tieng Viet, noi ro dieu dang bao ve, de khi no do
     thi doc mot dong la biet cai gi vua hong.
"""
