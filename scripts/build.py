import json, html, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BASE = "https://guna-id.pages.dev"

def read_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def esc(value):
    return html.escape(str(value), quote=True)

tools = read_json("tools.json")
raw_categories = read_json("categories.json")
settings = read_json("settings.json")

if not isinstance(tools, list) or not tools:
    raise SystemExit("GAGAL: tools.json kosong atau format salah")

# Membaca kategori dari JSON dengan beberapa format umum.
categories = {}
if isinstance(raw_categories, list):
    for item in raw_categories:
        if isinstance(item, str):
            slug, name = item, item.replace("-", " ").title()
        elif isinstance(item, dict):
            slug = item.get("slug") or item.get("id") or item.get("category")
            name = item.get("name") or item.get("title") or item.get("label") or slug
        else:
            continue
        if slug:
            categories[str(slug)] = str(name)

for tool in tools:
    if not all(tool.get(k) for k in ("slug", "name", "description", "type", "category")):
        raise SystemExit(f"Data alat tidak lengkap: {tool}")
    categories.setdefault(
        tool["category"],
        str(tool["category"]).replace("-", " ").title()
    )

# Satu halaman per kategori, bukan satu halaman per alat.
groups = {}
for tool in tools:
    groups.setdefault(tool["category"], []).append(tool)

def page(title, description, body, canonical):
    return f'''<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{BASE}{canonical}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
<header class="header">
<a class="brand" href="/">GUNA<span>.ID</span></a>
<a href="/pages/tentang.html">Tentang</a>
</header>
<main>{body}</main>
<footer>
<p>GUNA.ID — Alat digital gratis untuk Indonesia.</p>
<a href="/pages/privacy.html">Privasi</a> ·
<a href="/pages/terms.html">Ketentuan</a> ·
<a href="/pages/disclaimer.html">Disclaimer</a> ·
<a href="/pages/kontak.html">Kontak</a>
</footer>
</body>
</html>'''

# Definisi field tiap jenis alat.
forms = {
"discount": [("a","Harga awal"),("b","Diskon (%)")],
"installment": [("a","Total pinjaman"),("b","Jumlah bulan")],
"interest": [("a","Modal"),("b","Bunga (%)")],
"profit": [("a","Pendapatan"),("b","Total biaya")],
"daily": [("a","Pendapatan hari ini"),("b","Pengeluaran hari ini")],
"margin": [("a","Harga jual"),("b","Biaya/modal")],
"bep": [("a","Biaya tetap"),("b","Harga jual per unit"),("c","Biaya variabel per unit")],
"percentage": [("a","Angka dasar"),("b","Persentase (%)")],
"selling": [("a","Modal"),("b","Target margin (%)")],
"capital": [("a","Biaya bahan"),("b","Biaya operasional"),("c","Biaya lainnya")],
"stock": [("a","Stok awal"),("b","Barang masuk"),("c","Barang keluar")],
"salary": [("a","Gaji kotor"),("b","Potongan")],
"overtime": [("a","Upah per jam"),("b","Jam lembur")],
"thr": [("a","Gaji bulanan"),("b","Masa kerja (bulan)")],
"worktime": [("a","Jam mulai (0-24)"),("b","Jam selesai (0-24)")],
"fuel": [("a","Liter BBM"),("b","Harga per liter")],
"travel": [("a","Jarak (km)"),("b","Biaya per km")],
"electricity": [("a","Pemakaian (kWh)"),("b","Tarif per kWh")],
"consumption": [("a","Jarak tempuh (km)"),("b","BBM digunakan (liter)")],
"age": [("a","Tanggal lahir","date")],
"words": [("text","Teks","textarea")],
"characters": [("text","Teks","textarea")],
"textcase": [("text","Teks","textarea"),("mode","Format","select")],
"json": [("text","JSON","textarea")],
"password": [("a","Panjang password")],
"invoice": [("text","Nama pelanggan / keterangan","textarea"),("a","Nominal")],
"receipt": [("text","Nama pembayar / keterangan","textarea"),("a","Nominal")],
"qr": [("text","Teks atau URL","textarea")]
}

