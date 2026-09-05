/* Gia lap trang dat banh de CHAY THAT ma nguon trong node, khong can trinh
   duyet, khong can goi mang.

   Vi sao can: bo kiem cua #205 vong mot chi doc chuoi trong ma nguon de doan
   hanh vi. Codex bat duoc ba loi ma cach do khong the thay: dong ho doc sai
   thoi diem, ngay lech sau nua dem, va bam mot ngay da bi coi la chot ca
   khung gio. Ba loi do chi lo ra khi CHAY that va TUA duoc dong ho.

   Cach dung:
     node gia_lap_trang.js <duong-dan-banh.html> <ISO gio ban dau> <ma kich ban>

   Ma kich ban chay trong cung pham vi voi ma cua trang, nen goi thang duoc
   pick(), pickSlot(), drawCoDate(), mocGioNhan()... Trong kich ban co san:
     TUA(soPhut)   tua dong ho toi truoc
     DAT(iso)      dat lai dong ho
     EL('#id')     lay phan tu gia lap
     RA(obj)       in ket qua ra stdout dang JSON

   KHONG dung file nay lam bang chung ve giao dien: no khong tinh CSS, khong
   do duoc kich thuoc. Phan do kiem bang trinh duyet that, ghi trong PR. */

const fs = require('fs');
const vm = require('vm');

const duong = process.argv[2];
const gioDau = process.argv[3];
const kichBan = process.argv[4];

const html = fs.readFileSync(duong, 'utf8');
const m = html.match(/<script>([\s\S]*)<\/script>/);
if (!m) { throw new Error('khong thay khoi script trong trang'); }
let ma = m[1];

/* Cat cac loi goi khoi dong o cuoi tep: chung nap du lieu qua mang va dat
   nhip 60 giay, khong lien quan gi den viec dang kiem. */
ma = ma.replace(/\nnapTonQuay\(\);[\s\S]*$/, '\n');

/* ---------------- DONG HO DIEU KHIEN DUOC ---------------- */
let lech = 0;                       /* mili giay cong them vao dong ho that */
const goc = new Date(gioDau).getTime();
const batDau = Date.now();
const DateThat = Date;
function bayGio() { return goc + lech + (Date.now === nowGia ? 0 : 0); }
let hienTai = goc;

class DateGia extends DateThat {
	constructor(...a) {
		if (a.length === 0) { super(hienTai); } else { super(...a); }
	}
	static now() { return hienTai; }
}
function nowGia() { return hienTai; }

/* ---------------- DOM GIA LAP ---------------- */
function lamClassList(el) {
	const bo = new Set();
	return {
		add: c => bo.add(c),
		remove: c => bo.delete(c),
		toggle: (c, b) => { if (b === undefined) { bo.has(c) ? bo.delete(c) : bo.add(c); } else { b ? bo.add(c) : bo.delete(c); } },
		contains: c => bo.has(c),
		_bo: bo
	};
}

const kho = new Map();

function taoEl(ten) {
	const el = {
		id: ten,
		innerHTML: '',
		textContent: '',
		value: '',
		src: '',
		scrollTop: 0,
		hidden: false,
		style: {},
		dataset: {},
		classList: lamClassList(),
		_thuoc: {},
		_daTro: false,
		focus() { el._daTro = true; GHI.troVao = ten; },
		blur() { el._daTro = false; },
		setAttribute(k, v) { el._thuoc[k] = String(v); },
		getAttribute(k) { return k in el._thuoc ? el._thuoc[k] : null; },
		removeAttribute(k) { delete el._thuoc[k]; },
		addEventListener() {},
		removeEventListener() {},
		scrollIntoView() { GHI.keo = ten; },
		appendChild() {},
		insertAdjacentHTML(v, h) { el.innerHTML += h; },
		closest() { return null; },
		getBoundingClientRect() { return { x: 0, y: 0, width: 0, height: 0, top: 0, left: 0, right: 0, bottom: 0 }; },
		/* Tim con theo lop, doc thang tu innerHTML. Chi lam duoc bo chon
		   dang '.lop' hoac '.lop.lop2', du cho nhung cho trang nay dung.
		   Con tra ve duoc GIU LAI theo vi tri, de ma trang gan textContent
		   roi doc lai van thay. */
		querySelector(sel) {
			const ds = el.querySelectorAll(sel);
			return ds.length ? ds[0] : null;
		},
		querySelectorAll(sel) {
			/* Ho tro dang '.lop', '.lop.lop2', ten the, va danh sach ngan
			   cach bang dau phay. Du cho nhung cho trang nay dung. */
			const phan = String(sel).split(',').map(x => x.trim()).filter(Boolean);
			const the = el.innerHTML.match(/<[a-zA-Z][^>]*>/g) || [];
			const ra = [];
			let k = 0;
			the.forEach(t => {
				const tenThe = (t.match(/^<([a-zA-Z][\w-]*)/) || [, ''])[1].toLowerCase();
				const c = (t.match(/class="([^"]*)"/) || [, ''])[1].split(/\s+/);
				const khop = phan.some(pt => {
					if (pt.charAt(0) === '.') {
						const lop = pt.split('.').filter(Boolean);
						return lop.length && lop.every(l => c.indexOf(l) >= 0);
					}
					return pt.toLowerCase() === tenThe;
				});
				if (khop) {
					const khoa = ten + ' >> ' + sel + ' #' + k;
					k++;
					if (!kho.has(khoa)) kho.set(khoa, taoEl(khoa));
					const con = kho.get(khoa);
					con._the = t;
					ra.push(con);
				}
			});
			return ra;
		}
	};
	return el;
}

