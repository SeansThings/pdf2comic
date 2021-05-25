#!/usr/bin/python

import os
import sys
import getopt
import io
import pdf2image
import PIL
# import pathlib
from pathlib import Path
from zipfile import ZipFile
from alive_progress import alive_bar
import time
import subprocess

def trimBorder(im):
    # Trim the borders on pages based on top left pixel colour
    bg = PIL.Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = PIL.ImageChops.difference(im, bg)
    diff = PIL.ImageChops.add(diff, diff, 1, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)

def convertComic(comicFormat, inDir, outDir, pdf):
    # Replaces spaces with underscores in filenames        
    baseFN=os.path.splitext(pdf)[0]
    pageFN=baseFN.replace(' ', '_')

    # Convert and store pages
    pdfLocation = inDir / pdf
    pages = pdf2image.convert_from_path(pdfLocation)

    # Create zip file in ram
    zipIO = io.BytesIO()
    with ZipFile(zipIO, 'w') as comicZip:
        
        # Create progress bar
        with alive_bar(len(pages), title=baseFN, title_length='40', length='40', bar='blocks', spinner='dots_reverse') as bar:

            # Process each page
            for i in range(len(pages)):
                # Trim pages
                pages[i] = trimBorder(pages[i])

                # Replace PIL images with BytesIO image
                pageIO = io.BytesIO()
                pages[i].save(pageIO, 'WEBP')
                pages[i].close()
                pages[i] = pageIO
                
                # Add pages to archive file
                if comicFormat == 'cbr':
                    print('CBR\'s not yet supported!')
                    # os.system('rar')
                    # subprocess.call(['echo', 'Hello World!'])
                elif comicFormat == 'cbz':
                    # comicZip.writestr(pageFN + '_-_' + str(i).zfill(3) + '.webp', pages[i].getvalue())
                    pageName=pageFN + '_-_' + str(i).zfill(3) + '.webp'
                    comicZip.writestr(pageName, pages[i].getvalue())

                # Update progress bar
                time.sleep(0.001)
                bar()

    # Close archive file
    comicZip.close()            

    # Write archive to disk
    comicZipName = str(outDir / baseFN) + '.' + comicFormat
    with open(comicZipName, 'wb') as outFN:
        outFN.write(zipIO.getvalue())
        outFN.close()

def main(argv):
    # Check the command line arguments
    inputStr = '''
    pdf2comic.py
    ============

    Arguments              Options           Requisite   Notes    
    -h    --help                             Optional    Displays this help message
    -c    --comicFormat    cbr, r, cbz, z    Optional    Wanted comic format. Defaults to cbz
    -i    --inDir                            Required    Input directory containing pdf's or single PDF file
    -o    --outDir                           Optional    Output directory for comics


    Examples:

    Single: pdf2comic.py -c <Comic format> -i <Input file> -o <Output directory>
            
            pdf2comic.py -c cbz -i /home/user/comic.pdf
            pdf2comic.py -c cbr -i /home/user/comic.pdf -o /home/user/
            pdf2comic.py -c cbr -i C:\\comics\\comic.pdf
            pdf2comic.py -c cbz -i C:\\comics\\comic.pdf -o C:\\comics

    Batch:  pdf2comic.py -c <Comic format> -i <Input directory> -o <Output directory>

            pdf2comic.py -c cbz -i /home/user/comics
            pdf2comic.py -c cbr -i /home/user/comics -o /home/user/comics_converted
            pdf2comic.py -c cbr -i C:\\comics
            pdf2comic.py -c cbz -i C:\\comics -o C:\\comics_converted
    '''
    try:
        opts, args = getopt.getopt(argv,'hf:i:o:',['help','comicFormat=','inDir=','outDir='])
    except getopt.GetoptError:
        print(inputStr)
        sys.exit(2)
    
    inDir = ''
    outDir = ''
    comicFormat = ''

    # Process command line arguments
    if len(opts) >= 1:
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                print(inputStr)
                sys.exit()
            elif opt in ('-c', '--comicFormat'):
                comicFormat = arg
            elif opt in ('-i', '--inDir'):
                inDir = Path(arg)
            elif opt in ('-o', '--outDir'):
                outDir = Path(arg)
    else:
        print('No arguments provided')
        print(inputStr)
        sys.exit()

    # Determine if single or batch job
    if os.path.splitext(inDir)[1].lower() == '.pdf':
        jobMode='single'
    else:
        jobMode='batch'

    # Determine comic format or default to cbz
    if comicFormat.lower() in ('cbr', 'r'):
        comicFormat = 'cbr'
    elif comicFormat.lower() in ('cbz', 'z', ''):
        comicFormat = 'cbz'
    else:
        print('Invalid comic format selected!')
        print('Valid formats: cbr, z, cbr, r')

    # Check that the input directory exists and contains PDF files
    if jobMode == 'single':
        if inDir.exists() == False:            
            print('Input file does not exist!')
            sys.exit()
    elif jobMode == 'batch':
        if inDir.exists() == False:
            print('Input directory does not exist!')
            sys.exit()
        elif sum(1 for _ in inDir.glob('*')) == 0:
            print('Input directory is empty!')
            sys.exit()
        else:
            for file in os.listdir(inDir):
                if file.endswith('.pdf') == False and file.endswith('.PDF') == False:
                    print('No PDF files found in input directory!')
                    sys.exit()

    # Ensure directories exist and variables are valid 
    if jobMode == 'single':
        pdf = inDir.name
        inDir = inDir.parent
        outDir = inDir
    elif jobMode == 'batch':
        if outDir == '':
            outDir = Path(str(inDir.parent / inDir.name) + '_converted')
        print(outDir)
        if os.path.isdir(outDir) == False:
            os.mkdir(outDir)

    # Start converting
    if jobMode == 'single':
        convertComic(comicFormat, inDir, outDir, pdf)
    elif jobMode == 'batch' :
        for pdf in os.listdir(inDir):
            convertComic(comicFormat, inDir, outDir, pdf)

if __name__ == '__main__':
   main(sys.argv[1:])
