import sys
import zipfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import argparse
import os

def extract_text_from_epub(epub_path):
    with zipfile.ZipFile(epub_path, 'r') as epub:
        # import ipdb;ipdb.set_trace()
        # Find the content.opf file
        try:
            container = epub.read('META-INF/container.xml')
            container_root = ET.fromstring(container)
            rootfile_path = container_root.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile').get('full-path')
        except Exception as e:
            print(f"Error reading container.xml: {e}")
            return ""

        # Parse the content.opf file
        content_opf = epub.read(rootfile_path)
        opf_root = ET.fromstring(content_opf)
        
        # Get the spine order
        spine = opf_root.find('{http://www.idpf.org/2007/opf}spine')
        itemrefs = spine.findall('{http://www.idpf.org/2007/opf}itemref')
        
        # Create a mapping of id to href
        manifest = opf_root.find('{http://www.idpf.org/2007/opf}manifest')
        id_to_href = {item.get('id'): item.get('href') for item in manifest.findall('{http://www.idpf.org/2007/opf}item')}
        
        # Extract text in the correct order
        text = []
        for itemref in itemrefs:
            idref = itemref.get('idref')
            href = id_to_href.get(idref)
            if href and (href.endswith('.html') or href.endswith('.xhtml')):
                file_path = os.path.join(os.path.dirname(rootfile_path), href)
                try:
                    with epub.open(file_path) as html_file:
                        soup = BeautifulSoup(html_file.read(), 'html.parser')
                        text.append(soup.get_text())
                except KeyError:
                    print(f"Warning: File not found in EPUB: {file_path}")
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
        
    return '\n\n'.join(text)

def main():
    parser = argparse.ArgumentParser(description='Extract text from EPUB files.')
    parser.add_argument('epub_file', help='Path to the EPUB file')
    parser.add_argument('-o', '--output', help='Output file path (default: print to stdout)')
    args = parser.parse_args()

    text = extract_text_from_epub(args.epub_file)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(text)
    else:
        print(text)

if __name__ == '__main__':
    main()