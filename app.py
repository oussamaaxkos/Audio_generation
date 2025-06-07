from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for, jsonify, session
import os
import uuid
import time
import subprocess
import datetime
from threading import Thread
import requests
from werkzeug.utils import secure_filename
from demucs.apply import apply_model
from demucs.pretrained import get_model
from demucs.audio import AudioFile
import torch
import speech_recognition as sr
import pyttsx3
import webbrowser
import random
import re
import sys
import threading
import mysql.connector



# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'flac', 'ogg'}
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload
app.secret_key = os.urandom(24)  # Add secret key for session management

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)



# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="ms"
)


def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="ms"
    )
    return conn


# Track job status
processing_jobs = {}

# Global variable to store location data
current_location = None

# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def log(msg):
    print(f"[*] {msg}")

def convert_to_wav_with_ffmpeg(source_np, samplerate, output_path):
    subprocess.run([
        'ffmpeg', '-y', '-f', 'f32le', '-ar', str(samplerate),
        '-ac', str(source_np.shape[1]), '-i', 'pipe:0', output_path
    ], input=source_np.astype('float32').tobytes(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

import mysql.connector


def separate_audio(input_path, output_dir, job_id, user_id, model_name='htdemucs'):
    try:
        processing_jobs[job_id]['status'] = 'processing'
        
        os.makedirs(output_dir, exist_ok=True)
        log("Loading Demucs model...")
        model = get_model(model_name)
        device = "cuda" if torch.cuda.is_available() and not model.cpu else "cpu"
        
        log(f"Reading audio: {input_path}")
        wav = AudioFile(input_path).read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)
        
        log("Separating stems...")
        sources = apply_model(model, wav[None], device=device)[0]
        
        results = {}
        for name, source in zip(model.sources, sources):
            stem_path = os.path.join(output_dir, f"{name}.wav")
            convert_to_wav_with_ffmpeg(source.cpu().numpy().T, model.samplerate, stem_path)
            results[name] = f"{name}.wav"
            log(f"Saved: {stem_path}")
        
        # ✅ Save folder name to MySQL
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="ms"
            )
            cursor = conn.cursor()
            insert_query = "INSERT INTO outputs (s, user_id) VALUES (%s, %s)"
            cursor.execute(insert_query, (output_dir,user_id))
            conn.commit()
            cursor.close()
            conn.close()
            log(f"✅ Folder name '{output_dir}' inserted into 'outputs' table.")
        except Exception as db_err:
            log(f"⚠️ Database error: {db_err}")
        
        processing_jobs[job_id]['status'] = 'completed'
        processing_jobs[job_id]['results'] = results
        log("✅ Done! All stems extracted without noise filtering.")
    
    except Exception as e:
        processing_jobs[job_id]['status'] = 'failed'
        processing_jobs[job_id]['error'] = str(e)
        log(f"Error processing {input_path}: {e}")


def verify_user(email, password):
    """
    Vérifie si un utilisateur existe avec l'email et le mot de passe donnés.
    Retourne un dictionnaire avec id, nom, email si trouvé, sinon None.
    """
    try:
        # Connexion à la base de données
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="ms"
        )
        
        cursor = conn.cursor()
        
        # Requête SQL pour obtenir les informations nécessaires
        query = "SELECT id, name, email FROM users WHERE email = %s AND password = %s"
        cursor.execute(query, (email, password))
        
        # Récupération d'une seule ligne (si trouvée)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Si trouvé, retourne les données dans un dictionnaire
        if result:
            return {
                "id": result[0],
                "nom": result[1],
                "email": result[2]
            }
        else:
            return None
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login page display and form submission"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Vérifie si les identifiants sont corrects
        user = verify_user(email, password)
        
        if user:
            # Stocker l'utilisateur dans la session
            session['user'] = user  # On peut stocker tout l'objet user
            
            user_id = user['id']
            
            # Récupérer les outputs de cet utilisateur
            try:
                conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="",
                    database="ms"
                )
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM outputs WHERE user_id = %s", (user_id,))
                outputs = cursor.fetchall()
                cursor.close()
                conn.close()
            except Exception as e:
                flash(f"Erreur de base de données: {e}", "error")
                outputs = []

            # Afficher la page index avec outputs
            return render_template('index.html', user=user, outputs=outputs)
        
        else:
            flash('Incorrect email or password.', 'error')
            return render_template('login.html')

    return render_template('login.html')





@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Insérer les données dans la table users
            query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
            cursor.execute(query, (name, email, password))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            flash('Compte créé avec succès!', 'success')
            return redirect(url_for('login'))
            
        except mysql.connector.Error as err:
            flash(f'Erreur: {err}', 'error')
            return render_template('signup.html')
    
    return render_template('signup.html')


