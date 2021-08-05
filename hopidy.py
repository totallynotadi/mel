from utils import *
import discord_rpc
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
	discord_rpc.run(video.title)
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
def skip():
	player.set_mute(True)
	player.toggle_pause()
	player.seek(player.get_metadata()['duration'] - 3)
	player.toggle_pause()
def manage_stream():
	while True:
		command = input('\r>>> ')
		if '.stop' in command:
			skip()
			break

		elif '.nowp' in command:
			[print(f'\r--- {song} \n>>> ', end = ' ') for song in now_playing]

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
		try:
			player.toggle_pause()
		except:
			pass

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
