'use strict';
// Public site for Oasis Uzbek Kebab House. admin.js reuses $, $$, esc, money, api,
// toast, head, arrow, niceTime and config, so keep those as script-level globals.
const $ = (q, el = document) => el.querySelector(q), $$ = (q, el = document) => [...el.querySelectorAll(q)];
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const money = v => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(v / 100);
const arrow = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h16m-6-6 6 6-6 6"/></svg>';
const media = n => '/static/media/' + n;
const dishPhoto = i => media(i.id === 'samarkand-plov' ? 'plov-dish.webp' : i.image);
const PHONE = '410-777-9700', TEL = 'tel:+14107779700';
const maps = 'https://www.google.com/maps/search/?api=1&query=Oasis+Uzbek+Kebab+House+1430+Reisterstown+Rd+Pikesville+MD';
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const galleries = [
  ['platter.webp', 'From the grill', 'CDFcEOjDS2g'], ['interior.webp', 'At our table', 'CVsu8vdLwXW'],
  ['samarkand.webp', 'A glimpse of Samarkand', 'CAtMtTmjMs0'], ['samsa.webp', 'Tandoori samsa', 'CVsvWw8L0YE'],
  ['patio.webp', 'Our patio', 'C9ApN0guIgQ'], ['bread.webp', 'Fresh from the tandoor', 'CAtMDuoDoN9'],
  ['grill.webp', 'Over the coals', 'CcWhAdwrbpW'], ['entrance.webp', 'Welcome to Oasis', 'CzfYlPdMIi-'],
  ['shrimp.webp', 'Garlic butter shrimp', 'CBPU9AxD6Uk'],
];
let config, items = [], bag = [], toastTimer, search = '', menuObserver, statusTimer;
try { bag = JSON.parse(localStorage.getItem('oasis-bag') || '[]'); if (!Array.isArray(bag)) bag = []; } catch { bag = []; }

async function api(path, options = {}) {
  const r = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': config?.csrf || '', ...options.headers } });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || 'Something went wrong. Please try again.');
  return data;
}
function toast(text, action = '') {
  const t = $('#toast');
  t.innerHTML = `<span>${esc(text)}</span>${action}`;
  t.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('visible'), 4000);
}

/* ---------- Hours ---------- */
function minuteLabel(m) { const h = Math.floor(m / 60) % 24; return `${(h % 12) || 12}${m % 60 ? ':' + String(m % 60).padStart(2, '0') : ''} ${h >= 12 ? 'PM' : 'AM'}`; }
function nyNow() {
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', weekday: 'short', hour: 'numeric', minute: 'numeric', hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date()).map(p => [p.type, p.value]));
  return { day: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].indexOf(parts.weekday), minute: Number(parts.hour) * 60 + Number(parts.minute), date: `${parts.year}-${parts.month}-${parts.day}` };
}
function openState() {
  const { day, minute, date } = nyNow(), hours = config.settings.hours;
  const today = config.settings.closures.includes(date) ? null : hours[day];
  if (today && minute >= today[0] && minute < today[1]) return { open: true, text: `Open until ${minuteLabel(today[1])}` };
  if (today && minute < today[0]) return { open: false, text: `Opens today at ${minuteLabel(today[0])}` };
  for (let n = 1; n <= 7; n++) {
    const h = hours[(day + n) % 7];
    if (h) return { open: false, text: `Closed · opens ${n === 1 ? 'tomorrow' : DAYS[(day + n) % 7]} ${minuteLabel(h[0])}` };
  }
  return { open: false, text: 'Closed' };
}
function hoursRows() {
  // Group consecutive days that share hours: "Monday – Saturday  11 AM – 10 PM".
  const h = config.settings.hours, today = nyNow().day, rows = [];
  for (let n = 0; n < 7; n++) {
    const label = h[n] ? h[n].map(minuteLabel).join(' – ') : 'Closed', last = rows.at(-1);
    if (last && last.label === label) { last.end = n; last.today ||= n === today; } else rows.push({ start: n, end: n, label, today: n === today });
  }
  return rows.map(r => `<div class="hours-row${r.today ? ' today' : ''}"><span>${DAYS[r.start]}${r.end > r.start ? ' – ' + DAYS[r.end] : ''}</span><span>${r.label}</span></div>`).join('');
}
function renderChrome() {
  // The visit page lists hours itself; don't repeat them in its footer.
  if (location.pathname === '/visit') $('#footer-hours').parentElement.hidden = true; else $('#footer-hours').innerHTML = hoursRows();
}