def get_location():
    try:
        res = requests.get("https://ipinfo.io/json")
        data = res.json()
        loc = data.get("loc", "0,0").split(',')
        return {
            "latitude": float(loc[0]),
            "longitude": float(loc[1]),
            "city": data.get("city", "Unknown City"),
            "region": data.get("region", "Unknown Region"),
            "country": data.get("country", "Unknown Country")
        }
    except:
        return {"latitude": 0, "longitude": 0, "city": "Unknown", "region": "", "country": ""}

# Flask Routes
@app.route('/', methods=["GET", "POST"])
def index():
    global current_location
    return render_template('home.html')


from flask import session

@app.route('/start')
def start():
    global current_location
    
    # Récupérer l'utilisateur connecté
    user = session.get('user')
    
    if not user:
        flash("Vous devez être connecté pour voir vos fichiers.", "error")
        return redirect('/login')

    user_id = user['id']
    
    # Connexion à la base et récupération des outputs
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="ms"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM outputs WHERE user_id = %s", (user_id,))
        outputs = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        flash(f"Erreur base de données: {str(e)}", "error")
        outputs = []

    # Envoyer à index.html
    return render_template('index.html', location=current_location, outputs=outputs)



@app.route('/get_current_location')
def get_current_location():
    global current_location
    # Return the current location data as JSON
    return jsonify(current_location or {})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400
    
    file = request.files['file']
    if file.filename == '':
        return {'error': 'No selected file'}, 400
    
    if file and allowed_file(file.filename):
        # Generate unique ID for this job
        job_id = str(uuid.uuid4())
        
        # Create job output directory
        job_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)

        os.makedirs(job_output_dir, exist_ok=True)
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
        file.save(input_path)
        
        # Initialize job tracking
        processing_jobs[job_id] = {
            'id': job_id,
            'original_filename': filename,
            'input_path': input_path,
            'output_dir': job_output_dir,
            'status': 'queued',
            'created_at': time.time()
        }

        user_id = session.get('user', {}).get('id')

        # Start processing in background
        thread = Thread(target=separate_audio, args=(input_path, job_output_dir, job_id, user_id))
        thread.daemon = True
        thread.start()
        
        return {'job_id': job_id, 'status': 'queued'}, 202
    
    return {'error': 'File type not allowed'}, 400

@app.route('/status/<job_id>')
def job_status(job_id):
    if job_id not in processing_jobs:
        return {'error': 'Job not found'}, 404
    job = processing_jobs[job_id]
    response = {
        'id': job_id,
        'status': job['status'],
        'created_at': job['created_at']
    }
    
    if job['status'] == 'completed':
        response['results'] = {}
        for stem, filename in job['results'].items():
            response['results'][stem] = url_for('download_file', job_id=job_id, filename=filename, _external=True)
    
    if job['status'] == 'failed' and 'error' in job:
        response['error'] = job['error']
    
    return response

@app.route('/download/<job_id>/<filename>')
def download_file(job_id, filename):
    if job_id not in processing_jobs or processing_jobs[job_id]['status'] != 'completed':
        return {'error': 'Results not available'}, 404
    
    output_dir = processing_jobs[job_id]['output_dir']
    return send_from_directory(output_dir, filename)

@app.route('/cleanup', methods=['POST'])
def cleanup_old_jobs():
    # Optional endpoint to clean up old jobs
    current_time = time.time()
    expired_jobs = [job_id for job_id, job in processing_jobs.items() 
                   if current_time - job['created_at'] > 3600]  # 1 hour expiration
    
    for job_id in expired_jobs:
        job = processing_jobs[job_id]
        # Delete input file
        if os.path.exists(job['input_path']):
            os.remove(job['input_path'])
        
        # Delete output directory
        if os.path.exists(job['output_dir']):
            for file in os.listdir(job['output_dir']):
                os.remove(os.path.join(job['output_dir'], file))
            os.rmdir(job['output_dir'])
        
        # Remove from tracking
        del processing_jobs[job_id]
    
    return {'message': f'Cleaned up {len(expired_jobs)} expired jobs'}, 200

engine = pyttsx3.init()
speak_lock = threading.Lock()

