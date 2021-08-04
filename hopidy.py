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
from utils import *
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
#endregion

print("""
Welcome to Melodine. \n
Melodine is a simple command line tool to play and download music.\n
		
    	.play <Song Name> - Plays the top result for the search term.\n
    	.dload <Song Name> - Downloads the top result for the search term.\n
    	.addq <Song Name> - Adds song to the end of the queue\n
    	.showq - Displays queue\n
    	.playnext - <Song Name> - Plays the top search result after the currently playing song.\n
    	.nowp - Displays currently playing song.\n
    	.quit - Exits the program gracefully."""
)
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
		best.download(filepath=f"{formatted_search_term}{best.ext}")

		status_dir[search_term] = 'downloaded'
	except Exception as e:
		status_dir[search_term] = 'downloaded'
		print('errorr in downloading')
		#traceback.print_exc()
		print(e)
		pass

def ffplay(song):

	global player
	global vol

	search_term = song
	formatted_search_term = search_term.replace(' ', '+')

	html = requests.get("https://www.youtube.com/results?search_query=" + formatted_search_term)
	video_ids = re.findall(r"watch\?v=(\S{11})", str(html.content))
	video = pafy.new(video_ids[0])
	best = video.getbestaudio()
	url = best.url
	duration = video.duration
	opts = {'sync' : 'audio'}
	player = MediaPlayer(url, ffopts = opts)
	print(duration)
	player.toggle_pause()
	time.sleep(5)
	player.toggle_pause()

	last_pts = 0
	updated_pts = 0
	while True:
		updated_pts = int(float(str(player.get_pts())[: 3])) - 3

		while player.get_pause():
			time.sleep(0.4)

		if updated_pts == last_pts:
			player.toggle_pause()
			time.sleep(4)	
			player.toggle_pause()

		if int(float(str(player.get_pts())[: 3])) - 3 == int(float(str(player.get_metadata()['duration'])[: 3])) - 3:
			player.set_mute(True)
			player.toggle_pause()
			time.sleep(1)
			player.close_player()
			break
		time.sleep(1)
		last_pts = updated_pts

def skip():
	player.set_mute(True)
	player.toggle_pause()
	player.seek(player.get_metadata()['duration'] - 3)
	player.toggle_pause()
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
		except Exception as e:
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
def manage_stream():
	while True:
		command = input('\r>>> ')
		if '.stop' in command:
			skip()
			break

		elif '.nowp' in command:
			[print(f'\r--- {song} \n>>> ', end = ' ') for song in now_playing]

def check_empty_queue():
	while True:
		if len(now_playing) == 0:
			if len(queue) != 0:
				print('continuing from the queue')
				print('\r--- shifting songs \n>>> ', end = ' ')
				if search_dict ['search_type'] in ['track', None]:	search_dict ['playing_from'] = ['track', queue [0]]
				now_playing.append(queue[0])
				queue.remove(queue[0])
			elif len(search_dict ['playing_playlist']) != 0:
				print('continuing from the playlist')
				#if search_dict ['search_type'] == 'track':
				#	now_playing.append(search_dict ['search_content'] [0])
					#search_dict ['playing_from'] = [search_dict ['search_type'], search_dict ['search_content'] [0], [search_dict ['playing_from'] [-1] [search_dict ['playing_from'].index(queue [0]) + 1 : ]]]
				#	search_dict ['search_content'].remove(search_dict ['search_content'] [0])
				if search_dict ['search_type'] in ['albums', 'artists', 'playlists']:
					#print(search_dict ['playing_playlist'])
					now_playing.append(search_dict ['playing_playlist'] [0])
					#print(search_dict ['playing_playlist'])
					search_dict ['playing_playlist'].remove(search_dict ['playing_playlist'] [0])
					print(f"playing from {search_dict ['search_type']}: {search_dict ['playing_from'] [1]}")
				print(search_dict ['playing_from'])
		time.sleep(1)