/* ---------- Bag ---------- */
const bagCount = () => bag.reduce((n, l) => n + l.quantity, 0);
function persistBag() {
  try { localStorage.setItem('oasis-bag', JSON.stringify(bag)); } catch {}
  const count = bagCount();
  $('#bag-count').textContent = count || '';
  $('#open-bag').setAttribute('aria-label', `Open your order, ${count} ${count === 1 ? 'item' : 'items'}`);
  updateOrderSummaries();
}
function validBag() { bag = bag.filter(l => l && items.some(i => i.id === l.id) && Number.isInteger(l.quantity) && l.quantity > 0 && l.quantity <= 20 && typeof l.choices === 'object'); persistBag(); }
function linePrice(l) { const i = items.find(i => i.id === l.id); return (i?.price || 0) + Object.values(l.choices || {}).filter(x => String(x).endsWith('(+$1)')).length * 100; }
function totals() {
  const subtotal = bag.reduce((n, l) => n + linePrice(l) * l.quantity, 0);
  const tax = Math.floor((subtotal * config.settings.tax_bps + 5000) / 10000);
  return { subtotal, tax, total: subtotal + tax };
}
function addLine(i, quantity = 1, choices = {}) {
  const line = bag.find(l => l.id === i.id && JSON.stringify(l.choices) === JSON.stringify(choices));
  if (line && line.quantity + quantity > 20) { toast('Maximum 20 of each item.'); return false; }
  if (line) line.quantity += quantity; else bag.push({ id: i.id, quantity, choices });
  persistBag();
  const b = $('#open-bag'); b.classList.remove('bump'); void b.offsetWidth; b.classList.add('bump');
  toast(`${i.name} added`, '<button type="button" class="toast-action" data-open-bag>View order</button>');
  return true;
}
function totalHTML() {
  const t = totals();
  return `<div class="totals">${t.tax ? `<div class="total-line"><span>Subtotal</span><span>${money(t.subtotal)}</span></div><div class="total-line"><span>Tax</span><span>${money(t.tax)}</span></div>` : ''}<div class="total-line total"><span>Total</span><span>${money(t.total)}</span></div></div>`;
}
function bagHTML() {
  if (!bag.length) return '<div class="empty-bag"><p>Your order is empty.</p><p class="help">Add a few dishes from the menu to get started.</p></div>';
  return '<ul class="line-items">' + bag.map((l, n) => {
    const i = items.find(i => i.id === l.id), choices = Object.values(l.choices || {});
    return `<li class="line-item">${i.image ? `<img src="${dishPhoto(i)}" alt="" loading="lazy">` : ''}<div class="line-body"><h3>${esc(i.name)}</h3>${choices.length ? `<p>${choices.map(esc).join(' · ')}</p>` : ''}<div class="quantity"><button type="button" data-quantity="${n}" data-delta="-1" aria-label="${l.quantity === 1 ? 'Remove' : 'Remove one'} ${esc(i.name)}">${l.quantity === 1 ? '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14M10 7V5h4v2m-7 0 1 12h8l1-12"/></svg>' : '−'}</button><span aria-label="Quantity">${l.quantity}</span><button type="button" data-quantity="${n}" data-delta="1" aria-label="Add one ${esc(i.name)}" ${l.quantity >= 20 ? 'disabled' : ''}>+</button></div></div><span class="line-price">${money(linePrice(l) * l.quantity)}</span></li>`;
  }).join('') + '</ul>';
}
function openBag() {
  $('#bag-content').innerHTML = `<div class="drawer-body">${pickupNote()}${bagHTML()}</div><div class="drawer-foot">${bag.length ? totalHTML() + `<a class="button primary block" href="/checkout"><span>Checkout</span><span>${money(totals().total)}</span></a>` : `<a class="button primary block" href="/menu">Browse the menu ${arrow}</a>`}</div>`;
  if (!$('#bag-dialog').open) $('#bag-dialog').showModal();
}
function pickupNote() { return `<p class="pickup-note"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/></svg><span>Pickup at 1430 Reisterstown Rd · ready in about ${config.settings.pickup_lead} min · pay in store</span></p>`; }
function updateOrderSummaries() {
  const count = bagCount(), bar = $('#order-bar');
  if (bar) { bar.hidden = !count; bar.innerHTML = `<span class="order-bar-count">${count}</span><strong>View order</strong><span>${money(totals().total)}</span>`; }
  const side = $('#menu-cart');
  if (side) side.innerHTML = `<h2>Your order</h2>${pickupNote()}${bagHTML()}${bag.length ? totalHTML() + `<a class="button primary block" href="/checkout"><span>Checkout</span><span>${money(totals().total)}</span></a>` : ''}`;
  $$('[data-in-bag]').forEach(el => { const q = bag.filter(l => l.id === el.dataset.inBag).reduce((n, l) => n + l.quantity, 0); el.textContent = q ? q + ' in order' : ''; });
  if ($('#checkout-bag') && bag.length) $('#checkout-bag').innerHTML = bagHTML() + totalHTML();
  if ($('#place-total')) $('#place-total').textContent = money(totals().total);
}

