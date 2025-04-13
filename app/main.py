import redis
import json
import base64
import numpy as np
from PIL import Image
from io import BytesIO
import face_recognition
import ast


def main():
    print("Initializing")
    r = redis.Redis(host='redis', port=6379, db=0)
    pubsub = r.pubsub()
    pubsub.subscribe('encode')
    pubsub.subscribe('compare')
    while True:
        try:
            for message in pubsub.listen():
                match message['type']:
                    case 'message':
                        try:
                            match message['channel']:
                                case b'encode':
                                    data = json.loads(message['data'])
                                    match data.get('type'):
                                        case 'face':
                                            face_id = data['id']
                                            image_b64 = data['image']
                                            image_data = base64.b64decode(
                                                image_b64)
                                            image = Image.open(
                                                BytesIO(image_data))
                                            image_np = np.array(image)
                                            encodings = face_recognition.face_encodings(
                                                image_np)
                                            if not encodings:
                                                print(
                                                    f"[{face_id}] ⚠️ No face detected.")
                                                r.publish('face_encoded', json.dumps({
                                                    "id": face_id,
                                                    "status": "error",
                                                    "message": "No face detected"
                                                }))
                                                continue

                                            encoding_json = json.dumps(
                                                encodings[0].tolist())

                                            # Publica no canal 'face_encoded'
                                            response = {
                                                "id": face_id,
                                                "encoding": encoding_json,
                                                "status": "success"
                                            }

                                            r.publish('face_encoded',
                                                      json.dumps(response))
                                            print(
                                                f"[{face_id}] ✅ Face registrada com sucesso.")
                                        case _:
                                            print(data.get('type'),
                                                  "unknown type")
                                    break
                                case b'compare':
                                    data = json.loads(message['data'])
                                    match(data.get('type')):
                                        case 'face':
                                            face_id = data['id']
                                            image_b64 = data['image']

                                            # Decodifica a imagem base64
                                            image_data = base64.b64decode(
                                                image_b64)
                                            image = Image.open(
                                                BytesIO(image_data))
                                            image_np = np.array(image)

                                            encodings = face_recognition.face_encodings(
                                                image_np)
                                            if not encodings:
                                            
                                                r.publish('face_compared', json.dumps({
                                                    "id": face_id,
                                                    "status": "error",
                                                }))
                                                continue

                                            incoming_encoding = encodings[0]

                                            # cursor = 0
                                            matched_id = None
                                            for k in r.keys():
                                                value = r.get(k)
                                                print(value)
                                                if not value:
                                                    continue
                                                
                                                decoded = json.loads(value)
                                                print(decoded)

                                                # Verifica se o campo 'encoding' existe e não é None
                                                encoding_str = decoded.get('encoding')
                                                if encoding_str is None:
                                                    print(f"[{k}] ⚠️ Codificação não encontrada. Pulando...")
                                                    continue  # Pule este item, pois a codificação não está presente
                                                
                                                try:
                                                    # Tenta converter a string da codificação em um array NumPy
                                                    known_encoding = np.array(json.loads(encoding_str))  # Garantir que a codificação seja convertida de volta em array
                                                    print(f"Known encoding: {known_encoding}")
                                                except Exception as e:
                                                    print(f"Erro ao converter a codificação para array NumPy: {e}")
                                                    continue

                                                try:
                                                    # Compare as codificações
                                                    result = face_recognition.compare_faces([known_encoding], incoming_encoding, tolerance=0.6)
                                                    print(f"Resultado da comparação: {result}")
                                                    
                                                    if result:  # Verifique se result não está vazio
                                                        if result[0]:  # Se houver correspondência
                                                            print('MATCH!')
                                                            matched_id = k.decode().split(':')[1]
                                                            break
                                                    else:
                                                        print("Nenhum resultado de comparação encontrado.")
                                                except Exception as e:
                                                    print(f"Erro ao comparar as codificações: {e}")
                                                    continue
                             

                                            print(face_id, matched_id)
                                            r.publish('face_compared', json.dumps({
                                                "id": face_id,
                                                "status": "not_found" if not matched_id else "success",
                                                "matched_id": matched_id.replace('face-', '') if matched_id else None,
                                            }))
                                    break

                        except Exception as e:
                            print(
                                f"[{face_id}] ❌ Erro ao processar mensagem:", e)

        except KeyboardInterrupt:
            print(
                "\n🛑 Reloading...")
            break


if __name__ == "__main__":
    main()
