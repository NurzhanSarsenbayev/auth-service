# JWT RSA keys (local only)

This folder is **ignored by git**. Store private/public RSA keys here.

Expected files:
- jwtRS256.key
- jwtRS256.key.pub

Generate:
```bash
openssl genrsa -out jwtRS256.key 2048
openssl rsa -in jwtRS256.key -pubout -out jwtRS256.key.pub