/* ---------- Shared bits ---------- */
function demoNote() { return config.demo ? '<p class="demo-note">Website preview — orders and table requests here are tests and are not sent to the kitchen.</p>' : ''; }
function head(title, kicker = 'Oasis Uzbek Kebab House', description = '') {
  return `<header class="page-head"><h1>${esc(title)}</h1>${description ? `<p class="lede">${esc(description)}</p>` : ''}</header>`;
}
function addButton(i) {
  return `<button class="add-button" type="button" data-add="${i.id}" aria-label="Add ${esc(i.name)} to order" ${i.available ? '' : 'disabled'}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg></button>`;
}
function dishCard(i) {
  return `<article class="dish-card"><button class="dish-photo" type="button" data-item="${i.id}" aria-label="View ${esc(i.name)}"><img src="${dishPhoto(i)}" alt="${esc(i.name)}" loading="lazy"></button><div class="dish-card-body"><div><h3><button type="button" data-item="${i.id}">${esc(i.name)}</button></h3><p>${esc(i.description)}</p></div><div class="dish-card-foot"><span class="price">${money(i.price)}</span>${addButton(i)}</div></div></article>`;
}

/* ---------- Home ---------- */
function home() {
  document.body.classList.add('home');
  const signature = items.filter(i => i.image);
  $('#main').innerHTML = `
  <section class="hero" aria-label="Welcome to Oasis">
    <div class="hero-inner">
      <div class="hero-copy">
        <h1>Oasis Uzbek Kebab House</h1>
        <p class="lede">Halal Uzbek food · Pikesville, MD · Pickup and dine-in</p>
        <div class="hero-actions"><a class="button saffron" href="/menu">Order pickup ${arrow}</a><a class="button ghost" href="/reserve">Reserve a table</a></div>
      </div>
      <figure class="hero-media">
        <video id="hero-video" muted loop playsinline preload="auto" poster="${media('plov.webp')}" aria-label="Samarkand plov being served from the kazan at Oasis"><source src="${media('plov.mp4')}" type="video/mp4"></video>
        <button class="video-toggle" id="video-toggle" type="button" aria-label="Play video"></button>
      </figure>
    </div>
  </section>
  <section class="band band-sand">
    <div class="section">
      <div class="section-heading"><h2>Popular dishes</h2><a class="text-link" href="/menu">Full menu ${arrow}</a></div>
      <div class="dish-grid">${signature.map(dishCard).join('')}</div>
    </div>
  </section>`;
  const video = $('#hero-video'), toggle = $('#video-toggle');
  const update = () => { toggle.setAttribute('aria-label', video.paused ? 'Play video' : 'Pause video'); toggle.innerHTML = video.paused ? '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="m7 4 8 6-8 6Z"/></svg>' : '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M7 4v12M13 4v12"/></svg>'; };
  video.addEventListener('play', update); video.addEventListener('pause', update);
  toggle.addEventListener('click', () => video.paused ? video.play().catch(() => toast('The video is unavailable.')) : video.pause());
  if (!matchMedia('(prefers-reduced-motion: reduce)').matches) video.play().catch(() => {});
  update();
}

