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

# ========= TELEGRAM =========
def enviar_telegram(mensaje):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": mensaje
        })
    except Exception as e:
        print("❌ Error Telegram:", e)

# ========= HORA =========
hora_ejecucion = datetime.datetime.now().strftime("%H:%M")

# ========= HEADLESS =========
options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")

# ========= FECHA =========
hoy = datetime.datetime.now()
target_day = hoy + datetime.timedelta(days=7)

semana_actual = hoy - datetime.timedelta(days=hoy.weekday())
semana_siguiente = semana_actual + datetime.timedelta(days=7)

# ========= ESPERA =========
target_time = datetime.datetime.combine(datetime.date.today(), datetime.time(0,0,3))

while datetime.datetime.now() < target_time:
    time.sleep(0.05)

# ========= LOOP USUARIOS =========
for user in usuarios:

    USERNAME = user["username"]
    PASSWORD = user["password"]

    print(f"\n👤 Ejecutando para {USERNAME}")

    driver = webdriver.Chrome(options=options)
    driver.get(URL)
    wait = WebDriverWait(driver, 15)

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

    # ========= DETECCION =========
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
                time.sleep(1)

                # ✅ FIX CRÍTICO: esperar render dinámico
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//div[contains(@class,'reservada-usuario')]")
                        )
                    )
                    print("✅ DOM actualizado (reservada-usuario visible)")
                except:
                    print("⚠️ No se detectó reservada-usuario (puede no haber reserva)")

                reservas = driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class,'reservada-usuario')]"
                )

                for r in reservas:
                    try:
                        dia = r.get_attribute("data-dia")
                        hora = r.get_attribute("data-hora")

                        fecha = semana_base + datetime.timedelta(days=dias_map[dia])

                        hora_dt = datetime.datetime.strptime(hora, "%H%M")
                        fecha = fecha.replace(
                            hour=hora_dt.hour,
                            minute=hora_dt.minute
                        )

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

    # ========= CHECK SEMANA ACTUAL =========
    reserva = detectar_reserva_existente(semana_actual)

    if reserva:
        dia, hora, pista, fecha = reserva

        mensaje = f"""⚠️ YA TENES RESERVA
Usuario: {USERNAME}
Horario ejecución: {hora_ejecucion}

Día: {dia} ({fecha})
Hora: {hora}
Pista: {pista}"""

        enviar_telegram(mensaje)
        driver.quit()
        continue

    # ========= CAMBIO SEMANA =========
    fecha_str = target_day.strftime("%d/%m/%Y")

    driver.execute_script(f"""
    document.getElementById('calendario-selector-semana').value = '{fecha_str}';
    """)

    driver.execute_script("$('#calendario-selector-semana').trigger('change');")

    time.sleep(4)

    # ========= CHECK SEMANA SIGUIENTE =========
    reserva = detectar_reserva_existente(semana_siguiente)

    if reserva:
        dia, hora, pista, fecha = reserva

        mensaje = f"""⚠️ YA TENES RESERVA
Usuario: {USERNAME}
Horario ejecución: {hora_ejecucion}

Día: {dia} ({fecha})
Hora: {hora}
Pista: {pista}"""

        enviar_telegram(mensaje)
        driver.quit()
        continue

    # ========= INTENTAR RESERVA =========
    def intentar_reserva(dia, pista_id):
        try:
            pista_nombre = "Pista 2" if pista_id == "pista-58" else "Pista 1"

            driver.find_element(By.ID, pista_id).click()
            time.sleep(0.3)

            slots = driver.find_elements(
                By.XPATH,
                f"//div[@data-dia='{dia}' and @data-hora='2030']"
            )

            slots = [s for s in slots if s.is_displayed()]

            if not slots:
                return False

            slot = slots[0]

            driver.execute_script("arguments[0].click();", slot)
            time.sleep(0.8)

            if "reservada-usuario" in slot.get_attribute("class"):

                dias_map = {
                    "lunes": 0, "martes": 1, "miercoles": 2,
                    "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6
                }

                fecha = semana_siguiente + datetime.timedelta(days=dias_map[dia])
                fecha_fmt = fecha.strftime("%d/%m")

                mensaje = f"""✅ RESERVA CONFIRMADA
Usuario: {USERNAME}
Horario ejecución: {hora_ejecucion}

Día: {dia} ({fecha_fmt})
Hora: 20:30
Pista: {pista_nombre}"""

                enviar_telegram(mensaje)
                return True

            return False

        except:
            return False

    # ========= MODO COMPETITIVO =========
    dias = ["martes", "miercoles", "jueves", "lunes"]

    inicio = time.time()
    ok = False

    while time.time() - inicio < 5 and not ok:
        for dia in dias:
            if intentar_reserva(dia, "pista-58"):
                ok = True
                break
            if intentar_reserva(dia, "pista-30"):
                ok = True
                break
        time.sleep(0.12)

    if not ok:
        mensaje = f"""❌ NO SE ENCONTRÓ DISPONIBILIDAD
Usuario: {USERNAME}
Horario ejecución: {hora_ejecucion}"""

        enviar_telegram(mensaje)

    driver.quit()
