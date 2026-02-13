# JWT RSA keys (local only)

This folder is **ignored by git**. Store private/public RSA keys here.

Expected files:
- jwtRS256.key
- jwtRS256.key.pub

Generate (run from repo root):
```bash
openssl genrsa -out auth_service/keys/jwtRS256.key 2048
openssl rsa -in auth_service/keys/jwtRS256.key -pubout -out auth_service/keys/jwtRS256.key.pub
```
