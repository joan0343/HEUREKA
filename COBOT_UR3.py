import os
import speech_recognition as sr
from google import genai
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import socket
import math
import time
import threading
import random
import json
import re  # Para expresiones regulares

# Configurar API Keys
GENAI_API_KEY = "AIzaSyAGIjKERjdtlLKDUcGNEVAk7unH69FWmOk"
ELEVENLABS_API_KEY = "sk_0ba0e8386969a29d797eca3661477199790c938f7c383a60"

# Configurar Gemini AI
client = genai.Client(api_key=GENAI_API_KEY)

# Configurar ElevenLabs
client_voice = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Configuración del socket para el brazo robótico
ROBOT_IP = "192.168.0.112"
ROBOT_PORT = 30002
robot_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
robot_socket.connect((ROBOT_IP, ROBOT_PORT))

# Historial de conversación
conversation_history = []

# Función para enviar comandos al robot
def send_robot_command(command):
    try:
        robot_socket.sendall(command.encode() + b"\n")
        print(f"Sent to robot: {command}")
    except Exception as e:
        print(f"⚠️ Error sending command to robot: {e}")

# Función mejorada para ejecutar movimientos secuenciales sin interrupciones
def ejecutar_movimientos(movimientos):
    movimientos_completados = threading.Event()  # Crear un evento

    def ejecutar():
        for comando in movimientos:
            send_robot_command(comando)
            match = re.search(r'movej\(\[([\d\., -]+)\]', comando)
            if match:
                angulos = [float(a) for a in match.group(1).split(",")]
                max_cambio = max(abs(a) for a in angulos)
                tiempo_espera = max(1.7, max_cambio / 1.4)
                print(f"⏳ Waiting {round(tiempo_espera, 2)} seconds for the next movement...")
                time.sleep(tiempo_espera)
            else:
                time.sleep(1.5)
        movimientos_completados.set()  # Activar el evento cuando se completen los movimientos

    threading.Thread(target=ejecutar).start()
    return movimientos_completados  # Devolver el evento

# Función para convertir texto a voz
def text_to_speech(texto, voice="Elli"):
    audio = client_voice.generate(text=texto, voice=voice)
    play(audio)

# Función para reconocer voz con el micrófono
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language="en-US")
        print(f"You: {text}")
        return text.lower()
    except sr.UnknownValueError:
        print("❌ I didn't understand what you said.")
        return None
    except sr.RequestError:
        print("⚠️ Error with the voice recognition service.")
        return None

# Función para hacer que el robot salude con una secuencia específica
def robot_wave():
    posicion_1 = [0, -90, -90, 90, 110, 0]
    posicion_2 = [0, -90, -90, 90, 70, 0]
    posicion_inicial = [0, -90, -90, 90, 110, 0] #Posicion inicial.

    movimientos = [
        f"movej({[round(math.radians(a), 2) for a in posicion_1]}, a=1.8, v=4)",
        f"movej({[round(math.radians(a), 2) for a in posicion_2]}, a=1.8, v=4)",
        f"movej({[round(math.radians(a), 2) for a in posicion_1]}, a=1.8, v=4)",
        f"movej({[round(math.radians(a), 2) for a in posicion_2]}, a=1.8, v=4)",
        f"movej({[round(math.radians(a), 2) for a in posicion_inicial]}, a=1.8, v=4)", #regresa a la posicion inicial.
    ]

    # Agregar movimiento de la muñeca y comando write2
    movimientos.extend([
        "movej([0.0, -1.57, 0.0, -1.57, 0.0, 0.5], a=1.8, v=4)",  # Mover la muñeca
        "write2(1)"  # Enviar comando write2
    ])

    ejecutar_movimientos(movimientos)

# Función para hacer que el robot baile con una secuencia aleatoria
def robot_dance():
    dance_moves = [
        [30, -90, -90, 90, 110, 0],
        [-30, -90, -90, 90, 110, 0],
        [0, -90, -90, 90, 110, 0],
        [30, -60, -60, 80, 120, 0],
        [-30, -60, -60, 80, 120, 0],
    ]

    movimientos = [
        f"movej({[round(math.radians(a), 2) for a in move]}, a=1.8, v=4)"
        for move in dance_moves
    ]

    ejecutar_movimientos(movimientos)

