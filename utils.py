import math

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

'''
print(make_table(
            rows = [
                    [0, 'Game Over', 'Martin Garrix & LOOPERS'],
                    [1, 'Sundown', 'Eauxmar']
                ],
                
                labels =
                    ['index', 'tracks', 'artist'],

                centered = True
        ))
        '''

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

	search_dict ['playing_from'] = ['track', song]
 
	if len(search_dict) != 0:
		try:
			song = int(song)
			if search_dict ['search_type'] in ['artists', 'albums', 'playlists']:
				song = search_dict ['loaded_playlist'] [song]
			else:
				song = search_dict ['search_content'] [song]
				#search_dict ['search_content'].clear()
		except Exception as e:
			print('inside the except block')
			print(traceback.print_exc())
			print(e)
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
	player.seek(player.get_metadata()['duration'] - 3)
	player.toggle_pause()
	#time.sleep(2.2)
	#player.set_mute(False)

def watch_thread(song):
	song_path = os.path.join(queue_dir, song + '.wav')
	while song != 'placeholder' and (song in list(status_dir.keys())):
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
			results = spot.recommendations(seed_tracks = [track['id']], seed_artists = [dict ['id'] for dict in track ['artists']] [ : 4], seed_genres = seed_genres [ : 4], limit = 1)
			for track in results['tracks']:
				track_name = f"{track['name']} - {track['artists'][0]['name']}"
				recommendations.append(track_name)
	elif prev_search != None:
		get_recs(prev_search)
	else:
		for _ in range(3):
			recommendations.append(random_song.main())

	'''
	if len(recommendations) != 0:
		sleep_v = 15
		for song in recommendations:
			print(f'\r--- {song} \n>>> ', end = ' ')
			threading._start_new_thread(get_music, (song, None, 'queue', sleep_v, True, ))
			sleep_v += 5
			'''


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
		toast = True)

	#dont delete this way lmao, might prove useful later on

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
		if len(now_playing) == 0:
			if len(queue) != 0:
				print('continuing from the queue')
				print('\r--- shifting songs \n>>> ', end = ' ')
				if search_dict ['search_type'] in ['track', None]:	search_dict ['playing_from'] = ['track', queue [0]]
				now_playing.append(queue[0])
				queue.remove(queue[0])
			elif len(search_dict ['playing_playlist']) != 0:
				print('continuing from the playlist')
				if search_dict ['search_type'] == 'track':
					now_playing.append(search_dict ['search_content'] [0])
					#search_dict ['playing_from'] = [search_dict ['search_type'], search_dict ['search_content'] [0], [search_dict ['playing_from'] [-1] [search_dict ['playing_from'].index(queue [0]) + 1 : ]]]
					search_dict ['search_content'].remove(search_dict ['search_content'] [0])
				elif search_dict ['search_type'] in ['albums', 'artists', 'playlists']:
					now_playing.append(search_dict ['playing_playlist'] [0])
					search_dict ['playing_playlist'].remove(search_dict ['playing_playlist'] [0])
				print(search_dict ['playing_from'])
		time.sleep(1)


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

	opts = {'sync' : 'audio', 'volume': vol/100}
	player = MediaPlayer(url)

	#print(player.get_volume())
	#print(f'the global vol is: {vol}')
	#player.set_volume(vol)
	#print(player.get_volume())

	time.sleep(3)
	while True:
		if int(float(str(player.get_pts())[: 3])) - 3 == int(float(str(player.get_metadata()['duration'])[: 3])) - 3:
			player.set_mute(True)
			break
		time.sleep(1)

	player.toggle_pause()
	player.close_player()


def update_queue():
	for song in queue:
		if os.path.exists(os.path.join(queue_dir, song + '.wav')) == False and os.path.exists(os.path.join(music_dir, song + '.wav')) == False:
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
			if song == 'placeholder':
				continue
				#time.sleep(3.7)
			song_with_ext = song + '.wav'
			if os.path.exists(os.path.join(music_dir, song_with_ext)) == False and os.path.exists(os.path.join(queue_dir, song_with_ext)) == False:
				print("\r--- song dowloading since it isn't already downloaded. \n>>>", end = ' ')
				#get_music(song, None, 'queue')
			else:
				print("\r--- song already downloaded, playing now. \n>>>", end = ' ')
	
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