/* ---------- Menu ---------- */
const categoryId = c => 'category-' + c.toLowerCase().replace(/[^a-z0-9]+/g, '-');
function menuPage() {
  document.body.classList.add('menu-page');
  const categories = [...new Set(items.map(i => i.category))];
  const closed = !config.settings.accept_orders;
  $('#main').innerHTML = `
  <div class="menu-top"><h1>Menu</h1></div>
  ${closed ? '<p class="notice">Online pickup orders are paused right now. Please call <a href="' + TEL + '">' + PHONE + '</a>.</p>' : ''}
  <div class="menu-tools"><label class="search-field"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6"/><path d="m20 20-4.5-4.5"/></svg><span class="visually-hidden">Search the menu</span><input type="search" id="menu-search" placeholder="Search dishes" autocomplete="off"></label>
  <nav class="category-tabs" aria-label="Menu categories">${categories.map((c, n) => `<a href="#${categoryId(c)}"${n ? '' : ' class="active" aria-current="true"'}>${esc(c)}</a>`).join('')}</nav></div>
  <div class="ordering-layout"><div class="ordering-main">${demoNote()}<div id="menu-grid"></div><p class="menu-footnote">Please tell us about any allergies before ordering. Prices and availability are confirmed by the restaurant.</p></div><aside class="menu-cart" id="menu-cart" aria-label="Your order"></aside></div>
  <button class="order-bar" id="order-bar" type="button" hidden></button>`;
  drawMenu(); updateOrderSummaries();
  $('#menu-search').addEventListener('input', e => { search = e.target.value; drawMenu(); });
  $('#order-bar').addEventListener('click', openBag);
  $('.category-tabs').addEventListener('click', e => {
    const a = e.target.closest('a'); if (!a) return;
    if (search) { search = ''; $('#menu-search').value = ''; drawMenu(); }
    setActiveTab(a.hash.slice(1));
  });
  const selected = new URLSearchParams(location.search).get('item');
  if (selected) showItem(selected);
}
function setActiveTab(id) {
  $$('.category-tabs a').forEach(a => {
    const active = a.hash === '#' + id;
    a.classList.toggle('active', active);
    if (active) { a.setAttribute('aria-current', 'true'); a.scrollIntoView({ block: 'nearest', inline: 'nearest' }); } else a.removeAttribute('aria-current');
  });
}
function menuRow(i) {
  return `<article class="menu-row${i.available ? '' : ' unavailable'}"><button class="menu-row-main" type="button" data-item="${i.id}"><span class="menu-row-text"><span class="menu-row-name">${esc(i.name)}</span>${i.description ? `<span class="dish-description">${esc(i.description)}</span>` : ''}<span class="menu-row-meta"><span class="price">${i.available ? money(i.price) : 'Unavailable'}</span>${i.options.length ? '<span class="choice-tag">Choices</span>' : ''}<span class="in-bag" data-in-bag="${i.id}"></span></span></span>${i.image ? `<img src="${dishPhoto(i)}" alt="" loading="lazy">` : ''}</button>${addButton(i)}</article>`;
}
function drawMenu() {
  const q = search.trim().toLowerCase();
  const shown = items.filter(i => (i.name + ' ' + i.description + ' ' + i.category).toLowerCase().includes(q));
  const categories = [...new Set(shown.map(i => i.category))];
  $('#menu-grid').innerHTML = shown.length
    ? categories.map(c => `<section class="menu-category" id="${categoryId(c)}"><h2>${esc(c)}</h2><div class="menu-list">${shown.filter(i => i.category === c).map(menuRow).join('')}</div></section>`).join('')
    : `<p class="empty" role="status">No dishes match “${esc(search)}”.</p>`;
  updateOrderSummaries();
  menuObserver?.disconnect();
  menuObserver = new IntersectionObserver(entries => { const hit = entries.find(e => e.isIntersecting); if (hit) setActiveTab(hit.target.id); }, { rootMargin: '-160px 0px -65% 0px' });
  $$('.menu-category').forEach(s => menuObserver.observe(s));
}
function quickAdd(id) {
  const i = items.find(i => i.id === id);
  if (!i || !i.available) return;
  if (i.options.length) showItem(id); else addLine(i);
}
function showItem(id) {
  const i = items.find(i => i.id === id); if (!i) return;
  $('#item-content').innerHTML = `${i.image ? `<img class="dialog-image" src="${dishPhoto(i)}" alt="${esc(i.name)}">` : ''}<form id="add-item"><div class="dialog-body"><p class="eyebrow">${esc(i.category)}</p><h2 id="item-title">${esc(i.name)}</h2>${i.description ? `<p>${esc(i.description)}</p>` : ''}<p class="price">${money(i.price)}</p>${i.options.map((o, n) => `<fieldset class="item-options"><legend>${esc(o.label)} <span>Required</span></legend>${o.values.map(v => `<label class="option-row"><input type="radio" name="option-${n}" value="${esc(v)}" required><span>${esc(v.replace(' (+$1)', ''))}</span>${v.endsWith('(+$1)') ? '<span class="option-extra">+$1.00</span>' : ''}</label>`).join('')}</fieldset>`).join('')}<p class="help">Allergies or special requests? Add them at checkout.</p></div><div class="item-purchase"><div class="item-quantity"><button type="button" id="item-minus" aria-label="Decrease quantity">−</button><output id="item-qty" aria-live="polite">1</output><button type="button" id="item-plus" aria-label="Increase quantity">+</button></div><button class="button primary" type="submit" ${i.available ? '' : 'disabled'}><span>${i.available ? 'Add to order' : 'Unavailable'}</span><span id="item-total">${money(i.price)}</span></button></div></form>`;
  let quantity = 1; const form = $('#add-item');
  function recalc() {
    const f = new FormData(form), extra = i.options.filter((o, n) => String(f.get('option-' + n)).endsWith('(+$1)')).length * 100;
    $('#item-total').textContent = money((i.price + extra) * quantity); $('#item-qty').textContent = quantity;
    $('#item-minus').disabled = quantity <= 1; $('#item-plus').disabled = quantity >= 20;
  }
  $('#item-minus').addEventListener('click', () => { quantity = Math.max(1, quantity - 1); recalc(); });
  $('#item-plus').addEventListener('click', () => { quantity = Math.min(20, quantity + 1); recalc(); });
  form.addEventListener('change', recalc); recalc();
  form.addEventListener('submit', e => {
    e.preventDefault();
    const f = new FormData(form), choices = Object.fromEntries(i.options.map((o, n) => [o.label, f.get('option-' + n)]));
    if (addLine(i, quantity, choices)) $('#item-dialog').close();
  });
  $('#item-dialog').showModal();
}

