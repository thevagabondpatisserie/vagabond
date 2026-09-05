/* ------------- Chip trang thai cho cac man danh sach rieng cua Vagabond

   Anh Viet xin 05/09/2026: *"Ra soat ban desktop xem cac man danh sach
   nao can chip loc, chip trang thai nua thi em phai de xuat them het vao
   dum anh."*

   DEM THAT TRUOC KHI LAM
   ----------------------
   Ra soat ngay 05/09/2026 tren 76 doctype rieng cua Vagabond:

     * 23 doctype CO mot truong Select dong vai tro trang thai
     * 0 doctype co chip mau tren man danh sach

   Tuc la moi phieu de nghi chi, moi ho so thanh toan, moi phieu KPI deu
   dang mang mot truong trang thai day du y nghia, ma man danh sach thi
   khong he to no ra. Muon biet phieu nao dang cho giam doc duyet, mat
   phai doc tung dong chu nho trong cot.

   VI SAO MOT TEP CHUNG CHU KHONG PHAI MUOI TEP
   --------------------------------------------
   Muoi man nay hoi cung mot cau: to nay dang o trang thai nao va to mau
   gi. Chep muoi ban la muoi ban se lech nhau vao mot ngay khong ai doan
   truoc, dung cai bay quy tac 6 cua repo noi toi, va dung ly do
   minvoice_list.js da gop ba man vao mot tep.

   Nen o day chi co MOT bang khai va MOT ham gan. Them mot man moi chi
   viec them mot dong vao bang, khong dong toi ma.

   BA LUAT CUA BANG MAU, xin dung pha khi them dong moi
   ----------------------------------------------------
   1. XANH LA chi danh cho trang thai KET THUC TOT: da thu du, da thanh
      toan, hoan tat, da duyet. Nhin thay xanh la biet viec xong.
   2. DO chi danh cho viec DANG KET hoac DA HONG: bi tra lai, khong giao
      duoc, khach tu choi, thu thieu. Do khap noi thi do mat nghia, dung
      bai hoc chu "Qua han" cu o ban v420.
   3. XAM danh cho trang thai da DONG SO nhung khong con phai lam gi:
      nhap, da huy, bo qua. Xam nghia la dung ban tam toi.

   Con lai la cam va xanh duong cho cac buoc DANG CHAY giua chung, chia
   theo viec dang cho AI: cam la cho nguoi khac lam, xanh duong la den
   luot minh.

   MOT CHO TINH, MOT CHO HIEN (QT-19)
   ----------------------------------
   Ben nay KHONG tinh lai trang thai. Truong trang thai do may chu ghi
   san theo dung luong nghiep vu cua tung doctype, ben nay chi doc va to
   mau. Khong duoc them luat nghiep vu nao vao tep nay.

   MOT CAI BAY DA TRANH
   --------------------
   Gan de len `frappe.listview_settings` la xoa trang phan cua nguoi
   khac. Nen o day GOP chu khong gan de, giong het minvoice_list.js va
   bom_list.js. */