def update_queue():
	for song in queue:
		if os.path.exists(os.path.join(queue_dir, song + '.wav')) == False and os.path.exists(os.path.join(music_dir, song + '.wav')) == False:
			threading._start_new_thread(get_music, (song, None, 'queue', 0, True, ))
		if os.path.exists(os.path.join(music_dir, song + 'wav')):
			print('\r--- song already downloaded, so not doing it again \n>>> ', end = ' ')
			status_dir[song] = 'downloaded'

def queue_check():
	global music_dir
	global queue_dir
	music_dir = os.path.join(spotipy_dir, 'music')
	queue_dir = os.path.join(spotipy_dir, 'queue')
	playlist_dir = os.path.join(spotipy_dir, 'playlists')

	while True:
		for song in now_playing:
			if song == 'placeholder':
				continue
				#time.sleep(3.7)
			song_with_ext = song + '.wav'
			#if os.path.exists(os.path.join(music_dir, song_with_ext)) == False and os.path.exists(os.path.join(queue_dir, song_with_ext)) == False:
				#print("\r--- song dowloading since it isn't already downloaded. \n>>>", end = ' ')
				#get_music(song, None, 'queue')
				#print("\r--- song already downloaded, playing now. \n>>>", end = ' ')
	
			print(f'\r--- playing {song} \n>>> ', end = '')
				
			put_notification(song)
				
			ffplay(song)

			print(f'\r--- done playing {song}\n>>> ', end = '')

			#thread = threading.Thread(target = watch_thread, args = (song, ), daemon = True)
			#thread.start()

			time.sleep(0.5)

			now_playing.clear()
				
			#del status_dir [song]

		time.sleep(1)
