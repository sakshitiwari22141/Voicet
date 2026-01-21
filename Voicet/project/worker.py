from celery import Celery
from .voicet import translate_video
import os

def make_celery(app_name=__name__):
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    celery = Celery(app_name, broker=redis_url, backend=redis_url)
    return celery

celery = make_celery('voicet_worker')

@celery.task(bind=True)
def process_video_task(self, video_path, language_voice, gender_voice, output_path, original_filename):
    """
    Background task to process the video.
    """
    try:
        self.update_state(state='PROCESSING', meta={'status': 'Starting translation...'})
        
        # Call the heavy lifting function
        translate_video(video_path, language_voice, gender_voice, output_path)
        
        return {
            'status': 'Task completed!',
            'result': output_path,
            'original_filename': original_filename
        }
    except Exception as e:
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e
