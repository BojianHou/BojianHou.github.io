/* New-tab links, visitor map, light/dark switch, publication topic filters and the news "Show all" toggle. Without this script the site follows
   the system color scheme and every paper and news item shows. */
(function () {
  'use strict';

  // ----- Links to other sites and to files (papers, posters, slides) open in a new tab. Pages of this site, in-page anchors,
  // the top navigation and email links stay in the same tab. -----
  var opensNewTab = function (a) {
    var href = a.getAttribute('href');
    if (!href || href.charAt(0) === '#' || /^(mailto|tel|javascript):/i.test(href)) return false;
    if (a.closest('.site-header') || a.classList.contains('skip-link')) return false;
    if (a.hostname && a.hostname !== location.hostname) return true;
    return /\.(pdf|png|jpe?g|gif|webp|svg|pptx?|docx?|key|zip|mp4)$/i.test(a.pathname);
  };
  var markNewTab = function (a) {
    a.setAttribute('target', '_blank');
    var rel = (a.getAttribute('rel') || '').split(/\s+/).filter(Boolean);
    if (rel.indexOf('noopener') === -1) rel.push('noopener');
    a.setAttribute('rel', rel.join(' '));
  };
  Array.prototype.forEach.call(document.querySelectorAll('a[href]'), function (a) {
    if (opensNewTab(a)) markNewTab(a);
  });
  // Links added later (for example by the visitor map) get the same treatment when clicked.
  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a[href]') : null;
    if (a && !a.target && opensNewTab(a)) markNewTab(a);
  }, true);

  // ----- Visitor map (MapMyVisitors), loaded after the page so it never delays the first paint. Only the live site
  // loads it, so local builds and CI previews are not counted as visits. -----
  var vmap = document.getElementById('visitor-map');
  if (vmap && !/(^|\.)bojianhou\.com$/.test(location.hostname)) {
    vmap.classList.add('is-local');
    vmap.textContent = 'The visitor map shows on bojianhou.com';
  } else if (vmap) {
    var loadMap = function () {
      var s = document.createElement('script');
      s.id = 'mapmyvisitors';
      s.async = true;
      s.src = 'https://mapmyvisitors.com/map.js?d=' + vmap.getAttribute('data-id') + '&cl=3d4c72&co=1c2742&ct=ffffff&w=a';
      vmap.appendChild(s);
    };
    if (document.readyState === 'complete') loadMap(); else window.addEventListener('load', loadMap);
  }

  // ----- Light/dark switch (the saved choice is applied before paint by the inline script in rd-head.html) -----
  var toggle = document.querySelector('.theme-toggle');
  if (toggle) {
    var root = document.documentElement;
    var mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
    var current = function () { return root.getAttribute('data-theme') || (mq && mq.matches ? 'dark' : 'light'); };
    var sync = function () {
      var theme = current();
      var next = theme === 'dark' ? 'light' : 'dark';
      toggle.setAttribute('aria-label', 'Switch to ' + next + ' mode');
      toggle.setAttribute('title', 'Switch to ' + next + ' mode');
      Array.prototype.forEach.call(document.querySelectorAll('meta[name="theme-color"]'), function (m) {
        m.setAttribute('content', theme === 'dark' ? '#0A0F1C' : '#E9EDF3');
      });
    };
    toggle.addEventListener('click', function () {
      var next = current() === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) { /* storage blocked: the choice lasts for this page */ }
      sync();
    });
    if (mq && mq.addEventListener) mq.addEventListener('change', sync);
    sync();
  }

  // ----- Publication filters: topic groups in the first row; a group with several topics opens a second row -----
  var bar = document.querySelector('.pub-filters');

  // In-page jumps (#paper-id) land below the sticky header and the sticky topic bar. The bar's height depends on the
  // window width and on whether a second row is open, so it is measured. On phones the bar is not sticky and the
  // stylesheet's offset applies.
  var setOffset = function () {
    if (!bar) return;
    var cs = window.getComputedStyle(bar);
    document.documentElement.style.scrollPaddingTop = cs.position === 'sticky' ?
      Math.ceil((parseFloat(cs.top) || 0) + bar.getBoundingClientRect().height + 16) + 'px' : '';
  };
  var jumpToHash = function (instant) {
    var id = location.hash.slice(1);
    if (!id || id.indexOf('topic=') === 0) return;
    var t = document.getElementById(decodeURIComponent(id));
    if (t) t.scrollIntoView(instant ? { block: 'start', behavior: 'instant' } : { block: 'start' });
  };

  if (bar) {
    var chips = Array.prototype.slice.call(bar.querySelectorAll('.chip'));
    var subs = Array.prototype.slice.call(bar.querySelectorAll('.pub-sub'));
    var rows = Array.prototype.slice.call(bar.querySelectorAll('.pub-filters-row'));
    var pubs = Array.prototype.slice.call(document.querySelectorAll('.pub--list'));
    var years = Array.prototype.slice.call(document.querySelectorAll('.pub-year'));
    var countN = document.querySelector('.pub-count-n');
    var countLabel = document.querySelector('.pub-count-label');

    var chipFor = function (key) {
      for (var i = 0; i < chips.length; i += 1) if (chips[i].getAttribute('data-filter') === key) return chips[i];
      return null;
    };
    var labelOf = function (c) { return c.firstChild.textContent.trim(); };
    var matches = function (pub, chip) {
      var key = chip.getAttribute('data-filter');
      if (key === 'all') return true;
      if (key === 'selected') return pub.getAttribute('data-selected') === 'true';
      if (key === 'lead') return pub.getAttribute('data-lead') === 'true';
      var tags = ' ' + pub.getAttribute('data-tags') + ' ';
      return (chip.getAttribute('data-match') || key).split(' ').some(function (t) {
        return tags.indexOf(' ' + t + ' ') !== -1;
      });
    };

    var apply = function (key, updateHash) {
      var chip = chipFor(key);
      if (!chip) { key = 'all'; chip = chipFor('all'); }
      // the group whose second row is open: the chosen group itself, or the group of the chosen topic
      var group = chip.getAttribute('data-group') || (chip.hasAttribute('aria-controls') ? key : '');
      var shown = 0;
      pubs.forEach(function (p) {
        var ok = matches(p, chip);
        p.hidden = !ok;
        if (ok) shown += 1;
      });
      years.forEach(function (y) {
        y.hidden = !y.querySelector('.pub--list:not([hidden])');
      });
      chips.forEach(function (c) {
        var on = c === chip;
        c.setAttribute('aria-pressed', on ? 'true' : 'false');
        c.classList.toggle('is-parent', !on && group !== '' && c.getAttribute('data-filter') === group);
        if (c.hasAttribute('aria-controls')) c.setAttribute('aria-expanded', c.getAttribute('data-filter') === group ? 'true' : 'false');
      });
      subs.forEach(function (s) { s.hidden = s.getAttribute('data-group') !== group; });
      // keep the active chip visible when a chip row scrolls sideways (phones)
      rows.forEach(function (r) {
        var c = r.querySelector('[aria-pressed="true"], .is-parent');
        if (c && r.scrollWidth > r.clientWidth) {
          r.scrollLeft += c.getBoundingClientRect().left - r.getBoundingClientRect().left - 16;
        }
      });
      var label = '';
      if (key !== 'all') {
        var parent = chip.getAttribute('data-group') ? chipFor(group) : null;
        label = ' · ' + (parent ? labelOf(parent) + ' / ' : '') + labelOf(chip);
      }
      if (countN) countN.textContent = shown;
      if (countLabel) countLabel.textContent = label;
      if (updateHash && history.replaceState) {
        history.replaceState(null, '', key === 'all' ? location.pathname : '#topic=' + key);
      }
      setOffset();
    };

    var fromHash = function () {
      var m = /^#topic=([\w-]+)$/.exec(location.hash);
      if (m) { apply(m[1], false); return true; }
      return false;
    };

    chips.forEach(function (c) {
      c.addEventListener('click', function () { apply(c.getAttribute('data-filter'), true); });
    });
    bar.hidden = false;
    if (!fromHash()) {
      // A link to a single paper (#paper-id) keeps everything visible so the target is on the page.
      apply('all', false);
      jumpToHash(true);
    }
    window.addEventListener('hashchange', function () {
      if (!fromHash() && location.hash.length > 1) { apply('all', false); jumpToHash(); }
    });
    window.addEventListener('resize', setOffset);
    // fonts and images can still move things after this script runs; correct once more unless the reader has scrolled
    var moved = false;
    var stop = function () { moved = true; };
    ['wheel', 'touchstart', 'keydown', 'mousedown'].forEach(function (ev) { window.addEventListener(ev, stop, { passive: true, once: true }); });
    window.addEventListener('load', function () { setOffset(); if (!moved) jumpToHash(true); });
  }

  // ----- News "Show all" -----
  var lists = document.querySelectorAll('.news-list[data-limit]');
  Array.prototype.forEach.call(lists, function (list) {
    var limit = parseInt(list.getAttribute('data-limit'), 10) || 0;
    var items = list.querySelectorAll('.news-item');
    var btn = list.nextElementSibling;
    if (!limit || items.length <= limit || !btn || !btn.classList.contains('news-toggle')) return;
    var expanded = false;
    var render = function () {
      list.classList.toggle('is-expanded', expanded);
      btn.textContent = expanded ? btn.getAttribute('data-less') : btn.getAttribute('data-more');
      btn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    };
    btn.hidden = false;
    btn.addEventListener('click', function () {
      expanded = !expanded;
      render();
      if (!expanded) list.scrollIntoView({ block: 'start' });
    });
    render();
  });
})();
