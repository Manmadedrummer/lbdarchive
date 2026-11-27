/* Offline behaviour for the Lethal By Default ReverbNation rebuild.
   No libraries. Settings live in config.js, content in data.js. */
(function () {
  'use strict';
  var C = window.RN_CONFIG || {}, S = window.RN_SONGS || [], V = window.RN_VIDEOS || [], BIO = window.RN_BIO || '';
  var LIVE = '';
  var COLOR = '#b97c4e', COLOR_DONE = '#7a4a28';

  function $(s, c) { return (c || document).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); }
  function fmt(t) { t = Math.max(0, Math.floor(t || 0)); return Math.floor(t / 60) + ':' + ('0' + (t % 60)).slice(-2); }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;'); }
  function idxById(id) { for (var i = 0; i < S.length; i++) if (S[i].id === String(id)) return i; return -1; }
  function sameSong(i, j) { return i >= 0 && j >= 0 && S[i].slug === S[j].slug; }

  /* ---------- toast + modal ---------- */
  var toastT;
  function toast(msg) {
    var t = $('#rnToast'); if (!t) return;
    t.textContent = msg; t.hidden = false; clearTimeout(toastT);
    toastT = setTimeout(function () { t.hidden = true; }, 4200);
  }
  function modal(html) { $('#rnModalBody').innerHTML = html; $('#rnModal').hidden = false; }
  function closeModal() { $('#rnModal').hidden = true; $('#rnModalBody').innerHTML = ''; var b = $('#rnModal .rn-modal__box'); if (b) b.style.maxWidth = ''; }
  function copyText(txt) {
    if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(txt);
    var ta = document.createElement('textarea'); ta.value = txt; document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch (e) {} document.body.removeChild(ta); return Promise.resolve();
  }
  function shareModal(title, url) {
    modal('<h3>' + esc(title) + '</h3><div class="rn-share"><input id="rnShareUrl" readonly value="' + esc(url) + '"><button id="rnShareCopy">Copy link</button></div>');
    var inp = $('#rnShareUrl'); inp.select();
    $('#rnShareCopy').onclick = function () { copyText(url).then(function () { toast('Link copied'); }); };
  }
  function lyricsModal(i) {
    var s = S[i]; if (!s) return;
    modal('<h3>' + esc(s.title) + '</h3>' + (s.lyrics ? '<pre>' + esc(s.lyrics) + '</pre>' : '<p>No lyrics have been added for this song.</p>'));
  }

  /* ---------- audio ---------- */
  function srcFor(s) {
    if (C.audio && C.audio[s.slug]) return C.audio[s.slug];
    if (C.archiveItem) {
      var f = (C.archiveFiles && C.archiveFiles[s.slug]) || s.local.split('/').pop();
      return 'https://archive.org/download/' + encodeURIComponent(C.archiveItem) + '/' + encodeURIComponent(f);
    }
    return s.local;
  }
  var aud = new Audio(); aud.preload = 'none';
  var cur = -1;
  var shown = 0;           // song the featured player is showing
  var pageSlug = (location.pathname.split('/').pop() || '').toLowerCase();
  var fixedIdx = -1;       // for song pages
  for (var k = 0; k < S.length; k++) if (S[k].page === pageSlug) { fixedIdx = k; break; }
  if (fixedIdx >= 0) shown = fixedIdx;

  function showBar() { var b = $('#rnp'); if (b) { b.hidden = false; document.body.classList.add('rnp-on'); } }
  function play(i) {
    if (i < 0 || i >= S.length) return;
    if (!sameSong(i, cur) || !aud.getAttribute('src')) { aud.src = srcFor(S[i]); }
    cur = i; shown = i; showBar();
    var p = aud.play(); if (p && p.catch) p.catch(function () {});
    refresh(true);
  }
  function toggle(i) {
    if (sameSong(i, cur) && !aud.paused) aud.pause(); else play(i);
  }
  aud.addEventListener('error', function () {
    if (!aud.getAttribute('src')) return;
    toast('Couldn\u2019t load the audio for \u201c' + (S[cur] ? S[cur].title : 'this song') + '\u201d. Add your archive.org link in assets/js/config.js (or put the mp3 in /audio).');
    refresh(true);
  });
  aud.addEventListener('play', function () { refresh(true); tick(); });
  aud.addEventListener('pause', function () { refresh(true); });
  aud.addEventListener('timeupdate', function () { refresh(false); });
  aud.addEventListener('loadedmetadata', function () { refresh(false); });
  aud.addEventListener('ended', function () {
    var next = cur + 1;
    if (next < S.length) play(next); else { refresh(true); }
  });
  function tick() { if (!aud.paused) { refresh(false); requestAnimationFrame(tick); } }

  /* ---------- main (page) players with waveform ---------- */
  var mains = $$('.song-player').map(function (root) {
    var btn = $('.song-player__play-pause-button', root);
    if (!btn) return null;
    return { root: root, btn: btn, base: $('.song-player__waveform__base', root), canvas: $('canvas', root), wf: $('.song-player__waveform', root) };
  }).filter(Boolean);

  function drawWave(m, idx, prog) {
    if (!m.canvas || !m.base || !m.wf) return;
    var dpr = window.devicePixelRatio || 1;
    var w = Math.max(60, m.wf.clientWidth || 300), h = Math.max(30, m.wf.clientHeight || 80);
    if (m.canvas.width !== Math.round(w * dpr) || m.canvas.height !== Math.round(h * dpr)) { m.canvas.width = Math.round(w * dpr); m.canvas.height = Math.round(h * dpr); }
    var ctx = m.canvas.getContext('2d'), W = m.canvas.width, H = m.canvas.height;
    ctx.clearRect(0, 0, W, H);
    var data = S[idx].wave, bw = 2 * dpr, gap = 1 * dpr, n = Math.floor(W / (bw + gap)), x = 0;
    var cut = Math.floor(n * prog);
    for (var b = 0; b < n; b++) {
      var v = data[Math.floor(b * data.length / n)] / 128;
      var bh = Math.max(2 * dpr, v * H * 0.96);
      ctx.fillStyle = b < cut ? COLOR_DONE : COLOR;
      ctx.fillRect(x, H - bh, bw, bh);
      x += bw + gap;
    }
  }

  function refresh(full) {
    var playing = !aud.paused && cur >= 0;
    var dur = (aud.duration && isFinite(aud.duration)) ? aud.duration : (cur >= 0 ? S[cur].dur : 0);
    var t = aud.currentTime || 0;

    mains.forEach(function (m) {
      var idx = fixedIdx >= 0 ? fixedIdx : shown;
      var active = sameSong(idx, cur);
      var prog = active && dur ? t / dur : 0;
      var scope = m.root.closest('.waveform-container, .music-module, .profile-module__inner') || m.root.parentNode;
      $$('.song-player__position', scope).forEach(function (e) { if (e.className.indexOf('divider') < 0) e.textContent = fmt(active ? t : 0); });
      $$('.song-player__duration', scope).forEach(function (e) { e.textContent = fmt(S[idx].dur); });
      m.btn.classList.toggle('rn-playing', active && playing);
      m.btn.classList.remove('buffering'); m.btn.classList.add('animation-complete');
      if (full !== false || active) drawWave(m, idx, prog);
    });
    if (fixedIdx < 0) {
      var ft = $('.featured_song .text-alt'); if (ft) ft.textContent = S[shown].title;
    }
    if (full === false) { updateBar(playing, dur, t); return; }
    $$('[data-song-id]').forEach(function (e) {
      if (!e.classList.contains('button--play')) return;
      var id = idxById(e.getAttribute('data-song-id'));
      e.classList.toggle('rn-playing', id >= 0 && id === cur && playing);
    });
    $$('.slat').forEach(function (s) {
      var d = $('[data-song-id]', s); var id = d ? idxById(d.getAttribute('data-song-id')) : -1;
      s.classList.toggle('rn-cur', id >= 0 && id === cur);
    });
    updateBar(playing, dur, t);
  }

  /* ---------- docked bar ---------- */
  function updateBar(playing, dur, t) {
    if (cur < 0) return;
    var ic = $('#rnpPlay i'); if (ic) ic.className = 'icon-fa ' + (playing ? 'icon-pause' : 'icon-play');
    var title = $('#rnpTitle'); if (title && title.textContent !== S[cur].title) title.textContent = S[cur].title;
    var pct = dur ? Math.min(100, t / dur * 100) : 0;
    var f = $('#rnpFill'), kn = $('#rnpKnob'), tm = $('#rnpTime');
    if (f) f.style.width = pct + '%'; if (kn) kn.style.left = pct + '%'; if (tm) tm.textContent = fmt(t);
  }
  function bindBar() {
    var p = $('#rnpPlay'); if (!p) return;
    p.onclick = function () { if (cur < 0) play(0); else if (aud.paused) { var q = aud.play(); if (q && q.catch) q.catch(function () {}); } else aud.pause(); };
    $('#rnpNext').onclick = function () { play(Math.min(S.length - 1, cur + 1)); };
    $('#rnpPrev').onclick = function () { if ((aud.currentTime || 0) > 3) aud.currentTime = 0; else play(Math.max(0, cur - 1)); };
    $('#rnpVol').oninput = function () { aud.volume = this.value / 100; $('#rnpMute i').className = 'icon-fa ' + (aud.volume === 0 ? 'icon-volume-off' : 'icon-volume-up'); };
    $('#rnpMute').onclick = function () { aud.muted = !aud.muted; $('#rnpMute i').className = 'icon-fa ' + (aud.muted ? 'icon-volume-off' : 'icon-volume-up'); };
    $('#rnpBar').onclick = function (e) {
      var r = this.getBoundingClientRect(), d = aud.duration;
      if (d && isFinite(d)) aud.currentTime = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * d;
    };
    $('#rnpList').onclick = function () {
      closeMenus();
      var items = S.map(function (s, i) { return '<a data-q="' + i + '">' + esc((i + 1) + '. ' + s.title) + '</a>'; }).join('');
      menuAt(this, items, true);
    };
  }

  /* ---------- floating menus ---------- */
  function closeMenus() { $$('.rn-menu').forEach(function (m) { m.parentNode.removeChild(m); }); }
  function menuAt(anchor, html, above) {
    var m = document.createElement('div'); m.className = 'rn-menu'; m.innerHTML = html; document.body.appendChild(m);
    var r = anchor.getBoundingClientRect();
    var left = Math.min(window.scrollX + r.left, window.scrollX + document.documentElement.clientWidth - m.offsetWidth - 8);
    var top = above ? (window.scrollY + r.top - m.offsetHeight - 6) : (window.scrollY + r.bottom + 4);
    m.style.left = Math.max(4, left) + 'px'; m.style.top = Math.max(4, top) + 'px';
    return m;
  }

  /* ---------- helpers ---------- */
  function songIdxFrom(el) {
    var s = el.closest('.slat'); var d = s ? $('[data-song-id]', s) : null;
    if (!d) d = el.closest('[data-song-id]');
    if (d) return idxById(d.getAttribute('data-song-id'));
    return fixedIdx >= 0 ? fixedIdx : shown;
  }
  function songShareUrl(i) { try { return new URL(S[i].page, location.href).href; } catch (e) { return S[i].page; } }
  function videoById(id) { for (var i = 0; i < V.length; i++) if (V[i].id === String(id) || V[i].yt === id) return V[i]; return null; }
  var vv_el = null;
  function closeVideo() { if (vv_el) { vv_el.parentNode.removeChild(vv_el); vv_el = null; } }
  function videoModal(ytId, title) {
    closeVideo(); aud.pause();
    var local = C.video && C.video[ytId];
    var yurl = 'https://www.youtube.com/watch?v=' + encodeURIComponent(ytId);
    var player = local
      ? '<video controls autoplay src="' + esc(local) + '"></video>'
      : '<iframe src="https://www.youtube.com/embed/' + encodeURIComponent(ytId) + '?autoplay=1&rel=0" allow="autoplay; encrypted-media; fullscreen; picture-in-picture" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>';
    vv_el = document.createElement('div'); vv_el.className = 'rnpv';
    vv_el.innerHTML = '<div class="rnpv__box"><button class="rnpv__x" aria-label="Close">&#10005;</button>' +
      '<div class="rnpv__head"><h2>' + esc(title || 'Video') + '</h2></div><div class="rnpv__body">' +
      '<div class="rnpv__video">' + player + '</div>' +
      '<div class="rnpv__foot"><a data-vshare="1">Share</a>' + (local ? '' : '<a href="' + yurl + '" target="_blank" rel="noopener">Not playing? Watch on YouTube \u00bb</a>') + '</div></div></div>';
    document.body.appendChild(vv_el);
    vv_el.addEventListener('click', function (ev) {
      var t = ev.target;
      if (t === vv_el || t.closest('.rnpv__x')) { closeVideo(); return; }
      if (t.getAttribute && t.getAttribute('data-vshare')) { closeVideo(); shareModal('Share Video', 'https://youtu.be/' + ytId); }
    });
  }

  /* ---------- click handling ---------- */
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t.closest) return;

    if (t.closest('.rn-menu')) {
      var a = t.closest('.rn-menu a');
      if (a) {
        if (a.hasAttribute('data-q')) play(+a.getAttribute('data-q'));
        else if (a.hasAttribute('data-act')) {
          var act = a.getAttribute('data-act'), i = +a.getAttribute('data-i');
          if (act === 'lyrics') lyricsModal(i);
          if (act === 'share') shareModal('Share Song', songShareUrl(i));
          if (act === 'page') location.href = S[i].page;
          if (act === 'artist') location.href = 'index.html';
          if (act === 'yt') window.open('https://www.youtube.com/watch?v=' + a.getAttribute('data-yt'), '_blank');
          if (act === 'vshare') shareModal('Share Video', 'https://youtu.be/' + a.getAttribute('data-yt'));
        }
        closeMenus(); e.preventDefault();
      }
      return;
    }
    if (!t.closest('#rnpList')) closeMenus();

    if (t.id === 'rnModalX' || t.id === 'rnModal') { closeModal(); return; }

    var bio = t.closest('[data-rn="bio"]');
    if (bio) { e.preventDefault(); modal('<h3>About the Artist</h3><p>' + esc(BIO) + '</p>'); return; }

    var ly = t.closest('[data-rn="lyrics"]');
    if (ly) { e.preventDefault(); lyricsModal(songIdxFrom(ly)); return; }

    var sh = t.closest('[data-rn="share"], .share_artist_btn a, .button--share');
    if (sh) {
      e.preventDefault();
      var u = sh.getAttribute('data-url') || sh.getAttribute('data-share') || '', m;
      if ((m = u.match(/share_song\/(\d+)/))) { var si = idxById(m[1]); shareModal('Share Song', songShareUrl(si >= 0 ? si : 0)); }
      else if ((m = u.match(/share_video\/(\d+)/))) { var v = videoById(m[1]); shareModal('Share Video', 'https://youtu.be/' + (v ? v.yt : '')); }
      else shareModal('Share Artist', location.href);
      return;
    }

    var vp = t.closest('[data-rn="video"]');
    if (vp) {
      e.preventDefault();
      var card = vp.closest('.card--video'), yt = card ? card.getAttribute('data-yt') : '';
      var vv = videoById(yt);
      if (yt) videoModal(yt, vv ? vv.title : ''); return;
    }
    var vm = t.closest('[data-rn="videomenu"]');
    if (vm) {
      e.preventDefault(); closeMenus();
      var cd = vm.closest('.card--video'), y = cd ? cd.getAttribute('data-yt') : '';
      menuAt(vm, '<a data-act="yt" data-yt="' + esc(y) + '">Watch on YouTube</a><a data-act="vshare" data-yt="' + esc(y) + '">Share Video</a>');
      return;
    }
    var am = t.closest('.button--actions, .song-player__ellipsis a');
    if (am && am.getAttribute('data-rn') === 'showmenu') {
      e.preventDefault(); closeMenus();
      var slat = am.closest('.slat'), g = slat ? $('a[href*="google.com/maps"]', slat) : null;
      menuAt(am, g ? '<a href="' + esc(g.href) + '" target="_blank" rel="noopener">Get Directions</a>' : '<a>No directions available</a>');
      return;
    }
    if (am) {
      e.preventDefault(); closeMenus();
      if (am.closest('.song-player__ellipsis')) { menuAt(am, '<a data-act="artist">View Artist \u00bb</a>'); return; }
      var si2 = songIdxFrom(am);
      var items = '<a data-q="' + si2 + '">Play</a>' + (S[si2].lyrics ? '<a data-act="lyrics" data-i="' + si2 + '">Lyrics</a>' : '') +
                  '<a data-act="page" data-i="' + si2 + '">View Song</a><a data-act="share" data-i="' + si2 + '">Share Song</a>';
      menuAt(am, items); return;
    }

    var plus = t.closest('.song-row-icon-shim a');
    if (plus) { e.preventDefault(); e.stopPropagation(); var qi = songIdxFrom(plus); toast('\u201c' + S[qi].title + '\u201d is in the queue \u2013 it plays in order after the current song.'); return; }

    var more = t.closest('.text-container .pt1 a');
    if (more) {
      e.preventDefault();
      var tc = more.closest('.text-container'), p = $('.inner-text', tc), lab = $('span', more);
      var open = p.getAttribute('data-open') === '1';
      if (open) { p.style.maxHeight = '90px'; p.setAttribute('data-open', '0'); lab.textContent = 'Show All Lyrics'; }
      else { p.style.maxHeight = 'none'; p.setAttribute('data-open', '1'); lab.textContent = 'Show Less'; }
      return;
    }

    var wf = t.closest('.song-player__waveform');
    if (wf) {
      var mp = mains.filter(function (mm) { return mm.wf === wf; })[0];
      if (mp) {
        var idx = fixedIdx >= 0 ? fixedIdx : shown, r = wf.getBoundingClientRect(), frac = (e.clientX - r.left) / r.width;
        if (!sameSong(idx, cur)) play(idx);
        var seek = function () { if (aud.duration && isFinite(aud.duration)) aud.currentTime = frac * aud.duration; };
        if (aud.readyState >= 1) seek(); else aud.addEventListener('loadedmetadata', function f() { aud.removeEventListener('loadedmetadata', f); seek(); });
        return;
      }
    }

    var pb = t.closest('.song-player__play-pause-button');
    if (pb) { e.preventDefault(); toggle(fixedIdx >= 0 ? fixedIdx : shown); return; }

    var pa = t.closest('.music-top-controls a');
    if (pa && /play all/i.test(pa.textContent)) { e.preventDefault(); play(0); return; }

    var sa = t.closest('[data-song-action="play"][data-song-id]');
    if (sa) {
      var inner = t.closest('a, button');
      if (inner && inner !== sa && !inner.hasAttribute('data-song-action')) return;
      e.preventDefault();
      toggle(idxById(sa.getAttribute('data-song-id'))); return;
    }
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { closeModal(); closeMenus(); closeVideo(); } });

  /* ---------- sticky profile nav ---------- */
  var navWrap = $('.js-nav-module');
  if (navWrap) {
    var holder = navWrap.parentNode, hdrH = ($('#foundation_page_header') || {}).offsetHeight || 51;
    var onScroll = function () {
      var top = holder.getBoundingClientRect().top;
      var stuck = top <= hdrH;
      if (stuck !== navWrap.classList.contains('stuck')) {
        navWrap.classList.toggle('stuck', stuck);
        var hh = stuck ? (navWrap.offsetHeight || 60) + 'px' : '';
        holder.style.height = hh;
        if (holder.parentNode && holder.parentNode.classList.contains('sticky-wrapper')) holder.parentNode.style.height = hh;
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
  }

  /* ---------- photo carousel (owl markup from the original page) ---------- */
  var P = window.RN_PHOTOS || [];
  var owl = $('.owl-carousel');
  if (owl) {
    var outer = $('.owl-stage-outer', owl), stage = $('.owl-stage', owl), items = $$('.owl-item', owl);
    var prev = $('.owl-prev', owl), next = $('.owl-next', owl), pos = 0, STEP = 211;
    var layout = function () {
      var w = outer.clientWidth, n = Math.max(1, Math.floor((w + 8) / STEP));
      var iw = Math.floor((w - 8 * (n - 1)) / n);
      items.forEach(function (it) { it.style.width = iw + 'px'; it.style.marginRight = '8px'; it.classList.add('active'); });
      stage.style.width = (items.length * (iw + 8)) + 'px';
      owl._vis = n; owl._step = iw + 8; go(pos);
    };
    var go = function (p) {
      var max = Math.max(0, items.length - owl._vis);
      pos = Math.max(0, Math.min(max, p));
      stage.style.transition = 'transform .3s'; stage.style.transform = 'translate3d(' + (-pos * owl._step) + 'px,0,0)';
      if (prev) prev.classList.toggle('disabled', pos === 0);
      if (next) next.classList.toggle('disabled', pos >= max);
    };
    if (prev) prev.addEventListener('click', function () { go(pos - owl._vis); });
    if (next) next.addEventListener('click', function () { go(pos + owl._vis); });
    window.addEventListener('resize', layout); layout();
  }

  /* ---------- "View Photos" popup ---------- */
  var pv = null, pi = 0, grid = false;
  function buildPv() {
    pv = document.createElement('div'); pv.className = 'rnpv'; pv.hidden = true;
    pv.innerHTML = '<div class="rnpv__box"><button class="rnpv__x" aria-label="Close">&#10005;</button>' +
      '<div class="rnpv__head"><h2 id="rnpvTitle">View Photos</h2></div><div class="rnpv__body">' +
      '<div id="rnpvStage" class="rnpv__stage"><div class="rnpv__wrap">' +
      '<button class="rnpv__arr l" aria-label="Previous"><svg viewBox="0 0 20 40"><path d="M17 2L3 20l14 18"/></svg></button>' +
      '<img id="rnpvImg" alt="">' +
      '<button class="rnpv__arr r" aria-label="Next"><svg viewBox="0 0 20 40"><path d="M3 2l14 18L3 38"/></svg></button></div></div>' +
      '<div id="rnpvGrid" class="rnpv__grid" hidden></div>' +
      '<div class="rnpv__foot"><a id="rnpvShare">Share</a><a id="rnpvAll">View All Photos \u00bb</a></div></div></div>';
    document.body.appendChild(pv);
    $('#rnpvGrid', pv).innerHTML = P.map(function (p, i) { return '<a data-i="' + i + '"><img src="' + p.thumb + '" alt=""></a>'; }).join('');
    pv.addEventListener('click', function (e) {
      var t = e.target;
      if (t === pv || t.closest('.rnpv__x')) { pv.hidden = true; return; }
      if (t.closest('.rnpv__arr.l')) return setPhoto(pi - 1);
      if (t.closest('.rnpv__arr.r') || t.id === 'rnpvImg') return setPhoto(pi + 1);
      if (t.id === 'rnpvShare') return shareModalSafe();
      if (t.id === 'rnpvAll') return mode(!grid);
      var g = t.closest('#rnpvGrid a'); if (g) { mode(false); setPhoto(+g.getAttribute('data-i')); }
    });
  }
  function shareModalSafe() { pv.hidden = true; shareModal('Share Photo', location.href); }
  function mode(g) {
    grid = g; $('#rnpvStage').hidden = g; $('#rnpvGrid').hidden = !g;
    $('#rnpvTitle').textContent = g ? 'Photos' : 'View Photos';
    $('#rnpvAll').innerHTML = g ? '\u00ab Back to Photo' : 'View All Photos \u00bb';
  }
  function setPhoto(i) {
    pi = (i + P.length) % P.length; var im = $('#rnpvImg');
    im.onerror = function () { im.onerror = null; im.src = P[pi].thumb; };
    im.src = P[pi].full;
  }
  function openPhoto(i) { if (!pv) buildPv(); mode(false); setPhoto(i); pv.hidden = false; }
  document.addEventListener('click', function (e) {
    var im = e.target.closest && e.target.closest('.owl-item img, .owl-item li');
    if (!im) return;
    var img = im.tagName === 'IMG' ? im : im.querySelector('img'); if (!img) return;
    var id = img.getAttribute('data-photo') || img.getAttribute('data-id');
    for (var i = 0; i < P.length; i++) if (P[i].id === id) { e.preventDefault(); openPhoto(i); return; }
  });
  document.addEventListener('keydown', function (e) {
    if (!pv || pv.hidden) return;
    if (e.key === 'Escape') pv.hidden = true;
    if (!grid && e.key === 'ArrowLeft') setPhoto(pi - 1);
    if (!grid && e.key === 'ArrowRight') setPhoto(pi + 1);
  });

  /* ---------- boot ---------- */
  bindBar();
  window.addEventListener('resize', function () { refresh(true); });
  refresh(true);
  window.RN = { play: play, aud: aud, songs: S, modal: modal, toast: toast, closeModal: closeModal, esc: esc };
})();
