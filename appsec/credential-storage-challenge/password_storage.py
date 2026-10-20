"""
Credential storage layer.

Stores password records in users.txt using Argon2id.
Parameters were chosen by benchmarking on the development machine:
    m = 262144 KiB (256 MiB), t = 3, p = 1  ->  0.671 s per hash
"""

import json
import os
import time
import unicodedata

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

USERS_FILE = "users.txt"

# Upper bound on accepted password length, in characters.
# Well above the 10,000-character case the specification requires to work,
# but low enough that a single request cannot exhaust memory.
MAX_PASSWORD_LENGTH = 100_000

ph = PasswordHasher(
    memory_cost=262144,   # 256 MiB per hash
    time_cost=3,          # passes over memory
    parallelism=1,        # single lane
    hash_len=32,          # output length in bytes
    salt_len=16,          # random salt per record
)

# Built once, on first use, so an unknown username costs the same as a known one.
_dummy_hash = None


def _dummy():
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = ph.hash(b"dummy-password-for-constant-time-behaviour")
    return _dummy_hash


def _encode(text):
    """Normalise to NFC, then encode as UTF-8 bytes.

    Normalisation makes the two possible encodings of a character such as
    'a' collapse to one form, so a password registered on one platform
    still verifies on another. Nothing is stripped or trimmed: the value
    is otherwise passed through byte for byte.
    """
    return unicodedata.normalize("NFC", text).encode("utf-8")


def _normalise_username(username):
    return unicodedata.normalize("NFC", username)


def _load_records():
    """Return {username: hash}. An absent or unreadable file yields {}."""
    records = {}
    if not os.path.exists(USERS_FILE):
        return records

    with open(USERS_FILE, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records[record["username"]] = record["hash"]
            except (json.JSONDecodeError, KeyError, TypeError):
                continue  # skip a corrupted line rather than crash
    return records


def register(username, password):
    """Store a credential record. Returns True on success, False otherwise."""
    if not isinstance(username, str) or not isinstance(password, str):
        return False
    if username == "":
        return False
    if len(password) > MAX_PASSWORD_LENGTH:
        return False

    username = _normalise_username(username)

    if username in _load_records():
        return False  # username already taken

    digest = ph.hash(_encode(password))

    record = {"username": username, "hash": digest}

    # ensure_ascii=False keeps non-ASCII usernames readable in the file;
    # json.dumps still escapes newlines and control characters, so a single
    # record can never span more than one line.
    with open(USERS_FILE, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    return True


def verify(username, password):
    """Return True if the credentials match a stored record, else False."""
    if not isinstance(username, str) or not isinstance(password, str):
        return False

    if len(password) > MAX_PASSWORD_LENGTH:
        # Too long to be a credential we ever stored. Still burn the same
        # work as a real check so the response time reveals nothing.
        try:
            ph.verify(_dummy(), b"")
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            pass
        return False

    username = _normalise_username(username)
    stored = _load_records().get(username)
    encoded = _encode(password)

    if stored is None:
        # Unknown username: verify against a throwaway hash so that the
        # time taken does not disclose whether the account exists.
        try:
            ph.verify(_dummy(), encoded)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            pass
        return False

    try:
        return ph.verify(stored, encoded)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# --------------------------------------------------------------------------
# Test block
# --------------------------------------------------------------------------

ACCOUNTS = [
    ("alice", "123456"),
    ("bob", "iloveyou"),
    ("carol", "P@ssw0rd"),
    ("dave", "Summer2025!"),
    ("erin", "monkey123"),
    ("frank", "Ahmad1998"),
    ("grace", "correct-horse-battery-staple"),
    ("heidi", "velvet-anchor-glacier-7"),
    ("ivan", "xK9#mQ2vLp4$wRt7"),
    ("judy", "T\u00e2riq&M\u00f6tley_42"),
]


_results = []


def _report(label, action, expected):
    """Run action, time it, and print the outcome alongside the elapsed time."""
    start = time.perf_counter()
    actual = action()
    elapsed_ms = (time.perf_counter() - start) * 1000

    passed = actual == expected
    _results.append(passed)

    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {elapsed_ms:7.1f} ms  {label:<38} -> {actual}")


SCRATCH_FILE = "scratch_tests.txt"


def main():
    global USERS_FILE

    if os.path.exists(USERS_FILE):
        os.remove(USERS_FILE)

    # Build the dummy hash up front. It is created lazily on first use, and
    # that first use would otherwise land inside a timed check and double its
    # reading. In a real service the process is long-lived, so this cost is
    # paid once at startup rather than on a user's request.
    _dummy()

    print("Registering the ten assigned accounts...")
    for name, secret in ACCOUNTS:
        register(name, secret)
    print(f"Done. {USERS_FILE} contains exactly these ten accounts.\n")

    print("Checks against users.txt:")
    _report("correct username, correct password",
            lambda: verify("alice", "123456"), True)
    _report("correct username, wrong password",
            lambda: verify("alice", "wrong"), False)
    _report("username never registered",
            lambda: verify("mallory", "123456"), False)

    # The same visible text as judy's password, in decomposed form.
    decomposed = unicodedata.normalize("NFD", "T\u00e2riq&M\u00f6tley_42")
    _report("decomposed form still verifies",
            lambda: verify("judy", decomposed), True)
    _report("duplicate registration refused",
            lambda: register("alice", "anything"), False)

    print("\n  Note: the wrong-password and unknown-username rows above should")
    print("  take the same time. That is the dummy hash doing its job: response")
    print("  time does not reveal whether an account exists.")

    # The remaining cases need throwaway accounts. Point the module at a
    # scratch file so users.txt is left holding the ten assigned accounts
    # and nothing else, exactly as the specification requires.
    USERS_FILE = SCRATCH_FILE
    if os.path.exists(SCRATCH_FILE):
        os.remove(SCRATCH_FILE)

    try:
        print("\nEdge cases (scratch file):")

        register("empty_pw_user", "")
        _report("empty password, correct",
                lambda: verify("empty_pw_user", ""), True)
        _report("empty password, wrong",
                lambda: verify("empty_pw_user", "x"), False)

        long_password = "a" * 10_000
        register("long_pw_user", long_password)
        _report("10,000-character password",
                lambda: verify("long_pw_user", long_password), True)
        _report("10,000-char, one char off",
                lambda: verify("long_pw_user", "a" * 9_999), False)

        awkward = "line1\nline2\x00null\u00e9\u4f60\u597d"
        register("awkward_user", awkward)
        _report("newlines, null bytes, non-ASCII",
                lambda: verify("awkward_user", awkward), True)

        _report("password containing a colon",
                lambda: register("colon_user", "a:b:c"), True)
        _report("colon password verifies",
                lambda: verify("colon_user", "a:b:c"), True)
    finally:
        USERS_FILE = "users.txt"
        if os.path.exists(SCRATCH_FILE):
            os.remove(SCRATCH_FILE)

    passed = sum(_results)
    total = len(_results)
    print(f"\n{passed}/{total} checks passed.")
    print(f"Scratch file removed. {USERS_FILE} holds the ten assigned accounts.")


if __name__ == "__main__":
    main()
