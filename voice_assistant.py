import pyttsx3
import pyaudio
import json
from vosk import Model, KaldiRecognizer
import sqlite3
import time

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 180)  # Set speech rate

# Database setup function
def setup_database():
    conn = sqlite3.connect("assistant_responses.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS responses (
                        question TEXT PRIMARY KEY,
                        answer TEXT)''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_question ON responses (question)''')  # Index for faster lookups
    conn.commit()
    conn.close()

# Save the user-defined answer to the database
def save_response_to_db(question, answer):
    conn = sqlite3.connect("assistant_responses.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO responses (question, answer) VALUES (?, ?)", (question, answer))
    conn.commit()
    conn.close()

# Retrieve a response from the database for a given question
def get_response_from_db(question):
    conn = sqlite3.connect("assistant_responses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT answer FROM responses WHERE question = ?", (question,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

# Listen to the user's speech and convert it to text using Vosk with timeout
def listen_to_speech_vosk(timeout=5):
    model = Model(r"C:\Users\HP\Desktop\Asssitant\vosk-model-en-us-0.22\vosk-model-en-us-0.22")
    rec = KaldiRecognizer(model, 16000)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=2048)
    stream.start_stream()

    print("Listening...")
    start_time = time.time()

    while True:
        data = stream.read(2048, exception_on_overflow=False)
        if rec.AcceptWaveform(data):
            result = rec.Result()
            result_json = json.loads(result)
            if "text" in result_json:
                return result_json["text"]

        # Check if timeout has been reached
        if time.time() - start_time > timeout:
            print("Listening timed out.")
            break

    stream.stop_stream()
    stream.close()
    return None

# Make the assistant speak a given response
def speak(response):
    engine.say(response)
    engine.runAndWait()

# Main assistant function
def assistant():
    setup_database()
    while True:
        question = listen_to_speech_vosk()

        if question:
            print(f"You asked: {question}")
            saved_response = get_response_from_db(question)

            if saved_response:
                print(f"Assistant: {saved_response}")
                speak(saved_response)
            else:
                print("I don't know the answer to that. What should I say?")
                speak("I don't know the answer to that. What should I say?")
                user_defined_response = listen_to_speech_vosk(timeout=7)  # Reduced timeout for waiting

                if user_defined_response:
                    save_response_to_db(question, user_defined_response)
                    print(f"Saved: {user_defined_response}")
                    speak(f"Okay, I will remember that.")
                else:
                    print("No input received, moving on.")
                    speak("No input received, moving on.")

# Run the assistant
if __name__ == "__main__":
    assistant()
