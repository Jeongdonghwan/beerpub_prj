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

  /* ---------- 히어로 문구: 영상 처음 3초 표시 → 사라짐 → 마지막 3초 다시 표시 (루프마다 반복) ---------- */
  var hero = document.getElementById('s1');
  var heroTimeVideo = document.getElementById('heroVideo');
  if (hero && heroTimeVideo) {
    var COPY_SEC = 3;
    function updateHeroCopy() {
      var d = heroTimeVideo.duration;
      if (!d || isNaN(d)) return;
      var t = heroTimeVideo.currentTime;
      var show = t < COPY_SEC || t > d - COPY_SEC;
      hero.classList.toggle('s1--clean', !show);
    }
    heroTimeVideo.addEventListener('timeupdate', updateHeroCopy);
    heroTimeVideo.addEventListener('loadedmetadata', updateHeroCopy);
    updateHeroCopy();
    if (hero.classList.contains('s1--clean') && heroTimeVideo.readyState === 0) {
      hero.classList.remove('s1--clean'); /* 메타데이터 로드 전엔 문구 표시(영상 실패 대비) */
    }
  } else if (hero) {
    hero.classList.remove('s1--clean'); /* 영상 없는 폴백은 문구 상시 표시 */
  }

  /* ---------- 히어로 소리 — 자동으로 켜기 시도, 브라우저가 막으면 첫 인터랙션에서 자동 켬.
     버튼은 켜짐 상태에서 '소리 끄기' 토글로 동작 ---------- */
  var heroVideo = document.getElementById('heroVideo');
  var sndBtn = document.getElementById('heroSnd');
  if (heroVideo && sndBtn) {
    var autoArm = true; /* 사용자가 직접 끄기 전까지 자동 켜기 시도 유지 */
    function syncSnd() {
      var on = !heroVideo.muted;
      sndBtn.classList.toggle('on', on);
      sndBtn.setAttribute('aria-pressed', String(on));
      sndBtn.innerHTML = on ? '🔊 <span>소리 끄기</span>' : '🔇 <span>소리 켜기</span>';
    }
    function soundOn() {
      heroVideo.muted = false;
      heroVideo.volume = 1;
      var p = heroVideo.play();
      if (p && p.catch) {
        p.then(function () { autoArm = false; syncSnd(); })
         .catch(function () { heroVideo.muted = true; heroVideo.play(); syncSnd(); });
      } else {
        autoArm = false;
        syncSnd();
      }
      syncSnd();
    }
    sndBtn.addEventListener('click', function () {
      if (heroVideo.muted) {
        soundOn();
      } else {
        heroVideo.muted = true;
        autoArm = false; /* 직접 껐으면 자동으로 다시 켜지 않음 */
        syncSnd();
      }
    });
    soundOn(); /* 1차: 페이지 로드 즉시 시도 (차단될 수 있음) */
    ['pointerdown', 'touchstart', 'keydown', 'wheel'].forEach(function (t) {
      window.addEventListener(t, function onAct() {
        if (autoArm && heroVideo.muted) soundOn();
        if (!autoArm || !heroVideo.muted) window.removeEventListener(t, onAct, true);
      }, { capture: true, passive: true });
    });
  }

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

    /* 휠: 한 번에 한 섹션 (히어로 문구가 아직 안 나왔으면 첫 휠은 문구 등장에 사용) */
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
      var gap = Math.min(window.innerWidth * 0.185, 270);
      slides.forEach(function (el, i) {
        var off = i - cur;
        if (off > n / 2) off -= n;
        if (off < -n / 2) off += n;
        var big = off === 0;
        el.style.transform = 'translateX(' + off * gap + 'px)';
        el.style.zIndex = 10 - Math.abs(off);
        el.style.opacity = 1;
        el.style.filter = big ? 'none' : 'brightness(.88)';
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
