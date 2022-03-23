# serialInV6
# 2022-01-19: Add command line processing
# 2022-01-13: Add archive dir handling
# 2022-01-05: Add ctrl-C handling
# 2021-11-05: rework multi-block handling for bmp files, look at length in header
# 2021-11-04: add better serial handling (multi-block)
# 2021-10-27: add error handling
# 2021-10-14: Add PIL use to display graphic
import serial
from PIL import Image
import time
import signal
import os.path
import sys
import getopt

# process any command line settings
argv = sys.argv
port = "COM6"
try:
    opts, args = getopt.getopt(argv[1:],"p:")
except getopt.GetoptError:
    print ("correct invocation: " + argv[0] + " < -p 'port'>")
    print("ending...")
    sys.exit(2)
for opt, arg in opts:
    if opt == '-p':
        port = arg

fileName = 'file.bin'
mazSize = 1024 * 10
errs = 0
cnt = 0
waitComplete = 4 # 10
debug = False
# 2021-11-04: change 4 to 8 to 10 to .... secs
# Cabin: COM6
# Condo: COM12
print("port: " + port)
ser = serial.Serial(port, 9600, timeout=waitComplete)
term = False
archiveDir = os.path.isdir("./archive")

def handler(signum, frame):
  global term
  term = True
  print("Termination Started...")

def readBuffer():
    try:
        response = ser.read(mazSize) 
        ln = len(response)
    except OSError as err:
        response = ''
        ln = -1
        print("OS error: {0}".format(err))
    # print("read: " + str(ln))
    return response
    
def writeImage(l, buffer):
    fout = open(fileName, 'wb')
    fout.write(buffer)
    fout.close()
    print(", image written: " + str(len(buffer)), end='')
    if archiveDir:
        tag = buffer[6]
        tag = tag * 256 + buffer[7]
        tag = tag * 256 + buffer[8]
        tag = tag * 256 + buffer[9]
        fileName2 = ("./archive/f"+str(tag)+".bin")
        print(", filename2: " + fileName2 + "]",flush=True)
        fout = open(fileName2, 'wb')
        fout.write(buffer)
        fout.close()        
    # optional resize and display
    if debug == True:
        try:
            im = Image.open(fileName)        
            im = im.resize((100, 100))
            im.show()
        except OSError as err:
            print("OS error: {0}".format(err))
            print("Error ignored!")
            errs += 1
            print("Error cnt: " +str(errs))
        # im.close()
signal.signal(signal.SIGINT, handler)

while term == False:
    cnt += 1
    # print("loop: " + str(cnt))
    print('#',end='',flush=True)
    # read blocks and concat if needed
    response = readBuffer(); 
    ln = len(response)
    if ln < 4:  #toss short buffer at this stage .. this is not robust
        continue
    block = response
    bLen = ln    
    # check for header....
    if response[0] == 0x42 and response[1] == 0x4d:
        imLen = response[2] + 256*response[3]
        print("[bmp file, len: " + str(imLen),end='')    
    else:
        # pass junk thru...
        imLen = 0
        print("!!pass thru, len: " + str(ln) + "!!")
    while imLen > bLen:
        # this is only done for bmp file!
        time.sleep(5) # just a slight paws!
        response = readBuffer()
        ln = len(response)
        if ln > 0:
            block = block + response
            blen = bLen + ln
        else:
           break   # something is wrong, start over!
    # end inner while 
    if bLen > 0:
        writeImage(bLen, block)
print("done!")