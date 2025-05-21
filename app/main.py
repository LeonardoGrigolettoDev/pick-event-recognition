import redis
import json
import base64
import numpy as np
from PIL import Image
from io import BytesIO
import face_recognition
import ast
from face import FaceAI


def main():
    print("Initializing")
    r = redis.Redis(host='redis', port=6379, db=0)
    pubsub = r.pubsub()
    pubsub.subscribe('encode')
    pubsub.subscribe('compare')
    face_ai = FaceAI()
    while True:
        try:
            for message in pubsub.listen():
                match message['type']:
                    case 'message':
                        try:
                            data = json.loads(message['data'])
                            encode = message['channel'] == b'encode'
                            match data.get('type'):
                                case 'facial':
                                    face_id = data['id']
                                    image_b64 = data['image']
                                    if (not image_b64):
                                        print(
                                            f"Invalid data received: {data}")
                                        r.publish('face_encoded', json.dumps({
                                            "id": face_id,
                                            "status": "error",
                                            "message": "No image received"
                                        }))
                                        continue
                                    result = face_ai.read_face(
                                        image_b64) if encode else face_ai.recognize_face(image_b64, r)
                                    if not result:
                                        print(
                                            f"No face detected in image.")
                                        r.publish('face_encoded' if encode else 'face_compared', json.dumps({
                                            "id": face_id,
                                            "status": "error",
                                            "message": "No result found"
                                        }))
                                        continue

                                    # Publica no canal 'face_encoded'
                                    response = {
                                        "id": face_id,
                                        "encoding": result,
                                        "status": "success"
                                    } if encode else {
                                        "id": face_id,
                                        "status": "not_found" if not result else "success",
                                        "matched_id": result.replace('face-', '') if result else None,
                                    }

                                    r.publish('face_encoded' if encode else 'face_compared',
                                              json.dumps(response))
                                    print(
                                        f"[{face_id}] ✅ Face processed.")
                                case _:
                                    print(data.get('type'),
                                          "unknown type")

                        except Exception as e:
                            print(
                                f"[{face_id}] ❌ Erro ao processar mensagem:", e)

        except KeyboardInterrupt:
            print(
                "\n🛑 Reloading...")
            break


if __name__ == "__main__":
    main()
