from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
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

# ========= LOG =========
def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

# ========= TELEGRAM =========
def enviar_telegram(mensaje):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": mensaje}
        )
    except Exception as e:
        log(f"❌ Telegram error: {e}")

hora_ejecucion = datetime.datetime.now().strftime("%H:%M")

# ========= CHROME =========
options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")

# ========= FECHA =========
hoy = datetime.datetime.now()
target_day = hoy + datetime.timedelta(days=7)
semana_actual = hoy - datetime.timedelta(days=hoy.weekday())
semana_siguiente = semana_actual + datetime.timedelta(days=7)

dias_map = {
    "lunes": 0, "martes": 1, "miercoles": 2,
    "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6
}

# ========= LOOP =========
for user in usuarios:

    USERNAME = user["username"]
    PASSWORD = user["password"]
    CODIGO = user["codigo"].lower()

    log(f"👤 Usuario: {USERNAME}")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)
    actions = ActionChains(driver)

    driver.get(URL)

    # ========= LOGIN =========
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

    # ========= ESPERA ROBUSTA =========
    log("Esperando interfaz...")

    wait.until(EC.presence_of_element_located((By.ID, "pista-58")))
    driver.find_element(By.ID, "pista-58").click()

    time.sleep(1)

    wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'celda')]")))

    log("✅ Calendario cargado")

    # ========= DETECCIÓN =========
    def detectar_reserva(semana_base):

        pistas = [("pista-58", "Pista 2"), ("pista-30", "Pista 1")]
        ahora = datetime.datetime.now()

        for pista_id, pista_nombre in pistas:
            try:
                log(f"🎾 Revisando {pista_nombre}")

                driver.find_element(By.ID, pista_id).click()
                time.sleep(1)

                celdas = driver.find_elements(By.XPATH, "//div[contains(@class,'celda')]")

                for c in celdas:
                    try:
                        clase = c.get_attribute("class")
                        dia = c.get_attribute("data-dia")
                        hora = c.get_attribute("data-hora")

                        if not dia or not hora:
                            continue
                        if "reservada" not in clase:
                            continue

                        fecha = semana_base + datetime.timedelta(days=dias_map[dia])
                        hora_dt = datetime.datetime.strptime(hora, "%H%M")
                        fecha = fecha.replace(hour=hora_dt.hour, minute=hora_dt.minute)

                        if fecha < ahora:
                            continue

                        # ✅ HOVER
                        actions.move_to_element(c).perform()
                        time.sleep(0.8)

                        # ✅ LEER POPOVER
                        try:
                            pop = wait.until(
                                EC.presence_of_element_located((By.CLASS_NAME, "popover-body"))
                            )

                            texto = pop.text.strip().lower()
                            log(f"🔎 Popover: {texto}")

                            if CODIGO in texto:
                                log("✅ RESERVA PROPIA DETECTADA")

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

            except:
                continue

        return None

    # ========= SEMANA ACTUAL =========
    reserva = detectar_reserva(semana_actual)

    # ========= SEMANA SIGUIENTE =========
    if not reserva:

        log("➡️ Cambiando semana...")

        fecha_str = target_day.strftime("%d/%m/%Y")

        try:
            selector = wait.until(
                EC.presence_of_element_located((By.ID, "calendario-selector-semana"))
            )

            driver.execute_script("""
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('change'));
            """, selector, fecha_str)

            log("✅ Semana cambiada")

        except Exception as e:
            log(f"❌ Error cambio semana: {e}")

        time.sleep(3)

        reserva = detectar_reserva(semana_siguiente)

    # ========= RESULTADO =========
    if reserva:
        dia, hora, pista, fecha = reserva

        mensaje = f"""⚠️ YA TENES RESERVA
Usuario: {USERNAME}
Horario ejecución: {hora_ejecucion}

Día: {dia} ({fecha})
Hora: {hora}
Pista: {pista}"""

        log("📩 Enviando notificación de reserva")
        enviar_telegram(mensaje)

    else:
        log("❌ No se encontró reserva")

        mensaje = f"""❌ NO SE ENCONTRÓ DISPONIBILIDAD
Usuario: {USERNAME}
Horario ejecución: {hora_ejecucion}"""

        enviar_telegram(mensaje)

    driver.quit()
