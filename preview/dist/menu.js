'use strict';
const categoryNav = document.querySelector('.category-nav');
const menuResults = document.querySelector('#menu-results');
const menuSearch = document.querySelector('#menu-search');
const dishDialog = document.querySelector('#dish-dialog');
let menuItems = [];
let currentCategory = 'All dishes';
const dish = OasisMotion.dialogController(dishDialog);

const categories = [
	'All dishes',
	'Mains',
	'Kebabs',
	'Starters',
	'Salads',
	'Soups',
	'Seafood',
	'Sides',
	'Desserts',
	'Drinks',
	'Lunch Specials',
];
const imageFor = (item) =>
	item.image && ['plov.webp', 'samsa.webp'].includes(item.image)
		? `media/${item.image}`
		: null;

function renderCategories() {
	categoryNav.replaceChildren();
	categories.forEach((category) => {
		const button = document.createElement('button');
		button.type = 'button';
		button.textContent = category;
		const arrow = OasisMotion.createArrow();
		button.append(arrow);
		button.setAttribute('aria-pressed', String(currentCategory === category));
		button.addEventListener('click', () => {
			currentCategory = category;
			categoryNav
				.querySelectorAll('button')
				.forEach((control) =>
					control.setAttribute('aria-pressed', String(control === button)),
				);
			renderMenu();
			// Keep the chosen category and horizontal rail in place. No forced jump.
			if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
				menuResults.animate(
					[
						{ opacity: 0.35, transform: 'translateY(6px)' },
						{ opacity: 1, transform: 'translateY(0)' },
					],
					{ duration: 220, easing: 'ease-out' },
				);
			}
		});
		categoryNav.append(button);
	});
}

function makeDishRow(item) {
	const button = document.createElement('button');
	button.type = 'button';
	button.className = 'dish-row';
	button.setAttribute('aria-label', `View ${item.name}`);
	const body = document.createElement('div');
	body.className = 'dish-row-body';
	const name = document.createElement('h4');
	name.textContent = item.name;
	body.append(name);
	if (item.description) {
		const description = document.createElement('p');
		description.textContent = item.description;
		body.append(description);
	}
	button.append(body);
	const photo = imageFor(item);
	if (photo) {
		const image = document.createElement('img');
		image.className = 'dish-row-image';
		image.src = photo;
		image.alt = '';
		image.loading = 'lazy';
		button.append(image);
	}
	const arrow = OasisMotion.createArrow();
	arrow.classList.add('dish-row-arrow');
	button.append(arrow);
	button.addEventListener('click', () => showDish(item, button));
	return button;
}

function renderMenu() {
	const query = menuSearch.value.trim().toLowerCase();
	const visible = menuItems.filter(
		(item) =>
			(currentCategory === 'All dishes' || item.category === currentCategory) &&
			`${item.name} ${item.description} ${item.category}`
				.toLowerCase()
				.includes(query),
	);
	document.querySelector('#menu-status').textContent =
		`${visible.length} ${visible.length === 1 ? 'dish' : 'dishes'} shown`;
	menuResults.replaceChildren();
	if (!visible.length) {
		const empty = document.createElement('p');
		empty.className = 'menu-empty';
		empty.textContent = 'No dishes found. Try another search or category.';
		menuResults.append(empty);
		return;
	}
	categories.slice(1).forEach((category) => {
		const items = visible.filter((item) => item.category === category);
		if (!items.length) return;
		const section = document.createElement('section');
		section.className = 'menu-category';
		section.id = `category-${category.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;
		const header = document.createElement('div');
		header.className = 'menu-category-header';
		const heading = document.createElement('h3');
		heading.textContent = category;
		const count = document.createElement('span');
		count.textContent = `${items.length} ${items.length === 1 ? 'dish' : 'dishes'}`;
		header.append(heading, count);
		const list = document.createElement('div');
		list.className = 'dish-list';
		items.forEach((item) => list.append(makeDishRow(item)));
		section.append(header, list);
		menuResults.append(section);
	});
}

function showDish(item, trigger) {
	dishDialog.querySelector('#dish-category').textContent = item.category;
	dishDialog.querySelector('#dish-title').textContent = item.name;
	dishDialog.querySelector('#dish-description').textContent =
		item.description || 'From the Oasis menu.';
	const frame = dishDialog.querySelector('.dish-dialog-image');
	const photo = imageFor(item);
	frame.hidden = !photo;
	dishDialog.classList.toggle('has-image', Boolean(photo));
	if (photo) {
		frame.querySelector('img').src = photo;
		frame.querySelector('img').alt = item.name;
	}
	dish.open(trigger);
}

menuSearch.addEventListener('input', renderMenu);
renderCategories();
fetch('menu.json')
	.then((response) => {
		if (!response.ok) throw Error('Menu unavailable');
		return response.json();
	})
	.then((items) => {
		menuItems = items;
		renderMenu();
	})
	.catch(() => {
		menuResults.textContent = 'The menu is temporarily unavailable.';
	});
