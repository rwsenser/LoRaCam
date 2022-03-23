# Viewer7 from Viewer6 and  more-or-less from https://pythonguides.com/python-tkinter-image/
from tkinter import *
from PIL import Image, ImageTk
import signal
import os.path
import glob

# 2022-01-18: Add filenames to display and clean up code

# tunable constants
APP_NAME = "Viewer7 - Receive and View Images from LoRa"
DEFAULT_SCREEN_SIZE = 300
ARCHIVE_DIR = "archive/"
FILE_NAME = "file.bin"

currentNum = 0  # curse the cursor :)

def whichImage(_arg):
    global currentNum
    mylist = sorted([f for f in glob.glob(ARCHIVE_DIR + "*.bin")])
    ln = len(mylist)
    if ln > 0:
        if _arg == "|<<":
            fname = mylist[0]
            num = 0
            currentNum = num
        elif _arg == "<<":
            if currentNum-1 >= 0:
                currentNum -= 1;
                fname = mylist[currentNum]
                num = currentNum
            else: # no scroll action
                fname = mylist[currentNum]
                num = currentNum
        elif _arg == ">>":
            # ln is max size of incore list
            if currentNum+1 < ln:
                currentNum += 1;
                fname = mylist[currentNum]
                num = currentNum
            else: # no scroll action
                fname = mylist[0]
                num = 0
                currentNum = num
        elif _arg == ">>|":
            fname = mylist[ln-1]
            num = ln-1
            currentNum = num
        else:
            fname = ""
            num = -1
    else:
        fname = ""
        num = -1;
    # print("whichImage", fname, num)
    return [fname, num]
    
ws = Tk()
ws.title(APP_NAME)
ws.geometry('800x400')
ws.config(bg='#4a7a8c')
errs = 0
term = False
archiveDir = os.path.isdir(ARCHIVE_DIR)
if archiveDir:
    lst = whichImage("|<<")
    scrollFile = lst[0]
    scrollNum = lst[1]
else:
    scrollFile = ""
    scrollNum = -1

def handler(signum, frame):
  global term
  term = True
  print("Terminating.....")
  exit(1)


def resize_func():
    global errs
    showFileName
    showTag
    try:
        image = Image.open(FILE_NAME)
        w = int(size.get())
        h = int(size.get())
        resize_img = image.resize((w, h))
        img = ImageTk.PhotoImage(resize_img)
        disp_img.config(image=img)
        disp_img.image = img
        # tag hidden in file header
        fin = open(FILE_NAME, 'rb')
        buffer = fin.read(10) # only need header
        fin.close()
        tag = buffer[6]
        tag = tag * 256 + buffer[7]
        tag = tag * 256 + buffer[8]
        tag = tag * 256 + buffer[9]
        showTag.delete(0,END)
        showTag.insert(0,str(tag))
        showTag.pack(side=LEFT)
        if archiveDir and scrollFile != "":
            image2 = Image.open(scrollFile)
            resize_img2 = image2.resize((w, h))
            img2 = ImageTk.PhotoImage(resize_img2)
            disp_img_right.config(image=img2)
            disp_img_right.image = img2
            # scrollLabel.pack(padx=50, pady=5, side=LEFT)
            showFileName.delete(0, END)
            showFileName.insert(0, "[" +  str(scrollNum+1) +"]:"+scrollFile)
            showFileName.pack(side=LEFT)
    except OSError as err:
        # print("OS error: {0}".format(err))
        errs += 1
        print("Error ignored! (" + str(errs) + " code: " + str(err) + ")")
    
def auto_resize_func():
    resize_func()
    ws.after(2000, auto_resize_func)

def fullleft_func():
    global scrollFile, scrollNum
    lst = whichImage("|<<") 
    scrollFile = lst[0] 
    scrollNum = lst[1]
    # print("|<< " + scrollFile)
def left_func():
    global scrollFile, scrollNum
    lst = whichImage("<<") 
    scrollFile = lst[0] 
    scrollNum = lst[1]
    # print("<< " + scrollFile)
def right_func():
    global scrollFile, scrollNum
    lst = whichImage(">>") 
    scrollFile = lst[0] 
    scrollNum = lst[1]
    # print(">> " + scrollFile)
def fullright_func():
    global scrollFile, scrollNum
    lst = whichImage(">>|")
    scrollFile = lst[0]
    scrollNum = lst[1]
    # print(">>| " + scrollFile)

signal.signal(signal.SIGINT, handler)

# create needed frames, these hold multiple display items

frame = Frame(ws)
frame.pack()

frameBot = Frame(ws)
frameBot.pack(side=BOTTOM)

Label(
    frame,
    text='Current Image:'
    ).pack(padx=(50,1), pady=5, side=LEFT)
showTag = Entry(frame, width=12)
showTag.insert(0, "")
showTag.pack(padx=(0,20),side=LEFT)

Label(
    frame,
    text='Size'
    ).pack(side=LEFT)
size = Entry(frame, width=10)
size.insert(END, DEFAULT_SCREEN_SIZE)         # default window size ....
size.pack(side=LEFT)

resize_btn = Button(
    frame,
    text='Refresh',
    command=resize_func
)
resize_btn.pack(padx=30,side=LEFT)

scrollLabel = Label(
    frame,
    text='Scroll Image: '
    )
# scrollLabel.pack(padx=50, pady=0, side=LEFT)
scrollLabel.pack(side=LEFT)
showFileName = Entry(frame, width=32)
showFileName.insert(0, "")
showFileName.pack(side=LEFT)

fullLeft_bnt = Button(
    frameBot,
    text='|<<',
    command=fullleft_func
).pack(padx=10, pady=5, side=LEFT)

left_bnt = Button(
    frameBot,
    text='<<',
    command=left_func
).pack(padx=10, pady=5, side=LEFT)

Label(frameBot,
    text='Scroll Image Actions'
    ).pack(padx=50, pady=5, side=LEFT)
    
right_bnt = Button(
    frameBot,
    text='>>',
    command=right_func
).pack(padx=10, pady=5, side=LEFT)

fullRight_bnt = Button(
    frameBot,
    text='>>|',
    command=fullright_func
).pack(padx=10, pady=5, side=LEFT)


disp_img = Label()
disp_img.pack(padx=50, pady=15, side=LEFT)


disp_img_right = Label()
disp_img_right.pack(padx=50, pady=15, side=LEFT)

resize_func()

ws.after(500, auto_resize_func)

ws.mainloop()