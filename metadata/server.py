from flask import Flask, jsonify, request
import os
import random
import string
import secrets 
app = Flask(__name__)

# 🔐 Generate credentials
def generate_creds():
    return {
        "AccessKeyId": os.environ.get("ACCESS_KEY"),
        "SecretAccessKey": os.environ.get("SECRET_KEY"),
        "Token": ''.join(random.choices(string.ascii_letters, k=64))
    }

CREDS = generate_creds()

# 🔑 Store valid tokens
VALID_TOKENS = set()

# 🧠 Generate IMDSv2 token
@app.route("/latest/api/token", methods=["PUT"])
def token():
    ttl = request.headers.get("X-aws-ec2-metadata-token-ttl-seconds")

    if not ttl:
        return "Missing TTL header", 400

    token = secrets.token_hex(32)

    VALID_TOKENS.add(token)   # ✅ STORE TOKEN

    return token

# 🔒 Token validation middleware
def require_token():
    token = request.headers.get("X-aws-ec2-metadata-token")
    if token not in VALID_TOKENS:
        return False
    return True


# 🔓 Root (for discovery)
@app.route("/")
def root():
    return "latest/"


@app.route("/latest/")
def latest():
    return "meta-data/"


# 🔒 Protected metadata endpoints
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
def creds():
    if not require_token():
        return "Unauthorized", 401
    return jsonify(CREDS)


app.run(host="0.0.0.0", port=80)
