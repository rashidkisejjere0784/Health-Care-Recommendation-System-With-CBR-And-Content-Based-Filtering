from flask_mail import Message
from flask import current_app
import os
from dotenv import load_dotenv
import base64
from datetime import datetime, timedelta

load_dotenv()
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
HOST_NAME = os.environ.get('HOST_NAME')

def is_user_admin(id):
    return id == 1

def decode_token(token):
    try:
        decoded_payload = base64.b64decode(token.encode()).decode()
        print("heheh")
        print(decoded_payload)
        user_id, expiration, secret_key = decoded_payload.split(',')
        print(secret_key)
        # Check if the secret key matches
        if secret_key != JWT_SECRET_KEY:
            return None

        # Check if the token has expired
        if datetime.strptime(expiration, '%Y-%m-%d %H:%M:%S') < datetime.utcnow():
            return None

        return {'sub': user_id, 'expiration': expiration}
    except Exception as e:
        # Return None if decoding fails
        print(f"Error decoding token: {e}")
        return None

def create_access_token(user_id):
    expiration = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
    payload = f"{user_id},{expiration},{JWT_SECRET_KEY}"
    
    # Encode the payload using base64
    token = base64.b64encode(payload.encode()).decode()
    return token


def is_authenticated(User, session):
    if 'user_token' not in session:
        return False, False
    
    user_token = session['user_token']
    
    
    try:
        decoded_jwt = decode_token(user_token)
        user_id = int(decoded_jwt['sub'])
        
        user = User.query.filter_by(id=user_id).first()

        if user:
            is_auth = True
            is_admin = is_user_admin(user.id)
            return is_auth, is_admin
    except Exception as e:
        # Handle any errors that occur during token decoding
        current_app.logger.error(f"Token decoding failed: {e}")
        return False, False
    
    return False, False


def send_email(username, email, user, expires, mail, token):
    msg = Message(subject="Account Confirmation",
                  recipients=[email],
                  sender="rashid@pollicy.org",
                  body=f"Hello {username},\n\nThank you for registering! "
                       f"Please confirm your account using the following link: "
                       f"{HOST_NAME}/verify?token={token}\n\n"
                       f"This link will expire in {expires} minutes.\n\n"
                       "Best regards,\n Kisejjere Rashid")

    mail.send(msg)