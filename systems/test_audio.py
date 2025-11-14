# test_audio.py
from systems.audio import speak_word
speak_word("CAT", None)        # uses TTS
# or if you have an audio file:
print("Called speak_word; if audio device present you should hear something.")

