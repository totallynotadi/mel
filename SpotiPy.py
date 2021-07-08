import os
import time
import threading
import urllib.request
import requests
import re
import string
import socket
import traceback
import random_song

try:
	import ffpyplayer
except:
	os.system('pip install -r requirements.txt')
from ffpyplayer.player import MediaPlayer

from youtube_dl import YoutubeDL

from spotipy.oauth2 import SpotifyClientCredentials
import spotipy

#from pynotifier import Notification
from plyer import notification

# config stuff
#
# kill timer
# group listening related stuff
# user creds
# autoplay - enable/disable
# ffopts
# genre selection
#

# TO-DO
#
# handle exceptions well
# help command
# fix ico in notifs
# listen with frands
# play/search by genre/artist
# fix genre and random recs
# get a config
# integrate youtube api with the spotify one
# fix global spot object
# can optionally play a video too
# use async

global search_dict
search_dict = {}

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

global status_dir
status_dir = {}

global spotipy_dir
spotipy_dir = os.path.join(os.path.expanduser('~'), 'SpotiPy')
if not os.path.exists(spotipy_dir):
	os.mkdir(spotipy_dir)
	os.mkdir(os.path.join(spotipy_dir, 'music'))
	os.mkdir(os.path.join(spotipy_dir, 'queue'))
	os.mkdir(os.path.join(spotipy_dir, 'cover_art_dir'))
	os.mkdir(os.path.join(spotipy_dir, 'playlists'))


def socket_handler():
	SEPARATOR = '<SEPARATOR>'

	global BUFFER_SIZE
	BUFFER_SIZE = 512

	host = '18.116.67.97'
	# host = '192.168.43.164'
	port = 105001

	global client_socket
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	client_socket.connect((host, port))
	print("[+]connected")

	pass

def parse_opts(command):
	no_auto = False
	if '--no-auto' in command:
		no_auto = True
		command = command.split('--no-auto')
		command.remove('')
		song = command [0].strip()
	else:	song = command

	if len(search) != 0:
		try:
			song = int(song)
			print(song)
			song = search_dict ['search_content'] [song]
			print(song)
			search.clear()
		except Exception:
			pass

	return song, no_auto

def toggle_autoplay():
	global autoplay
	if autoplay == True:
		autoplay = False
		if len(recommendations) == 0:	clear_recs()
		recommendations.clear()
	elif autoplay == False:	autoplay = True

def manage_stream():
	while True:
		command = input('\r>>> ')
		if '.stop' in command:
			skip()
			break

		elif '.nowp' in command:
			[print(f'\r--- {song} \n>>> ', end = ' ') for song in now_playing]

def clear_recs():
	for song in recommendations:
		thread = threading.Thread(target = watch_thread, args = (song, ))
		thread.start()

def skip():
	player.set_mute(True)
	player.toggle_pause()
	player.seek(player.get_metadata()['duration'] - 2)
	player.toggle_pause()
	time.sleep(2.2)
	player.set_mute(False)

def watch_thread(song):
	song_path = os.path.join(queue_dir, song + '.wav')
	while song != 'placeholder':
		if status_dir [song] == 'downloaded':
			time.sleep(1)
			os.remove(song_path)
			print(f'\rdeleted {song_path} \n>>> ', end = ' ')
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
	# print(spot.audio_features(track_results ['tracks'] ['items'] [0] ['id']))

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
			results = spot.recommendations(seed_tracks = [track['id']], seed_artists = [dict ['id'] for dict in track ['artists']] [ : 5], seed_genres = seed_genres [ : 5], limit = 1)
			for track in results['tracks']:
				track_name = f"{track['artists'][0]['name']} - {track['name']}"
				recommendations.append(track_name)
	elif prev_search != None:
		get_recs(prev_search)
	else:
		for _ in range(3):
			recommendations.append(random_song.main())

	if len(recommendations) != 0:
		sleep_v = 15
		for song in recommendations:
			print(f'\r--- {song} \n>>> ', end = ' ')
			threading._start_new_thread(get_music, (song, None, 'queue', sleep_v, True, ))
			sleep_v += 5


