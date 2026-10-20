# Lab 04 · Payback Time

**Category:** A06 Insecure Design &nbsp;·&nbsp; **Target:** OWASP Juice Shop &nbsp;·&nbsp; **Tools:** Browser DevTools

## Lab Description

> Force a negative basket total to make the shop pay you instead of charging you, by sending a value the user interface would never allow.

## Overview

Insecure design is not a single bug you can patch; it is a missing rule. The application assumes the quantity is always a positive number because the UI only lets you pick positive numbers. But the UI is not the server. If the server never enforces "quantity must be at least 1" and "a total can't go below zero", the attacker just talks to the API directly and breaks the assumption the whole design rested on.

## Solution

Logged in as a normal user, I added the most highly priced product I could find to the basket. That was the Juice Shop "Permafrost" 2020 Edition at 9999.99.

![The most expensive item in the basket, one unit at 9999.99.](images/fig4-1.png)

I start with the most expensive item so the effect of a negative quantity is large and obvious.

With DevTools open on the **Network** tab, I changed the quantity in the UI and watched for the request that carries the update. It is a `PUT` to `/api/BasketItems/<id>`, and the server answers `200 OK`.

![The basket update request: PUT /api/BasketItems/10, returning 200 OK.](images/fig4-2.png)

This identifies the exact request the app uses to update a basket line, which is the one I need to tamper with.

I used **Copy as fetch** from the Network tab so I had the whole call, headers and body, ready to edit.

![Copy › Copy as fetch on the basket update request.](images/fig4-3.png)

Copying the full call lets me replay it from the console with my own changes, bypassing the form entirely.

![The copied fetch in the console, quantity 1 highlighted in the body.](images/fig4-4.png)

Here is the request pasted into the console, with the quantity sitting at its original value of `1` before I edit it.

Then I changed it to `-100`. In the web page the lowest you can go is 1, but sending the request straight to the API lets me push past that limit into a negative number.

![The same request re-sent with the body changed to quantity -100.](images/fig4-5.png)

This is the key move: a negative quantity the UI would never submit, sent directly to the API.

![The basket after tampering: quantity -100 and a total of -999999.](images/fig4-6.png)

The basket now shows `-100` units and a total of `-999999`. The negative quantity made the whole total negative.

I went to checkout and completed the order. Because the total is negative the shop credits the wallet instead of charging it.

![Order confirmed and the Payback Time challenge solved.](images/fig4-7.png)

The order that should have cost ten thousand instead pays me, and the challenge is solved.

## Root cause, impact and fix

| | |
| --- | --- |
| **Missing invariants** | Quantity must be a whole number of at least 1; an order total must never be below 0; wallet debits must be non-negative. |
| **Why UI limits don't help** | The attacker talks directly to the API, so any limit that only lives in the browser is irrelevant. |
| **Why it's a design problem** | The application relied on frontend limitations instead of enforcing the rules on the server. |
| **Fix** | Validate every basket update on the server, reject any order whose total is below 0, only ever debit a wallet by a positive amount, and add database `CHECK` constraints such as `quantity >= 1`. |