# Voice Assistant Class
class VoiceAssistant:
    def __init__(self):
        print("DEBUG: Initializing VoiceAssistant")
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        
        # Configure voice properties
        print("DEBUG: Configuring voice properties")
        self.engine.setProperty('rate', 180)  # Speed of speech
        voices = self.engine.getProperty('voices')
        print(f"DEBUG: Available voices: {len(voices)}")
        for i, voice in enumerate(voices):
            print(f"DEBUG: Voice {i}: {voice.id}")
        self.engine.setProperty('voice', voices[1].id)  # Female voice
        print(f"DEBUG: Selected voice: {voices[1].id}")
        
        # Define command patterns
        self.command_patterns = {
            'open_settings': [r'(open|launch|start|show|access|bring up|display|get to|navigate to).*settings',
                              r'(settings|preferences|options|configuration).*open',
                              r'(change|modify|adjust|tweak).*settings',
                              r'(let me|need to|want to|would like to|have to|can i|may i).*settings',
                              r'(take me to|go to|head to).*settings',
                              r'(go back to|return to|reopen).*settings'],
            'where_am_i': [
                            r'(where|what|tell me).*(am i|is my location|is my position)',
                            r'(location|position|place).*(where|what)',
                            r'(find|locate|show).*(me|my location|my position)'
            ],
            'open_chrome': [r'(open|launch|start|run|execute|bring up|load).*chrome',
                            r'(browse|surf|search|look).*web',
                            r'(chrome|google chrome|browser).*open',
                            r'(let me|need to|want to|would like to).*chrome',
                            r'i need to (use|access) chrome',
                            r'(go back to|return to|reopen).*chrome'],
            'open_youtube': [r'(open|launch|start|watch|view|bring up|load).*youtube',
                             r'(videos|watch videos|streaming).*youtube',
                             r'(youtube|video platform).*open',
                             r'(let me|need to|want to|would like to).*youtube',
                             r'(check out|see).*youtube',
                             r'(go back to|return to|reopen).*youtube'],
            'open_facebook': [r'(open|launch|start|check|view|bring up|load).*facebook',
                              r'(social media|facebook feed|timeline).*facebook',
                              r'(facebook|social network).*open',
                              r'(let me|need to|want to|would like to).*facebook',
                              r'(check out|see).*facebook',
                              r'(go back to|return to|reopen).*facebook'],
            'open_spotify': [
                                r'(open|launch|start|run|play|bring up|load).*spotify',
                                r'(let me|need to|want to|would like to).*spotify',
                                r'(music|songs|playlist).*spotify',
                                r'listen.*(music|spotify|songs)',
                                r'(spotify|music app).*open',
                                r'(go back to|return to|reopen).*spotify'
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
            'where_am_i': self.get_my_location,  # Added the where_am_i handler
        }

        self.is_running = True

    def speak(self, text):
        def _speak(text):
            with speak_lock:  # 🔒 Lock access to engine
                print(f"DEBUG: Attempting to speak: {text}")
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                    print(f"DEBUG: Successfully spoke: {text}")
                except Exception as e:
                    print(f"DEBUG: Error in speak: {str(e)}")
        threading.Thread(target=_speak, args=(text,)).start()

    def think(self):
        self.speak(random.choice(self.responses['thinking']))
        time.sleep(random.uniform(0.5, 1.5))

    # Added new method to handle "where am I" command
    def get_my_location(self):
        """Gets and communicates user's current location"""
        global current_location
        
        self.think()
        self.speak("Let me find your location.")
        
        try:
            # Get location data
            location_data = get_location()
            current_location = location_data  # Update the global location variable
            
            # Prepare a human-friendly response
            location_message = f"You are currently in {location_data['city']}, {location_data['region']}, {location_data['country']}."
            
            # Communicate the location to the user
            self.speak(location_message)
            
            # Log the location data
            print(f"Location found: {location_data}")
            
            # Let the user know they can see this on the web interface
            self.speak("I've updated the map in your browser with your current location.")
            
            # Refresh the page to show the location (optional)
            # webbrowser.open('http://localhost:5000/start')
            
            return location_data
            
        except Exception as e:
            self.speak("I'm having trouble determining your location right now.")
            print(f"Error getting location: {e}")
            return None

    def open_settings(self):
        print("Thinking...")
        self.think()
        print("speaking")
        self.speak("Opening settings.")
        print("Trying to open settings...")
        try:
            os.system("start ms-settings:")
        except Exception as e:
            self.speak("Sorry, I couldn't open settings.")
            print(f"Error: {e}")

    def open_chrome(self):
        print("DEBUG: Starting open_chrome method")
        self.think()
        print("DEBUG: About to speak 'Launching Chrome'")
        self.speak("Launching Chrome.")
        print("DEBUG: After speak command")
        try:
            chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'
            webbrowser.get(chrome_path).open('https://www.google.com')
            print("DEBUG: Chrome opened successfully")
        except Exception as e:
            print(f"DEBUG: Error opening Chrome: {str(e)}")
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

# Initialize voice assistant and listen for commands
voice_assistant = VoiceAssistant()
@app.route("/start_voice_assistant")
def start_voice_assistant():
    threading.Thread(target=voice_assistant.run).start()  # Fixed the target (removed the parentheses)
    return "Voice assistant started", 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')