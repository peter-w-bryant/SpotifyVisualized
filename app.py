from flask import Flask, request, url_for, render_template, redirect, session, flash
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import pandas as pd

from spotify_client import *


app = Flask(__name__)
app.secret_key = 'super_secret_key'                         # Key used to sign session cookies

# A session cookie is used to store data about the user's session.
# This cookie is signed with the secret key, so that it can't be tampered with.
# The cookie is set on the client, and the client sends it back to the server with each request.
# The server can then use the data stored in the cookie to identify the user.
# The index page will force the user force the user to authorize Spotify to allow us to access their data.

app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session' # Name of session cookie
TOKEN_INFO = 'token_info'     # TOKEN_INFO is a key in the session dictionary that stores the token information. It will contain the access token, refresh token,
                              # expiration time, and token type. The token information is stored in a dictionary.
 
app = Flask(__name__) # Instantiate the flask app
 
app.secret_key = 'not-so-secret-key'
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'

"""
HOME/INDEX PAGE: This page will welcome the user and prompt them to authorize Spotify to allow us to access their data.
"""
@app.route('/')
def index():
    if request.method == 'POST':
        return redirect(url_for('login'))
    return render_template('index.html')

"""
LOGIN: Endpoint for the login page. This will redirect the user to sign in with Spotify at the authorization URL.
"""
@app.route('/login')
def login():
    sp_oauth = create_spotify_oauth()        # Create a SpotifyOAuth object
    auth_url = sp_oauth.get_authorize_url()  # Get the authorization URL, the user will be redirected here to authorize the app by signing in
    return redirect(auth_url)                # Redirect the user to the authorization URL

"""
AUTHORIZE: Endpoint is where the user will be redirected to after they have logged in with Spotify. Now that the user has authorized the app,
we can get the access token from the authorization code and store it in the session. We will then redirect the user to the get tracks page.
"""
@app.route('/authorize')
def authorize():
    sp_oauth = create_spotify_oauth()            # Create a SpotifyOAuth object
    session.clear()                              # Clear the session data
    code = request.args.get('code')              # Get the authorization code from the request
    token_info = sp_oauth.get_access_token(code) # Get the access token from the authorization code
    session["token_info"] = token_info           # Store the token information in the session cookie
    session["signed_in"] = True                  # Set the signed in boolean to True
    return redirect(url_for('myaccount'))       # Redirect the user to the get tracks page


"""
LOGOUT: Endpoint for logging out. This will clear the session data and redirect the user to the index page.
"""
@app.route('/logout') 
def logout():
    for key in list(session.keys()):            # Iterate through the session dictionary
        session.pop(key)                        # Remove each key from the session dictionary
    session.clear()
    return redirect('/')                        # Redirect the user to the index page

"""
GET TRACKS: Endpoint for getting the user's saved tracks. This will get the user's saved tracks and display them in a table.
"""
@app.route('/getTracks')
def get_all_tracks():
    session['token_info'], token_authorized = get_token()                     # Get the token information from the session cookie by calling the get_token function below
    session.modified = True                                                   # Indicate that the session data has been modified
    if not token_authorized:                                                  # If the token is not valid
        return redirect('/')                                                  # Redirect the user to the index page
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))  # Create a Spotify object using the access token stored in the session
    results = []
    iter = 0
    # Iterate through the user's saved tracks
    while True:
        offset = iter * 50                                                        # The offset is used to get the next 50 tracks
        iter += 1                                                                 # Increment the iterator
        curGroup = sp.current_user_saved_tracks(limit=50, offset=offset)['items'] # Get the next 50 tracks
        for idx, item in enumerate(curGroup):                                     # Iterate through the retrieved tracks (50 tracks total in curGroup)
            track = item['track']                                                 # Get the track from the item
            val = track['name'] + " - " + track['artists'][0]['name']             # Get the track name and artist name, format: "Track Name - Artist Name"
            results += [val]                                                      # Add the track name and artist name formated values to the results list
        if (len(curGroup) < 50):   # If the length of the current group is less than 50, we have reached the end of the user's saved tracks
            break                  # Break out of the while loop
    
    # Convert the results list to a pandas dataframe so that we can display it in a table
    df = pd.DataFrame(results, columns=["song names"])  # Create a pandas dataframe with the results list
    df.to_csv('songs.csv', index=False)                 # Save the dataframe to a csv file
    return "done"                                       # Return "done" to indicate that the function has finished

