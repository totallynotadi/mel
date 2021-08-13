import requests
import re
import pafy
from ffpyplayer.player import MediaPlayer
import time
import os
import utils 
import threading
import discord_rpc
print("""
Welcome to Melodine. 
Melodine is a simple command line tool to play and download music.
		
    	.play <Song Name> - Plays the top result for the search term.
    	.dload <Song Name> - Downloads the top result for the search term.
    	.addq <Song Name> - Adds song to the end of the queue
    	.showq - Displays queue
    	.playnext - <Song Name> - Plays the top search result after the currently playing song.
    	.nowp - Displays currently playing song.
    	.quit - Exits the program gracefully."""
) 

try:
	discord_rpc.set_status("nothing peeposad")
except:	
	pass
def ffplay(song):

	global player
	global vol

	search_term = song
	formatted_search_term = search_term.replace(' ', '+')

	html = requests.get("https://www.youtube.com/results?search_query=" + formatted_search_term)
	video_ids = re.findall(r"watch\?v=(\S{11})", str(html.content))
	vid_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
	video = pafy.new(video_ids[0])
	best = video.getbestaudio()
	url = best.url
	opts = {'sync' : 'audio'}
	player = MediaPlayer(url, ffopts = opts)
	utils.put_notification(song)
	try:
		discord_rpc.set_status(video.title, vid_url)
		
	except:	
		pass
	#threading._start_new_thread(discord_rpc.update_discord(), ())
	player.toggle_pause()
	time.sleep(1)
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

			try:
				discord_rpc.set_status("nothing peeposad")
			except:	pass
			break
		time.sleep(1)
		last_pts = updated_pts
def queue_check():
	global music_dir
	global queue_dir
	music_dir = os.path.join(utils.melodine_dir, 'music')
	queue_dir = os.path.join(utils.melodine_dir, 'queue')
	#playlist_dir = os.path.join(utils.melodine_dir, 'playlists')
	while True:
		for song in utils.now_playing:
			if song == 'placeholder':
				continue
				#time.sleep(3.7)
			#song_with_ext = song + '.wav'
			#if os.path.exists(os.path.join(music_dir, song_with_ext)) == False and os.path.exists(os.path.join(queue_dir, song_with_ext)) == False:
				#print("\r--- song dowloading since it isn't already downloaded. \n>>>", end = ' ')
				#get_music(song, None, 'queue')
				#print("\r--- song already downloaded, playing now. \n>>>", end = ' ')
	
			print(f'\r--- playing {song} \n>>> ', end = '')
			print(song)
			utils.get_recs(song)
			utils.add_req()
			ffplay(song)

			print(f'\r--- done playing {song}\n>>> ', end = '')
			
			#thread = threading.Thread(target = watch_thread, args = (song, ), daemon = True)
			#thread.start()

			time.sleep(0.5)

			utils.now_playing.clear()
			utils.add_req()
			#del status_dir [song]

		time.sleep(1)
def check_empty_queue():

	while True:
		#print("passed")
		if len(utils.now_playing) == 0:
			if len(utils.queue) != 0:
				print('continuing from the utils.queue')
				print('\r--- shifting songs \n>>> ', end = ' ')
				if utils.search_dict ['search_type'] in ['track', None]:	utils.search_dict ['playing_from'] = ['track', utils.queue [0]]
				utils.now_playing.append(utils.queue[0])
				utils.queue.remove(utils.queue[0])
			elif len(utils.search_dict ['playing_playlist']) != 0:
				print('continuing from the playlist')
				#if utils.search_dict ['search_type'] == 'track':
				#	utils.now_playing.append(utils.search_dict ['search_content'] [0])
					#utils.search_dict ['playing_from'] = [utils.search_dict ['search_type'], utils.search_dict ['search_content'] [0], [utils.search_dict ['playing_from'] [-1] [utils.search_dict ['playing_from'].index(utils.queue [0]) + 1 : ]]]
				#	utils.search_dict ['search_content'].remove(utils.search_dict ['search_content'] [0])
				if utils.search_dict ['search_type'] in ['albums', 'artists', 'playlists']:
					#print(utils.search_dict ['playing_playlist'])
					utils.now_playing.append(utils.search_dict ['playing_playlist'] [0])
					#print(utils.search_dict ['playing_playlist'])
					utils.search_dict ['playing_playlist'].remove(utils.search_dict ['playing_playlist'] [0])
					print(f"playing from {utils.search_dict ['search_type']}: {utils.search_dict ['playing_from'] [1]}")
				print(utils.search_dict ['playing_from'])
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
			[print(f'\r--- {song} \n>>> ', end = ' ') for song in utils.now_playing]
