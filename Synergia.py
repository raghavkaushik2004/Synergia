import PySimpleGUI as sg
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build as build_calendar
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import webbrowser
import datetime
import os.path
import calendar
import subprocess
import time
import threading 
from PIL import Image, ImageTk
from io import BytesIO
import requests
import datetime

# Spotify API credentials
SPOTIFY_CLIENT_ID = '480508544b3d4621bb22064ff2174374'
SPOTIFY_CLIENT_SECRET = 'cac951ef201f4bc9b99c990fb8e9fe08'
SPOTIFY_REDIRECT_URI = 'http://localhost:5000/callback'  # Valid redirect URI for local development

# Google Calendar API credentials
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_spotify():
    sp_oauth = SpotifyOAuth(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI,
                            scope='user-read-playback-state user-modify-playback-state playlist-read-private')
    token_info = sp_oauth.get_access_token()

    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        webbrowser.open(auth_url)
        return None

    return spotipy.Spotify(auth=token_info['access_token'])

def authenticate_google_calendar():
    creds = None

    if os.path.exists('calendar_token.json'):
        creds = Credentials.from_authorized_user_file('calendar_token.json')

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                './client_secret_842294873082-obs81j2v0okr85j2ddpnirp1u5qn4prt.apps.googleusercontent.com.json', GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)

        with open('calendar_token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

scopes = "user-library-read user-read-playback-state user-modify-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET, redirect_uri=SPOTIFY_REDIRECT_URI, scope=scopes))

# Fetch user's playlists
user_playlists = sp.current_user_playlists()
playlist_names = [playlist['name'] for playlist in user_playlists['items']]

def list_spotify_playlists(spotify):
    playlists = spotify.current_user_playlists()
    return [playlist['name'] for playlist in playlists['items']]

def play_spotify_playlist(spotify, playlist_name):
    playlists = spotify.current_user_playlists()
    playlist_id = None

    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            playlist_id = playlist['id']
            break

    if playlist_id:
        tracks = spotify.playlist_tracks(playlist_id)
        if tracks['items']:
            track_uri = tracks['items'][0]['track']['uri']
            spotify.start_playback(uris=[track_uri])

def create_calendar_popup(current_day):
    # Show calendar of the current month and highlight the current date
    now = datetime.datetime.now()
    year = now.year
    month = now.month

    cal = calendar.monthcalendar(year, month)

    # Add formatting to highlight the current date
    layout = [[sg.Text(f'{calendar.month_name[month]} {year}', font=('Helvetica', 14))]]

    for week in cal:
        formatted_week = []
        for day in week:
            if day == 0:
                formatted_week.append(sg.Text('', size=(3, 2)))
            elif day == current_day:
                formatted_week.append(sg.Text(f'{day}', size=(3, 2), background_color='#001F3F', text_color='white'))
            else:
                formatted_week.append(sg.Text(f'{day}', size=(3, 2)))

        layout.append(formatted_week)

    layout.append([sg.Button('Close')])

    return sg.Window('Calendar View', layout, keep_on_top=True, finalize=True)

def execute_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            check=True
        )
        output = result.stdout
        return output
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"
def play_next_track():
    while True:
        current_track = sp.current_playback()
        if current_track is not None and not current_track['is_playing']:
            print("playing next track")
            sp.next_track()
        time.sleep(1)
