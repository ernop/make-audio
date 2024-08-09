import requests
import sys
import os
import subprocess
import clean
import time
import argparse
from typing import List

api_key = open('apikey.txt', 'r').read().strip()
endpoint = 'https://api.openai.com/v1/audio/speech'

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

voices = 'alloy,echo,fable,onyx,nova,shimmer'.split(',')
# alloy - boring, male-female ish? unclear. Really very very deep.
# echo - male, high, young, clear, annoying.
# fable - british, male, highish? very twangy and annoying. Tried it, hated it.
# nova - female, american
# onyx - the standard chatgpt voice, laconic, artificial waiting times
# shimmer - deep female, oh this is scarlett

def parse_filename(input_filename: str) -> str:
    filename = os.path.basename(input_filename)
    return os.path.splitext(filename)[0]

def split_text(text: str, limit: int) -> List[str]:
    sections = text.split("\n")
    result = []
    current_chunk = ""

    for section in sections:
        section = section.replace('\r', ' ').strip()
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

def generate_audio(part: str, voice: str, format: str, title: str, ii: int) -> str:
    data = {
        'model': 'tts-1',
        'input': part,
        'voice': voice,
        'format': format
    }

    fn = f'working/{title}-voice_{voice}-{ii}.{format}'

    if os.path.exists(fn):
        print("skipping existing file.", fn)
        return fn

    print(fn)

    response = requests.post(endpoint, headers=headers, json=data)

    if response.status_code == 200:
        with open(fn, 'wb') as audio_file:
            audio_file.write(response.content)
        print(f'Audio saved as {fn}')
        return fn
    else:
        print('Error:', response.status_code, response.text)
        import ipdb
        ipdb.set_trace()
        return ""

def concatenate_audio_files(generated_files: List[str], title: str, voice: str):
    with open('working/file_list.txt', 'w') as file_list:
        for file in generated_files:
            file_list.write(f"file '{os.path.abspath(file)}'\n")

    output_file = f'output/{title}-{voice}.mp3'
    ffmpeg_command = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'working/file_list.txt', '-c', 'copy', output_file]

    subprocess.run(ffmpeg_command)
    print(f'Concatenated audio saved as {output_file}')

def main(input_filename: str):
    title = parse_filename(input_filename)
    raw_input_file = f'input/{title}.txt'
    
    if not os.path.exists(raw_input_file):
        print(f"Error: File {raw_input_file} not found.")
        sys.exit(1)

    clean.do(raw_input_file)
    clean_input_file = raw_input_file.replace('.txt', '.clean.txt')

    input_text = open(clean_input_file, 'r').read()
    format = 'mp3'
    voices = ['fable']  # You can modify this list as needed

    LIMIT = 4000
    parts = split_text(input_text, LIMIT)

    print(f"got: {len(parts)} parts!")

    for voice in voices:
        ii = 1
        voice = voice.strip()
        generated_files = []
        total_time = 0
        times = []

        for part in parts:
            start_time = time.time()

            fn = generate_audio(part, voice, format, title, ii)
            if fn:
                generated_files.append(fn)

            end_time = time.time()
            chunk_time = end_time - start_time
            total_time += chunk_time
            times.append(chunk_time)

            # Calculate average time of last 5 chunks (or all if less than 5)
            avg_time = sum(times[-5:]) / len(times[-5:])
            projected_total = avg_time * len(parts)

            print(f"Chunk {ii}/{len(parts)}: {chunk_time:.1f} seconds")
            print(f"Total time so far: {total_time:.1f} seconds")
            print(f"Projected total time: {projected_total:.1f} seconds")
            print(f"Estimated time remaining: {projected_total - total_time:.1f} seconds")
            print("--------------------")

            ii += 1

        concatenate_audio_files(generated_files, title, voice)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate audio from text file using OpenAI TTS API")
    parser.add_argument("filename", help="Input text filename (with or without path and .txt extension)")
    args = parser.parse_args()

    main(args.filename)