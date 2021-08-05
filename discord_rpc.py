import time

import discordsdk as dsdk

app = dsdk.Discord(872801340601040916, dsdk.CreateFlags.default)

activity_manager = app.get_activity_manager()
activity_manager.register_command("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
activity = dsdk.Activity()
activity.state = "Vibing"
activity.assets.large_image = "avicii"
activity.assets.small_image = "avicii"
activity.assets.large_text = "avicii"
activity.assets.small_text = "avicii"
activity.party.id = "musik"
activity.party.size.current_size = 1
activity.party.size.max_size = 8
activity.secrets.join = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def callback(result):
    if result == dsdk.Result.ok:
        print("Successfully set the activity!")
    else:
        raise Exception(result)

def run(song_title):
    activity.details = f"to {song_title}"
    activity_manager.update_activity(activity, callback)
    # Don't forget to call run_callbacks
    while 1:
        time.sleep(1/10)
        app.run_callbacks()

