# standard library imports
import threading
import urllib
import socket
import time
import sys
import os
import re
from ffpyplayer.player import MediaPlayer
from youtube_dl import YoutubeDL
from spotipy.oauth2 import SpotifyClientCredentials
from plyer import notification
import pafy
import requests
#local imports
sys.path.insert(1, r'../Melodine/src/random_tracks')
import get_random_track

# third party module imports
# automatically download mising modules
modules = {
           "ffpyplayer": "from ffpyplayer.player import MediaPlayer",
           "youtube_dl": "from youtube_dl import YoutubeDL",
           "spotipy": "from spotipy.oauth2 import SpotifyClientCredentials",
           "plyer": "from plyer import notification ", # or can also use : from pynotifier import Notification 
           "pafy": "import pafy",
           "requests": "import requests"
           }

for module in list(modules.keys()):
    try:
        exec(modules [module])
    except ModuleNotFoundError:
        os.system(f"python -m pip install --upgrade {module}")
        exec(modules [module])
import spotipy
    

# config stuff
#
# kill timer
# group listening related stuff
# user creds
#

#TODO
#
# handle exceptions well
# help command
# streaming opts
# direct play
# autoplay
# fix ico in notifs
# listen with frands
# play/search by genre/artist

global autoplay
autoplay = True
global prev_track
prev_track = None
prev_search = None
global spot
spot = spotipy.Spotify(client_credentials_manager = SpotifyClientCredentials('6b8eb89b95414a56a1c97dad45d9c587', '6747fd4c5e294ec685e850cf0e6dcc6e'))
global recommendations
recommendations = []
recommendations.append('placeholder')
global queue
global now_playing
queue = []
now_playing = []
global status_dict
status_dict = {}
global melodine_dir
melodine_dir = os.path.join(os.path.expanduser('~'), '.melodine')




def toggle_autoplay():
    global autoplay
    if autoplay == True:
        autoplay = False
        if len(recommendations) != 0:
            clear_recs()
        recommendations.clear()
    elif autoplay == False:
        autoplay = True


def manage_stream():
    while True:
        command = input('\r>>> ')
        if '.stop' in command:
            skip()
            break


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
    while True:
        if status_dict [song] == 'downloaded':
            time.sleep(1)
            os.remove(song_path)
            print(f'\r::: deleted {song_path} \n>>> ', end = ' ')
            if song in list(status_dict.keys()):    del status_dict[song]
            break
    time.sleep(5)


def manage_recommendations():
    global prev_change_flag
    prev_change_flag = False
    while True:
        if (len(recommendations) == 0 or prev_change_flag == True) and autoplay:
            print('\r--- updating recommendations \n>>> ', end=' ')
            time.sleep(0.8)
            if prev_change_flag == True:
                clear_recs()
            recommendations.clear()
            prev_change_flag = False
            get_recs(prev_track)
        time.sleep(1.75)


def handle_autoplay():
    while True:
        if len(now_playing) == 0 and len(queue) == 0 and prev_track != None and autoplay:
            now_playing.append(recommendations[0])
            # status_dict [recommendations [0]] = 'downloaded'
            recommendations.remove(recommendations[0])
        time.sleep(1.75)


def get_recs(name):
    global prev_search
    track_results = spot.search(name)

    items = track_results['tracks']['items']
    # print(spot.audio_features(track_results ['tracks'] ['items'] [0] ['id']))

    def get_genre_from_artist(artists):
        genres = []
        for artist in artists:
            search_result = spot.search(artist, type='artist')
            artist = search_result['artists']['items'][0]
            genres += artist['genres']
        return list(set(genres))

    if len(items) > 0:	
        track = items [0]
        artists = [dict['name'] for dict in track['artists']]
        seed_genres = get_genre_from_artist(artists)
        for _ in range(4):
            try:    results = spot.recommendations(seed_tracks = [track['id']], seed_artists = [dict['id'] for dict in track['artists']][: 5], seed_genres = seed_genres[: 5], limit=1)
            except spotipy.exceptions.SpotifyException:    results = spot.recommendations(seed_tracks = [track ['id']], seed_artists = [track_results['tracks'] ['items'] [0] ['artists'] [0] ['id']], limit = 1)
            if len(results ['tracks']) == 0:
                get_recs(prev_search)
                break
            for track in results['tracks']: 
                track_name = f"{track['artists'][0]['name']} - {track['name']}"
                recommendations.append(track_name)
                prev_search = name
    elif prev_search != None:    get_recs(prev_search)
    else:	
        for _ in range(3):
            recommendations.append(get_random_track.main())
    if len(recommendations) != 0:
        sleep_v = 10
        for song in recommendations:
            print(f'\r--- {song} \n>>> ', end = ' ')
            threading._start_new_thread(get_music, (song, 'queue', None, sleep_v, ))
            sleep_v += 5


