from flask import Flask, jsonify, request
import os
import secrets
import json

app = Flask(__name__)

CREDS_FILE = "/data/creds.json"

# -----------------------
# Generate or Load Creds
# -----------------------
def generate_creds():
    creds = {
        "AccessKeyId": secrets.token_hex(8),
        "SecretAccessKey": secrets.token_hex(16),
        "Token": secrets.token_urlsafe(32)
    }

    with open(CREDS_FILE, "w") as f:
        json.dump(creds, f)

    return creds


if os.path.exists(CREDS_FILE):
    with open(CREDS_FILE) as f:
        CREDS = json.load(f)
else:
    CREDS = generate_creds()


# -----------------------
# IMDSv2 Token Handling
# -----------------------
VALID_TOKENS = set()

@app.route("/latest/api/token", methods=["PUT"])
def token():
    ttl = request.headers.get("X-aws-ec2-metadata-token-ttl-seconds")
    if not ttl:
        return "Missing TTL header", 400

    token = secrets.token_hex(32)
    VALID_TOKENS.add(token)
    return token


def require_token():
    token = request.headers.get("X-aws-ec2-metadata-token")
    return token in VALID_TOKENS


# -----------------------
# Metadata Endpoints
# -----------------------
@app.route("/")
def root():
    return "latest/"


@app.route("/latest/")
def latest():
    return "meta-data/"


@app.route("/latest/meta-data/")
def meta_root():
    if not require_token():
        return "Unauthorized", 401
    return "iam/"


@app.route("/latest/meta-data/iam/")
def iam():
    if not require_token():
        return "Unauthorized", 401
    return "security-credentials/"


@app.route("/latest/meta-data/iam/security-credentials/")
def role_name():
    if not require_token():
        return "Unauthorized", 401
    return "ctf-role"


@app.route("/latest/meta-data/iam/security-credentials/ctf-role")
def creds_endpoint():
    if not require_token():
        return "Unauthorized", 401
    return jsonify(CREDS)


# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
