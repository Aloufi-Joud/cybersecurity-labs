# Task 01 · Network traffic analysis in Splunk

**Program:** stc × Misk Virtual Work Experience — Cybersecurity Incident Response &nbsp;·&nbsp; **Tools:** Splunk, Blue Coat proxy logs

## Task

Analyse a set of web-proxy logs in Splunk to find evidence of an attack, then document it:

1. Log in to the SIEM (Splunk) used to analyse the systems' and network's security events.
2. Load the provided log file into Splunk (upload it under **Add Data → Upload → Select File**).
3. Search and analyse the logs for any attacks, using a filter such as `action="blocked"` to focus on traffic that was prevented.
4. Identify the attacks and write a cyber-incident report.
5. Fill in a log table and identify the suspicious fields.

## Overview

A web proxy sits between users and the internet and records every request, whether it was **allowed** or **blocked** by policy. For an analyst, the blocked events are the fast way in: they are the requests the security controls already decided were dangerous. Filtering a day's traffic down to `action="blocked"` turns thousands of ordinary browsing events into a short list worth reading, and the proxy's own fields (category, threat risk, filter result) explain *why* each one was stopped.

## What I did

I loaded the proxy log into Splunk (`Add Data → Upload`), confirmed it parsed into fields, then narrowed the whole capture to the events that were blocked:

```
action="blocked"
```

Out of 26 events for the user `Fahad3315` (client `10.55.66.777`), 24 were allowed (VirusTotal, HaveIBeenPwned, YouTube) and **2 were blocked**. Both blocked events were the same target, and the proxy's own metadata made the reason obvious.

## Finding

The user attempted to reach **`www.zone-h.org`**, a site the proxy classifies under the category **Hacking**. `zone-h.org` is a well-known public archive of defaced websites, the kind of resource associated with attacker reconnaissance rather than normal business browsing. The proxy policy denied both requests.

What makes it more than an idle click is the surrounding activity: the same user had been visiting offensive/OSINT tooling (VirusTotal, HaveIBeenPwned) in the same session. On its own each site is harmless, but together with an attempt to reach a hacking resource, the pattern is worth flagging.

### Suspicious fields

| # | Field | Value | Why it's suspicious |
| --- | --- | --- | --- |
| 1 | `action` | `blocked` | The request was stopped by policy, not completed. |
| 2 | `cs_categories` | `Hacking` | The destination is categorised as a hacking resource. |
| 3 | `cs_threat_risk` | `4` | A high threat-risk score assigned by the proxy. |
| 4 | `cs_host` | `www.zone-h.org` | A known website-defacement archive, not business-related. |

Supporting fields: `sc_filter_result = DENIED`, `s_action = TCP_DENIED`, `sc_status = 403`, `vendor_action = policy_denied`.

### The blocked log entries

```
2021-11-16 08:39:26  10.55.66.777  Fahad3315  stc\proxylanusers  policy_denied  DENIED
"Hacking"  http://www.zone-h.org/  403  TCP_DENIED  GET  http  www.zone-h.org  80  /favicon.ico
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/95.0.4638.69 Safari/537.36"  threat_risk 4

2021-11-16 08:39:24  10.55.66.777  Fahad3315  stc\proxylanusers  policy_denied  DENIED
"Hacking"  403  TCP_DENIED  GET  http  www.zone-h.org  80  /
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/95.0.4638.69 Safari/537.36"  threat_risk 4
```

## Incident report

- **When:** 16 Nov 2021, around 11:39 (UTC+3).
- **Who:** user `Fahad3315` (auth group `stc\proxylanusers`), internal client `10.55.66.777`, through proxy `10.20.30.40`.
- **What:** two GET requests to `www.zone-h.org`, a destination categorised as **Hacking** with threat risk **4**.
- **Outcome:** both requests were **blocked** by proxy policy (`TCP_DENIED`, HTTP 403). No data left the network to that host.
- **Assessment:** attempted access to a hacking/defacement resource, in a session that also touched offensive-security tooling. The control worked, but the behaviour should be reviewed with the user's manager, because intent, not just outcome, is what matters here.
- **Recommendations:** keep the Hacking category blocked for this user group; review the account's recent proxy history for other high-risk categories; confirm whether the activity was sanctioned (for example, security research) before escalating.

## Takeaway

The blocked events were the whole story. Filtering to `action="blocked"` and reading the proxy's category and threat-risk fields turned a full day of browsing into a single, defensible finding in a couple of minutes.

> The username, IP addresses and host in this log are from the training scenario, not a real environment.