def put_notification(song):

    image_urls, album_name, artists, track = get_metadata(song)
    # formatted_track = track.replace(' ', '_')d
    if not image_urls is None:
        print('\r---image_urls is not None \n>>> ', end=' ')
        get_image(image_urls['mid'], track)
        #image_path = os.path.join(melodine_dir, 'cover_art_dir', f'{track}.png')
    else:
        #image_path = None
        pass

    # convert_img_to_ico(os.path.join(melodine_dir, 'queue', 'cover_art_dir', f'{formatted_track}.{extension}'))


    notification.notify(
        title = track,
        message = f"\nBy {artists}\nfrom Album {album_name}", 
        app_icon = os.path.join(melodine_dir, 'cover_art_dir', track + '.png'),
        timeout = 15,
        toast = False
    )


def get_image(image_url, song):
    image_data = requests.get(image_url)
    with open(os.path.join(melodine_dir, 'cover_art_dir', song + '.png'), 'wb') as le_image:
        le_image.write(image_data.content)


def get_metadata(song_name):
    try:
        search_str = song_name

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
    player = MediaPlayer(path)
    time.sleep(0.5)
    while True:
        if int(float(str(player.get_pts())[: 3])) - 2 == int(float(str(player.get_metadata()['duration'])[: 3])) - 2:
            time.sleep(0.5)
            player.toggle_pause()
            player.close_player()
            break
    time.sleep(1)


def update_queue():
    for song in queue:
        if os.path.exists(os.path.join(queue_dir, song + '.wav')) == False and os.path.exists(os.path.join(music_dir, song + '.wav')) == False and os.path.exists(os.path.join(queue_dir, song + '.wav.part')) == False:
            threading._start_new_thread(get_music, (song, 'queue', ))
        if os.path.exists(os.path.join(music_dir, song + 'wav')):
            print('\r--- song already downloaded, so not doing it again \n>>> ', end=' ')
            status_dict[song] = 'downloaded'


def get_music(search_term, out_dir, save_as = None, sleep_val = 0, no_part = True):
    try:

        status_dict[search_term] = 'downloading'
        time.sleep(sleep_val)
        if save_as == None:
            save_as = search_term
        music_dir = os.path.join(melodine_dir, out_dir)
        download_path = os.path.join(music_dir, search_term)
        html = requests.get("https://www.youtube.com/results?search_query=" + search_term.replace(' ', '+'))
        video_ids = re.findall(r"watch\?v=(\S{11})", str(html.content))
        video_url = 'https://www.youtube.com/watch?v=' + video_ids[0]

        audio_downloder = YoutubeDL({
                                    'outtmpl': f'{download_path}.wav',
                                    'hls_prefer_native': True,
                                    'format': 'bestaudio',
                                    'extractaudio': True,
                                    'continuedl': True,
                                    'no_part': no_part,
                                    'quiet': True,
                                    'retries': 5
                                    })
        audio_downloder.extract_info(video_url)
        status_dict[search_term] = 'downloaded'
    except urllib.error.HTTPError as error:
        status_dict[search_term] = 'downloaded'
        print('\r::: error while downloading, retrying')
        get_music(search_term, 'queue')
    except Exception as error:
        print('::: unhandled exception occured while downloading')
        #traceback.print_exc()
        print(error)
        pass


