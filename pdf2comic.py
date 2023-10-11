#!/usr/bin/python3

import os
from posixpath import splitext
import sys
import getopt
import io
import zipfile
import pdf2image
import PIL
import rarfile 
# import pathlib
from pathlib import Path
from zipfile import ZipFile
from alive_progress import alive_bar
import time
import subprocess
# import rarfile

def trimBorder(im):
    # Trim the borders on pages based on top left pixel colour
    bg = PIL.Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = PIL.ImageChops.difference(im, bg)
    diff = PIL.ImageChops.add(diff, diff, 1, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)

def convertPDF(comicFormat, inputFoD, outDir, pdfFile, trim):
    # Replaces spaces with underscores in filenames
    baseFN=os.path.splitext(pdfFile)[0]
    pageFN=baseFN.replace(' ', '_')

    # Convert and store pages
    pdfLocation = inputFoD / pdfFile
    pages = pdf2image.convert_from_path(pdfLocation)

    # Create zip file in ram
    zipIO = io.BytesIO()
    with ZipFile(zipIO, 'w') as comicZip:

        # Create progress bar
        with alive_bar(len(pages)) as bar:#, title=baseFN, title_length='40', length='40', bar='blocks', spinner='dots_reverse') as bar:

            # Process each page
            for i in range(len(pages)):

                # Check if pages are to be trimmed
                if trim == True:
                    pages[i] = trimBorder(pages[i])

                # Replace PIL images with BytesIO image
                pageIO = io.BytesIO()
                pages[i].save(pageIO, 'WEBP')
                pages[i].close()
                pages[i] = pageIO

                # Add pages to archive file
                if comicFormat == 'cbz':
                    pageName=pageFN + '_-_' + str(i).zfill(3) + '.webp'
                    comicZip.writestr(pageName, pages[i].getvalue())
                elif comicFormat == 'cbr':
                    print('CBR\'s not yet supported!')
                    # os.system('rar')
                    # subprocess.call(['echo', 'Hello World!'])

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

def convertComic(inputFoD, outDir, comicArchive):

    # Replaces spaces with underscores in filenames
    baseFN=os.path.splitext(comicArchive)[0]
    baseFE=os.path.splitext(comicArchive)[1]
    pageFN=baseFN.replace(' ', '_')

    # Determine comic format and extract accordingly
    if baseFE == '.cbz':
        archiveFile = zipfile.ZipFile(inputFoD / comicArchive, 'r')
    elif baseFE == '.cbr':
        archiveFile = rarfile.RarFile(inputFoD / comicArchive, 'r')
    else:
        print('Unable to determine comic format')
        sys.exit()
 
    # Create zip file in ram
    zipIO = io.BytesIO()
    with ZipFile(zipIO, 'w') as comicZip:


        # Create progress bar
        with alive_bar(len(archiveFile.namelist()), title=baseFN, title_length=40, length=40, bar='blocks') as bar:
            i = 1

            orderedNameList = archiveFile.namelist()
            orderedNameList.sort()

            for page in orderedNameList:
                # Convert each page to WEPB format
                if os.path.splitext(page)[1].lower() in ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.wepb'):
                    pageIO = io.BytesIO()
                    pageBy = PIL.Image.open(io.BytesIO(archiveFile.read(page)))
                    pageBy.save(pageIO, 'WEBP')
                    pageBy.close()
                    pageBy = pageIO
                    pageName = pageFN + '_-_' + str(i).zfill(3) + '.webp'
                    comicZip.writestr(pageName, pageBy.getvalue())
                # Copy metadata to new archive
                elif page == 'ComicInfo.xml':
                    pageIO = io.BytesIO()
                    pageBy = io.BytesIO(archiveFile.read(page))
                    pageName = 'ComicInfo.xml'
                    comicZip.writestr(pageName, pageBy.getvalue())

                i = i + 1

                # Update progress bar
                time.sleep(0.001)
                bar()

    # Close archive files
    archiveFile.close()
    comicZip.close()

    # Write archive to disk
    comicZipName = str(outDir / baseFN) + '.' + 'cbz'
    with open(comicZipName, 'wb') as outFN:
        outFN.write(zipIO.getvalue())
        outFN.close()

