# -*- coding: utf-8 -*-
"""Bảng đối chiếu emoji -> biểu tượng Lucide cho giao diện ui-b (bản 4 mục 3).

MỘT nguồn: sửa ở đây rồi chạy `python3 cong_cu/ui_b/sinh_bieu_tuong.py`.
Máy sinh ra khối biểu tượng trong 81-ui-b.js và bảng docs/ui-nghe-si/bang-bieu-tuong.md.

GOC: bảng anh Việt đã duyệt trong đặc tả. DE_XUAT: phần còn lại, biểu tượng
gần nghĩa nhất, chờ duyệt trong PR 1. CHAM: chấm màu trạng thái, lớp vẽ đổi
thành chấm tròn tô màu chứ không thành biểu tượng nét.
"""

GOC = {
	"🔔": "bell", "👤": "circle-user-round", "🏠": "house", "📌": "pin",
	"🛒": "shopping-cart", "🧑‍🍳": "chef-hat", "📥": "package-plus", "📤": "package-minus",
	"🧮": "calculator", "🎂": "cake", "💝": "heart-handshake", "🚚": "truck",
	"📈": "chart-line", "🧾": "receipt", "💰": "wallet", "📋": "clipboard-list",
	"📄": "file-text", "✅": "circle-check", "🕐": "clock", "🖥": "monitor",
	"🏬": "store", "🏪": "store", "🥡": "shopping-bag", "🖨": "printer", "💵": "banknote",
	"➕": "plus", "📒": "book-open", "🎁": "gift", "💳": "credit-card",
	"🎫": "ticket", "🎟": "ticket-percent", "⏳": "hourglass", "🏦": "landmark",
	"🛵": "bike", "💬": "message-circle", "⚠": "triangle-alert",
	"✎": "pencil", "✏": "pencil", "📝": "pencil", "🔎": "search", "🔍": "search",
	"✕": "x", "×": "x", "✓": "check", "📷": "image", "🖼": "image",
	"👥": "users", "🔒": "lock", "📦": "package",
}