/* ---------- Gallery & visit ---------- */
function gallery() {
  $('#main').innerHTML = head('Gallery', 'Food, place & tradition') + `<div class="page-content"><div class="gallery-grid">${galleries.map(([img, label], n) => `<button class="gallery-tile" type="button" data-photo="${n}" aria-label="View photo: ${esc(label)}"><img src="${media(img)}" alt="${esc(label)}" loading="lazy"><span>${esc(label)}</span></button>`).join('')}</div><p class="gallery-credit">Photos from <a href="https://www.instagram.com/oasiskebabhouse/" target="_blank" rel="noreferrer">@oasiskebabhouse</a>. The Samarkand image celebrates our roots in Uzbekistan.</p></div>`;
}
function photo(n) {
  const [img, label, post] = galleries[n];
  $('#photo-content').innerHTML = `<img src="${media(img)}" alt="${esc(label)}"><div class="photo-caption"><h2>${esc(label)}</h2><a href="https://www.instagram.com/p/${post}/" target="_blank" rel="noreferrer">View on Instagram</a></div>`;
  $('#photo-dialog').showModal();
}
function visit() {
  $('#main').innerHTML = head('Hours & directions', 'Visit Oasis') + `<div class="page-content split-page">
  <div class="feature-photo"><img src="${media('entrance.webp')}" alt="The Oasis entrance"></div>
  <div class="visit-panel">
    <div class="visit-block"><h2>Find us</h2><p>1430 Reisterstown Rd<br>Pikesville, MD 21208</p><div class="hero-actions"><a class="button primary" href="${maps}" target="_blank" rel="noreferrer">Get directions ${arrow}</a><a class="button" href="${TEL}">Call ${PHONE}</a></div></div>
    <div class="visit-block"><h2>Opening hours</h2><p class="visit-status">${esc(openState().text)}</p>${hoursRows()}<p class="help">Call ahead for holiday hours.</p></div>
  </div></div>`;
}

