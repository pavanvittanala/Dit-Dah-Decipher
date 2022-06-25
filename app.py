from flask import Flask, render_template, Response, request, jsonify
from gtts import gTTS
import os
import morse_translator
from morse_detect import MorseClass

app = Flask(__name__)
global morseclass
global morse_Text



def readymade_results(total_morse):
    print("Morse Code: ", total_morse.replace("¦", " "))
    morse_text = morse_translator.from_morse(total_morse)
    print("Translated: ", morse_text)
    return morse_text


@app.route('/speakMorse', methods=['POST'])
def speak_results():
    global morse_Text
    d = request.get_json()
    print(d)
    morse_text = morse_Text
    morse_text = "The decoded morse code is "+morse_text
    speaker = gTTS(text=morse_text, lang="en", slow=False)
    speaker.save("morse_speech.mp3")
    os.system("mpg321 morse_speech.mp3")
    return jsonify({"1":1})


@app.route('/')
def index_():
    return render_template('home.html')


@app.route('/morse')
def camera():
    return render_template('morsecam.html')


@app.route('/morsedecode')
def morsedecode():
    global morseclass, morse_Text
    morse_code_final = morseclass.total_morse
    morse_text = morse_translator.from_morse(morse_code_final)
    morse_Text, morseclass = morse_text, 1
    return render_template('show.html', sentences=morse_text)


def gen(cam):
    while True:
        frame = cam.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    global morseclass
    morseclass = MorseClass()
    return Response(gen(morseclass), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(debug=True)
