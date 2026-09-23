'use strict';
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const header = document.querySelector('.site-header');
const progress = document.querySelector('.scroll-progress span');
const year = document.querySelector('#year');
if (year) year.textContent = new Date().getFullYear();

let scrollScheduled = false;
let scrollMax = 1;
function measurePage() {
	scrollMax = Math.max(
		document.documentElement.scrollHeight - window.innerHeight,
		1,
	);
	updateScrollState();
}
function updateScrollState() {
	progress.style.transform = `scaleX(${Math.min(window.scrollY / scrollMax, 1)})`;
	header.classList.toggle('is-sticky', window.scrollY > 30);
	scrollScheduled = false;
}
window.addEventListener(
	'scroll',
	() => {
		if (!scrollScheduled) {
			scrollScheduled = true;
			requestAnimationFrame(updateScrollState);
		}
	},
	{ passive: true },
);
window.addEventListener('resize', measurePage, { passive: true });
if ('ResizeObserver' in window)
	new ResizeObserver(measurePage).observe(document.body);
measurePage();

const video = document.querySelector('#hero-video');
const videoToggle = document.querySelector('#video-toggle');
if (video && videoToggle) {
	let userPaused = false;
	let heroVisible = true;
	const dataSaver = Boolean(navigator.connection?.saveData);
	const mayAutoplay = () =>
		!reducedMotion.matches &&
		!dataSaver &&
		!userPaused &&
		heroVisible &&
		!document.documentElement.classList.contains('overlay-open') &&
		!document.hidden;
	function updateVideoButton() {
		const paused = video.paused;
		videoToggle.classList.toggle('is-paused', paused);
		videoToggle.setAttribute(
			'aria-label',
			paused ? 'Play background video' : 'Pause background video',
		);
		videoToggle.querySelector('span').textContent = paused
			? 'Play film'
			: 'Pause film';
	}
	video.addEventListener('play', updateVideoButton);
	video.addEventListener('pause', updateVideoButton);
	video.addEventListener('error', () => {
		videoToggle.hidden = true;
	});
	videoToggle.addEventListener('click', () => {
		if (video.paused) {
			userPaused = false;
			video.play().catch(() => {
				videoToggle.hidden = true;
			});
		} else {
			userPaused = true;
			video.pause();
		}
	});
	if (mayAutoplay())
		video.play().catch(() => {
			videoToggle.hidden = true;
		});
	reducedMotion.addEventListener('change', () => {
		if (mayAutoplay()) video.play().catch(() => {});
		else video.pause();
	});
	document.addEventListener('visibilitychange', () => {
		if (mayAutoplay()) video.play().catch(() => {});
		else video.pause();
	});
	document.addEventListener('oasis:overlaychange', () => {
		if (mayAutoplay()) video.play().catch(() => {});
		else video.pause();
	});
	if ('IntersectionObserver' in window) {
		new IntersectionObserver(
			(entries) => {
				heroVisible = entries[0].isIntersecting;
				if (mayAutoplay()) video.play().catch(() => {});
				else video.pause();
			},
			{ threshold: 0.03 },
		).observe(document.querySelector('.hero'));
	}
	updateVideoButton();
}

if ('IntersectionObserver' in window && !reducedMotion.matches) {
	document.documentElement.classList.add('motion-ready');
	const observer = new IntersectionObserver(
		(entries) => {
			entries.forEach((entry) => {
				if (entry.isIntersecting) {
					entry.target.classList.add('is-visible');
					observer.unobserve(entry.target);
				}
			});
		},
		{ rootMargin: '160px 0px 160px 0px', threshold: 0.01 },
	);
	document
		.querySelectorAll('.reveal')
		.forEach((element) => observer.observe(element));
}

const galleryDialog = document.querySelector('#gallery-dialog');
if (galleryDialog) {
	const gallery = OasisMotion.dialogController(galleryDialog);
	document.querySelectorAll('[data-image]').forEach((button) =>
		button.addEventListener('click', () => {
			const thumbnail = button.querySelector('img');
			const fullImage = galleryDialog.querySelector('img');
			fullImage.width = thumbnail.naturalWidth || 1000;
			fullImage.height = thumbnail.naturalHeight || 1000;
			galleryDialog.querySelector('img').src = button.dataset.image;
			galleryDialog.querySelector('img').alt = button
				.getAttribute('aria-label')
				.replace(/^View /, '');
			galleryDialog.querySelector('p').textContent = button.dataset.caption;
			gallery.open(button);
		}),
	);
}
