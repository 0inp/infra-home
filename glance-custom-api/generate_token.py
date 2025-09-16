import os

from google_auth_oauthlib.flow import InstalledAppFlow

# This scope allows reading YouTube data.
YOUTUBE_SCOPES: list[str] = ["https://www.googleapis.com/auth/youtube.readonly"]
TOKEN_FILE: str = "credentials/token.json"
CLIENT_SECRET_FILE: str = "credentials/client_secret.json"


def main():
    """Runs the OAuth 2.0 flow to generate a token file."""
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"Error: Client secret file not found at {CLIENT_SECRET_FILE}")
        print(
            "Please download your client secret from the Google Cloud Console and place it there."
        )
        return

    # Create a flow instance to manage the OAuth 2.0 Authorization Flow
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, YOUTUBE_SCOPES)

    # Run the flow using a local server.
    creds = flow.run_local_server(port=9090)

    # Save the credentials for the next run
    with open(TOKEN_FILE, "w") as token:
        token.write(creds.to_json())

    print(f"Token saved to {TOKEN_FILE}")
    print("You can now upload this file to your server.")


if __name__ == "__main__":
    main()
