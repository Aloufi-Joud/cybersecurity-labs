# Cybersecurity Labs

Hands-on security write-ups from the **Cybersecurity Solutions & Analytics Bootcamp** (Kaspersky & Tuwaiq Academy, 2026). Each lab documents what I did, why it worked, and how to fix it, with the reasoning spelled out at every step.

## Featured

**[Credential Storage Challenge](appsec/credential-storage-challenge/)** — a secure password-storage layer I built from scratch with Argon2id, including timing-safe verification against username enumeration, Unicode-safe handling, and a benchmarked parameter choice. This is engineering rather than a guided lab, and it is the piece I'm most proud of.

## Contents

| Area | What's inside |
| --- | --- |
| [**appsec/**](appsec/) | OWASP Juice Shop labs across the OWASP Top 10, plus the Argon2id [credential-storage challenge](appsec/credential-storage-challenge/) |
| [**portswigger/**](portswigger/) | Seven PortSwigger Web Security Academy labs (access control, authentication, business logic), solved with Burp Suite |
| [**mobile/**](mobile/) | VaultBank Android pentest: [Easy & Medium](mobile/vaultbank-easy-medium/) and [Hard & Insane](mobile/vaultbank-hard-insane/) tiers |
| [**incident-response/**](incident-response/) | stc × Misk incident-response simulation: SIEM log analysis in Splunk, blocked-traffic triage, and incident reporting |
| [**network/**](network/) | Network domain labs: OSI model, subnetting, port-scan scripting, attack-case analysis, FTP traffic analysis in Wireshark |

Each lab page follows the same layout: a short description, an overview of the vulnerability, a step-by-step solution with every screenshot explained, and a root-cause / impact / fix table.

## Skills and tools

- **Web:** Burp Suite (Proxy, Repeater, Intruder), OWASP Top 10, SQL injection, XSS, IDOR, access control, business-logic flaws
- **Mobile:** jadx, apktool, Frida, objection, Ghidra, adb, JWT tampering
- **Network:** Wireshark, Nmap, Netcat, OSI analysis, subnetting
- **Incident response:** Splunk (SIEM), proxy-log triage, blocked-traffic analysis, incident reporting
- **Secure coding:** Argon2id password storage, timing-safe verification

## About these labs

All testing was done against intentionally vulnerable training targets (OWASP Juice Shop, PortSwigger Web Security Academy, and the VaultBank training app) in a controlled lab environment, as part of the bootcamp coursework.

---

*Prepared by Joud Aloufi*
