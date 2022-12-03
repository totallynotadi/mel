import time

import pypresence 
client_id = 876122036697722891
try:
    RPC = pypresence.Presence(client_id=client_id)
    RPC.connect()
except:    pass

playing = False
avicii = "index"
def set_status(song_title, url="https://youtube.com/watch?v=dQw4w9WgXcQ"):
    start_time=time.time() # Using the time that we imported at the start. start_time equals time.
    RPC.update(buttons=[{"label": "Website", "url": url},
        {"label": "GitHub", "url": "https://github.com/addyett/Melodine"}],
        state=f"to {song_title}",
        details="Vibing",
        large_image="index",
        large_text="Never Gonna Give You Up",
        small_image="index", 
        small_text="Hello!", 
        start=start_time)
def update_discord():
    print("Updated")
    while True:
        time.sleep(15) #Can only update presence every 15 seconds

