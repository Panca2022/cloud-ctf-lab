# ☁️ Cloud SSRF → IMDSv2 → Privilege Escalation CTF

## Description
This challenge simulates a cloud environment with:
- SSRF vulnerability
- Internal metadata service (IMDSv2)
- Credential leakage
- Privilege escalation to storage service

## Goal
Retrieve the flag from:
http://storage/secret-archive

## Setup

### Requirements
- Docker
- Docker Compose

### Run
```bash
docker-compose up --build
```

### Access App
http://localhost:5000

## Hints
- Internal services exist
- Metadata might require authentication
- Headers may be useful

## Author
YourName
