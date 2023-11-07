from flask import Flask, request, jsonify, render_template, send_from_directory, abort
import os
import subprocess
import requests
import re
import sys
from datetime import datetime
import time

app = Flask(__name__)

def check_environment_variables():
    """
    Check the presence of required environment variables on startup and
    prints a warning if the optional DISCORD_WEBHOOK_URL is missing.
    """
    required_vars = ['JNCEP_EMAIL', 'JNCEP_PASSWORD', 'JNCEP_OUTPUT_DIR']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}. Exiting.")
        sys.exit(1)
    
    if not os.getenv('DISCORD_WEBHOOK_URL'):
        print("Warning: DISCORD_WEBHOOK_URL is not set. Discord notifications will not be sent.")

def send_discord_notification(title, description):
    """
    Sends a Discord notification with a given title and description if
    DISCORD_WEBHOOK_URL is set.
    """
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if webhook_url:
        payload = {"embeds": [{"title": title, "description": description, "color": 5814783}]}
        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Discord notification failed: {e}")

def truncate(text, max_length=64):
    """
    Truncates the provided text to the specified max_length at the nearest
    preferred breakpoint without splitting words, appending ellipsis if needed.
    This version also handles filenames by truncating the series name part
    before "_Volume" and retains the volume and part information.
    """
    # Separate the base name and extension
    base_name, extension = os.path.splitext(text)
    # Find the position of "_Volume" in the base name
    volume_index = base_name.find('_Volume')
    
    # If "_Volume" is not found or the series name is short enough, return the base name with underscores replaced
    if volume_index == -1 or volume_index <= max_length:
        return base_name.replace('_', ' ') + extension

    # Extract the series name part before "_Volume"
    series_name = base_name[:volume_index]
    # Replace underscores with spaces for the series name
    series_name = series_name.replace('_', ' ')

    # Truncate the series name if it's longer than the max_length
    if len(series_name) > max_length:
        breakpoints = ('.', ',', ';', ' ')
        for bp in breakpoints:
            idx = series_name.rfind(bp, 0, max_length)
            if idx != -1:
                return series_name[:idx] + '...' + base_name[volume_index:].replace('_', ' ') + extension
        
        idx = series_name.rfind(' ', 0, max_length)
        if idx != -1:
            series_name = series_name[:idx] + '...'
        else:
            series_name = series_name[:max_length-3] + '...'

    # Return the truncated series name with the volume and part information and extension
    return series_name + base_name[volume_index:].replace('_', ' ') + extension

def run_jncep_command(command, success_message, error_message):
    """
    Runs the given jncep command using subprocess, sends a Discord notification
    based on the outcome, and returns the appropriate JSON response.
    """
    process = subprocess.run(command, capture_output=True, text=True)
    if process.returncode == 0:
        send_discord_notification(success_message, process.stdout)
        return jsonify({"message": process.stdout}), 200
    else:
        send_discord_notification(error_message, process.stderr)
        return jsonify({"message": process.stderr}), 400

@app.route('/generate-epub', methods=['POST'])
def generate_epub():
    """Endpoint to generate an EPUB from a J-Novel Club URL."""
    data = request.json
    jnovel_club_url = data['jnovel_club_url']
    cmd = [
        "jncep", "epub",
        "--email", os.getenv('JNCEP_EMAIL'),
        "--password", os.getenv('JNCEP_PASSWORD'),
        "--output", os.getenv('JNCEP_OUTPUT_DIR', '/app/downloads'),
        jnovel_club_url
    ] + (['--byvolume'] if data.get('byvolume', True) else []) \
      + (['--parts', data['parts']] if 'parts' in data else [])
    
    process = subprocess.run(cmd, capture_output=True, text=True)
    if "Success!" in process.stdout:
        series_name = re.search(r'/series/(.+?)(#|$)', jnovel_club_url).group(1).replace('-', ' ').title()
        description = f"Series: {truncate(series_name)}\n" \
                      f"Selection: Volume {data.get('parts', 'Not specified')}"
        send_discord_notification("EPUB Downloaded", description)
        return jsonify({"message": "EPUB generation process completed."}), 200
    
    send_discord_notification("EPUB Generation Error", "An error occurred while generating the EPUB.")
    return jsonify({"error": "An error occurred while generating the EPUB."}), 400

@app.route('/list', methods=['GET'])
def list_tracked():
    """Endpoint to list all tracked J-Novel Club URLs for EPUB generation."""
    return run_jncep_command(["jncep", "track", "list"],
                             "Tracking List Retrieved",
                             "Failed to Retrieve Tracking List")

@app.route('/track', methods=['GET'])
def sync_track():
    """Endpoint to update the tracking list with the latest changes."""
    return run_jncep_command(["jncep", "track", "sync"],
                             "Tracking List Synchronized",
                             "Synchronization Failed")

@app.route('/sync', methods=['GET'])
def update_epubs():
    """Endpoint to download EPUBs based on the tracking list."""
    output_dir = os.getenv('JNCEP_OUTPUT_DIR', '/app/downloads')  # Get the output directory from environment variable
    # Include the --byvolume flag in the command list
    return run_jncep_command(["jncep", "update", "--byvolume", "--output", output_dir],
                             "EPUBs Updated",
                             "Update Failed")


check_environment_variables()
# Path to the downloads directory
downloads_dir = os.getenv('JNCEP_OUTPUT_DIR', '/app/downloads')

# Ensure the directory exists
os.makedirs(downloads_dir, exist_ok=True)

@app.route('/')
def index():
    query = request.args.get('search', '').replace(' ', '_')  # Replace spaces with underscores for the search
    try:
        # List files in the downloads directory
        files = os.listdir(downloads_dir)
        
        # Process files for display and sort them by creation time, newest first
        processed_files = sorted([
            {
                'display_name': truncate(os.path.splitext(f)[0]),  # Apply truncation to the series name
                'full_name': f,  # Full filename for download link
                'timestamp': os.path.getctime(os.path.join(downloads_dir, f))  # File creation time as Unix timestamp
            }
            for f in files if query.lower() in f.lower().replace('_', ' ')  # Search functionality
        ], key=lambda x: x['timestamp'], reverse=True)  # Sort files by timestamp, newest first
    except OSError as e:
        return f"Error accessing the downloads directory: {e}", 500

    # Render the template with the list of files and the current search query
    return render_template('index.html', files=processed_files, query=query.replace('_', ' '))  # Display query with spaces

@app.route('/download/<path:filename>')
def download(filename):
    try:
        # Send file for download
        return send_from_directory(downloads_dir, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)