#endregion

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


		queue.append(song)
		print('\r--- updating queue \n>>> ', end = ' ')
		status_dir[song] = 'downloaded'	
		if not no_auto and autoplay == True:
				prev_track = song
				prev_change_flag = True

	elif '.playnext' in command:
		command = command[10:]

		song, no_auto = parse_opts(command)

		queue.insert(0, song)
		print('\r--- updating queue \n>>> ', end = ' ')
		status_dir[song] = 'downloaded'
		if not no_auto and autoplay == True:
				prev_track = song
				prev_change_flag = True

	elif '.play' in command:
		command = command [6 : ]

		song, no_auto = parse_opts(command)

		try:	now_playing.remove('placeholder')
		except:	pass

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

			if (not no_auto) and autoplay == True:
				prev_track = song
				prev_change_flag = True

			print(search_dict ['playing_from'])
			if search_dict ['search_type'] in ['playlists', 'albums', 'artists']:
				search_dict ['playing_from'] = [search_dict ['search_type'], selected, search_dict ['playing_playlist'] [search_dict ['loaded_playlist'].index(song) + 1 : ]]
				search_dict ['playing_playlist'] = search_dict ['playing_playlist'] [search_dict ['loaded_playlist'].index(song) + 1 : ]
			else:
				if search_dict ['search_type'] == None:	search_dict ['playing_from'] = ['track', song]
				else:	search_dict ['playing_from'] = [search_dict ['search_type'], song]

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
		try:	print(search_dict ['playing_from'])
		except:	pass
		print(f'\r--- {now_playing [0]} \n>>> ', end = ' ')

	elif '.pause' in command:
		if player.get_pause() == False:
			player.set_pause(True)
			print(player.get_pause())
			print('setting to pause')
			print(player.get_pause())
		else:	player.set_pause(False)

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
		if index - 1 < 0:	prev_track = now_playing [0]
		else:	prev_track = queue [index - 1]
		prev_change_flag = True
		del queue[index]

	elif '.stream' in command:
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
		player.seek(-2)
		time.sleep(1)

	elif '.search' in command:
		opts = ['--track', '--playlist', '--album', '--artist']
		command = command.split(' ', 2)
		opt = command [1]
		term = command [2]
		if opt not in opts:
			print("the viable opts are '--track', '--playlist', '--artist' and '--album'")
			continue

		if opt == opts [0]:	key = 'tracks'
		elif opt == opts [1]:	key = 'playlists'
		elif opt == opts [2]:	key = 'albums'
		elif opt == opts [3]:	key = 'artists'

		search_dict ['search_type'] = key
		if key == 'tracks':	search_dict ['search_content'] = []
		else:	search_dict ['search_content'] = {}
		search_dict ['loaded_playlist'] = []

		search_results = spot.search(term, type = opt [2 : ], limit = 25)

		items = search_results [key] ['items']

		table_rows = []
		for index, opts in enumerate(items):
			if opt [2 : ] == 'track':
				
				search_dict ['search_content'].append(f"{opts ['name']} - {opts ['artists'] [0] ['name']}")
				table_rows.append([index, f"{opts ['name']}", f"{opts ['artists'] [0] ['name']}"])	

			elif opt [2 : ] == 'playlist':
				print(f"\r--- {opts ['name']} by {opts ['owner'] ['display_name']} \n>>> ", end = ' ')
				search_dict ['search_content'] [opts ['name']] = opts ['id']

			elif opt [2 : ] == 'album':
				print(f"\r--- {opts ['name']} by {' & '.join([dict ['name'] for dict in opts ['artists']])} \n>>> ", end = ' ')
				search_dict ['search_content'] [opts ['name']] = f"{opts ['id']}"

			elif opt [2 : ] == 'artist':
				print(f"\r--- {opts ['name']} - {opts ['genres']} \n>>> ", end = ' ')
				search_dict ['search_content'] [opts ['name']] = f"{opts ['id']}"

		if search_dict ['search_type'] == 'tracks':
			print(make_table(
				rows = table_rows,
				labels = ['index', 'tracks', 'artists'],
				centered = True
			))

	elif '.list' in command:
		index = int(command.split(' ', 1) [1])
		content_dict = search_dict ['search_content']

		selected = list(content_dict.keys()) [index]
		key_id = content_dict [selected]

		search_dict ['loaded_playlist'].clear()

		table_rows = []
		if search_dict ['search_type'] == 'playlists':
			le_playlist = spot.playlist_items(key_id) ['items']
			for index, song in enumerate(le_playlist):
				song_name = f"{song ['track'] ['name']} - {song ['track'] ['artists'] [0] ['name']}"
				search_dict ['loaded_playlist'].append(song_name)
				table_rows.append([f"{index}", f"{song ['track'] ['name']}", f"{' & '.join([artist ['name'] for artist in song ['track'] ['artists']])}"])	

		elif search_dict ['search_type'] == 'albums':
			for index, album_song in enumerate(spot.album_tracks(key_id) ['items']):
				song_name = f"{album_song ['name']} - {album_song ['artists'] [0] ['name']}"
				search_dict ['loaded_playlist'].append(song_name)
				table_rows.append([f"{index}", f"{album_song ['name']}", f"{' & '.join([dict ['name'] for dict in album_song ['artists']])}"])	

		elif search_dict ['search_type'] == 'artists':
			songs_list = []
			#print(spot.artist_albums(key_id) ['items'])
			artist_album = spot.artist_albums(key_id) ['items']
			for album in artist_album:
				album_id = album ['id']
				for index, album_song in enumerate(spot.album_tracks(album_id) ['items']):
					song_name = f"{album_song ['name']} - {album_song ['artists'] [0] ['name']}"
					if song_name not in songs_list:
						search_dict ['loaded_playlist'].append(song_name)
						table_rows.append([f"{index}", f"{album_song ['name']}", f"{' & '.join([dict ['name'] for dict in album_song ['artists']])}"])
						songs_list.append(song_name)

		print(make_table(
			rows = list(table_rows),
			labels = ['index', 'tracks', 'artist'],
			centered = True
		))

		search_dict ['playing_playlist'] = search_dict ['loaded_playlist']

	elif '.showrecs' in command:
		for rec in recommendations:
			print(f'--- {rec}')
		print(f'--- for previous track : {prev_track}')

	elif '.srch' in command:
		print(search_dict)

	elif '.stat' in command:
		print(f'\r--- {status_dir} \n>>> ', end = ' ')

	elif '.close' in command:
		player.close_player()

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
			#watch_thread(song)
			os.remove(os.path.join(queue_dir, song))
		break
		exit()
