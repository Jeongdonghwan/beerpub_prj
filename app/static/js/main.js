/* ============================================================
   main.js — 메인 페이지 전용
   풀페이지 도트내비 + 섹션 재진입 리빌 · 센터포커스 캐러셀 · 비용 탭
   ============================================================ */
(function () {
  'use strict';

  /* ---------- 풀페이지: 섹션 활성화 + 도트 내비 (이탈 시 .active 제거 → 재진입 재생) ---------- */
  var secs = Array.prototype.slice.call(document.querySelectorAll('.fp'));
  var nav = document.getElementById('fpnav');
  if (nav && secs.length) {
    secs.forEach(function (s) {
      var a = document.createElement('a');
      a.href = '#' + s.id;
      a.setAttribute('aria-label', s.id);
      nav.appendChild(a);
    });
    var dots = Array.prototype.slice.call(nav.children);
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

  /* ---------- PC 풀페이지: 휠 한 번 = 한 섹션 전환 ----------
     CSS scroll-snap 만으로는 일반 스크롤처럼 흘러가므로 휠을 가로채
     다음/이전 섹션으로만 이동. 모바일(≤1024px)·모달 열림 상태는 제외. */
  var mqDesktop = window.matchMedia('(min-width:1025px)');
  var wheelLock = false;
  window.addEventListener('wheel', function (e) {
    if (!mqDesktop.matches || !secs.length) return;
    if (document.body.classList.contains('modal-open')) return; /* 모달 내부 스크롤 허용 */
    e.preventDefault();
    if (wheelLock || Math.abs(e.deltaY) < 4) return;
    var idx = Math.round(window.scrollY / window.innerHeight);
    var next = Math.min(Math.max(idx + (e.deltaY > 0 ? 1 : -1), 0), secs.length - 1);
    if (next === idx) return;
    wheelLock = true;
    secs[next].scrollIntoView({ behavior: 'smooth' });
    setTimeout(function () { wheelLock = false; }, 850);
  }, { passive: false });

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
      slides.forEach(function (el, i) {
        var off = i - cur;
        if (off > n / 2) off -= n;
        if (off < -n / 2) off += n;
        var big = off === 0;
        el.style.transform = 'translateX(' + off * 180 + 'px) scale(' + (big ? 1 : 0.78) + ')';
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
    setInterval(function () { cur = (cur + 1) % n; render(); }, 3500);
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
