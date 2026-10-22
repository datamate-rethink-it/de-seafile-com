/* Eigener Code der statischen Seite. Wird nie neu erzeugt - anders als
   webroot/, das _build/gen_static.py bei jedem Lauf wegwirft. */
(function () {
	'use strict';

	/* Alte Suchadressen auffangen.
	   Die WordPress-Suche lief unter /?s=begriff; solche Adressen stehen in
	   alten Treffern und Lesezeichen. Auf einer statischen Seite ist die
	   Abfragezeichenkette fuer den Server unsichtbar - die Startseite kaeme
	   ohne Hinweis. Darum hier umleiten. */
	if (window.location.pathname === '/' && window.location.search) {
		var p = new URLSearchParams(window.location.search).get('s');
		if (p) {
			window.location.replace('/suche/?q=' + encodeURIComponent(p));
			return;
		}
	}

	/* Trial-Formular.
	   Angelegt wird der Mandant auf dem Trial-Server; Caddy im Image reicht
	   /api/trial dorthin weiter, der Browser bleibt also bei gleicher
	   Herkunft. Frueher war das ein gewoehnlicher POST auf die Seite
	   selbst, den PHP beantwortet hat. */
	var formular = document.querySelector('#trial-formular');
	if (!formular) {
		return;
	}
	var meldung = document.getElementById('trial-meldung');
	var text = document.getElementById('trial-meldung-text');

	function zeigen(art, inhalt) {
		text.className = 'col-md-6 alert alert-' + art;
		text.innerHTML = inhalt;
		meldung.hidden = false;
		meldung.scrollIntoView({ behavior: 'smooth', block: 'center' });
	}

	formular.addEventListener('submit', function (ereignis) {
		ereignis.preventDefault();
		var knopf = formular.querySelector('[type=submit]');
		knopf.disabled = true;
		fetch('/api/trial', {
			method: 'POST',
			body: new FormData(formular),
			headers: { Accept: 'application/json' }
		})
			.then(function (antwort) {
				return antwort.json().then(function (daten) {
					return { ok: antwort.ok, daten: daten };
				});
			})
			.then(function (ergebnis) {
				if (ergebnis.ok) {
					zeigen('success', ergebnis.daten.meldung);
					formular.hidden = true;
				} else {
					zeigen('danger', (ergebnis.daten.fehler || []).join('<br/>') ||
						'Es ist ein Fehler aufgetreten. Bitte wenden Sie sich an den Support.');
					knopf.disabled = false;
					/* Die Aufgabe ist verbraucht - der Dienst nimmt jede nur
					   einmal an. Ohne das Zuruecksetzen koennte der Besucher
					   es nie wieder versuchen. */
					var widget = document.querySelector('altcha-widget');
					if (widget && typeof widget.reset === 'function') {
						widget.reset();
					}
				}
			})
			.catch(function () {
				zeigen('danger', 'Das Testsystem ist gerade nicht erreichbar. ' +
					'Bitte versuchen Sie es später noch einmal oder schreiben Sie uns an ' +
					'<a href="mailto:seafile@datamate.org">seafile@datamate.org</a>.');
				knopf.disabled = false;
			});
	});
})();
