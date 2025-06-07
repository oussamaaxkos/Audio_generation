import whisper
from deep_translator import GoogleTranslator
import elevenlabs
from dotenv import load_dotenv
import os

def main():
    # Load API key from .env file
    load_dotenv()
    api_key = os.getenv("ELEVEN_API_KEY")
    if not api_key:
        raise EnvironmentError("ELEVEN_API_KEY not found in .env file")

    # Set API key in environment for elevenlabs
    os.environ["ELEVEN_API_KEY"] = api_key
    
    # Get elevenlabs version
    elevenlabs_version = getattr(elevenlabs, "__version__", "unknown")
    print(f"Using elevenlabs version: {elevenlabs_version}")
    
    try:
        # First, let's explore the structure to find the right methods
        print("Exploring voices client structure...")
        if hasattr(elevenlabs.voices, "client"):
            client = elevenlabs.voices.client
            
            # Try to get available voices
            if hasattr(client, "get_all_voices"):
                available_voices = client.get_all_voices()
                print("Successfully got voices using client.get_all_voices()")
            elif hasattr(client, "get_voices"):
                available_voices = client.get_voices()
                print("Successfully got voices using client.get_voices()")
            elif hasattr(client, "get_all"):
                available_voices = client.get_all()
                print("Successfully got voices using client.get_all()")
            elif hasattr(client, "list"):
                available_voices = client.list()
                print("Successfully got voices using client.list()")
            else:
                print("Available methods in elevenlabs.voices.client:")
                for name in dir(client):
                    if not name.startswith("__"):
                        print(f"- {name}")
                raise ValueError("Could not find a method to get voices")
        else:
            raise ValueError("elevenlabs.voices.client not found")
        
        # Display available voices
        print("\nAvailable voices:")
        for i, voice in enumerate(available_voices):
            # Try different attributes that might contain the name
            name = None
            if hasattr(voice, "name"):
                name = voice.name
            elif hasattr(voice, "voice_name"):
                name = voice.voice_name
            elif hasattr(voice, "display_name"):
                name = voice.display_name
            else:
                name = str(voice)
            
            # Try to get voice ID
            voice_id = None
            if hasattr(voice, "voice_id"):
                voice_id = voice.voice_id
            elif hasattr(voice, "id"):
                voice_id = voice.id
                
            # Print with ID if available
            if voice_id:
                print(f"{i+1}. {name} (ID: {voice_id})")
            else:
                print(f"{i+1}. {name}")
        
        # Select voice
        voice_index = input("\nSelect a voice number from the list above (default: 1): ")
        try:
            voice_index = int(voice_index) - 1
            if voice_index < 0 or voice_index >= len(available_voices):
                print(f"Invalid selection. Using the first voice.")
                voice_index = 0
        except ValueError:
            print("Invalid input. Using the first voice.")
            voice_index = 0
        
        selected_voice = available_voices[voice_index]
        
        # Get the voice ID (required for text_to_speech)
        voice_id = None
        if hasattr(selected_voice, "voice_id"):
            voice_id = selected_voice.voice_id
        elif hasattr(selected_voice, "id"):
            voice_id = selected_voice.id
        else:
            # Try to find any attribute that might be an ID
            for attr_name in dir(selected_voice):
                if "id" in attr_name.lower() and not attr_name.startswith("__"):
                    voice_id = getattr(selected_voice, attr_name)
                    break
        
        if not voice_id:
            raise ValueError("Could not determine voice ID for selected voice")
            
        # Get voice name for display
        voice_name = None
        if hasattr(selected_voice, "name"):
            voice_name = selected_voice.name
        elif hasattr(selected_voice, "voice_name"):
            voice_name = selected_voice.voice_name
        elif hasattr(selected_voice, "display_name"):
            voice_name = selected_voice.display_name
        else:
            voice_name = str(selected_voice)
            
        print(f"Selected voice: {voice_name} (ID: {voice_id})")
        
        # Load audio file
        print("\nLoading Whisper model...")
        model = whisper.load_model("base")
        
        # Path to your audio file
        audio_file = input("Enter the path to your audio file: ")
        if not os.path.exists(audio_file):
            print(f"File not found: {audio_file}")
            return
        
        # Transcribe audio
        print("Transcribing audio...")
        result = model.transcribe(audio_file)
        transcription = result["text"]
        print(f"\nOriginal text: {transcription}")
        
        # Detect language
        detected_language = result.get("language", "en")
        print(f"Detected language: {detected_language}")
        
        # Choose target language for translation
        target_language = input("Enter target language code (e.g., 'en' for English, 'fr' for French): ")
        
        # Translate text
        print("Translating text...")
        translator = GoogleTranslator(source=detected_language, target=target_language)
        translated_text = translator.translate(transcription)
        print(f"\nTranslated text: {translated_text}")
        
        # Generate speech from translated text
        print("Generating speech from translated text...")
        
        # Try to find the right text-to-speech function
        if hasattr(elevenlabs, "text_to_speech") and callable(elevenlabs.text_to_speech):
            audio = elevenlabs.text_to_speech(text=translated_text, voice_id=voice_id)
            print("Used elevenlabs.text_to_speech")
        elif hasattr(elevenlabs.text_to_speech, "generate"):
            audio = elevenlabs.text_to_speech.generate(text=translated_text, voice_id=voice_id)
            print("Used elevenlabs.text_to_speech.generate")
        elif hasattr(elevenlabs.text_to_speech, "synthesize"):
            audio = elevenlabs.text_to_speech.synthesize(text=translated_text, voice_id=voice_id)
            print("Used elevenlabs.text_to_speech.synthesize")
        elif hasattr(elevenlabs.text_to_speech, "client") and hasattr(elevenlabs.text_to_speech.client, "generate"):
            audio = elevenlabs.text_to_speech.client.generate(text=translated_text, voice_id=voice_id)
            print("Used elevenlabs.text_to_speech.client.generate")
        else:
            print("Could not find a suitable text-to-speech method. Available in text_to_speech:")
            for name in dir(elevenlabs.text_to_speech):
                if not name.startswith("__"):
                    print(f"- {name}")
            return
        
        # Save the audio
        output_file = f"translated_output_{target_language}.mp3"
        with open(output_file, "wb") as f:
            f.write(audio)
        
        print(f"Audio saved to {output_file}")
        
        # Play the audio
        play_option = input("Do you want to play the audio? (y/n): ")
        if play_option.lower() == 'y':
            if hasattr(elevenlabs, "play") and callable(elevenlabs.play):
                elevenlabs.play(audio)
                print("Playing audio using elevenlabs.play")
            else:
                print("Play function not found in elevenlabs library.")
                print("The audio has been saved and can be played using another media player.")
                
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()