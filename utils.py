#region Imports
import os
import time
import threading
import urllib.request
import requests
import re
import string
import socket
import traceback
from ffpyplayer.player import MediaPlayer
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import pafy
from pynotifier import Notification
import tqdm
import fuzzy_recs
import math
#endregion

#region Global Variables
global selected

global search_dict
search_dict = {}
search_dict ['playing_playlist'] = []
search_dict ['search_type'] = None

global autoplay
autoplay = True

vol = 100

prev_search = None

global prev_track
prev_track = None

global spot
spot = spotipy.Spotify(client_credentials_manager = SpotifyClientCredentials('5af907e805114b54ad674b1765447cf4', '6cc582cd14894babad8fc9043ae7a982'))

global recommendations
recommendations = []
recommendations.append('placeholder')

global queue
global now_playing
queue = []
now_playing = []
now_playing.append('placeholder')

global status_dir
status_dir = {}

global spotipy_dir
spotipy_dir = os.path.join(os.path.expanduser('~'), 'SpotiPy')
queue_dir = os.path.join(os.path.expanduser('~'), 'queue')
music_dir = os.path.join(os.path.expanduser('~'), 'music')
#endregion
def centre(string, length, character = " "):
    return character * int((length - len(string)) / 2) + string + character * math.ceil((length - len(string)) / 2)

def make_table(rows, labels = None, centered = False):
    Horizontal = "─"
    Vertical = "│"
    Down_Right = "┌"
    Down_Left = "┐"
    Up_Right = "└"
    Up_Left = "┘"
    Vertical_Right = "├"
    Vertical_Left = "┤"
    Down_Horizontal = "┬"
    Up_Horizontal = "┴"
    Vertical_Horizontal = "┼"

    curve_down_right = "╭"
    curve_down_left = "╮"
    curve_up_right = "╰"
    curve_up_left = "╯"
    
    number_of_rows = len(rows)
    number_of_columns = len(rows[0])

    max_text = []
    for i in range(number_of_columns):
        max_text.append(max([len(str(x[i])) for x in rows] + [len(str(labels[i])) if labels else 0]) + 10)

    frame = []
    frame.append(curve_down_right + "".join(["─" * (x + 2) + Down_Horizontal for x in max_text])[:-1] + curve_down_left)

    if labels:
        if centered:
            frame.append(Vertical + "".join([" " + centre(str(value), max_text[index]) + " " + Vertical for index, value in enumerate(labels)]))
        else:
            frame.append(Vertical + "".join([" " + str(value) + " " * (max_text[index] - len(str(value)) + 1) + Vertical for index, value in enumerate(labels)]))
        frame.append(Vertical_Right + "".join(["─" * (x + 2) + Vertical_Horizontal for x in max_text])[:-1] + Vertical_Left)

    for i in range(number_of_rows):
        if centered:
            frame.append(Vertical + "".join([" " + centre(str(value), max_text[index]) + " " + Vertical for index, value in enumerate(rows[i])]))
        else:
            frame.append(Vertical + "".join([" " + str(value) + " " * (max_text[index] - len(str(value)) + 1) + Vertical for index, value in enumerate(rows[i])]))

    frame.append(curve_up_right + "".join(["─" * (x + 2) + Up_Horizontal for x in max_text])[:-1] + curve_up_left)
    
    return "\n".join(frame)

#region Music Functions
def get_music(search_term, save_as, out_dir, sleep_val = 0, part = True):
	alpha_list = list(string.printable)[: -6]
	alpha_list.remove('/')
	alpha_list.remove('\\')
	alpha_list.remove('"')
	alpha_list.append(' ')

	filter_search_term = ''.join(
	    [char for char in search_term if char in alpha_list])

	try:
		status_dir[search_term] = 'downloading'

		time.sleep(sleep_val)

		if save_as == None:
			save_as = search_term

		spotipy_dir = os.path.join(os.path.expanduser('~'), 'SpotiPy')

		music_dir = os.path.join(spotipy_dir, out_dir)
		download_path = os.path.join(music_dir, search_term)
		formatted_search_term = filter_search_term.replace(' ', '+')

		html = urllib.request.urlopen(
		    "https://www.youtube.com/results?search_query=" + formatted_search_term)
		video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())

		yt_url_thingy = 'https://www.youtube.com/watch?v='
		le_url = yt_url_thingy + video_ids[0]

		song = pafy.new(le_url)
		best = song.getbestaudio()
		best.download(filepath=f"{formatted_search_term}{best.extension}")

		status_dir[search_term] = 'downloaded'
	except Exception as e:
		status_dir[search_term] = 'downloaded'
		print('errorr in downloading')
		#traceback.print_exc()
		print(e)
		pass
#endregion
#region Autoplay Functions
def parse_opts(command):
	#takes in variable command and parses for autoplay
	no_auto = False
	if '--no-auto' in command:
		no_auto = True
		command = command.split('--no-auto')
		command.remove('')
		song = command [0].strip()
	else:	song = command

	search_dict ['playing_from'] = ['track', song]
 
	if len(search_dict) != 0:
		try:
			song = int(song)
			if search_dict ['search_type'] in ['artists', 'albums', 'playlists']:
				 if (search_dict ['playing_playlist']) == 0:	song = search_dict ['loaded_playlist'] [song]
				 else:	song = search_dict ['playing_playlist'] [song]
			else:
				song = search_dict ['search_content'] [song]
		except:
			pass

	return song, no_auto

