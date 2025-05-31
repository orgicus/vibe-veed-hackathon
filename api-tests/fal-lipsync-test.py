import fal_client

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])

result = fal_client.subscribe(
    "veed/lipsync",
    arguments={
        "video_url": "https://v3.fal.media/files/koala/AFOar6hx4Ncgh2aREOntB_output.mp4",
        "audio_url": "https:/sensori.al/vibe-veed-hack/elevenlabs_output.mp3"
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)
print(result)