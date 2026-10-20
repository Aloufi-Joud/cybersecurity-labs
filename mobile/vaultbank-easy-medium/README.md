# VaultBank Mobile Pentest — Easy & Medium Tiers

Mobile application penetration-testing lab from the Cybersecurity Solutions & Analytics Bootcamp (Kaspersky & Tuwaiq Academy). VaultBank is a deliberately vulnerable Android training app; every challenge is a known planted weakness.

**Tools:** apktool, jadx, adb, Frida, CyberChef

## Executive summary
This report covers all ten challenges of the VaultBank lab across the Easy and Medium tiers. The Easy tier exposes secrets that are readable or reachable by anyone who holds the app file or the device. The Medium tier moves into storage, IPC, client logic, crypto and anti-root. The theme is the same throughout: anything shipped inside the app, whether a stored value, an encryption key, or a security decision, is under the attacker's control. Each challenge failed for one reason, it trusted the client.

**Severity spread:** 3 High, 4 Medium, 3 Low.

## Scope and methodology
Target: the VaultBank Android app (APK), tested on an emulator and, for the Medium tier, a rooted emulator. Testing combined static analysis of the decompiled app with dynamic analysis, including logcat capture, run-as, content provider queries and Frida instrumentation.

## Findings
Findings are ordered by severity, highest first.

### E2 · The Key Under the Mat — High
A live payment provider API key is baked into the build. It lands in the generated `BuildConfig` class as the `API_KEY` constant, in plain text. The value starts with `sk_live_`, so it is a real key.

- **Impact:** `buildConfigField` values become plain strings in the compiled DEX. Anyone who extracts the app could use the key against the real payment account.
- **Remediation:** Never hardcode live keys in the app. Route payment calls through a backend that holds the key, and rotate the exposed key immediately.

### M2 · Provider That Overshares — High
`VaultProvider.query` returns the whole table with no filtering and no permission check, and the provider is exported in the manifest with no permission. Any app, or adb, can query it and read every row.

- **Impact:** An exported provider with no permission and no access control lets anyone read the app's database.
- **Remediation:** Set the provider to not exported, or require a signature-level permission, and filter queries so callers only get rows they are authorized to see.

### M3 · Auth on the Wrong Side — High
There is a hidden staff sign-in whose decision is made entirely on the device. `LoginActivity` hardcodes the staff username and password and a `validateLocal` method that just compares input to those constants. The credentials can be read from the code, and the check can be bypassed without them.

- **Impact:** Any authentication decision made on the client can be read or bypassed. It belongs on the server.
- **Remediation:** Move authentication to the server. Never ship credentials in the app, and never make the access decision on the client.

### M1 · Insecure Local Storage — Medium
After login the app stores data on the device in the clear. `LoginActivity` calls `getSharedPreferences("session", 0)` then `putString("session_flag", ...)`, writing to `shared_prefs/session.xml`. The `0` is `MODE_PRIVATE`, which only blocks other apps and does not encrypt.

- **Impact:** SharedPreferences is just XML inside the app sandbox. With root or a debuggable build it is readable, so any secret stored there is effectively cleartext.
- **Remediation:** Do not store secrets in SharedPreferences. Keep session state server-side, or use the Android Keystore for anything that must live on the device.

### E3 · The Door Left Open — Medium
`SecretActivity` is declared `exported="true"` with no intent-filter in the manifest. Nothing in the interface links to it, but it can still be started from outside the app. Its `onCreate` writes the flag straight into the screen text.

- **Impact:** Exported true lets any app, or the adb shell, start a component. Reachable plus hidden is the whole bug.
- **Remediation:** Set exported to false on internal screens, or guard them with a signature-level permission.

### E4 · Loud Logs — Medium
During sign-in the app writes a session token to the device log in the clear, under a custom tag `VaultBankAuth`. The same token is also hardcoded in `LoginActivity`.

- **Impact:** logcat is readable through adb and by anything with log access. Sensitive values should never be logged, even in debug builds.
- **Remediation:** Remove the hardcoded token and strip debug logging of sensitive values from release builds.

### M4 · Your Own Key, Handed to You — Medium
An encrypted premium license ships inside the app alongside the key that unlocks it. `Crypto.java` holds the key `0123456789abcdef`, the base64 ciphertext `LICENSE_BLOB`, and the algorithm `AES/ECB/PKCS5Padding`.

