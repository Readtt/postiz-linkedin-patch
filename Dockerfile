# Patch official Postiz: personal LinkedIn scopes + TikTok URL verification file.
FROM ghcr.io/gitroomhq/postiz-app:latest

USER root
COPY patch_linkedin_scopes.py /tmp/patch_linkedin_scopes.py
RUN python3 /tmp/patch_linkedin_scopes.py && rm -f /tmp/patch_linkedin_scopes.py

# TikTok Developers URL Properties signature file (must be at site root)
COPY tiktokdEmM6KkREgMqmnF4QcKvq9zzy3kXlLWk.txt /tmp/tiktok-verify.txt
RUN set -e; \
  for d in \
    /app/apps/frontend/public \
    /app/apps/frontend/.next/static \
    /www \
    /var/www/html \
    /usr/share/nginx/html \
    /app/public; do \
      if [ -d "$d" ]; then cp /tmp/tiktok-verify.txt "$d/tiktokdEmM6KkREgMqmnF4QcKvq9zzy3kXlLWk.txt"; echo "placed in $d"; fi; \
    done; \
  # Also place under /app root for any custom static middleware
  cp /tmp/tiktok-verify.txt /app/tiktokdEmM6KkREgMqmnF4QcKvq9zzy3kXlLWk.txt; \
  # Inject nginx location if nginx.conf exists
  if [ -f /etc/nginx/nginx.conf ]; then \
    grep -q 'tiktokdEmM6KkREgMqmnF4QcKvq9zzy3kXlLWk.txt' /etc/nginx/nginx.conf || \
    sed -i 's|server {|server {\n    location = /tiktokdEmM6KkREgMqmnF4QcKvq9zzy3kXlLWk.txt { root /app; default_type text/plain; }|' /etc/nginx/nginx.conf || true; \
  fi; \
  rm -f /tmp/tiktok-verify.txt

