from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import datetime
import os
import requests
import json

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========= CONFIG =========
URL = "https://ociopadel.es"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
usuarios = json.loads(os.getenv("USERS_JSON"))

def enviar_telegram(mensaje):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": mensaje
        })
    except Exception as e:
        print("❌ Error Telegram:", e)

hora_ejecucion = datetime.datetime.now().strftime("%H:%M")

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")

hoy = datetime.datetime.now()
target_day = hoy + datetime.timedelta(days=7)

semana_actual = hoy - datetime.timedelta(days=hoy.weekday())
semana_siguiente = semana_actual + datetime.timedelta(days=7)

target_time = datetime.datetime.combine(datetime.date.today(), datetime.time(0,0,3))

while datetime.datetime.now() < target_time:
    time.sleep(0.05)

# ========= LOOP USUARIOS =========
for user in usuarios:

    USERNAME = user["username"]
    PASSWORD = user["password"]

    print(f"\n\n====================")
    print(f"👤 Usuario: {USERNAME}")
    print(f"====================")

    driver = webdriver.Chrome(options=options)
    driver.get(URL)
    wait = WebDriverWait(driver, 15)

    time.sleep(1)
    try:
        driver.find_element(By.XPATH, "//button[contains(text(),'Agree')]").click()
    except:
        pass

    flecha = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "mbri-down")))
    driver.execute_script("arguments[0].click();", flecha)

    time.sleep(2)

    wait.until(EC.presence_of_element_located((By.ID, "email-formbuilder-2"))).send_keys(USERNAME)
    driver.find_element(By.XPATH, "//input[@type='password']").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button[contains(text(),'Enviar')]").click()

    time.sleep(5)

    # ========= DEBUG DETECCION =========
    def detectar_reserva_existente(semana_base):

    pistas = [("pista-58", "Pista 2"), ("pista-30", "Pista 1")]
    ahora = datetime.datetime.now()

    dias_map = {
        "lunes": 0, "martes": 1, "miercoles": 2,
        "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6
    }

    for pista_id, pista_nombre in pistas:
        try:
            driver.find_element(By.ID, pista_id).click()
            time.sleep(1.2)  # ✅ mantener

            # ✅ SOLO TUS RESERVAS
            reservas = driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'celda') and contains(@class,'reservada-usuario')]"
            )

            for r in reservas:
                try:
                    dia = r.get_attribute("data-dia")
                    hora = r.get_attribute("data-hora")

                    fecha = semana_base + datetime.timedelta(days=dias_map[dia])
                    hora_dt = datetime.datetime.strptime(hora, "%H%M")

                    fecha = fecha.replace(hour=hora_dt.hour, minute=hora_dt.minute)

                    # ✅ filtro temporal correcto
                    if fecha >= ahora:
                        return (
                            dia,
                            f"{hora[:2]}:{hora[2:]}",
                            pista_nombre,
                            fecha.strftime("%d/%m")
                        )

                except:
                    continue

        except:
            continue

    return None

    # ========= TEST SEMANA ACTUAL =========
    print("\n🟢 CHECK SEMANA ACTUAL")
    reserva = detectar_reserva_existente(semana_actual)

    if reserva:
        print("🔥 DETECTADA EN SEMANA ACTUAL:", reserva)
    else:
        print("❌ NO detectada en semana actual")

    # ========= CAMBIO SEMANA =========
    fecha_str = target_day.strftime("%d/%m/%Y")

    driver.execute_script(f"""
    document.getElementById('calendario-selector-semana').value = '{fecha_str}';
    """)
    driver.execute_script("$('#calendario-selector-semana').trigger('change');")

    time.sleep(4)

    # ========= TEST SEMANA SIGUIENTE =========
    print("\n🔵 CHECK SEMANA SIGUIENTE")
    reserva = detectar_reserva_existente(semana_siguiente)

    if reserva:
        print("🔥 DETECTADA EN SEMANA SIGUIENTE:", reserva)
    else:
        print("❌ NO detectada en semana siguiente")

    driver.quit()
