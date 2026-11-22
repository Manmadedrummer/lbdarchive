# Lethal By Default Archive

A static copy of the band's old Google Sites archive: albums, live videos and photos.
Plain HTML, CSS and a little JavaScript. No build step is needed to view or host it.

**Live site:** https://manmadedrummer.github.io/lbdarchive/

## What's here

| Path | Contents |
| :-- | :-- |
| `index.html` | Home page |
| `albums-main/` | Albums (Lethal By Default and Graven-Suicide) with track links |
| `video-main/` | Live videos: YouTube embeds plus links to the source files |
| `photos/` | Photo galleries with a click-to-enlarge viewer |
| `gravensuicide/` | Graven-Suicide landing page |
| `images/` | Web-sized images (`images/thumbs/` holds the small gallery versions) |
| `source-pages/` | The original pages saved from Google Sites with SingleFile |
| `source-images/` | Full-size original artwork and photos (never modified) |
| `tools/build_site.py` | Regenerates the site from `source-pages/` and `source-images/` |

## Hosting on GitHub Pages

**Settings → Pages → Deploy from a branch → `main` → `/ (root)` → Save.**

## Rebuilding

```
pip install beautifulsoup4 lxml pillow
python tools/build_site.py source-pages . source-images
```

The script re-creates the pages and web-sized images from the originals. Gallery photos come from the folders in
`source-images/DONE PHOTOS/`: add or remove pictures there and rebuild. Exact duplicates are skipped, GPS and camera
data are stripped from the web copies, and black bars baked into a photo are trimmed from the web copy only.

## Still to add

`Graven Suicide - Demo` (Albums → Graven-Suicide Albums) isn't in `source-pages/` yet, so its link still points to the old
Google Sites page. Save it with SingleFile as `LBDArchive - Graven Suicide -Demo.html`, drop it in `source-pages/`, and rebuild.

## Notes

- Videos are YouTube embeds. If one is ever removed, the "Source file" link beneath it still points to the original file on OneDrive.
