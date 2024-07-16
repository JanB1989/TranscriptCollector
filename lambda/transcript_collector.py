import re
import os
import json
from datetime import datetime, timezone

import boto3
from pytubefix import YouTube

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb_client = boto3.resource('dynamodb')

def decide_caption_track(caption_tracks, priority_list):
    """Decides the best caption track based on a priority list."""
    caption_set = set(caption_tracks)
    for track in priority_list:
        if track in caption_set:
            return track
    return None

def extract_caption(youtube_video, track_code):
    """Extracts the caption for the specified track code."""
    return youtube_video.captions.get(track_code)

def format_publish_date(date):
    """Formats the datetime object to an ISO 8601 string with timezone info."""
    if date:
        return date.astimezone(timezone.utc).isoformat()
    return None

def time_str_to_milliseconds(time_str):
    """Converts a time string in the format 'HH:MM:SS,fff' to milliseconds."""
    dt = datetime.strptime(time_str, "%H:%M:%S,%f")
    milliseconds = (dt.hour * 3600 + dt.minute * 60 + dt.second) * 1000 + dt.microsecond // 1000
    return milliseconds

def parse_srt_to_dict(srt_caption):
    """Parses SRT captions into a dictionary format."""
    captions = re.split(r'\n\n', srt_caption.strip())
    parsed_captions = []
    caption_length = 0
    
    for caption in captions:
        parts = caption.split('\n')
        timestamp = parts[1]
        start_time, end_time = timestamp.split(' --> ')
        start_time_ms = time_str_to_milliseconds(start_time)
        end_time_ms = time_str_to_milliseconds(end_time)
        text = ' '.join(parts[2:])
        caption_length += len(text)
        parsed_captions.append({
            'start_time': start_time_ms,
            'end_time': end_time_ms,
            'text': text
        })
    
    return parsed_captions, caption_length

def extract_video_metadata(youtube_video):
    """Extracts metadata from the YouTube video."""
    video_data = {
        'video_id': youtube_video.video_id,
        'title': youtube_video.title,
        'views': youtube_video.views,
        'description': youtube_video.description,
        'thumbnail_url': youtube_video.thumbnail_url,
        'author': youtube_video.author,
        'channel_url': youtube_video.channel_url,
        'keywords': youtube_video.keywords,
        'length': youtube_video.length,
        'key_moments': youtube_video.key_moments,
        'publish_date': format_publish_date(youtube_video.publish_date),
        'rating': youtube_video.rating,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'caption_tracks': [track.code for track in youtube_video.caption_tracks]
    }
    
    video_data = {k: v for k, v in video_data.items() if v}
    return video_data

def lambda_handler(event, context):
    """AWS Lambda function handler."""
    table_name = os.environ['DYNAMODB_TABLE_NAME']
    bucket_name = os.environ['BUCKET_NAME']
    
    table = dynamodb_client.Table(table_name)
    youtube_video = YouTube(event.get("video_url"))
    video_metadata = extract_video_metadata(youtube_video)
    priority_list = ['a.en', 'en', 'en-US', 'en-GB', 'en-AU', 'en-CA']
    
    caption_track_code = decide_caption_track(video_metadata['caption_tracks'], priority_list)
    result = {"video_metadata": video_metadata}
    
    if caption_track_code:
        caption, caption_length = parse_srt_to_dict(youtube_video.captions[caption_track_code].generate_srt_captions())
        result["caption"] = caption
        video_metadata["caption_length"] = caption_length
        
        s3_key = f'{video_metadata["video_id"]}/transcript.json'
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(caption)
        )
        
        video_metadata["s3_path"] = f's3://{bucket_name}/{s3_key}'
    
    table.put_item(Item=video_metadata)
    return result
