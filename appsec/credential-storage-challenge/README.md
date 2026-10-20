# Credential Storage Challenge

A secure password-storage layer built for the Application Security module. Passwords are stored with Argon2id, with care taken over timing side-channels, Unicode handling, and parameter choice.

**Run:** `python password_storage.py`
**Dependency:** `argon2-cffi==25.1.0` (see `requirements.txt`)

## Files
- `password_storage.py` — the storage layer (`register`, `verify`) plus a self-test block.
- `users.txt` — the credential file, one JSON record per line (test accounts).
- `requirements.txt` — the single dependency.

## Design justification

**01 Which algorithm, and why over the alternatives?**
Argon2id was chosen because its high memory cost prevents GPUs from executing thousands of simultaneous cracking attempts. The "id" variant provides both side-channel and GPU resistance. The alternatives fall short: bcrypt requires too little memory, scrypt resists time-memory tradeoffs less well, and PBKDF2 uses no memory at all and is chosen for FIPS compliance rather than strength.

**02 What parameters, and how were they chosen?**
`m = 262144 KiB (256 MiB)`, `t = 3`, `p = 1`, `hash_len = 32`, `salt_len = 16`. Seven combinations were benchmarked on the development machine, three runs each after a warm-up, and the heaviest configuration that held a login inside 0.5 to 1.0 seconds was selected. Beyond that the delay becomes noticeable and the memory per request risks taking the server down under concurrent logins. `p = 1` matches a login path that serves one request per thread. `hash_len = 32` yields a 256-bit output and `salt_len = 16` yields the 128 random bits per record that RFC 9106 recommends.

**03 What is in `users.txt` besides the hash?**
The username, and nothing else. The Argon2 string already carries the algorithm, version, parameters and salt. Each record is one JSON object per line, written and read as explicit UTF-8, so an unusual character in a name cannot corrupt the file or spill a record across two lines.

**04 What does an attacker gain from the file?**
Usernames, salts, and parameters, all of which verification requires anyway, plus the ability to guess offline with no rate limiting. Unique salts still force each account to be attacked on its own. What the design controls is the price of one guess: 0.671 seconds and 256 MiB instead of microseconds.

**05 What would change before production?**
1. A breached-password blocklist that refuses weak passwords at registration.
2. A pepper held in an HSM, so a stolen file is useless without a key outside the database.
3. A real database: `users.txt` has no locking, so concurrent registrations interleave and every check rereads the file.

## Security details worth noting
- **Constant-time behaviour:** unknown usernames and over-length passwords are verified against a throwaway dummy hash, so response time never reveals whether an account exists.
- **Unicode safety:** usernames and passwords are normalised to NFC before hashing, so the two encodings of a character verify against each other; nothing is trimmed or stripped.
- **Robust file handling:** a corrupted line is skipped rather than crashing the loader, and control characters are JSON-escaped so one record can never span two lines.