def make_form(tool):
    slug, typ = tool["slug"], tool["type"]
    fields = forms.get(typ, [])
    controls = []

    for field in fields:
        fid, label = field[0], field[1]
        kind = field[2] if len(field) > 2 else "number"
        control_id = f"{slug}-{fid}"

        if kind == "textarea":
            control = f'<textarea id="{control_id}" name="{fid}" rows="4"></textarea>'
        elif kind == "select":
            control = (
                f'<select id="{control_id}" name="mode">'
                '<option value="upper">HURUF BESAR</option>'
                '<option value="lower">huruf kecil</option>'
                '<option value="title">Huruf Judul</option>'
                '</select>'
            )
        else:
            attrs = 'step="any" inputmode="decimal"' if kind == "number" else ""
            control = f'<input id="{control_id}" name="{fid}" type="{kind}" {attrs} required>'

        controls.append(f'<label for="{control_id}">{esc(label)}{control}</label>')

    if not fields:
        controls.append('<p>Jenis alat ini belum memiliki form.</p>')

    note = ""

    return f'''
<details class="tool-panel" id="{esc(slug)}">
<summary>{esc(tool["name"])}</summary>
<div class="tool-panel-body">
<p>{esc(tool["description"])}</p>
<form class="tool-form" data-type="{esc(typ)}">
{"".join(controls)}
<button type="submit">Proses</button>
</form>
<pre class="result" aria-live="polite">Hasil akan muncul di sini.</pre>
{note}
</div>
</details>'''

# Beranda: hanya kategori, pencarian tetap bisa menemukan alat individual.
category_cards = []
for slug, items in groups.items():
    label = categories[slug]
    tool_links = []
    for tool in items:
        search_text = " ".join([
            tool["name"], tool["description"], label, slug
        ]).lower()
        tool_links.append(
            f'<a class="tool-link" data-search="{esc(search_text)}" '
            f'href="/kategori/{esc(slug)}.html#{esc(tool["slug"])}">'
            f'{esc(tool["name"])}</a>'
        )

    category_cards.append(f'''
<section class="category-card" data-category="{esc(label.lower())}">
<h2><a href="/kategori/{esc(slug)}.html">{esc(label)}</a>
<span class="muted">({len(items)} alat)</span></h2>
<div class="tool-links">{"".join(tool_links)}</div>
</section>''')

home = f'''
<section class="hero">
<h1>Alat Digital Gratis untuk Indonesia</h1>
<p>Kalkulator dan alat produktivitas yang mudah digunakan.</p>
</section>
<label for="search">Cari alat</label>
<input class="search" id="search" placeholder="Cari nama alat, fungsi, atau kategori..." autocomplete="off">
<p id="search-status" class="muted" aria-live="polite">Pilih kategori atau cari alat.</p>
<div id="category-list">{"".join(category_cards)}</div>
<p id="no-results" hidden>Alat tidak ditemukan.</p>
<script>
(() => {{
 const input = document.getElementById("search");
 const cards = [...document.querySelectorAll(".category-card")];
 const status = document.getElementById("search-status");
 const empty = document.getElementById("no-results");

 function filter() {{
   const q = input.value.trim().toLocaleLowerCase("id");
   let count = 0;

   cards.forEach(card => {{
     const categoryMatch = card.dataset.category.includes(q);
     const links = [...card.querySelectorAll(".tool-link")];
     let matches = 0;

     links.forEach(link => {{
       const found = !q || categoryMatch ||
         link.dataset.search.includes(q) ||
         link.textContent.toLocaleLowerCase("id").includes(q);
       link.hidden = !found;
       if (found) matches++;
     }});

     card.hidden = q !== "" && matches === 0;
     count += matches;
   }});

   empty.hidden = count > 0;
   status.textContent = q ? count + " alat cocok." : "Pilih kategori atau cari alat.";
 }}
 input.addEventListener("input", filter);
 filter();
}})();
</script>
'''
write(ROOT / "index.html", page(
    "Alat Digital Gratis | GUNA.ID",
    "Kumpulan kalkulator dan alat produktivitas gratis untuk kebutuhan harian dan usaha.",
    home, "/"
))

