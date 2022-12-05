# region Imports
import curses
from curses.textpad import Textbox, rectangle
from curses import wrapper
from ffpyplayer.player import MediaPlayer
from ffpyplayer.tools import set_log_callback, loglevels
import math
import melodine as melo
import os
import time
import utils
# endregion

# region to make ffpyplayer not output anything
loglevel_emit = 'error'
def log_callback(message, level):
    if message and loglevels[level] <= loglevels[loglevel_emit]:
        print ("error")

set_log_callback(log_callback)
# endregion
def main(stdscr):
    curses.noecho()
    global height
    global width
    global playing
    playing = False
    height, width = stdscr.getmaxyx()
    print(height)
    # Quits if terminal is too small
    if height < 14 or width < 40:
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()
        print("Terminal too small!")
        quit()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    # Initialises search box and player window
    box = draw_search_box(stdscr)
    playerwin = draw_player(stdscr)
    playerwin.refresh()
    curses.curs_set(0)
    while True:
        c = stdscr.getch()
        # If window resized redraw elements
        # FIXME: Does not redraw correctly
        if c == curses.KEY_RESIZE:
            if height < 14 or width < 40:
                curses.nocbreak()
                stdscr.keypad(False)
                curses.echo()
                curses.endwin()
                print("Terminal too small!")
                quit()
            box = draw_search_box(stdscr)
            playerwin = draw_player(stdscr)
            playerwin.refresh()
        if c == ord('/') :
            results = search(box, stdscr)
        elif c == ord('q'):
            curses.nocbreak()
            stdscr.keypad(False)
            curses.echo()
            curses.endwin()
            break
        elif c >= ord('0') and c <= ord('9'):
            selected = results[int(chr(c))]
            url = selected.url
            utils.put_notification(selected)
            player_update(playerwin, selected.artists[0].name, selected.name, selected.duration)
            ffplay(selected, playerwin)
        elif c == ord('p'):
            player.toggle_pause()
            player_update(playerwin)

# region Curses Functions
# Initialises player window with "Nothing Playing"
def draw_player(stdscr):
    playerwin = curses.newwin(5, width - 1, height - 5, 0)
    playerwin.border()
    playerwin.addstr(0, 1, "Nothing Playing", curses.color_pair(1) | curses.A_BOLD)
    playerwin.refresh()
    playing = False
    return playerwin

# Method to draw search box
def draw_search_box(stdscr):
    stdscr.addstr(0, 0, "Search (/ to focus):", curses.color_pair(1) | curses.A_BOLD)
    stdscr.keypad(True)
    editwin = curses.newwin(1,30, 2,1)
    rectangle(stdscr, 1,0, 1+1+1, 1+30+1)
    stdscr.refresh()
    box = Textbox(editwin)
    return box

# Updates player window with track data and progressbar
def player_update(player, artist=None, title=None, duration=None):
    minutes = math.floor(duration / 60)
    seconds = math.floor(duration % 60)
    playerwin = curses.newwin(5, width - 1, height - 5, 0)
    length = width - 16
    playerwin.border()
    if playing == True:
        playerwin.addstr(0, 1, "Paused", curses.color_pair(1) | curses.A_BOLD)
        playing == False
    else:
        playerwin.addstr(0, 1, "Playing", curses.color_pair(1) | curses.A_BOLD)
        playing == True
    if artist and title:
        playerwin.addstr(1, 2, title, curses.color_pair(2) | curses.A_BOLD)
        playerwin.addstr(2, 2, artist, curses.color_pair(1))
        playerwin.addstr(3, 2, "0:00")
        playerwin.addstr(3, width - 7, f"{minutes}:{'{:02d}'.format(seconds)}")
        playerwin.addstr(3, 8, "-" * length)
    playerwin.refresh()

def search(box, stdscr):
    curses.curs_set(1)
    box.edit()
    # Get resulting contents
    search = box.gather()
    # Print the window to the screen
    results = melo.spotify.search(search, types=['tracks']).tracks
    color = curses.has_colors()
    # Print results based on screensize, maxed at 10
    result_num = height - 9
    if height - 9 > 10:
        result_num = 10
    result_box = curses.newwin(result_num + 2, width - 1, 4, 0)
    result_box.border()
    result_box.addstr(0, 1, "Enter index number to play", curses.color_pair(1) | curses.A_BOLD)
    line = 1
    
    for result in results[:result_num]:
        name = str(result.name)
        artists_list = []
        for artist in result.artists:
            artists_list.append(str(artist.name))
        artists = ' & '.join(artists_list)
        if len(artists) > width/3:
            artists = result.artists[0].name
        if len(name) > width/3:
            name = name[:(int(width/3))]
        duration_minute, duration_seconds = math.floor(result.duration / 60), "{:02d}".format(math.floor(result.duration % 60))
        result_box.addstr(line, 1, f"{line - 1}. |{name}{(int(width/3) - len(name)) * ' '}|{artists}{(int(width/3) - len(artists)) * ' '}|{duration_minute}:{duration_seconds}")
        line += 1
        curses.curs_set(0)
        result_box.refresh()
    return results

# Updates progressbar
def progressbar(playerwin, pts, duration):
    length = width - 16
    percent = duration / length
    position = math.floor(pts / percent)
    playerwin.addstr(1, 30, f"%: {round(percent,2)}, len: {round(length,2)}, pts%%: {round(pts % percent, 2)}, pos: {position}, pts: {'{:03d}'.format(pts)}")
    playerwin.addstr(3, 8, "=" * position)
    minutes = math.floor(pts / 60)
    seconds = math.floor(pts % 60)
    playerwin.addstr(3, 2, f"{minutes}:{'{:02d}'.format(seconds)}")
    playerwin.refresh()
# endregion

def ffplay(track, playerwin):

    global player
    global vol

    opts = { 'loglevel': 'panic' }
    path = os.path.join(os.path.expanduser('~'), 'Music', track.id + '.mp3')
    if not os.path.exists(path):
        utils.get_music(track, track.id)
    player = MediaPlayer(path, loglevel='quiet')
    utils.put_notification(track)
    #threading._start_new_thread(discord_rpc.update_discord(), ())
    '''player.toggle_pause()
    time.sleep(1)
    player.toggle_pause()'''
    last_pts = 0
    updated_pts = 0
    while True:
        updated_pts = int(float(str(player.get_pts())[: 3])) - 3
        progressbar(playerwin, updated_pts + 3, player.get_metadata()['duration'])
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

        time.sleep(1)
        last_pts = updated_pts

wrapper(main)