#region Imports
import os 
import time
import threading
import urllib.request
import requests
import re
import string
import socket
import random_song

try:
	import ffpyplayer
except:
	os.system('pip install -r requirements.txt')
from ffpyplayer.player import MediaPlayer

from youtube_dl import YoutubeDL

from spotipy.oauth2 import SpotifyClientCredentials
import spotipy

from pynotifier import Notification
#endregion
# config stuff
#
# kill timer
# group listening related stuff
# user creds
#

# TO-DO
#
# handle exceptions well
# help command
# streaming opts
# direct play
# autoplay
# fix ico in notifs
# listen with frands
# play/search by genre/artist

#region Global Variables

#No idea wtf this exists help Adi
global prev_track
prev_track = None

#Change this to copy users credentials
global spot
spot = spotipy.Spotify(client_credentials_manager = SpotifyClientCredentials('5af907e805114b54ad674b1765447cf4', '6cc582cd14894babad8fc9043ae7a982'))

#Recommendations list
global recommendations
recommendations = []
recommendations.append('placeholder')

#Lists for the queue and the now playing song
global queue
global now_playing
queue = []
now_playing = []

global status_dir
status_dir = {}

#Code directory initialisation.
global spotipy_dir
spotipy_dir = os.path.join(os.path.expanduser('~'), 'SpotiPy')
if not os.path.exists(spotipy_dir):
	os.mkdir(spotipy_dir)
	os.mkdir(os.path.join(spotipy_dir, 'music'))
	os.mkdir(os.path.join(spotipy_dir, 'queue'))
	os.mkdir(os.path.join(spotipy_dir, 'cover_art_dir'))
	os.mkdir(os.path.join(spotipy_dir, 'playlists'))

#endregion

#region Functions
def socket_handler():
	SEPARATOR = '<SEPARATOR>'

	global BUFFER_SIZE
	BUFFER_SIZE = 512

	host = '18.116.67.97'
	#host = '192.168.43.164'
	port = 105001

	global client_socket
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	client_socket.connect((host, port))
	print("[+]connected")

	pass

#Command to skip song but currently broken. Do not use this command, breaks the script
'''def skip():
	player.set_mute(True)
	player.toggle_pause()
	player.seek(player.get_metadata() ['duration'] - 2)
	player.toggle_pause()
	time.sleep(2.2)
	player.set_mute(False)
'''
#Deletes song after playing
def watch_thread(song):
	song_path = os.path.join(queue_dir, song + '.wav')
	while True:
		if os.path.exists(song_path):
			os.remove(song_path)
			print(f'deleted {song_path}')
			break
	time.sleep(5)

#Manages the recommendations list
def manage_recommendations():
	global prev_change_flag
	prev_change_flag = False

	while True:
		if len(recommendations) == 0 or prev_change_flag == True:
			print('\r--- updating recommendations \n>>> ', end = ' ')
			time.sleep(3)
			if prev_change_flag == True:
				for song in recommendations:
					thread = threading.Thread(target = watch_thread, args = (song, ), daemon = True)
					thread.start()
					#threading._start_new_thread(watch_thread, (song, ))
					print(f'\r--- spawned the watch thread for {song} \n>>> ', end = ' ')
			recommendations.clear()
			prev_change_flag = False
			print('\r--- getting recs \n>>> ', end = ' ')
			get_recs(prev_track)
			print('--- done \n>>> ', end = ' ')
		time.sleep(1.75)

#Manages the autoplay feature
def handle_autoplay():
	while True:
		if len(now_playing) == 0 and len(queue) == 0 and prev_track != None:
			now_playing.append(recommendations [0])
			status_dir [recommendations [0]] = 'downloaded'
			recommendations.remove(recommendations [0])
		time.sleep(1.75)

#Gets recommensations for autoplay
def get_recs(name):
	track_results = spot.search(name)

	items = track_results['tracks']['items']
	#print(spot.audio_features(track_results ['tracks'] ['items'] [0] ['id']))

	if len(items) > 0:
		track = items[0]
		for _ in range(2):
			results = spot.recommendations(seed_tracks=[track ['id']], seed_artists=[track_results['tracks'] ['items'] [0] ['artists'] [0] ['id']], limit=1)
			for track in results['tracks']:
				track_name = f"{track['artists'][0]['name']} - {track['name']}"
				recommendations.append(track_name)
	else:
		for i in range(3):
			recommendations.append(random_song.main())

	if len(recommendations) != 0:
		sleep_v = 20
		for song in recommendations:
			print(f'\r--- {song} \n>>> ', end = ' ')
			threading._start_new_thread(get_music, (song, None, 'queue', sleep_v))
			sleep_v += 10

		print(f'\r--- downloading the song {recommendations [0]} from the recs \n>>> ', end = ' ')
		
		print('\r--- thread starte \n>>> ', end = ' ')

