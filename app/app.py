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
        body { background: #0f172a; color: #e2e8f0; font-family: Arial, sans-serif; }
        .container { width: 650px; margin: 80px auto; padding: 30px; background: #1e293b; border-radius: 10px; }
        h2 { text-align: center; color: #38bdf8; }
        label { margin-top: 10px; display: block; }
        input { width: 100%; padding: 10px; margin-top: 5px; background: #0f172a; color: white; border: none; border-radius: 6px; }
        button { width: 100%; padding: 12px; margin-top: 20px; background: #38bdf8; border: none; border-radius: 6px; }
        .output { margin-top: 20px; padding: 15px; background: black; font-family: monospace; white-space: pre-wrap; }
        .hint { margin-top: 15px; font-size: 0.9em; color: #facc15; }
    </style>
</head>
<body>

<div class="container">
    <h2>☁️ Cloud File Fetcher</h2>

    <form method="POST" autocomplete="off">

        <label>Target URL</label>
        <input name="url" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false"
               placeholder="Try internal services: http://metadata/ or http://storage/">

        <label>HTTP Method</label>
        <input name="method" placeholder="GET / PUT / POST">

        <label>Metadata Token (IMDSv2 Header)</label>
        <input name="metadata_token" placeholder="X-aws-ec2-metadata-token (if required)" autocomplete="off">

        <label>X-Access-Key</label>
        <input name="access_key" placeholder="Enter access key (from metadata)" autocomplete="off">

        <label>X-Secret-Key</label>
        <input name="secret_key" placeholder="Enter secret key (from metadata)" autocomplete="off">

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
        # Required for IMDSv2 token request
        headers["X-aws-ec2-metadata-token-ttl-seconds"] = "21600"

        # Metadata token
        metadata_token = request.form.get("metadata_token")
        if metadata_token:
            headers["X-aws-ec2-metadata-token"] = metadata_token

        # Storage credentials
        access_key = request.form.get("access_key")
        secret_key = request.form.get("secret_key")

        if access_key:
            headers["X-Access-Key"] = access_key

        if secret_key:
            headers["X-Secret-Key"] = secret_key

        try:
            # Handle HTTP method
            if method == "POST":
                r = requests.post(url, headers=headers, timeout=3)
            elif method == "PUT":
                r = requests.put(url, headers=headers, timeout=3)
            elif method == "DELETE":
                r = requests.delete(url, headers=headers, timeout=3)
            else:
                r = requests.get(url, headers=headers, timeout=3)

            # Pretty JSON output
            try:
                output = json.dumps(r.json(), indent=4)
            except:
                output = r.text[:1000]

            # Context-aware hints
            if r.status_code == 401:
                output += "\n\n💡 Hint: It looks like you might need a metadata token to access this endpoint."
            elif r.status_code == 403:
                output += "\n\n💡 Hint: Access denied. Check if you are using the correct access and secret keys."
            elif r.status_code >= 500:
                output += "\n\n💡 Hint: Server error. Try a different HTTP method or check the URL."

        except requests.exceptions.ConnectionError:
            output = "⚠️ Could not connect to the target URL."
            output += "\n\n💡 Hint: Are you using the correct internal service name? Example: http://metadata/ or http://storage/"
        except requests.exceptions.Timeout:
            output = "⚠️ Request timed out."
            output += "\n\n💡 Hint: Try increasing timeout or check network connectivity."
        except Exception as e:
            output = f"Error fetching URL: {str(e)}"
            output += "\n\n💡 Hint: Double-check your URL, HTTP method, and credentials."

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
