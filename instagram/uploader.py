import logging
import json
import time
import os

# Fix for instagrapi moviepy v2 incompatibility
import moviepy
import moviepy.editor
moviepy.VideoFileClip = moviepy.editor.VideoFileClip

from instagrapi import Client

from core.config import IG_SESSION

logger = logging.getLogger(__name__)

class InstagramUploader:
    def __init__(self):
        self.client = Client()
        
    def login(self):
        try:
            sessionid = IG_SESSION
            if not sessionid:
                logger.warning("IG_SESSION secret not found in environment. Cannot upload.")
                return False
                
            self.client.login_by_sessionid(sessionid)
            logger.info("Successfully logged in to Instagram via sessionid!")
            return True
        except Exception as e:
            logger.error(f"Instagram login failed: {e}")
            return False
            
    def upload_reel(self, video_path: str, caption: str, thumbnail_path: str = None) -> bool:
        if not os.path.exists(video_path):
            logger.error(f"Video not found: {video_path}")
            return False
            
        try:
            logger.info(f"Starting upload for {video_path}")
            # instagrapi expects an absolute or clean relative path, wait a bit before upload
            time.sleep(2) 
            
            media = self.client.clip_upload(
                path=video_path,
                caption=caption,
                thumbnail=thumbnail_path if thumbnail_path and os.path.exists(thumbnail_path) else None
            )
            
            logger.info(f"Successfully uploaded reel! Media ID: {media.pk}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload reel: {e}")
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uploader = InstagramUploader()
    if uploader.login():
        caption = "జీవిత పాఠాలు - Motivation ✨\n\n#telugu #motivation #telugureels #life #inspiration"
        video = "../output/final_reel.mp4"
        thumb = "../output/final_reel_thumb.jpg"
        
        uploader.upload_reel(video, caption, thumb)
