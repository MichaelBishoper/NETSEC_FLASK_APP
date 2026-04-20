import os
import json
from flask import Flask, render_template, redirect, url_for, g, jsonify
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
    'OVERWRITE_REDIRECT_URI': f"{os.getenv("CALLBACK_URL")}",
})

oidc = OpenIDConnect(app)

# Routes

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/debug')
@oidc.require_login
def debug_token():
    all_info = oidc.user_getinfo(['openid'])
    return jsonify(all_info)

@app.route('/protected')
@oidc.require_login
def protected():
    user_info = oidc.user_getinfo(['groups'])
    user_groups = user_info.get('groups', [])
    
    if 'students' in user_groups:
        return redirect(url_for('student'))
    elif 'faculty' in user_groups:
        return redirect(url_for('faculty'))
    elif 'admins' in user_groups:
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('home'))

# @app.route('/student')
# def student():
#     user_info = oidc.user_getinfo(['preferred_username', 'name', 'email'])
#     return render_template('student.html')

# @app.route('/faculty')
# def faculty():
#     return render_template('faculty.html')

# @app.route('/admin')
# def admin():
#     return render_template('admin.html')

@app.route('/logout')
def logout():
    oidc.logout()
    return redirect('/')
    
if __name__ == "__main__":
    app.run()