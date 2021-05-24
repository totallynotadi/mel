import os 
import time
import threading
import urllib.request
import requests
import re
try:
	import ffpyplayer
except:
	os.system('python -m pip install ffpyplayer')
from ffpyplayer.player import MediaPlayer

try:
	from youtube_dl import YoutubeDL
except:
	os.system('python -m pip install youtube_dl')
from youtube_dl import YoutubeDL

try:
	import spotipy
except:
	os.system('python -m pip install spotipy')
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy

from pynotifier import Notification


# TO-DO
#
#handle exceptions well
#help command

global queue
global now_playing
queue = []
now_playing = []

global ye_slash
global no_slash
if os.name == 'nt':
	ye_slash = '\\'
	no_slash = '/'
else:
	ye_slash = '/' 
	no_slash = '\\'

global spotipy_dir
spotipy_dir = os.path.join(os.path.expanduser('~'), 'SpotiPy').replace(no_slash, ye_slash)
spot = spotipy.Spotify(client_credentials_manager = SpotifyClientCredentials('5af907e805114b54ad674b1765447cf4', '6cc582cd14894babad8fc9043ae7a982'))

if not os.path.exists(spotipy_dir):
	os.mkdir(spotipy_dir)
	os.mkdir(os.path.join(spotipy_dir, 'music'))
	os.mkdir(os.path.join(spotipy_dir, 'queue'))
	os.mkdir(os.path.join(spotipy_dir, 'queue', 'cover_art_dir'))
	os.mkdir(os.path.join(spotipy_dir, 'playlists'))

def get_track(name):
    results = spot.search(q='track:' + name, type='track')
    items = results['tracks']['items']
    if len(items) > 0:
        return items[0]
    else:
        return None

def show_recommendations_for_track(track):
	reclist = []
	results = spot.recommendations(seed_tracks=[track['id']], limit=1)
	for track in results['tracks']:
		track_name = f"{track['artists'][0]['name']} - {track['name']}"
		reclist.append(track_name)
	return reclist[0]

def put_notification(song):

	image_urls, album_name, artists, track, track_id = get_metadata(song)
	formatted_track = track.replace(' ', '_')
	get_image(image_urls ['high'], formatted_track)
	Notification(
		title = track,
		description = f'{artists}\n{album_name}',
		icon_path = (os.path.join(spotipy_dir, 'queue', 'cover_art_dir', 'img.png')), # On Windows .png is required, on Linux - .png
		duration = 5,                              												  
		urgency = 'normal'
	).send()
	


def get_image(image_url, song):
	if os.name == 'nt':
		extension = '.png'
	else:
		extension = '.png'

	image_data = requests.get(image_url)
	with open(os.path.join(spotipy_dir, 'queue', 'cover_art_dir', 'img' + extension), 'wb') as le_image:
		le_image.write(image_data.content)
		le_image.close()

def get_metadata(song_name):
    track = spot.search(song_name)


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
    track_id = track ['tracks'] ['items'] [0] ['id']
    return images, album_name, artists, track_name, track_id

def check_empty_queue():
	while True:
		if len(now_playing) == 0 and len(queue) != 0:
			now_playing.append(queue [0])
			queue.remove(queue [0])

def ffplay(path):

	global player

	player = MediaPlayer(path)

	time.sleep(5)
	while True:
		if str(player.get_pts()) [ : 3] == str(player.get_metadata() ['duration']) [ : 3]:
			break
	player.toggle_pause()
	player.close_player()

def update_queue():
	for song in queue:
		if os.path.exists(f'{music_dir}{ye_slash}{song}.png') == False and os.path.exists(f'{queue_dir}{ye_slash}{song}.mp3') == False:
			threading._start_new_thread(get_music, (song, None, 'queue'))

def get_music(search_term, save_as, out_dir):

	if save_as == None:
		save_as = search_term
	
	spotipy_dir = os.path.join(os.path.expanduser('~'), 'SpotiPy').replace(no_slash, ye_slash)

	music_dir = spotipy_dir + f'{ye_slash}{out_dir}'
	download_path = music_dir + f'{ye_slash}{save_as}' 
	search_term = search_term.replace(' ', '+')

	html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + search_term)
	video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())

	yt_url_thingy = 'https://www.youtube.com/watch?v='
	le_url = yt_url_thingy + video_ids [0]
	#webbrowser.open_new_tab(le_url)

	audio_downloder = YoutubeDL({'extractaudio' : True,
								'audioformat' : 'mp3',
								'audioquality' : 256,
								'format':'bestaudio',
								'outtmpl': f'{download_path}.mp3',
								'quiet' : True}) 	

	audio_downloder.extract_info(le_url)

