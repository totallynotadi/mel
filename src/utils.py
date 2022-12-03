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
from json import loads
from ffpyplayer.player import MediaPlayer
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import pafy
from pynotifier import Notification
import tqdm
import fuzzy_recs
import math
import melodine as melo
import youtube_dl
#endregion

#region Client Key Assignment
'''with open("client_keys.json", "r") as keys:
	
    client_keys = loads(keys.read())
    try:
        if client_keys["personal"]["CLIENT_ID"] and client_keys["personal"]["CLIENT_SECRET"]:
            CLIENT_ID = client_keys["personal"]["CLIENT_ID"]
            CLIENT_SECRET = client_keys["personal"]["CLIENT_SECRET"]
        else:
            CLIENT_ID = client_keys["public"]["CLIENT_ID"]
            CLIENT_SECRET = client_keys["public"]["CLIENT_SECRET"]
    except KeyError:    # In case the personal key is undefined in the json
        CLIENT_ID = client_keys["public"]["CLIENT_ID"]
        CLIENT_SECRET = client_keys["public"]["CLIENT_SECRET"]'''
melo.spotify.client.authorize()
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

global melodine_dir
melodine_dir = os.path.join(os.path.expanduser('~'), '.melodine')
queue_dir = os.path.join(os.path.expanduser('~'), 'queue')
music_dir = os.path.join(os.path.expanduser('~'), 'music')
#endregion
def centre(string, length, character = " "):
    return character * int((length - len(string)) / 2) + string + character * math.ceil((length - len(string)) / 2)

def make_table(rows, labels = None, centered = False):
    Vertical = "│"
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
def get_music(track, save_as, sleep_val = 0, part = True):
	'''alpha_list = list(string.printable)[: -6]
	alpha_list.remove('/')
	alpha_list.remove('\\')
	alpha_list.remove('"')
	alpha_list.append(' ')
	filter_search_term = ''.join(
		[char for char in search_term if char in alpha_list])'''

	try:
		ydl_opts = {
			'format': 'bestaudio/best',
			'postprocessors': [{
			'key': 'FFmpegExtractAudio',
			'preferredcodec': 'mp3',
			'preferredquality': '192',
			}],
			'quiet': 'true',
			'outtmpl': os.path.join(os.path.expanduser('~'), 'Music', save_as + '.mp3')
		}
		with youtube_dl.YoutubeDL(ydl_opts) as ydl:
			ydl.download([track.url])
	except Exception as e:
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
	else:	
		song = command

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
			add_req()
		time.sleep(1.75)

def add_req():
	queue.append(recommendations[0])
	recommendations.remove(recommendations[0])
def get_recs(track):
	for _ in range(4):
		#track_results['tracks']['items'][0]['artists'][0]['id']
		results = track.get_recommendations()
		for song in results[1:]:
			track_name = f"{song.name} - {song.artists}"
			recommendations.append(song.name)

#endregion
#region Metadata Functions
def put_notification(track):
	quality = ['high', 'mid', 'low']
	counter = 0
	images = {}
	album_name = track.album.name
	artists = []
	for artist in track.artists:
		artists.append(artist.name)
	artists = ' & '.join(artists)
	for image in track.images:
			images[quality[counter]] = image.url
			counter += 1
	
	# formatted_track = track.replace(' ', '_')
	if images is not None:
		get_image(images['high'], track)
		image_path = os.path.join(melodine_dir, 'cover_art_dir', f'{track}.png')
	else:
		image_path = None
		print("Image url is none")

	Notification(
    title = track.name,
    description = f'{artists}\nfrom album {album_name}',		# On Windows .ico is required, on Linux - .png
	icon_path = image_path,
    duration = 5,									 			# Duration in seconds
    urgency = 'normal'
	).send()
	f = open("History.txt", "a")
	f.write(f"{track.name} - {artists}\n")
	f.close()

def get_image(image_url, song):
	image_data = requests.get(image_url)
	with open(os.path.join(melodine_dir, 'cover_art_dir', f'{song}.png'), 'wb') as le_image:
		le_image.write(image_data.content)

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
