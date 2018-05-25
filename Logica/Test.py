#!/usr/bin/env python3
# coding: utf-8
import sys
import os
from threading import Thread , Event
from PyQt5 import QtWidgets, uic, QtGui, QtCore, QtMultimedia, QtMultimediaWidgets
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QColor
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PIL import Image
import vlc
import resources
import resources2
import QLABEL2
import skvideo.io
import cv2
import numpy as np
import mutagen
from  moviepy.editor import *
from time import time , sleep

"""
Funciones Logica
"""

def openVideo(filename):
    return skvideo.io.vreader(filename)
##end def

def getVideoData(filename):
    data = skvideo.io.ffprobe(filename)['video']
    rate = data['@r_frame_rate']
    frames = data['@nb_frames']
    pix = data['@pix_fmt']
    codec = data['@codec_name']
    bitrate = data['@bit_rate']
    rateint = int(rate[:2])
    vwidth, vheight  = int(data['@coded_width']) , int(data['@coded_height'])
    return [rateint, vwidth, vheight, frames, rate, pix, codec, bitrate]
##end def

def openImage(filename):
    return cv2.imread(filename)
##end def

def getImageData(image):
    iwidth, iheight, depht = image.shape
    return [iwidth,iheight,depht]
##end def

def convertPos(x,y,video):
    orx = 640
    ory = 360
    vwidth = getVideoData(video)[1]
    vheight = getVideoData(video)[2]
    return [(x*vwidth)/orx, (y*vheight)/ory]
##end def

def addImage(video,videotemp,img,start,end,pos):
    start = int(start)
    end = int(end)
    print("Adding Image...")
    reader = skvideo.io.FFmpegReader(video)
    image =cv2.cvtColor(openImage(img),4)
    rateint = getVideoData(video)[0]
    writer = skvideo.io.FFmpegWriter(videotemp, inputdict={
      '-r': getVideoData(video)[4],
    },
    outputdict={
      '-vcodec': getVideoData(video)[6],
      '-pix_fmt': getVideoData(video)[5],
      '-r': getVideoData(video)[4],
      '-bit_rate': getVideoData(video)[7],
    })
    cframe = 0
    start_time = time()
    for frame in reader.nextFrame():
        if cframe >= start*rateint and cframe < end*rateint:
            addImageHelper(frame,image,pos,getVideoData(video))
            writer.writeFrame(frame)
        else:
            writer.writeFrame(frame)
        cframe+=1
        #if cframe == 100:
        #    break
    writer.close()
    setOriginalAudio(video,videotemp)
    elapsed_time = time() - start_time
    print("Numero de frames: ", cframe)
    print("Tiempo total transcurrido: %0.10f s." % elapsed_time)
##end def

def addImageHelper(frame,image,pos,videoinfo):
    iwidth = getImageData(image)[0]
    iheight = getImageData(image)[1]
    vwidth = videoinfo[1]
    vheight = videoinfo[2]
    x, y = int(pos[0]),int(pos[1])
    start_time = time()
    for i in range(0,iwidth):
        for j in range(0, iheight):
            if i + y < vheight and j + x < vwidth:
                frame[i+y][j+x] = image[i][j]
    elapsed_time = time() - start_time
    print("Tiempo total transcurrido: %0.10f s." % elapsed_time)
##end def

def setOriginalAudio(video,tempfile):
    videoclip = VideoFileClip(video)
    videoclip2 = VideoFileClip(tempfile)
    audio = videoclip.audio
    audio.write_audiofile("ot.mp3")
    videoclip.close()
    videoclip2.write_videofile("temp.mp4",codec=getVideoData(video)[6],audio="ot.mp3")
    videoclip2.close()
    os.remove(tempfile)
    os.rename("temp.mp4",tempfile)
    os.remove("ot.mp3")
##end def

def addSound (start, sound2, video):
    videoclip = VideoFileClip(video)
    audio = videoclip.audio
    audio.write_audiofile("ot.mp3")
    f = mutagen.File("ot.mp3")
    br = (f.info.bitrate/8000)*1024
    c1 = open("ot.mp3","r+b")
    c2 = open(sound2,"rb")
    byte2 = c2.read()
    size = int (start*br)
    c1.read(size)
    c1.write(byte2)
    c1.close()
    c2.close()
    videoclip.write_videofile("temp.mp4",codec=getVideoData(video)[6],audio="ot.mp3")
    videoclip.close()
    os.remove(video)
    os.rename("temp.mp4",video)
    return True
##end def

''' Estructura con datos basicos para saber path '''
class MediaFile:
    def __init__(self,name,path,typef):
        self.name = name
        self.path = path
        self.typef = typef
