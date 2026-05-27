from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import datetime
import os
import requests

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========= CONFIG =========
URL = "https://ociopadel.es"

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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

# ========= HEADLESS =========
options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# ========= FECHA =========
hoy = datetime.datetime.now()
target_day = hoy + datetime.timedelta(days=7)

# ========= ESPERA HASTA MEDIANOCHE =========
target_time = datetime.datetime.combine(datetime.date.today(), datetime.time(0,0,3))

while datetime.datetime.now() < target_time:
    time.sleep(0.05)

print("⏰ Ejecutando post medianoche...")

# ========= DRIVER =========
driver = webdriver.Chrome(options=options)
driver.get(URL)

wait = WebDriverWait(driver, 15)

# ========= COOKIES =========
time.sleep(1)
try:
    driver.find_element(By.XPATH, "//button[contains(text(),'Agree')]").click()
except:
    pass

# ========= LOGIN =========
flecha = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "mbri-down")))
driver.execute_script("arguments[0].click();", flecha)

time.sleep(2)

wait.until(EC.presence_of_element_located((By.ID, "email-formbuilder-2"))).send_keys(USERNAME)
driver.find_element(By.XPATH, "//input[@type='password']").send_keys(PASSWORD)
driver.find_element(By.XPATH, "//button[contains(text(),'Enviar')]").click()

time.sleep(5)

# ========= FUNCION DETECTAR RESERVA =========
def detectar_reserva_existente():
    pistas = [
        ("pista-58", "Pista 2"),
        ("pista-30", "Pista 1")
    ]

    for pista_id, pista_nombre in pistas:
        try:
            driver.find_element(By.ID, pista_id).click()
            time.sleep(0.5)

            reservas = driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'celda') and contains(@class,'reservada-usuario')]"
            )

            reservas_visibles = [r for r in reservas if r.is_displayed()]

            if reservas_visibles:
                r = reservas_visibles[0]
                dia = r.get_attribute("data-dia")
                hora = r.get_attribute("data-hora")

                hora_fmt = f"{hora[:2]}:{hora[2:]}"
                return (dia, hora_fmt, pista_nombre)

        except:
            continue

    return None

# ========= CHECK SEMANA ACTUAL =========
reserva = detectar_reserva_existente()

if reserva:
    dia, hora, pista = reserva

    mensaje = f"""⚠️ YA TENES RESERVA (SEMANA ACTUAL)
Día: {dia}
Hora: {hora}
Pista: {pista}"""

    print(mensaje)
    enviar_telegram(mensaje)
    driver.quit()
    exit()

print("✅ Sin reservas en semana actual")

# ========= CAMBIO SEMANA =========
fecha_str = target_day.strftime("%d/%m/%Y")

driver.execute_script(f"""
document.getElementById('calendario-selector-semana').value = '{fecha_str}';
""")

driver.execute_script("""
$('#calendario-selector-semana').trigger('change');
""")

time.sleep(3)

print(f"✅ Semana siguiente cargada: {fecha_str}")

# ========= CHECK SEMANA SIGUIENTE =========
reserva = detectar_reserva_existente()

if reserva:
    dia, hora, pista = reserva

    mensaje = f"""⚠️ YA TENES RESERVA (SEMANA SIGUIENTE)
Día: {dia}
Hora: {hora}
Pista: {pista}"""

    print(mensaje)
    enviar_telegram(mensaje)
    driver.quit()
    exit()

print("✅ Sin reservas en semana siguiente → buscar")

# ========= FUNCION RESERVA =========
def intentar_reserva(dia, pista_id):
    try:
        pista_nombre = "Pista 2" if pista_id == "pista-58" else "Pista 1"

        driver.find_element(By.ID, pista_id).click()
        time.sleep(0.3)

        slots = driver.find_elements(
            By.XPATH,
            f"//div[@data-dia='{dia}' and @data-hora='2030']"
        )

        slots_visibles = [s for s in slots if s.is_displayed()]

        if not slots_visibles:
            return False

        slot = slots_visibles[0]

        driver.execute_script("arguments[0].click();", slot)
        time.sleep(0.8)

        if "reservada-usuario" in slot.get_attribute("class"):
            mensaje = f"""✅ RESERVA CONFIRMADA
Día: {dia}
Hora: 20:30
Pista: {pista_nombre}"""

            print(mensaje)
            enviar_telegram(mensaje)
            return True

        return False

    except:
        return False

# ========= MODO COMPETITIVO =========
dias_orden = ["martes", "miercoles", "jueves", "lunes"]

inicio = time.time()
reserva = False

while time.time() - inicio < 5 and not reserva:
    for dia in dias_orden:
        print(f"⚡ Intentando {dia}")

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
