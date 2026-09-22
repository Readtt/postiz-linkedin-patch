# Patch official Postiz so personal LinkedIn OAuth does not request org scopes.
FROM ghcr.io/gitroomhq/postiz-app:latest

USER root
COPY patch_linkedin_scopes.py /tmp/patch_linkedin_scopes.py
RUN python3 /tmp/patch_linkedin_scopes.py && rm -f /tmp/patch_linkedin_scopes.py