/* ---------- Booking forms ---------- */
function savedContact() { try { return JSON.parse(localStorage.getItem('oasis-contact') || 'null'); } catch { return null; } }
function contactFields() {
  const c = savedContact() || {};
  return `<label class="full">Name<input name="name" autocomplete="name" maxlength="100" required value="${esc(c.name)}"></label><label>Phone<input type="tel" name="phone" autocomplete="tel" maxlength="30" required value="${esc(c.phone)}"></label><label>Email<input type="email" name="email" autocomplete="email" maxlength="254" required value="${esc(c.email)}"></label><label class="check-label full"><input type="checkbox" name="remember" ${c.name ? 'checked' : ''}> Remember my details on this device</label>`;
}
function isoDay(date) { return date.toISOString().slice(0, 10); }
function openDays() {
  // Dates the restaurant is open within the booking window, in restaurant-local terms.
  const out = [], start = new Date(config.today + 'T12:00:00Z');
  for (let n = 0; n <= config.settings.advance_days; n++) {
    const d = new Date(start); d.setUTCDate(d.getUTCDate() + n);
    const iso = isoDay(d), weekday = (d.getUTCDay() + 6) % 7;
    if (!config.settings.hours[weekday] || config.settings.closures.includes(iso)) continue;
    out.push({ iso, top: n === 0 ? 'Today' : n === 1 ? 'Tomorrow' : d.toLocaleDateString('en-US', { weekday: 'short', timeZone: 'UTC' }), bottom: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' }) });
  }
  return out;
}
function dateChips() {
  return `<fieldset class="chip-field full"><legend>Day</legend><div class="chips date-chips">${openDays().map((d, n) => `<label class="chip"><input type="radio" name="date" value="${d.iso}" ${n ? '' : 'checked'} required><span><strong>${d.top}</strong><small>${d.bottom}</small></span></label>`).join('')}</div></fieldset>`;
}
const chosenDate = () => $('input[name=date]:checked')?.value;
const chosenGuests = () => Number($('input[name=guests]:checked')?.value || 2);
async function loadSlots(reserve, auto = false) {
  const date = chosenDate(), guests = chosenGuests(), box = $('#time-box'), help = $('#slot-help');
  if (!date) { box.innerHTML = ''; help.textContent = 'No days are available to book right now.'; return; }
  box.setAttribute('aria-busy', 'true');
  try {
    const result = await api(`/api/slots?kind=${reserve ? 'reservation' : 'pickup'}&date=${encodeURIComponent(date)}&guests=${guests}`);
    if (chosenDate() !== date || chosenGuests() !== guests) return;
    if (!result.slots.length) {
      // On first load, skip ahead to the next day that still has times.
      const next = auto && $('input[name=date]:checked')?.closest('.chip')?.nextElementSibling?.querySelector('input');
      if (next) { next.checked = true; return loadSlots(reserve, true); }
      box.innerHTML = ''; help.textContent = 'No times left on this day — please choose another.'; return;
    }
    box.innerHTML = reserve
      ? `<div class="chips time-chips">${result.slots.map(s => `<label class="chip"><input type="radio" name="time" value="${s.value}" required><span>${esc(s.label)}</span></label>`).join('')}</div>`
      : `<label class="visually-hidden" for="time">Pickup time</label><select id="time" name="time" required>${result.slots.map((s, n) => `<option value="${s.value}">${n ? '' : 'Earliest · '}${esc(s.label)}</option>`).join('')}</select>`;
    help.textContent = 'Times are Eastern Time.';
  } catch (e) { help.textContent = e.message; }
  finally { box.removeAttribute('aria-busy'); }
}
function reservation() {
  const max = config.settings.max_party;
  $('#main').innerHTML = head('Reserve a table') + `<div class="page-content">${demoNote()}<div class="booking-layout">
  <form class="form-card" id="request-form" novalidate>
    ${config.settings.accept_reservations ? '' : `<p class="notice">Online table requests are paused. Please call <a href="${TEL}">${PHONE}</a>.</p>`}
    <div class="form-step"><h2><span>1</span>Party size</h2><div class="chips guest-chips">${Array.from({ length: max }, (_, n) => `<label class="chip"><input type="radio" name="guests" value="${n + 1}" ${n === 1 ? 'checked' : ''}><span>${n + 1}</span></label>`).join('')}</div><p class="help">More than ${max} guests? Call <a href="${TEL}">${PHONE}</a>.</p></div>
    <div class="form-step"><h2><span>2</span>Day &amp; time</h2><div class="form-grid">${dateChips()}<fieldset class="chip-field full"><legend>Time</legend><div id="time-box"></div></fieldset><p class="help full" id="slot-help" aria-live="polite"></p></div></div>
    <div class="form-step"><h2><span>3</span>Your details</h2><div class="form-grid">${contactFields()}<label class="full">Anything we should know? <span class="help">Optional</span><textarea name="notes" maxlength="1000" placeholder="A special occasion, high chair or accessibility needs"></textarea></label></div></div>
    <p class="form-error" role="alert" id="form-error"></p>
    <button class="button primary block" type="submit">Request table ${arrow}</button>
    <p class="help">Your table is held once the restaurant confirms. <a href="/privacy">Privacy</a></p>
  </form>
  </div></div>`;
  wireRequest(true);
}
function checkout() {
  if (!bag.length) {
    $('#main').innerHTML = head('Your order is empty', 'Pickup') + `<div class="page-content"><a class="button primary" href="/menu">Browse the menu ${arrow}</a></div>`;
    return;
  }
  $('#main').innerHTML = head('Checkout', 'Pickup · pay in store') + `<div class="page-content">${demoNote()}<div class="checkout-layout">
  <form class="form-card" id="request-form" novalidate>
    ${config.settings.accept_orders ? '' : `<p class="notice">Online pickup orders are paused. Please call <a href="${TEL}">${PHONE}</a>.</p>`}
    <div class="form-step"><h2><span>1</span>Pickup time</h2><div class="form-grid">${dateChips()}<fieldset class="chip-field full"><legend>Time</legend><div id="time-box"></div></fieldset><p class="help full" id="slot-help" aria-live="polite"></p></div></div>
    <div class="form-step"><h2><span>2</span>Your details</h2><div class="form-grid">${contactFields()}<label class="full">Order notes <span class="help">Optional</span><textarea name="notes" maxlength="1000" placeholder="Allergies or special requests"></textarea></label></div></div>
    <p class="form-error" role="alert" id="form-error"></p>
    <button class="button primary block" type="submit"><span>${config.demo ? 'Place test order' : 'Place order'}</span><span id="place-total">${money(totals().total)}</span></button>
    <p class="help">No online payment — pay at the counter. We’ll email you when the restaurant confirms. <a href="/privacy">Privacy</a></p>
  </form>
  <aside class="panel order-summary"><div class="summary-head"><h2>Your order</h2><a class="text-link" href="/menu">Add items</a></div>${pickupNote()}<div id="checkout-bag">${bagHTML()}${totalHTML()}</div></aside>
  </div></div>`;
  wireRequest(false);
}
function wireRequest(reserve) {
  loadSlots(reserve, true);
  const form = $('#request-form');
  form.addEventListener('change', e => { if (e.target.name === 'date' || e.target.name === 'guests') loadSlots(reserve); });
  let key = crypto.randomUUID();
  form.addEventListener('input', () => { key = crypto.randomUUID(); });
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const button = $('button[type=submit]', form), error = $('#form-error');
    error.textContent = '';
    const invalid = $$('input,select,textarea', form).find(el => !el.checkValidity());
    if (invalid) {
      error.textContent = invalid.name === 'time' ? 'Please choose a time.' : invalid.name === 'email' ? 'Please enter a valid email address.' : `Please complete ${invalid.closest('label')?.firstChild?.textContent?.trim().toLowerCase() || 'the form'}.`;
      invalid.focus(); return;
    }
    button.disabled = true;
    const data = Object.fromEntries(new FormData(form));
    const remember = data.remember === 'on'; delete data.remember;
    try { if (remember) localStorage.setItem('oasis-contact', JSON.stringify({ name: data.name, email: data.email, phone: data.phone })); else localStorage.removeItem('oasis-contact'); } catch {}
    data.request_key = key;
    if (reserve) data.guests = Number(data.guests); else data.items = bag;
    try {
      const result = await api(reserve ? '/api/reservations' : '/api/orders', { method: 'POST', body: JSON.stringify(data) });
      if (!reserve) { bag = []; persistBag(); }
      location.href = (reserve ? '/reservation/' : '/order/') + result.token;
    } catch (err) { error.textContent = err.message; button.disabled = false; loadSlots(reserve); }
  });
}

