# postiz-linkedin-patch

Thin wrapper around `ghcr.io/gitroomhq/postiz-app:latest` that strips LinkedIn
organization OAuth scopes from the **personal** LinkedIn provider so individual
profiles can connect without Advertising API / company verification.

LinkedIn Page provider scopes are left unchanged.
