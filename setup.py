pip install -r requirements.txt
spotipy_dir = os.path.join(os.path.expanduser('~'), 'SpotiPy')
if not os.path.exists(spotipy_dir):
	os.mkdir(spotipy_dir)
	os.mkdir(os.path.join(spotipy_dir, 'music'))
	os.mkdir(os.path.join(spotipy_dir, 'queue'))
	os.mkdir(os.path.join(spotipy_dir, 'cover_art_dir'))
	os.mkdir(os.path.join(spotipy_dir, 'playlists'))