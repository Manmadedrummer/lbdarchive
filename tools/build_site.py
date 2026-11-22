#!/usr/bin/env python3
"""
Build the Lethal By Default Archive static site from SingleFile saves of the
old Google Sites pages.

Usage:  python3 build_site.py <source-pages-dir> <output-dir> [source-images-dir]

Needs:  pip install beautifulsoup4 lxml pillow

Drop any new SingleFile save into the source dir (named "LBDArchive - <Title>.html")
and re-run - the page will appear in the site and links to it switch from the old
Google Sites address to the local page automatically.
"""
import sys, os, re, io, base64, hashlib, html, shutil, glob
from urllib.parse import urlparse, unquote, parse_qs
from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
IMGSRC = sys.argv[3] if len(sys.argv) > 3 else None   # folder holding your original images (source-images)
PHOTOS = os.path.join(IMGSRC, "DONE PHOTOS") if IMGSRC else None
OLD = "https://sites.google.com/view/lbdarchive/"
SITE = "Lethal By Default Archive"

# (output path, nav label, title used in the saved file name or None)
PAGES = [
    ("", "Home", None),
    ("gravensuicide", "Graven-Suicide", "GravenSuicide"),
    ("photos", "Photos", "Photos"),
    ("photos/cd-release", "CD Release (11/14/2009)", "CD Release"),
    ("photos/chataqua-park", "Chataqua Park (05/15/2010)", "Chataqua Park"),
    ("photos/cover-photos", "Cover Photos", "Cover Photos"),
    ("photos/facebook-post-photos", "Facebook Post Photos", "Facebook Post Photos"),
    ("photos/flyers", "Flyers", "Flyers"),
    ("photos/live-photos", "Live Photos", "Live Photos"),
    ("photos/profile-pictures", "Profile Pictures", "Profile Pictures"),
    ("photos/promo-photos", "Promo Photos", "Promo Photos"),
    ("photos/reverbnation", "Reverbnation", "Reverbnation"),
    ("photos/tagged", "Tagged Photos", "Tagged"),
    ("photos/the-21-club", "The 21 Club (02/19/2011)", "The 21 Club"),
    ("albums-main", "Albums", "Albums Main"),
    ("albums-main/gsalbums", "Graven-Suicide Albums", "GSAlbums"),
    ("albums-main/gsalbums/graven-suicide-demo", "Graven Suicide - Demo", "Graven Suicide -Demo"),
    ("albums-main/lbd-albums", "Lethal By Default Albums", "LBD Albums"),
    ("albums-main/lbd-albums/descent-ep", "Descent EP", "Descent EP"),
    ("albums-main/lbd-albums/live-2010", "Live 2010", "Live 2010"),
    ("albums-main/lbd-albums/shedding-illusions", "Shedding Illusions", "Shedding Illusions"),
    ("albums-main/lbd-albums/the-broadcast", "The Broadcast", "The Broadcast"),
    ("albums-main/lbd-albums/shedding-illusions-daycore", "Shedding Illusions (Day~Night)", "Shedding Illusions (Daycore)"),
    ("albums-main/lbd-albums/the-broadcast-day-night", "The Broadcast (Day~Night)", "The Broadcast (Day-Night)"),
    ("albums-main/lbd-albums/the-relay", "The Relay", "The Relay"),
    ("video-main", "Videos", "Video Main"),
    ("video-main/gsvideos", "Graven-Suicide Videos", "GSVideos"),
    ("video-main/gsvideos/woodhull-150th", "Woodhull 150th", "Woodhull 150th"),
    ("video-main/gsvideos/ricks", "Rick Thompson's", "Ricks"),
    ("video-main/gsvideos/extras", "Extras", "Extras"),
    ("video-main/lbd-videos", "Lethal By Default Videos", "LBD Videos"),
    ("video-main/lbd-videos/new-billiards", "(New) Billiards on Main", "New Billiards"),
    ("video-main/lbd-videos/old-billiards", "(Old) Billiards on Main", "Old Billiards"),
    ("video-main/lbd-videos/21-club", "21 Club", "21 Club"),
    ("video-main/lbd-videos/kewanee", "Chataqua Will Rock You Fest", "Kewanee"),
    ("video-main/lbd-videos/henry-county-fair", "Henry County Fair", "Henry County Fair"),
    ("video-main/lbd-videos/best-western", "Best Western", "Best Western"),
    ("video-main/lbd-videos/labor-temple", "Labor Temple", "Labor Temple"),
    ("video-main/lbd-videos/pops", "Pop's NightClub & Concert Venue", "Pops"),
    ("video-main/lbd-videos/rme", "River Music Experience", "RME"),
    ("video-main/lbd-videos/springstock", "Springstock", "Springstock"),
    ("video-main/lbd-videos/old-billiards-on-main", "Old Billiards on Main /w Dax", "Old Billiards On Main"),
    ("video-main/lbd-videos/bsides", "B-Sides", "Bsides"),
]
LABEL = {p: l for p, l, _ in PAGES}
TITLE2PATH = {t: p for p, _, t in PAGES if t}