(function () {

	/* Bang khai. Moi doctype: ten truong giu trang thai, va bang mau cho
	   tung gia tri. Gia tri viet DUNG NGUYEN VAN nhu trong tep JSON cua
	   doctype, ke ca khi khong dau, vi day la thu may so sanh. */
	var KHAI = {
		'Vagabond De Nghi Chi': {
			truong: 'trang_thai',
			mau: {
				'Nhap': 'gray',
				'Cho duyet': 'orange',
				'Cho giam doc': 'orange',
				'Cho ke toan': 'blue',
				'Hoan tat': 'green',
				'Da chi': 'green',
				'Bi tra lai': 'red',
				'Da huy': 'gray',
			},
		},
		'Vagabond Ho So TT': {
			truong: 'trang_thai',
			mau: {
				'Nhap': 'gray',
				'Cho ke toan': 'orange',
				'Cho giam doc': 'orange',
				'Da duyet': 'blue',
				'Da thanh toan': 'green',
				'Tu choi': 'red',
				'Huy': 'gray',
			},
		},
		'Vagabond KPI Phieu': {
			truong: 'trang_thai',
			mau: {
				'Cho quan ly': 'orange',
				'Cho ke toan': 'orange',
				'Cho giam doc': 'orange',
				'Da duyet': 'green',
				'Da day chi': 'green',
				'Da huy': 'gray',
			},
		},
		'Vagabond Cong No': {
			truong: 'trang_thai',
			mau: {
				'Cho thu': 'orange',
				'Da thu du': 'green',
				/* Thu thieu la do that: khach da tra nhung khong du, dong
				   tien treo lai va khong ai tu phat hien duoc. */
				'Thu thieu': 'red',
				'Huy': 'gray',
			},
		},
		'Vagabond Hoan Tien': {
			truong: 'trang_thai',
			mau: {
				'Cho chi': 'orange',
				'Da chi': 'blue',
				'Da doi soat': 'blue',
				'Hoan thanh': 'green',
				'Da huy': 'gray',
			},
		},
		'Vagabond Nop Quy': {
			truong: 'trang_thai',
			mau: {
				'Nháp': 'gray',
				'Chờ ký nhận': 'orange',
				'Đã nộp quỹ': 'green',
				'Đã huỷ': 'gray',
			},
		},
		'Bao Gia Ban Hang': {
			truong: 'trang_thai',
			mau: {
				'Nháp': 'gray',
				'Đã gửi khách': 'blue',
				'Khách duyệt': 'green',
				'Khách từ chối': 'red',
				/* Het hieu luc khong phai loi cua ai, chi la to bao gia da
				   qua han. Cam de sales ngo toi ma goi lai khach. */
				'Hết hiệu lực': 'orange',
				'Đã lên hợp đồng': 'green',
			},
		},
		'Hop Dong Ban Hang': {
			truong: 'trang_thai',
			mau: {
				'Nháp': 'gray',
				'Đã gửi khách': 'blue',
				'Đang thương thảo': 'orange',
				'Đang thực hiện': 'blue',
				'Hoàn tất': 'green',
				'Đã thanh lý': 'green',
				'Huỷ': 'gray',
			},
		},
		'Vagabond Don Huy': {
			truong: 'trang_thai',
			mau: {
				'Cho hoan': 'orange',
				'Dang hoan': 'blue',
				'Da hoan': 'green',
				'Khong phai hoan': 'gray',
				'Bo qua': 'gray',
			},
		},
		'Vagabond Yeu Cau TT': {
			truong: 'tinh_trang',
			mau: {
				'Cho thanh toan': 'orange',
				'Da thanh toan': 'green',
				'Da huy': 'gray',
			},
		},
		'Vagabond Kiem Kho Diem': {
			truong: 'tinh_trang',
			mau: {
				'Dang ban': 'orange',
				'Da chot': 'green',
			},
		},
		'Vagabond Nhan Banh': {
			truong: 'tinh_trang',
			mau: {
				'Dang nhan': 'orange',
				'Da chot': 'green',
			},
		},
	};

	function gan(dt, khai) {
		var CU = frappe.listview_settings[dt] || {};
		var ind_cu = CU.get_indicator;
		var truong = khai.truong;

		CU.add_fields = (CU.add_fields || []).concat([truong]);

		CU.get_indicator = function (doc) {
			var tt = String(doc[truong] || '').trim();

			/* Chua co trang thai thi noi that la chua co, dung bia. Mot
			   chip noi sai con hai hon khong co chip nao. */
			if (!tt) {
				if (ind_cu) {
					try {
						return ind_cu(doc);
					} catch (e) {
						/* Phan cua nguoi khac hong thi van phai tra ve
						   duoc mot cai gi do. */
					}
				}
				return ['Chưa có trạng thái', 'gray', truong + ',=,'];
			}

			/* Gia tri la nhung van hien ra, mau xam. Nhu vay them mot
			   trang thai moi ben may chu ma quen khai o day thi man hinh
			   van chay dung, chi la chua co mau rieng. */
			return [tt, khai.mau[tt] || 'gray', truong + ',=,' + tt];
		};

		CU._vgb_ind_cu = ind_cu;
		frappe.listview_settings[dt] = CU;
	}

	Object.keys(KHAI).forEach(function (dt) {
		gan(dt, KHAI[dt]);
	});
})();
