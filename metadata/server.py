from flask import Flask, jsonify, request
import os
import secrets

app = Flask(__name__)

# Load secrets from environment
ACCESS_KEY = os.environ.get("ACCESS_KEY","CTF_ACCESS_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY","CTF_SECRET_KEY")

# Store valid IMDSv2 tokens
VALID_TOKENS = set()

# Generate IAM credentials dynamically
def generate_creds():
    return {
        "AccessKeyId": ACCESS_KEY,
        "SecretAccessKey": SECRET_KEY,
        "Token": secrets.token_urlsafe(32)
    }

CREDS = generate_creds()

# -----------------------
# IMDSv2 token endpoint
# -----------------------
@app.route("/latest/api/token", methods=["PUT"])
def token():
    ttl = request.headers.get("X-aws-ec2-metadata-token-ttl-seconds")
    if not ttl:
        return "Missing TTL header", 400

    token = secrets.token_hex(32)
    VALID_TOKENS.add(token)
    return token

# -----------------------
# Token validation helper
# -----------------------
def require_token():
    token = request.headers.get("X-aws-ec2-metadata-token")
    return token in VALID_TOKENS

# -----------------------
# Metadata endpoints
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