# hashes (md5 of the data URI, first 6 hex) of the shared site art
H_BG, H_LOGO_WIDE, H_LOGO_SQ = "c1a35c", "2ab62b", "2fe7b6"


def h6(s):
    return hashlib.md5(s.encode()).hexdigest()[:6]


# stored-image name -> original file in source-images (used instead of the copy embedded in the saved page)
OVERRIDE = {
    "albums-main-lbd-albums-descent-ep-cover": "Descent.jpg",
    "albums-main-lbd-albums-live-2010-cover": "lbd.jpg",
    "albums-main-lbd-albums-shedding-illusions-cover": "SheddingIllusions.jpg",
    "albums-main-lbd-albums-shedding-illusions-daycore-cover": "SIDaycore.png",
    "albums-main-lbd-albums-shedding-illusions-daycore-cover-2": "SINightcore.jpg",
    "albums-main-lbd-albums-the-broadcast-cover": "The Broadcast.jpg",
    "albums-main-lbd-albums-the-broadcast-day-night-cover": "BroadcastDaycore.jpg",
    "albums-main-lbd-albums-the-broadcast-day-night-cover-2": "BroadcastNightcore.jpg",
    "albums-main-lbd-albums-the-relay-cover": "TheRelay.jpg",
    "card-21-club": "21Club.jpg", "card-albums": "Albums.png", "card-b-sides": "Bsides.jpg",
    "card-best-western": "BestWestern.png", "card-chataqua-will-rock-you-fest": "Kewanee.jpg",
    "card-demo": "GSDemo.jpg", "card-descent": "Descent.jpg", "card-extras": "Extras.jpg",
    "card-graven-suicidealbums": "GSLOGO.jpg", "card-henry-county-fair": "Fair.jpg",
    "card-labor-temple": "LaborTemple.jpg", "card-lethal-by-defaultalbums": "lbd.jpg",
    "card-live-2010": "lbd.jpg", "card-new-billiards-on-main": "NewBilliards.jpg",
    "card-old-billiards-on-main-w-dax": "OBOM.png", "card-old-billiards-on-main": "Old Billiards.jpg",
    "card-pop-s-nightclub-concert-venue": "Pops.jpg", "card-rick-thompson-s": "Ricks.jpg",
    "card-river-music-experience": "RME.jpg", "card-shedding-illusions-day-night": "SIDay-Night.jpg",
    "card-shedding-illusions": "SheddingIllusions.jpg", "card-springstock": "Springstock.jpg",
    "card-the-braodcast-day-night": "BroadcastDayNight.jpg", "card-the-broadcast": "The Broadcast.jpg",
    "card-the-relay": "TheRelay.jpg", "card-videos": "Video.png", "card-woodhull-150th": "Woodhull150th.jpg",
}
# page path -> folder under "DONE PHOTOS" (full-size originals replace the pictures saved from Google Sites)
PHOTO_DIRS = {
    "photos/cd-release": "CD Release (11-14-09)", "photos/chataqua-park": "Chataqua Park (5-15-10)",
    "photos/cover-photos": "CoverPhotos", "photos/facebook-post-photos": "Facebook Post Photos",
    "photos/flyers": "Flyers", "photos/live-photos": "Live Photos", "photos/profile-pictures": "ProfilePictures",
    "photos/promo-photos": "Promo Photos", "photos/reverbnation": "Reverbnation", "photos/tagged": "Tagged",
    "photos/the-21-club": "The 21 Club (2-19-11)",
}
WEB_MAX = 1800     # longest edge of the full-size web copy
CARD_MAX = 1400