const GHI = { troVao: null, keo: null, banh: [], goiMang: [] };

/* Lay noi dung THAT trong the co id nay tu HTML cua trang, de phan tu gia lap
   khoi rong ruot. Can vi tgl() doc `nut.querySelector('.bx')`, ma o dau tich
   do nam san trong markup chu khong do JavaScript sinh ra. */
function ruotTheoId(id) {
	const re = new RegExp('<([a-zA-Z][\\w-]*)([^>]*\\sid="' + id + '")([^>]*)>');
	const m = re.exec(html);
	if (!m) return '';
	const ten = m[1];
	if (/\/>\s*$/.test(m[0])) return '';
	let i = m.index + m[0].length;
	const batDau = i;
	let sau = 1;
	const q = new RegExp('<(\\/?)' + ten + '\\b[^>]*>', 'g');
	q.lastIndex = i;
	let t;
	while ((t = q.exec(html))) {
		sau += t[1] ? -1 : 1;
		if (sau === 0) return html.slice(batDau, t.index);
	}
	return '';
}

function EL(sel) {
	if (!kho.has(sel)) {
		const el = taoEl(sel);
		if (sel.charAt(0) === '#' && sel.indexOf(' ') < 0) el.innerHTML = ruotTheoId(sel.slice(1));
		kho.set(sel, el);
	}
	return kho.get(sel);
}

const document = {
	querySelector: EL,
	querySelectorAll: sel => [EL(sel)],
	getElementById: id => EL('#' + id),
	createElement: t => taoEl('<' + t + '>'),
	addEventListener() {},
	body: taoEl('body'),
	documentElement: taoEl('html'),
	head: taoEl('head')
};
document.body.style = {};

/* ---------------- MANG GIA LAP ---------------- */
async function fetchGia(url, opt) {
	GHI.goiMang.push({ url: String(url), opt: opt || null });
	return {
		ok: true,
		status: 200,
		json: async () => ({ message: { ok: true, total_fee: 30000, diem_lay: 'Bep Vagabond' } }),
		text: async () => '{}'
	};
}

const window = {
	location: { hash: '', pathname: '/banh', href: 'http://x/banh', replace() {}, search: '' },
	addEventListener() {},
	removeEventListener() {},
	scrollTo() {},
	matchMedia: () => ({ matches: false, addEventListener() {}, addListener() {} }),
	history: { pushState() {}, replaceState() {}, back() {} },
	localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
	innerWidth: 390,
	innerHeight: 844
};

const hopBoi = {
	console, JSON, Math, Number, String, Boolean, Array, Object, Set, Map, RegExp,
	Error, isNaN, isFinite, parseInt, parseFloat, encodeURIComponent, decodeURIComponent,
	Promise, Intl, TextEncoder, TextDecoder,
	Date: DateGia,
	document, window, fetch: fetchGia,
	navigator: { userAgent: 'gia lap', clipboard: { writeText: async () => {} } },
	localStorage: window.localStorage,
	location: window.location,
	history: window.history,
	setTimeout: (f) => { if (typeof f === 'function') f(); return 0; },
	clearTimeout() {},
	setInterval: () => 0,
	clearInterval() {},
	requestAnimationFrame: (f) => { f(); return 0; },
	alert() {}, confirm: () => true,
	EL,
	GHI,
	RA: (o) => { console.log(JSON.stringify(o)); },
	DAT: (iso) => { hienTai = new DateThat(iso).getTime(); },
	TUA: (phut) => { hienTai = hienTai + Number(phut) * 60000; }
};
hopBoi.globalThis = hopBoi;
hopBoi.self = hopBoi;

const boi = vm.createContext(hopBoi);
vm.runInContext(ma, boi, { filename: 'banh.html' });
vm.runInContext(kichBan, boi, { filename: 'kich-ban' });
