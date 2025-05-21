import base64
from PIL import Image
from io import BytesIO
import redis
import numpy as np
import face_recognition
import json
import ast
from app import base


class FaceAI:
    def __init__(self):
        pass

    def read_face(self, image_b64):
        """
        Reads a face from the image and returns the face data.
        """
        image_data = base64.b64decode(
            image_b64)
        image = Image.open(
            BytesIO(image_data))
        image_np = np.array(image)
        encodings = face_recognition.face_encodings(
            image_np)
        if not encodings:
            return None

        encoding_json = json.dumps(
            encodings[0].tolist())
        return encoding_json

    def recognize_face(self, face: str, r):
        """
        Recognizes the face and returns the result.
        """
        image_data = base64.b64decode(face)
        image = Image.open(BytesIO(image_data))
        image_np = np.array(image)

        encodings = face_recognition.face_encodings(
            image_np)
        if not encodings:
            return None

        incoming_encoding = encodings[0]

        matched_id = None
        for k in r.keys():
            value = r.get(k)
            if not value:
                continue

            decoded = json.loads(value)

            encoding_str = decoded.get('encoding')
            if encoding_str is None:
                continue

            try:
                known_encoding = np.array(json.loads(encoding_str))
            except Exception as e:
                print(
                    f"Error on convertion to array NumPy: {e}")
                continue

            try:
                # Compare as codificações
                result = face_recognition.compare_faces(
                    [known_encoding], incoming_encoding, tolerance=0.6)

                if result:  # Verifique se result não está vazio
                    if result[0]:  # Se houver correspondência
                        print('Found a match.')
                        matched_id = k.decode().split(':')[1]
                        break
                print("Not found.")
            except Exception as e:
                print(f"Erro ao comparar as codificações: {e}")
                continue
        return matched_id
