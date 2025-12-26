# kakao_business_api.py

import requests
import json
from typing import Dict, Any, List

class KakaoBusinessAPI:
    """Manages KakaoTalk Business API integration for sending messages."""
    
    def __init__(self, app_key: str, client_id: str, client_secret: str, callback_url: str):
        self.app_key = app_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.callback_url = callback_url
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = 0
        self.auth_url = "https://kauth.kakao.com/oauth/token"
        self.message_send_url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
        
    def _get_headers(self) -> Dict[str, str]:
        """Helper to get authorization headers."""
        if not self.access_token or self.token_expires_at < time.time():
            self.refresh_access_token()
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
        }

    def get_authorization_code_url(self) -> str:
        """Generates the URL for user authorization."""
        return (
            f"https://kauth.kakao.com/oauth/authorize?client_id={self.client_id}"
            f"&redirect_uri={self.callback_url}&response_type=code"
        )

    def get_access_token(self, code: str) -> bool:
        """Exchanges authorization code for access and refresh tokens."""
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.callback_url,
            "code": code
        }
        
        response = requests.post(self.auth_url, data=data)
        token_info = response.json()
        
        if "access_token" in token_info:
            self.access_token = token_info["access_token"]
            self.refresh_token = token_info.get("refresh_token")
            self.token_expires_at = time.time() + token_info["expires_in"]
            print("Access token obtained successfully.")
            return True
        else:
            print(f"Failed to get access token: {token_info.get("error_description", token_info)}")
            return False

    def refresh_access_token(self) -> bool:
        """Refreshes the access token using the refresh token."""
        if not self.refresh_token:
            print("No refresh token available.")
            return False
            
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }
        
        response = requests.post(self.auth_url, data=data)
        token_info = response.json()
        
        if "access_token" in token_info:
            self.access_token = token_info["access_token"]
            self.token_expires_at = time.time() + token_info["expires_in"]
            if "refresh_token" in token_info: # Refresh token can also be refreshed
                self.refresh_token = token_info["refresh_token"]
            print("Access token refreshed successfully.")
            return True
        else:
            print(f"Failed to refresh access token: {token_info.get("error_description", token_info)}")
            return False

    def send_text_message(self, receiver_uuid: str, text: str) -> Dict[str, Any]:
        """Sends a text message to a specific user (receiver_uuid)."""
        template_object = {
            "object_type": "text",
            "text": text,
            "link": {
                "web_url": "https://developers.kakao.com",
                "mobile_web_url": "https://developers.kakao.com"
            },
            "button_title": "자세히 보기"
        }
        
        data = {
            "template_object": json.dumps(template_object)
        }
        
        headers = self._get_headers()
        response = requests.post(self.message_send_url, headers=headers, data=data)
        return response.json()

    def send_custom_message(self, receiver_uuid: str, template_id: int, args: Dict[str, str]) -> Dict[str, Any]:
        """Sends a custom message using a predefined template."""
        data = {
            "template_id": template_id,
            "args": json.dumps(args)
        }
        
        headers = self._get_headers()
        response = requests.post(self.message_send_url, headers=headers, data=data)
        return response.json()

    def send_feed_message(self, receiver_uuid: str, title: str, description: str, image_url: str, link_url: str) -> Dict[str, Any]:
        """Sends a feed type message."""
        template_object = {
            "object_type": "feed",
            "content": {
                "title": title,
                "description": description,
                "image_url": image_url,
                "link": {
                    "web_url": link_url,
                    "mobile_web_url": link_url
                }
            },
            "buttons": [
                {
                    "title": "웹으로 보기",
                    "link": {
                        "web_url": link_url,
                        "mobile_web_url": link_url
                    }
                }
            ]
        }
        
        data = {
            "template_object": json.dumps(template_object)
        }
        
        headers = self._get_headers()
        response = requests.post(self.message_send_url, headers=headers, data=data)
        return response.json()

# Example usage (replace with your actual credentials and logic)
if __name__ == "__main__":
    # These would typically come from environment variables or a secure config file
    KAKAO_APP_KEY = "YOUR_KAKAO_APP_KEY"
    KAKAO_CLIENT_ID = "YOUR_KAKAO_CLIENT_ID"
    KAKAO_CLIENT_SECRET = "YOUR_KAKAO_CLIENT_SECRET"
    KAKAO_CALLBACK_URL = "http://localhost:5000/kakao/oauth"
    
    kakao_api = KakaoBusinessAPI(
        app_key=KAKAO_APP_KEY,
        client_id=KAKAO_CLIENT_ID,
        client_secret=KAKAO_CLIENT_SECRET,
        callback_url=KAKAO_CALLBACK_URL
    )
    
    # Step 1: Get authorization code (manual step, user needs to open this URL in browser)
    print(f"Please open this URL in your browser to authorize: {kakao_api.get_authorization_code_url()}")
    
    # After user authorizes, Kakao redirects to KAKAO_CALLBACK_URL with a 'code' parameter
    # You would then capture this code in your Flask/Django app and pass it to get_access_token
    # For demonstration, let's assume we got a code:
    # auth_code = input("Enter the authorization code from the redirect URL: ")
    # if kakao_api.get_access_token(auth_code):
    #     print("Successfully authenticated with Kakao.")
        
    #     # Example: Send a text message (you need a valid receiver_uuid)
    #     # receiver_uuid = "USER_KAKAO_UUID"
    #     # message_response = kakao_api.send_text_message(receiver_uuid, "안녕하세요! SSTDMS에서 알림을 보냅니다.")
    #     # print(f"Message send response: {message_response}")
        
    #     # Example: Send a feed message
    #     # feed_response = kakao_api.send_feed_message(
    #     #     receiver_uuid,
    #     #     "새로운 프로젝트 알림",
    #     #     "프로젝트 'ABC'가 생성되었습니다. 지금 확인하세요!",
    #     #     "https://example.com/project_image.jpg",
    #     #     "https://example.com/project/abc"
    #     # )
    #     # print(f"Feed message send response: {feed_response}")
    # else:
    #     print("Kakao authentication failed.")

import time # Added for time.time() in _get_headers


