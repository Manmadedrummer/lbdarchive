#!/usr/bin/env python3
"""Adds a 'Back to Archive' button to every .html file in the folders you give it (skips files that already have it).
Usage: python add_back_button.py <folder> [<folder> ...]   (run on folders that sit directly inside the repo's articles folder, e.g. articles/gravensuicide.tripod.com)"""
import sys,os,re
BACK=('<style>#back-to-archive{position:fixed;top:10px;left:10px;z-index:99999;background:#d4202c;color:#fff;font:600 13px Arial,sans-serif;'
 'letter-spacing:.05em;text-transform:uppercase;padding:8px 14px;border-radius:4px;text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,.6)}'
 '#back-to-archive:hover{background:#ff3b47}</style><a id="back-to-archive" href="../articles.html">&larr; Back to Archive</a>\n')
for d in sys.argv[1:]:
    for f in os.listdir(d):
        if f.lower().endswith(".html"):
            p=os.path.join(d,f);t=open(p,encoding="utf-8",errors="surrogateescape").read()
            if "back-to-archive" in t: continue
            t=re.sub(r"(</body>)",lambda m:BACK+m.group(1),t,count=1,flags=re.I)
            open(p,"w",encoding="utf-8",errors="surrogateescape").write(t);print("updated",p)
