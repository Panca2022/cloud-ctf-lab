# Cloud SSRF → IMDSv2 → Privilege Escalation CTF

> This is a **security lab**, not a normal app. The vulnerabilities are **intentional** — they are the entire point. The "reliability work" here is about making the lab easier to run, log, and explain, not about fixing the SSRF. Fixing the SSRF would destroy the CTF.

This is a strong interview project because it demonstrates:
- Understanding of SSRF attacks
- Knowledge of AWS IMDSv2
- Docker networking and microservices
- Multi-container orchestration
- Security awareness

---

A deliberately vulnerable multi-container cloud lab that simulates a real-world attack chain: **Server-Side Request Forgery (SSRF)** → **AWS Instance Metadata Service (IMDSv2) exploitation** → **credential leakage** → **privilege escalation to cloud storage**.

Built with Docker Compose and Flask, this lab is designed for security training, red-team practice, and cloud security education.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [The Attack Chain](#2-the-attack-chain)
3. [Architecture](#3-architecture)
4. [Folder Structure](#4-folder-structure)
5. [Services](#5-services)
6. [How It Works](#6-how-it-works)
7. [Setup](#7-setup)
8. [Running the Lab](#8-running-the-lab)
9. [Walkthrough (Solution)](#9-walkthrough-solution)
10. [Why These Design Decisions](#10-why-these-design-decisions)
11. [Security Concepts Demonstrated](#11-security-concepts-demonstrated)
12. [Limitations](#12-limitations)
13. [Future Improvements](#13-future-improvements)
14. [Interview Notes](#14-interview-notes)

---

## 1. Project Overview

This lab simulates a common cloud misconfiguration:

- A public-facing web app contains an **SSRF vulnerability**
- The app can reach an **internal metadata service** (mimicking AWS IMDSv2)
- The metadata service requires a **token** before it returns credentials
- Once credentials are stolen, they unlock a **storage service** holding a secret flag

Goal: retrieve the flag from `http://storage/secret-archive`.

---

## 2. The Attack Chain

```text
[ Attacker ]
     |
     |  1. Finds SSRF in app (Cloud File Fetcher)
     v
[ App:5000 ]  --- HTTP request --->  [ Metadata ]
     |                                    |
     |  2. PUT /latest/api/token          |
     |  3. GET  /latest/meta-data/iam/    |
     |        security-credentials/ctf-role
     |                                    |
     |  4. Gets AccessKeyId + SecretKey   |
     v
[ App:5000 ]
     |
     |  5. Sends X-Access-Key + X-Secret-Key
     v
[ Storage ]  --- validates ---> returns flag{...}
```

---

## 3. Architecture

Three Flask services on a shared Docker bridge network (`ctfnet`):

| Service    | Port | Role                                       |
|------------|------|---------------------------------------------|
| `app`      | 5000 | Public-facing SSRF vulnerability             |
| `metadata` | 80   | Simulates AWS IMDSv2 with token auth         |
| `storage`  | 80   | Requires valid credentials to reveal flag    |

The metadata and storage services share a volume (`shared-data`) containing `creds.json`.

---

## 4. Folder Structure

```text
cloud-ctf-lab-main/
├── docker-compose.yml
├── README.md
├── .gitignore
├── app/
│   ├── app.py
│   └── Dockerfile
├── metadata/
│   ├── server.py
│   └── Dockerfile
└── storage/
    ├── server.py
    └── Dockerfile
```

---

## 5. Services

### `app` — Cloud File Fetcher
- Public endpoint on port 5000
- Accepts a URL, HTTP method, and headers via a form
- Uses `requests` to fetch the URL server-side (this is the SSRF)
- Returns the raw response

### `metadata` — Simulated IMDSv2
- Requires `PUT /latest/api/token` with `X-aws-ec2-metadata-token-ttl-seconds` header
- Returns credentials at `/latest/meta-data/iam/security-credentials/ctf-role`
- Enforces token on every metadata route

### `storage` — Protected Cloud Storage
- `/` lists buckets
- `/secret-archive` requires valid `X-Access-Key` and `X-Secret-Key`
- Returns a dynamically generated flag

---

## 6. How It Works

1. The app runs `requests.get(url)` with an attacker-controlled URL — this is the SSRF.
2. The attacker uses SSRF to call `http://metadata/latest/api/token` via `PUT` with the TTL header.
3. Metadata returns a token.
4. The attacker sends SSRF with `X-aws-ec2-metadata-token: <token>` to `/latest/meta-data/iam/security-credentials/ctf-role`.
5. Metadata returns `creds.json`.
6. The attacker sends SSRF to `http://storage/secret-archive` with `X-Access-Key` and `X-Secret-Key`.
7. Storage validates and returns the flag.

---

## 7. Setup

Requirements:
- Docker
- Docker Compose

```bash
git clone https://github.com/Panca2022/cloud-ctf-lab.git
cd cloud-ctf-lab-main
docker-compose up --build
```

---

## 8. Running the Lab

Open the app:

```
http://localhost:5000
```

Try a URL like `http://metadata/` to explore.

---

## 9. Walkthrough (Solution)

**Step 1 — Get the IMDSv2 token via SSRF**
- URL: `http://metadata/latest/api/token`
- Method: `PUT`
- Header: `X-aws-ec2-metadata-token-ttl-seconds: 21600`
- Result: a token string

**Step 2 — Use the token to read the role name**
- URL: `http://metadata/latest/meta-data/iam/security-credentials/`
- Method: `GET`
- Header: `X-aws-ec2-metadata-token: <token>`
- Result: `ctf-role`

**Step 3 — Read the credentials**
- URL: `http://metadata/latest/meta-data/iam/security-credentials/ctf-role`
- Method: `GET`
- Header: `X-aws-ec2-metadata-token: <token>`
- Result: JSON with `AccessKeyId` and `SecretAccessKey`

**Step 4 — Use credentials to fetch the flag**
- URL: `http://storage/secret-archive`
- Method: `GET`
- Headers:
  - `X-Access-Key: <AccessKeyId>`
  - `X-Secret-Key: <SecretAccessKey>`
- Result: `flag{CTF_...}`

---

## 10. Why These Design Decisions

**Why Docker Compose?**
It lets us model three separate services with a private network, exactly like a real cloud. This shows understanding of microservices and cloud networking.

**Why Flask?**
Lightweight, simple, minimal dependencies. Each service is under 100 lines. This keeps the focus on the security lesson, not on framework complexity.

**Why a shared volume for credentials?**
In real AWS, credentials come from the metadata service. Here, both services share `/data/creds.json` so the metadata service can serve them and the storage service can validate them. It simulates the trust model without over-engineering.

**Why IMDSv2 (token-based) rather than IMDSv1 (no token)?**
IMDSv1 is trivial to exploit with a single GET. IMDSv2 forces a two-step token flow with a PUT — this teaches the extra hop required in real SSRF attacks. It is a much better learning exercise.

**Why SSRF in the app?**
SSRF is one of the top risks in the OWASP Top 10 and one of the most common cloud security issues. A file fetcher is a realistic trigger — many real services had SSRF through "URL preview" or "file loader" features.

**Why a dynamic flag?**
The flag is generated at container start with random characters, so it cannot be hardcoded in any writeup. This is best practice in modern CTFs.

**Why the "hints" in the app?**
The app returns hints for 401, 403, and 500 errors. This makes the lab beginner-friendly — the user is guided when stuck. It also mimics real-world services that return verbose error messages.

---

## 11. Security Concepts Demonstrated

| Concept                  | Where                                                  |
|---------------------------|--------------------------------------------------------|
| SSRF                       | `app/app.py` — `requests.get(url)` with no allowlist  |
| IMDSv2 token flow          | `metadata/server.py` — `PUT /latest/api/token`        |
| Credential leakage         | `metadata/server.py` — `/latest/meta-data/iam/...`    |
| Authorization bypass       | `storage/server.py` — header-based auth                |
| Container networking       | `docker-compose.yml` — private bridge                  |
| Race condition fix         | `storage/server.py` — retry loop for creds file       |

---

## 12. Limitations

- Metadata service runs over HTTP (no TLS) — acceptable for a lab
- Credentials are stored in a shared volume instead of an in-memory vault
- No rate limiting on the token endpoint
- No HTTPS on the app
- The flag is not persisted across restarts (dynamically generated each time) — see Part 2, Add 6 for a fix

---

## 13. Future Improvements

1. **Difficulty levels** — easy (IMDSv1) and hard (IMDSv2 with hop limit)
2. **Scoreboard** — track teams and times
3. **Flag submission endpoint** — validate `flag{...}` server-side
4. **Logging** — write every request to `logs/app.log`
5. **Health checks** — `depends_on` with `condition: service_healthy`
6. **HTTPS** — self-signed certs for realism
7. **GuardDuty-style detection** — log suspicious SSRF patterns
8. **Multiple flags** — a multi-step capture path
9. **Documented detection rules** — how a defender would catch this
10. **Kubernetes version** — as a follow-up lab

---

### Honest framing

> "This lab is intentionally vulnerable — that's the point. If I fixed the SSRF or removed the metadata endpoint, there would be no lesson. The design choices are about making the attack chain realistic and educational, not about making the app secure."

---

### E. Quick cheat sheet

| Question | One-liner |
|---|---|
| What is the attack? | SSRF → IMDSv2 → credentials → storage flag |
| Why IMDSv2? | Two-step token flow, harder to exploit than IMDSv1 |
| How do services talk? | Private Docker bridge network, service names |
| How to prevent SSRF? | Allowlist, block internal IPs, IMDSv2 hop limit 1 |
| What was the race condition fix? | Retry loop for `creds.json` |
| OWASP category? | A10:2021 SSRF |
| Real-world example? | Capital One 2019 breach |
| Why a dynamic flag? | Cannot be hardcoded in writeups |

---

