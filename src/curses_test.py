import curses
from curses.textpad import Textbox, rectangle
from curses import wrapper
import math
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import melodine as melo

scope = "user-read-playback-position user-top-read user-read-recently-played user-library-modify user-library-read"


def main(stdscr):
    curses.noecho()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    stdscr.addstr(0, 0, "Search:", curses.color_pair(1) | curses.A_BOLD)
    stdscr.keypad(True)
    editwin = curses.newwin(1,30, 2,1)
    rectangle(stdscr, 1,0, 1+1+1, 1+30+1)
    stdscr.refresh()
    box = Textbox(editwin)

    # Let the user edit until Ctrl-G is struck.
    box.edit()

    # Get resulting contents
    message = box.gather()

    # Print the window to the screen
    results = sp.search(message, type='track')
    color = curses.has_colors()
    width = stdscr.getmaxyx()[1] - 1
    result_box = curses.newwin(12, width, 5, 0)
    result_box.border()
    line = 1
    for result in results['tracks']['items']:
        name = result['name']
        artists_list = []
        for artist in result['artists']:
            artists_list.append(artist['name'])
        artists = ' & '.join(artists_list)
        if len(artists) > width/3:
            artists = result['artists'][0]['name']
        duration_minute, duration_seconds = math.floor(result['duration_ms'] / 1000 / 60), "{:02d}".format(math.floor(result['duration_ms'] / 1000 % 60))
        result_box.addstr(line, 1, f"{'{:02d}'.format(line)}. |{name}{(int(width/3) - len(name)) * ' '}|{artists}{(int(width/3) - len(artists)) * ' '}|{duration_minute}:{duration_seconds}")
        line += 1

    result_box.refresh()
    while True:
        c = stdscr.getch()
        if c == ord('q'):
            curses.nocbreak()
            stdscr.keypad(False)
            curses.echo()
            curses.endwin()
            break
    

wrapper(main)