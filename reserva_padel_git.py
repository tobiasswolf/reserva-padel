from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import datetime
import os
import requests  # ✅ nuevo

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========= CONFIG =========
URL = "https://ociopadel.es"

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ========= TELEGRAM FUNCTION =========
def enviar_telegram(mensaje):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": mensaje
        })
    except:
        print("⚠️ Error enviando Telegram")


# ========= HEADLESS =========
options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# ========= FECHA =========
hoy = datetime.datetime.now()
target_day = hoy + datetime.timedelta(days=7)

dias_map = {
    "Monday": "lunes",
    "Tuesday": "martes",
    "Wednesday": "miercoles",
    "Thursday": "jueves",
    "Friday": "viernes",
    "Saturday": "sabado",
    "Sunday": "domingo"
}

dia_objetivo = dias_map[target_day.strftime("%A")]

print(f"📅 Día objetivo: {dia_objetivo}")

# ========= ORDEN =========
orden_dias = []

if dia_objetivo in ["martes", "miercoles", "jueves"]:
    orden_dias.append(dia_objetivo)

for d in ["martes", "miercoles", "jueves"]:
    if d != dia_objetivo:
        orden_dias.append(d)

orden_dias.append("lunes")

# ========= ESPERA =========
target_time = datetime.datetime.combine(datetime.date.today(), datetime.time(0,0,3))

while datetime.datetime.now() < target_time:
    time.sleep(0.05)

print("⏰ Ejecutando...")

# ========= DRIVER =========
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

# ========= CHECK RESERVA =========
mis_reservas = driver.find_elements(
    By.XPATH,
    "//div[contains(@class,'celda') and contains(@class,'reservada-usuario')]"
)

if len(mis_reservas) > 0:
    r = mis_reservas[0]
    dia = r.get_attribute("data-dia")
    hora = r.get_attribute("data-hora")

    mensaje = f"⚠️ YA TIENES RESERVA\nDía: {dia}\nHora: {hora[:2]}:{hora[2:]}"
    print(mensaje)
    enviar_telegram(mensaje)

    driver.quit()
    exit()

# ========= CAMBIO SEMANA =========
fecha_str = target_day.strftime("%d/%m/%Y")

driver.execute_script(f"document.getElementById('calendario-selector-semana').value = '{fecha_str}';")
driver.execute_script("$('#calendario-selector-semana').trigger('change');")

time.sleep(3)

# ========= FUNCIÓN =========
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
            mensaje = f"✅ RESERVA CONFIRMADA\nDía: {dia}\nHora: 20:30\nPista: {pista_nombre}"
            print(mensaje)
            enviar_telegram(mensaje)
            return True

        return False

    except:
        return False

# ========= MODO COMPETITIVO =========
inicio = time.time()
reserva = False

while time.time() - inicio < 5 and not reserva:
    for dia in orden_dias:
        if intentar_reserva(dia, "pista-58"):
            reserva = True
            break
        if intentar_reserva(dia, "pista-30"):
            reserva = True
            break

    time.sleep(0.12)

if not reserva:
    mensaje = "❌ NO SE ENCONTRÓ DISPONIBILIDAD"
    print(mensaje)
    enviar_telegram(mensaje)

driver.quit()
