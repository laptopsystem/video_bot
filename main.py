import os
import requests
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import instaloader

# Global Configurations
USERNAME = "devrajoriya"
PASSWORD = "Sym4nt3c!"
TOKEN_API_URL = "https://api.socialverseapp.com/user/token"
BASE_API_URL = "https://api.socialverseapp.com/posts"
VIDEO_DIR = "videos"


# Function to fetch the Flic Token
def get_flic_token():
    try:
        response = requests.get(f"{TOKEN_API_URL}?username={USERNAME}&password={PASSWORD}")
        if response.status_code == 200:
            token = response.json().get("token")
            if token:
                print("Flic Token fetched successfully.")
                return token
            else:
                print("Token not found in response.")
        else:
            print(f"Failed to fetch token: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error fetching token: {e}")
    return None


# Downloader Logic for Instagram
def download_instagram_video(post_url, output_dir="videos"):
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Initialize Instaloader
        loader = instaloader.Instaloader(download_videos=True)

        # Extract the shortcode from the Instagram URL
        shortcode = post_url.split("/")[-2]
        post = instaloader.Post.from_shortcode(loader.context, shortcode)

        # Save the video to the directory
        target_dir = os.path.join(output_dir, shortcode)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        loader.download_post(post, target=target_dir)

        # Locate the downloaded video file
        video_file = None
        for file_name in os.listdir(target_dir):
            if file_name.endswith(".mp4"):
                video_file = os.path.join(target_dir, file_name)
                break

        if video_file:
            print(f"Instagram video downloaded: {video_file}")
            return video_file
        else:
            print("No video file found.")
            return None
    except Exception as e:
        print(f"Error downloading Instagram video: {e}")
        return None


# Downloader Logic for TikTok
def download_tiktok_video(post_url, output_dir="videos"):
    try:
        # Use yt-dlp for TikTok downloads
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        file_name = os.path.join(output_dir, "%(title)s.%(ext)s")
        subprocess.run(["yt-dlp", "-o", file_name, post_url], check=True)
        print(f"TikTok video downloaded to {output_dir}")
        return output_dir  # Return the directory for further processing
    except Exception as e:
        print(f"Error downloading TikTok video: {e}")
        return None


# API Interaction to get upload URL
def get_upload_url(token):
    try:
        headers = {"Flic-Token": token, "Content-Type": "application/json"}
        response = requests.get(f"{BASE_API_URL}/generate-upload-url", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get upload URL: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error getting upload URL: {e}")
    return None


# Upload video to URL
def upload_video_to_url(upload_url, file_path):
    try:
        with open(file_path, 'rb') as video_file:
            response = requests.put(upload_url, data=video_file, headers={"Content-Type": "video/mp4"})
        if response.status_code == 200:
            print("Video uploaded successfully.")
            return True
        else:
            print(f"Failed to upload video: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"Error uploading video: {e}")
        return False


# Create Post after Upload
def create_post(token, title, hash_value, category_id):
    try:
        headers = {"Flic-Token": token, "Content-Type": "application/json"}
        body = {
            "title": title,
            "hash": hash_value,
            "is_available_in_public_feed": False,
            "category_id": category_id,
        }

        # Make the POST request to create the post
        response = requests.post(BASE_API_URL, headers=headers, json=body)

        if response.status_code == 200:
            response_json = response.json()
            # Check if the response contains a success message
            if response_json.get("status") == "success":
                print("Post created successfully.")
                print(f"Post Identifier: {response_json.get('identifier')}")
                return response_json  # Return the post details for further processing
            else:
                print(f"Unexpected response: {response_json}")
        else:
            print(f"Failed to create post: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error creating post: {e}")
    return None


# Process Video and Upload
def process_video(file_path, token):
    try:
        upload_data = get_upload_url(token)
        if not upload_data:
            print("Failed to get upload URL.")
            return

        upload_url = upload_data["url"]
        hash_value = upload_data["hash"]

        # Upload the video
        if upload_video_to_url(upload_url, file_path):
            # Create the post after successful upload
            post_data = create_post(token, "Uploaded Video", hash_value, category_id=25)
            if post_data:
                os.remove(file_path)  # Delete file only after successful post creation
                print(f"Processed and deleted: {file_path}")
            else:
                print("Post creation failed.")
        else:
            print("Video upload failed, skipping deletion.")
    except Exception as e:
        print(f"Error processing video: {e}")


# Watch Directory for New Video
class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.mp4'):
            token = get_flic_token()
            if token:
                process_video(event.src_path, token)
            else:
                print("Failed to fetch Flic Token.")


def watch_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    event_handler = VideoHandler()
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=False)
    observer.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


# Main Script
if __name__ == "__main__":
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR)

    token = get_flic_token()
    if not token:
        print("Failed to fetch Flic Token. Exiting...")
        exit()

    print("Welcome to the Video Bot!")
    while True:
        print("\nMenu:")
        print("1. Download Instagram Video")
        print("2. Download TikTok Video")
        print("3. Watch Directory for Video Upload")
        print("4. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            post_url = input("Enter Instagram video URL: ")
            downloaded_file = download_instagram_video(post_url)
            if downloaded_file:
                process_video(downloaded_file, token)
        elif choice == "2":
            post_url = input("Enter TikTok video URL: ")
            downloaded_file = download_tiktok_video(post_url)
            if downloaded_file:
                process_video(downloaded_file, token)
        elif choice == "3":
            print("Watching directory for new videos...")
            watch_directory(VIDEO_DIR)
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.")