def put_notification(song):

	image_urls, album_name, artists, track = get_metadata(song)
	# formatted_track = track.replace(' ', '_')d
	if image_urls is not None:
		print('\r---image_urls is not None \n>>> ', end = ' ')
		get_image(image_urls['mid'], track)
		image_path = os.path.join(spotipy_dir, 'cover_art_dir', f'{track}.png')
	else:
		image_path = None

	# convert_img_to_ico(os.path.join(spotipy_dir, 'queue', 'cover_art_dir', f'{formatted_track}.{extension}'))


	notification.notify(
		title = track,
		message = f"\nBy {artists}\nfrom Album {album_name}",
		app_name = "hopidy",
		app_icon = r'C:\users\gadit\downloads\music_icon0.ico',
		timeout = 10,
		ticker = "hopidy",
		toast = False
	)

	
	#Notification(
    #title = track,
    #description = f'{artists}\nfrom album {album_name}',		# On Windows .ico is required, on Linux - .png
	#icon_path = r'C:\users\gadit\downloads\Music_29918.ico',
    #duration = 5,									 			# Duration in seconds
    #urgency = 'normal'
	#).send()


def get_image(image_url, song):
	image_data = requests.get(image_url)
	with open(os.path.join(spotipy_dir, 'cover_art_dir', song + '.png'), 'wb') as le_image:
		le_image.write(image_data.content)
		le_image.close()


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


def check_empty_queue():
	while True:
		if len(now_playing) == 0 and len(queue) != 0:
			print('\r--- shifting songs \n>>> ', end=' ')
			now_playing.append(queue[0])
			queue.remove(queue[0])
		time.sleep(1)


def ffplay(path):

	global player
	global vol

	opts = {'sync' : 'audio', 'volume': vol/100}
	player = MediaPlayer(path, ffopts = opts)

	time.sleep(2.67)
	#print(player.get_volume())
	#print(f'the global vol is: {vol}')
	player.set_volume(vol)
	#print(player.get_volume())

	while True:
		if int(float(str(player.get_pts())[: 3])) - 2 == int(float(str(player.get_metadata()['duration'])[: 3])) - 2:
			break
		time.sleep(0.2)
	player.toggle_pause()
	player.close_player()


def update_queue():
	for song in queue:
		if os.path.exists(os.path.join(queue_dir, song + '.wav')) == False and os.path.exists(os.path.join(music_dir, song + '.wav')) == False and os.path.exists(os.path.join(queue_dir, song + '.wav.part')) == False:
			threading._start_new_thread(get_music, (song, None, 'queue', 0, True, ))
		if os.path.exists(os.path.join(music_dir, song + 'wav')):
			print('\r--- song already downloaded, so not doing it again \n>>> ', end = ' ')
			status_dir[song] = 'downloaded'


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

		audio_downloder = YoutubeDL({'extractaudio': True,
									'audioformat': 'wav',
									'audioquality': 320,
									'format': 'bestaudio',
									'outtmpl': f'{download_path}.wav',
									'nopart': part,
									'quiet': True})

		audio_downloder.extract_info(le_url)

		status_dir[search_term] = 'downloaded'
	except Exception as e:
		status_dir[search_term] = 'downloaded'
		print('errorr in downloading')
		#traceback.print_exc()
		print(e)
		pass


def queue_check():
	global music_dir
	global queue_dir
	music_dir = os.path.join(spotipy_dir, 'music')
	queue_dir = os.path.join(spotipy_dir, 'queue')
	playlist_dir = os.path.join(spotipy_dir, 'playlists')

	while True:
		for song in now_playing:
			# print(status_dir)
			while status_dir [song] == 'downloading' or 'queueholder' in queue:
				time.sleep(2)
			song_with_ext = song + '.wav'
			if os.path.exists(os.path.join(music_dir, song_with_ext)) == False and os.path.exists(os.path.join(queue_dir, song_with_ext)) == False:
				print(f'\r--- {song} is not downloaded, downloading it now \n>>> ', end = '')
				
				#threading._start_new_thread(get_music, (song, None, 'queue', 0, True, ))
				get_music(song, None, 'queue', 0, True)
				#time.sleep(10)

				print(f'\r--- playing {song} \n>>> ', end = '') 

				put_notification(song)

				ffplay(os.path.join(queue_dir, song + '.wav'))

				print(f'\r--- done playing {song}\n>>> ', end = '')

				thread = threading.Thread(target = watch_thread, args = (song, ))
				thread.start()
				# os.remove(os.path.join(queue_dir, song_with_ext))

				time.sleep(0.5)

				now_playing.clear()

			elif os.path.exists(os.path.join(music_dir, song_with_ext)):
				print(f'\r--- this song is already downloaded in the music dir, so playing it now \n>>> ', end=' ')

				print('\r--- playing audio \n>>> ', end='')

				put_notification(song)

				ffplay(os.path.join(music_dir, song + '.wav'))

				print(f'\r--- done playing {song}\n>>> ', end='')
				time.sleep(0.5)

				now_playing.clear()
				time.sleep(0.5)

			else:

				print('\r--- this song is already downloaded in the queue dir, so playing it now \n>>> ', end = ' ')

				print('\r--- playing audio \n>>> ', end = ' ')

				put_notification(song)

				ffplay(os.path.join(queue_dir, song + '.wav'))
				print(f'\r--- done playing {song}\n>>> ', end = '')

				thread = threading.Thread(target = watch_thread, args = (song, ))
				thread.start()
				# os.remove(os.path.join(queue_dir, song_with_ext))

				now_playing.clear()
				time.sleep(0.5)

			if song in list(status_dir.keys()):
				del status_dir[song]

		time.sleep(1)