def natkey(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def trim_black(im):
    """Crop pure-black bars baked into an image (web copy only; originals are untouched)."""
    import numpy as np
    a = np.asarray(im.convert("L"))
    h, w = a.shape
    cols = np.where(a.max(axis=0) > 14)[0]
    rows = np.where(a.max(axis=1) > 14)[0]
    if len(cols) == 0 or len(rows) == 0:
        return im
    l, r, t, b = cols[0], cols[-1] + 1, rows[0], rows[-1] + 1
    if (r - l) < 0.4 * w or (b - t) < 0.4 * h:
        return im
    if (l + (w - r)) < 0.03 * w and (t + (h - b)) < 0.03 * h:
        return im
    return im.crop((l, t, r, b))


def web_copy(src_path, dest_rel_noext, maxedge, thumb=False):
    """Resize an original to a web-friendly JPEG (EXIF/GPS stripped). Returns file name under images/."""
    im = Image.open(src_path)
    try:
        from PIL import ImageOps
        im = ImageOps.exif_transpose(im)
    except Exception:
        pass
    if im.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", im.size, (0, 0, 0))
        im = im.convert("RGBA"); bg.paste(im, mask=im.split()[-1]); im = bg
    else:
        im = im.convert("RGB")
    if thumb:
        im = trim_black(im)
    full = im.copy()
    full.thumbnail((maxedge, maxedge), Image.LANCZOS)
    full.save(os.path.join(OUT, "images", dest_rel_noext + ".jpg"), "JPEG", quality=86, optimize=True, progressive=True)
    if thumb:
        t = im.copy(); t.thumbnail((640, 640), Image.LANCZOS)
        t.save(os.path.join(OUT, "images/thumbs", dest_rel_noext + ".jpg"), "JPEG", quality=80, optimize=True)
    return dest_rel_noext + ".jpg"


def folder_gallery(page_path):
    """Return list of image file names (under images/) built from the original photos folder, de-duplicated."""
    if not PHOTOS or page_path not in PHOTO_DIRS:
        return None
    d = os.path.join(PHOTOS, PHOTO_DIRS[page_path])
    if not os.path.isdir(d):
        return None
    files = sorted([f for f in os.listdir(d) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))], key=natkey)
    seen, out, base = set(), [], slug(page_path)
    n = 0
    for f in files:
        raw = open(os.path.join(d, f), "rb").read()
        hh = hashlib.md5(raw).hexdigest()
        if hh in seen:
            continue
        seen.add(hh)
        n += 1
        out.append(web_copy(os.path.join(d, f), f"{base}-{n:03d}", WEB_MAX, thumb=True))
    return out


# ---------------------------------------------------------------- images
os.makedirs(OUT, exist_ok=True)
for d in ("images/site", "images/thumbs", "css", "js"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)

IMG_BY_HASH = {}   # hash -> relative file name under images/
USED_NAMES = set()
DATA_RE = re.compile(r"data:image/([\w+.-]+);base64,([A-Za-z0-9+/=]{100,})")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "x"


def store_image(datauri, hint, thumb=False):
    h = h6(datauri)
    if h in IMG_BY_HASH:
        return IMG_BY_HASH[h]
    m = DATA_RE.match(datauri)
    kind, b64 = m.group(1).split("+")[0], m.group(2)
    ext = {"jpeg": "jpg"}.get(kind, kind)
    name = slug(hint)
    base, n = name, 2
    while name in USED_NAMES:
        name = f"{base}-{n}"; n += 1
    USED_NAMES.add(name)
    if IMGSRC and name in OVERRIDE and os.path.exists(os.path.join(IMGSRC, OVERRIDE[name])):
        rel = web_copy(os.path.join(IMGSRC, OVERRIDE[name]), name, CARD_MAX)
        IMG_BY_HASH[h] = rel
        return rel
    rel = f"{name}.{ext}"
    raw = base64.b64decode(b64 + "===")
    with open(os.path.join(OUT, "images", rel), "wb") as f:
        f.write(raw)
    if thumb:
        try:
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            im.thumbnail((640, 640))
            im.save(os.path.join(OUT, "images/thumbs", f"{name}.jpg"), "JPEG", quality=80, optimize=True)
        except Exception as e:
            print("thumb failed", rel, e)
    IMG_BY_HASH[h] = rel
    return rel


# ---------------------------------------------------------------- parsing
def resolve(href):
    """Return ('int', outpath) / ('ext', url) / (None, None)."""
    if not href or href.startswith("#"):
        return None, None
    u = href
    if "google.com/url" in u:
        q = parse_qs(urlparse(u).query).get("q")
        if q:
            u = q[0]
    if u.startswith(OLD):
        p = u[len(OLD):].split("?")[0].split("#")[0].strip("/")
        if p == "home":
            p = ""
        if p == "home/gravensuicide":
            p = "gravensuicide"
        return "int", p
    return "ext", u


def inline(node):
    out = []
    for c in node.children:
        if isinstance(c, NavigableString):
            out.append(html.escape(str(c).replace("\xa0", " ")))
        elif isinstance(c, Tag):
            if c.name == "br":
                out.append("<br>")
            elif c.name == "a":
                kind, tgt = resolve(c.get("href", ""))
                inner = inline(c)
                if kind is None:
                    out.append(inner)
                else:
                    out.append(f'<a href="@@{kind}:{html.escape(tgt, quote=True)}@@">{inner}</a>')
            else:
                out.append(inline(c))
    return "".join(out)


def first_link(node):
    for a in node.find_all("a"):
        k, t = resolve(a.get("href", ""))
        if k:
            return k, t
    return None, None


