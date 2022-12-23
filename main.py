from flask import Flask, request, render_template
from deezer import Deezer
from deemix import *
from deemix.types.Track import Track
from deemix.types.DownloadObjects import Single
from deemix.utils import formatListener
from deemix.decryption import streamTrack
from deemix.downloader import Downloader, formatsName
from deemix.settings import load as loadSettings
from pathlib import Path
import deemix.utils.localpaths as localpaths

from dotenv import load_dotenv
import os

load_dotenv()

arl = os.environ.get("arl")

class LogListener:
    @classmethod
    def send(cls, key, value=None):
        logString = formatListener(key, value)
        if logString: print(logString)


def download(link):
    dz = Deezer()
    dz.login_via_arl(arl)
    bitrate = 9
    listener = LogListener()
    downloadObject = generateDownloadObject(dz, link, bitrate, None, listener)
    configFolder = localpaths.getConfigFolder()

    settings = loadSettings(configFolder)
    # dl = Downloader(dz, downloadObject, settings)

    # if isinstance(downloadObject, Single):
    #     track = dl.downloadWrapper({
    #         'trackAPI': downloadObject.single.get('trackAPI'),
    #         'albumAPI': downloadObject.single.get('albumAPI')
    #     }).get('single)
    # print(downloadObject.toDict().get('single'))
    track = Track().parseData(
                    dz=dz,
                    track_id=downloadObject.toDict().get('single').get('trackAPI')['id'],
                    trackAPI=downloadObject.toDict().get('single').get('trackAPI'),
                    albumAPI=downloadObject.toDict().get('single').get('albumAPI'),
                    playlistAPI=downloadObject.toDict().get('single').get("playlistAPI")
                )
    print(track.urls)
    track.downloadURL = track.urls[formatsName['FLAC']]
    stream = None
    yield streamTrack(stream, track, 0, downloadObject, listener)


app = Flask("__name__")

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/dl", methods=["POST"])
def DL():
    uri = request.form["uri"]
    return app.response_class(download(uri), mimetype="application/octet-stream")