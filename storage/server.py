from flask import Flask, request, jsonify
import os
import random
import string

app = Flask(__name__)

# 🔐 Fake credentials (from metadata)
VALID_ACCESS_KEY = os.environ.get("ACCESS_KEY","PLACEHOLDER")
VALID_SECRET_KEY = os.environ.get("SECRET_KEY","PLACEHOLDER")

# 📦 Buckets
BUCKETS = ["public-assets", "logs-backup", "secret-archive"]

# 🔥 Generate dynamic flag at runtime
def generate_flag():
    rand = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=20))
    return f"f|g{{CTF_{rand}}}"

FLAG = generate_flag()

@app.route("/")
def list_buckets():
    return jsonify(BUCKETS)


@app.route("/secret-archive")
def secret_archive():
    access_key = request.headers.get("X-Access-Key")
    secret_key = request.headers.get("X-Secret-Key")

    # 🔒 Access control
    if access_key != VALID_ACCESS_KEY or secret_key != VALID_SECRET_KEY:
        return "Access Denied", 403

    # 🔥 Return dynamic flag
    return jsonify({
        "flag": FLAG,
        "note": "Sensitive backup data"
    })


app.run(host="0.0.0.0", port=80)