def parse(path, pagepath):
    t = open(path, encoding="utf-8", errors="replace").read()
    t = DATA_RE.sub(lambda m: "IMGDATA:" + base64.b64encode(m.group(0).encode()).decode(), t)
    s = BeautifulSoup(t, "lxml")
    for x in s(["script", "style", "svg", "noscript", "link", "meta"]):
        x.decompose()
    sec = s.find("section")
    root = sec.parent if sec else s.body
    blocks = []

    def datauri(tag_style_or_src):
        m = re.search(r"IMGDATA:([A-Za-z0-9+/=]+)", tag_style_or_src or "")
        return base64.b64decode(m.group(1)).decode() if m else None

    def walk(n):
        for c in n.children:
            if not isinstance(c, Tag):
                continue
            nm, st = c.name, c.get("style", "")
            if nm in ("h1", "h2", "h3", "h4", "h5", "h6", "p"):
                txt = c.get_text("", strip=True).replace("\xa0", " ")
                if not txt:
                    continue
                k, tgt = first_link(c)
                blocks.append(dict(t="h" if nm != "p" else "p", level=nm, html=inline(c), text=txt, lk=k, lt=tgt))
                continue
            if nm == "iframe":
                sd = c.get("srcdoc", "") or ""
                v = re.search(r"watch\?v=([\w-]{11})", sd)
                ti = re.search(r"<title>(.*?)</title>", sd)
                if v:
                    blocks.append(dict(t="video", id=v.group(1), title=html.unescape(re.sub(r" - YouTube$", "", ti.group(1))) if ti else ""))
                continue
            if nm == "img":
                d = datauri(c.get("src"))
                if d:
                    blocks.append(dict(t="img", data=d))
                continue
            if "background" in st and "IMGDATA" in st:
                d = datauri(st)
                if d and h6(d) != H_BG:
                    if c.get("aria-label") == "Carousel image":
                        blocks.append(dict(t="gal", data=d))
                    else:
                        blocks.append(dict(t="img", data=d))
                continue
            walk(c)

    walk(root)
    # merge consecutive gallery images
    merged = []
    for b in blocks:
        if b["t"] == "gal" and merged and merged[-1]["t"] == "gallery":
            merged[-1]["data"].append(b["data"])
        elif b["t"] == "gal":
            merged.append(dict(t="gallery", data=[b["data"]]))
        else:
            merged.append(b)
    blocks = merged
    title = pagepath
    if blocks and blocks[0]["t"] == "h":
        title = blocks[0]
        blocks = blocks[1:]
    return title, blocks


# ---------------------------------------------------------------- load
pages = {}
for p, label, ft in PAGES:
    if not ft:
        continue
    fn = os.path.join(SRC, f"LBDArchive - {ft}.html")
    if os.path.exists(fn):
        ttl, blocks = parse(fn, p)
        pages[p] = dict(path=p, label=LABEL[p], h1=ttl["text"] if isinstance(ttl, dict) else ttl, blocks=blocks)
# galleries rebuilt from the original photo folders (also creates pages that were never saved)
for gp, folder in PHOTO_DIRS.items():
    files = folder_gallery(gp)
    if not files:
        continue
    if gp in pages:
        pages[gp]["blocks"] = [b for b in pages[gp]["blocks"] if b["t"] not in ("gallery", "img")] + [dict(t="gallery", files=files)]
    else:
        pages[gp] = dict(path=gp, label=LABEL[gp], h1=LABEL[gp], blocks=[dict(t="gallery", files=files)])
    print("gallery", gp, len(files), "photos")
missing = [p for p, _, ft in PAGES if ft and p not in pages]
print("pages built:", len(pages), "| still not saved:", missing)


def depth(p):
    return 0 if p == "" else p.count("/") + 1


def rel(from_p, to_p, file=True):
    """relative URL from page from_p to page to_p (index.html explicit so it works from disk)."""
    up = "../" * depth(from_p)
    return up + (to_p + "/" if to_p else "") + "index.html"


def fix_links(h, cur):
    def sub(m):
        kind, tgt = m.group(1), html.unescape(m.group(2))
        if kind == "int":
            if tgt in pages or tgt == "":
                return f'href="{rel(cur, tgt)}"'
            return f'href="{OLD}{tgt}" target="_blank" rel="noopener"'
        return f'href="{html.escape(tgt, quote=True)}" target="_blank" rel="noopener"'
    return re.sub(r'href="@@(int|ext):(.*?)@@"', sub, h)


def target_href(kind, tgt, cur):
    if kind == "int":
        if tgt in pages or tgt == "":
            return rel(cur, tgt), ""
        return OLD + tgt, ' target="_blank" rel="noopener"'
    return tgt, ' target="_blank" rel="noopener"'


# ---------------------------------------------------------------- rendering
def crumbs(p):
    out = [("", "Home")]
    parts = p.split("/") if p else []
    for i in range(1, len(parts) + 1):
        pp = "/".join(parts[:i])
        out.append((pp, LABEL.get(pp, parts[i - 1])))
    return out


def is_hub(blocks):
    return any(b["t"] in ("h", "p") and b["lk"] == "int" for b in blocks) and not any(b["t"] == "video" for b in blocks)


