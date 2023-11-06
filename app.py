from flask import Flask, request, jsonify
import os
import subprocess
import requests
import re

app = Flask(__name__)

# Send a formatted Discord embed
def send_discord_embed(title, desc):
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if webhook_url:
        requests.post(webhook_url, json={"embeds": [{"title": title, "description": desc, "color": 5814783}]})

def truncate(name, max_length=32):
    if len(name) > max_length:
        for bp in (':', ',', ' '):
            if bp in name[:max_length]:
                return name[:name[:max_length].rindex(bp)] + '...'
        return name[:max_length-3] + '...'
    return name

@app.route('/generate-epub', methods=['POST'])
def generate_epub():
    data = request.json
    cmd = ["jncep", "epub", "--email", os.getenv('JNCEP_EMAIL'), "--password", os.getenv('JNCEP_PASSWORD'), "--output", os.getenv('JNCEP_OUTPUT_DIR', '/app/downloads'), data['jnovel_club_url']]
    cmd += ['--byvolume'] if data.get('byvolume', True) else []
    cmd += ['--parts', data['parts']] if 'parts' in data else []
    
    process = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:", process.stdout, "\nSTDERR:", process.stderr)
    
    if "Success!" in process.stdout:
        series_name = re.search(r'/series/(.+?)(#|$)', data['jnovel_club_url']).group(1).replace('-', ' ').title()
        send_discord_embed("EPUB Downloaded", f"Series: {truncate(series_name)}\nSelection: Volume {data.get('parts', 'Not specified')}")
    else:
        send_discord_embed("EPUB Generation Error", "An error occurred while generating the EPUB.")
        return jsonify({"error": "An error occurred while generating the EPUB."}), 400
    
    return jsonify({"message": "EPUB generation process completed."}), 200

@app.route('/list', methods=['GET'])
def list_tracked():
    cmd = ["jncep", "track", "list"]
    process = subprocess.run(cmd, capture_output=True, text=True)
    return jsonify({"message": process.stdout}), 200 if process.returncode == 0 else 400

@app.route('/sync', methods=['GET'])
def sync_track():
    cmd = ["jncep", "track", "sync"]
    process = subprocess.run(cmd, capture_output=True, text=True)
    response_message = process.stdout if process.returncode == 0 else process.stderr
    return jsonify({"message": response_message}), 200 if process.returncode == 0 else 400

@app.route('/track', methods=['GET'])
def update_epubs():
    cmd = ["jncep", "update"]
    process = subprocess.run(cmd, capture_output=True, text=True)
    if process.returncode == 0:
        send_discord_embed("Update Success", "EPUBs have been updated.")
        return jsonify({"message": process.stdout}), 200
    else:
        send_discord_embed("Update Error", "An error occurred while updating EPUBs.")
        return jsonify({"message": process.stderr}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)