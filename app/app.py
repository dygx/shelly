# app.py
from flask import Flask, render_template, jsonify, request
import requests
import json
import logging
from datetime import datetime
import threading
import schedule
import time
import os

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

SHELLY_IP = "192.168.1.51"  # Assurez-vous que cette adresse IP est correcte
SCHEDULE_FILE = 'schedule.json'

# Vérifier si le fichier schedule.json existe, sinon le créer
if not os.path.exists(SCHEDULE_FILE):
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump([], f)

def send_shelly_command(method, params=None):
    url = f"http://{SHELLY_IP}/rpc"
    payload = {
        "id": 1,
        "method": method,
        "params": params or {}
    }
    try:
        logging.debug(f"Envoi de la requête à : {url}")
        logging.debug(f"Payload : {payload}")
        response = requests.post(url, json=payload, timeout=5)
        logging.debug(f"Réponse reçue : {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Erreur lors de l'envoi de la commande : {str(e)}")
        return {"error": str(e)}

def load_schedule():
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            schedule_data = json.load(f)
        # Validation des données
        validated_schedule = []
        for item in schedule_data:
            if all(key in item for key in ['time', 'action', 'active']):
                try:
                    # Vérifier si le format de l'heure est correct
                    datetime.strptime(item['time'], "%H:%M")
                    validated_schedule.append(item)
                except ValueError:
                    logging.warning(f"Format d'heure invalide ignoré : {item}")
            else:
                logging.warning(f"Élément de programmation invalide ignoré : {item}")
        return validated_schedule
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        logging.error("Erreur de décodage JSON du fichier de programmation")
        return []

def save_schedule(schedule_data):
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(schedule_data, f)

def apply_schedule_item(item):
    logging.info(f"Applying schedule item: {item}")
    send_shelly_command("Switch.Set", {"id": 0, "on": item['action'] == 'on'})

def setup_schedule():
    schedule.clear()
    for item in load_schedule():
        if item['active']:
            try:
                schedule.every().day.at(item['time']).do(apply_schedule_item, item)
            except schedule.ScheduleValueError as e:
                logging.error(f"Erreur lors de la configuration de la programmation : {e}")

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    result = send_shelly_command("Shelly.GetStatus")
    logging.debug(f"Résultat de /status : {result}")
    return jsonify(result)

@app.route('/energy_data')
def energy_data():
    result = send_shelly_command("Switch.GetStatus", {"id": 0})
    logging.debug(f"Résultat de /energy_data : {result}")
    return jsonify(result)

@app.route('/toggle', methods=['POST'])
def toggle():
    current_state = send_shelly_command("Switch.GetStatus", {"id": 0})
    new_state = not current_state.get('result', {}).get('output', False)
    return jsonify(send_shelly_command("Switch.Set", {"id": 0, "on": new_state}))

@app.route('/settings', methods=['GET'])
def get_settings():
    result = send_shelly_command("Shelly.GetConfig")
    logging.debug(f"Résultat de get_settings : {result}")
    return jsonify(result)

@app.route('/schedule', methods=['GET', 'POST'])
def schedule_route():
    if request.method == 'GET':
        return jsonify(load_schedule())
    else:
        new_schedule = request.json
        save_schedule(new_schedule)
        setup_schedule()
        return jsonify({"success": True})

def start_schedule_thread():
    thread = threading.Thread(target=run_schedule, daemon=True)
    thread.start()
    return thread

if __name__ == '__main__':
    try:
        logging.info("Démarrage de l'application...")
        setup_schedule()
        schedule_thread = start_schedule_thread()
        logging.info("Thread de programmation démarré.")
        logging.info("Démarrage du serveur Flask...")
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    except Exception as e:
        logging.error(f"Une erreur s'est produite lors du démarrage de l'application : {str(e)}")
    finally:
        if 'schedule_thread' in locals() and schedule_thread.is_alive():
            logging.info("Arrêt du thread de programmation...")
            # Ici, vous pourriez ajouter un mécanisme pour arrêter proprement le thread si nécessaire
        logging.info("Application arrêtée.")