"""
GET TRACKS: Endpoint for getting the user's saved tracks. This will get the user's saved tracks and display them in a table.
"""
@app.route('/myaccount')
def myaccount():
    msg = "You have successfully signed in with your Spotify credentials!"
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))
    profile_info = sp.current_user()
    display_name = profile_info['display_name']
    profile_image_url = profile_info['images'][0]['url']
    print("TEST")
    print(profile_info)
    print(profile_image_url)
    print(display_name)
    return render_template('myaccount.html', msg=msg, display_name=display_name, profile_image_url=profile_image_url)


@app.route('/mytracks')
def mytracks():
    msg = "You have successfully signed in with your Spotify credentials!"
    session['token_info'], token_authorized = get_token()                     # Get the token information from the session cookie by calling the get_token function below
    session.modified = True                                                   # Indicate that the session data has been modified
    if not token_authorized:                                                  # If the token is not valid
        return redirect('/')                                                  # Redirect the user to the index page
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))  # Create a Spotify object using the access token stored in the session
    results = []
    iter = 0
    # Iterate through the user's saved tracks
    while True:
        offset = iter * 50                                                         # The offset is used to get the next 50 tracks
        iter += 1                                                                 # Increment the iterator
        curGroup = sp.current_user_saved_tracks(limit=50, offset=offset)['items']  # Get the next 50 tracks
        for idx, item in enumerate(curGroup):                                     # Iterate through the retrieved tracks (50 tracks total in curGroup)
            track = item['track']                                                 # Get the track from the item
            val = track['name'] + " - " + track['artists'][0]['name']             # Get the track name and artist name, format: "Track Name - Artist Name"
            results += [val]                                                      # Add the track name and artist name formated values to the results list
        if (len(curGroup) < 50):   # If the length of the current group is less than 50, we have reached the end of the user's saved tracks
            break                 # Break out of the while loop
    
    # Convert the results list to a pandas dataframe so that we can display it in a table
    df = pd.DataFrame(results, columns=["song names"])  # Create a pandas dataframe with the results list
    table = [df.to_html(classes='data', header="true")] # Convert the dataframe to an HTML table
    return render_template('mytracks.html', tables= table)                                       # Return "done" to indicate that the function has finished

"""
GET_TOKEN: This function will check if the token is valid and get a new token if it has expired. It will return the token information and a boolean 
indicating if the token is valid.
"""
def get_token():
    token_valid = False                                      # Boolean to indicate if the token is valid (i.e. not expired)
    token_info = session.get("token_info", {})               # Get the token information from the session cookie

    # Checking if the session already has a token stored
    if not (session.get('token_info', False)):               # If there is no token in the session
        token_valid = False                                  # Set the token valid boolean to False
        return token_info, token_valid                       # Return the token information and the token valid boolean

    # Checking if token has expired
    now = int(time.time())                                                      # Get the current time
    is_token_expired = session.get('token_info').get('expires_at') - now < 60   # Check if the token will expire within the next 60 seconds 
                                                                                # is_token_expired will be True if the token will expired, and false otherwise
    # Refreshing token if it has expired
    if (is_token_expired):                                                                          # If the token has expired                                            
        sp_oauth = create_spotify_oauth()                                                           # Create a SpotifyOAuth object                     
        token_info = sp_oauth.refresh_access_token(session.get('token_info').get('refresh_token'))  # Refresh the access token by passing the refresh token stored in the session

    # Return the token information and a boolean indicating if the token is valid
    token_valid = True                  # Set the token valid boolean to True 
    return token_info, token_valid      # Return the token information and the token valid boolean

"""
Function to create a SpotifyOAuth object. This object is used to authenticate the user with Spotify. The scope determines what data we can access.
In our case, we want the user-library-read scope, which allows us to read the user's saved tracks.
"""
def create_spotify_oauth():
    return SpotifyOAuth(
            client_id="9755ec99cb86450bb04ecd1a6547647a",
            client_secret="620e0bc86c0846929c83d61ec1fd92df", 
            redirect_uri=url_for('authorize', _external=True),
            scope="user-library-read")

if __name__ == '__main__':
    app.run(debug=True)