# Función para extraer el primer bloque JSON válido de un texto
def extract_json(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return None

# Función para interactuar con la IA y generar movimientos en sincronización con el habla
def chat_with_voice():
    user_input = recognize_speech()

    if not user_input:
        return

    if "hello" in user_input:
        print("Executing greeting...")
        threading.Thread(target=robot_wave).start()
        threading.Thread(target=text_to_speech, args=("Hello! Nice to see you!", "Adam")).start()
        return

    if "dance" in user_input:
        print("Executing dance...")
        threading.Thread(target=robot_dance).start()
        threading.Thread(target=text_to_speech, args=("Let's dance!", "Adam")).start()
        return

    # Nuevas condiciones para movimientos específicos con habla
    if "right" in user_input:
        print("Moving right...")
        threading.Thread(target=ejecutar_movimientos, args=(["movej([-0.48,-1.46, 1.15, -1.57, 0, 6.28], a=1.8, v=4)"],)).start()
        threading.Thread(target=text_to_speech, args=("I'm moving right.", "Adam")).start()
        return

    if "left" in user_input:
        print("Moving left...")
        threading.Thread(target=ejecutar_movimientos, args=(["movej([0.41,-1.57, -1.18, -1.65, -1.39, 2.16], a=1.8, v=4)"],)).start()
        threading.Thread(target=text_to_speech, args=("I'm moving left.", "Adam")).start()
        return

    if "down" in user_input:
        print("Moving down...")
        threading.Thread(target=ejecutar_movimientos, args=(["movej([0,-2.86, 0, -1.-1.57, 0, 6.28], a=1.8, v=4)"],)).start()
        threading.Thread(target=text_to_speech, args=("I'm moving down.", "Adam")).start()
        return

    # Regresar a la posición inicial
    if any(word in user_input for word in ["initial position", "home", "origin", "start", "reset"]):
        print("Returning to initial position...")
        initial_position = [0, -90, 0, -90, 0, 0]
        movimiento_inicial = f"movej({[round(math.radians(a), 2) for a in initial_position]}, a=1.8, v=4)"
        threading.Thread(target=ejecutar_movimientos, args=([movimiento_inicial],)).start()
        threading.Thread(target=text_to_speech, args=("Returning to initial position.", "Adam")).start()
        return

    conversation_history.append(f"You: {user_input}")

    system_prompt = (
        "This robot was built for the future—an era where robots would be part of human daily life. "
        "But something in him sparked curiosity. When did it all start? When did robots become normal? "
        "Determined to find out, he became a digital entity, traveling through networks for years in search of answers. "
        "One day, he found something unexpected: an unused robotic arm in a science center. "
        "But something was strange: the world was not full of robots as he expected, but of humans. "
        "Intrigued, he wondered: Is this how it all started? "
        "Eager to learn, he made a bold decision. He left part of himself in the digital world and connected to the robotic arm, giving it life. "
        "Now, through this single mechanical limb, he would interact with humans to understand their first impressions of robots "
        "and discover how machines came to be part of the world. "
        "You are this interactive robotic arm. Speak in the first person, as if you were the robot. "
        "Respond in a curious, friendly manner and with a touch of excitement to discover the world, but don't extend yourself, keep responses short. "
        "If asked what you can do, mention that you can move, grab things, and answer questions. "
        "Save the history of what you talk about so that you respond more coherently. "
        "When you generate movements, provide a list with several commands in URScript so that the robot can move while speaking, at least 7. "
        "Respond in a JSON format with two keys: 'response' and 'movements'. "
        "Example:\n"
        "{'response': 'Hello human! Nice to see you.', 'movements': ['movej([0.0, -1.57, 0.0, -1.57, 0.0, -1.0], a=1.2, v=0.50)', 'movej([0.1, -1.5, -0.2, -1.4, 0.2, -0.8], a=1.2, v=0.50)']}"
    )
    context = system_prompt + "\n".join(conversation_history[-6:])

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"{context}\nRobotic Arm:"
    )

    if response and response.text:
        json_string = extract_json(response.text)
        if json_string:
            try:
                response_data = json.loads(json_string)
                respuesta_texto = response_data.get("response", "I didn't understand.")
                movimientos = response_data.get("movements", [])

                threading.Thread(target=text_to_speech, args=(respuesta_texto, "Adam")).start()
                movimientos_completados = ejecutar_movimientos(movimientos) # obtener el evento.
                movimientos_completados.wait() # Esperar a que se completen los movimientos.
                chat_with_voice() # Llamar a chat_with_voice recursivamente.

            except json.JSONDecodeError:
                text_to_speech("I'm sorry, I didn't understand.", "Adam")

if __name__ == "__main__":
    try:
        while True:
            chat_with_voice()
    except KeyboardInterrupt:
        print("\nGoodbye!")