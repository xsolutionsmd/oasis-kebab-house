'use strict';

// An intentionally local design preview: no storage, availability API, or submission.
(() => {
	const form = document.querySelector('#reservation-form');
	const fields = document.querySelector('#reservation-fields');
	const date = form.elements.date;
	const status = document.querySelector('#reservation-status');
	const review = OasisMotion.dialogController(
		document.querySelector('#reservation-review'),
	);
	const controls = [...form.querySelectorAll('input')];
	const today = () =>
		new Intl.DateTimeFormat('en-CA', {
			timeZone: 'America/New_York',
			year: 'numeric',
			month: '2-digit',
			day: '2-digit',
		}).format(new Date());
	date.min = today();

	function validate(control) {
		let message = '';
		if (!control.value.trim())
			message = `Please enter ${control.name === 'guests' ? 'the number of guests' : control.name === 'name' ? 'your name' : control.name === 'email' ? 'your email address' : control.name === 'phone' ? 'your phone number' : 'a preferred ' + control.name}.`;
		else if (control.name === 'date' && control.validity.rangeUnderflow)
			message = 'Please choose today or a future date.';
		else if (control.name === 'guests' && !control.validity.valid)
			message = 'Please enter a whole number of at least one guest.';
		else if (control.name === 'email' && !control.validity.valid)
			message = 'Please enter an email address, such as name@example.com.';
		else if (
			control.name === 'phone' &&
			control.value.replace(/\D/g, '').length < 7
		)
			message = 'Please enter a phone number with at least seven digits.';
		else if (!control.validity.valid) message = 'Please check this value.';
		document.getElementById(`${control.name}-error`).textContent = message;
		if (message) control.setAttribute('aria-invalid', 'true');
		else control.removeAttribute('aria-invalid');
		return !message;
	}

	controls.forEach((control) =>
		control.addEventListener('input', () => {
			if (control.hasAttribute('aria-invalid')) validate(control);
			status.textContent = '';
		}),
	);
	form.addEventListener('submit', (event) => {
		event.preventDefault();
		date.min = today();
		const invalid = controls.filter((control) => !validate(control));
		if (invalid.length) {
			status.textContent = `Please check ${invalid.length === 1 ? 'the highlighted field' : 'the highlighted fields'} before reviewing your request.`;
			invalid[0].focus();
			return;
		}
		status.textContent = '';
		const value = (name) => form.elements.namedItem(name).value.trim();
		const dateLabel = new Date(`${value('date')}T12:00:00`).toLocaleDateString(
			'en-US',
			{ weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' },
		);
		const timeLabel = new Date(
			`2000-01-01T${value('time')}`,
		).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
		const entries = [
			['Date', dateLabel],
			['Time', `${timeLabel} · preferred`],
			['Guests', value('guests')],
			['Name', value('name')],
			['Email', value('email')],
			['Phone', value('phone')],
		];
		if (value('notes')) entries.push(['Notes', value('notes')]);
		const summary = document.querySelector('#request-summary');
		summary.replaceChildren(
			...entries.map(([label, text]) => {
				const row = document.createElement('div');
				const term = document.createElement('dt');
				const description = document.createElement('dd');
				term.textContent = label;
				description.textContent = text;
				row.append(term, description);
				return row;
			}),
		);
		review.open(form.querySelector('[type="submit"]'));
	});
	fields.disabled = false;
})();
