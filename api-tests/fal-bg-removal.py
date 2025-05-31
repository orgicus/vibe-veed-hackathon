import fal_client

def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
           print(log["message"])

result = fal_client.subscribe(
    "fal-ai/bria/background/remove",
    arguments={
        "image_url": "./assets/GP-690px.jpg"
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)
print(result)