# Cryptography

Use a vetted library and its high-level API. Never invent a scheme, a mode, a padding or a key derivation.

| Need | Use | Reject |
| --- | --- | --- |
| Password storage | Argon2id (or bcrypt, scrypt, PBKDF2 with a high iteration count where required), per-password salt | MD5, SHA-1, SHA-256 alone, unsalted hashes, reversible encryption |
| Symmetric encryption | AES-256-GCM or ChaCha20-Poly1305 (authenticated), a fresh unique nonce for every message | DES, 3DES, RC4, ECB mode, CBC without a MAC, nonce reuse |
| Public-key signatures | Ed25519, ECDSA P-256, RSA-PSS with 3072 bits or more | RSA PKCS#1 v1.5 for new designs, RSA below 2048, DSA |
| Key exchange | X25519, ECDH P-256, TLS 1.3 | Static Diffie-Hellman with small groups |
| Hashing for integrity | SHA-256, SHA-3, BLAKE2 | MD5, SHA-1 |
| Message authentication | HMAC-SHA-256, or an AEAD mode | Plain hash of key plus message |
| Random values (tokens, keys, nonces, ids) | The OS CSPRNG: `secrets`, `crypto.randomBytes`, `crypto/rand`, `RandomNumberGenerator`, `SecureRandom`, `getrandom` | `Math.random`, `random`, `rand()`, `mt_rand`, time-based seeds |
| Key derivation from a secret | HKDF, Argon2id, scrypt | Home-made stretching |

## Rules
- Keys come from a secret manager or KMS, never from source or a constant. Separate keys per purpose. Support rotation: include a key id with ciphertext.
- Compare secrets and MACs in constant time (`hmac.compare_digest`, `crypto.timingSafeEqual`, `subtle.ConstantTimeCompare`, `hash_equals`).
- Encrypt then authenticate, or use AEAD. Verify before decrypting or parsing. Treat any failure as a hard error with a generic message.
- TLS: certificate and hostname validation on, TLS 1.2 minimum, modern cipher suites, no custom trust-all handlers.
- Do not use encryption as an access-control substitute, and do not log or return key material.
- When you must touch legacy crypto you cannot remove, say so, keep it behind one interface, and flag it for review.
