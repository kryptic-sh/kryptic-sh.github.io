// kryptic.sh shared page JS: deferred analytics + live version badges.
(function () {
  'use strict';

  // ---- deferred GA (single property for the whole domain) ----
  var GA_ID = 'G-B3CF3E04WS';
  var gaLoaded = false;
  function loadGA() {
    if (gaLoaded) return;
    gaLoaded = true;
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    function gtag() {
      dataLayer.push(arguments);
    }
    gtag('js', new Date());
    gtag('config', GA_ID);
  }
  ['pointerdown', 'keydown', 'scroll', 'touchstart'].forEach(function (e) {
    window.addEventListener(e, loadGA, { once: true, passive: true });
  });
  setTimeout(loadGA, 8000);

  // ---- live versions from the GitHub API ----
  // Any element with data-version="<repo>" gets its text replaced by the
  // latest release tag of github.com/kryptic-sh/<repo>. Optional
  // data-pad="N" right-pads with spaces (for aligned <pre> columns).
  // Cached in sessionStorage for an hour to stay far away from the 60
  // req/hr unauthenticated rate limit.
  var slots = document.querySelectorAll('[data-version]');
  if (!slots.length) return;

  var byRepo = {};
  slots.forEach(function (el) {
    var repo = el.getAttribute('data-version');
    (byRepo[repo] = byRepo[repo] || []).push(el);
  });

  function apply(repo, tag) {
    byRepo[repo].forEach(function (el) {
      var text = tag;
      var pad = parseInt(el.getAttribute('data-pad') || '0', 10);
      if (pad > 0) {
        while (text.length < pad) text += ' ';
      }
      el.textContent = text;
    });
  }

  function semverKey(tag) {
    return tag
      .replace(/^v/, '')
      .split(/[.+-]/)
      .map(function (p) {
        return /^\d+$/.test(p) ? p.padStart(8, '0') : p;
      })
      .join('.');
  }

  function fetchTag(repo) {
    var api = 'https://api.github.com/repos/kryptic-sh/' + repo;
    return fetch(api + '/releases/latest')
      .then(function (r) {
        if (!r.ok) throw new Error('no releases');
        return r.json();
      })
      .then(function (j) {
        return j.tag_name;
      })
      .catch(function () {
        // repos without GitHub Releases: fall back to highest v* tag
        return fetch(api + '/tags?per_page=100')
          .then(function (r) {
            if (!r.ok) throw new Error('no tags');
            return r.json();
          })
          .then(function (tags) {
            var names = tags
              .map(function (t) {
                return t.name;
              })
              .filter(function (n) {
                return /^v\d/.test(n);
              })
              .sort(function (a, b) {
                return semverKey(a) < semverKey(b) ? -1 : 1;
              });
            return names[names.length - 1];
          });
      });
  }

  Object.keys(byRepo).forEach(function (repo) {
    var key = 'kryptic-ver:' + repo;
    var cached = null;
    try {
      cached = JSON.parse(sessionStorage.getItem(key) || 'null');
    } catch (_) {}
    if (cached && Date.now() - cached.t < 3600e3) {
      apply(repo, cached.v);
      return;
    }
    fetchTag(repo)
      .then(function (tag) {
        if (!tag) return;
        try {
          sessionStorage.setItem(
            key,
            JSON.stringify({ t: Date.now(), v: tag })
          );
        } catch (_) {}
        apply(repo, tag);
      })
      .catch(function () {
        /* leave the placeholder text */
      });
  });
})();
