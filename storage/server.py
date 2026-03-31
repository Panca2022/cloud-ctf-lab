from flask import Flask, request, jsonify
import os
import json
import time
import random
import string

app = Flask(__name__)

CREDS_FILE = "/data/creds.json"

# -----------------------
# Safe Credential Loader (Race Condition Fix)
# -----------------------
while True:
    try:
        with open(CREDS_FILE) as f:
            CREDS = json.load(f)
        break
    except:
        time.sleep(0.2)

VALID_ACCESS_KEY = CREDS["AccessKeyId"]
VALID_SECRET_KEY = CREDS["SecretAccessKey"]


# -----------------------
# Buckets
# -----------------------
BUCKETS = ["public-assets", "logs-backup", "secret-archive"]


# -----------------------
# Generate Dynamic Flag
# -----------------------
def generate_flag():
    rand = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
    return f"flag{{CTF_{rand}}}"

FLAG = generate_flag()


# -----------------------
# Routes
# -----------------------
@app.route("/")
def list_buckets():
    return jsonify(BUCKETS)


@app.route("/secret-archive")
def secret_archive():
    access_key = request.headers.get("X-Access-Key")
    secret_key = request.headers.get("X-Secret-Key")

    if access_key != VALID_ACCESS_KEY or secret_key != VALID_SECRET_KEY:
        return "Access Denied", 403

    return jsonify({
        "flag": FLAG,
        "note": "Sensitive backup data"
    })

@app.route("/health")
def health():
    return "OK"

# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
