from flask import Flask, request, url_for, render_template, redirect, session, flash
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
import time
import pandas as pd
from os import urandom


from spotify_client import *


app = Flask(__name__)
app.secret_key = urandom(64)                        # Key used to sign session cookies

# A session cookie is used to store data about the user's session.
# This cookie is signed with the secret key, so that it can't be tampered with.
# The cookie is set on the client, and the client sends it back to the server with each request.
# The server can then use the data stored in the cookie to identify the user.
# The index page will force the user force the user to authorize Spotify to allow us to access their data.

app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session' # Name of session cookie
TOKEN_INFO = 'token_info'     # TOKEN_INFO is a key in the session dictionary that stores the token information. It will contain the access token, refresh token,
                              # expiration time, and token type. The token information is stored in a dictionary.
 
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

# shellydey7
# ShellyDey7star
@app.route('/authorize')
def authorize():
    # Authentication flow is off, we are spotify OAuth token no way to specify the user. 

    session.clear()                                    # Clear the session
    sp_oauth = create_spotify_oauth()                  # Create a SpotifyOAuth object
    code = request.args.get('code')                    # Get the authorization code from the request
    token_info = sp_oauth.get_access_token(code)       # Get the access token from the authorization code
    session[TOKEN_INFO] = token_info                   # Store the token information in the session cookie
    session["signed_in"] = True                        # Set the signed in boolean to True
    # Access user name data from access token
    token = token_info['access_token']
    sp = spotipy.Spotify(auth=token)
    user = sp.current_user()
    sp = spotipy.client.Spotify(auth=token_info.get('access_token'))  # Create a Spotify client using the access token
    msg = "You have successfully signed in as {}!".format(sp.current_user()['display_name'])
    flash(msg, 'good-signin')
    return redirect(url_for('myaccount'))              # Redirect the user to the get tracks page


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
# @app.route('/recTracks')
# def get_rec_tracks():
#     session['token_info'], token_authorized = get_token()                     # Get the token information from the session cookie by calling the get_token function below
#     session.modified = True                                                   # Indicate that the session data has been modified
#     if not token_authorized:                                                  # If the token is not valid
#         return redirect('/')                                                  # Redirect the user to the index page
#     sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))  # Create a Spotify object using the access token stored in the session
#     results = []
#     iter = 0
#     # Iterate through the user's saved tracks
#     while True:
#         offset = iter * 50                                                        # The offset is used to get the next 50 tracks
#         iter += 1                                                                 # Increment the iterator
#         curGroup = sp.current_user_saved_tracks(limit=50, offset=offset)['items'] # Get the next 50 tracks
#         for idx, item in enumerate(curGroup):                                     # Iterate through the retrieved tracks (50 tracks total in curGroup)
#             track = item['track']                                                 # Get the track from the item
#             val = track['name'] + " - " + track['artists'][0]['name']             # Get the track name and artist name, format: "Track Name - Artist Name"
#             results += [val]                                                      # Add the track name and artist name formated values to the results list
#         if (len(curGroup) < 50):   # If the length of the current group is less than 50, we have reached the end of the user's saved tracks
#             break                  # Break out of the while loop
    
#     # Convert the results list to a pandas dataframe so that we can display it in a table
#     df = pd.DataFrame(results, columns=["song names"])  # Create a pandas dataframe with the results list
#     df.to_csv('songs.csv', index=False)                 # Save the dataframe to a csv file
#     return "done"                                       # Return "done" to indicate that the function has finished

