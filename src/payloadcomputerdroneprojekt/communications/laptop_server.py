from flask import Flask, request
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_image():
    """
    Receive an image file via HTTP POST and save it to received_images/.
    """
    try:
        if 'file' not in request.files:
            return {"error": "No file provided"}, 400
        file = request.files['file']
        if not file.filename:
            return {"error": "No filename provided"}, 400

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "./received_images"
        os.makedirs(output_dir, exist_ok=True)
        ext = os.path.splitext(file.filename)[1] or '.jpg'
        filename = os.path.join(output_dir, f"image_{timestamp}{ext}")
        
        # Save the file
        file.save(filename)
        print(f"Image received successfully: {filename}")
        return {"message": "Image uploaded successfully"}, 200

    except Exception as e:
        print(f"Error receiving image: {e}")
        return {"error": str(e)}, 500

@app.route('/upload_objects', methods=['POST'])
def upload_objects():
    """
    Receive a JSON or CSV file containing found objects via HTTP POST and save it to received_objects/.
    """
    try:
        if 'file' not in request.files:
            return {"error": "No file provided"}, 400
        file = request.files['file']
        if not file.filename:
            return {"error": "No filename provided"}, 400

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "./received_objects"
        os.makedirs(output_dir, exist_ok=True)
        ext = os.path.splitext(file.filename)[1] or '.data'
        filename = os.path.join(output_dir, f"objects_{timestamp}{ext}")
        
        # Save the file
        file.save(filename)
        print(f"Objects received successfully: {filename}")
        return {"message": "Objects uploaded successfully"}, 200

    except Exception as e:
        print(f"Error receiving objects: {e}")
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)