def main(argv):
    # Check the command line arguments
    helpStr = '''
    pdf2comic.py
    ============

    Arguments              Options           Requisite   Notes
    -h    --help                             Optional    Displays this help message.
    -t    --trim                             Optional    Trim borders on every page. Defaults to False.
    -c    --comicFormat    cbz, z            Optional    Wanted comic format. Defaults to cbz.
    -i    --inputFoD                         Required    Input directory containing pdf/cbz/cbr files.
                                                         A single pdf/cbz/cbr input file.
    -o    --outDir                           Optional    Output directory for comics.


    Examples:

    Converting PDF's to comic formats:
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
        opts, args = getopt.getopt(argv,'htci:o',['help','trim=','comicFormat=','inputFoD=','outDir='])
    except getopt.GetoptError:
        print(helpStr)
        sys.exit(2)

    trim = False
    inputFoD = ''
    outDir = ''
    comicFormat = ''

    # Process command line arguments
    if len(opts) >= 1:
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                print(helpStr)
                sys.exit()
            elif opt in ('-t', '--trim'):
                trim = True
            elif opt in ('-c', '--comicFormat'):
                comicFormat = arg
            elif opt in ('-i', '--inputFoD'):
                inputFoD = Path(arg)
            elif opt in ('-o', '--outDir'):
                outDir = Path(arg)
    else:
        print('No arguments provided')
        print(helpStr)
        sys.exit()

#    print("1: " + str(inputFoD))

    # Check input file or directory exists
    if os.path.exists(inputFoD) == False:
        print("Error: " + str(inputFoD) + " does not exist!")
        sys.exit()
    elif len(os.listdir(inputFoD)) == 0:
        print("Error: " + str(inputFoD) + " is empty!")
        sys.exit()

    # Determine file extension
    if os.path.isfile(inputFoD) == True:
        inputFE = Path(inputFoD).suffix.lower()
    elif os.path.isdir(inputFoD) == True:
        for f in os.listdir(inputFoD):
            inputFE = Path(f).suffix.lower()
            break
    else:
        print('Unable to determine file extension')
        sys.exit()

    # Determine app mode
    if inputFE == ".pdf":
        appMode = 'pdf'
    elif inputFE in ('.cbz', '.cbr'):
        appMode = 'comic'
    else:
        print('Unable to determine app mode')
        sys.exit()

    # Determine if single or batch job
    if os.path.isfile(inputFoD):
        jobMode = 'single'
    elif os.path.isdir(inputFoD):
        jobMode = 'batch'
    else:
        print("Error: Dunno")
        sys.exit()

    # Determine comic format or default to cbz
    if comicFormat.lower() in ('cbr', 'r'):
        comicFormat = 'cbr'
    elif comicFormat.lower() in ('cbz', 'z', ''):
        comicFormat = 'cbz'
    else:
        print('Invalid comic format selected!')
        print('Valid formats: cbz, z')

    # Ensure directories exist and variables are valid 
    if jobMode == 'single':
        inputFile = inputFoD.name
        inputFoD = inputFoD.parent
        if outDir == '':
            outDir = inputFoD
        if os.path.isdir(outDir) == False:
            os.mkdir(outDir)
    elif jobMode == 'batch':
        if outDir == '':
            outDir = Path(str(inputFoD.parent / inputFoD.name) + '_converted')
        if os.path.isdir(outDir) == False:
            os.mkdir(outDir)
    else:
        print('Error! Unknown job mode.')

    # Determine app mode
    if appMode == 'pdf':

        # Start converting
        if jobMode == 'single':
            convertPDF(comicFormat, inputFoD, outDir, inputFile, trim)
        elif jobMode == 'batch' :
            for pdfFile in os.listdir(inputFoD):
                convertPDF(comicFormat, inputFoD, outDir, pdfFile, trim)

    elif appMode == 'comic':

        # Start converting
        if jobMode == 'single':
            convertComic(inputFoD, outDir, inputFile)
        elif jobMode == 'batch' :
            for comicArchive in os.listdir(inputFoD):
                convertComic(inputFoD, outDir, comicArchive)
    else:
        print('Invalid app mode!')
        print(helpStr)
        sys.exit()

if __name__ == '__main__':
   main(sys.argv[1:])
