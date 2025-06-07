import whisper
from googletrans import Translator
from gtts import gTTS

# Transcription
model = whisper.load_model("base")
result = model.transcribe("audio_en.mp3")
english_text = result["text"]
print("Transcribed:", english_text)

# Traduction
translator = Translator()
arabic_text = translator.translate(english_text, src='en', dest='ar').text
print("Translated:", arabic_text)

# Synthèse vocale
tts = gTTS(arabic_text, lang='ar')
tts.save("translated_arabic.mp3")
