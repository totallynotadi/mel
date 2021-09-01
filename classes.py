import threading
import requests
import spotipy
import time
import re

from spotipy.oauth2 import SpotifyClientCredentials
from ffpyplayer.player import MediaPlayer
from youtube_dl import YoutubeDL
from plyer import notification
from pyyoutube import Api
import pafy

# yt-dl errors
# youtube_dl.utils.ExtractorError
# youtube_dl.utils.DownloadError
# urllib.error.HTTPError

# errors
#
# base error class
# no attributes supplied
# not searchable on spotify
class ObjectNotConstructable(Exception):
    # base exception class
    def __str__(self, string = None):
        if not string is None:    return string
        else:    return 'object not constructable'
class NoAttributesSupplied(ObjectNotConstructable):
    ObjectNotConstructable.__str__("no search term or ID supplied")
class ObjectNotSearchable(ObjectNotConstructable):
    ObjectNotConstructable.__str__("empty response from the spotify API")


spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials('6b8eb89b95414a56a1c97dad45d9c587', '6747fd4c5e294ec685e850cf0e6dcc6e'))


def filter_search_term(search_term: str):
    # filter the strings like "Official Music Video" out of the title
    erase_from = None
    for word in search_term.lower().split(' '):
        for trigger in ['official', 'music', 'audio', 'wave', 'video']:
            if trigger in word:
                trigger_index = search_term.index(word)
                erase_from = trigger_index
                for bracket in ['(', '[']:
                    if bracket in search_term[trigger_index - 1]:
                        erase_from -= 1
    return (' ').join(search_term[: erase_from])


class Track:
    def __init__(self, name = None, track_id = None):
        # preferred extension is set to .wav, but it might change based on the extension of the higest quality stream')

        # this block of code determines the attribute to be used to construct the object
        # i.e. wether to construct based on a search term of directly from an ID
        self.__type = None
        for attribute in [name, track_id]:
            if not attribute is None:    self.__type  = [key for key, value in locals().items() if value == attribute] [0]
        if self.__type == None:    raise NoAttributesSupplied

        self.track_id = track_id
        self.title = name
        self.ext = '.wav'
        self.filename = self.title + self.ext
        self.fetch_type = None

    def __fetch_url(self):
        print(':::fetching url')
        # pafy stuff
        # the below lines of code take a long time to execute (about 3 to 4 seconds of runtime)
        # thus their handling is important
        # this is executed lazily i.e. only when needed
        html = requests.get("https://www.youtube.com/results?search_query=" + self.title.replace(' ', '+'))
        video = pafy.new(re.findall(r"watch\?v=(\S{11})", str(html.content))[0])
        best_stream = video.getbestaudio(preftype = "wav", ftypestrict = False)

        self.ext = '.' + best_stream.extension
        self.title = filter_search_term(video.title).strip()
        self.url = best_stream.url
        self.filename = self.title + self.ext
        print('video title:::', filter_search_term(video.title))

    def fetch_metadata(self):
        # dont repeat if all the data's been already fetched
        if not self.fetch_type is None:    return

        # doing the url fetch in a thread and sleeping for a while 
        # since the execution of this function takes about 3 to 4 seconds
        # guess that's how you be lazy
        print(':::started the url fetch')
        threading._start_new_thread(self.__fetch_url, ())
        time.sleep(2)
        #self.__fetch_url()

        if self.__type == 'track_id':
            track = spotify.track(self.track_id)
        if self.__type == 'name':
            track_search = spotify.search(self.title, type = 'track', limit = 1)
            if len(track_search ['tracks'] ['items']) <= 0:
                print(':::track not available from spotify, doing a minimal fetch')
                if '-' in self.title:    self.artists = [self.title.split('-')[0].strip()]
                else:    self.artists = None
                self.__artists_names = None
                self.album = None
                self.track_id = None
                self.genres = None
                self.fetch_type = 'minimal'
                return
            else:    track = track_search ['tracks'] ['items'] [0]

        self.track_id = track['id']

        self.artists = []
        self.__artists_names = []
        for artist in track['artists']:
            self.artists.append(Artist(artist_id = artist['id']))
            self.__artists_names.append(artist['name'])

        self.genres = []
        for artist in self.artists:
            for genre in artist.genres:
                self.genres.append(genre)

        self.album = Album(album_id = track ['album'] ['id'])
            
        self.fetch_type = 'full'

        print(':::fetched')

    def send_notification(self):
        print(":::sending notif")
        # send notification

        # fetch metadata for the track if it has'nt already been fetched
        if self.fetch_type is None:
            self.fetch_metadata()
        message = ''
        if not self.__artists_names is None:
            message = self.__artists_names
            if len(message) == 1:    pass
            elif len(message) == 2:    message.insert(1, ' and ')
            else:
                increment = 1
                for i in range(len(message)):
                    if not i == len(message) - 1:
                        insert_index = i + increment
                        message.insert(insert_index, ' and ')
                        increment += insert_index + 1
            message = ''.join(message)
        if not self.album is None:
            message += f'\nfrom album {self.album.name}'
        notification.notify(
            title = self.title,
            message = message,
            app_icon = r'C:\users\gadit\downloads\music_icon0.ico',
            app_name = 'M E L O D I N E',
            timeout = 10,
            toast = False
            )

    def download(self, custom = None, no_part = True):
        global audio_downloader
        audio_downloader = YoutubeDL({
                            #'buffersize': 512,
                            #'http_chunk_size': 256,
                            #'audioformat': 'wav',
                            #'format': 'bestaudio',
                            'outtmpl': self.title + self.ext,
                            'extractaudio': True,
                            'retries': 5,
                            'continuedl': True,
                            'nopart': no_part,
                            'hls_prefer_native': True,
                            'quiet': True
                            })
        audio_downloader.extract_info(self.url)

    def play(self):
        self.fetch_metadata()
        self.download(no_part = True)
        print('::: downloaded')
        threading._start_new_thread(self.send_notification, ())

        self.player = MediaPlayer(self.filename)
        time.sleep(0.5)
        print('::: playing')

        last_pts = 0
        updated_pts = 0
        while True:
            updated_pts = int(float(str(self.player.get_pts())[: 3])) - 3
            print(':::updated', updated_pts)
            # print(player.get_pts())

            while self.player.get_pause():
                time.sleep(0.5)
            if updated_pts == last_pts:
                self.player.toggle_pause()
                print("---buffered out, pausing")
                time.sleep(1)
                self.player.toggle_pause()
            if int(float(str(self.player.get_pts())[: 3])) - 3 == int(float(str(self.player.get_metadata()['duration'])[: 3])) - 3:
                print(':::breaking')
                self.player.toggle_pause()
                self.player.close_player()
            
            last_pts = updated_pts
            time.sleep(1)
        print(':::finished playing')