#Notifies whenever a song starts playing
def put_notification(song):

	image_urls, album_name, artists, track = get_metadata(song)
	#formatted_track = track.replace(' ', '_')d
	if image_urls is not None:
		print('\r---image_urls is not None \n>>> ', end = ' ')
		get_image(image_urls ['mid'], track)
		image_path = os.path.join(spotipy_dir, 'cover_art_dir', f'{track}.png')
	else:
		image_path = None

	#convert_img_to_ico(os.path.join(spotipy_dir, 'queue', 'cover_art_dir', f'{formatted_track}.{extension}'))
	
	Notification(
    title = track,
    description = f'{artists}\nfrom album {album_name}',
	icon_path = image_path, # On Windows .ico is required, on Linux - .png
    duration = 5,									 # Duration in seconds
    urgency = 'normal'
	).send()
	
#Gets the image from the Spotify API
def get_image(image_url, song):
	image_data = requests.get(image_url)
	with open(os.path.join(spotipy_dir, 'cover_art_dir', song + '.png'), 'wb') as le_image:
		le_image.write(image_data.content)
		le_image.close()

#Gets the metadata for the currently playing 
def get_metadata(song_name):
	try:
		search_str = song_name


		track = spot.search(search_str)

		quality = ['high', 'mid', 'low']
		counter = 0
		images = {}

		for image_dict in track ['tracks'] ['items'] [0] ['album'] ['images']:

			images [quality [counter]] = image_dict ['url']
			counter += 1

		album_name = track ['tracks'] ['items'] [0] ['album'] ['name']

		artists = []
		artists_list = track ['tracks'] ['items'] [0] ['artists']
		for dictionary in artists_list:
			artists.append(dictionary ['name'])
		artists = ' & '.join(artists)

		track_name = track ['tracks'] ['items'] [0] ['name']

		if os.name == 'nt':
			images = None

		return images, album_name, artists, track_name
	except Exception:
		return None, None, song_name.split(' ') [0], song_name

#Checks if the queue is empty
def check_empty_queue():
	while True:
		if len(now_playing) == 0 and len(queue) != 0:
			print('\r--- shifting songs \n>>> ', end = ' ')
			now_playing.append(queue [0])
			queue.remove(queue [0])
		time.sleep(1)

#Initialises FFPyPlayer
def ffplay(path):

	global player

	player = MediaPlayer(path)

	time.sleep(5)
	while True:
		if str(player.get_pts()) [ : 3] == str(player.get_metadata() ['duration']) [ : 3]:
			break
		time.sleep(0.2)
	player.toggle_pause()
	player.close_player()

#Updates the queue and downloads the songs in the queue
def update_queue():
	for song in queue:
		if os.path.exists(os.path.join(queue_dir, song + '.wav')) == False and os.path.exists(os.path.join(music_dir, song + '.wav')) == False and os.path.exists(os.path.join(queue_dir, song + '.wav.part')) == False:
			threading._start_new_thread(get_music, (song, None, 'queue'))
		if os.path.exists(os.path.join(music_dir, song + 'wav')):
			print('\r--- song already downloaded, so not doing it again \n>>> ', end = ' ')
			status_dir [song] = 'downloaded'

#Downloads the song from YouTube
def get_music(search_term, save_as, out_dir, sleep_val=0):
	alpha_list = list(string.printable) [ : -6]
	alpha_list.remove('/')
	alpha_list.remove('\\')
	alpha_list.remove('"')
	alpha_list.append(' ')

	time.sleep(sleep_val)
	
	filter_search_term = ''.join([char for char in search_term if char in alpha_list])

	try:
		status_dir [search_term] = 'downloading'

		if save_as == None:
			save_as = search_term
		
		spotipy_dir = os.path.join(os.path.expanduser('~'), 'SpotiPy')

		music_dir = os.path.join(spotipy_dir, out_dir)
		download_path = os.path.join(music_dir, search_term)
		formatted_search_term = filter_search_term.replace(' ', '+')

		html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + formatted_search_term)
		video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())

		yt_url_thingy = 'https://www.youtube.com/watch?v='
		le_url = yt_url_thingy + video_ids [0]

		audio_downloder = YoutubeDL({'extractaudio' : True,
									'audioformat' : 'wav',
									'audioquality' : 320,
									'format':'bestaudio',
									'outtmpl': f'{download_path}.wav',
									'convertsubtitles': 'srt',
									'allsubtitles': True,									
									'addmetadata': True,
									'quiet' : True}) 	

		audio_downloder.extract_info(le_url)

		status_dir [search_term] = 'downloaded'
	except Exception as e:
		print('errorr in downloading')
		print(e)
		pass