/* ---------- Status ---------- */
function niceTime(t) { return new Intl.DateTimeFormat('en-US', { dateStyle: 'full', timeStyle: 'short', timeZone: 'America/New_York' }).format(new Date(t)); }
async function statusPage() {
  clearTimeout(statusTimer);
  const [, kind, token] = location.pathname.split('/');
  try {
    const r = await api(`/api/status/${kind}/${encodeURIComponent(token)}`);
    const words = {
      received: ['Order received', 'We’ll update this page as soon as the restaurant confirms.'], accepted: ['Pickup confirmed', 'Your order is confirmed. Pay at the counter when you collect.'],
      preparing: ['In the kitchen', 'Your order is being prepared.'], ready: ['Ready for pickup', 'Your food is ready. See you soon.'], collected: ['Thank you', 'We hope you enjoyed your meal.'],
      requested: ['Request received', 'Your table is held once the restaurant confirms.'], confirmed: ['Your table is confirmed', 'We look forward to welcoming you.'],
      seated: ['Welcome to Oasis', 'Enjoy your time at our table.'], declined: ['Request declined', 'Please call the restaurant for help.'], cancelled: ['Reservation cancelled', 'Please call the restaurant if you need help.'],
    };
    const steps = kind === 'order' ? [['received', 'Received'], ['accepted', 'Confirmed'], ['preparing', 'Preparing'], ['ready', 'Ready'], ['collected', 'Collected']] : [['requested', 'Requested'], ['confirmed', 'Confirmed'], ['seated', 'Seated']];
    const at = steps.findIndex(s => s[0] === r.status), stopped = at < 0;
    const [title, description] = words[r.status] || ['An update from Oasis', ''];
    $('#main').innerHTML = `<div class="page-content status-wrap"><article class="panel status-card">${demoNote()}<p class="eyebrow">${kind === 'order' ? 'Pickup order' : 'Table request'}</p><h1>${title}</h1><p>${description}</p>
      ${stopped ? `<span class="status-pill stopped">${esc(r.status)}</span>` : `<ol class="progress">${steps.map(([, label], n) => `<li class="${n < at ? 'done' : n === at ? 'current' : ''}"${n === at ? ' aria-current="step"' : ''}><span></span>${label}</li>`).join('')}</ol>`}
      <div class="status-when"><span>${kind === 'order' ? 'Pickup' : 'Table'}</span><strong>${niceTime(r.data.time)}</strong>${r.data.guests ? `<span>${r.data.guests} ${r.data.guests === 1 ? 'guest' : 'guests'}</span>` : ''}</div>
      ${r.data.update_note ? `<p class="notice">${esc(r.data.update_note)}</p>` : ''}
      ${r.data.items ? '<ul class="line-items">' + r.data.items.map(i => `<li class="line-item"><div class="line-body"><h3>${i.quantity} × ${esc(i.name)}</h3>${Object.values(i.choices).length ? `<p>${Object.values(i.choices).map(esc).join(' · ')}</p>` : ''}</div><span class="line-price">${money(i.price * i.quantity)}</span></li>`).join('') + `</ul><div class="total-line total"><span>Total · pay in store</span><span>${money(r.data.total)}</span></div>` : ''}
      <div class="status-place"><p>Oasis Uzbek Kebab House<br>1430 Reisterstown Rd, Pikesville, MD 21208</p><div class="hero-actions"><a class="button small" href="${maps}" target="_blank" rel="noreferrer">Directions</a><a class="button small" href="${TEL}">Call ${PHONE}</a></div></div>
      <p class="help">Bookmark this page to check for updates. It refreshes automatically.${config.email_delivery ? ' Updates are also emailed.' : ''}</p></article></div>`;
    const final = ['collected', 'seated', 'declined', 'cancelled'].includes(r.status);
    if (!final) statusTimer = setTimeout(statusPage, 30000);
  } catch (e) { $('#main').innerHTML = head('Request not found') + `<div class="page-content"><p>${esc(e.message)}</p></div>`; }
}
function privacy() {
  $('#main').innerHTML = head('Your privacy') + `<div class="page-content text-page"><p>This is an X Solutions demonstration website for Oasis Uzbek Kebab House. Test requests are not restaurant orders or confirmed bookings.</p><h2>Information you provide</h2><p>Pickup and table requests store your name, email, phone number, chosen time, dishes and any notes. Authorized administrators and employees can see and update these details to manage requests. Avoid entering sensitive information in notes.</p><h2>Admin access and email</h2><p>Admin sign-in uses Google to verify an invited email address. An administrator can separately connect a Google account to send confirmations through Gmail. Connecting a sender does not give that account admin access.</p><h2>Storage</h2><p>Your order is saved in this browser. If you choose “Remember my details”, your name, email and phone are also saved in this browser only; untick it on your next request to remove them. Essential session cookies support sign-in and protect forms. Request records are stored on the application server. This site does not collect payment card information and does not include advertising trackers.</p><h2>Questions or deletion</h2><p>For questions about this demo or to request removal of submitted information, contact <a href="https://xsolutionsmd.com">X Solutions</a>. For restaurant questions, call <a href="${TEL}">${PHONE}</a>.</p></div>`;
}

