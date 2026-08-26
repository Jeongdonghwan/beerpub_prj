/* ============================================================
   common.js — 전 페이지 공통 컴포넌트 (바닐라 JS, 라이브러리 금지)
   ScrollReveal · InfiniteMarquee · Modal · LayerPopup ·
   StickyHeader · Parallax · 햄버거 · GoTop · 가맹문의 폼 제출
   ============================================================ */
(function () {
  'use strict';

  /* ---------- 1. ScrollReveal — [data-reveal] 1회 실행 (서브 페이지용) ---------- */
  var revealEls = document.querySelectorAll('[data-reveal]');
  if (revealEls.length) {
    var revIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          var delay = e.target.getAttribute('data-delay') || 0;
          e.target.style.transitionDelay = delay + 's';
          e.target.classList.add('revealed');
          revIO.unobserve(e.target);
        }
      });
    }, { threshold: 0.15 });
    revealEls.forEach(function (el) { revIO.observe(el); });
  }

  /* ---------- 2. InfiniteMarquee — 세트 3복제 + CSS keyframes ---------- */
  document.querySelectorAll('.mq-track').forEach(function (track) {
    var set = track.querySelector('.set');
    if (!set) return;
    track.appendChild(set.cloneNode(true));
    track.appendChild(set.cloneNode(true));
    var speed = track.getAttribute('data-speed');
    if (speed) track.style.setProperty('--dur', speed + 's');
    var dir = track.getAttribute('data-direction');
    if (dir === 'reverse') track.closest('.mq').classList.add('rev');
  });

  /* ---------- 3. Modal — [data-modal-url] fetch 주입, ESC/딤 닫기 ---------- */
  var modal = document.getElementById('modal');
  if (modal) {
    var modalBody = modal.querySelector('.modal-body');
    function openModal(html) {
      modalBody.innerHTML = html;
      modal.hidden = false;
      document.body.classList.add('modal-open');
    }
    function closeModal() {
      modal.hidden = true;
      modalBody.innerHTML = '';
      document.body.classList.remove('modal-open');
    }
    document.addEventListener('click', function (e) {
      var trigger = e.target.closest('[data-modal-url]');
      if (trigger) {
        e.preventDefault();
        fetch(trigger.getAttribute('data-modal-url'))
          .then(function (r) { return r.text(); })
          .then(openModal)
          .catch(function () {});
      }
    });
    modal.querySelector('.modal-dim').addEventListener('click', closeModal);
    modal.querySelector('.modal-close').addEventListener('click', closeModal);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !modal.hidden) closeModal();
    });
  }

  /* ---------- 4. LayerPopup — 쿠키 popup_close_{id} 24h ---------- */
  function getCookie(name) {
    var m = document.cookie.match('(?:^|; )' + name + '=([^;]*)');
    return m ? m[1] : null;
  }
  document.querySelectorAll('.layer-popup').forEach(function (pop) {
    var id = pop.getAttribute('data-popup-id');
    if (getCookie('popup_close_' + id)) return;
    pop.hidden = false;
    pop.querySelector('.lp-close').addEventListener('click', function () {
      pop.hidden = true;
    });
    pop.querySelector('.lp-today').addEventListener('click', function () {
      document.cookie = 'popup_close_' + id + '=1; max-age=86400; path=/';
      pop.hidden = true;
    });
  });

  /* ---------- 5. StickyHeader — scrollY > 80 → .scrolled ---------- */
  var header = document.querySelector('.site-header');
  var goTop = document.querySelector('.go-top');
  function onScroll() {
    var y = window.scrollY;
    if (header) header.classList.toggle('scrolled', y > 80);
    if (goTop) goTop.classList.toggle('show', y > 400);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (goTop) goTop.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  /* ---------- 6. Parallax — data-parallax="0.3", 모바일 비활성 ---------- */
  var parallaxEls = document.querySelectorAll('[data-parallax]');
  if (parallaxEls.length && window.matchMedia('(min-width:1025px)').matches) {
    window.addEventListener('scroll', function () {
      parallaxEls.forEach(function (el) {
        var speed = parseFloat(el.getAttribute('data-parallax')) || 0.3;
        var rect = el.getBoundingClientRect();
        el.style.transform = 'translateY(' + (rect.top * speed * -0.2) + 'px)';
      });
    }, { passive: true });
  }

  /* ---------- 수익분석 파이 — 차오르는 애니메이션 + 조각 라벨 ---------- */
  document.querySelectorAll('.donut[data-segs]').forEach(function (d) {
    var segs;
    try { segs = JSON.parse(d.getAttribute('data-segs')); } catch (err) { return; }
    var labels = d.querySelector('.donut-labels');
    function paint(p) {
      var acc = 0, parts = [];
      segs.forEach(function (s) {
        var deg = s.pct * 3.6 * p;
        parts.push(s.color + ' ' + acc + 'deg ' + (acc + deg) + 'deg');
        acc += deg;
      });
      if (acc < 360) parts.push('transparent ' + acc + 'deg 360deg');
      d.style.background = 'conic-gradient(' + parts.join(',') + ')';
    }
    function placeLabels() {
      if (!labels) return;
      labels.innerHTML = '';
      var acc = 0;
      segs.forEach(function (s) {
        var deg = s.pct * 3.6, mid = acc + deg / 2;
        acc += deg;
        if (s.pct < 2.4) return;                 /* 극소 조각은 표에서만 */
        var out = s.pct < 6;                     /* 작은 조각은 링 바깥 */
        var r = out ? 1.13 : (s.accent ? 0.74 : 0.76);
        var a = (mid - 90) * Math.PI / 180;
        var el = document.createElement('span');
        el.className = 'dl' + (s.accent ? ' accent' : '') + (out ? ' out' : '');
        el.style.left = (50 + Math.cos(a) * 50 * r) + '%';
        el.style.top = (50 + Math.sin(a) * 50 * r) + '%';
        el.innerHTML = s.label + '<b>' + s.pct + '%</b>';
        labels.appendChild(el);
      });
    }
    paint(0);
    var played = false;
    new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting || played) return;
        played = true;
        var t0 = performance.now();
        (function step(now) {
          var p = Math.min((now - t0) / 1300, 1);
          paint(1 - Math.pow(1 - p, 3));
          if (p < 1) requestAnimationFrame(step); else placeLabels();
        })(t0);
      });
    }, { threshold: 0.35 }).observe(d);
  });

  /* ---------- 숫자 카운트업 — [data-count] ---------- */
  var counters = document.querySelectorAll('[data-count]');
  if (counters.length) {
    var cntIO = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target, target = parseInt(el.getAttribute('data-count'), 10);
        cntIO.unobserve(el);
        if (isNaN(target)) return;
        var t0 = performance.now();
        (function step(now) {
          var p = Math.min((now - t0) / 1200, 1);
          var v = Math.round(target * (1 - Math.pow(1 - p, 3)));
          el.textContent = v.toLocaleString();
          if (p < 1) requestAnimationFrame(step);
        })(t0);
      });
    }, { threshold: 0.5 });
    counters.forEach(function (el) { cntIO.observe(el); });
  }

  /* ---------- 햄버거 → 풀스크린 아코디언 (body scroll lock) ---------- */
  var ham = document.querySelector('.ham');
  if (ham) {
    ham.addEventListener('click', function () {
      var open = document.body.classList.toggle('nav-open');
      ham.setAttribute('aria-expanded', open);
      document.body.style.overflow = open ? 'hidden' : '';
    });
  }

  /* ---------- 가맹문의 폼 — fetch 제출 (논-JS 폴백: 일반 POST) ---------- */
  document.querySelectorAll('.inq-form, .inq-page-form').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = form.querySelector('[type="submit"]');
      btn.disabled = true;
      fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Requested-With': 'fetch' }
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.ok) {
            alert('가맹문의가 접수되었습니다. 빠르게 연락드리겠습니다.');
            form.reset();
          } else {
            alert(data.msg || '접수에 실패했습니다. 다시 시도해 주세요.');
          }
        })
        .catch(function () { form.submit(); })
        .finally(function () { btn.disabled = false; });
    });
  });
})();
