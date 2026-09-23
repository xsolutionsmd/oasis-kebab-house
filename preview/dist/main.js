'use strict';
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const header = document.querySelector('.site-header');
const progress = document.querySelector('.scroll-progress span');
const toggle = document.querySelector('.menu-toggle');
const mobileNav = document.querySelector('.mobile-nav');
const year = document.querySelector('#year');
if (year) year.textContent = new Date().getFullYear();

let scrollScheduled = false;
function updateScrollState() {
  const scrollMax = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
  progress.style.transform = `scaleX(${Math.min(window.scrollY / scrollMax, 1)})`;
  header.classList.toggle('is-sticky', window.scrollY > 30);
  scrollScheduled = false;
}
window.addEventListener('scroll', () => {
  if (!scrollScheduled) {
    scrollScheduled = true;
    requestAnimationFrame(updateScrollState);
  }
}, { passive: true });
window.addEventListener('resize', updateScrollState, { passive: true });
updateScrollState();

if (toggle && mobileNav) {
  function setMenu(open, returnFocus = false) {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    mobileNav.hidden = !open;
    document.body.classList.toggle('nav-open', open);
    document.querySelector('main').inert = open;
    document.querySelector('footer').inert = open;
    if (open) mobileNav.querySelector('a')?.focus();
    else if (returnFocus) toggle.focus();
  }
  toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true', true));
  mobileNav.addEventListener('click', event => { if (event.target.closest('a')) setMenu(false); });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') setMenu(false, true);
  });
  window.matchMedia('(min-width: 851px)').addEventListener('change', event => { if (event.matches) setMenu(false); });
}

const video = document.querySelector('#hero-video');
const videoToggle = document.querySelector('#video-toggle');
if (video && videoToggle) {
  let userPaused = false;
  let heroVisible = true;
  const dataSaver = Boolean(navigator.connection?.saveData);
  const mayAutoplay = () => !reducedMotion.matches && !dataSaver && !userPaused && heroVisible && !document.hidden;
  function updateVideoButton() {
    const paused = video.paused;
    videoToggle.classList.toggle('is-paused', paused);
    videoToggle.setAttribute('aria-label', paused ? 'Play background video' : 'Pause background video');
    videoToggle.querySelector('span').textContent = paused ? 'Play film' : 'Pause film';
  }
  video.addEventListener('play', updateVideoButton);
  video.addEventListener('pause', updateVideoButton);
  video.addEventListener('error', () => { videoToggle.hidden = true; });
  videoToggle.addEventListener('click', () => {
    if (video.paused) {
      userPaused = false;
      video.play().catch(() => { videoToggle.hidden = true; });
    } else {
      userPaused = true;
      video.pause();
    }
  });
  if (mayAutoplay()) video.play().catch(() => { videoToggle.hidden = true; });
  reducedMotion.addEventListener('change', () => {
    if (mayAutoplay()) video.play().catch(() => {});
    else video.pause();
  });
  document.addEventListener('visibilitychange', () => {
    if (mayAutoplay()) video.play().catch(() => {});
    else video.pause();
  });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => {
      heroVisible = entries[0].isIntersecting;
      if (mayAutoplay()) video.play().catch(() => {});
      else video.pause();
    }, { threshold: 0.03 }).observe(document.querySelector('.hero'));
  }
  updateVideoButton();
}

if ('IntersectionObserver' in window && !reducedMotion.matches) {
  document.documentElement.classList.add('motion-ready');
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
  document.querySelectorAll('.reveal').forEach(element => observer.observe(element));
}

const galleryDialog = document.querySelector('#gallery-dialog');
if (galleryDialog) {
  let galleryTrigger;
  document.querySelectorAll('[data-image]').forEach(button => button.addEventListener('click', () => {
    galleryTrigger = button;
    galleryDialog.querySelector('img').src = button.dataset.image;
    galleryDialog.querySelector('img').alt = button.getAttribute('aria-label').replace(/^View /, '');
    galleryDialog.querySelector('p').textContent = button.dataset.caption;
    galleryDialog.showModal();
    galleryDialog.querySelector('.dialog-close').focus();
  }));
  galleryDialog.querySelector('.dialog-close').addEventListener('click', () => galleryDialog.close());
  galleryDialog.addEventListener('click', event => { if (event.target === galleryDialog) galleryDialog.close(); });
  galleryDialog.addEventListener('close', () => galleryTrigger?.focus());
}
