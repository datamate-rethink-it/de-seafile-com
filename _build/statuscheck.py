#!/usr/bin/env python3
"""Status + Location jeder Adresse, ohne Weiterleitungen zu folgen.

Aufruf: statuscheck.py [BASIS-URL] [AUSGABEDATEI]

ACHTUNG: status-live.json enthaelt den Stand der frueheren WordPress-Seite und
ist die Vergleichsbasis von verify_status.py. de.seafile.com laeuft inzwischen
auf Hugo, deshalb immer eine eigene AUSGABEDATEI angeben.
"""
import json, pathlib, sys, time, urllib.request, urllib.error

B = pathlib.Path(__file__).resolve().parent
base = sys.argv[1] if len(sys.argv) > 1 else 'https://de.seafile.com'
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else B / 'status-live.json'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **kw): return None

op = urllib.request.build_opener(NoRedirect)
res = {}
routes = [l.strip() for l in (B / 'wp' / 'all-routes.txt').read_text().splitlines() if l.strip()]
for r in routes:
    req = urllib.request.Request(base + r, headers={'User-Agent': 'de-seafile-statuscheck/1'})
    try:
        with op.open(req, timeout=60) as resp:
            res[r] = {'status': resp.status, 'location': resp.headers.get('Location'),
                      'bytes': len(resp.read())}
    except urllib.error.HTTPError as e:
        res[r] = {'status': e.code, 'location': e.headers.get('Location'), 'bytes': len(e.read())}
    except Exception as e:
        res[r] = {'status': None, 'error': str(e)}
    time.sleep(0.1)
out.write_text(json.dumps(res, indent=1, ensure_ascii=False))
print('geschrieben:', out, len(res))
