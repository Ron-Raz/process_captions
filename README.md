# process_captions
Custom workflow for processing captions in a Kaltura channel

# Usage example:
python3 processCaptions.py PID=<pid> ADMINSECRET=<secret> USERID=ron.raz@kaltura.com SERVICEURL=https://www.kaltura.com/ FROMCAT=159481552 TOCAT=282451502

# Flow:
Loop on entry IDs in category/channel FROMCAT:

  if an entryId.srt exists:
  
    upload the captions file to the entry
    
    delete entry from FROMCAT
    
    add entry to TOCAT
    
  else:
  
    download the video for the entry
    
    extract the audio from it and save it
    
