__author__ = 'Dipnarayan Das,Hera Hassan'
__copyright__ = "All Rights Reserved"
__credits__ = ["Dipnarayan Das","Hera Hassan"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Dipnarayan Das,Hera Hassan"
__email__ = "dipnarayan.das35@gmail.com"
__status__ = "Under Development"

import pyaudio
import wave
from array import array
from sys import byteorder
from struct import pack
import sys
import wave
import copy
import subprocess
from time import sleep
import os
import time
from flask import Flask, request, redirect, url_for, render_template, Response
from werkzeug import secure_filename
import speech_recognition as sr
from os import path
import tkinter
from pydub import AudioSegment
from pydub.playback import play
import json
import glob
import requests
import logging

global saddress
with open("config.txt") as f:
	data=f.read()

saddress=data
# Loading the grammar
'''
try:
	r = requests.get(url = data+"/algo.py")
except requests.exceptions.Timeout:
	print('Timeout')
    # Maybe set up for a retry, or continue in a retry loop
except requests.exceptions.TooManyRedirects:
	print('Too many redirects')
    # Tell the user their URL was bad and try a different one
except requests.exceptions.RequestException as e:
    # catastrophic error. bail.
    #print(e)
    print('Server not responding. Following may be the causes')
    print('1. You have not proper internet connection -> Recheck the connection')
    print('2. Server address was changed -> Upgrade the module or download the latest release')
    sys.exit(1)
'''
with open('grammar/grammar.txt') as f:  
	grammars=f.read().split(",")

for g in grammars:
	with open('grammar/'+g+'.txt') as f1:
		exec(g+"="+str(f1.read().split("|")))

#exec(r.content.decode())

audio=[]
dataj={}
emotionj={}
emotions=["fear","anger","sadness","stronger","joy","disgust","surprise","trust","anticipation","nothing"]
emotion_effect=["slow,loud","fast,loud","slow,cool","loud","louder","slow,loud","loudest","slow,cool","slow","nothing"]
ctypes=["loud","cool","silence","fast","slow"]

content_words=[verb,noun,adjective,adverb,wh]#stressed negative_auxiliaries
structure_words=[pronoun,preposition,article,aux_verb,modal_verb]#non-stressed conjunction

sys_offset=1
content_word_effect="loud=1.5,slow=0.8"
structure_word_effect="fast=1.3"

#os.system("curl "+saddress+"/database/voices/voice.dll --output temp.dll --silent")

with open('database/voices/voice.dll') as json_file:  
    dataj = json.load(json_file)

#os.system("curl "+saddress+"/database/wordinfo.dll --output temp.dll --silent")

with open('database/wordinfo.dll') as json_file:  
    emotionj = json.load(json_file)


def fslice(word,per):
    dur=(duration(word)*per)/100
    #print(dur)
    return word[:int(dur)]

def bslice(word,per):
    dur=(duration(word)*per)/100
    #print(dur)
    return word[-int(dur):]

def crossfader(word1,word2,per):
    mil=(duration(word1)*per)/100
    return word1.append(word2, crossfade=mil)

def fader(word,mil1,mil2):
    return word.fade_in(mil1).fade_out(mil2)


def applygain(word,val):
    #word+=val
    word.export("tempa.wav", format="wav", tags={'artist': 'Hera Hassan', 'album': 'N/A', 'comments': 'This is created by Twee'})
    os.system("ffmpeg -nostats -loglevel 0 -i tempa.wav -filter:a \"volume="+str(val)+"\" tempd.wav")
    word=AudioSegment.from_wav("tempd.wav")
    os.system("del tempa.wav & del tempd.wav")
    return word

def removegain(word,val):
    #word-=val
    word.export("tempa.wav", format="wav", tags={'artist': 'Hera Hassan', 'album': 'N/A', 'comments': 'This is created by Twee'})
    os.system("ffmpeg -nostats -loglevel 0 -i tempa.wav -filter:a \"volume="+str(val)+"\" tempd.wav")
    word=AudioSegment.from_wav("tempd.wav")
    os.system("del tempa.wav & del tempd.wav")
    return word

def mix(word1,word2):
    #awesome = do_it_over.fade_in(2000).fade_out(3000)
    word1+=word2
    return word1
def duration(word):
    return len(word)#millisecond

def create_silence(val):
    return AudioSegment.silent(duration=val)#millisecond

def create_stereo(word1,word2):
    #left_channel = AudioSegment.from_wav(word1)
    #right_channel = AudioSegment.from_wav(word2)
    word1.export("tempa.wav", format="wav", tags={'artist': 'Hera Hassan', 'album': 'N/A', 'comments': 'This is created by Twee'})
    word2.export("tempb.wav", format="wav", tags={'artist': 'Hera Hassan', 'album': 'N/A', 'comments': 'This is created by Twee'})
    os.system("ffmpeg -nostats -loglevel 0 -i tempa.wav -i tempb.wav -filter_complex \"[0:a][1:a]amerge=inputs=2[aout]\" -map \"[aout]\" out.wav")
    #stereo_sound = AudioSegment.from_mono_audiosegments(word1,word2)
    stereo_sound=AudioSegment.from_wav("out.wav")
    os.system("del tempa.wav & del tempb.wav & del out.wav")
    return stereo_sound

def speed(word,val):
    # shift the pitch up by half an octave (speed will increase proportionally)
    '''
    octaves = val#Ex: 0.5
    new_sample_rate = int(word.frame_rate * (2.0 ** octaves))
    hipitch_sound = word._spawn(word.raw_data, overrides={'frame_rate': new_sample_rate})
    hipitch_sound = hipitch_sound.set_frame_rate(44100)
    '''
    word.export("tempa.wav", format="wav", tags={'artist': 'Hera Hassan', 'album': 'N/A', 'comments': 'This is created by Twee'})
    os.system("ffmpeg -nostats -loglevel 0 -i tempa.wav -filter:a \"atempo="+str(val)+"\" -vn tempd.wav")
    word=AudioSegment.from_wav("tempd.wav")
    os.system("del tempa.wav & del tempd.wav")
    return word

def about():
    os.system("Fn.dll Print 0a \"Twee is Artificially Intelligent TTS Engine. For more information see Twee online documentation.\"")
    print(" ")

def author():
    os.system("color f0 & cls & InsertBmp /x:0 /y:50 /p:author.bmp /z:100 & pause")
    os.system("cls & Fn.dll Print 0a \"Contact Email:\"")
    print(" ")
    print("Dipnarayan Das - dipnarayan.das35@gmail.com")
    print("Hera Hassan - herahassan6666@gmail.com")

if len(sys.argv)>0:
    if sys.argv[sys_offset+1]=="-author":
        author()
    if sys.argv[sys_offset+1]=="-about":
        about()
    if sys.argv[sys_offset+1]=="-init":
        os.system("title Twee & color f0 & Fn.dll Print 0a \"Thank you for using Twee\"")
        print(" ")
    if sys.argv[sys_offset+1]=="-listen":
        app = Flask(__name__)       
        log = logging.getLogger('werkzeug')
        log.disabled = True
        app.logger.disabled = True
        @app.route("/<path>")
        def index(path):
            #print(path)
            #command='nlp.py '+path
            #os.system(command)
            path_par=path.split(" ")
            if path_par[0]=="-i":
                if path_par[1]=="-s":
                    command=''
                    audio=create_silence(100)
                    count=len(path_par)
                    #global val
                    val=-1
                    #print(path_par)
                    for i in range(count-2):
                        #print("================================")
                        #print(path_par[i+2])
                        try:
                            val=dataj[path_par[i+2]][0]['info']
                            #print(emotionj[path_par[i+2]][0]['emotions'])
                            #os.system("curl "+saddress+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                            audiodata=AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2)
                        except:
                            print("Twee is not able to tell this right now. Sorry for inconvenience.")
                        if emotions.index(emotionj[path_par[i+2]][0]['emotions'])==0:
                            emotionsd=emotion_effect[0]
                            emotions_fil=emotionsd.split(",")
                            for fil in emotions_fil:
                                if fil=="loud":
                                    audiodata=applygain(audiodata,2.0)
                                elif fil=="cool":
                                    audiodata=removegain(audiodata,0.5)
                                elif fil=="fast":
                                    audiodata=speed(audiodata,1.5)
                                elif fil=="slow":
                                    audiodata=speed(audiodata,0.5)
                                elif fil=="louder":
                                    audiodata=applygain(audiodata,4.0)
                                elif fil=="loudest":
                                    audiodata=applygain(audiodata,10.0)
                                elif fil=="nothing":
                                    audiodata=audiodata

                        elif emotions.index(emotionj[path_par[i+2]][0]['emotions'])==1:
                            emotionsd=emotion_effect[1]
                            emotions_fil=emotionsd.split(",")
                            for fil in emotions_fil:
                                if fil=="loud":
                                    audiodata=applygain(audiodata,2.0)
                                elif fil=="cool":
                                    audiodata=removegain(audiodata,0.5)
                                elif fil=="fast":
                                    audiodata=speed(audiodata,1.5)
                                elif fil=="slow":
                                    audiodata=speed(audiodata,0.5)
                                elif fil=="louder":
                                    audiodata=applygain(audiodata,4.0)
                                elif fil=="loudest":
                                    audiodata=applygain(audiodata,10.0)
                                elif fil=="nothing":
                                    audiodata=audiodata

                        elif emotions.index(emotionj[path_par[i+2]][0]['emotions'])==2:
                            emotionsd=emotion_effect[2]
                            emotions_fil=emotionsd.split(",")
                            for fil in emotions_fil:
                                if fil=="loud":
                                    audiodata=applygain(audiodata,2.0)
                                elif fil=="cool":
                                    audiodata=removegain(audiodata,0.5)
                                elif fil=="fast":
                                    audiodata=speed(audiodata,1.5)
                                elif fil=="slow":
                                    audiodata=speed(audiodata,0.5)
                                elif fil=="louder":
                                    audiodata=applygain(audiodata,4.0)
                                elif fil=="loudest":
                                    audiodata=applygain(audiodata,10.0)
                                elif fil=="nothing":
                                    audiodata=audiodata

                        elif emotions.index(emotionj[path_par[i+2]][0]['emotions'])==3:
                            emotionsd=emotion_effect[3]
                            emotions_fil=emotionsd.split(",")
                            for fil in emotions_fil:
                                if fil=="loud":
                                    audiodata=applygain(audiodata,2.0)
                                elif fil=="cool":
                                    audiodata=removegain(audiodata,0.5)
                                elif fil=="fast":
                                    audiodata=speed(audiodata,1.5)
                                elif fil=="slow":
                                    audiodata=speed(audiodata,0.5)
                                elif fil=="louder":
                                    audiodata=applygain(audiodata,4.0)
                                elif fil=="loudest":
                                    audiodata=applygain(audiodata,10.0)
                                elif fil=="nothing":
                                    audiodata=audiodata

                        elif emotions.index(emotionj[path_par[i+2]][0]['emotions'])==4:
                            emotionsd=emotion_effect[4]
                            emotions_fil=emotionsd.split(",")
                            for fil in emotions_fil:
                                if fil=="loud":
                                    audiodata=applygain(audiodata,2.0)
                                elif fil=="cool":
                                    audiodata=removegain(audiodata,0.5)
                                elif fil=="fast":
                                    audiodata=speed(audiodata,1.5)
                                elif fil=="slow":
                                    audiodata=speed(audiodata,0.5)
                                elif fil=="louder":
                                    audiodata=applygain(audiodata,4.0)
                                elif fil=="loudest":
                                    audiodata=applygain(audiodata,10.0)
                                elif fil=="nothing":
                                    audiodata=audiodata

                        elif emotions.index(emotionj[path_par[i+2]][0]['emotions'])==5:
                            #print("6")
                            emotionsd=emotion_effect[5]
                            emotions_fil=emotionsd.split(",")
                            for fil in emotions_fil:
                                if fil=="loud":
                                    audiodata=applygain(audiodata,2.0)
                                elif fil=="cool":
                                    audiodata=removegain(audiodata,0.5)
                                elif fil=="fast":
                                    audiodata=speed(audiodata,1.5)
                                elif fil=="slow":
                                    audiodata=speed(audiodata,0.5)
                                elif fil=="louder":
                                    audiodata=applygain(audiodata,4.0)
                                elif fil=="loudest":
                                    audiodata=applygain(audiodata,10.0)
                                elif fil=="nothing":
                                    audiodata=audiodata

                        elif emotions.index(emotionj[path_par[i+2]][0]['emotions'])==6:
                            emotionsd=emotion_effect[6]
                            emotions_fil=emotionsd.split(",")
                            for fil in emotions_fil:
                                if fil=="loud":
                                    audiodata=applygain(audiodata,2.0)
                                elif fil=="cool":
                                    audiodata=removegain(audiodata,0.5)
                                elif fil=="fast":
                                    audiodata=speed(audiodata,1.5)
                                elif fil=="slow":
                                    audiodata=speed(audiodata,0.5)
                                elif fil=="louder":
                                    audiodata=applygain(audiodata,4.0)
                                elif fil=="loudest":
                                    audiodata=applygain(audiodata,10.0)
                                elif fil=="nothing":
                                    audiodata=audiodata

                        elif emotions.index(emotionj[path_par[i+2]][0]['emotions'])==7:
                            emotionsd=emotion_effect[7]
                            emotions_fil=emotionsd.split(",")
                            for fil in emotions_fil:
                                if fil=="loud":
                                    audiodata=applygain(audiodata,2.0)
                                elif fil=="cool":
                                    audiodata=removegain(audiodata,0.5)
                                elif fil=="fast":
                                    audiodata=speed(audiodata,1.5)
                                elif fil=="slow":
                                    audiodata=speed(audiodata,0.5)
                                elif fil=="louder":
                                    audiodata=applygain(audiodata,4.0)
                                elif fil=="loudest":
                                    audiodata=applygain(audiodata,10.0)
                                elif fil=="nothing":
                                    audiodata=audiodata

                        elif emotions.index(emotionj[path_par[i+2]][0]['emotions'])==8:
                            emotionsd=emotion_effect[8]
                            emotions_fil=emotionsd.split(",")
                            for fil in emotions_fil:
                                if fil=="loud":
                                    audiodata=applygain(audiodata,2.0)
                                elif fil=="cool":
                                    audiodata=removegain(audiodata,0.5)
                                elif fil=="fast":
                                    audiodata=speed(audiodata,1.5)
                                elif fil=="slow":
                                    audiodata=speed(audiodata,0.5)
                                elif fil=="louder":
                                    audiodata=applygain(audiodata,4.0)
                                elif fil=="loudest":
                                    audiodata=applygain(audiodata,10.0)
                                elif fil=="nothing":
                                    audiodata=audiodata

                        elif emotions.index(emotionj[path_par[i+2]][0]['emotions'])==9:
                            emotionsd=emotion_effect[9]
                            emotions_fil=emotionsd.split(",")
                            for fil in emotions_fil:
                                if fil=="loud":
                                    audiodata=applygain(audiodata,2.0)
                                elif fil=="cool":
                                    audiodata=removegain(audiodata,0.5)
                                elif fil=="fast":
                                    audiodata=speed(audiodata,1.5)
                                elif fil=="slow":
                                    audiodata=speed(audiodata,0.5)
                                elif fil=="louder":
                                    audiodata=applygain(audiodata,4.0)
                                elif fil=="loudest":
                                    audiodata=applygain(audiodata,10.0)
                                elif fil=="nothing":
                                    audiodata=audiodata

                        elif emotions.index(emotionj[path_par[i+2]][0]['emotions'])==10:
                            emotionsd=emotion_effect[10]
                            emotions_fil=emotionsd.split(",")
                            for fil in emotions_fil:
                                if fil=="loud":
                                    audiodata=applygain(audiodata,2.0)
                                elif fil=="cool":
                                    audiodata=removegain(audiodata,0.5)
                                elif fil=="fast":
                                    audiodata=speed(audiodata,1.5)
                                elif fil=="slow":
                                    audiodata=speed(audiodata,0.5)
                                elif fil=="louder":
                                    audiodata=applygain(audiodata,4.0)
                                elif fil=="loudest":
                                    audiodata=applygain(audiodata,10.0)
                                elif fil=="nothing":
                                    audiodata=audiodata

                        audio=mix(audio,audiodata)
                        command+=path_par[i+2]+" "
                    #print(command)
                    with open("temp.dll", "wb") as fwav:
                        fwav.write(audio.raw_data)
                    os.system("echo y | ffmpeg -nostats -loglevel 0 -f s16le -ar 44.1k -ac "+str(1)+" -i temp.dll processed.wav")
                    data=''
                    def generate():
                        with open("processed.wav", "rb") as fwav:
                            data = fwav.read(1024)
                            while data:
                                yield data
                                data = fwav.read(1024)
                        os.system("del processed.wav")
                    return Response(generate(), mimetype="audio/x-wav")
            elif path_par[0]=="-c":
                if path_par[1]=="-s":
                    command=''
                    audiodata=create_silence(100)
                    count=len(path_par)
                    #global val
                    val=-1
                    for i in range(count-2):
                        if path_par[i+2].split("~")[0]!="silence":
                            try:
                                val=dataj[path_par[i+2].split("~")[1]][0]['info']
                            except:
                                print("Twee is not able to tell this right now. Sorry for inconvenience.")
                            if path_par[i+2].split("~")[0]=="loud":
                                #os.system("curl "+saddress+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                                audiodata=mix(audiodata,applygain(AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2),2.0))
                            elif path_par[i+2].split("~")[0]=="cool":
                                #os.system("curl "+saddress+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                                audiodata=mix(audiodata,removegain(AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2),0.5))
                            elif path_par[i+2].split("~")[0]=="fast":
                                #os.system("curl "+saddress+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                                audiodata=mix(audiodata,speed(AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2),1.5))
                            elif path_par[i+2].split("~")[0]=="slow":
                                #os.system("curl "+saddress+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                                audiodata=mix(audiodata,speed(AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2),0.5))
                            elif path_par[i+2].split("~")[0]=="na":
                                #os.system("curl "+saddress+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                                audiodata=mix(audiodata,AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2))
                            command+=path_par[i+2]+" "
                        else:
                            audiodata=mix(audiodata,create_silence(int(path_par[i+2].split("-")[1])))
                            command+=p[i+2]+" "
                    #print(command)
                    with open("temp.dll", "wb") as fwav:
                        fwav.write(audiodata.raw_data)
                    os.system("echo y | ffmpeg -nostats -loglevel 0 -f s16le -ar 44.1k -ac "+str(1)+" -i temp.dll processed.wav")
                    data=''
                    def generate():
                        with open("processed.wav", "rb") as fwav:
                            data = fwav.read(1024)
                            while data:
                                yield data
                                data = fwav.read(1024)
                        os.system("del processed.wav")
                    return Response(generate(), mimetype="audio/x-wav")
            elif path_par[0]=="-s":
                command=''
                audiodata=create_silence(100)
                count=len(path_par)
                trig=0
                for i in range(count-1):
                    cw_count=0
                    sw_count=0
                    try:
                        val=dataj[path_par[i+1]][0]['info']
                    except:
                        print("Twee is not able to tell this right now. Sorry for inconvenience.")
                    #os.system("curl "+saddress+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                    audiodata=mix(audiodata,AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2))
                    '''
                    if trig:
                        if cw_count:
                            audiodata=crossfader(audiodata,AudioSegment.from_file("temp.dll", format="raw", frame_rate=44100, channels=1, sample_width=2),10)
                            cw_count=0
                        elif sw_count:
                            audiodata=crossfader(audiodata,AudioSegment.from_file("temp.dll", format="raw", frame_rate=44100, channels=1, sample_width=2),30)
                            sw_count=0
                        else:
                            audiodata=crossfader(audiodata,AudioSegment.from_file("temp.dll", format="raw", frame_rate=44100, channels=1, sample_width=2),0)
                    else:
                        audiodata=mix(audiodata,AudioSegment.from_file("temp.dll", format="raw", frame_rate=44100, channels=1, sample_width=2))

                    for cw in content_words:
                        if path_par[i+1] in cw:
                            cw_count=1
                            filters=content_word_effect.split(",")
                            for fil in filters:
                                if fil.split("=")[0]=="loud":
                                    audiodata=applygain(audiodata,float(fil.split("=")[1]))
                                elif fil.split("=")[0]=="slow":
                                    print("=============////============")
                                    audiodata=speed(audiodata,float(fil.split("=")[1]))


                    for sw in structure_words:
                        if path_par[i+1] in sw:
                            sw_count=1
                            filters=content_word_effect.split(",")
                            for fil in filters:
                                if fil.split("=")[0]=="loud":
                                    audiodata=applygain(audiodata,float(fil.split("=")[1]))
                                elif fil.split("=")[0]=="slow":
                                    print("---------------")
                                    audiodata=speed(audiodata,float(fil.split("=")[1]))
                                elif fil.split("=")[0]=="fast":
                                    print("=======================")
                                    audiodata=speed(audiodata,float(fil.split("=")[1]))
                    trig=1
                    '''
                    command+=path_par[i+1]+" "
                #print(command)
                with open("temp.dll", "wb") as fwav:
                    fwav.write(audiodata.raw_data)
                os.system("echo y | ffmpeg -nostats -loglevel 0 -f s16le -ar 44.1k -ac "+str(1)+" -i temp.dll processed.wav")
                data=''
                def generate():
                    with open("processed.wav", "rb") as fwav:
                        data = fwav.read(1024)
                        while data:
                            yield data
                            data = fwav.read(1024)
                        #os.system("del /f processed.wav")
                return Response(generate(), mimetype="audio/x-wav")

        if __name__ == "__main__":
            app.run(host=str(sys.argv[sys_offset+2]), port=int(sys.argv[sys_offset+3]), debug=True,threaded=True)


    if sys.argv[sys_offset+1]=="-export":
        command=''
        val=-1
        audiodata=create_silence(100)
        count=len(sys.argv)
        for i in range(count-2-sys_offset):
            try:
                val=dataj[sys.argv[sys_offset+i+2]][0]['info']
            except:
                print("Twee is not able to tell this right now. Sorry for inconvenience.")
            #os.system("curl "+data+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
            audio=AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2)#.set_frame_rate(90000)
            audiodata=mix(audiodata,audio)
        #play(audiodata)
        #print(audiodata.frame_rate)
        #os.chdir(realpath)
        audiodata.export("test.wav", format="wav", tags={'artist': 'Hera Hassan', 'album': 'N/A', 'comments': 'This is created by Twee'})
        #os.chdir(os.path.dirname(new_module.__file__))

    if sys.argv[sys_offset+1]=="-s":
        start = time.time()
        command=''
        val=-1
        count=len(sys.argv)
        for i in range(count-2-sys_offset):
            try:
                val=dataj[sys.argv[sys_offset+i+2]][0]['info']
            except:
                print("Twee is not able to tell this right now. Sorry for inconvenience.")
            #audio=AudioSegment.from_file("database\\voices\\"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2)
            #os.system("curl "+data+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
            audio=fslice(AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2),90)
            audio=bslice(audio,90)
            play(audio)
            #print(audio.max)
            command+=sys.argv[sys_offset+i+2]+" "
        end = time. time()
        #print(end - start)
        #print(command)
    elif sys.argv[sys_offset+1]=="-i":
        if sys.argv[sys_offset+2]=="-s":
            command=''
            val=-1
            audio=create_silence(100)
            count=len(sys.argv)
            for i in range(count-3-sys_offset):
                try:
                    val=dataj[sys.argv[sys_offset+i+3]][0]['info']
                    #print(emotionj[sys.argv[i+3]][0]['emotions'])
                    #os.system("curl "+data+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                    audiodata=AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2)
                except:
                    print("Twee is not able to tell this right now. Sorry for inconvenience.")
                if emotions.index(emotionj[sys.argv[sys_offset+i+3]][0]['emotions'])==0:
                    #print(emotions[0])
                    emotionsd=emotion_effect[0]
                    emotions_fil=emotionsd.split(",")
                    for fil in emotions_fil:
                        if fil=="loud":
                            audiodata=applygain(audiodata,2.0)
                        elif fil=="cool":
                            audiodata=removegain(audiodata,0.5)
                        elif fil=="fast":
                            audiodata=speed(audiodata,1.5)
                        elif fil=="slow":
                            audiodata=speed(audiodata,0.5)
                        elif fil=="louder":
                            audiodata=applygain(audiodata,4.0)
                        elif fil=="loudest":
                            audiodata=applygain(audiodata,10.0)
                        elif fil=="nothing":
                            audiodata=audiodata

                elif emotions.index(emotionj[sys.argv[sys_offset+i+3]][0]['emotions'])==1:
                    #print(emotions[1])
                    emotionsd=emotion_effect[1]
                    emotions_fil=emotionsd.split(",")
                    for fil in emotions_fil:
                        if fil=="loud":
                            audiodata=applygain(audiodata,2.0)
                        elif fil=="cool":
                            audiodata=removegain(audiodata,0.5)
                        elif fil=="fast":
                            audiodata=speed(audiodata,1.5)
                        elif fil=="slow":
                            audiodata=speed(audiodata,0.5)
                        elif fil=="louder":
                            audiodata=applygain(audiodata,4.0)
                        elif fil=="loudest":
                            audiodata=applygain(audiodata,10.0)
                        elif fil=="nothing":
                            audiodata=audiodata

                elif emotions.index(emotionj[sys.argv[sys_offset+i+3]][0]['emotions'])==2:
                    #print(emotions[2])
                    emotionsd=emotion_effect[2]
                    emotions_fil=emotionsd.split(",")
                    for fil in emotions_fil:
                        if fil=="loud":
                            audiodata=applygain(audiodata,2.0)
                        elif fil=="cool":
                            audiodata=removegain(audiodata,0.5)
                        elif fil=="fast":
                            audiodata=speed(audiodata,1.5)
                        elif fil=="slow":
                            audiodata=speed(audiodata,0.5)
                        elif fil=="louder":
                            audiodata=applygain(audiodata,4.0)
                        elif fil=="loudest":
                            audiodata=applygain(audiodata,10.0)
                        elif fil=="nothing":
                            audiodata=audiodata

                elif emotions.index(emotionj[sys.argv[sys_offset+i+3]][0]['emotions'])==3:
                    #print(emotions[3])
                    emotionsd=emotion_effect[3]
                    emotions_fil=emotionsd.split(",")
                    for fil in emotions_fil:
                        if fil=="loud":
                            audiodata=applygain(audiodata,2.0)
                        elif fil=="cool":
                            audiodata=removegain(audiodata,0.5)
                        elif fil=="fast":
                            audiodata=speed(audiodata,1.5)
                        elif fil=="slow":
                            audiodata=speed(audiodata,0.5)
                        elif fil=="louder":
                            audiodata=applygain(audiodata,4.0)
                        elif fil=="loudest":
                            audiodata=applygain(audiodata,10.0)
                        elif fil=="nothing":
                            audiodata=audiodata

                elif emotions.index(emotionj[sys.argv[sys_offset+i+3]][0]['emotions'])==4:
                    #print(emotions[4])
                    emotionsd=emotion_effect[4]
                    emotions_fil=emotionsd.split(",")
                    for fil in emotions_fil:
                        if fil=="loud":
                            audiodata=applygain(audiodata,2.0)
                        elif fil=="cool":
                            audiodata=removegain(audiodata,0.5)
                        elif fil=="fast":
                            audiodata=speed(audiodata,1.5)
                        elif fil=="slow":
                            audiodata=speed(audiodata,0.5)
                        elif fil=="louder":
                            audiodata=applygain(audiodata,4.0)
                        elif fil=="loudest":
                            audiodata=applygain(audiodata,10.0)
                        elif fil=="nothing":
                            audiodata=audiodata

                elif emotions.index(emotionj[sys.argv[sys_offset+i+3]][0]['emotions'])==5:
                    #print(emotions[5])
                    emotionsd=emotion_effect[5]
                    emotions_fil=emotionsd.split(",")
                    for fil in emotions_fil:
                        if fil=="loud":
                            audiodata=applygain(audiodata,2.0)
                        elif fil=="cool":
                            audiodata=removegain(audiodata,0.5)
                        elif fil=="fast":
                            audiodata=speed(audiodata,1.5)
                        elif fil=="slow":
                            audiodata=speed(audiodata,0.5)
                        elif fil=="louder":
                            audiodata=applygain(audiodata,4.0)
                        elif fil=="loudest":
                            audiodata=applygain(audiodata,10.0)
                        elif fil=="nothing":
                            audiodata=audiodata

                elif emotions.index(emotionj[sys.argv[sys_offset+i+3]][0]['emotions'])==6:
                    #print(emotions[6])
                    emotionsd=emotion_effect[6]
                    emotions_fil=emotionsd.split(",")
                    for fil in emotions_fil:
                        if fil=="loud":
                            audiodata=applygain(audiodata,2.0)
                        elif fil=="cool":
                            audiodata=removegain(audiodata,0.5)
                        elif fil=="fast":
                            audiodata=speed(audiodata,1.5)
                        elif fil=="slow":
                            audiodata=speed(audiodata,0.5)
                        elif fil=="louder":
                            audiodata=applygain(audiodata,4.0)
                        elif fil=="loudest":
                            audiodata=applygain(audiodata,10.0)
                        elif fil=="nothing":
                            audiodata=audiodata

                elif emotions.index(emotionj[sys.argv[sys_offset+i+3]][0]['emotions'])==7:
                    #print(emotions[7])
                    emotionsd=emotion_effect[7]
                    emotions_fil=emotionsd.split(",")
                    for fil in emotions_fil:
                        if fil=="loud":
                            audiodata=applygain(audiodata,2.0)
                        elif fil=="cool":
                            audiodata=removegain(audiodata,0.5)
                        elif fil=="fast":
                            audiodata=speed(audiodata,1.5)
                        elif fil=="slow":
                            audiodata=speed(audiodata,0.5)
                        elif fil=="louder":
                            audiodata=applygain(audiodata,4.0)
                        elif fil=="loudest":
                            audiodata=applygain(audiodata,10.0)
                        elif fil=="nothing":
                            audiodata=audiodata

                elif emotions.index(emotionj[sys.argv[sys_offset+i+3]][0]['emotions'])==8:
                    #print(emotions[8])
                    emotionsd=emotion_effect[8]
                    emotions_fil=emotionsd.split(",")
                    for fil in emotions_fil:
                        if fil=="loud":
                            audiodata=applygain(audiodata,2.0)
                        elif fil=="cool":
                            audiodata=removegain(audiodata,0.5)
                        elif fil=="fast":
                            audiodata=speed(audiodata,1.5)
                        elif fil=="slow":
                            audiodata=speed(audiodata,0.5)
                        elif fil=="louder":
                            audiodata=applygain(audiodata,4.0)
                        elif fil=="loudest":
                            audiodata=applygain(audiodata,10.0)
                        elif fil=="nothing":
                            audiodata=audiodata

                elif emotions.index(emotionj[sys.argv[sys_offset+i+3]][0]['emotions'])==9:
                    #print(emotions[9])
                    emotionsd=emotion_effect[9]
                    emotions_fil=emotionsd.split(",")
                    for fil in emotions_fil:
                        if fil=="loud":
                            audiodata=applygain(audiodata,2.0)
                        elif fil=="cool":
                            audiodata=removegain(audiodata,0.5)
                        elif fil=="fast":
                            audiodata=speed(audiodata,1.5)
                        elif fil=="slow":
                            audiodata=speed(audiodata,0.5)
                        elif fil=="louder":
                            audiodata=applygain(audiodata,4.0)
                        elif fil=="loudest":
                            audiodata=applygain(audiodata,10.0)
                        elif fil=="nothing":
                            audiodata=audiodata
                elif emotions.index(emotionj[sys.argv[sys_offset+i+3]][0]['emotions'])==10:
                    #print(emotions[10])
                    emotionsd=emotion_effect[10]
                    emotions_fil=emotionsd.split(",")
                    for fil in emotions_fil:
                        if fil=="loud":
                            audiodata=applygain(audiodata,2.0)
                        elif fil=="cool":
                            audiodata=removegain(audiodata,0.5)
                        elif fil=="fast":
                            audiodata=speed(audiodata,1.5)
                        elif fil=="slow":
                            audiodata=speed(audiodata,0.5)
                        elif fil=="louder":
                            audiodata=applygain(audiodata,4.0)
                        elif fil=="loudest":
                            audiodata=applygain(audiodata,10.0)
                        elif fil=="nothing":
                            audiodata=audiodata
                audio=mix(audio,audiodata)
                command+=sys.argv[sys_offset+i+3]+" "
            play(audio)
            #print(command)
    elif sys.argv[sys_offset+1]=="-c":
        if sys.argv[sys_offset+2]=="-s":
            command=''
            val=-1
            count=len(sys.argv)
            for i in range(count-3-sys_offset):
                try:
                    word=sys.argv[sys_offset+i+3].split("~")[1]
                    if word!="-":
                        val=dataj[word][0]['info']
                except:
                    print("Twee is not able to tell this right now. Sorry for inconvenience.")
                notation=sys.argv[sys_offset+i+3].split("~")[0]
                if notation=="l":
                    #os.system("curl "+data+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                    audio=applygain(AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2),2.0)
                elif notation=="c":
                    #os.system("curl "+data+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                    audio=removegain(AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2),0.5)
                elif notation=="f":
                    #os.system("curl "+data+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                    audio=speed(AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2),1.5)
                elif notation=="s":
                    #os.system("curl "+data+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                    #print('s')
                    audio=speed(AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2),0.5)
                elif notation=="n":
                    #os.system("curl "+data+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                    #print('n')
                    audio=AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2)
                elif notation=="left":
                    #os.system("curl "+data+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                    #left~do you,right~like this
                    word1=AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2)
                    blank=create_silence(duration(word1))
                    '''
                    print(duration(word1))
                    print(duration(blank))
                    blank=word2
                    blank=blank.set_frame_rate(word2.frame_rate)
                    blank.set_sample_width(word2.sample_width)
                    samples=word2.get_array_of_samples()
                    blank=blank._spawn(samples[:len(word1.get_array_of_samples())])
                    '''
                    audio=create_silence(50)
                    audio=audio.set_channels(2)
                    audio=create_stereo(word1,blank)
                elif notation=="right":
                    #os.system("curl "+data+"/database/voices/"+str(val)+".dll --output temp.dll --silent")
                    #left~do you,right~like this
                    word1=AudioSegment.from_file("database/voices/"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2)
                    blank=create_silence(duration(word1))
                    '''
                    print(duration(word1))
                    print(duration(blank))
                    blank=word2
                    blank=blank.set_frame_rate(word2.frame_rate)
                    blank.set_sample_width(word2.sample_width)
                    samples=word2.get_array_of_samples()
                    blank=blank._spawn(samples[:len(word1.get_array_of_samples())])
                    '''
                    audio=create_silence(50)
                    audio=audio.set_channels(2)
                    audio=create_stereo(blank,word1)
                elif word=="-":
                    audio=create_silence(int(notation))
                #audio=AudioSegment.from_file("database\\voices\\"+str(val)+".dll", format="raw", frame_rate=44100, channels=1, sample_width=2)
                play(audio)
                command+=sys.argv[sys_offset+i+3]+" "
            #print(command)


