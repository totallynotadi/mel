import os 
import time
import threading
from youtube_dl import YoutubeDL
import urllib.request
import re
from pynput.keyboard import Key, Controller
import audioread

# TO-DO
#
#handle exceptions well
#help command
#make it quit well
#
# add auto pip installs 
# pyinput
# moviepy


global queue
queue = []

global ye_slash
global no_slash
if os.name == 'nt':
	ye_slash = '\\'
	no_slash = '/'
else:
	ye_slash = '/' 
	no_slash = '\\'

'''
while True:
	search_term = str(input('what term do you want to search? \n')).replace(' ', '+')
	#formatted_search_term = search_term.replace(' ', '+')
	save_as = str(input('what do you want to save this song as (the file name) : '))

	get_urls.get_music_for_term(search_term, save_as)

	queue.append(save_as)

	os.system(f'C:\\code_workspace\\spotify\\music\\{save_as}.mp3')
'''

global spotipy_dir
spotipy_dir = os.path.join(os.path.expanduser('~'), 'SpotiPy').replace(no_slash, ye_slash)

if not os.path.exists(spotipy_dir):
	os.mkdir(spotipy_dir)
	os.mkdir(os.path.join(spotipy_dir, 'music'))
	os.mkdir(os.path.join(spotipy_dir, 'queue'))
	os.mkdir(os.path.join(spotipy_dir, 'playlists'))

def check_current_song():
	while True:
		current_song = queue [0]
		time.sleep(2)

def ffplay(path):
	os.system(f'"{path}"')

def get_duration(dir, song):
	with audioread.audio_open(os.path.join(dir, song)) as le_audio:
		total_sec = le_audio.duration
	return total_sec

def update_queue():
	print(queue)
	for song in queue:
		print('--- updating music from inside update queue')
		print(song)
		print(queue.index(song) == 0)
		if queue.index(song) == 0:
			print('--- skipping to renew current song')
			continue
		else:
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

	audio_downloder = YoutubeDL({'extractaudio' : False,
								 'audioformat' : 'mp3',
								 'audioquality' : 320,	
								 'format':'bestaudio',
								 'outtmpl': f'{download_path}.mp3',
								 'quiet' : False}) 

	audio_downloder.extract_info(le_url)

	keyboard = Controller()
	keyboard.press(Key.enter)
	keyboard.release(Key.enter)

def queue_check():
	music_dir = os.path.join(spotipy_dir, 'music').replace(no_slash, ye_slash)
	queue_dir = os.path.join(spotipy_dir, 'queue').replace(no_slash, ye_slash)
	playlist_dir = os.path.join(spotipy_dir, 'playlists').replace(no_slash, ye_slash)

	while True:
		for song in queue:
			print(song)
			print(queue)
			song_with_ext = song + '.mp3'
			print(os.path.exists(os.path.join(queue_dir, song_with_ext)))
			print(os.path.join(queue_dir, song_with_ext))
			print(os.path.join(music_dir, song_with_ext))
			if os.path.exists(os.path.join(music_dir, song_with_ext)) == False and os.path.exists(os.path.join(queue_dir, song_with_ext)) == False:
				print('--- this song is not downloaded, downloading it now')
				get_music(search_term = song, save_as = None, out_dir = 'queue')
				threading._start_new_thread(ffplay, (f"{queue_dir}{ye_slash}{song}.mp3", ))
				print('--- playing audio')
				print(f'--- sleeping for {get_duration(queue_dir, song_with_ext)}')
				time.sleep(get_duration(queue_dir, song_with_ext))
				print('--- done sleeping')
				queue.remove(song)
				os.remove(os.path.join(queue_dir, song_with_ext))
				print('audio file deleted')
				print(os.path.exists(os.path.join(queue_dir, song)))
			#elif os.path.exists(os.path.join(music_dir, song)) == True or os.path.exists(os.path.join(queue_dir, song)) == True:
			elif os.path.exists(os.path.join(music_dir, song)):
				print(f'--- this song is already downloaded in the music dir, so playing it now')
				threading._start_new_thread(ffplay, (f"{music_dir}{ye_slash}{song}.mp3", ))
				print(f'--- sleeping for {get_duration(music_dir, song_with_ext)}')
				time.sleep(get_duration(music_dir, song_with_ext))
				print('--- done sleeping')
			else:
				print(f'--- this song is already downloaded in the queue dir, so playing it now')
				threading._start_new_thread(ffplay, (f"{queue_dir}{ye_slash}{song}.mp3", ))
				print(f'--- sleeping for {get_duration(queue_dir, song_with_ext)}')
				time.sleep(get_duration(queue_dir, song_with_ext))
				print('--- done sleeping')
				os.remove(os.path.join(queue_dir, song_with_ext))
				print('--- audio file deleted')
				queue.remove(song)

		time.sleep(2)

threading._start_new_thread(queue_check, ())

while True:

	command = str(input('>>> '))

	if '.play' in command:
		song = command [6 : ]
		print(queue)
		queue.append(song)
		print(queue)
		#time.sleep(5)
		#update_queue()

	if '.addq' in command:
		song = command [6 : ]
		queue.append(song)
		print('--- calling update queue')
		threading._start_new_thread(update_queue, ())
	
	if '.dload' in command:
		song = command [7 : ]  
		save_as = str(input('--- (enter the name for the audio file to be saved as) \n--- '))
		
		threading._start_new_thread(get_music, (song, save_as, 'music'))

	if '.quit' in command:
		break
		exit()
