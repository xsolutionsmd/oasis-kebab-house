'use strict';

// Shared motion: native scrolling stays native; only deliberate anchor clicks glide.
window.OasisMotion = (() => {
	const preference = matchMedia('(prefers-reduced-motion: reduce)');
	const ease = 'cubic-bezier(.22, 1, .36, 1)';
	const locks = new Set();
	const header = document.querySelector('.site-header');
	const toggle = document.querySelector('.menu-toggle');
	const shell = document.querySelector('.mobile-nav-shell');
	const nav = document.querySelector('.mobile-nav');
	const background = [
		...document.querySelectorAll('main, footer, .brand, .skip-link'),
	];
	let menuOpen = false;
	let menuSequence = 0;
	let panelAnimation;
	let linkAnimations = [];
	let scrollFrame = 0;
	let scrollSequence = 0;

	function lock(owner, active) {
		if (active) locks.add(owner);
		else locks.delete(owner);
		document.documentElement.classList.toggle('overlay-open', locks.size > 0);
		document.dispatchEvent(new Event('oasis:overlaychange'));
	}

	function createArrow() {
		const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
		svg.setAttribute('viewBox', '0 0 24 24');
		svg.setAttribute('class', 'arrow-icon');
		svg.setAttribute('aria-hidden', 'true');
		svg.setAttribute('focusable', 'false');
		const path = document.createElementNS(svg.namespaceURI, 'path');
		path.setAttribute('d', 'M5 19 19 5M5 5h14v14');
		svg.append(path);
		return svg;
	}

	function focusWithoutScroll(element) {
		if (!element) return;
		if (!element.matches('a, button, input, [tabindex]')) {
			element.tabIndex = -1;
			element.addEventListener(
				'blur',
				() => element.removeAttribute('tabindex'),
				{ once: true },
			);
		}
		element.focus({ preventScroll: true });
	}

	function stopScroll() {
		cancelAnimationFrame(scrollFrame);
		scrollSequence += 1;
		document.documentElement.classList.remove('anchor-gliding');
	}

	function scrollToTarget(target, { focus = true, immediate = false } = {}) {
		stopScroll();
		const sequence = scrollSequence;
		target.classList.add('is-visible');
		target
			.querySelectorAll('.reveal')
			.forEach((element) => element.classList.add('is-visible'));
		target.querySelectorAll('img[loading="lazy"]').forEach((image) => {
			image.loading = 'eager';
		});
		const start = window.scrollY;
		const landing =
			(target.matches('section, .menu-experience') &&
				target.querySelector('[data-anchor-content]')) ||
			target;
		// Measure layout, not the temporary transform of an entering reveal.
		let landingTop = 0;
		for (let element = landing; element; element = element.offsetParent)
			landingTop += element.offsetTop;
		const offset =
			header.getBoundingClientRect().height + (landing === target ? 20 : 32);
		const destination =
			target.id === 'top'
				? 0
				: Math.max(
						0,
						Math.min(
							landingTop - offset,
							document.documentElement.scrollHeight - innerHeight,
						),
					);
		const distance = destination - start;
		const finish = () => {
			document.documentElement.classList.remove('anchor-gliding');
			if (focus) focusWithoutScroll(target);
		};
		if (immediate || preference.matches || Math.abs(distance) < 4) {
			window.scrollTo({ top: destination, behavior: 'instant' });
			finish();
			return;
		}
		// Long links get time to decelerate instead of racing through the page.
		const duration = Math.min(1600, 600 + Math.abs(distance) * 0.16);
		let started;
		document.documentElement.classList.add('anchor-gliding');
		function step(now) {
			if (sequence !== scrollSequence) return;
			started ??= now;
			const elapsed = Math.min((now - started) / duration, 1);
			const eased = (1 - Math.cos(Math.PI * elapsed)) / 2;
			window.scrollTo({ top: start + distance * eased, behavior: 'instant' });
			if (elapsed < 1) scrollFrame = requestAnimationFrame(step);
			else finish();
		}
		scrollFrame = requestAnimationFrame(step);
	}

	['wheel', 'touchstart', 'pointerdown'].forEach((type) => {
		window.addEventListener(type, stopScroll, { passive: true });
	});
	window.addEventListener('keydown', (event) => {
		if (
			[
				'ArrowDown',
				'ArrowUp',
				'PageDown',
				'PageUp',
				'Home',
				'End',
				' ',
				'Escape',
				'Tab',
			].includes(event.key)
		)
			stopScroll();
	});
	window.addEventListener('popstate', stopScroll);

	// Cross-page links use the same framing once fonts and images have settled.
	// Never take the scroll position back after the visitor starts interacting.
	const initialScrollSequence = scrollSequence;
	window.addEventListener(
		'load',
		async () => {
			await document.fonts.ready;
			if (!location.hash || scrollSequence !== initialScrollSequence) return;
			let target;
			try {
				target = document.getElementById(
					decodeURIComponent(location.hash.slice(1)),
				);
			} catch {
				return;
			}
			if (target) scrollToTarget(target, { focus: false, immediate: true });
		},
		{ once: true },
	);

	async function setMenu(open, { immediate = false } = {}) {
		const sequence = ++menuSequence;
		const wasHidden = shell.hidden;
		const previous = wasHidden
			? {
					opacity: preference.matches ? '0' : '1',
					transform: preference.matches ? 'none' : 'translateY(-100%)',
				}
			: {
					opacity: getComputedStyle(nav).opacity,
					transform: getComputedStyle(nav).transform,
				};
		panelAnimation?.cancel();
		linkAnimations.forEach((animation) => animation.cancel());
		linkAnimations = [];
		menuOpen = open;
		toggle.setAttribute('aria-expanded', String(open));
		toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
		nav.inert = !open;
		if (open) {
			stopScroll();
			shell.style.setProperty(
				'--menu-top',
				`${Math.max(0, header.getBoundingClientRect().bottom)}px`,
			);
			shell.hidden = false;
			lock('menu', true);
			background.forEach((element) => {
				element.inert = true;
			});
			focusWithoutScroll(nav.querySelector('a'));
		} else if (!wasHidden) {
			focusWithoutScroll(toggle);
		}
		const destination = {
			opacity: open || !preference.matches ? '1' : '0',
			transform:
				open || preference.matches ? 'translateY(0)' : 'translateY(-100%)',
		};
		nav.style.opacity = destination.opacity;
		nav.style.transform = destination.transform;
		if (!immediate && !(wasHidden && !open)) {
			const duration = preference.matches ? 140 : open ? 520 : 360;
			panelAnimation = nav.animate([previous, destination], {
				duration,
				easing: open || preference.matches ? ease : 'cubic-bezier(.4, 0, 1, 1)',
			});
			if (open && wasHidden && !preference.matches) {
				linkAnimations = [...nav.querySelectorAll('a, p')].map(
					(element, index) =>
						element.animate(
							[
								{ opacity: 0, transform: 'translateY(18px)' },
								{ opacity: 1, transform: 'translateY(0)' },
							],
							{
								duration: 380,
								delay: 70 + index * 35,
								easing: ease,
								fill: 'backwards',
							},
						),
				);
			}
			try {
				await panelAnimation.finished;
			} catch {
				return false;
			}
		}
		if (sequence !== menuSequence) return false;
		if (!open) {
			shell.hidden = true;
			background.forEach((element) => {
				element.inert = false;
			});
			lock('menu', false);
		}
		return true;
	}

	if (toggle && shell && nav) {
		toggle.addEventListener('click', () => setMenu(!menuOpen));
		document.addEventListener('keydown', (event) => {
			if (shell.hidden) return;
			if (event.key === 'Escape') {
				event.preventDefault();
				setMenu(false);
			}
			if (event.key !== 'Tab') return;
			const controls = menuOpen
				? [toggle, ...nav.querySelectorAll('a')]
				: [toggle];
			const first = controls[0];
			const last = controls[controls.length - 1];
			if (
				event.shiftKey &&
				(document.activeElement === first ||
					!controls.includes(document.activeElement))
			) {
				event.preventDefault();
				focusWithoutScroll(last);
			} else if (
				!event.shiftKey &&
				(document.activeElement === last ||
					!controls.includes(document.activeElement))
			) {
				event.preventDefault();
				focusWithoutScroll(first);
			}
		});
		matchMedia('(min-width: 851px)').addEventListener('change', (event) => {
			if (event.matches) setMenu(false, { immediate: true });
		});
		window.addEventListener(
			'resize',
			() => {
				if (!shell.hidden)
					shell.style.setProperty(
						'--menu-top',
						`${Math.max(0, header.getBoundingClientRect().bottom)}px`,
					);
			},
			{ passive: true },
		);
		window.addEventListener('pagehide', () =>
			setMenu(false, { immediate: true }),
		);
	}

	document.addEventListener('click', async (event) => {
		const link = event.target.closest('a[href]');
		if (
			!link ||
			event.defaultPrevented ||
			event.button !== 0 ||
			event.metaKey ||
			event.ctrlKey ||
			event.shiftKey ||
			event.altKey ||
			link.target ||
			link.hasAttribute('download')
		)
			return;
		const url = new URL(link.href, location.href);
		const normalize = (path) => path.replace(/index\.html$/, '');
		const samePage =
			url.origin === location.origin &&
			normalize(url.pathname) === normalize(location.pathname) &&
			url.search === location.search;
		let target;
		try {
			target =
				samePage &&
				url.hash &&
				document.getElementById(decodeURIComponent(url.hash.slice(1)));
		} catch {
			return;
		}
		const fromMenu = nav?.contains(link);
		if (!target && !fromMenu) return;
		event.preventDefault();
		if (fromMenu && !(await setMenu(false))) return;
		if (target) {
			if (location.hash !== url.hash) history.pushState(null, '', url.hash);
			scrollToTarget(target);
		} else location.assign(url.href);
	});

	function dialogController(dialog) {
		let trigger;
		let animation;
		let closing = false;
		async function close() {
			if (!dialog.open || closing) return;
			closing = true;
			const current = {
				opacity: getComputedStyle(dialog).opacity,
				transform: getComputedStyle(dialog).transform,
			};
			animation?.cancel();
			dialog.classList.add('is-closing');
			animation = dialog.animate(
				[
					current,
					{
						opacity: 0,
						transform: preference.matches
							? 'none'
							: 'translateY(12px) scale(.99)',
					},
				],
				{ duration: preference.matches ? 120 : 220, easing: ease },
			);
			try {
				await animation.finished;
			} catch {
				return;
			}
			dialog.close();
			animation.cancel();
			dialog.classList.remove('is-closing');
			closing = false;
		}
		dialog
			.querySelectorAll('.dialog-close, [data-close]')
			.forEach((button) => button.addEventListener('click', close));
		dialog.addEventListener('cancel', (event) => {
			event.preventDefault();
			close();
		});
		dialog.addEventListener('click', (event) => {
			const rect = dialog.getBoundingClientRect();
			if (
				event.target === dialog &&
				(event.clientX < rect.left ||
					event.clientX > rect.right ||
					event.clientY < rect.top ||
					event.clientY > rect.bottom)
			)
				close();
		});
		dialog.addEventListener('close', () => {
			lock(dialog, false);
			focusWithoutScroll(trigger);
		});
		return {
			open(source) {
				trigger = source;
				lock(dialog, true);
				dialog.showModal();
				focusWithoutScroll(dialog.querySelector('.dialog-close'));
				animation = dialog.animate(
					[
						{
							opacity: 0,
							transform: preference.matches
								? 'none'
								: 'translateY(18px) scale(.985)',
						},
						{ opacity: 1, transform: 'translateY(0) scale(1)' },
					],
					{ duration: preference.matches ? 140 : 380, easing: ease },
				);
			},
			close,
		};
	}

	preference.addEventListener('change', () => {
		stopScroll();
		if (!shell.hidden) setMenu(menuOpen, { immediate: true });
	});
	return { createArrow, scrollToTarget, dialogController };
})();
