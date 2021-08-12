import time

import pypresence 
client_id = 872801340601040916
RPC = pypresence.Presence(client_id=client_id)
RPC.connect()

playing = False
avicii = "avicii"
def set_status(song_title):
    start_time=time.time() # Using the time that we imported at the start. start_time equals time.
    RPC.update(buttons=[{"label": "Website", "url": "https:/youtube.com/watch?v=dQw4w9WgXcQ"}, {"label": "GitHub", "url": "https://github.com/addyett/Melodine"}], state=f"to {song_title}", details="Vibing", large_image="avicii", large_text="Never Gonna Give You Up",
            small_image="avicii", small_text="Hello!", start=start_time)
def update_discord():
    print("Updated")
    while True:
        time.sleep(15) #Can only update presence every 15 seconds