threading._start_new_thread(queue_check, ())
threading._start_new_thread(check_empty_queue, ())
	

if utils.autoplay:
	threading._start_new_thread(utils.manage_recommendations, ())
	threading._start_new_thread(utils.handle_autoplay, ())

while True:

	command = str(input('\r>>> '))

	if '.addq' in command:
		command = command[6:]

		song, no_auto = utils.parse_opts(command)


		utils.queue.append(song)
		print('\r--- updating queue \n>>> ', end = ' ')
		utils.status_dir[song] = 'downloaded'	
		if not no_auto and utils.autoplay == True:
				prev_track = song
				prev_change_flag = True

	elif '.playnext' in command:
		command = command[10:]

		song, no_auto = utils.parse_opts(command)

		utils.queue.insert(0, song)
		print('\r--- updating queue \n>>> ', end = ' ')
		utils.status_dir[song] = 'downloaded'
		if not no_auto and utils.autoplay == True:
				prev_track = song
				prev_change_flag = True
	elif '.next' in command:
		utils.now_playing.clear()
		player.close_player()
	elif '.list' in command:
		index = int(command.split(' ', 1) [1])
		content_dict = utils.search_dict ['search_content']

		selected = list(content_dict.keys()) [index]
		key_id = content_dict [selected]

		utils.search_dict ['loaded_playlist'].clear()

		table_rows = []
		if utils.search_dict ['search_type'] == 'playlists':
			le_playlist = utils.spot.playlist_items(key_id) ['items']
			for index, song in enumerate(le_playlist):
				song_name = f"{song ['track'] ['name']} - {song ['track'] ['artists'] [0] ['name']}"
				utils.search_dict ['loaded_playlist'].append(song_name)
				table_rows.append([f"{index}", f"{song ['track'] ['name']}", f"{' & '.join([artist ['name'] for artist in song ['track'] ['artists']])}"])	

	elif '.play' in command:
		command = command [6 : ]

		song, no_auto = utils.parse_opts(command)

		try:	utils.now_playing.remove('placeholder')
		except:	pass

		if (len(utils.now_playing) == 0 and len(song) != 0) or (len(utils.now_playing) != 0 and len(song) != 0):
			if len(utils.now_playing) != 0:
				utils.queue.insert(0, song)
				if song not in list(utils.status_dir.keys()):
					utils.status_dir[song] = 'downloaded'
				skip()
			else:	utils.now_playing.append(song)

			if song not in list(utils.status_dir.keys()):
				utils.status_dir[song] = 'downloaded'
			try:	utils.recommendations.remove('placeholder')
			except Exception:	pass

			if (not no_auto) and utils.autoplay == True:
				prev_track = song
				prev_change_flag = True

			print(utils.search_dict ['playing_from'])
			if utils.search_dict ['search_type'] in ['playlists', 'albums', 'artists']:
				utils.search_dict ['playing_from'] = [utils.search_dict ['search_type'], selected, utils.search_dict ['playing_playlist'] [utils.search_dict ['loaded_playlist'].index(song) + 1 : ]]
				utils.search_dict ['playing_playlist'] = utils.search_dict ['playing_playlist'] [utils.search_dict ['loaded_playlist'].index(song) + 1 : ]
			else:
				if utils.search_dict ['search_type'] == None:	utils.search_dict ['playing_from'] = ['track', song]
				else:	utils.search_dict ['playing_from'] = [utils.search_dict ['search_type'], song]

		elif len(song) == 0:
			try:	player.toggle_pause()
			except Exception:	pass

	elif '.dload' in command:
		song = command[7:]
		print('\r--- (enter the name for the audio file to be saved as) \n---', end = " ")
		save_as = str(input())

		threading._start_new_thread(utils.get_music, (song, save_as, 'music', ))

	elif '.showq' in command:
		for song in utils.queue:
			print(f'--- {song}')

	elif '.nowp' in command:
		try:	print(utils.search_dict ['playing_from'])
		except:	pass
		print(f'\r--- {utils.now_playing [0]} \n>>> ', end = ' ')

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
		utils.clear_recs()
		threading._start_new_thread(utils.watch_thread, (utils.queue[index], ))
		if index - 1 < 0:	prev_track = utils.now_playing [0]
		else:	prev_track = utils.queue [index - 1]
		prev_change_flag = True
		del utils.queue[index]

	elif '.stream' in command:
		try:	skip()
		except:	pass
		utils.toggle_autoplay()
		utils.clear_recs()

		title = command.split(' ', 1) [1]

		print(f'--- streaming "{title}"')

		threading._start_new_thread(utils.get_music, (title, None, 'queue', 0, False))

		time.sleep(5)

		while True:
			if os.path.exists(os.path.join(queue_dir, title + '.wav.part')) == True:
				threading._start_new_thread(manage_stream, ())
				ffplay(os.path.join(queue_dir, title + '.wav.part'))
				utils.queue.append('queueholder')
				print(utils.queue)
				del utils.status_dir [title]
				utils.queue.remove('queueholder')
				break

		utils.toggle_autoplay()

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

		utils.search_dict ['search_type'] = key
		if key == 'tracks':	utils.search_dict ['search_content'] = []
		else:	utils.search_dict ['search_content'] = {}
		utils.search_dict ['loaded_playlist'] = []

		search_results = utils.spot.search(term, type = opt [2 : ], limit = 25)

		items = search_results [key] ['items']

		table_rows = []
		for index, opts in enumerate(items):
			if opt [2 : ] == 'track':
				
				utils.search_dict ['search_content'].append(f"{opts ['name']} - {opts ['artists'] [0] ['name']}")
				table_rows.append([index, f"{opts ['name']}", f"{opts ['artists'] [0] ['name']}"])	

			elif opt [2 : ] == 'playlist':
				print(f"\r--- {opts ['name']} by {opts ['owner'] ['display_name']} \n>>> ", end = ' ')
				utils.search_dict ['search_content'] [opts ['name']] = opts ['id']

			elif opt [2 : ] == 'album':
				print(f"\r--- {opts ['name']} by {' & '.join([dict ['name'] for dict in opts ['artists']])} \n>>> ", end = ' ')
				utils.search_dict ['search_content'] [opts ['name']] = f"{opts ['id']}"

			elif opt [2 : ] == 'artist':
				print(f"\r--- {opts ['name']} - {opts ['genres']} \n>>> ", end = ' ')
				utils.search_dict ['search_content'] [opts ['name']] = f"{opts ['id']}"

		if utils.search_dict ['search_type'] == 'tracks':
			print(utils.make_table(
				rows = table_rows,
				labels = ['index', 'tracks', 'artists'],
				centered = True
			))

		elif utils.search_dict ['search_type'] == 'albums':
			for index, album_song in enumerate(utils.spot.album_tracks(key_id) ['items']):
				song_name = f"{album_song ['name']} - {album_song ['artists'] [0] ['name']}"
				utils.search_dict ['loaded_playlist'].append(song_name)
				table_rows.append([f"{index}", f"{album_song ['name']}", f"{' & '.join([dict ['name'] for dict in album_song ['artists']])}"])	

		elif utils.search_dict ['search_type'] == 'artists':
			songs_list = []
			#print(spot.artist_albums(key_id) ['items'])
			artist_album = utils.spot.artist_albums(key_id) ['items']
			for album in artist_album:
				album_id = album ['id']
				for index, album_song in enumerate(utils.spot.album_tracks(album_id) ['items']):
					song_name = f"{album_song ['name']} - {album_song ['artists'] [0] ['name']}"
					if song_name not in songs_list:
						utils.search_dict ['loaded_playlist'].append(song_name)
						table_rows.append([f"{index}", f"{album_song ['name']}", f"{' & '.join([dict ['name'] for dict in album_song ['artists']])}"])
						songs_list.append(song_name)

		print(utils.make_table(
			rows = list(table_rows),
			labels = ['index', 'tracks', 'artist'],
			centered = True
		))

		utils.search_dict ['playing_playlist'] = utils.search_dict ['loaded_playlist']

	elif '.showrecs' in command:
		for rec in utils.recommendations:
			print(f'--- {rec}')
		print(f'--- for previous track : {prev_track}')

	elif '.srch' in command:
		print(utils.search_dict)

	elif '.stat' in command:
		print(f'\r--- {utils.status_dir} \n>>> ', end = ' ')

	elif '.close' in command:
		player.close_player()

	elif '.toggle-autoplay' in command:
		utils.toggle_autoplay()
		print(utils.autoplay)

	elif '.history' in command:
		print(open("History.txt", "r").read())
	# if '.playlist' in command:
	#	play

	elif '.quit' in command:
		try:
			f.close()
			skip()
			time.sleep(0.5)
			player.close_player()
		except NameError:
			pass

		for song in os.listdir(queue_dir):
			#watch_thread(song)
			os.remove(os.path.join(queue_dir, song))
		break
