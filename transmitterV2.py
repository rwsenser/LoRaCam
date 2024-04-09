
# transmitterV2.py from transmitterV1.py
# take picture and send via lora, and loop
# 2024-04-09
# add ramdisk support
#
print("Loading...",flush=True)

from os import system
from cv2 import imread, imwrite, resize, IMREAD_UNCHANGED, INTER_AREA
import time
import os.path
import signal
import sys
import getopt

# for lora:
# import time
from busio import SPI
from digitalio import DigitalInOut, Direction, Pull
import board
from adafruit_rfm9x import RFM9x

BLOCK_SIZE = 224 # 128 # 32 # 64 # 128
timeDelay = 27 
verbose = False
ramDisk = "/tmp/ramdisk/"
archiveDir = os.path.isdir("./archive")

# process commmand line
argv = sys.argv
try:
    opts, args = getopt.getopt(argv[1:],"t:nv")
except getopt.GetoptError:
    print ("correct invocation: " + argv[0] + " <-t 'seconds'> <-n> <-v>")
    print("Ending...")
    sys.exit(2)
for opt, arg in opts:
    if opt == '-t':
        timeDelay  = int(arg)
    elif opt == '-n':
        archiveDir = False
    elif opt == '-v':
        verbose = True 

def handler(signum, frame):
  global term
  term = True
  print("Termination Started...")

if archiveDir:
  print("Archive On")
else:
  print("Archive Off")
print("timeDelay: " + str(timeDelay))
if verbose:
  print("Verbose On")
else:
  print("Verbose Off")
print("Start...",flush=True)
# Configure LoRa Radio
CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
rfm9x = RFM9x(spi, CS, RESET, 915.0)
rfm9x.tx_power = 23
term = False
signal.signal(signal.SIGINT, handler)

# main loop
while term == False:
    if verbose:
      print("Loop...",flush=True)
      print("raspistill")
    # added -n to stop preview
    # step 1: snap picture
    # added -t <n> to speen up, def value is 5 (secs)
    # os.system('raspistill -t 2 -n -o temp.jpg')
    tempfile1 = ramDisk + 'temp.jpg'
    system('raspistill -t 2 -n -o ' + tempfile1 )
    if verbose:
      print('done!') 

    #step 2: resize picture and make sqaure, output: tempsq.jpg 
    if verbose:
      print("resize and squared") 
 
    # img = cv2.imread('temp.jpg', cv2.IMREAD_UNCHANGED)
    img = imread(tempfile1, IMREAD_UNCHANGED)
 
    # print('Original Dimensions : ',img.shape)
 
    # scale_percent = 25 # was 60 # percent of original size
    # width = int(img.shape[1] * scale_percent / 100)
    # `height = int(img.shape[0] * scale_percent / 100)
    dim = 32
    width = dim 
    height = dim
    dim = (width, height)
  
    # resize image
    # resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
    resized = resize(img, dim, interpolation = INTER_AREA)
    if verbose: 
      print('Resized Dimensions : ',resized.shape)

    # cv2.imwrite('tempsq.jpg', resized)
    tempfile2 = ramDisk + 'tempsq.jpg' 
    imwrite(tempfile2, resized)
    if verbose:
      print('done!') 

    #step 3: copy color file to archive (optional)
    seconds = int(time.time())
    if archiveDir:
      fname = "./archive/C" + str(seconds) + ".jpg"
      imwrite(fname, resized)
      if verbose:
        print('done archive!')

    #step 4: make monochrome, output: tempmn.bmp
    if verbose:
      print("convert")
    tempfile3 = ramDisk + 'tempmn.bmp'
    cmd = 'convert ' + tempfile2 + ' -monochrome ' + tempfile3
    system(cmd)
    if verbose:
      print('done!')

    #step 5: input monochrom3, and tag,  write via lora and optionally archive
    if verbose:
      print("read file and lora")
    file = open(tempfile3,"rb")
    c = 0
    buf =  bytearray()
    byte = file.read(1)
    while byte:
        # do something
        c += 1
        buf += byte
        byte = file.read(1)
    # print("bytes read: " + str(c))
    # tag bin file in bytes 6 ..9 with seconds value
    s3 = (seconds >> 24) & 255
    s2 = (seconds >> 16) & 255
    s1 = (seconds >> 8) & 255
    s0 = (seconds ) & 255
    buf[6] = s3
    buf[7] = s2
    buf[8] = s1
    buf[9] = s0
    # optional archive write
    if archiveDir:
      # use seconds from above
      fname2 = "./archive/B" + str(seconds) + ".bin"
      with open(fname2, "wb") as file:
        file.write(buf)   
    #  lora writes
    offset = 0;
    mv = memoryview(bytearray(buf))
    while c > 0:
        if c > BLOCK_SIZE:
            #output BLOCK_SIZE and adjust c
            # print("lora send: " + str(offset) +"," +str(offset+BLOCK_SIZE))
            local_bytes = mv[offset:(offset+BLOCK_SIZE)]
            rfm9x.send(local_bytes)
            c -= BLOCK_SIZE
            offset += BLOCK_SIZE
        else:
            #output < BLOCK_SIZE
            # print("lora send: " + str(offset) + " end" )
            local_bytes = mv[offset:]
            rfm9x.send(local_bytes)
            c = -1
    if verbose:
      print('tag:' + str(seconds))
      print('done!') 
      print('iteration finished! -- waiting now',flush=True)
      print("#",end='',flush=True)
    # a photo cycle with small B&W takes about 3 seconds
    time.sleep(timeDelay) 

print("Ending...")
