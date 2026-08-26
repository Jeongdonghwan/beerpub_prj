/* ============================================================
   main.js — 메인 페이지 전용
   풀페이지 전환(자체 easing) · 도트내비 · 섹션 재진입 리빌 ·
   센터포커스 캐러셀 · 비용 탭
   ============================================================ */
(function () {
  'use strict';

  var secs = Array.prototype.slice.call(document.querySelectorAll('.fp'));
  var nav = document.getElementById('fpnav');
  var mqDesktop = window.matchMedia('(min-width:1025px)');

  /* ---------- 도트 내비 생성 + 섹션 활성화 (이탈 시 .active 제거 → 재진입 재생) ---------- */
  var dots = [];
  if (nav && secs.length) {
    secs.forEach(function (s) {
      var a = document.createElement('a');
      a.href = '#' + s.id;
      a.setAttribute('aria-label', s.id);
      nav.appendChild(a);
    });
    dots = Array.prototype.slice.call(nav.children);
    var secIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var i = secs.indexOf(e.target);
        if (e.isIntersecting) {
          e.target.classList.add('active');
          dots.forEach(function (d) { d.classList.remove('on'); });
          dots[i].classList.add('on');
        } else {
          e.target.classList.remove('active'); /* 재진입 시 리빌 재생 */
        }
      });
    }, { threshold: 0.45 });
    secs.forEach(function (s) { secIO.observe(s); });
  }

  /* ---------- PC 풀페이지 전환 — fullpage.js 감성의 자체 easing ----------
     브라우저 기본 smooth + scroll-snap 조합은 전환이 뚝뚝 끊겨서,
     휠/키/도트 입력을 가로채 easeInOutCubic 900ms 로 직접 스크롤한다.
     모바일(≤1024px)은 일반 스크롤 유지. */
  if (secs.length && mqDesktop.matches) {
    /* CSS scroll-behavior:smooth 가 rAF 프레임마다 애니메이션을 걸지 않도록 해제 */
    document.documentElement.style.scrollBehavior = 'auto';

    var animating = false;
    var DUR = 900;

    function easeInOutCubic(t) {
      return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }
    function nearestIndex() {
      return Math.min(Math.max(Math.round(window.scrollY / window.innerHeight), 0), secs.length - 1);
    }
    function goTo(i) {
      i = Math.min(Math.max(i, 0), secs.length - 1);
      var start = window.scrollY;
      var end = secs[i].offsetTop;
      var dist = end - start;
      if (Math.abs(dist) < 2) return;
      animating = true;
      var t0 = performance.now();
      requestAnimationFrame(function step(now) {
        var p = Math.min((now - t0) / DUR, 1);
        window.scrollTo(0, start + dist * easeInOutCubic(p));
        if (p < 1) {
          requestAnimationFrame(step);
        } else {
          /* 관성 휠 잔여 이벤트가 곧바로 다음 전환을 트리거하지 않게 짧게 유지 */
          setTimeout(function () { animating = false; }, 80);
        }
      });
    }

    /* 휠: 한 번에 한 섹션 */
    window.addEventListener('wheel', function (e) {
      if (!mqDesktop.matches) return;
      if (document.body.classList.contains('modal-open')) return; /* 모달 내부 스크롤 허용 */
      e.preventDefault();
      if (animating || Math.abs(e.deltaY) < 4) return;
      goTo(nearestIndex() + (e.deltaY > 0 ? 1 : -1));
    }, { passive: false });

    /* 키보드: 방향키·PageUp/Down·스페이스 */
    window.addEventListener('keydown', function (e) {
      if (!mqDesktop.matches || document.body.classList.contains('modal-open')) return;
      var tag = (document.activeElement || {}).tagName;
      if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
      var delta = { ArrowDown: 1, PageDown: 1, ' ': 1, ArrowUp: -1, PageUp: -1 }[e.key];
      if (delta === undefined) return;
      e.preventDefault();
      if (!animating) goTo(nearestIndex() + delta);
    });

    /* 스크롤바 드래그 등 자유 스크롤 후 가장 가까운 섹션으로 정렬 */
    var settleTimer;
    window.addEventListener('scroll', function () {
      if (!mqDesktop.matches || animating) return;
      clearTimeout(settleTimer);
      settleTimer = setTimeout(function () {
        var i = nearestIndex();
        if (Math.abs(window.scrollY - secs[i].offsetTop) > 2) goTo(i);
      }, 140);
    }, { passive: true });

    /* 도트·스크롤 화살표·GNB(/#s6 형태 포함) 등 같은 페이지 #앵커는 easing 으로.
       다른 페이지에서 온 /#sN 링크는 브라우저 기본 이동. */
    document.addEventListener('click', function (e) {
      var a = e.target.closest('a[href*="#"]');
      if (!a || !mqDesktop.matches) return;
      if (a.pathname !== location.pathname || !a.hash) return;
      var target = document.querySelector(a.hash);
      if (target && target.classList.contains('fp')) {
        e.preventDefault();
        goTo(secs.indexOf(target));
      }
    });

    /* 다른 페이지에서 /#sN 으로 진입한 경우 해당 섹션으로 즉시 정렬 */
    if (location.hash) {
      var landing = document.querySelector(location.hash);
      if (landing && landing.classList.contains('fp')) {
        window.scrollTo(0, landing.offsetTop);
      }
    }
  }

  /* ---------- 시그니처 주류 센터포커스 캐러셀 (슬라이드는 서버 렌더 DOM) ---------- */
  var car = document.getElementById('car');
  if (car) {
    var slides = Array.prototype.slice.call(car.querySelectorAll('.dr'));
    var dotsEl = document.getElementById('carDots');
    var nameEl = document.getElementById('carName');
    var link = car.getAttribute('data-link') || '';
    var n = slides.length;
    var cur = 0;

    slides.forEach(function (el, i) {
      el.addEventListener('click', function () {
        if (i === cur && link) { location.href = link; return; }
        cur = i;
        render();
      });
    });

    if (dotsEl) {
      slides.forEach(function (_, i) {
        var d = document.createElement('i');
        d.addEventListener('click', function () { cur = i; render(); });
        dotsEl.appendChild(d);
      });
    }

    function render() {
      /* 잔 간격: 뷰포트 비례 (PC 최대 300px) — 양옆 잔이 살짝 겹치며 하단을 채움 */
      var gap = Math.min(window.innerWidth * 0.19, 300);
      slides.forEach(function (el, i) {
        var off = i - cur;
        if (off > n / 2) off -= n;
        if (off < -n / 2) off += n;
        var big = off === 0;
        el.style.transform = 'translateX(' + off * gap + 'px) scale(' + (big ? 1 : 0.82) + ')';
        el.style.zIndex = 10 - Math.abs(off);
        el.style.opacity = Math.abs(off) >= 2 ? 0.5 : 1;
        el.style.filter = big ? 'none' : 'brightness(.6)';
        el.classList.toggle('center', big);
      });
      if (nameEl) nameEl.textContent = slides[cur].getAttribute('data-name') || '';
      if (dotsEl) {
        Array.prototype.forEach.call(dotsEl.children, function (d, i) {
          d.classList.toggle('on', i === cur);
        });
      }
    }
    render();
    window.addEventListener('resize', render);
    setInterval(function () { cur = (cur + 1) % n; render(); }, 3500);
  }

  /* ---------- 개설절차 슬라이더 — 진행바 + 화살표 ---------- */
  var track = document.getElementById('stepsTrack');
  if (track) {
    var steps = track.children.length;
    var prev = document.getElementById('stepsPrev');
    var next = document.getElementById('stepsNext');
    var bar = document.getElementById('stepsBar');
    var idx = 0;
    function visible() { return window.matchMedia('(min-width:1025px)').matches ? 5 : 2; }
    function draw() {
      var v = visible();
      var max = Math.max(steps - v, 0);
      idx = Math.min(Math.max(idx, 0), max);
      track.style.transform = 'translateX(' + (-idx * (100 / v)) + '%)';
      bar.style.width = Math.min((idx + v) / steps * 100, 100) + '%';
      prev.disabled = idx === 0;
      next.disabled = idx === max;
    }
    prev.addEventListener('click', function () { idx--; draw(); });
    next.addEventListener('click', function () { idx++; draw(); });
    window.addEventListener('resize', draw);
    draw();
  }

  /* ---------- 비용 테이블 — Jinja 가 3평형 전부 렌더, JS 는 탭 show/hide 만 ---------- */
  var costTabs = document.querySelectorAll('.tabs button[data-size]');
  var costTables = document.querySelectorAll('.ctab[data-size]');
  costTabs.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var size = btn.getAttribute('data-size');
      costTabs.forEach(function (b) { b.classList.toggle('on', b === btn); });
      costTables.forEach(function (t) {
        t.classList.toggle('on', t.getAttribute('data-size') === size);
      });
    });
  });
})();
