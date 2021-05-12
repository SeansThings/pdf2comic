#!/usr/bin/python3.8
import os
import io
import pdf2image
import PIL
from zipfile import ZipFile
from alive_progress import alive_bar
from time import sleep

workingDir=os.environ['HOME'] + '/.pdf2comic'
pdfDir=workingDir+'/pdf'
imgDir=workingDir+'/img'
archDir=workingDir+'/comics'

def trimBorder(im):
    bg = PIL.Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = PIL.ImageChops.difference(im, bg)
    diff = PIL.ImageChops.add(diff, diff, 1, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)

# Check for working directory. If not found prompt for location.
if os.path.isdir(workingDir)  == False:    
    print('Working directory not found. Please enter location of working directory:')
    workingDir = input('(e.g. /home/user/.pdf2comic): ')
    os.mkdir(workingDir)

# Create PDF dir if missing
if os.path.isdir(pdfDir) == False:
    os.mkdir(pdfDir)


# Split PDF into seperate pages
if os.path.isdir(imgDir) == False:
    os.mkdir(imgDir)


for pdf in os.listdir(pdfDir):
    baseFN=os.path.splitext(pdf)[0]
    pageFN=baseFN.replace(' ', '_')
    images = pdf2image.convert_from_path(pdfDir + '/' + pdf)
    zip_file_bytes_io = io.BytesIO()
    with ZipFile(zip_file_bytes_io, 'w') as zip_file:
        with alive_bar(len(images), title='Trimming and archiving', length='20', bar='smooth', spinner='dots_reverse') as bar:
            for i in range(len(images)):
                # Trim pages
                images[i] = trimBorder(images[i])

                # Convert pages to ByteIO
                file_object = io.BytesIO()
                images[i].save(file_object, "WEBP")
                images[i].close()
                images[i] = file_object

                # Add pages to archive
                zip_file.writestr(pageFN + '_-_' + str(i).zfill(3) + '.webp', images[i].getvalue())

                sleep(0.001)
                bar()

        zip_file.close()
        

# Write archive to disk
with open(imgDir + '/' + baseFN + '.cbr', 'wb') as outFN:
    outFN.write(zip_file_bytes_io.getvalue())
    outFN.close()
