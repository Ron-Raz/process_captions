import sys
import subprocess
import urllib.request
from os.path import exists
from KalturaClient import *
from KalturaClient.Plugins.Core import *
from KalturaClient.Plugins.Caption import *

def getConf(paramsArray):
    ret= {}
    for arg in paramsArray:
        nameValuePair= arg.split('=')
        if len(nameValuePair)==2:
            ret[nameValuePair[0].upper()]= nameValuePair[1]
    return ret

def kStart(conf):
    ret={'CLIENT':None,'FILTER':None,'FROMCAT':None,'TOCAT':None}
    config = KalturaConfiguration()
    config.serviceUrl = conf['SERVICEURL']
    ret['CLIENT'] = KalturaClient(config)
    ks = ret['CLIENT'].session.start(conf['ADMINSECRET'], conf['USERID'], KalturaSessionType.USER, conf['PID'], 86400, '')
    ret['CLIENT'].setKs(ks)
    ret['FILTER'] = KalturaMediaEntryFilter()
    ret['FILTER'].categoriesIdsMatchAnd = conf['FROMCAT']
    ret['FROMCAT']= conf['FROMCAT']
    ret['TOCAT']= conf['TOCAT']
    return ret

def processCaptions(kInst,entryId,captionsFileName):
    print('uploading',captionsFileName)
    # First you'll need to use uploadToken.add to create a new upload token.
    upload_token = KalturaUploadToken()
    result = kInst['CLIENT'].uploadToken.add(upload_token)
    # Now we'll use the newly created Upload Token to upload the SRT
    upload_token_id = result.id
    file_data = open(captionsFileName, 'rb')
    resume = False
    final_chunk = True
    resume_at = -1
    result = kInst['CLIENT'].uploadToken.upload(upload_token_id, file_data, resume, final_chunk, resume_at)
    # Next you'll need to create a Caption Asset, which describes the format, language, and label of your captions
    caption_asset = KalturaCaptionAsset()
    caption_asset.language = "English"
    caption_asset.format = KalturaCaptionType.SRT
    caption_asset.label = "Ron's English"
    caption_asset.isDefault = KalturaNullableBoolean.TRUE_VALUE
    result = kInst['CLIENT'].caption.captionAsset.add(entryId, caption_asset)
    # Now that you've created a new Caption Asset and uploaded your caption file, 
    # you need to associate them with each other using the captionAsset.setContent method.
    # Set the id parameter to the entryId of a media item, 
    # and the contentResource[token] parameter to the Upload Token's ID
    id = result.id
    content_resource = KalturaUploadedFileTokenResource()
    content_resource.token = upload_token_id
    result = kInst['CLIENT'].caption.captionAsset.setContent(id, content_resource)
    # remove entry from category/channel
    result = kInst['CLIENT'].categoryEntry.delete(entryId, kInst['FROMCAT'])
    # add entry to category/channel
    category_entry = KalturaCategoryEntry()
    category_entry.categoryId = kInst['TOCAT']
    category_entry.entryId = entryId
    result = kInst['CLIENT'].categoryEntry.add(category_entry)

def extractAudioFile(downloadUrl,videoFileName,audioFileName):
    try:
        print('getting video file',downloadUrl,videoFileName)
        urllib.request.urlretrieve(downloadUrl, videoFileName)
        print('extracting audio file',audioFileName)
        subprocess.run(['ffmpeg','-i',videoFileName,'-vn','-acodec','copy',audioFileName])
    except:
        print('Skipping extractAudioFile (',downloadUrl,',',videoFileName,',',audioFileName,')')

def processFiles(kInst):
    ret= None;
    res = kInst['CLIENT'].media.list(kInst['FILTER'], KalturaFilterPager())
    for entry in res.getObjects():
        audioFileName= entry.id+'.aac'
        videoFileName= entry.id+'.mp4'
        captionsFileName= entry.id+'.srt'
        if exists(captionsFileName):
            # upload the captions, and move the entry to an output channel
            processCaptions(kInst,entry.id,captionsFileName)
        else:
            if not exists(audioFileName) and entry.downloadUrl:
                extractAudioFile(entry.downloadUrl,videoFileName,audioFileName)
            else:
                print('skipping',entry.id)
            # break

config= getConf(sys.argv)
kInstance= kStart(config)
processFiles(kInstance)