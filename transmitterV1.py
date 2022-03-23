
# transmitterV1.py from transLoop2.py
# take picture and send via lora, and loop
# 2022-01-20
#
# 2022-01-20:
# Added command line process and clean up code 
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
archiveDir = os.path.isdir("./archive")

# process commmand line
argv = sys.argv
try:
    opts, args = getopt.getopt(argv[1:],"t:n")
except getopt.GetoptError:
    print ("correct invocation: " + argv[0] + " <-t 'seconds'> <-n>")
    print("Ending...")
    sys.exit(2)
for opt, arg in opts:
    if opt == '-t':
        timeDelay  = int(arg)
    elif opt == '-n':
        archiveDir = False 

def handler(signum, frame):
  global term
  term = True
  print("Termination Started...")

if archiveDir:
  print("Archive On")
else:
  print("Archive Off")
print("timeDelay: " + str(timeDelay))
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
    # print("Loop...",flush=True)
    # step 1: snap picture
    # print("raspistill")
    # added -n to stop preview
    # added -t <n> to speen up, def value is 5 (secs)
    # os.system('raspistill -t 2 -n -o temp.jpg')
    system('raspistill -t 2 -n -o temp.jpg')
    # print('done!') 

    #step 2: resize picture and make sqaure, output: tempsq.jpg 
    # print("resize and squared") 
 
    # img = cv2.imread('temp.jpg', cv2.IMREAD_UNCHANGED)
    img = imread('temp.jpg', IMREAD_UNCHANGED)
 
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
 
    # print('Resized Dimensions : ',resized.shape)

    # cv2.imwrite('tempsq.jpg', resized)
    imwrite('tempsq.jpg', resized)
    # print('done!') 

    #step 3: copy color file to archive (optional)
    seconds = int(time.time())
    if archiveDir:
      fname = "./archive/C" + str(seconds) + ".jpg"
      imwrite(fname, resized)
      # print('done archive!')

    #step 4: make monochrome, output: tempmn.bmp
    # print("convert")
    system('convert tempsq.jpg -monochrome tempmn.bmp')
    # print('done!')

       

    #step 5: input tempmn.bmp, and tag,  write via lora and optionally archive
    # print("read file and lora")
    file = open("tempmn.bmp","rb")
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
    # print('tag:' + str(seconds))
    # print('done!') 
    # print('iteration finished! -- waiting now',flush=True)
    print("#",end='',flush=True)
    # time.sleep(20)  # wait 20 seconds
    # a photo cycle with small B&W takes about 3 seconds
    time.sleep(timeDelay) 

print("Ending...")
