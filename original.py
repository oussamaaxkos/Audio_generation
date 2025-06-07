import speech_recognition as sr
import pyttsx3
import webbrowser
import os
import subprocess
import datetime
import random
import re
import time
import sys

class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        
        # Configure voice properties
        self.engine.setProperty('rate', 180)  # Speed of speech
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)  # Female voice
        
        # Define command patterns
        self.command_patterns = {
            'open_settings': [r'(open|launch|start|show|access|bring up|display|get to|navigate to).*settings',
                              r'(settings|preferences|options|configuration).*open',
                              r'(change|modify|adjust|tweak).*settings',
                              r'(let me|need to|want to|would like to|have to|can i|may i).*settings',
                              r'(take me to|go to|head to).*settings'],
            'open_chrome': [r'(open|launch|start|run|execute|bring up|load).*chrome',
                            r'(browse|surf|search|look).*web',
                            r'(chrome|google chrome|browser).*open',
                            r'(let me|need to|want to|would like to).*chrome',
                            r'i need to (use|access) chrome'],
            'open_youtube': [r'(open|launch|start|watch|view|bring up|load).*youtube',
                             r'(videos|watch videos|streaming).*youtube',
                             r'(youtube|video platform).*open',
                             r'(let me|need to|want to|would like to).*youtube',
                             r'(check out|see).*youtube'],
            'open_facebook': [r'(open|launch|start|check|view|bring up|load).*facebook',
                              r'(social media|facebook feed|timeline).*facebook',
                              r'(facebook|social network).*open',
                              r'(let me|need to|want to|would like to).*facebook',
                              r'(check out|see).*facebook'],
            'open_spotify': [
                                r'(open|launch|start|run|play|bring up|load).*spotify',
                                r'(let me|need to|want to|would like to).*spotify',
                                r'(music|songs|playlist).*spotify',
                                r'listen.*(music|spotify|songs)',
                                r'(spotify|music app).*open'
                            ],
            
            'open_and_play_spotify': [
                                r'(open|launch).*spotify.*(play|listen|song|music|track)?',
                                r'i want to listen.*spotify',
                                r'play.*spotify',
                                r'(spotify).*play.*'
                            ],


            'get_time': [r'what.*time.*is.*it',
                         r'(tell|know|check|give).*time',
                         r'(current|present) time',
                         r'time.*now',
                         r'(what is|got|have).*clock'],
            'get_date': [r'what.*date.*is.*it',
                         r'(tell|know|check|give).*date',
                         r'(current|present|today\'s) date',
                         r'date.*today',
                         r'(what is|got|have).*calendar'],
            'exit': [r'(exit|quit|close|stop|end|terminate|goodbye|bye|see you|later)',
                     r'(shut|turn) (down|off)',
                     r'that\'s all',
                     r'(i\'m|i am) (done|finished)',
                     r'stop (listening|running)']
        }

        # Predefined responses
        self.responses = {
            'greetings': ["Hi there! How can I assist you today?", "Hello! What can I help you with?", 
                          "Nice to hear you! How may I be of service?", "Greetings! What would you like me to do?",
                          "Hey there! I'm ready to help you out!"],
            'morning_responses': ["Good morning! How are you today?", "Morning sunshine! Ready for the day?",
                                  "Top of the morning to you! What's on your agenda?", "Good morning! How did you sleep?",
                                  "Morning! Let's make today a great day!"],
            'acknowledge': ["I'm on it!", "Right away!", "Consider it done!", "Working on that for you now.",
                            "Processing your request."],
            'farewells': ["Goodbye! Have a wonderful day!", "See you later! Take care!", 
                          "Have a great day! Call me when you need me.", "Goodbye! It was nice talking with you.",
                          "Until next time! Stay well!"],
            'not_understood': ["I didn't quite catch that. Could you try again?", 
                               "Sorry, I'm not sure what you mean. Can you rephrase?",
                               "I didn't understand that command. Can you say it differently?",
                               "Hmm, I'm having trouble understanding. Could you repeat that?",
                               "That command is unfamiliar to me. Can you try another way?"],
            'thinking': ["Let me think about that...", "Processing your request...", 
                         "Just a moment while I work on that...", "I'm figuring that out for you...",
                         "Working on your request..."]
        }

        # Action functions
        self.actions = {
            'open_settings': self.open_settings,
            'open_chrome': self.open_chrome,
            'open_youtube': lambda: self.open_website("https://youtube.com", "YouTube"),
            'open_facebook': lambda: self.open_website("https://facebook.com", "Facebook"),
            'get_time': self.get_time,
            'get_date': self.get_date,
            'exit': self.exit_assistant,
            'open_spotify': self.open_spotify,
            'open_and_play_spotify': self.open_and_play_spotify,


        }

        self.is_running = True

    def speak(self, text):
        print(f"Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def think(self):
        self.speak(random.choice(self.responses['thinking']))
        time.sleep(random.uniform(0.5, 1.5))

    def open_settings(self):
        self.think()
        self.speak("Opening settings.")
        subprocess.run('start ms-settings:', shell=True)

    def open_chrome(self):
        self.think()
        self.speak("Launching Chrome.")
        try:
            chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'
            webbrowser.get(chrome_path).open('https://www.google.com')
        except:
            webbrowser.open('https://www.google.com')
    def open_spotify(self):
        """Opens Spotify application with natural interaction"""
        self.think()
        self.speak(random.choice([
            "Opening Spotify for you.",
            "Starting up Spotify.",
            "Let me get your music ready on Spotify.",
            "Bringing up Spotify now.",
            "Launching Spotify. Get ready to vibe!"
            
        ]))
        time.sleep(0.5)
        try:
            # Try launching installed Spotify (Windows default path)
            spotify_path = "C:/Users/{}/AppData/Roaming/Spotify/Spotify.exe".format(os.getlogin())
            os.startfile(spotify_path)
        except Exception:
            # Fallback to Spotify web
            self.speak("I couldn't find the app, opening Spotify in your browser instead.")
            webbrowser.open("https://open.spotify.com")


    def open_website(self, url, name):
        self.think()
        self.speak(f"Opening {name}.")
        webbrowser.open(url)

    def get_time(self):
        self.think()
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        self.speak(f"The time is {current_time}.")

    def get_date(self):
        self.think()
        today = datetime.date.today().strftime("%A, %B %d, %Y")
        self.speak(f"Today is {today}.")

    def exit_assistant(self):
        self.speak(random.choice(self.responses['farewells']))
        self.is_running = False

    def interpret_command(self, text):
        text = text.lower()

        if any(greeting in text for greeting in ["hi", "hello", "hey"]):
            self.speak(random.choice(self.responses['greetings']))
            return

        if "good morning" in text:
            self.speak(random.choice(self.responses['morning_responses']))
            return

        if "how are you" in text:
            self.speak("I'm doing great! How about you?")
            return

        if "your name" in text:
            self.speak("I'm your personal voice assistant, always ready to help!")
            return

        for command, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    self.actions[command]()
                    return
                    
    def open_and_play_spotify(self):
        """Opens Spotify and plays music based on user's request"""
        self.think()
        self.speak("I'll help you play some music. What would you like to listen to?")
        
        try:
            query = self.listen(return_text=True)  # Get what the user wants to hear
            if not query:
                self.speak("I didn't catch what you wanted to listen to. Please try again.")
                return
                
            self.speak(f"Great choice! Looking for {query} on Spotify.")
            
            # First attempt - try direct play with Spotify desktop app
            try:
                # Clean query and format for Spotify URI
                query_encoded = query.replace(" ", "%20")
                
                # Try the direct play URI format (most effective)
                direct_uri = f"spotify:search:{query_encoded}"
                os.system(f'start {direct_uri}')
                
                # Wait for app to load
                time.sleep(2)
                
                # Inform user to help complete the action
                self.speak("I've opened Spotify. Please select a song from the search results to play.")
                return
                
            except Exception as e:
                print(f"Desktop app attempt failed: {e}")
                pass
                
            # Second attempt - open Spotify web player with search
            try:
                self.speak("Opening Spotify in your web browser.")
                
                # Force the track search over general search for better results
                url = f"https://open.spotify.com/search/{query_encoded}/tracks"
                webbrowser.open(url)
                
                time.sleep(1)
                self.speak("I've found some matching tracks. Click on one to play it.")
                
            except Exception as e:
                # Last resort - plain Spotify with instructions
                self.speak("I'm having trouble with specific searches. Opening Spotify homepage.")
                webbrowser.open("https://open.spotify.com")
                time.sleep(1)
                self.speak(f"Please use the search bar to find {query}.")
                print(f"Web player error: {e}")
                
        except Exception as e:
            self.speak("Sorry, I encountered an issue connecting to Spotify.")
            print(f"Error in open_and_play_spotify: {e}")

    def listen(self, return_text=False):
        with sr.Microphone() as mic:
            print("\nListening...")
            self.recognizer.adjust_for_ambient_noise(mic, duration=0.5)
            try:
                audio = self.recognizer.listen(mic, timeout=5)
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                if return_text:
                    return text
                self.interpret_command(text)
            except sr.WaitTimeoutError:
                print("Listening timed out. No speech detected.")
            except sr.UnknownValueError:
                self.speak("Sorry, I didn't understand what you said.")
            except sr.RequestError as e:
                self.speak("There was a problem with the speech recognition service.")
                print(f"API Error: {e}")
            return None


    def run(self):
        self.speak("Assistant initialized and ready.")
        while self.is_running:
            self.listen()

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
