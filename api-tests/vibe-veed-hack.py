"""
1. service to upload a single user image  
    1. use cloudinary script, store the resuting URL
    2. upload the result URL to fal background removal
    3. store output video somewhere
2. service to take in effects prompt:
    - input = backround removal result
    - prompt (can contain effects)
3. service to take in promot to generate audio
    - use elevenlabs api script
    - store result
4. service to put it together
    - video effects .mp4 file
    - eleven labs .mp3 file
    - send to fal for lipsync
    - store result
5. when done notify/email URL
"""