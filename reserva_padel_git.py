from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import datetime
import os

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========= CONFIG =========
URL = "https://ociopadel.es"

# ✅ CREDENCIALES SEGURAS DESDE GITHUB
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

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

print(f"🔁 Orden: {orden_dias}")

# ✅ ESPERA HASTA 00:00
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

# ========= ESPERAR CALENDARIO =========
wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "celda")))

# ========= CAMBIO DE SEMANA =========
fecha_str = target_day.strftime("%d/%m/%Y")

driver.execute_script(f"""
document.getElementById('calendario-selector-semana').value = '{fecha_str}';
""")

driver.execute_script("""
$('#calendario-selector-semana').trigger('change');
""")

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

        slots_visibles = [s for s in slots if s.is_displayed()]

        if not slots_visibles:
            return False

        slot = slots_visibles[0]

        driver.execute_script("arguments[0].click();", slot)
        time.sleep(0.8)

        if "reservada-usuario" in slot.get_attribute("class"):
            print(f"✅ RESERVA → {dia} 20:30 {pista_nombre}")
            return True

        return False

    except:
        return False

# ========= MODO COMPETITIVO =========
inicio = time.time()
duracion = 5

reserva = False

while time.time() - inicio < duracion and not reserva:
    for dia in orden_dias:

        if intentar_reserva(dia, "pista-58"):
            reserva = True
            break

        if intentar_reserva(dia, "pista-30"):
            reserva = True
            break

    time.sleep(0.12)

if not reserva:
    print("❌ No se pudo reservar")

driver.quit()