def build_cards(blocks, cur):
    """Group img + linked headings/paragraphs into cards. Returns list of ('card',...) or ('label',text) or ('p',html)."""
    items, card = [], None

    def flush():
        nonlocal card
        if card and (card.get("title") or card.get("img")):
            items.append(("card", card))
        card = None

    for b in blocks:
        if b["t"] == "img":
            flush()
            card = dict(img=b["data"], kicker=[], desc=[], title=None, href=None, from_p=False)
        elif b["t"] in ("h", "p"):
            linked = b["lk"] == "int" or (b["lk"] == "ext" and b["t"] == "h")
            if card is None:
                if linked:
                    card = dict(img=None, kicker=[], desc=[], title=None, href=None, from_p=False)
                else:
                    items.append(("p", b["html"])); continue
            if linked and card["title"] is None:
                card["title"] = b["text"]; card["href"] = (b["lk"], b["lt"]); card["from_p"] = b["t"] == "p"
            elif linked:
                flush()
                card = dict(img=None, kicker=[], desc=[], title=b["text"], href=(b["lk"], b["lt"]), from_p=b["t"] == "p")
            else:
                if card["title"] is None:
                    card["kicker"].append(b["text"])
                elif card["from_p"] and len(b["text"]) < 30:
                    flush(); items.append(("label", b["text"]))
                else:
                    card["desc"].append(b["text"])
    flush()
    return items


def render_card(c, cur, first_gallery_thumb):
    href, extra = target_href(c["href"][0], c["href"][1], cur) if c["href"] else ("#", "")
    img = ""
    if c["img"]:
        f = store_image(c["img"], "card-" + slug(c["title"] or "x"))
        img = f'<img src="{"../" * depth(cur)}images/{f}" alt="" loading="lazy">'
    elif c["href"] and c["href"][0] == "int" and c["href"][1] in first_gallery_thumb:
        img = f'<img src="{"../" * depth(cur)}images/thumbs/{first_gallery_thumb[c["href"][1]]}" alt="" loading="lazy">'
    kick = "".join(f'<span class="kicker">{html.escape(k)}</span>' for k in c["kicker"])
    desc = "".join(f"<p>{html.escape(d)}</p>" for d in c["desc"])
    cls = "card" + ("" if img else " noimg")
    return f'<a class="{cls}" href="{href}"{extra}><div class="thumb">{img}</div><div class="body">{kick}<h3>{html.escape(c["title"] or "")}</h3>{desc}</div></a>'


def render(page, first_gallery_thumb):
    cur = page["path"]
    up = "../" * depth(cur)
    b = page["blocks"]
    body = []
    slugname = slug(cur or "home")
    gal_idx = 0
    if is_hub(b):
        grid = []
        for kind, v in build_cards(b, cur):
            if kind == "card":
                grid.append(render_card(v, cur, first_gallery_thumb))
            else:
                if grid:
                    body.append('<div class="cards">' + "".join(grid) + "</div>"); grid = []
                body.append(f'<h2 class="label">{html.escape(v)}</h2>' if kind == "label" else f'<p class="intro">{fix_links(v, cur)}</p>')
        if grid:
            body.append('<div class="cards">' + "".join(grid) + "</div>")
    else:
        i = 0
        while i < len(b):
            x = b[i]
            if x["t"] == "gallery":
                gal_idx += 1
                figs = []
                items_ = x["files"] if "files" in x else x["data"]
                for n, d in enumerate(items_, 1):
                    f = d if "files" in x else store_image(d, f"{slugname}-{n:02d}", thumb=True)
                    figs.append(f'<a href="{up}images/{f}" data-lb><img src="{up}images/thumbs/{os.path.splitext(f)[0]}.jpg" alt="{html.escape(page["h1"])} photo {n}" loading="lazy"></a>')
                body.append(f'<div class="gallery">{"".join(figs)}</div>')
            elif x["t"] == "video":
                cap = []
                j = i + 1
                while j < len(b) and b[j]["t"] == "p":
                    cap.append(b[j]); j += 1
                caption = "".join(f"<p>{fix_links(c['html'], cur)}</p>" for c in cap)
                caption = re.sub(r'(<a href="[^"]*"[^>]*>)\s*Source\s*(</a>)', r'\1Source file\2', caption)
                title = html.escape(x["title"] or (cap[0]["text"] if cap else "Video"))
                body.append(
                    f'<article class="video"><div class="player"><iframe src="https://www.youtube-nocookie.com/embed/{x["id"]}" title="{title}" loading="lazy" '
                    f'allow="accelerometer; encrypted-media; picture-in-picture" allowfullscreen></iframe></div><div class="cap">{caption}</div></article>')
                i = j; continue
            elif x["t"] == "img":
                album = cur.startswith("albums-main/")
                f = store_image(x["data"], f"{slugname}-" + ("cover" if album else "image"))
                alt = f'{page["h1"]} cover art' if album else page["h1"]
                body.append(f'<figure class="cover"><img src="{up}images/{f}" alt="{html.escape(alt)}"></figure>')
            elif x["t"] == "h":
                lvl = "h2" if x["level"] in ("h1", "h2") else "h3"
                body.append(f'<{lvl}>{fix_links(x["html"], cur)}</{lvl}>')
            elif x["t"] == "p":
                cls = ' class="tracks"' if "1drv.ms" in x["html"] or "@@ext:" in x["html"] else ""
                body.append(f'<p{cls}>{fix_links(x["html"], cur)}</p>')
            i += 1
    nav = [("", "Home"), ("albums-main", "Albums"), ("video-main", "Videos"), ("photos", "Photos"), ("gravensuicide", "Graven-Suicide")]
    navhtml = "".join(
        f'<a href="{rel(cur, p) if (p in pages or p == "") else OLD + p}"{" class=on" if (cur == p or (p and cur.startswith(p + "/"))) else ""}>{l}</a>' for p, l in nav)
    cr = crumbs(cur)
    crhtml = " <span>/</span> ".join(
        (f'<a href="{rel(cur, p)}">{html.escape(l)}</a>' if (p in pages or p == "") and p != cur else html.escape(l)) for p, l in cr) if cur else ""
    title = page["h1"] if cur else SITE
    return PAGE_TMPL.format(
        title=html.escape(f"{title} · {SITE}" if cur else SITE), up=up, nav=navhtml, crumbs=f'<nav class="crumbs" aria-label="Breadcrumb">{crhtml}</nav>' if cur else "",
        h1=html.escape(page["h1"]), body="\n".join(body), home=rel(cur, ""))