DE_XUAT = {
	"🚫": "ban", "→": "arrow-right", "📎": "paperclip", "💾": "save", "🏭": "factory",
	"🍰": "cake-slice", "📅": "calendar", "🔗": "link", "🏢": "building-2", "↩": "undo-2",
	"🏷": "tag", "○": "circle", "🗂": "folders", "🧺": "shopping-basket", "🔄": "refresh-cw",
	"📊": "chart-column", "📚": "library", "🗑": "trash-2", "●": "circle-dot", "✍": "pen-line",
	"🔁": "repeat", "▾": "chevron-down", "💸": "hand-coins", "🥐": "croissant", "📞": "phone",
	"🌐": "globe", "⛔": "octagon-x", "☑": "square-check", "⚙": "settings", "★": "star",
	"✉": "mail", "🧑": "user", "📑": "file-stack", "⬜": "square", "⭐": "star", "⬇": "arrow-down",
	"📣": "megaphone", "🏛": "building", "🎉": "party-popper", "❓": "circle-question-mark",
	"📍": "map-pin", "📭": "inbox", "🫙": "container", "✖": "x", "📖": "book-open-text",
	"🧪": "flask-conical", "🔐": "lock-keyhole", "🤝": "handshake", "🍳": "cooking-pot",
	"✨": "sparkles", "💡": "lightbulb", "▶": "play", "↻": "rotate-cw", "💠": "diamond",
	"✦": "sparkle", "☐": "square", "🪑": "armchair", "🧭": "compass", "📁": "folder",
	"📧": "mail", "🧊": "refrigerator", "▸": "chevron-right", "🛡": "shield", "🗓": "calendar-days",
	"🎯": "target", "🙋": "hand", "⏰": "alarm-clock", "✗": "x", "🆕": "badge-plus", "☆": "star",
	"🔑": "key", "⚡": "zap", "🧁": "dessert", "🚧": "construction", "🌤": "cloud-sun",
	"◀": "chevron-left", "❄": "snowflake", "🕓": "clock-4", "←": "arrow-left", "⬆": "arrow-up",
	"👔": "shirt", "📗": "book", "🍽": "utensils", "🌕": "moon", "🔳": "scan", "🧩": "puzzle",
	"⛽": "fuel", "💲": "circle-dollar-sign", "🌙": "moon", "🗝": "key-round", "📨": "mail-open",
	"⌄": "chevron-down", "🥣": "soup", "🎵": "music", "👍": "thumbs-up", "🗺": "map",
	"🚕": "car-taxi-front", "🕒": "clock-3", "📮": "mailbox", "✋": "hand", "⏩": "fast-forward",
	"➖": "minus", "🔧": "wrench", "▴": "chevron-up", "💌": "heart", "⏸": "pause",
	"✂": "scissors", "🔮": "wand-sparkles", "⇄": "arrow-left-right", "🏗": "hard-hat",
	"💼": "briefcase", "🧑‍💼": "briefcase", "🧹": "paintbrush", "🥚": "egg", "🧂": "flask-round", "⚖": "scale",
	"⌛": "hourglass", "🧍": "person-standing", "🌑": "moon", "✔": "check", "❔": "circle-question-mark",
	"🔓": "lock-open", "🍵": "cup-soda", "🌾": "wheat", "👁": "eye", "👀": "eye", "↑": "arrow-up",
	"👋": "hand", "📂": "folder-open", "☕": "coffee", "🌸": "flower-2", "🍓": "cherry",
	"🤖": "bot", "🪙": "coins", "🙅": "user-x", "🎖": "medal", "👻": "ghost", "📏": "ruler",
	"❌": "x", "🛍": "shopping-bag", "🧰": "hammer", "📘": "book", "◈": "diamond",
	"☛": "arrow-right", "⌨": "keyboard", "🕘": "clock-9", "🌅": "sunrise", "☀": "sun",
	"🍬": "candy", "↔": "move-horizontal", "▲": "chevron-up", "▼": "chevron-down",
	"◉": "circle-dot", "⬅": "arrow-left", "🔢": "hash", "👆": "pointer", "🧱": "brick-wall",
	"🏁": "flag", "🔺": "triangle", "🔻": "chevron-down", "❗": "circle-alert", "🖊": "pen",
	"🇻": "flag", "🇳": "flag", "🥮": "cookie", "▪": "square", "🎨": "palette", "📜": "scroll",
	"↺": "rotate-ccw", "⇪": "arrow-big-up", "🔕": "bell-off", "📱": "smartphone",
	"🧋": "cup-soda", "🍂": "leaf", "🎓": "graduation-cap", "🍑": "apple", "🍋": "citrus",
	"🥭": "apple", "🍫": "cookie", "🎄": "tree-pine", "🔥": "flame", "❤": "heart", "🤍": "heart",
	"👉": "arrow-right", "◦": "circle", "✧": "sparkle", "➤": "arrow-right", "✿": "flower",
	"❀": "flower", "↗": "arrow-up-right",
	# v691 (#614, UI18, UI19): danh mục Zalo chung cai_dat_loi_chung.js.
	"🚨": "circle-alert", "🚀": "megaphone", "🛠": "wrench",
	# v693 (test live #614, UI18, UI101): biểu tượng do máy chủ trả (mẫu bút toán, vai trò, báo cáo,
	# danh mục) và ℹ ngoài dải emoji cũ của bộ quét.
	"ℹ": "info", "🩺": "stethoscope", "🏧": "banknote", "🎩": "briefcase", "👑": "crown",
	"🪪": "id-card", "💻": "laptop", "📉": "trending-down", "🥤": "cup-soda", "🩹": "bandage",
	"🍁": "leaf", "🕯": "flame", "►": "play"
}

# Chấm màu trạng thái: vẽ thành chấm tròn tô màu trạng thái của bộ chuẩn.
CHAM = {
	"🟢": "xong", "🟡": "cho", "🔴": "loi", "🟣": "nhom", "🔵": "nhom",
	"🟠": "cho", "⚪": "huy", "⭕": "loi",
}

# Biểu tượng khung chung gọi theo TÊN, không qua emoji.
KHUNG = ("chevron-left", "chevron-right", "chevron-down", "arrow-up-right", "house", "bell",
	"circle-user-round", "message-circle", "x", "check", "search", "plus", "ellipsis")