'''
 data = json.loads(jsonData)
    if 'to' not in data:
        
    if 'to' not in data['to']:
        raise ValueError("No target in given data")
'''
'''
channel_count = sound.channels
frames_per_second = sound.frame_rate
bytes_per_frame = sound.frame_width
peak_amplitude = sound.max
raw_audio_data = sound.raw_data
number_of_frames_in_sound = sound.frame_count()
fade_quieter_beteen_2_and_3_seconds = sound1.fade(to_gain=-3.5, start=2000, end=3000)
AudioSegment(…).reverse()
AudioSegment(…).set_frame_rate()
AudioSegment(…).set_channels()
#left channel at index 0 and the right channel at index 1.
AudioSegment(…).split_to_mono()
AudioSegment(…).get_array_of_samples()
#export / save pitch changed sound
hipitch_sound.export("out.wav", format="wav")
play(hipitch_sound)
first_10_seconds = song[:ten_seconds]
last_5_seconds = song[-5000:]
backwards = song.reverse()
# 1.5 second crossfade
with_style = beginning.append(end, crossfade=1500)
# 2 sec fade in, 3 sec fade out
awesome = do_it_over.fade_in(2000).fade_out(3000)
awesome.export("mashup.mp3", format="mp3", tags={'artist': 'Various artists', 'album': 'Best of 2011', 'comments': 'This album is awesome!'})
song = AudioSegment.from_wav("never_gonna_give_you_up.wav")
'''