def queue_check():
	global music_dir
	global queue_dir
	music_dir = os.path.join(spotipy_dir, 'music').replace(no_slash, ye_slash)
	queue_dir = os.path.join(spotipy_dir, 'queue').replace(no_slash, ye_slash)
	playlist_dir = os.path.join(spotipy_dir, 'playlists').replace(no_slash, ye_slash)

	while True:
		for song in now_playing:
			song_with_ext = song + '.mp3'
			if os.path.exists(os.path.join(music_dir, song_with_ext)) == False and os.path.exists(os.path.join(queue_dir, song_with_ext)) == False:
				print('\n--- this song is not downloaded, downloading it now \n>>> ', end = '')
				get_music(song, None, 'queue')
				
				#threading._start_new_thread(ffplay, (f"{queue_dir}{ye_slash}{song}.mp3", ))

				#play_thread = threading.Thread(group = None, target = ffplay, name = None, args = (f"{queue_dir}{ye_slash}{song}.mp3", ), kwargs = None, daemon = None)
				#play_thread.start()

				#while True:
				#	if not play_thread.is_alive:
				#		break

				print(f'--- playing {song} \n>>> ', end = '')
				
				put_notification(song)
				
				ffplay(f"{queue_dir}{ye_slash}{song}.mp3")
				
				print(f'\n--- done playing {song}\n>>> ', end = '')
				
				os.remove(os.path.join(queue_dir, song_with_ext))
				time.sleep(0.9)
				now_playing.clear()
				track = get_track(song)
				autoplay = show_recommendations_for_track(track)
				print(autoplay)
				queue.append(autoplay)
				print('---updating queue\n>>>')
				threading._start_new_thread(update_queue, ())

			elif os.path.exists(os.path.join(music_dir, song_with_ext)):
				print(f'\n--- this song is already downloaded in the music dir, so playing it now')

				#threading._start_new_thread(ffplay, (f"{music_dir}{ye_slash}{song}.mp3", ))

				#play_thread = threading.Thread(group = None, target = ffplay, name = None, args = (f"{music_dir}{ye_slash}{song}.mp3", ), kwargs = None, daemon = None)
				#play_thread.start()
				
				#while True:
				#	if not play_thread.is_alive:
				#		break
				
				print('--- playing audio \n>>> ', end = '')
				
				put_notification(song)

				ffplay(f"{music_dir}{ye_slash}{song}.mp3")
				print(f'\n--- done playing {song}\n>>> ', end = '')
				now_playing.clear()
				track = get_track(song)
				autoplay = show_recommendations_for_track(track)
				print(autoplay)
				queue.append(autoplay)
				print('---updating queue\n>>>')
				threading._start_new_thread(update_queue, ())

			else:

				print(f'\n--- this song is already downloaded in the queue dir, so playing it now')

				#threading._start_new_thread(ffplay, (f"{queue_dir}{ye_slash}{song}.mp3", ))

				#play_thread = threading.Thread(group = None, target = ffplay, name = None, args = (f"{queue_dir}{ye_slash}{song}.mp3", ), kwargs = None, daemon = None)
				#play_thread.start()
				
				#while True:
				#	if not play_thread.is_alive:
				#		break

				print('--- playing audio \n>>> ', end = '')

				put_notification(song)
				
				ffplay(f"{queue_dir}{ye_slash}{song}.mp3")
				print(f'\n--- done playing {song}\n>>> ', end = '')
				
				#keyboard.press(Key.enter)
				#
				# keyboard.release(Key.enter)

				os.remove(os.path.join(queue_dir, song_with_ext))
				time.sleep(0.9)
				now_playing.clear()
				track = get_track(song)
				autoplay = show_recommendations_for_track(track)
				print(autoplay)
				queue.append(autoplay)
				print('---updating queue\n>>>')
				threading._start_new_thread(update_queue, ())

		time.sleep(1)

threading._start_new_thread(queue_check, ())
threading._start_new_thread(check_empty_queue, ())

while True:

	command = str(input('>>> '))

	if '.play ' in command:
		if len(now_playing) == 0:
			song = command [6 : ]
			now_playing.append(song)
		else:
			player.toggle_pause()

	if '.addq' in command:
		song = command [6 : ]
		queue.append(song)
		print('---updating queue\n>>>')
		threading._start_new_thread(update_queue, ())
	
	if '.dload' in command:
		song = command [7 : ]  
		save_as = str(input('--- (enter the name for the audio file to be saved as) \n--- '))
		
		threading._start_new_thread(get_music, (song, save_as, 'music'))

	if '.showq' in command:
		print(queue)

	if '.nowp' in command:
		print(now_playing)

	if '.pause' in command:
		player.toggle_pause()

	if '.skip' in command:
		player.toggle_pause()
		player.seek(player.get_metadata() ['duration'] - 5)
		time.sleep(6)
		now_playing.clear()
		print('\r')
		continue

	#if '.playlist' in command:
	#	play

	if '.quit' in command:
		break
		exit()
	'''
	if '.autoplay' in command:
		song = command [10 : ]
		now_playing.append(song)
		track = get_track(song)
		autoplay = show_recommendations_for_track(track)
		queue.append(autoplay[0])
		print('---updating queue\n>>>')
		threading._start_new_thread(update_queue, ())
	'''
	
	if '.playnext' in command:
		song = command [10 : ]
		queue.insert(0, song)
		print('---updating queue\n>>>')
		threading._start_new_thread(update_queue, ())
