import fal_client

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])

result = fal_client.subscribe(
    "fal-ai/pixverse/v4.5/image-to-video/fast",
    arguments={
        "prompt": "Many rainbow unicorns and bubbles in the background",
        "image_url": "https://v3.fal.media/files/elephant/UqJWRm_nNoFWLWtlZ4ty-_bd00b1cf45c647e78851b8d8cfab4c89.png"
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)
print(result)