def toggle_autoplay():
	global autoplay
	if autoplay == True:
		autoplay = False
		if len(recommendations) == 0:	clear_recs()
		recommendations.clear()
	elif autoplay == False:	autoplay = True

def clear_recs():
	for song in recommendations:
		thread = threading.Thread(target = watch_thread, args = (song, ))
		thread.start()

def watch_thread(song):
	while song != 'placeholder' and (song in list(status_dir.keys())):
		if status_dir [song] == 'downloaded':
			time.sleep(1)
			if song in list(status_dir.keys()):
				del status_dir[song]
			break
	time.sleep(5)

def manage_recommendations():
	global prev_change_flag
	prev_change_flag = False

	while True:
		if (len(recommendations) == 0 or prev_change_flag == True) and autoplay and prev_track != None:
			print('\r--- updating recommendations \n>>> ', end = ' ')
			time.sleep(0.8)
			if prev_change_flag == True:
				clear_recs()
			recommendations.clear()
			prev_change_flag = False
			get_recs(prev_track)
		time.sleep(1.75)

def handle_autoplay():
	while True:
		if len(now_playing) == 0 and len(queue) == 0 and prev_track != None and autoplay and len(recommendations) != 0:
			now_playing.append(recommendations[0])
			# status_dir [recommendations [0]] = 'downloaded'
			recommendations.remove(recommendations[0])
		time.sleep(1.75)

def get_recs(name):

	global prev_search

	spot = spotipy.Spotify(client_credentials_manager = SpotifyClientCredentials('5af907e805114b54ad674b1765447cf4', '6cc582cd14894babad8fc9043ae7a982'))

	track_results = spot.search(name, type = 'track')

	items = track_results['tracks']['items']

	def get_genre_from_artist(artists):
		genres = []
		for artist in artists:
			search_result = spot.search(artist, type = 'artist')
			artist = search_result ['artists'] ['items'] [0]
			genres += artist ['genres']
		return list(set(genres))

	if len(items) > 0:
		prev_search = name
		track = items[0]
		artists = [dict ['name'] for dict in track ['artists']]
		seed_genres = get_genre_from_artist(artists)
		for _ in range(4):
			#track_results['tracks']['items'][0]['artists'][0]['id']
			results = spot.recommendations(seed_tracks = [track['id']], seed_artists = [dict ['id'] for dict in track ['artists']] [ : 1], seed_genres = seed_genres [ : 1], limit = 1)
			for track in results['tracks']:
				track_name = f"{track['name']} - {track['artists'][0]['name']}"
				recommendations.append(track_name)
	elif prev_search != None:
		get_recs(prev_search)
	else:
		for _ in range(3):
			recommendations.append(fuzzy_recs.main())

#endregion
#region Metadata Functions
def put_notification(song):
	image_urls, album_name, artists, track = get_metadata(song)
	# formatted_track = track.replace(' ', '_')
	if image_urls is not None:
		print('\r---image_urls is not None \n>>> ', end = ' ')
		get_image(image_urls['mid'], track)
		image_path = os.path.join(spotipy_dir, 'cover_art_dir', f'{track}.png')
	else:
		image_path = None

	Notification(
    title = track,
    description = f'{artists}\nfrom album {album_name}',		# On Windows .ico is required, on Linux - .png
	icon_path = image_path,
    duration = 5,									 			# Duration in seconds
    urgency = 'normal'
	).send()

def get_image(image_url, song):
	image_data = requests.get(image_url)
	with open(os.path.join(spotipy_dir, 'cover_art_dir', f'{song}.png'), 'wb') as le_image:
		le_image.write(image_data.content)

def get_metadata(song_name):
	try:
		search_str = song_name

		spot = spotipy.Spotify(client_credentials_manager = SpotifyClientCredentials('5af907e805114b54ad674b1765447cf4', '6cc582cd14894babad8fc9043ae7a982'))

		track = spot.search(search_str)

		quality = ['high', 'mid', 'low']
		counter = 0
		images = {}

		for image_dict in track['tracks']['items'][0]['album']['images']:

			images[quality[counter]] = image_dict['url']
			counter += 1

		album_name = track['tracks']['items'][0]['album']['name']

		artists = []
		artists_list = track['tracks']['items'][0]['artists']
		for dictionary in artists_list:
			artists.append(dictionary['name'])
		artists = ' & '.join(artists)

		track_name = track['tracks']['items'][0]['name']

		if os.name == 'nt':
			images = None

		return images, album_name, artists, track_name
	except Exception:
		return None, None, song_name.split(' ')[0], song_name
#endregion
#region Management

def update_queue():
	for song in queue:
		if os.path.exists(os.path.join(queue_dir, song + '.wav')) == False and os.path.exists(os.path.join(music_dir, song + '.wav')) == False:
			threading._start_new_thread(get_music, (song, None, 'queue', 0, True, ))
		if os.path.exists(os.path.join(music_dir, song + 'wav')):
			print('\r--- song already downloaded, so not doing it again \n>>> ', end = ' ')
			status_dir[song] = 'downloaded'


#endregion
