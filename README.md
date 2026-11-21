# Lethal By Default Archive

A static copy of the band's old Google Sites archive: albums, live videos and photos.
Plain HTML, CSS and a little JavaScript, with no build step needed to view or host it.

**Live site:** `https://manmadedrummer.github.io/lbdarchive/` (after turning on GitHub Pages, see below)

## What's here

| Path | Contents |
| :-- | :-- |
| `index.html` | Home page |
| `albums-main/` | Albums (Lethal By Default and Graven-Suicide) with track links |
| `video-main/` | Live videos: embedded YouTube players plus links to the source files |
| `photos/` | Photo galleries with a click-to-enlarge viewer |
| `gravensuicide/` | Graven-Suicide landing page |
| `images/` | All images (`images/thumbs/` holds small versions for the galleries) |
| `source-pages/` | The original pages saved from Google Sites with SingleFile |
| `tools/build_site.py` | Script that regenerates the site from `source-pages/` |

## Hosting on GitHub Pages

1. Open the repo's **Settings → Pages**.
2. Under **Build and deployment**, choose **Deploy from a branch**.
3. Pick the `main` branch and the `/ (root)` folder, then **Save**.
4. After a minute or two the site is live at the address above.

## Adding the pages that are still missing

Three pages weren't in the first save, so their links still point to the old Google Sites address:

- `CD Release (11/14/2009)`
- `Live Photos`
- `Graven Suicide - Demo`

To add them, open each page on the old site, save it with SingleFile, and drop the file into `source-pages/`
named `LBDArchive - CD Release.html`, `LBDArchive - Live Photos.html` and `LBDArchive - Graven Suicide -Demo.html`.
Then rebuild:

```
pip install beautifulsoup4 lxml pillow
python tools/build_site.py source-pages .
```

The new pages appear and every link to them switches to the local copy.

## Notes

- Videos are YouTube embeds. If a video is ever removed from YouTube, the "Source file" link beneath it still points to the original file on OneDrive.
- Gallery photos are the sizes Google Sites served, which may be smaller than the originals. Keep the originals somewhere safe.
