import os
import json
from flask import Flask, render_template, redirect, url_for, request
from dotenv import load_dotenv
from flask_oidc import OpenIDConnect

load_dotenv()

app = Flask(__name__)

# Client Secrets JSON
client_secrets = {
    "web": {
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "auth_uri": f"{os.getenv('KEYCLOAK_SERVER')}/realms/{os.getenv('KEYCLOAK_REALM')}/protocol/openid-connect/auth",
        "token_uri": f"{os.getenv('KEYCLOAK_SERVER')}/realms/{os.getenv('KEYCLOAK_REALM')}/protocol/openid-connect/token",
        "userinfo_uri": f"{os.getenv('KEYCLOAK_SERVER')}/realms/{os.getenv('KEYCLOAK_REALM')}/protocol/openid-connect/userinfo",
        "issuer": f"{os.getenv("KEYCLOAK_SERVER")}/realms/{os.getenv("KEYCLOAK_REALM")}",
        "redirect_uris": [
            f"{os.getenv("CALLBACK_URL")}"
        ]
    }
}

with open('client_secrets.json', 'w') as f:
    json.dump(client_secrets, f)
    
# Flask OIDC Configuration
app.config.update({
    'SECRET_KEY': os.getenv('FLASK_SECRET_KEY', 'a-default-dev-key'),
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
    'OIDC_ID_TOKEN_COOKIE_SECURE': False,
    'OIDC_USER_INFO_ENABLED': True,
    'OIDC_SCOPES': ['openid', 'email', 'profile'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post',
    'OIDC_CALLBACK_ROUTE': '/oidc/callback',
    'OVERWRITE_REDIRECT_URI': f"{os.getenv('CALLBACK_URL')}",
})

oidc = OpenIDConnect(app)

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/debug-groups')
@oidc.require_login
def debug_groups():
    user_info = oidc.user_getinfo(['groups', 'preferred_username', 'email'])
    return f"""
    <h1>Debug Info</h1>
    <p>User: {user_info.get('preferred_username', 'Not found')}</p>
    <p>Email: {user_info.get('email', 'Not found')}</p>
    <p>Groups: {user_info.get('groups', 'Not found - empty or missing')}</p>
    <p>Full user_info: {user_info}</p>
    <a href="/protected">Back to protected</a>
    """
    
@app.route('/oidc/callback')
def oidc_callback_debug():
    """Debug to see if callback is being hit."""
    print("=== CALLBACK WAS HIT ===")
    print(f"Request args: {request.args}")
    print(f"Request url: {request.url}")
    return "Callback received! Check your logs."

@app.route('/protected')
@oidc.require_login
def protected():
    user_info = oidc.user_getinfo(['groups'])
    user_groups = user_info.get('groups', [])
    
    print(f"User groups: {user_groups}")
    
    if 'students' in user_groups:
        print("Redirecting to student")
        return redirect(url_for('student'))
    
    elif 'faculty' in user_groups:
        print("Redirecting to faculty")
        return redirect(url_for('faculty'))
    elif 'admins' in user_groups:
        print("Redirecting to admin")
        return redirect(url_for('admin'))
    else:
        print(f"No matching group found. Groups: {user_groups}")
        print("Redirecting to home")
        return redirect(url_for('home'))

@app.route('/student')
def student():
    user_info = oidc.user_getinfo(['preferred_username', 'name', 'email', 'groups'])
    return render_template('student.html', user=user_info)

@app.route('/faculty')
def faculty():
    user_info = oidc.user_getinfo(['preferred_username', 'name', 'email', 'groups'])
    return render_template('faculty.html', user=user_info)

@app.route('/admin')
def admin():
    user_info = oidc.user_getinfo(['preferred_username', 'name', 'email', 'groups'])
    return render_template('admin.html', user=user_info)

# this was used for the logout debugging please ignore
@app.route('/debug-session')
def debug_session():
    from flask import session
    return str(dict(session))

@app.route('/logout')
def logout():

    logout_url = (
        f"{os.getenv('KEYCLOAK_SERVER')}"
        f"/realms/{os.getenv('KEYCLOAK_REALM')}"
        f"/protocol/openid-connect/logout"
        f"?client_id={os.getenv('CLIENT_ID')}"
        f"&post_logout_redirect_uri=http://146.190.108.128/"
    )

    return redirect(logout_url)
    
if __name__ == "__main__":
    app.run()