# Satu halaman gabungan per kategori.
for slug, items in groups.items():
    label = categories[slug]
    body = f'''
<nav><a href="/">Beranda</a> / {esc(label)}</nav>
<h1>{esc(label)}</h1>
<p>Pilih alat yang dibutuhkan. Buka panel alat, isi data, lalu proses.</p>
<label for="group-search">Cari alat dalam kategori</label>
<input id="group-search" class="search" placeholder="Cari alat..." autocomplete="off">
<div id="group-tools">{"".join(make_form(t) for t in items)}</div>
<p id="group-empty" hidden>Alat tidak ditemukan.</p>
<script>
(() => {{
 const input = document.getElementById("group-search");
 const panels = [...document.querySelectorAll(".tool-panel")];
 const empty = document.getElementById("group-empty");
 function filter() {{
   const q = input.value.trim().toLocaleLowerCase("id");
   let count = 0;
   panels.forEach(panel => {{
     const found = panel.textContent.toLocaleLowerCase("id").includes(q);
     panel.hidden = !found;
     if (found) count++;
   }});
   empty.hidden = count > 0;
 }}
 input.addEventListener("input", filter);
 const target = location.hash.slice(1);
 if (target) {{
   const panel = document.getElementById(target);
   if (panel) {{
     panel.open = true;
     panel.scrollIntoView({{ behavior: "auto", block: "start" }});
   }}
 }}
}})();
</script>
<script src="/assets/js/app.js" defer></script>
'''
    write(ROOT / "kategori" / f"{slug}.html", page(
        f"{label} Gratis | GUNA.ID",
        f"Kumpulan alat {label.lower()} gratis di GUNA.ID.",
        body, f"/kategori/{slug}.html"
    ))

# Halaman legal yang sederhana.
legal = {
"tentang": ("Tentang GUNA.ID", "GUNA.ID menyediakan alat digital gratis.", "GUNA.ID menyediakan kalkulator dan alat produktivitas gratis."),
"privacy": ("Kebijakan Privasi", "Kebijakan privasi GUNA.ID.", "Alat inti memproses input di browser. Jangan memasukkan informasi rahasia ke alat publik."),
"terms": ("Ketentuan Layanan", "Ketentuan penggunaan GUNA.ID.", "Gunakan hasil alat sebagai estimasi dan periksa kembali hasil yang penting."),
"disclaimer": ("Disclaimer", "Batasan hasil kalkulasi GUNA.ID.", "Hasil kalkulasi merupakan perkiraan berdasarkan input pengguna, bukan nasihat profesional."),
"kontak": ("Kontak", "Informasi kontak GUNA.ID.", "Kanal kontak resmi perlu ditambahkan sebelum publikasi.")
}
for slug, (title, desc, content) in legal.items():
    write(ROOT / "pages" / f"{slug}.html", page(
        title + " | GUNA.ID", desc,
        f"<h1>{esc(title)}</h1><p>{esc(content)}</p>",
        f"/pages/{slug}.html"
    ))

write(ROOT / "404.html", page(
    "Halaman Tidak Ditemukan | GUNA.ID",
    "Halaman yang dicari tidak tersedia.",
    '<h1>Halaman tidak ditemukan</h1><p>Periksa alamat atau kembali ke beranda.</p><a href="/">Ke Beranda</a>',
    "/404.html"
))

urls = ["/"] + [f"/kategori/{slug}.html" for slug in groups]
urls += [f"/pages/{slug}.html" for slug in legal]
xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for url in urls:
    xml += f"  <url><loc>{BASE}{url}</loc></url>\n"
xml += "</urlset>\n"
write(ROOT / "sitemap.xml", xml)
write(ROOT / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")

print(f"BUILD OK: {len(groups)} halaman kategori, {len(tools)} alat.")
print("Beranda: pencarian alat, deskripsi, dan kategori.")
