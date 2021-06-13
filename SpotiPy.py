import os 
import time
import threading
import urllib.request
import requests
import re

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

if not os.path.exists(spotipy_dir):
	os.mkdir(spotipy_dir)
	os.mkdir(os.path.join(spotipy_dir, 'music'))
	os.mkdir(os.path.join(spotipy_dir, 'queue'))
	os.mkdir(os.path.join(spotipy_dir, 'queue', 'cover_art_dir'))
	os.mkdir(os.path.join(spotipy_dir, 'playlists'))

def put_notification(song):

	image_urls, album_name, artists, track = get_metadata(song)
	#formatted_track = track.replace(' ', '_')
	if image_urls is not None:
		print('---image_urls is None')
		get_image(image_urls ['mid'], track)
		image_path = os.path.join(spotipy_dir, 'queue', 'cover_art_dir', f'{track}.png')
	else:
		image_path = None

	#convert_img_to_ico(os.path.join(spotipy_dir, 'queue', 'cover_art_dir', f'{formatted_track}.{extension}'))
	
	Notification(
    title = track,
    description = artists,
	icon_path = image_path, # On Windows .ico is required, on Linux - .png
    duration = 7,									 # Duration in seconds
    urgency = 'low'
	).send()
	

def get_image(image_url, song):

	image_data = requests.get(image_url)
	with open(os.path.join(spotipy_dir, 'queue', 'cover_art_dir', song + 'png'), 'wb') as le_image:
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

def check_empty_queue():
	while True:
		if len(now_playing) == 0 and len(queue) != 0:
			print('shifting songs')
			now_playing.append(queue [0])
			queue.remove(queue [0])
		time.sleep(1)

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
		if os.path.exists(f'{music_dir}{ye_slash}{song}.wav') == False and os.path.exists(f'{queue_dir}{ye_slash}{song}.wav') == False:
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
								 'audioformat' : 'wav',
								 'audioquality' : 256,
								 'format':'bestaudio',
								 'outtmpl': f'{download_path}.wav',
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
			song_with_ext = song + '.wav'
			if os.path.exists(os.path.join(music_dir, song_with_ext)) == False and os.path.exists(os.path.join(queue_dir, song_with_ext)) == False:
				print('\n--- this song is not downloaded, downloading it now \n>>> ', end = '')
				get_music(song, None, 'queue')
		
				#threading._start_new_thread(ffplay, (f"{queue_dir}{ye_slash}{song}.mp3", ))

				#play_thread = threading.Thread(group = None, target = ffplay, name = None, args = (f"{queue_dir}{ye_slash}{song}.mp3", ), kwargs = None, daemon = None)
				#play_thread.start()

				#while True:
				#	if not play_thread.is_alive:
				#		break

				print(f'\n--- playing {song} \n>>> ', end = '')
				
				put_notification(song)

				ffplay(f"{queue_dir}{ye_slash}{song}.wav")

				print(f'\n--- done playing {song}\n>>> ', end = '')
			
				os.remove(os.path.join(queue_dir, song_with_ext))

				now_playing.clear()

				#print('removed the song from the queue dir')
				#print(f'now playing list after playing : {now_playing}')
				#print(f'queue list after playing : {queue}')
				time.sleep(0.9)

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

				ffplay(f"{music_dir}{ye_slash}{song}.wav")
				print(f'\n--- done playing {song}\n>>> ', end = '')

				now_playing.clear()

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

				ffplay(f"{queue_dir}{ye_slash}{song}.wav")
				print(f'\n--- done playing {song}\n>>> ', end = '')

				#keyboard.press(Key.enter)
				#
				# keyboard.release(Key.enter)

				os.remove(os.path.join(queue_dir, song_with_ext))

				now_playing.clear()

				#print('removed the song from the queue dir')
				#print(f'now playing list after playing : {now_playing}')
				#print(f'queue list after playing : {queue}')
				time.sleep(0.9)
				#now_playing.clear()

		time.sleep(1)

threading._start_new_thread(queue_check, ())
threading._start_new_thread(check_empty_queue, ())

while True:

	command = str(input('>>> '))

	if '.play' in command:
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
		player.seek(player.get_metadata() ['duration'] - 2)
		player.toggle_pause()
		#print(f'now playing before the skip command : {now_playing}')
		#print(f'queue lsit before the skip command : {queue}')
		#now_playing.clear()
		#print(f'now playing after the skip command : {now_playing}')
		#print(f'queue list after the skip command : {queue}')
		time.sleep(2.5)
		#print('cleared the now_playing list')
		print('\r')

	#if '.playlist' in command:
	#	play

	if '.quit' in command:
		break
		exit()
