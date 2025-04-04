import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Define Gmail & Calendar Scope
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar.events"
]

def authenticate_gmail():
    """ Authenticate user with Google OAuth for Gmail & Calendar """
    creds = None
    
    # Pehle se token.pickle file hai to load karo
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    
    # Token invalid ya expire ho gaya to refresh ya naya lo
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=8000)

        # Token save karo
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    
    return creds

if __name__ == "__main__":
    creds = authenticate_gmail()
    if creds:
        print(" Authentication Successful!")
    else:
        print(" Authentication Failed!")