/**
 * main.js — MJ WebTech Pvt. Ltd. v2
 * Handles: AOS, navbar scroll, back-to-top, counter animation,
 *          flash auto-dismiss, smooth scroll, char counter, file UX.
 */
'use strict';

(function () {

  /* ── AOS ── */
  if (typeof AOS !== 'undefined') {
    AOS.init({ duration: 700, easing: 'ease-out-cubic', once: true, offset: 60 });
  }

  /* ── Navbar scroll glow ── */
  const navbar = document.getElementById('mainNavbar');
  function updateNavbar() {
    if (navbar) navbar.classList.toggle('scrolled', window.scrollY > 40);
  }
  window.addEventListener('scroll', updateNavbar, { passive: true });
  updateNavbar();

  /* ── Back to top ── */
  const btt = document.getElementById('backToTop');
  window.addEventListener('scroll', () => {
    if (btt) btt.classList.toggle('visible', window.scrollY > 400);
  }, { passive: true });
  btt?.addEventListener('click', e => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); });

  /* ── Flash auto-dismiss (5 s) ── */
  document.querySelectorAll('.flash-item').forEach(el => {
    setTimeout(() => bootstrap.Alert.getOrCreateInstance(el)?.close(), 5500);
  });

  /* ── Smooth anchor scroll ── */
  const getScrollOffset = () => {
    const navHeight = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--navbar-h')) || 72;
    return navHeight + 16;
  };

  const scrollToTarget = target => {
    if (!target) return;
    const offset = getScrollOffset();
    const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
    window.scrollTo({ top, behavior: 'smooth' });
    target.classList.add('scroll-highlight');
    window.setTimeout(() => target.classList.remove('scroll-highlight'), 1700);
  };

  const ensureTargetVisible = target => {
    if (!target) return;
    const offset = getScrollOffset();
    const rect = target.getBoundingClientRect();
    if (rect.top > window.innerHeight * 0.4 || rect.top < offset - 10) {
      const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    }
  };

  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', e => {
      const id = link.getAttribute('href').slice(1);
      const target = document.getElementById(id);
      if (target) {
        e.preventDefault();
        scrollToTarget(target);
        const nav = document.getElementById('navMenu');
        if (nav?.classList.contains('show')) bootstrap.Collapse.getOrCreateInstance(nav).hide();
      }
    });
  });

  const handleInitialHashScroll = () => {
    const hash = window.location.hash;
    if (!hash) return;
    const target = document.getElementById(hash.slice(1));
    if (target) {
      window.setTimeout(() => {
        scrollToTarget(target);
        window.setTimeout(() => ensureTargetVisible(target), 220);
      }, 120);
    }
  };

  if (document.readyState === 'complete') {
    handleInitialHashScroll();
  } else {
    window.addEventListener('load', handleInitialHashScroll);
  }

  /* ── Animated counters ── */
  const counters = document.querySelectorAll('[data-count]');
  if (counters.length) {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const target = +el.dataset.count;
        let cur = 0;
        const step = Math.max(1, Math.ceil(target / 60));
        const t = setInterval(() => {
          cur = Math.min(cur + step, target);
          el.textContent = cur;
          if (cur >= target) clearInterval(t);
        }, 25);
        obs.unobserve(el);
      });
    }, { threshold: 0.5 });
    counters.forEach(c => obs.observe(c));
  }

  /* ── Textarea character counter ── */
  document.querySelectorAll('textarea[maxlength], textarea.mj-input').forEach(ta => {
    const max = ta.getAttribute('maxlength') || 3000;
    const wrapper = document.createElement('div');
    wrapper.className = 'text-end text-muted small char-counter mt-1';
    wrapper.textContent = `0 / ${max}`;
    ta.parentNode.insertBefore(wrapper, ta.nextSibling);
    ta.addEventListener('input', () => {
      const len = ta.value.length;
      wrapper.textContent = `${len} / ${max}`;
      wrapper.style.color = len > max * 0.9 ? '#F87171' : '';
    });
  });

  /* ── Form validation: add .was-validated on submit attempt ── */
  document.querySelectorAll('form[novalidate]').forEach(form => {
    form.addEventListener('submit', () => form.classList.add('was-validated'));
  });

  /* ── Active nav link from URL ── */
  const path = window.location.pathname;
  document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && path.startsWith(href)) {
      link.classList.add('active');
    } else if (href === '/' && path === '/') {
      link.classList.add('active');
    }
  });

})();
