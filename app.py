from flask import Flask, render_template, request, send_from_directory, jsonify
import yt_dlp
from pydub import AudioSegment
from midiutil import MIDIFile
from music21 import converter
import os
import subprocess

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/convert", methods=['POST'])
def convert():
    video_url = request.form['url']
    instrument = request.form['instrument']
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': 'static/downloaded_audio.%(ext)s',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        return jsonify({"error": f"Erro ao baixar o áudio: {str(e)}"}), 500

    audio_file = 'static/downloaded_audio.wav'
    
    if not os.path.exists(audio_file):
        return jsonify({"error": "Arquivo de áudio não encontrado."}), 500

    try:
        audio = AudioSegment.from_wav(audio_file)

        midi = MIDIFile(1)
        track = 0
        time = 0
        midi.addTrackName(track, time, "Track")
        midi.addTempo(track, time, 120)
        
        instrument_program = 0
        if instrument == "piano":
            instrument_program = 0

        midi.addProgramChange(track, 0, time, instrument_program)
        midi.addNote(track, 0, 60, time, 1, 100)

        if not os.path.exists("static/midi_files"):
            os.makedirs("static/midi_files")
        midi_file = "static/midi_files/converted_audio.mid"
        with open(midi_file, "wb") as output_file:
            midi.writeFile(output_file)
    except Exception as e:
        return jsonify({"error": f"Erro ao processar o áudio: {str(e)}"}), 500

    try:
        midi_score = converter.parse(midi_file)
        if not os.path.exists("static/musicxml"):
            os.makedirs("static/musicxml")
        musicxml_file = "static/musicxml/converted_audio.xml"
        midi_score.write('musicxml', fp=musicxml_file)

        # Convert MusicXML to PDF using MuseScore
        if not os.path.exists("static/pdf"):
            os.makedirs("static/pdf")
        pdf_file = "static/pdf/converted_audio.pdf"
        musescore_path = "C:/Program Files/MuseScore 4/bin/MuseScore4.exe"
        if not os.path.exists(musescore_path):
            return jsonify({"error": f"MuseScore não encontrado no caminho: {musescore_path}"}), 500

        subprocess.run([musescore_path, musicxml_file, '-o', pdf_file], check=True)

    except Exception as e:
        return jsonify({"error": f"Erro ao converter MIDI para notação musical: {str(e)}"}), 500

    return render_template('preview.html', midi_url=midi_file, musicxml_url=musicxml_file, pdf_url=pdf_file)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('static', filename)

if __name__ == "__main__":
    app.run(debug=True)