#Checks the queue for songs
def queue_check():
	global music_dir
	global queue_dir
	music_dir = os.path.join(spotipy_dir, 'music')
	queue_dir = os.path.join(spotipy_dir, 'queue')
	#playlist_dir = os.path.join(spotipy_dir, 'playlists') Redundant code for now

	while True:
		for song in now_playing:
			while status_dir [song] == 'downloading':
				time.sleep(5.0)
			song_with_ext = song + '.wav'
			if os.path.exists(os.path.join(music_dir, song_with_ext)) == False and os.path.exists(os.path.join(queue_dir, song_with_ext)) == False:
				print("Song dowloading since it isn't already downloaded.")
				get_music(song, None, 'queue')
			else:
				print("Song already downloaded, playing now.")
	
			print(f'\r--- playing {song} \n>>> ', end = '')
				
			put_notification(song)
				
			ffplay(os.path.join(queue_dir, song + '.wav'))

			print(f'\r--- done playing {song}\n>>> ', end = '')

			thread = threading.Thread(target = watch_thread, args = (song, ), daemon = True)
			thread.start()

			time.sleep(0.5)

			now_playing.clear()
				

			del status_dir [song]

		time.sleep(1)

threading._start_new_thread(queue_check, ())
threading._start_new_thread(check_empty_queue, ())
threading._start_new_thread(manage_recommendations, ())
threading._start_new_thread(handle_autoplay, ())

#endregion

#region Input
while True:

	command = str(input('\r>>> '))

	if '.addq' in command:
		song = command [6 : ]
		song = ''.join([char for char in song if char not in ['\\', '/', '"', '|']])
		queue.append(song)
		print('\r--- updating queue \n>>> ', end = ' ')
		status_dir [song] = 'downloaded'
		threading._start_new_thread(update_queue, ())
		prev_track = song
		prev_change_flag = True

	elif '.playnext' in command:
		song = command [10 : ]
		song = ''.join([char for char in song if char not in ['\\', '/', '"', '|']])
		queue.insert(0, song)
		print('\r--- updating queue \n>>> ', end = ' ')
		threading._start_new_thread(update_queue, ())
		status_dir [song] = 'downloaded'
		prev_track = song
		prev_change_flag = True

	elif '.play' in command:
		song = command [6 : ]
		song = ''.join([char for char in song if char not in ['\\', '/', '"', '|']])
		if (len(now_playing) == 0 and len(song) != 0) or (len(now_playing) != 0 and len(song) != 0):
			if len(now_playing) != 0:
				#for song in recommendations:
				#	thread = threading.Thread(target = watch_thread, args = (song + '.wav', ), daemon = True)
				#	thread.start()
				queue.insert(0, song)
				status_dir [song] = 'downloaded'
				#skip()
			else:
				now_playing.append(song)
			status_dir [song] = 'downloaded'
			try:
				recommendations.remove('placeholder')
			except Exception:
				pass
			prev_track = song
			prev_change_flag = True
		elif len(song) == 0:
			try:
				player.toggle_pause()
			except Exception:
				pass
	
	elif '.dload' in command:
		song = command [7 : ]  
		print('\r--- (enter the name for the audio file to be saved as) \n---', end = " ")
		save_as = str(input())
		
		threading._start_new_thread(get_music, (song, save_as, 'music'))

	elif '.showq' in command:
		for song in queue:
			print(f'--- {song}')

	elif '.nowp' in command:
		print('   ', now_playing)
		print(f'\r--- {now_playing [0]} \n>>> ', end = ' ')

	elif '.pause' in command:
		player.toggle_pause()

	
	elif '.setvol' in command:
		vol = int(command.split(' ', 1)[1]) / 100
		print(f'vol : {vol}')
		print(player.get_volume())
		player.set_volume(vol)
		print(player.get_volume())

	elif '.remove' in command:
		index = int(command.split(' ', 1) [1])
		try:
			os.remove(os.path.join(queue_dir, queue [index] + '.wav.part'))
		except Exception:
			os.remove(os.path.join(queue_dir, queue [index] + '.wav'))
		del queue [index]

	elif '.showrecs' in command:
		for rec in recommendations:
			print(f'--- {rec}')
		print(f'--- for previous track : {prev_track}')

	#if '.playlist' in command:
	#	play

	elif '.quit' in command:
		try:
			skip()
			player.close_player()
			time.sleep(0.1)
		except NameError:
			pass

		for song in os.listdir(queue_dir):
			song_path = os.path.join(queue_dir, song)
			try:
				os.remove(song_path)
			except Exception:
				while True:
					if os.path.exists(song_path):
						os.remove(song_path)
						break
				time.sleep(1.65)
		break
		exit()
#endregion