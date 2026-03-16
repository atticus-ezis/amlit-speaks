from models import ShortStory, Chapter, ChildrenStory

stream_media_type = "audio/mpeg"

elevenlabs_voices = {
    "test": "t1fAowkucZX8hwnFep08",
    "alt-3": "UmQN7jS1Ee8B1czsUtQh",
    "alt-2": "4dZr8J4CBeokyRkTRpoN",
    "alt-1": "fjnwTZkKtQOJaYzGLa6n",
    "default": "fnYMz3F5gMEDGMWcH1ex",
}

model_lookup = {
    "short_story": ShortStory,
    "chapter": Chapter,
    "children_story": ChildrenStory,
}


audio_formats = {
    "audio/mpeg": "mp3_44100_128",
    "audio/ogg; codecs=opus": "opus_48000_64",
}

elevenlabs_formats = [
    "mp3_22050_32",  # this is "audio/mpeg"
    "mp3_24000_48",
    "mp3_44100_32",
    "mp3_44100_64",
    "mp3_44100_96",
    "mp3_44100_128",
    "mp3_44100_192",
    "pcm_8000",
    "pcm_16000",
    "pcm_22050",
    "pcm_24000",
    "pcm_32000",
    "pcm_44100",
    "pcm_48000",
    "ulaw_8000",
    "alaw_8000",
    "opus_48000_32",
    "opus_48000_64",  # this is "audio/ogg; codecs=opus"
    "opus_48000_96",
    "opus_48000_128",
    "opus_48000_192",
]
