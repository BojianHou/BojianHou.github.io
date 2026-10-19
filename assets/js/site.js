/* New-tab links, light/dark switch, publication topic filters and the news "Show all" toggle. Without this script the site follows
   the system color scheme and every paper and news item shows. */
(function () {
  'use strict';

  // ----- Links open in a new tab, except the top navigation, the skip link, in-page anchors and email links -----
  Array.prototype.forEach.call(document.querySelectorAll('a[href]'), function (a) {
    var href = a.getAttribute('href');
    if (!href || href.charAt(0) === '#' || /^(mailto|tel|javascript):/i.test(href)) return;
    if (a.closest('.site-header') || a.classList.contains('skip-link')) return;
    a.setAttribute('target', '_blank');
    var rel = (a.getAttribute('rel') || '').split(/\s+/).filter(Boolean);
    if (rel.indexOf('noopener') === -1) rel.push('noopener');
    a.setAttribute('rel', rel.join(' '));
  });

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

  // ----- Publication filters -----
  var bar = document.querySelector('.pub-filters');
  if (bar) {
    var chips = Array.prototype.slice.call(bar.querySelectorAll('.chip'));
    var pubs = Array.prototype.slice.call(document.querySelectorAll('.pub--list'));
    var years = Array.prototype.slice.call(document.querySelectorAll('.pub-year'));
    var countN = document.querySelector('.pub-count-n');
    var countLabel = document.querySelector('.pub-count-label');

    var matches = function (pub, key) {
      if (key === 'all') return true;
      if (key === 'selected') return pub.getAttribute('data-selected') === 'true';
      if (key === 'lead') return pub.getAttribute('data-lead') === 'true';
      return (' ' + pub.getAttribute('data-tags') + ' ').indexOf(' ' + key + ' ') !== -1;
    };

    var apply = function (key, updateHash) {
      var valid = chips.some(function (c) { return c.getAttribute('data-filter') === key; });
      if (!valid) key = 'all';
      var shown = 0;
      pubs.forEach(function (p) {
        var ok = matches(p, key);
        p.hidden = !ok;
        if (ok) shown += 1;
      });
      years.forEach(function (y) {
        y.hidden = !y.querySelector('.pub--list:not([hidden])');
      });
      var label = '';
      chips.forEach(function (c) {
        var on = c.getAttribute('data-filter') === key;
        c.setAttribute('aria-pressed', on ? 'true' : 'false');
        if (on && key !== 'all') label = ' · ' + c.firstChild.textContent.trim();
      });
      // keep the active chip visible when the chip bar scrolls sideways (phones)
      chips.forEach(function (c) {
        if (c.getAttribute('aria-pressed') === 'true' && bar.scrollWidth > bar.clientWidth) {
          bar.scrollLeft = Math.max(0, c.offsetLeft - bar.offsetLeft - 16);
        }
      });
      if (countN) countN.textContent = shown;
      if (countLabel) countLabel.textContent = label;
      if (updateHash && history.replaceState) {
        history.replaceState(null, '', key === 'all' ? location.pathname : '#topic=' + key);
      }
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
    }
    window.addEventListener('hashchange', function () {
      if (!fromHash() && location.hash.length > 1) apply('all', false);
    });
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