"""
My Account: Endpoint for getting a sample of a user's listening history. This will get the user's listening history and display it in a tables.
"""
@app.route('/myaccount')
def myaccount():
    session['token_info'], token_authorized = get_token()                     # Get the token information from the session cookie by calling the get_token function below
    session.modified = True                                                   # Indicate that the session data has been modified
    if not token_authorized:                                                  # If the token is not valid
        return redirect('/')                                                  # Redirect the user to the index page
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))  # Create a Spotify object using the access token stored in the session

    # Get the user's 15 most recently played tracks and their images
    results = []
    recent_track_images_urls = []
    curGroup = sp.current_user_recently_played(limit=15)['items']             # Get the next 15 tracks
    for idx, item in enumerate(curGroup):                                     # Iterate through the retrieved tracks (50 tracks total in curGroup)
        track = item['track']                                                 # Get the track from the item
        val = track['name'] + " - " + track['artists'][0]['name']             # Get the track name and artist name, format: "Track Name - Artist Name"
        results += [val]                                                      # Add the track name and artist name formated values to the results list
        recent_track_images_urls += [track['album']['images'][0]['url']]      # Add the track's image url to the list of track image urls
    df = pd.DataFrame(results, columns=["Song Name"])                         # Create a pandas dataframe with the results list
    df_to_html = df.to_html(classes='data', header="true").replace('<th>','<th style = "color:white; text-align:center">')
    recent_tracks_table = [df_to_html]                                        # Convert the dataframe to an HTML table

    # Get the user's 15 top artists and their images 
    results = []
    artist_image_urls = []
    genre = []
    artist_popularity = []
    curGroup = sp.current_user_top_artists(limit=15)['items']                 # Get the next 15 tracks
    for idx, item in enumerate(curGroup):                                     # Iterate through the retrieved tracks (50 tracks total in curGroup)
        artist = item['name']                                                 # Get the track from the item
        results += [artist]                                                   # Add the track name and artist name formated values to the results list
        artist_image_urls += [item['images'][0]['url']]
        genre += [item['genres']]
        artist_popularity += [item['popularity']]
    df = pd.DataFrame(results, columns=["Artist Name"])                       # Create a pandas dataframe with the results list
    # Convert the list of genres to a string
    genre = [', '.join(map(str, l)) for l in genre]                          # Convert the list of genres to a string
    df['Genre'] = genre
    df['Spotify Popularity*'] = artist_popularity
    df_to_html = df.to_html(classes='data', header="true").replace('<th>','<th style = "color:white; text-align:center">')
    top_artists_table = [df_to_html]                                          # Convert the dataframe to an HTML table

    # Get the user's 15 top tracks, their images, their artists, the number of streams
    results = []
    album_images_urls = []
    artists = []
    track_play_counts = []
    curGroup = sp.current_user_top_tracks(limit=15)['items']                  # Get the next 15 tracks
    for idx, item in enumerate(curGroup):                                     # Iterate through the retrieved tracks (50 tracks total in curGroup)
        track = item['name']                                                  # Get the track from the item
        results += [track]                                                    # Add the track name and artist name formated values to the results list
        album_images_urls += [item['album']['images'][0]['url']]
        artists += [item['artists'][0]['name']]
        track_play_counts += [item['popularity']]
    df = pd.DataFrame(results, columns=["Song Name"])                         # Create a pandas dataframe with the results list
    df['Artist'] = artists
    df['Spotify Popularity*'] = track_play_counts
    df_to_html = df.to_html(classes='data', header="true").replace('<th>','<th style = "color:white; text-align:center">')
    top_tracks_table = [df_to_html]                                           # Convert the dataframe to an HTML table

    # Get the currently playing track from the current user
    results = []
    # curSong = sp.current_user_playing_track()
    # Access the name of the current song
    curSong = False
    album_name = False
    album_image_url = False
    cur_song_info_array = False
    if sp.current_user_playing_track() is not None:
        curSong = sp.current_user_playing_track()['item']['name']
        album_name = sp.current_user_playing_track()['item']['album']['name']
        album_image_url = sp.current_user_playing_track()['item']['album']['images'][0]['url']
        cur_song_info_array = [curSong, album_name, album_image_url]
    

    return render_template('myaccount.html', cur_song_info_array=cur_song_info_array, current_recent_tracks_table=recent_tracks_table, recent_track_images_urls=recent_track_images_urls, top_artists_table=top_artists_table, artist_image_urls=artist_image_urls ,top_tracks_table=top_tracks_table, album_images_urls=album_images_urls, username=sp.current_user()['display_name'], profile_image_url=sp.current_user()['images'][0]['url'] )

"""
GET TRACKS: Endpoint for getting the user's saved tracks. This will get the user's saved tracks and display them in a table.
"""
@app.route('/recTracks')
def get_current_rec_tracks():
    session['token_info'], token_authorized = get_token()                     # Get the token information from the session cookie by calling the get_token function below
    session.modified = True                                                   # Indicate that the session data has been modified
    if not token_authorized:                                                  # If the token is not valid
        return redirect('/')                                                  # Redirect the user to the index page
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))  # Create a Spotify object using the access token stored in the session
    artists = []
    curGroup = sp.current_user_top_tracks(limit=15)['items']                  # Current group of top tracks for the current user
    for idx, item in enumerate(curGroup):
        # artists += [item['artists'][0]['name']]
        artists += [item['artists'][0]['id']]
    genres = []
    # curGroup = sp.current_user_top_genres(limit=50)['items']
    genreSeeds = sp.recommendation_genre_seeds()
    # for idx, item in enumerate(curGroup):
    #     genres += [item['genres'][0]['name']]

    print("Artists length: ", len(artists), " Top Artists: ", artists)
    print("Genres length: ", len(genreSeeds), " Top Artists: ", genreSeeds)




    return render_template('mytracks.html')                                       # Return "done" to indicate that the function has finished

"""
GET_TOKEN: This function will check if the token is valid and get a new token if it has expired. It will return the token information and a boolean 
indicating if the token is valid.
"""
def get_token():
    token_valid = False                                      # Boolean to indicate if the token is valid (i.e. not expired)
    token_info = session.get(TOKEN_INFO, {})               # Get the token information from the session cookie

    # Checking if the session already has a token stored
    if not (session.get(TOKEN_INFO, False)):               # If there is no token in the session
        token_valid = False                                  # Set the token valid boolean to False
        return token_info, token_valid                       # Return the token information and the token valid boolean

    # Checking if token has expired
    now = int(time.time())                                                      # Get the current time
    is_token_expired = session.get(TOKEN_INFO).get('expires_at') - now < 60   # Check if the token will expire within the next 60 seconds 
                                                                                # is_token_expired will be True if the token will expired, and false otherwise
    # Refreshing token if it has expired
    if (is_token_expired):                                                                          # If the token has expired                                            
        sp_oauth = create_spotify_oauth()                                                           # Create a SpotifyOAuth object                     
        token_info = sp_oauth.refresh_access_token(session.get(TOKEN_INFO).get('refresh_token'))  # Refresh the access token by passing the refresh token stored in the session

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
            scope="user-library-read user-read-recently-played user-read-private user-top-read user-read-currently-playing")

if __name__ == '__main__':
    app.run(debug=True)