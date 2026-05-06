import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

API_URL = "https://virtualtop.alwaysdata.net/index.php" 
BETFLAG_URL = "https://www.betflag.it/virtual" 

# Configurazione per Render
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")

driver = webdriver.Chrome(options=chrome_options)

def esegui_scansione():
    print(f"\n--- Analisi: {time.strftime('%H:%M:%S')} ---")
    try:
        driver.get(BETFLAG_URL)
        time.sleep(10)

        eventi = driver.find_elements(By.CLASS_NAME, "box-home.event")
        print(f"Trovati {len(eventi)} eventi")
        
        for event in eventi:
            try:
                pal_raw = event.find_element(By.CLASS_NAME, "box-data").get_attribute('textContent')
                parts = pal_raw.replace('P.', '').replace('A.', '').split()
                date_str = datetime.now().strftime('%Y%m%d')
                if len(parts) >= 2:
                    pal_id = f"{parts[0]}_{parts[1]}_{date_str}"
                else:
                    continue

                raw_teams = event.find_element(By.CLASS_NAME, "desavv").get_attribute('textContent').strip()
                home = raw_teams.upper()

                try:
                    bookmaker = event.find_element(By.CSS_SELECTOR, ".box-event-info h3").get_attribute('textContent').strip()
                except:
                    bookmaker = "Betflag"

                btns = event.find_element(By.ID, "C9").find_elements(By.CLASS_NAME, "btn.bOdd")
                if len(btns) >= 3:
                    q1 = btns[0].get_attribute('textContent').strip()
                    qx = btns[1].get_attribute('textContent').strip()
                    q2 = btns[2].get_attribute('textContent').strip()
                else:
                    continue

                if not q1 or q1 in ["0", "0.00", "0,00"]: 
                    continue

                requests.post(API_URL, data={
                    'palinsesto': pal_id,
                    'home': home,
                    'bookmaker': bookmaker,
                    'q1': q1.replace(',', '.'),
                    'qx': qx.replace(',', '.'),
                    'q2': q2.replace(',', '.')
                })
                print(f"[OK] Inviato: {home} ({bookmaker}) - {q1}/{qx}/{q2}")
            except Exception as e:
                print(f"Errore evento: {e}")
                continue

        # Risultati
        chiusi = driver.find_elements(By.CLASS_NAME, "box-close")
        for box in chiusi:
            try:
                p_raw = box.find_element(By.CLASS_NAME, "box-data").get_attribute('textContent')
                p_parts = p_raw.replace('P.', '').replace('A.', '').split()
                if len(p_parts) >= 2:
                    p_id_prefix = f"{p_parts[0]}_{p_parts[1]}"
                    res = box.find_element(By.TAG_NAME, "h3").get_attribute('textContent').strip()
                    if res:
                        requests.post(API_URL, data={'palinsesto_prefix': p_id_prefix, 'result': res})
                        print(f"[RISULTATO] {p_id_prefix} -> {res}")
            except: 
                continue

    except Exception as e:
        print(f"Errore generale: {e}")

if __name__ == "__main__":
    print("=== VirtualPRO Scraper su Render ===")
    while True:
        try:
            esegui_scansione()
            print("Attendo 120 secondi...")
            time.sleep(120)
        except KeyboardInterrupt:
            print("\nFermato manualmente")
            break
        except Exception as e:
            print(f"Errore loop: {e}")
            time.sleep(60)
