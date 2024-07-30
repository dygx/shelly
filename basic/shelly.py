import requests
import schedule
import time
from datetime import datetime

class ShellyPlug:
    def __init__(self, ip_address):
        self.base_url = f"http://{ip_address}"

    def turn_on(self):
        response = requests.get(f"{self.base_url}/relay/0?turn=on")
        if response.status_code == 200:
            print("Prise allumée")
        else:
            print("Erreur lors de l'allumage de la prise")

    def turn_off(self):
        response = requests.get(f"{self.base_url}/relay/0?turn=off")
        if response.status_code == 200:
            print("Prise éteinte")
        else:
            print("Erreur lors de l'extinction de la prise")

    def get_power_info(self):
        response = requests.get(f"{self.base_url}/meter/0")
        if response.status_code == 200:
            data = response.json()
            print(f"Puissance actuelle: {data['power']} W")
            print(f"Énergie totale: {data['total']} Wh")
        else:
            print("Erreur lors de la récupération des infos de puissance")

    def set_schedule(self, start_time, end_time):
        # Notez que cette fonction est une simulation, car l'API Shelly 
        # ne supporte pas directement la programmation via HTTP.
        # Vous devrez adapter cette partie selon les capacités réelles de votre appareil.
        print(f"Programmation définie : Allumage à {start_time}, extinction à {end_time}")

def main():
    shelly = ShellyPlug("192.168.1.51")  # Remplacez par l'adresse IP de votre Shelly Plug S

    while True:
        print("\nQue voulez-vous faire ?")
        print("1. Allumer la prise")
        print("2. Éteindre la prise")
        print("3. Obtenir les infos de puissance")
        print("4. Définir une programmation")
        print("5. Quitter")

        choice = input("Entrez votre choix (1-5): ")

        if choice == '1':
            shelly.turn_on()
        elif choice == '2':
            shelly.turn_off()
        elif choice == '3':
            shelly.get_power_info()
        elif choice == '4':
            start_time = input("Heure de début (HH:MM): ")
            end_time = input("Heure de fin (HH:MM): ")
            shelly.set_schedule(start_time, end_time)

            # Utilisation de la bibliothèque 'schedule' pour la programmation
            schedule.every().day.at(start_time).do(shelly.turn_on)
            schedule.every().day.at(end_time).do(shelly.turn_off)
            print("Programmation définie")
        elif choice == '5':
            print("Au revoir!")
            break
        else:
            print("Choix non valide. Veuillez réessayer.")

        # Exécute les tâches programmées
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()