PAGE_TMPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="Archive of the band Lethal By Default: albums, live videos, and photos.">
<link rel="icon" href="{up}images/site/logo-square.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}css/style.css">
</head>
<body>
<header class="top">
  <a class="brand" href="{home}"><img src="{up}images/site/logo-wide.jpg" alt="Lethal By Default"></a>
  <nav class="main" aria-label="Main">{nav}</nav>
</header>
<main>
  {crumbs}
  <h1>{h1}</h1>
  {body}
</main>
<footer>Lethal By Default Archive · Galesburg, IL</footer>
<script src="{up}js/site.js"></script>
</body>
</html>
"""

HOME_TMPL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lethal By Default Archive</title>
<meta name="description" content="Archive of the band Lethal By Default: albums, live videos, and photos.">
<link rel="icon" href="images/site/logo-square.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
</head>
<body class="home">
<header class="top">
  <a class="brand" href="index.html"><img src="images/site/logo-wide.jpg" alt="Lethal By Default"></a>
  <nav class="main" aria-label="Main">{nav}</nav>
</header>
<main>
  <section class="hero">
    <img src="images/site/logo-square.png" alt="Lethal By Default logo" width="320" height="320">
    <h1>Lethal By Default Archive</h1>
    <p>Albums, live videos and photos from the Galesburg, Illinois band, kept in one place.</p>
  </section>
  <div class="cards">{cards}</div>
</main>
<footer>Lethal By Default Archive · Galesburg, IL</footer>
</body>
</html>
"""


# ---------------------------------------------------------------- shared art
def find_shared():
    src = open(os.path.join(SRC, "LBDArchive - Albums Main.html"), encoding="utf-8", errors="replace").read()
    for m in DATA_RE.finditer(src):
        h = h6(m.group(0))
        raw = base64.b64decode(m.group(2) + "===")
        if h == H_BG:
            open(os.path.join(OUT, "images/site/bg.jpg"), "wb").write(raw)
        elif h == H_LOGO_WIDE:
            open(os.path.join(OUT, "images/site/logo-wide.jpg"), "wb").write(raw)
        elif h == H_LOGO_SQ:
            open(os.path.join(OUT, "images/site/logo-square.png"), "wb").write(raw)


find_shared()
if IMGSRC:
    for src_, dst_ in (("logo.jpg", "images/site/logo-wide.jpg"), ("bg.jpg", "images/site/bg.jpg")):
        if os.path.exists(os.path.join(IMGSRC, src_)):
            shutil.copy(os.path.join(IMGSRC, src_), os.path.join(OUT, dst_))
    if os.path.exists(os.path.join(IMGSRC, "lbd.jpg")):
        im_ = Image.open(os.path.join(IMGSRC, "lbd.jpg")).convert("RGB")
        im_.thumbnail((512, 512)); im_.save(os.path.join(OUT, "images/site/logo-square.png"), optimize=True)

# first gallery thumbnail per gallery page (used as card art on the Photos hub)
first_gallery_thumb = {}
for p, pg in pages.items():
    for blk in pg["blocks"]:
        if blk["t"] == "gallery" and "files" in blk:
            first_gallery_thumb[p] = os.path.splitext(blk["files"][0])[0] + ".jpg"
            break
        if blk["t"] == "gallery" or (blk["t"] == "img" and p.startswith("photos/")):
            d0 = blk["data"][0] if blk["t"] == "gallery" else blk["data"]
            f = store_image(d0, f"{slug(p or 'home')}-01", thumb=True)
            first_gallery_thumb[p] = os.path.splitext(f)[0] + ".jpg"
            break

