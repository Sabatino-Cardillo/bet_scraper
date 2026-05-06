import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
import traceback
import random

API_URL = "https://virtualtop.alwaysdata.net/index.php" 
BETFLAG_URL = "https://www.betflag.it/virtual" 

# === I TUOI PROXY WEBSHARE ===
PROXIES = [
    'http://mwxscebx:v60ud3aolyz1@31.59.20.176:6754',
    'http://mwxscebx:v60ud3aolyz1@92.113.242.158:6742',
    'http://mwxscebx:v60ud3aolyz1@198.23.239.134:6540',
    'http://mwxscebx:v60ud3aolyz1@45.38.107.97:6014',
    'http://mwxscebx:v60ud3aolyz1@107.172.163.27:6543',
    'http://mwxscebx:v60ud3aolyz1@216.10.27.159:6837',
    'http://mwxscebx:v60ud3aolyz1@142.111.67.146:5611',
    'http://mwxscebx:v60ud3aolyz1@191.96.254.138:6185',
]

def get_random_proxy():
    return random.choice(PROXIES)

print("=== AVVIO SERVIZIO RENDER ===", flush=True)
print(f"Python version: {sys.version}", flush=True)

# === FAKE WEB SERVER ===
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Scraper is running!')
    def log_message(self, format, *args):
        pass

def run_webserver():
    try:
        server = HTTPServer(('0.0.0.0', 10000), HealthHandler)
        print("[WEB] Server avviato sulla porta 10000", flush=True)
        server.serve_forever()
    except Exception as e:
        print(f"[WEB] ERRORE: {e}", flush=True)

Thread(target=run_webserver, daemon=True).start()

# === CONFIGURAZIONE CHROME CON PROXY ===
print("[SETUP] Configuro Chrome con proxy...", flush=True)

# Scegli un proxy casuale
proxy = get_random_proxy()
print(f"[PROXY] Utilizzo: {proxy.split('@')[1] if '@' in proxy else proxy}", flush=True)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# User-Agent realistico
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# IMPOSTA IL PROXY
chrome_options.add_argument(f'--proxy-server={proxy}')

driver = None
try:
    driver = webdriver.Chrome(options=chrome_options)
    print("[SETUP] Chrome avviato con successo!", flush=True)
except Exception as e:
    print(f"[SETUP] ERRORE Chrome: {e}", flush=True)

def esegui_scansione():
    if driver is None:
        print("[ERRORE] Driver Chrome non disponibile", flush=True)
        return
        
    print(f"\n--- Analisi: {time.strftime('%H:%M:%S')} ---", flush=True)
    try:
        print(f"[DEBUG] Carico {BETFLAG_URL}...", flush=True)
        driver.get(BETFLAG_URL)
        time.sleep(10)
        
        eventi = driver.find_elements(By.CLASS_NAME, "box-home.event")
        print(f"[DEBUG] Trovati {len(eventi)} eventi", flush=True)
        
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

                r = requests.post(API_URL, data={
                    'palinsesto': pal_id,
                    'home': home,
                    'bookmaker': bookmaker,
                    'q1': q1.replace(',', '.'),
                    'qx': qx.replace(',', '.'),
                    'q2': q2.replace(',', '.')
                }, timeout=10)
                print(f"[OK] {home} ({bookmaker}) - {q1}/{qx}/{q2} (HTTP {r.status_code})", flush=True)
                
            except Exception as e:
                print(f"Errore evento: {e}", flush=True)
                continue

        chiusi = driver.find_elements(By.CLASS_NAME, "box-close")
        print(f"[DEBUG] Trovati {len(chiusi)} risultati chiusi", flush=True)
        
        for box in chiusi:
            try:
                p_raw = box.find_element(By.CLASS_NAME, "box-data").get_attribute('textContent')
                p_parts = p_raw.replace('P.', '').replace('A.', '').split()
                if len(p_parts) >= 2:
                    p_id_prefix = f"{p_parts[0]}_{p_parts[1]}"
                    res = box.find_element(By.TAG_NAME, "h3").get_attribute('textContent').strip()
                    if res:
                        r = requests.post(API_URL, data={'palinsesto_prefix': p_id_prefix, 'result': res}, timeout=10)
                        print(f"[RISULTATO] {p_id_prefix} -> {res} (HTTP {r.status_code})", flush=True)
            except: 
                continue

    except Exception as e:
        print(f"Errore generale: {e}", flush=True)
        print(traceback.format_exc(), flush=True)

print("=== Avvio loop scraper ===", flush=True)
while True:
    try:
        esegui_scansione()
        print("Attendo 120 secondi...", flush=True)
        time.sleep(120)
    except KeyboardInterrupt:
        print("\nFermato manualmente", flush=True)
        break
    except Exception as e:
        print(f"Errore loop: {e}", flush=True)
        time.sleep(60)
