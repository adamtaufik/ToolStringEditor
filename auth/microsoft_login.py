# auth/microsoft_login.py
import threading
import webbrowser
import time
from flask import Flask, request
import msal
import tempfile
import os

from utils.session_manager import SessionManager

CLIENT_ID = "0ed91e5c-d383-425d-b137-2790b342debe"
TENANT_ID = "69db6309-1571-4c9e-bd41-8808077c50e6"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_URI = "http://localhost:5000/getAToken"
SCOPE = ["User.Read"]

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wirehub_secret_key'
auth_result = {}
server_thread = None


@app.route("/getAToken")
def authorized():
    """Handles redirect from Microsoft after login."""
    global auth_result

    code = request.args.get("code")
    if not code:
        return "No authorization code provided."

    msal_app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
    result = msal_app.acquire_token_by_authorization_code(
        code, scopes=SCOPE, redirect_uri=REDIRECT_URI
    )

    auth_result.update(result)
    print("\n=== Microsoft Login Result ===")
    print(auth_result)
    print("==============================\n")

    # Shut down Flask server after login
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if shutdown:
        shutdown()

    # ✅ Return HTML that closes popup after 3s
    return """
    <html>
        <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h2>✅ Login successful!</h2>
            <p>You can close this window. It will close automatically in 3 seconds.</p>
            <script>
                setTimeout(() => {
                    window.open('', '_self', '');
                    window.close();
                }, 3000);
            </script>
        </body>
    </html>
    """


def run_server():
    app.run(port=5000, debug=False, use_reloader=False)

def login_with_microsoft():
    """Launch Microsoft login in a popup and return token result."""
    global auth_result, server_thread
    auth_result.clear()

    # Start Flask server in background
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Create MSAL client
    msal_app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
    auth_url = msal_app.get_authorization_request_url(scopes=SCOPE, redirect_uri=REDIRECT_URI)

    # ✅ Create popup launcher HTML (requires a click to bypass popup blocker)
    html_content = f"""
    <html>
        <head>
            <title>WireHub Login</title>
            <script>
                function openPopup() {{
                    const popup = window.open("{auth_url}", "MicrosoftLogin",
                        "width=600,height=700,left=400,top=100");
                    const checkPopup = setInterval(() => {{
                        if (popup.closed) {{
                            clearInterval(checkPopup);
                            window.close();
                        }}
                    }}, 500);
                }}
            </script>
        </head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 80px;">
            <h2>Welcome to WireHub</h2>
            <p>Please sign in with your Microsoft account to continue.</p>
            <button onclick="openPopup()" 
                    style="background-color:#0078D4; color:white; font-size:16px;
                           padding:12px 28px; border:none; border-radius:6px; cursor:pointer;">
                Sign in with Microsoft
            </button>
        </body>
    </html>
    """

    import tempfile, os
    temp_html = os.path.join(tempfile.gettempdir(), "wirehub_login.html")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    # ✅ Open launcher page — popup opens only after button click (not blocked)
    webbrowser.open(f"file:///{temp_html}")

    # Wait for token result (polling)
    import time
    for _ in range(60):
        if auth_result:
            break
        time.sleep(1)

    if not auth_result:
        return {"error": "Login timed out or failed."}

    # ✅ Extract user info
    access_token = auth_result.get("access_token")
    user_name = auth_result.get("id_token_claims", {}).get("name", "Unknown User")
    user_email = auth_result.get("id_token_claims", {}).get("preferred_username", "Unknown Email")

    # ✅ Save to global session
    session = SessionManager()
    session.set_user(user_name, user_email, access_token)

    return auth_result
