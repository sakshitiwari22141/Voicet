from flask import Blueprint, render_template, request, redirect, url_for, abort, flash, current_app, send_from_directory, send_file, jsonify
from flask_login import login_required, current_user
from . import db
from .models import Videos
from werkzeug.utils import secure_filename
from .worker import process_video_task
import yt_dlp

import os
import random
import string


import logging

# Configure logging to show up in Colab
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html', active='home')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name, active='profile')

@main.route('/upload', methods=['POST'])
@login_required
def upload():
    url = request.form.get('url')
    file = request.files.get('file')

    if url:
        try:
            random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            random_filename = random_string + '.mp4'
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                
            file_path = os.path.join(upload_dir, random_filename)
            
            logger.info(f"Downloading YouTube video from {url}")
            
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': file_path,
                'quiet': True,
                'no_warnings': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'YouTube Video')

            new_video = Videos(
                file_name=random_filename,
                file_extension='.mp4',
                original_filename=title + '.mp4',
                file_path=file_path,
                video_processed=0,
                percent_processed=0,
                posted_by=current_user.name)

            db.session.add(new_video)
            db.session.commit()
            logger.info(f"YouTube video saved: {title}")
            flash('YouTube video has been saved!', 'success')
            return redirect(url_for('main.gallery'))
        except Exception as e:
            logger.error(f"Error downloading YouTube video: {e}")
            flash(f'Error downloading YouTube video: {str(e)}', 'danger')
            return redirect(url_for('main.index'))

    if file and file.filename != '':
        try:
            random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            file_extension = os.path.splitext(file.filename)[1]
            random_filename = random_string + file_extension
            
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)

            file_path = os.path.join(upload_dir, random_filename)

            file.save(file_path)
            
            new_video = Videos(
                file_name=random_filename,
                file_extension=file_extension,
                original_filename=file.filename,
                file_path=file_path,
                video_processed=0,
                percent_processed=0,
                posted_by=current_user.name)

            db.session.add(new_video)
            db.session.commit()
            logger.info(f"Uploaded file saved: {file.filename}")
            flash('Post has been saved!', 'success')
            return redirect(url_for('main.gallery'))
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            flash(f'Error uploading file: {str(e)}', 'danger')
            return redirect(url_for('main.index'))

    flash('No file or URL provided', 'warning')
    return redirect(url_for('main.index'))


@main.route('/gallery/<int:id>/download', methods=['GET'])
@login_required
def download_post(id):
    video = Videos.query.get_or_404(id)
    if video.posted_by != current_user.name:
        abort(403) 
    
    filename = video.file_name
    original_filename = video.original_filename
    uploads = os.path.join(current_app.root_path, "static/uploads/")
    if not os.path.exists(os.path.join(uploads, filename)):
        flash('File not found on server.', 'danger')
        return redirect(url_for('main.gallery'))
        
    return send_from_directory(uploads, filename, as_attachment=True, download_name=original_filename)


@main.route('/gallery')
@login_required
def gallery():
    videos = Videos.query.filter_by(posted_by=current_user.name).all() # Only show own videos
    return render_template('gallery.html', videos=videos , active='gallery')

@main.route('/gallery/<int:id>/delete', methods=['GET'])
@login_required
def delete_post(id):
    video = Videos.query.get_or_404(id)
    if video.posted_by != current_user.name:
        abort(403)
        
    try:
        # Delete file from disk
        if os.path.exists(video.file_path):
            os.remove(video.file_path)
            logger.info(f"Deleted file: {video.file_path}")
        else:
            logger.warning(f"File not found for deletion: {video.file_path}")
            
        db.session.delete(video)
        db.session.commit()
        flash('Post has been deleted!','success') # changed to success for better UX
    except Exception as e:
        logger.error(f"Error deleting video: {e}")
        flash(f'Error deleting video: {str(e)}', 'danger')
        
    return redirect(url_for('main.gallery'))

@main.route('/gallery/<int:id>/translate', methods=['GET','POST'])
@login_required
def translate_post(id):
    video = Videos.query.get_or_404(id)
    if video.posted_by != current_user.name:
        abort(403)

    if request.method == 'GET':
        flash('Post can be translated!','success')
        return render_template('translate_post.html', video=video)

    elif request.method == 'POST':
        filepath = video.file_path
        language_voice = request.form.get('translateTo')
        gender_voice = request.form.get('gender')
        
        gender = 'male' if gender_voice == "male" else 'female'

        logger.info(f'Queuing Translation ID: {id}')
        
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        file_extension = video.file_extension
        random_filename = random_string + file_extension
        
        # Determine output path independent of current working directory
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        output_path = os.path.join(upload_dir, random_filename)
        
        # Start Celery Task
        task = process_video_task.delay(filepath, language_voice, gender_voice, output_path, f"Translated_{video.original_filename}")
        
        # We don't save to DB immediately, or we could save with 'Processing' status.
        # For now, let's just return the Task ID to the frontend.
        return jsonify({'task_id': task.id}), 202

@main.route('/status/<task_id>')
def taskstatus(task_id):
    task = process_video_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
            response['original_filename'] = task.info.get('original_filename', 'translated.mp4')
            
            # Here we might want to save to DB if we didn't before.
            # But the worker function doesn't have access to Flask app context properly unless configured.
            # For simplicity, we can let the task return the path and frontend redirects to a 'save' endpoint, 
            # Or assume the worker saved the file and we just need to let the user download it.
            
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)
