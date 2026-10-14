from flask import Flask, request, jsonify
import os
import json
import time
import random
import string
import logging

app = Flask(__name__)

# -----------------------
# Logging
# -----------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("storage")

CREDS_FILE = "/data/creds.json"

# -----------------------
# Safe Credential Loader (Race Condition Fix)
# -----------------------
while True:
    try:
        with open(CREDS_FILE) as f:
            CREDS = json.load(f)
        break
    except Exception:
        time.sleep(0.2)

VALID_ACCESS_KEY = CREDS["AccessKeyId"]
VALID_SECRET_KEY = CREDS["SecretAccessKey"]


# -----------------------
# Buckets
# -----------------------
BUCKETS = ["public-assets", "logs-backup", "secret-archive"]


# -----------------------
# Flag (persisted across restarts)
# -----------------------
# Lives on the same /data volume as creds.json, so no docker-compose change
# is needed beyond the shared-data volume mount already in place.
FLAG_FILE = "/data/flag.txt"


def load_or_create_flag():
    if os.path.exists(FLAG_FILE):
        with open(FLAG_FILE) as f:
            return f.read().strip()
    rand = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
    flag = f"flag{{CTF_{rand}}}"
    with open(FLAG_FILE, "w") as f:
        f.write(flag)
    return flag


FLAG = load_or_create_flag()


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
        log.warning("Access denied to /secret-archive")
        return "Access Denied", 403

    log.info("Flag retrieved by authorized caller")
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