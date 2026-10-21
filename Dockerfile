# syntax=docker/dockerfile:1
#
# de.seafile.com als ausliefernder Container: Caddy mit der fertig
# gebauten Seite. Kein TLS, kein Hostname - davor steht das native nginx
# des Servers (siehe deploy/nginx-vhost.conf).
#
# Der Build ist in sich geschlossen: ein frischer Clone genuegt, es braucht
# weder den alten WordPress-Dateibestand noch Node. Die Werkzeuge in
# _build/ sind Migrations- und Pruefwerkzeug und nicht Teil des Builds.
#
#   docker build -t de-seafile-com:dev .
#   docker run --rm -p 127.0.0.1:8083:80 de-seafile-com:dev

ARG HUGO_VERSION=0.168.0
ARG PAGEFIND_VERSION=1.4.0
ARG CADDY_VERSION=2.11.7

# ---------------------------------------------------------------- Build
FROM debian:trixie-slim AS builder

ARG HUGO_VERSION
ARG PAGEFIND_VERSION

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

# Hugo Extended als vorgebaute Binaerdatei - die Seite braucht keinen
# SCSS-Compiler, aber es ist dieselbe Fassung, gegen die geprueft wurde.
# Pagefind als eigenstaendige musl-Binaerdatei, damit kein Node ins Bild
# muss (die npm-Fassung laedt genau diese Datei nach).
RUN set -eux; \
    curl -fsSL -o /tmp/hugo.tar.gz \
      "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz"; \
    tar -C /usr/local/bin -xzf /tmp/hugo.tar.gz hugo; \
    curl -fsSL -o /tmp/pagefind.tar.gz \
      "https://github.com/CloudCannon/pagefind/releases/download/v${PAGEFIND_VERSION}/pagefind-v${PAGEFIND_VERSION}-x86_64-unknown-linux-musl.tar.gz"; \
    tar -C /usr/local/bin -xzf /tmp/pagefind.tar.gz; \
    rm /tmp/hugo.tar.gz /tmp/pagefind.tar.gz; \
    hugo version; \
    pagefind --version

WORKDIR /src
COPY . /src

# Kein --minify: das gaebe die Vergleichbarkeit mit dem Schnappschuss auf,
# die _build/verify.py nachweist.
#
# sitemap.xml muss weg: /sitemap.xml ist eine 301 auf /sitemap_index.xml,
# und eine Datei an der Stelle verdeckt die Weiterleitung. Hugo schreibt
# sie trotz [sitemap] disable = true, nur leer.
RUN set -eux; \
    hugo --gc --destination /src/public; \
    rm -f /src/public/sitemap.xml; \
    pagefind --site /src/public; \
    test -f /src/public/index.html; \
    test -f /src/public/support/benutzer/anleitung/seahub/2fa-aktivieren/index.html; \
    test -f /src/public/news/index.html; \
    test -f /src/public/feed/index.xml; \
    test -f /src/public/category/funktionen/index.xml; \
    test -f /src/public/sitemap_index.xml; \
    test -f /src/public/pagefind/pagefind-ui.js; \
    test ! -e /src/public/sitemap.xml; \
    test ! -e /src/public/plugin-integration; \
    test ! -e /src/public/featurelog; \
    test ! -e /src/public/now; \
    cp -al /src/public /src/site; \
    rm -rf /src/site/wp-content/uploads

# ---------------------------------------------------------------- Laufzeit
FROM caddy:${CADDY_VERSION}-alpine

COPY deploy/Caddyfile.container /etc/caddy/Caddyfile
COPY deploy/redirects.caddy /etc/caddy/redirects.caddy

# Zwei Schichten mit Absicht: die Bilder der Beitraege und Seiten aendern
# sich fast nie, der Rest bei jedem Textdurchgang. Ein Inhalts-Release
# uebertraegt dadurch nur den kleinen Teil neu.
COPY --from=builder /src/public/wp-content/uploads /srv/wp-content/uploads
COPY --from=builder /src/site /srv

LABEL org.opencontainers.image.title="de.seafile.com" \
      org.opencontainers.image.description="de.seafile.com als statische Seite (Hugo) mit Caddy" \
      org.opencontainers.image.source="https://github.com/datamate-rethink-it/de-seafile-com" \
      org.opencontainers.image.licenses="UNLICENSED"

EXPOSE 80