/* ---------- Global events ---------- */
document.addEventListener('click', e => {
  const close = e.target.closest('[data-close]'); if (close) close.closest('dialog').close();
  if (e.target.closest('[data-open-bag]')) { $('#toast').classList.remove('visible'); openBag(); }
  const add = e.target.closest('[data-add]'); if (add) { quickAdd(add.dataset.add); return; }
  const item = e.target.closest('[data-item]'); if (item) showItem(item.dataset.item);
  const p = e.target.closest('[data-photo]'); if (p) photo(Number(p.dataset.photo));
  const q = e.target.closest('[data-quantity]');
  if (q) {
    const n = Number(q.dataset.quantity);
    bag[n].quantity += Number(q.dataset.delta);
    if (bag[n].quantity < 1) bag.splice(n, 1);
    persistBag();
    if ($('#bag-dialog').open) openBag();
    if (location.pathname === '/checkout' && !bag.length) checkout();
  }
});
$$('dialog').forEach(d => d.addEventListener('click', e => {
  if (e.target !== d) return;
  const r = d.getBoundingClientRect();
  if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) d.close();
}));
$('#open-bag').addEventListener('click', openBag);
$('#open-nav').addEventListener('click', () => $('#nav-dialog').showModal());
$('#year').textContent = new Date().getFullYear();
$$('.main-nav a, #nav-dialog nav a').forEach(a => { if (a.pathname === location.pathname) a.setAttribute('aria-current', 'page'); });

async function init() {
  try {
    config = await api('/api/config');
    items = (await api('/api/menu')).items;
    validBag();
    const path = location.pathname;
    if (path.startsWith('/admin')) {
      document.body.classList.add('admin-page');
      const s = document.createElement('script'); s.src = '/static/admin.js'; document.head.append(s);
      return;
    }
    renderChrome();
    const pages = { '/': home, '/menu': menuPage, '/gallery': gallery, '/visit': visit, '/reserve': reservation, '/checkout': checkout, '/privacy': privacy };
    if (pages[path]) pages[path]();
    else if (/^\/(order|reservation)\//.test(path)) statusPage();
  } catch (e) {
    $('#main').innerHTML = `<div class="page-content"><h1>We’ll be right back.</h1><p>${esc(e.message)}</p><a class="button" href="/">Try again</a></div>`;
  }
}
init();