''' Form '''
class Form(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        uic.loadUi('../Vista/gracias.ui', self)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        self.file_list = []
        super(MainWindow, self).__init__()
        uic.loadUi('../Vista/interface.ui', self)

        ''' Actions for label buttons of widget list '''
        self.Add.clicked.connect(self.Add_files)
        self.Select.clicked.connect(self.get_selected_item)
        self.Erase.clicked.connect(self.remove_selected_item)
        self.ChangePosition.clicked.connect(self.change_image)
        ''' Actions for Control the editor '''
        self.export_2.clicked.connect(self.Remderize_video)
        self.ChangeImage.clicked.connect(self.put_image)
        self.ChangeAudio.clicked.connect(self.put_audio)
        self.get_start.clicked.connect(self.set_init_frame)
        self.get_end.clicked.connect(self.set_end_frame)


        self.label2 = QtWidgets.QLabel("Ja'mapel cocunubo", self)
        self.label2.setText("")
        ''' Actions of menu bar '''
        self.actionExit.triggered.connect(self.exit)
        self.actionExport.triggered.connect(self.Remderize_video)
        self.actionOpen_Video.triggered.connect(self.OpenFile2)
        ''' Para entradas y salidas '''
        self.to_draw = None
        self.selected_item = None # Variable con el item seleccionado por ej imagen ,a udio , video
        self.changes = None
        self.actvid = None
        self.actaud = None
        self.s1 = None
        self.s2 = None
        self.actimg = None
        self.tinicio = None
        self.tfin = None
        self.minframe = -1
        self.maxframe = -1
        self.newpath = None
        self.inicio = None # Variable con frame de inicio
        self.final = None # Variable con frame de terminacion
        self.x = None # Variable con posicion relativa en x
        self.y = None # Variable con posicion relative en y
        self.frame = None
        ''' DOnde puedes probar lo del VLC '''
        # creating a basic vlc instance
        self.instance = vlc.Instance()
        self.mediaPlayer =  self.instance.media_player_new()
        # In this widget, the video will be drawn
        if sys.platform == "darwin": # for MacOS
            from PyQt5.QtWidgets import QMacCocoaViewContainer
            self.videoPlayer = QMacCocoaViewContainer(0)
        else:
            self.videoPlayer = QtWidgets.QFrame()
        self.videoPlayer.resize(640,360)
        self.palette = self.videoPlayer.palette()
        self.palette.setColor (QPalette.Window,
                               QColor(0,0,0))
        self.videoPlayer.setPalette(self.palette)
        self.videoPlayer.setAutoFillBackground(True)
        self.isPaused = False
        self.Play.clicked.connect(self.play)
        self.Pause.clicked.connect(self.pause)
        self.Stop.clicked.connect(self.stop)

        self.Timer.setMaximum(1000)
        self.Timer.sliderMoved.connect(self.setPosition)
        self.Volume.sliderMoved.connect(self.setVolume)
        self.Volume.setRange(0, 100)
        self.lay.addWidget(self.videoPlayer)

        self.reloj = QtCore.QTimer(self)
        self.reloj.setInterval(1)
        self.reloj.timeout.connect(self.updateUI)

        self.t = Thread(target=self.counter )
        self.t2 = Thread(target=self.counter2 )
        self.t3 = Thread(target=self.Draw_Image)

        self.timeEdit.setDisplayFormat("hh:mm:ss AP")
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1000)

        self.t.start()
        self.t2.start()

        #self.selection.mousePressEvent = self.getPos

        #self.layout = QtWidgets.QVBoxLayout()
        self.counterpro.display(0)
        self.show()

    def updateTime(self):
        current = QtCore.QDateTime.currentDateTime()
        self.timeEdit.setTime(current.time())

    def getPos(self , event):
        x = event.pos().x()
        y = event.pos().y()
        self.xspin.setValue(x * 1.0)
        self.yspin.setValue(y * 1.0)
        self.x = x
        self.y = y
        self.label.hide()
        print(x,y)

        self.ChangePosition.setEnabled(True)
        self.spinBox.setEnabled(False)
        self.spinBox_2.setEnabled(False)
        self.xlabel_2.setEnabled(False)
        self.xlabel_3.setEnabled(False)

        if self.tinicio == None or self.actimg == None or self.actvid == None or self.x == None or self.y == None :
            print("Error cargando algo")
        else:
            pos = convertPos(self.x,self.y,self.actvid)
            self.changes=[self.actvid,self.actimg,self.tinicio,self.tfin,pos]
            print("Exito , ", pos , self.actvid , self.actimg)

    def get_file(self,name):
        ret = None
        for x in self.file_list :
            if x.name == name:
                ret = x
                break
        print(ret.name)
        return ret
    def counter(self ):
        while 1:
            self.counterpro.display(self.getPosition() * 1000)

    def counter2(self):
        while 1:
            self.Timer.setValue(self.getPosition() * 1000)

    def Add_files(self):
        image_formats = [".jpg",".jpeg",".png",".ico",".nef",".bpm"]
        video_formats = [".avi",".mp4",".mov",".mpeg",".mkv"]
        audio_formats = [".mp3",".wav"]
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self,"Select Media Files", "","All Files (*);;Image Files (*.jpeg)", options=options)
        name = os.path.basename(fileName)
        filename, file_extension = os.path.splitext(name)
        ubication = None
        if file_extension.lower() in image_formats :
            image = Image.open(fileName)
            image.thumbnail((500, 500), Image.ANTIALIAS)
            image.save('../Resources/'+"."+filename+".png", 'PNG')
            ubication = '../Resources/'+"."+filename+".png"
            typef = "image"
        if file_extension.lower() in audio_formats :
            ubication = "../Resources/audio-file.png"
            typef = "audio"
        if file_extension.lower() in video_formats :
            ubication = "../Resources/video-file.png"
            typef = "video"
        if ubication != None:
            pixmap = QIcon(ubication)
            item = QtWidgets.QListWidgetItem(pixmap,filename)
            self.file_list.append(MediaFile(filename,fileName,typef))
            self.filelist.addItem(item)

    def get_selected_item(self):
        self.ChangePosition.setEnabled(False)
        self.ChangeImage.setEnabled(False)
        self.ChangeAudio.setEnabled(False)
        self.spinBox.setEnabled(False)
        self.spinBox_2.setEnabled(False)
        self.xlabel_2.setEnabled(False)
        self.xlabel_3.setEnabled(False)
        self.get_start.setEnabled(False)
        self.get_end.setEnabled(False)
        if len(self.filelist.selectedItems()) > 0:
            self.selected_item = self.get_file(self.filelist.selectedItems()[0].text())
            if self.selected_item.typef == "image":
                self.ChangeImage.setEnabled(True)
                self.actimg = self.selected_item.path
                self.spinBox.setEnabled(True)
                self.spinBox_2.setEnabled(True)
                self.xlabel_2.setEnabled(True)
                self.xlabel_3.setEnabled(True)
                self.get_start.setEnabled(True)
                self.get_end.setEnabled(True)
            elif self.selected_item.typef == "audio":
                self.ChangeAudio.setEnabled(True)
                self.spinBox.setEnabled(True)
                #self.spinBox_2.setEnabled(True)
                self.xlabel_2.setEnabled(True)
                #self.xlabel_3.setEnabled(True)
                self.actaud = self.selected_item.path
            if self.selected_item.typef == "video":
                self.OpenFile(self.selected_item.path)
                self.actvid = self.selected_item.path
    def set_init_frame(self):
        self.spinBox.setValue(int(round(self.getPosition() * 1000) ))
    def set_end_frame(self):
        self.spinBox_2.setValue(int(round(self.getPosition() * 1000) ))
    def calculateTime(self):
        self.minframe = self.spinBox.value()
        self.maxframe = self.spinBox_2.value()

        framerate = self.mediaPlayer.get_fps()
        startf = self.spinBox.value()
        endf = self.spinBox_2.value()
        self.tinicio = startf/framerate
        self.tfin = endf/framerate

    def remove_selected_item(self):
        listItems=self.filelist.selectedItems()
        if len(listItems) == 0 : return
        self.filelist.takeItem(self.filelist.row(listItems[0]))
    ''' Functions for edit the video '''
    ''' Todos los metodos que consideres dejalos comentados y pone con que lo linkeo '''

    def Remderize_video(self): # Metodo con funcion de remderizar
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        self.newpath, _ = QtWidgets.QFileDialog.getSaveFileName(self,"Select Media Files", "","All Files (*)", options=options)

        if False :
            print("Error cargando algo")
        else:
            pid = os.fork()
            if pid == 0 :
                print(self.changes[0],self.newpath,self.changes[1],self.changes[2],self.changes[3],self.changes[4])
                addImage(self.changes[0],self.newpath,self.changes[1],self.changes[2],self.changes[3],self.changes[4])
                exit(0)

    def put_image(self): # Metodo que pone la imagen
        #self.label.show()
        self.get_start.setEnabled(True)
        self.get_end.setEnabled(True)
        self.label = QtWidgets.QLabel("Ja'mapel", self)
        self.label.setText("")
        self.label.setGeometry(QtCore.QRect(19,44, 640, 360))
        self.label.setMinimumSize(QtCore.QSize(640, 360))
        self.label.setMaximumSize(QtCore.QSize(640, 360))
        self.label.setCursor(QtCore.Qt.PointingHandCursor)
        self.label.mousePressEvent = self.getPos
        self.label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.label.show()
        self.ChangeImage.setEnabled(False)
        self.calculateTime()
        self.make_mini_image()
        self.t3.start()

    def change_image(self): # Metodo que pone la imagen

        #self.label.show()
        self.label = QtWidgets.QLabel("Ja'mapel", self)
        self.label.setText("")
        self.label.setGeometry(QtCore.QRect(19,44, 640, 360))
        self.label.setMinimumSize(QtCore.QSize(640, 360))
        self.label.setMaximumSize(QtCore.QSize(640, 360))
        self.label.setCursor(QtCore.Qt.PointingHandCursor)
        self.label.mousePressEvent = self.getPos
        self.label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.label.show()
        self.ChangeImage.setEnabled(False)


    def chg_image(self): # Metodo que pone la imagen
        self.calculateTime()
        if self.tinicio == None or self.actimg == None or self.actvid == None or self.x == None or self.y == None :
            print("Error cargando algo")
        else:
            pos = convertPos(self.x,self.y,self.actvid)
            self.changes=[self.actvid,self.actimg,self.tinicio,self.tfin,pos]

    def exit(self):
        pos = [self.x,self.y]
        self.changes.append([self.actvid,self.actimg,self.tinicio,self.tfin, pos])

    def put_audio(self): # Metodo que pone el audio
        self.calculateTime()
        if self.tinicio == None or self.actaud==None or self.actvid==None:
            print("Error cargando algo")
        else:
            addSound(self.tinicio,self.actaud,self.actvid)
    def exit(self):
        window = Form()
        window.show()
        window.exec_()
        exit(0)
    def play (self):
        #if self.mediaPlayer.is_playing():
        self.mediaPlayer.play()
        self.isPaused = False
        self.videoPlayer.resize(640,360)
    def pause(self):
        #if not self.mediaPlayer.is_playing():
        self.mediaPlayer.pause()
        self.isPaused = True
    def stop(self):
        self.mediaPlayer.stop()
    def setVolume(self, Volume):
        self.mediaPlayer.audio_set_volume(Volume)
    def setPosition(self, position):
        self.mediaPlayer.set_position(position / 1000.0)
    def getPosition(self ):
        return self.mediaPlayer.get_position()
    def updateUI(self):
        self.Timer.setValue(self.mediaplayer.get_position() * 1000)
        self.reloj.stop()
        if not self.isPaused:
            self.stop()
    def make_mini_image(self):
        image = Image.open(self.actimg)
        w, h = image.size
        self.s1 = w/2
        self.s2 = h/2
        image.thumbnail((self.s1, self.s2), Image.ANTIALIAS)
        image.save('../Resources/'+"."+"DRAW"+".png", 'PNG')
        self.to_draw = '../Resources/'+"."+"DRAW"+".png"

    def OpenFile(self, filename=None):
        '''
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(self,"Select Media Files", "","All Files (*);;Image Files (*.jpeg)", options=options)
        '''
        if sys.version < '3':
            filename = unicode(filename)
        self.media = self.instance.media_new(filename)
        self.mediaPlayer.set_media(self.media)
        self.media.parse()

        if sys.platform.startswith('linux'):
            self.mediaPlayer.set_xwindow(self.videoPlayer.winId())
        elif sys.platform == "win32":
            self.mediaPlayer.set_hwnd(self.videoPlayer.winId())
        elif sys.platform == "darwin":
            self.mediaPlayer.set_nsobject(int(self.videoPlayer.winId()))
        self.videoPlayer.resize(640,360)
        self.play()
    def OpenFile2(self):

        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self,"Select Media Files", "","All Files (*);;Image Files (*.jpeg)", options=options)

        if sys.version < '3':
            filename = unicode(filename)
        self.media = self.instance.media_new(filename)
        self.mediaPlayer.set_media(self.media)
        self.media.parse()

        if sys.platform.startswith('linux'):
            self.mediaPlayer.set_xwindow(self.videoPlayer.winId())
        elif sys.platform == "win32":
            self.mediaPlayer.set_hwnd(self.videoPlayer.winId())
        elif sys.platform == "darwin":
            self.mediaPlayer.set_nsobject(int(self.videoPlayer.winId()))
        self.videoPlayer.resize(640,360)
        self.play()
    def Draw_Image(self):
        while 1 :
            sleep(0.05)
            var = self.getPosition() * 1000
            #print(" tengo ",var," quiero ", self.minframe , " con un " , self.maxframe)
            if var >= self.minframe and var <= self.maxframe :
                if self.actimg != None :
                    self.label2.setGeometry(QtCore.QRect(self.x,self.y, self.s1, self.s2))
                    self.label2.setMinimumSize(QtCore.QSize(self.s1, self.s2))
                    self.label2.setMaximumSize(QtCore.QSize(self.s1, self.s2))
                    self.label2.setAttribute(QtCore.Qt.WA_TranslucentBackground)
                    pixmap = QPixmap(self.to_draw)
                    self.label2.setPixmap(pixmap);
                    self.label2.setMask(pixmap.mask());
                    self.label2.show()
            else :
                self.label2.hide()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
