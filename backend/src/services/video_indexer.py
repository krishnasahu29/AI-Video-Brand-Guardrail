'''
Connector between python code and Azure video indexer
'''

from time import time
from uuid import uuid4
from PIL.Image import logger
import os, time, requests, logging, yt_dlp
from azure.identity import DefaultAzureCredential

logger = logging.getLogger("video_indexer")

class VideoIndexerService:

    def __init__(self):
        self.account_id = os.getenv("AZURE_VI_ACCOUNT_ID")
        self.location = os.getenv("AZURE_VI_LOCATION")
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group = os.getenv("AZURE_RESOURCE_GROUP")
        self.vi_name = os.getenv("AZURE_VI_NAME", "multi-agentic-ai-indexer-stack")
        self.credentials = DefaultAzureCredential()

    def get_access_token(self):
        '''
        Generates an ARM token
        '''
        try:
            token_object = self.credentials.get_token(
                "https://management.azure.com/.default"
            )

            return token_object.token

        except Exception as e:
            logger.error(f"Error fetching token: {e}")
            raise

    def get_account_token(self, arm_access_token):
        '''
        Exchanges the ARM token for Video Indexer account team
        '''
        url = (
            f"https://management.azure.com/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{self.resource_group}"
            f"/providers/Microsoft.VideoIndexer/accounts/{self.vi_name}"
            f"/generateAccessToken?api-version=2024-01-01"
        )

        headers = {"Authorization": f"Bearer {arm_access_token}"}
        payload = {"permissionType": "Contributor", "scope": "Account"}
        
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Failed to get VI account token : {response.text}")

        return response.json().get("accessToken")

    # Function to download the youtube video
    def download_youtube_video(self, youtube_url, output_path='temp_video.mp4'):
        """
        Downloads a youtube video to a local file
        """
        
        logger.info(f"Downloading the youtube video : {youtube_url}")
        
        ydl_opts = {
            "format": 'best',
            "outtmpl": output_path, # output template
            "no_warnings": False,
            "quiet": True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            logger.info(f"Video downloaded successfully to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error downloading youtube video : {e}")
            raise

    # Funtion to upload video the Azure Video Indexer
    def upload_video(self, video_path, video_name):
        """
        Uploads the video toAzure Video Indexer
        """

        arm_token = self.get_access_token()
        vi_token = self.get_account_token(arm_token)

        api_url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos"
        
        params = {
            "accesstoken": vi_token,
            "name": video_name,
            "privacy": "Private",
            "indexingPreset": "Default"
        }

        logger.info(f"Uploading file {video_path} to Azure Video Indexer")


        # Open the video in binary and stream it on Azure
        with open(video_path, "rb") as video_file:
            files =  {'file': (video_path, video_file)}
            response = requests.post(api_url, params=params, files=files)
        
        if response.status_code != 200:
            raise Exception(f"Failed to upload video: {response.text}")
        
        logger.info(f"Video uploaded successfully")
        return response.json().get("id")

    def wait_for_processing(self, video_id):

        logger.info(f"Waiting for the video: {video_id} to process....")
        while True:
            arm_token = self.get_access_token()
            vi_token = self.get_account_token(arm_token)

            video_url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos/{video_id}/Index"
            params = {"accesstoken": vi_token}
            response = requests.get(video_url, params=params)
            if response.status_code != 200:
                logger.error(f"Error fetching video status: HTTP {response.status_code} - {response.text}")
            data = response.json()

            state = data.get("state")

            if state == "Processed":
                return data

            elif state == "Failed":
                raise Exception("Video indexing failed in Azure")

            elif state == "Quarantined":
                raise Exception("Video quarantined due to content policy violations")

            logger.info(f"Status: {state} .... wait for 30 seconds")
            time.sleep(30)
    
    def extract_data(self, vi_json):
        '''
        Extracts data from json into state format (ocr, transcript)
        '''

        transcript_lines = []
        for v in vi_json.get("videos", []):
            for insights in v.get("insights", []).get("transcript", []):
                transcript_lines.append(insights.get("text"))

        ocr_lines = []
        for v in vi_json.get("videos", []):
            for insights in v.get("insights", []).get("ocr", []):
                ocr_lines.append(insights.get("text"))

        return {
            "transcript": " ".join(transcript_lines),
            "ocr_text": ocr_lines,
            "video_metadata": {
                "duration": vi_json.get("summarizedInsights", {}).get("duration"),
                "platform": "youtube"
            }
        }

        