class Artist:
    # stuff needed from an artists class
    #
    # id - spotify id for the album
    # name - name of the artist
    # genres - a list of all the genres from an artist
    # albums - a list of all the albums from an artist
    # top tracks - a list of top tracks (a list containing track objects for the top tracks)

    def __init__(self, name = None, artist_id = None):
        print(locals())
        self.name = name
        self.artist_id = artist_id
        type = None
        for attribute in [name, artist_id]:
            if not attribute is None:    type = [key for key, value in locals().items() if value == attribute] [0]
        if type == None:    raise NoAttributesSupplied
        if type == 'name':
            artist_search = spotify.search(self.name, type = 'artist', limit = 1)
            artist = artist_search['artists']['items'][0]
        elif type == 'artist_id':    artist = spotify.artist(artist_id)
        if len(artist) > 0:
            self.artist_id = artist ['id']
            self.name = artist ['name']
            self.genres = artist ['genres']
            self.top_tracks = [Track(track ['id']) for track in spotify.artist_top_tracks(artist_id) ['tracks']]
        else:    raise ObjectNotSearchable

    # a list of album objects containing the albums from the searched artist
    # make it's own method to get albums from an artiist and call tha method for whenever we need the albums 
    # since contructing all the albums for an artist is an expensive computation (shit ton of api requests)
    def fetch_albums(self, artist):
        self.albums = [Album(album ['id']) for album in spotify.artist_albums(self.artist_id) ['items']]


class Album:
    # stuff needed from a album
    #
    # id - spotify id for the album
    # name - the name of the album
    # artists - a list containing a artist object of all the artists from a album
    # tracks - a list containing track objects for all the tracks in a album
    # type - the type of album (a full album, or a single or smthng)

    def __init__(self, name = None, album_id = None):
        type = None
        for attribute in [name, album_id]:
            if not attribute is None:    type = [key for key, value in locals().items() if value == attribute] [0]
        if type == None:    raise NoAttributesSupplied
        if type == 'name':
            album_search = spotify.search(name, type = 'album', limit = 1)
            album = album_search ['albums'] ['items'] [0]
        elif type == 'album_id':    album = spotify.album(album_id)
        if len(album) > 0:
            self.album_id = album ['id']
            self.name = album ['name']
            self.artists = [Artist(artist_id = artist ['id']) for artist in album ['artists']]
            self.tracks = [Track(track ['id']) for track in spotify.album_tracks(album ['id']) ['items']]
            self.album_type = album ['type']
        else:    raise ObjectNotSearchable


    def list(self):
        pass





if __name__ == 'main':
    start = time.time()

    track = Track('憂鬱 - Sun')
    track.fetch_metadata()
    print(track.artists)

    end = time.time()
    print(end-start)

    print(':::playing track')
    track.play()