# ---------------------------------------------------------------- write pages
for p, pg in pages.items():
    d = os.path.join(OUT, p)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(render(pg, first_gallery_thumb))

# home page (hand built; the old home page held 4 picture links)
nav = [("", "Home"), ("albums-main", "Albums"), ("video-main", "Videos"), ("photos", "Photos"), ("gravensuicide", "Graven-Suicide")]
navhtml = "".join(f'<a href="{rel("", p)}"{" class=on" if p == "" else ""}>{l}</a>' for p, l in nav)
art = {}
if "albums-main" in pages:
    for b in pages["albums-main"]["blocks"]:
        if b["t"] == "img":
            art.setdefault("albums", store_image(b["data"], "card-lethal-by-default-albums"))
if "gravensuicide" in pages:
    for b in pages["gravensuicide"]["blocks"]:
        if b["t"] == "img":
            art.setdefault("gs", store_image(b["data"], "card-graven-suicide"))
def src_card(fn, name):
    fp = os.path.join(IMGSRC, fn) if IMGSRC else None
    return web_copy(fp, name, CARD_MAX) if fp and os.path.exists(fp) else None


for k, (fn, nm) in {"albums": ("Albums.png", "home-albums"), "videos": ("Video.png", "home-videos"),
                    "photos": ("Photos.png", "home-photos"), "gs": ("GSLOGO.jpg", "home-graven-suicide")}.items():
    v = src_card(fn, nm)
    if v:
        art[k] = v
if "video-main/lbd-videos" in pages and "videos" not in art:
    for b in pages["video-main/lbd-videos"]["blocks"]:
        if b["t"] == "img":
            art.setdefault("videos", store_image(b["data"], "card-videos"))
home_cards = [
    ("albums-main", "Albums", "Lethal By Default and Graven-Suicide albums, remixes and remasters.", art.get("albums")),
    ("video-main", "Videos", "Live shows and extras from both bands.", art.get("videos")),
    ("photos", "Photos", "Flyers, promo shots, live photos and more.", art.get("photos")),
    ("gravensuicide", "Graven-Suicide", "The earlier band: albums and videos.", art.get("gs")),
]
chtml = []
for p, t, dsc, im in home_cards:
    if im is None and (p == "photos" and "photos/promo-photos" in first_gallery_thumb):
        pic = f'<img src="images/thumbs/{first_gallery_thumb["photos/promo-photos"]}" alt="" loading="lazy">'
    elif im:
        pic = f'<img src="images/{im}" alt="" loading="lazy">'
    else:
        pic = ""
    chtml.append(f'<a class="card{"" if pic else " noimg"}" href="{rel("", p)}"><div class="thumb">{pic}</div><div class="body"><h3>{t}</h3><p>{dsc}</p></div></a>')
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(HOME_TMPL.format(nav=navhtml, cards="".join(chtml)))

