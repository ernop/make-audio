﻿import requests
import sys
from pydub import AudioSegment
import os
import subprocess

api_key=open('apikey.txt','r').read().strip()
endpoint = 'https://api.openai.com/v1/audio/speech'

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}


voices = 'alloy,echo,fable,onyx,nova,shimmer'.split(',')
#alloy - boring, male-female ish? unclear. Really very very deep.
#echo - male, high, young, clear, annoying.
#fable - british, male, highish? very twangy and annoying. Tried it, hated it.
#nova - female, american
#onyx - the standard chatgpt voice, laconic, artificial waiting times
#shimmer - deep female, oh this is scarlett

title='<filename>' #file of this name.txt must be in output.
input_text = open(f'working/{title}.txt', 'r').read()
format='mp3'
voice='onyx'

#input limit, at some point this will extend.
#TODO do this more, and switch to elevenlabs.
LIMIT=4000

def split_text(text, limit):
    sections = text.split("\n\n")
    result = []
    current_chunk = ""

    for section in sections:
        if len(current_chunk) + len(section) + 2 <= limit:
            if current_chunk:
                current_chunk += "\r\n\r\n" + section
            else:
                current_chunk = section
        else:
            if current_chunk:
                result.append(current_chunk)
            current_chunk = section

    if current_chunk:
        result.append(current_chunk)

    return result

parts=split_text(input_text, LIMIT)

generated_files=[]
print(f"got: {len(parts)} parts!")

ii=1
for part in parts:
    voice = voice.strip()

    data = {
        'model': 'tts-1',
        'input': part,
        'voice': voice,
        'format': 'mp3'
    }

    fn = f'working/{title}-voice_{voice[:3]}-{ii}.{format}'

    if os.path.exists(fn):
        print("skipping existing file.",fn)
        generated_files.append(fn)
        ii=ii+1
        continue

    print(fn)

    response = requests.post(endpoint, headers=headers, json=data)

    if response.status_code == 200:
        with open(fn, 'wb') as audio_file:
            audio_file.write(response.content)
        print(f'Audio saved as {fn}')
        generated_files.append(fn)
    else:
        print('Error:', response.status_code, response.text)
        import ipdb;ipdb.set_trace()
    ii=ii+1

# Create a file list for ffmpeg
with open('working/file_list.txt', 'w') as file_list:
    for file in generated_files:
        file_list.write(f"file '{os.path.abspath(file)}'\n")

# Concatenate MP3 files without re-encoding
output_file = f'output/{title}-{voice}.mp3'
ffmpeg_command = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'working/file_list.txt', '-c', 'copy', output_file]

subprocess.run(ffmpeg_command)
print(f'Concatenated audio saved as {output_file}')