import openai
import pyaudio
import wave
import speech_recognition as sr
import tkinter as tk
from tkinter import messagebox
import threading
import random
import ttkbootstrap as ttk
import os

# Empty string due to private API Key
openai.api_key = os.getenv('OPENAI_API_KEY')

class InterviewAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Interview Assistant")
        self.style = ttk.Style("darkly")

        self.is_recording = False
        self.frames = []
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024
        self.audio = pyaudio.PyAudio()

        self.current_question_index = 0
        self.questions = []
        self.transcribed_text = ""
        self.load_questions("questions.txt")

        self.create_main_widgets()

    def create_main_widgets(self):
        self.question_frame = ttk.Frame(self.root)
        self.question_frame.pack(pady=20)

        self.question_label = ttk.Label(self.question_frame, text="", wraplength=400, justify="center", font=("Helvetica", 14))
        self.question_label.pack(pady=10)

        self.button_frame = ttk.Frame(self.root)
        self.button_frame.pack(pady=10)

        self.record_button = ttk.Button(self.button_frame, text="Record", command=self.toggle_recording, bootstyle="primary-outline")
        self.record_button.pack(side=tk.LEFT, padx=10)

        self.prev_button = ttk.Button(self.button_frame, text="Prev", command=self.prev_question, bootstyle="info-outline")
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.next_button = ttk.Button(self.button_frame, text="Next", command=self.next_question, bootstyle="info-outline")
        self.next_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = ttk.Button(self.button_frame, text="Stop", command=self.stop_recording, state=tk.DISABLED, bootstyle="danger-outline")
        self.stop_button.pack(side=tk.LEFT, padx=10)

        self.text_output = ttk.Text(self.root, height=10, width=50, font=("Helvetica", 12))
        self.text_output.pack(pady=20)

        self.recognizer = sr.Recognizer()
        self.display_question()

    def load_questions(self, filename):
        with open(filename, 'r') as file:
            self.questions = file.read().split('\n\n')
        random.shuffle(self.questions)

    def display_question(self):
        if self.current_question_index < len(self.questions):
            self.question_label.config(text=self.questions[self.current_question_index])
        else:
            self.question_label.config(text="No more questions.")
            self.record_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            self.prev_button.config(state=tk.DISABLED)

    def toggle_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.record_button.config(text="Record")
            self.stop_button.config(state=tk.DISABLED)
        else:
            self.is_recording = True
            self.frames = []
            self.record_button.config(text="Stop")
            self.stop_button.config(state=tk.NORMAL)
            threading.Thread(target=self.record_audio).start()

    def record_audio(self):
        stream = self.audio.open(format=self.audio_format, channels=self.channels,
                                 rate=self.rate, input=True,
                                 frames_per_buffer=self.chunk)
        while self.is_recording:
            data = stream.read(self.chunk)
            self.frames.append(data)
        stream.stop_stream()
        stream.close()
        self.convert_to_text()

    def stop_recording(self):
        self.is_recording = False
        self.record_button.config(text="Record")
        self.stop_button.config(state=tk.DISABLED)

    def convert_to_text(self):
        wf = wave.open("response.wav", 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        with sr.AudioFile("response.wav") as source:
            audio_data = self.recognizer.record(source)
            try:
                text = self.recognizer.recognize_google(audio_data)
                self.transcribed_text = text
                self.text_output.insert(tk.END, text + "\n")
                print("Transcribed Text: " + text)
                self.process_answer(text)
            except sr.UnknownValueError:
                self.text_output.insert(tk.END, "Could not understand audio\n")
            except sr.RequestError as e:
                self.text_output.insert(tk.END, f"Could not request results; {e}\n")

    def process_answer(self, answer):
        prompt = f"Separate the answer/text from the audio and split it up into the STAR method don’t add any additional text that wasn’t in the audio, after that tell me what I can improve upon in each category and then give me a new and improved STAR response using mine as a basis, only add what is necessary don't add more than you need to(situation, task, action, result) and then rate my answer 1-10: {answer}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ]
        )
        processed_answer = response.choices[0].message['content'].strip()
        print("Processed Answer: " + processed_answer)  # Debug print
        self.show_result_gui(processed_answer)

    def show_result_gui(self, processed_answer):
        self.result_window = tk.Toplevel(self.root)
        self.result_window.title("Result")

        self.result_frame = ttk.Frame(self.result_window)
        self.result_frame.pack(pady=20)

        # Display the processed answer in a text widget
        self.processed_text = ttk.Text(self.result_frame, height=25, width=100, font=("Helvetica", 12))
        self.processed_text.pack(pady=10)
        self.processed_text.insert(tk.END, processed_answer)

        # Close button
        self.close_button = ttk.Button(self.result_frame, text="Close", command=self.result_window.destroy, bootstyle="danger-outline")
        self.close_button.pack(pady=10)

    def next_question(self):
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            self.display_question()

    def prev_question(self):
        if self.current_question_index > 0:
            self.current_question_index -= 1
            self.display_question()

if __name__ == "__main__":
    root = ttk.Window(themename="darkly")
    app = InterviewAssistantApp(root)
    root.mainloop()
