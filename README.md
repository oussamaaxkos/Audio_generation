Flask Application Project with AI and Voice Assistant

Project Description

This project is a web application developed with Flask that integrates artificial intelligence technologies for audio processing (text-to-speech and speech-to-text) and audio track separation. It also includes a voice assistant and user management with a MySQL database.

Features

• Audio Track Separation (Demucs): Allows separating instruments and vocals from an audio file.

• Text-to-Speech (TTS): Converts text into speech.

• Speech-to-Text (STT): Converts speech into text.

• Voice Assistant: An integrated voice assistant capable of recognizing commands and performing actions (opening applications, getting location, etc.).

• User Management: User registration and login with data storage in a MySQL database.

• Job Tracking: Tracks the status of background audio separation tasks.

• File Download: Ability to download processed audio files.

• Old Job Cleanup: Functionality to clean up temporary files and expired jobs.

• Location Detection: Uses the ipinfo.io API to get the user's location.

Technologies Used

• Backend: Flask (Python)

• Audio Processing: Demucs, speech_recognition, pyttsx3

• Database: MySQL

• Other Python Libraries: os, uuid, time, subprocess, datetime, threading, requests, werkzeug.utils, torch, webbrowser, random, re, sys, mysql.connector

Installation

Prerequisites

• Python 3.x

• pip (Python package manager)

• MySQL Server

• ffmpeg (for audio conversion)

Installation Steps

1. Clone the repository (if applicable):

2. Create a virtual environment (recommended):

3. Install Python dependencies:

4. MySQL Database Configuration:

• Create a database named ms (or whatever you configured in app.py).

• Create the users and outputs tables with the following schemas (adjust if necessary):



5. Install ffmpeg:

• On Ubuntu/Debian:

• On macOS (with Homebrew):

• On Windows: Download the executable from the official FFmpeg website and add it to your PATH.



Usage

1. Run the Flask application:

2. Access the application:
Open your web browser and go to http://127.0.0.1:5000 (or the configured port).

3. Application Features:

• Sign Up/Login: Create an account or log in.

• Audio Upload: Upload an audio file for track separation.

• Voice Assistant : Interact with the voice assistant via commands defined in the code.