- **Impact:** Strong encryption is useless if the key ships in the same app. The key has to live outside the client.
- **Remediation:** Keep the key off the client. Decrypt server-side, or derive the key from a server-provided secret at runtime.

### E1 · Strings Don't Hide Secrets — Low
A promotional code is built into the app and never shown in the interface. It lives in the string resources, in a resource named `promo_code`, in plain text.

- **Impact:** String resources are storage for static data, not a security boundary. Every value ships word for word inside the APK.
- **Remediation:** Do not ship secrets in string resources. Keep promo codes on the server and fetch them at runtime.

### E5 · Config Says Too Much — Low
A bundled config file, `assets/config.json`, carries a `telemetry_key` field shaped like Base64 among otherwise plain fields. That mismatch marks it as the target, and decoding it reveals the flag.

- **Impact:** Files under assets are shipped word for word inside the APK, and Base64 is encoding, not encryption.
- **Remediation:** Do not ship secrets in assets. Move the telemetry key server-side.

### M5 · Root Check, in Java — Low
A rewards feature refuses to run on rooted devices. `DashboardActivity` gates the reward behind `RootCheck.isRootedJava()`, which looks for su binaries and checks `Build.TAGS` for test-keys. Because the check runs in the app, it can be forced to return false.

- **Impact:** A root check that runs inside the app can be flipped by the attacker. It slows people down but does not stop them.
- **Remediation:** Do not rely on a client-side root check as a security control. Enforce sensitive logic server-side, with attestation if integrity matters.

## Summary

| ID | Weakness | Severity |
| --- | --- | --- |
| E2 | Live API key in BuildConfig | High |
| M2 | Exported provider, no access control | High |
| M3 | Client-side auth, hardcoded creds | High |
| M1 | Insecure local storage in cleartext | Medium |
| E3 | Exported activity, no intent-filter | Medium |
| E4 | Session token leaked to logcat | Medium |
| M4 | Hardcoded key shipped with ciphertext | Medium |
| E1 | Promo code in string resources | Low |
| E5 | Base64 secret in bundled assets | Low |
| M5 | Client-side root check, bypassable | Low |

## Recommendations
- Keep secrets and keys off the client. Keys, promo codes and tokens belong on a server, not in resources, generated code or assets.
- Treat encoding as cosmetic. Base64 and similar are not encryption.
- Lock down exported components. Default internal screens and providers to not exported or permission-guarded.
- Put authentication and authorization on the server, not in app code.
- Strip sensitive logging from release builds.
- Treat client-side checks like root detection as speed bumps, not controls.
- Rotate any key that has shipped inside an app; assume it is already public.

## Steps to reproduce
The key commands used, in the same order as the findings.

**E2:** Opened the APK in jadx and read `API_KEY` in the generated `BuildConfig` class.

**M2:** Queried the exported provider on the device using the authority from the manifest.
```
adb shell content query --uri content://com.pentestlab.target.provider
```

**M3:** Read the hardcoded staff credentials in `LoginActivity`; alternatively a Frida script `m3.js` overrides `validateLocal` to return true.
```
frida -U -f com.pentestlab.target -l m3.js
```

**M1:** Used run-as to read the SharedPreferences file.
```
adb shell run-as com.pentestlab.target cat /data/data/com.pentestlab.target/shared_prefs/session.xml
```

**E3:** Decoded the manifest, confirmed `SecretActivity` was exported with no intent-filter, then launched it directly.
```
adb shell am start -n com.pentestlab.target/.SecretActivity
```

**E4:** Followed the app's log output while signing in.
```
adb shell pidof com.pentestlab.target
adb logcat -c
adb logcat --pid=<pid>
adb logcat VaultBankAuth:D *:S
```

**M4:** Found `Crypto.java` by searching the decompiled code for Cipher / SecretKeySpec / AES, then decrypted offline in CyberChef (From Base64, then AES Decrypt, key as UTF8, mode ECB).

**E1:** Decoded the package with apktool and searched the output.
```
apktool d target.apk -o out -f
findstr /s /i "promo" out\*
```

**E5:** Opened the bundled `assets/config.json`, found `telemetry_key` as a Base64-shaped value, and decoded it in CyberChef.

**M5:** Forced the root check to return false with Frida (`m5.js` overrides `isRootedJava`).
```
frida -U -f com.pentestlab.target -l m5.js
```
