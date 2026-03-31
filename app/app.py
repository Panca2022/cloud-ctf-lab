from flask import Flask, request, render_template_string, json
import requests

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="autocomplete" content="off">
    <title>Cloud File Fetcher</title>
    <style>
        body {
            background: #0f172a;
            color: #e2e8f0;
            font-family: Arial, sans-serif;
        }
        .container {
            width: 650px;
            margin: 80px auto;
            padding: 30px;
            background: #1e293b;
            border-radius: 10px;
        }
        h2 { text-align: center; color: #38bdf8; }
        label { margin-top: 10px; display: block; }
        input {
            width: 100%;
            padding: 10px;
            margin-top: 5px;
            background: #0f172a;
            color: white;
            border: none;
            border-radius: 6px;
        }
        button {
            width: 100%;
            padding: 12px;
            margin-top: 20px;
            background: #38bdf8;
            border: none;
            border-radius: 6px;
        }
        .output {
            margin-top: 20px;
            padding: 15px;
            background: black;
            font-family: monospace;
            white-space: pre-wrap;
        }
    </style>
</head>
<body>

<!-- metadata: http://metadata/ -->

<div class="container">
    <h2>☁️ Cloud File Fetcher</h2>

    <form method="POST" autocomplete="off">

        <label>Target URL</label>
     	<input name="url" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" placeholder="Try internal services like http://metadata/ or http://storage/">

        <label>HTTP Method</label>
        <input name="method" placeholder="GET / PUT / POST">

        <label>X-Access-Key</label>
        <input name="access_key" placeholder="Enter access key" autocomplete="off">

        <label>X-Secret-Key</label>
        <input name="secret_key" placeholder="Enter secret key" autocomplete="off">

	<label>Metadata Token</label>
	<input name="metadata_token" placeholder="Paste IMDSv2 token here">

        <button type="submit">Fetch</button>
    </form>

    {% if output %}
    <div class="output">{{output}}</div>
    {% endif %}
</div>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    output = ""

    if request.method == "POST":
        url = request.form.get("url")
        method = request.form.get("method", "GET").upper()

        headers = {}

        # ✅ Required for IMDSv2 token request
        headers["X-aws-ec2-metadata-token-ttl-seconds"] = "21600"

        # ✅ Metadata token (for protected metadata endpoints)
        metadata_token = request.form.get("metadata_token")
        if metadata_token:
            headers["X-aws-ec2-metadata-token"] = metadata_token

        # ✅ Storage credentials (for storage service)
        access_key = request.form.get("access_key")
        secret_key = request.form.get("secret_key")

        if access_key:
            headers["X-Access-Key"] = access_key

        if secret_key:
            headers["X-Secret-Key"] = secret_key

        try:
            # ✅ HTTP method handling
            if method == "POST":
                r = requests.post(url, headers=headers, timeout=3)
            elif method == "PUT":
                r = requests.put(url, headers=headers, timeout=3)
            elif method == "DELETE":
                r = requests.delete(url, headers=headers, timeout=3)
            else:
                r = requests.get(url, headers=headers, timeout=3)

            # ✅ Pretty JSON output
            try:
                output = json.dumps(r.json(), indent=4)
            except:
                output = r.text[:1000]

        except Exception as e:
            output = f"""
Error fetching URL.

Debug Info:
- Internal services may exist:
    • http://metadata/
    • http://storage/
- Try different HTTP methods

Actual Error:
{str(e)}
"""

    return render_template_string(HTML, output=output)


@app.route("/robots.txt")
def robots():
    return """
User-agent: *
Disallow: /internal

# metadata at http://metadata/
"""


@app.route("/internal")
def internal():
    return """
Internal Services:
- http://metadata/
- http://storage/
"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