threading._start_new_thread(queue_check, ())
threading._start_new_thread(check_empty_queue, ())
if autoplay:
	threading._start_new_thread(manage_recommendations, ())
	threading._start_new_thread(handle_autoplay, ())

while True:

	command = str(input('\r>>> '))

	if '.addq' in command:
		command = command[6:]

		song, no_auto = parse_opts(command)

		song = ''.join([char for char in song if char not in ['\\', '/', '"', '|']])
		queue.append(song)
		print('\r--- updating queue \n>>> ', end = ' ')
		status_dir[song] = 'downloaded'	
		threading._start_new_thread(update_queue, ())
		if not no_auto and autoplay == True:
				prev_track = song
				prev_change_flag = True

	elif '.playnext' in command:
		command = command[10:]

		song, no_auto = parse_opts(command)

		song = ''.join([char for char in song if char not in ['\\', '/', '"', '|']])
		queue.insert(0, song)
		print('\r--- updating queue \n>>> ', end = ' ')
		threading._start_new_thread(update_queue, ())
		status_dir[song] = 'downloaded'
		if not no_auto and autoplay == True:
				prev_track = song
				prev_change_flag = True

	elif '.play' in command:
		command = command [6 : ]

		song, no_auto = parse_opts(command)

		song = ''.join([char for char in song if char not in ['\\', '/', '"', '|']])

		if (len(now_playing) == 0 and len(song) != 0) or (len(now_playing) != 0 and len(song) != 0):
			if len(now_playing) != 0:
				queue.insert(0, song)
				if song not in list(status_dir.keys()):
					status_dir[song] = 'downloaded'
				skip()
			else:	now_playing.append(song)

			if song not in list(status_dir.keys()):
				status_dir[song] = 'downloaded'
			try:	recommendations.remove('placeholder')
			except Exception:	pass

			if not no_auto and autoplay == True:
				prev_track = song
				prev_change_flag = True

		elif len(song) == 0:
			try:	player.toggle_pause()
			except Exception:	pass

	elif '.dload' in command:
		song = command[7:]
		print('\r--- (enter the name for the audio file to be saved as) \n---', end = " ")
		save_as = str(input())

		threading._start_new_thread(get_music, (song, save_as, 'music', ))

	elif '.showq' in command:
		for song in queue:
			print(f'--- {song}')

	elif '.nowp' in command:
		print(f'\r--- {now_playing [0]} \n>>> ', end = ' ')

	elif '.pause' in command:
		player.toggle_pause()

	elif '.skip' in command:
		skip_time = command[6:]
		
		if len(skip_time) == 0 or skip_time == []:
			skip()
		else:
			print(f'current pts : {player.get_pts()}')
			print(f'total duration : {player.get_metadata() ["duration"]}')
			target_time = player.get_pts() + int(skip_time)
			if target_time > player.get_metadata()['duration']:
				skip()
			else:
				player.toggle_pause()
				player.seek(target_time)
				player.toggle_pause()

	elif '.setvol' in command:
		print(f'--- current volume is : {vol}')
		vol = int(command.split(' ', 1)[1])
		print(f'vol : {vol / 100}')
		print(player.get_volume())
		player.set_volume(vol / 100)
		print(player.get_volume())

	elif '.remove' in command:
		index = int(command.split(' ', 1)[1])
		clear_recs()
		threading._start_new_thread(watch_thread, (queue[index], ))
		#del status_dir [queue [index]]
		if index - 1 < 0:	prev_track = now_playing [0]
		else:	prev_track = queue [index - 1]
		prev_change_flag = True
		del queue[index]

	elif '.stream' in command:
		# status_dir [0] = 'downloading'
		try:	skip()
		except:	pass
		toggle_autoplay()
		clear_recs()

		title = command.split(' ', 1) [1]

		print(f'--- streaming "{title}"')

		threading._start_new_thread(get_music, (title, None, 'queue', 0, False))

		time.sleep(5)

		while True:
			if os.path.exists(os.path.join(queue_dir, title + '.wav.part')) == True:
				threading._start_new_thread(manage_stream, ())
				ffplay(os.path.join(queue_dir, title + '.wav.part'))
				queue.append('queueholder')
				print(queue)
				del status_dir [title]
				queue.remove('queueholder')
				break

		toggle_autoplay()

	elif '.rewind' in command:
		player.toggle_pause()
		time.sleep(0.2)
		player.seek(2)
		time.sleep(0.2)
		player.toggle_pause()

	elif '.search' in command:
		opts = ['--track', '--playlist', '--album', '--artist']
		command = command.split(' ', 2)
		opt = command [1]
		term = command [2]
		if opt not in opts:
			print("the viable opts are '--tracks', '--playlist', '--artist' and '--album'")
			continue

		if opt == opts [0]:	key = 'tracks'
		elif opt == opts [1]:	key = 'playlists'
		elif opt == opts [2]:	key = 'albums'
		elif opt == opts [3]:	key = 'artists'

		search_dict ['search_type'] = key
		if key == 'tracks':	search_dict ['search_content'] = []
		else:	search_dict ['search_content'] = {}
		search_dict ['loaded_playlist'] = []
		search_dict ['playing_from']

		search_results = spot.search(term, type = opt [2 : ], limit = 25)

		items = search_results [key] ['items']

		for opts in items:
			if opt [2 : ] == 'track':
				print(f"\r--- {opts ['name']} by {' & '.join([dict ['name'] for dict in opts ['artists']])} \n>>> ", end = ' ')
				search_dict ['search_content'].append(f"{opts ['name']} by {' & '.join([dict ['name'] for dict in opts ['artists']])}")

			elif opt [2 : ] == 'playlist':
				print(f"\r--- {opts ['name']} by {opts ['owner'] ['display_name']} \n>>> ", end = ' ')
				search_dict ['search_content'] [opts ['name']] = opts ['id']

			elif opt [2 : ] == 'album':
				print(f"\r--- {opts ['name']} by {' & '.join([dict ['name'] for dict in opts ['artists']])} \n>>> ", end = ' ')
				search_dict ['search_content'] [opts ['name']] = f"{opts ['id']}"

			elif opt [2 : ] == 'artist':
				print(f"\r--- {opts ['name']} - {opts ['genres']} \n>>> ", end = ' ')
				search_dict ['search_content'] [opts ['name']] = f"{opts ['id']}"

	elif '.list' in command:
		index = int(command.split(' ', 1) [1])
		content_dict = search_dict ['search_content']

		if search_dict ['search_type'] == 'playlists':
			#search_dict ['playing_from'] = content_dict [list(content_dict.keys()) [index]]
			selected = content_dict [list(content_dict.keys()) [index]]
			key_id = content_dict [selected]
			le_playlist = spot.playlist_items(key_id) ['items']
			for song in le_playlist:
				song_name = f"{song ['name']} - {' & '.join([artist ['name'] for artist in song ['artists']])}"
				print(song_name)
				search_dict ['loaded_playlist'].append(song_name)

		elif search_dict ['search_type'] == 'album':
			selected = content_dict [list(content_dict.keys()) [index]]
			key_id = content_dict [selected]
			for album_song in spot.album_tracks(key_id) ['items']:
				song_name = f"{album_song ['name']} - {' & '.join([dict ['name'] for dict in album_song ['artists']])}"
				print(song_name)
				search_dict ['loaded_playlist'].append(song_name)

		elif search_dict ['search_type'] == 'artists':
			#search_dict ['playing_from'] = content_dict [list(content_dict.keys()) [index]]
			selected = content_dict [list(content_dict.keys()) [index]]
			key_id = content_dict [selected]
			artist_album = spot.artist_album(key_id) ['artists'] ['items']
			for album in artist_album:
				album_id = album ['id']
				for album_song in spot.album_tracks(album_id) ['items']:
					song_name = f"{album_song ['name']} - {' & '.join([dict ['name'] for dict in album_song ['artists']])}"
					print(song_name)
					search_dict ['loaded_playlist'].append(song_name) 

	elif '.showrecs' in command:
		for rec in recommendations:
			print(f'--- {rec}')
		print(f'--- for previous track : {prev_track}')

	elif '.srch' in command:
		print(len(search))

	elif '.stat' in command:
		print(f'\r--- {status_dir} \n>>> ', end = ' ')

	elif '.toggle-autoplay' in command:
		toggle_autoplay()

	# if '.playlist' in command:
	#	play

	elif '.quit' in command:
		try:
			skip()
			time.sleep(0.5)
			player.close_player()
		except NameError:
			pass

		for song in os.listdir(queue_dir):
			os.remove(os.path.join(queue_dir, song))
		break
		exit()
