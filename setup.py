import os

print("== Melodine Setup ==")
print("\nInstalling required dependencies...\n")

os.system("pip install -r requirements.txt")

print("\n...done\n")

melodine_dir = os.path.join(os.path.expanduser('~'), '.melodine')

if not os.path.exists(melodine_dir):
    os.mkdir(melodine_dir)
    os.mkdir(os.path.join(melodine_dir, 'music'))
    os.mkdir(os.path.join(melodine_dir, 'queue'))
    os.mkdir(os.path.join(melodine_dir, 'cover_art_dir'))
    os.mkdir(os.path.join(melodine_dir, 'playlists'))
    