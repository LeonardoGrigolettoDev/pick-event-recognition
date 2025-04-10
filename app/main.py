from flask import Flask, request, jsonify
import face_recognition
import numpy as np
from PIL import Image

from io import BytesIO

app = Flask(__name__)
known_faces = {}

@app.route('/encode-face', methods=['POST'])
def register_face():
    face_id = request.form.get("id")
    image_file = request.files.get("image")

    if not face_id or not image_file:
        return jsonify({"error": "Missing id or image"}), 400

    image = Image.open(image_file.stream)
    image_np = np.array(image)

    encodings = face_recognition.face_encodings(image_np)
    if not encodings:
        return jsonify({"error": "No face found"}), 400

    known_faces[face_id] = encodings[0].tolist()
    return jsonify({"message": "Face registered", "id": face_id, 'enconding': known_faces[face_id]}), 200

@app.route('/recognize', methods=['POST'])
def recognize_face():
    image_file = request.files.get("image")

    if not image_file:
        return jsonify({"error": "Missing image"}), 400

    image = Image.open(image_file.stream)
    image_np = np.array(image)

    encodings = face_recognition.face_encodings(image_np)
    if not encodings:
        return jsonify({"error": "No face found"}), 400

    unknown_encoding = encodings[0]
    for face_id, known_encoding in known_faces.items():
        match = face_recognition.compare_faces([known_encoding], unknown_encoding)[0]
        if match:
            return jsonify({"match": True, "id": face_id})
    return jsonify({"match": False})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

