import os
from PIL import Image
from io import BytesIO
from datetime import date
import PIL.ImageGrab
import operator
import Data.coords as crds
import json
import win32.win32api as win32
import re
from modules.adbmirror.adb import *
import cv2
import numpy as np
import modules.mydecorators as mydecorators
# Globals
# ------------------------------
x_pad = 1
y_pad = 1

def readJson():
    json_file   = open('coordinates.json')
    json_str    = json_file.read()
    parsed_json = (json.loads(json_str))
    return parsed_json

def get_cords():
    x,y = win32.GetCursorPos()
    x = x - x_pad
    y = y - y_pad
    print(x,y)

def getSnapperFactory(flag):
    if flag == '2':
        return EmulatorSnapper()
    elif flag == '1':
        return ADBSnapper()
    else:
        raise ValueError('value must be 1 or 2')


class Snapper(object):
    def __init__(self):
        self._imgpath  = "Screens/"
        self._backpath = "Backup/"
        self._imgname  = "screen.png"
        self._image    = None

    """
        take the current Screen imgs and move them to Screens/Backup/<day>/quest# - autoincrement
    """
    def store(self, startpath = None):
        today      = date.today()
        startpath  = self._imgpath if not startpath else startpath
        backuppath = self._imgpath + self._backpath
        reg        = r"(.*[a-zA-Z])(.*\d)"
        regpng     = r".*.png" 
        os.makedirs(backuppath+today.strftime("%m-%d-%Y"), exist_ok=True)
        backupdaypath = backuppath + today.strftime("%m-%d-%Y")

        pref     = "quest"
        startVal = 0

        sufxs = []
        # get the destination of the Screens imgs
        for root, dirs, files in os.walk(backupdaypath):
            for d in dirs:
                m = re.match(reg, d)
                sufxs.append(int(m.group(2)))
            
            sufxs.sort()
            break
        
        # creating the new folder
        if len(sufxs) > 0:
            newfolder = pref + str((sufxs[-1] + 1))
        else:
            newfolder = pref + str(startVal)

        newfolderpath = backupdaypath + os.sep + newfolder
        os.makedirs(newfolderpath, exist_ok=True)
        # transfer from Screen dir to the new folder all the .png file
        for root, dirs, files in os.walk(startpath):
            for f in files:
                if re.match(regpng, f) is not None:
                    os.replace(root + f, newfolderpath + os.sep + f)
            break

    def screen(self, *args, **kwargs):
        raise NotImplementedError
    
    def screenpath(self):
        return self._imgpath + self._imgname

class ADBSnapper(Snapper):
    def __init__(self):
        super().__init__()

    @mydecorators.timeit("ADBSnapper.screen")
    def screen(self, *args, **kwargs):
        #return 1
        #return os.system("adb exec-out screencap -p > " + self._imgpath + self._imgname)
        data = run_adb('exec-out screencap -p', out_file="{}{}".format(self._imgpath,self._imgname), *args, **kwargs)
        self._image = cv2.imdecode(np.frombuffer(data, np.uint8), -1)
        return 1

class EmulatorSnapper(Snapper):
    def __init__(self):
        super().__init__()
        self.__crds = crds.Cord()

    def screen(self, *args, **kwargs):
        box_hp = tuple(map(operator.add, (x_pad,y_pad,x_pad,y_pad), self.__crds.homepage))
        im  = PIL.ImageGrab.grab(box_hp)
        im.save(os.getcwd() + '\\' + self._imgpath + self._imgname, 'PNG')
        return 1

