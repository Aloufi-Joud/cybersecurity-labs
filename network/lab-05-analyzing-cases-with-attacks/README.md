# Lab 05 · Analyzing cases with attacks

**Domain:** Network &nbsp;·&nbsp; **Skill:** Traffic and evidence analysis

## Purpose

To read short evidence descriptions, decide whether each one is an attack, and classify its type. Eleven cases, including some that are normal traffic meant to look suspicious.

## Overview

Detection is as much about ruling things out as catching them. Several of these cases describe behaviour that trips an alert but turns out to be legitimate (a monitoring node, a rescheduled backup, a chatty app). Being able to say *why* something is normal is just as important as naming an attack, because that is what separates a real finding from a false positive.

## The eleven cases

| # | Case | Verdict |
| --- | --- | --- |
| 01 | Sweep of the whole subnet with ICMP | Ping sweep (reconnaissance) |
| 02 | SYN packets across many ports | TCP SYN port scan (stealth scan) |
| 03 | Unsolicited ARP replies for the gateway | ARP spoofing / poisoning |
| 04 | A second, unregistered DHCP offer | Rogue DHCP server |
| 05 | DHCP pool drained from one port | DHCP starvation |
| 06 | A DNS reply from the wrong node | DNS spoofing |
| 07 | Rapid SSH logins, then admin access | Brute force |
| 08 | Half-open connections pile up | TCP SYN flood (denial of service) |
| 09 | Stable, limited monitoring traffic | Normal monitoring activity |
| 10 | Heavy night transfers after a schedule change | Normal backup operations |
| 11 | Many DNS queries from one app host | Normal application behaviour |

## Reasoning behind a few verdicts

- **01 Subnet-wide ICMP:** one workstation pinged every address in the subnet in a short time and never tried to connect to a service. That is reconnaissance, checking which hosts are alive, not normal traffic.
- **02 Many-port SYN scan:** SYNs to many ports, each followed by an immediate RST once the server answered, so no real connection was ever made. Probing ports without exchanging data is a port scan.
- **03 Gateway ARP poisoning:** the node kept sending ARP replies nobody asked for, claiming the gateway's IP maps to its own MAC. Workstations' ARP caches took the wrong MAC and traffic started routing through that node.
- **07 SSH brute force:** the same IP tried many usernames very fast until it finally logged in as admin, and it worked.
- **08 SYN flood:** a flood of SYNs with almost no final ACKs, so the server filled with half-open connections and legitimate clients couldn't connect.
- **10 Rescheduled night backup (normal):** the night traffic went only to backup servers on normal ports with no errors, and the change log showed the backup had just been moved to night. Planned, not an attack.

## Takeaway

The three "normal" cases are the point of the exercise. Classifying traffic is not about matching a pattern to an attack name; it is about weighing the evidence, including the context that explains why something unusual is actually fine.
