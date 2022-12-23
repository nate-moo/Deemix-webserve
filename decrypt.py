from deemix.utils.crypto import _md5, _ecbCrypt, _ecbDecrypt, generateBlowfishKey, decryptChunk
from deemix.utils import USER_AGENT_HEADER
from deemix.types.DownloadObjects import Single
from deemix.decryption import *

def streamTrack(outputStream, track, start=0, downloadObject=None, listener=None):
    if downloadObject and downloadObject.isCanceled: raise DownloadCanceled
    headers= {'User-Agent': USER_AGENT_HEADER}
    chunkLength = start
    isCryptedStream = "/mobile/" in track.downloadURL or "/media/" in track.downloadURL

    itemData = {
        'id': track.id,
        'title': track.title,
        'artist': track.mainArtist.name
    }

    try:
        with get(track.downloadURL, headers=headers, stream=True, timeout=10) as request:
            request.raise_for_status()
            if isCryptedStream:
                blowfish_key = generateBlowfishKey(str(track.id))

            complete = int(request.headers["Content-Length"])
            if complete == 0: raise DownloadEmpty
            if start != 0:
                responseRange = request.headers["Content-Range"]

            isStart = True
            for chunk in request.iter_content(2048 * 3):
                if isCryptedStream:
                    if len(chunk) >= 2048:
                        chunk = decryptChunk(blowfish_key, chunk[0:2048]) + chunk[2048:]

                if isStart and chunk[0] == 0 and chunk[4:8].decode('utf-8') != "ftyp":
                    for i, byte in enumerate(chunk):
                        if byte != 0: break
                    chunk = chunk[i:]
                isStart = False

                chunkLength += len(chunk)

                if downloadObject:
                    if isinstance(downloadObject, Single):
                        chunkProgres = (chunkLength / (complete + start)) * 100
                        downloadObject.progressNext = chunkProgres
                    else:
                        chunkProgres = (len(chunk) / (complete + start)) / downloadObject.size * 100
                        downloadObject.progressNext += chunkProgres\
                
                yield outputStream

    except (SSLError, u3SSLError):
        streamTrack(outputStream, track, chunkLength, downloadObject, listener)
    except (RequestsConnectionError, ReadTimeout, ChunkedEncodingError):
        sleep(2)
        streamTrack(outputStream, track, start, downloadObject, listener)