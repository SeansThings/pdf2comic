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

def main(argv):
    # Check the command line arguments
    inputStr = 'pdf2comic.py -f <Comic format> -i <Input directory> -o <Output directory>'
    try:
        opts, args = getopt.getopt(argv,'hf:i:o:',['comicFormat=','inDir=','outDir='])
    except getopt.GetoptError:
        print(inputStr)
        sys.exit(2)
    
    inDir = ''
    outDir = ''
    comicFormat = ''

    # Process command line arguments
    if len(opts) >= 1:
        for opt, arg in opts:
            if opt == '-h':
                print(inputStr)
                sys.exit()
            elif opt in ('-f', '--comicFormat'):
                comicFormat = arg
            elif opt in ('-i', '--inDir'):
                inDir = Path(arg)
            elif opt in ('-o', '--outDir'):
                outDir = Path(arg)
    else:
        print('No arguments provided')
        print(inputStr)
        sys.exit()

    # Determine comic format or default to cbz
    if comicFormat.lower() in ('cbr', 'r'):
        comicFormat = 'cbr'
    elif comicFormat.lower() in ('cbz', 'z', ''):
        comicFormat = 'cbz'
    else:
        print('Invalid comic format selected!')
        print('Valid formats: cbr, z, cbr, r')

    # Python 3.10 required
    # match comicFormat.lower():
    #     case 'cbz', 'z':
    #       comicFormat = 'cbz'
    #     case 'cbr':
    #       comicFormat = 'cbr'
    #     case _:
    #        print('Invalid comic format selected!')
    #        print('Valid formats: cbr, z, cbr, r')

    # Check that the input directory exists and contains PDF files
    # if os.path.isdir(inDir) == False:
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

    # Create output dir if missing
    if os.path.isdir(outDir) == False:
        os.mkdir(outDir)

    # Iterate through each PDF file found
    for pdf in os.listdir(inDir):
        baseFN=os.path.splitext(pdf)[0]
        pageFN=baseFN.replace(' ', '_')

        # Convert and store pages
        # pages = pdf2image.convert_from_path(inDir + '/' + pdf)
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
        # with open(outDir + '/' + baseFN + '.cbr', 'wb') as outFN:
        comicZipName = str(outDir / baseFN) + '.cbr'
        with open(comicZipName, 'wb') as outFN:
            outFN.write(zipIO.getvalue())
            outFN.close()

if __name__ == '__main__':
   main(sys.argv[1:])