def queue_check():
    global music_dir
    global queue_dir
    music_dir = os.path.join(melodine_dir, 'music')
    queue_dir = os.path.join(melodine_dir, 'queue')

    while True:
        for song in now_playing:
            #wait while the current song is being downloaded, since downloadint while palying causes buffer errors
            while status_dict[song] == 'downloading':    time.sleep(2)
            song_with_ext = song + '.wav'

            # determining the directory to play from (dont download if the track is alredy saved)
            # the play_path is set to the dierecotry based on the directory in which the song is downloaded
            # by default, it is set to the queue_dir
            play_path = os.path.join(melodine_dir, 'queue')
            if os.path.exists(os.path.join(music_dir, song_with_ext)):
                play_path = os.path.join(melodine_dir, 'music')
            elif os.path.exists(os.path.join(music_dir, song_with_ext)) == False and os.path.exists(os.path.join(queue_dir, song_with_ext)) == False:
                get_music(song, 'queue')

            # the last case scenario being that the song is already saved in the queue_dir
            print('\r--- playing audio \n>>> ', end = ' ')
            put_notification(song)
            ffplay(os.path.join(play_path, song + '.wav'))
            threading._start_new_thread(watch_thread, (song, ))
            print(f'\r--- finished playing {song}\n>>> ', end = '')
            time.sleep(0.5)
            now_playing.clear()
            if song in list(status_dict.keys()):    del status_dict[song]
        time.sleep(1)


threading._start_new_thread(queue_check, ())
threading._start_new_thread(check_empty_queue, ())
if autoplay:
    threading._start_new_thread(manage_recommendations, ())
    threading._start_new_thread(handle_autoplay, ())

while True:

    command = str(input('\r>>> '))

    if '.addq' in command:
        song = command[6:]
        queue.append(song)
        print('\r--- updating queue \n>>> ', end = ' ')
        status_dict[song] = 'downloaded'
        threading._start_new_thread(update_queue, ())
        prev_track = song
        prev_change_flag = True

    elif '.playnext' in command:
        song = command[10:]
        queue.insert(0, song)
        print('\r--- updating queue \n>>> ', end = ' ')
        threading._start_new_thread(update_queue, ())
        status_dict[song] = 'downloaded'
        prev_track = song
        prev_change_flag = True

    elif '.play' in command:
        song = command[6:]

        if (len(now_playing) == 0 and len(song) != 0) or (len(now_playing) != 0 and len(song) != 0):
            if len(now_playing) != 0:
                # for song in recommendations:
                #	thread = threading.Thread(target = watch_thread, args = (song + '.wav', ), daemon = True)
                #	thread.start()
                queue.insert(0, song)
                if song not in list(status_dict.keys()):
                    status_dict[song] = 'downloaded'
                skip()
            else:
                now_playing.append(song)

            if song not in list(status_dict.keys()):
                status_dict[song] = 'downloaded'
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
        song = command[7:]
        print('\r--- (enter the name for the audio file to be saved as) \n---', end = " ")
        save_as = str(input())

        threading._start_new_thread(get_music, (song, save_as, 'music', ))

    elif '.showq' in command:
        for song in queue:
            print(f'--- {song}')

    elif '.nowp' in command:
        print('   ', now_playing)
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
        del status_dict[queue[index]]
        if index - 1 < 0:
            prev_track = now_playing [0]
        else:
            prev_track = queue [index - 1]
        prev_change_flag = True
        del queue[index]

    elif '.stream' in command:
        # status_dct [0] = 'downloading'
        try:
            skip()
        except:
            pass
        toggle_autoplay()
        clear_recs()

        title = command.split(' ', 1)[1]

        print(f'--- streaming "{title}"')

        threading._start_new_thread(
            get_music, (title, None, 'queue', 0, False))

        time.sleep(5)

        while True:
            if os.path.exists(os.path.join(queue_dir, title + '.wav.part')) == True:
                threading._start_new_thread(manage_stream, ())
                ffplay(os.path.join(queue_dir, title + '.wav.part'))
                queue.append('queueholder')
                print(queue)
                del status_dict[title]
                queue.remove('queueholder')
                break
        toggle_autoplay()
    
    elif '.rewind' in command:
        # player.toggle_pause()
        # time.sleep(0.2)
        player.seek(2)
        time.sleep(1)
        # player.toggle_pause()

    elif '.showrecs' in command:
        for rec in recommendations:
            print(f'--- {rec}')
        print(f'--- for previous track : {prev_track}')

    elif '.stat' in command:
        print(f'\r--- {status_dict} \n>>> ', end = ' ')

    elif '.toggle_autoplay' in command:
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
        sys.exit(1)