todo_items=[]
def main():
    # Authenticate with Spotify
    spotify = authenticate_spotify()

    if not spotify:
        sg.popup('Please authorize Spotify access in the browser window.')
        return

    # Authenticate with Google Calendar
    calendar_credentials = authenticate_google_calendar()
    calendar_service = build_calendar('calendar', 'v3', credentials=calendar_credentials)

    # Layout for PySimpleGUI window
    layout = [
        [sg.Column([
            [sg.Text('Spotify ', font=('Helvetica', 16))],
            [sg.Text('Playlist:')],
            [sg.Listbox(values=playlist_names, size=(40, 10), key='-PLAYLISTS-', enable_events=True)],
            [sg.Button('<<<', key='-PREVIOUS_BUTTON-'),sg.Button('|>', key='-PLAY_BUTTON-'),sg.Button('||', key='-PAUSE_BUTTON-'),sg.Button('>>', key='-NEXT_BUTTON-')],[sg.Text('Currently Playing: ', key='-CURRENTLY_PLAYING-')],
            [sg.Image(key='-IMAGE-', size=(300, 300))],
        ], element_justification='center'),
        sg.VerticalSeparator(pad=None),  
        sg.Column([
            [sg.Text('Shell   ', font=('Helvetica', 16)),sg.Text(font=("Helvetica", 14), key="-TIME-")],
            [sg.Text("Enter a shell command:")],
            [sg.InputText(key="-COMMAND-",size=(20, 1))],
            [sg.Button("Execute"), sg.Button("Clear Screen")],
            [sg.Text("Output:", pad=(20, 0))],
            [sg.Output(size=(40, 10), key="-OUTPUT-")],
            [sg.Text('Tasks', font=('Helvetica', 18), justification='center')],
            [sg.InputText('', key='-TASK-', size=(20, 1)), sg.Button('Add', key='-ADD-'),sg.Button('Delete', key='-DELETE-')],
            [sg.Listbox(values=todo_items, size=(40, 10), key='-LIST-', enable_events=True)],
            #[sg.Button('To-Do List', key='-OPEN_TODO-',button_color='#856A5D'),sg.Button('CLI',button_color='#856A5D')],
            
            [sg.Text('Google Calendar', font=('Helvetica', 16))],
            [sg.Button('Calendar Events', key='-LIST_EVENTS-')],
            [sg.Button('Calendar', key='-SHOW_CALENDAR-',)],
        ], element_justification='center')],
    ]

    window = sg.Window('Multitasker', layout, finalize=True)

    calendar_popup = None
    todo_popup = None
    #todo_items = []
    cli_popup = None
    i=0
    running = False
    thread = None
    while True:
        event, values = window.read()
        #i=0;
        if event == sg.WIN_CLOSED:
            running = False
            break
        elif event == '-PLAY_BUTTON-':
            selected_playlist = values['-PLAYLISTS-'][0]
            tracks = sp.playlist_tracks(user_playlists['items'][playlist_names.index(selected_playlist)]['id'])
            if tracks['items']:
                track_uri = tracks['items'][0]['track']['uri']
                sp.start_playback(uris=[track_uri])
                '''if not running and thread is None:
                running = True
                # Start the thread to check for next track
                thread = threading.Thread(target=play_next_track)
                thread.start()'''
        
        elif event == '-PAUSE_BUTTON-':
            running = False
            sp.pause_playback()
        elif event == '-PREVIOUS_BUTTON-':
            i-=1
            if tracks['items'] and i>=0 and i<len(tracks['items']):
                prev_track_uri = tracks['items'][i]['track']['uri']
                sp.start_playback(uris = [prev_track_uri])
                sg.popup(f"Playing next track: {tracks['items'][i]['track']['name']}")
        elif event == '-NEXT_BUTTON-':
            # Check if there are tracks in the playlist
            i+=1
            if tracks['items'] and i<len(tracks['items']):
                # Get the URI of the next track in the playlist
                next_track_uri = tracks['items'][i]['track']['uri']

                # Start playback of the next track in the playlist
                sp.start_playback(uris=[next_track_uri])
                sg.popup(f"Playing next track: {tracks['items'][i]['track']['name']}")
            '''        elif event == '-OPEN_TODO-':
            if todo_popup:
                todo_popup.close()
            todo_popup = create_todo_popup(todo_list)'''
        elif event == '-ADD-':
            new_task = values['-TASK-']
            if new_task:
                todo_items.append(new_task)
                window['-LIST-'].update(values=todo_items)
                window['-TASK-'].update('')
        elif event == '-DELETE-':
            selected_task = values['-LIST-']
            if selected_task:
                todo_items.remove(selected_task[0])
                window['-LIST-'].update(values=todo_items)
        elif event == '-SHOW_CALENDAR-':
            # Show calendar of the current month and highlight the current date
            if calendar_popup:
                calendar_popup.close()
            current_day = datetime.datetime.now().day
            calendar_popup = create_calendar_popup(current_day)
        elif event == 'Close':
            if calendar_popup:
                calendar_popup.close()  
            '''        elif event == 'Show CLI':
            cli_popup = create_cli_popup()'''
            
        if event == "Execute":
            command = values["-COMMAND-"]
            output = execute_command(command)
            print(output)
        if event == "Clear Screen":
            window["-OUTPUT-"].update("")
            '''elif event == 'Close CLI':
            cli_popup.close()
            if cli_popup:
                cli_popup.close()
                cli_popup = None'''

        current_track = sp.current_playback()
        if current_track is not None and current_track['is_playing']:
            currently_playing_text = f"Currently Playing: {current_track['item']['name']} by {current_track['item']['artists'][0]['name']}"
            window['-CURRENTLY_PLAYING-'].update(currently_playing_text)
        else:
            window['-CURRENTLY_PLAYING-'].update("Currently Playing: Nothing")
        track_info = sp.current_playback()

        if track_info and 'item' in track_info:
            track_name = track_info['item']['name']
            album_name = track_info['item']['album']['name']
            album_cover_url = track_info['item']['album']['images'][0]['url']

            # Fetch the album cover image
            response = requests.get(album_cover_url)
            image_bytes = BytesIO(response.content)
            album_cover_image = Image.open(image_bytes)
            album_cover_image.thumbnail((300, 300))

            # Update the PySimpleGUI window with the album cover
            window['-IMAGE-'].update(data=ImageTk.PhotoImage(album_cover_image))
        current_time = datetime.datetime.now().strftime("%H:%M")
        window["-TIME-"].update(current_time)
    window.close()

if __name__ == '__main__':
    main()