# ---------------------------------------------------------------- css / js
open(os.path.join(OUT, "css/style.css"), "w", encoding="utf-8").write(r""":root{
  --bg:#0b0b0c; --panel:rgba(18,18,20,.82); --line:#2a2a2e; --text:#e8e6e3; --muted:#a09d99;
  --red:#e0202a; --red-hi:#ff3b45;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg) url(../images/site/bg.jpg) center/cover fixed;color:var(--text);
  font:16px/1.6 Inter,system-ui,Segoe UI,sans-serif;min-height:100vh;display:flex;flex-direction:column}
body::before{content:"";position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:-1}
a{color:var(--red-hi);text-underline-offset:3px}
a:hover{color:#fff}
.top{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;
  padding:10px max(16px,calc((100% - 1100px)/2));background:rgba(0,0,0,.78);border-bottom:2px solid var(--red);position:sticky;top:0;z-index:10;backdrop-filter:blur(6px)}
.brand img{display:block;height:46px;width:auto}
.main{display:flex;gap:4px;flex-wrap:wrap}
.main a{font:500 15px/1 Oswald,sans-serif;letter-spacing:.08em;text-transform:uppercase;text-decoration:none;color:var(--text);padding:10px 14px;border-radius:3px}
.main a:hover,.main a.on{background:var(--red);color:#fff}
main{width:100%;max-width:1100px;margin:0 auto;padding:28px 16px 56px;flex:1}
h1,h2,h3{font-family:Oswald,sans-serif;font-weight:700;letter-spacing:.03em;line-height:1.15}
h1{font-size:clamp(30px,5vw,48px);margin:.2em 0 .6em;text-transform:uppercase;text-shadow:0 2px 14px #000}
h1::after{content:"";display:block;width:84px;height:4px;background:var(--red);margin-top:12px}
h2{font-size:26px;margin:1.6em 0 .5em;text-transform:uppercase}
h3{font-size:20px;margin:1.2em 0 .4em}
.crumbs{font-size:14px;color:var(--muted)} .crumbs a{color:var(--muted)} .crumbs a:hover{color:#fff} .crumbs span{margin:0 4px;opacity:.6}
.intro{color:var(--muted);max-width:70ch}

.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:18px;margin:20px 0}
.card{display:flex;flex-direction:column;background:var(--panel);border:1px solid var(--line);border-radius:6px;overflow:hidden;
  text-decoration:none;color:var(--text);transition:transform .15s,border-color .15s,box-shadow .15s}
.card:hover{transform:translateY(-3px);border-color:var(--red);box-shadow:0 8px 26px rgba(224,32,42,.25);color:var(--text)}
.card .thumb{aspect-ratio:4/3;background:#000;overflow:hidden}
.card.noimg .thumb{display:none}
.card.noimg{align-self:start}
.card .thumb img{width:100%;height:100%;object-fit:cover;display:block}
.card .body{padding:14px 16px 16px}
.card h3{margin:0;font-size:20px;text-transform:uppercase}
.card p{margin:.4em 0 0;color:var(--muted);font-size:14px}
.card .kicker{display:block;font:500 12px Oswald,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--red-hi);margin-bottom:2px}
.card.noimg .body{padding:18px 18px}
.label{margin-top:2em;border-bottom:1px solid var(--line);padding-bottom:6px}

.gallery{columns:3 240px;column-gap:12px;margin:20px 0}
.gallery a{display:block;margin:0 0 12px;break-inside:avoid;border:1px solid var(--line);border-radius:4px;overflow:hidden;background:#000}
.gallery img{width:100%;display:block;transition:transform .25s,opacity .25s}
.gallery a:hover img{transform:scale(1.03);opacity:.9}

.cover{margin:20px 0}.cover img{max-width:min(100%,360px);border-radius:6px;border:1px solid var(--line);display:block}
.tracks{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--red);padding:14px 18px;border-radius:4px;max-width:620px}

.video{margin:26px 0;background:var(--panel);border:1px solid var(--line);border-radius:6px;overflow:hidden}
.player{aspect-ratio:16/9;background:#000}.player iframe{width:100%;height:100%;border:0;display:block}
.cap{padding:12px 16px}.cap p{margin:.2em 0}

footer{text-align:center;color:var(--muted);font-size:13px;padding:22px 16px;border-top:1px solid var(--line);background:rgba(0,0,0,.7)}

.hero{text-align:center;padding:24px 0 8px}
.hero img{width:min(240px,60vw);height:auto;filter:drop-shadow(0 6px 24px rgba(224,32,42,.45))}
.hero h1::after{margin-left:auto;margin-right:auto}
.hero p{color:var(--muted);max-width:56ch;margin:0 auto}

.lb{position:fixed;inset:0;background:rgba(0,0,0,.93);z-index:50;display:none;align-items:center;justify-content:center;padding:24px}
.lb.open{display:flex}.lb img{max-width:100%;max-height:100%;border-radius:4px}
.lb button{position:absolute;background:rgba(0,0,0,.6);color:#fff;border:1px solid #444;font-size:26px;width:46px;height:46px;border-radius:50%;cursor:pointer}
.lb button:hover{background:var(--red)}
.lb .x{top:16px;right:16px}.lb .p{left:14px;top:50%}.lb .n{right:14px;top:50%}
@media(max-width:560px){.brand img{height:38px}.main a{padding:8px 10px;font-size:13px}.lb .p,.lb .n{top:auto;bottom:16px}}
""")

open(os.path.join(OUT, "js/site.js"), "w", encoding="utf-8").write(r"""(function(){
  var links=[].slice.call(document.querySelectorAll('a[data-lb]'));
  if(!links.length) return;
  var box=document.createElement('div');box.className='lb';box.setAttribute('role','dialog');box.setAttribute('aria-label','Photo viewer');
  box.innerHTML='<button class="x" aria-label="Close">×</button><button class="p" aria-label="Previous">‹</button><img alt=""><button class="n" aria-label="Next">›</button>';
  document.body.appendChild(box);
  var img=box.querySelector('img'),i=0;
  function show(k){i=(k+links.length)%links.length;img.src=links[i].href;img.alt=links[i].querySelector('img').alt;box.classList.add('open');}
  function hide(){box.classList.remove('open');img.removeAttribute('src');}
  links.forEach(function(a,k){a.addEventListener('click',function(e){e.preventDefault();show(k);});});
  box.querySelector('.x').onclick=hide;box.querySelector('.p').onclick=function(){show(i-1)};box.querySelector('.n').onclick=function(){show(i+1)};
  box.addEventListener('click',function(e){if(e.target===box)hide();});
  document.addEventListener('keydown',function(e){if(!box.classList.contains('open'))return;
    if(e.key==='Escape')hide();else if(e.key==='ArrowLeft')show(i-1);else if(e.key==='ArrowRight')show(i+1);});
})();
""")

print("images stored:", len(IMG_BY_HASH))
