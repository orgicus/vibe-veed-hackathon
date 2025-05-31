import asyncio
import fal_client

async def subscribe():
    handler = await fal_client.submit_async(
        "fal-ai/bria/background/remove",
        arguments={
            "image_url": "./assets/GP-690px.jpg"
        },
    )

    async for event in handler.iter_events(with_logs=True):
        print(event)

    result = await handler.get()

    print(result)


if __name__ == "__main__":
    asyncio.run(subscribe())