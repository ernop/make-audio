import sys
import os
import chardet

#[a-zA-Z] [a-zA-Z] [a-zA-Z] [a-zA-Z] this pattern also is suspicious in many books, used for emphasis but totally doesn't seem to work when dealing with conversion to audio.

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    return chardet.detect(raw_data)['encoding']

def load_replacements(file_path):
    replacements = {}
    encoding = detect_encoding(file_path)
    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
        for line in f:
            try:
                if not line.strip():
                    replacements[line[0]]=' '
                    continue
                lsp  = line.strip().split(maxsplit=1)
                if len(lsp)==2:
                    original, replacement = lsp
                    replacements[original] = replacement
                else:
                    original = lsp[0]
                    replacements[original] = " "
            except ValueError:
                print(f"Warning: Skipping invalid line in replacements file: {line.strip()}")
    return replacements

def clean_text(text, replacements):
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    return text

def find_non_ascii(text):
    return set(char for char in text if ord(char) > 127)

def main(input_file, output_file, replacements_file):
    replacements = load_replacements(replacements_file)

    input_encoding = detect_encoding(input_file)
    with open(input_file, 'r', encoding=input_encoding, errors='replace') as f:
        text = f.read()

    cleaned_text = clean_text(text, replacements)

    non_ascii = find_non_ascii(cleaned_text)

    if non_ascii:
        print("The following non-ASCII characters are still present:")
        for char in non_ascii:
            print(f"'{char}' (Unicode: U+{ord(char):04X})")
        print("Please update the replacements file and run the program again.")
    else:
        # Write output file
        with open(output_file, 'w', encoding='ascii') as f:
            f.write(cleaned_text)
        print(f"Cleaned text has been written to {output_file}")

def do(path):
    input_file = path
    output_file = path.replace('.txt', '.clean.txt')
    replacements_file = 'replacements.txt'
    main(input_file, output_file, replacements_file)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python clean.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    replacements_file = 'replacements.txt'

    if not all(os.path.exists(file) for file in [input_file, replacements_file]):
        print("Input file or replacements file not found.")
        sys.exit(1)

    main(input_file, output_file, replacements_file)
