from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import datetime
import os
import json

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = "https://ociopadel.es"

usuarios = json.loads(os.getenv("USERS_JSON"))

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")

hoy = datetime.datetime.now()
target_day = hoy + datetime.timedelta(days=7)

semana_actual = hoy - datetime.timedelta(days=hoy.weekday())

dias_map = {
    "lunes": 0, "martes": 1, "miercoles": 2,
    "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6
}

# ========= LOOP USUARIOS =========
for user in usuarios:

    print("\n\n========================")
    print(f"👤 Usuario: {user['username']}")
    print("========================")

    driver = webdriver.Chrome(options=options)
    driver.get(URL)

    wait = WebDriverWait(driver, 15)

    time.sleep(1)

    # cookies
    try:
        driver.find_element(By.XPATH, "//button[contains(text(),'Agree')]").click()
    except:
        pass

    # login
    flecha = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "mbri-down")))
    driver.execute_script("arguments[0].click();", flecha)

    time.sleep(2)

    wait.until(EC.presence_of_element_located((By.ID, "email-formbuilder-2"))).send_keys(user["username"])
    driver.find_element(By.XPATH, "//input[@type='password']").send_keys(user["password"])
    driver.find_element(By.XPATH, "//button[contains(text(),'Enviar')]").click()

    time.sleep(5)

    # ========= FUNCIÓN DEBUG =========
    def debug_semana(nombre):

        print(f"\n===== 📅 DEBUG {nombre} =====")

        pistas = [("pista-58", "Pista 2"), ("pista-30", "Pista 1")]

        for pista_id, pista_nombre in pistas:

            print(f"\n🎾 {pista_nombre}")

            try:
                driver.find_element(By.ID, pista_id).click()
                time.sleep(2)

                celdas = driver.find_elements(By.XPATH, "//div[contains(@class,'celda')]")

                print(f"Total celdas: {len(celdas)}")

                for c in celdas:
                    try:
                        clase = c.get_attribute("class")
                        dia = c.get_attribute("data-dia")
                        hora = c.get_attribute("data-hora")

                        if not dia or not hora:
                            continue

                        # 🔥 FILTRO SOLO 20:30 (para no saturar)
                        if hora != "2030":
                            continue

                        fecha = semana_base + datetime.timedelta(days=dias_map[dia])
                        hora_dt = datetime.datetime.strptime(hora, "%H%M")
                        fecha = fecha.replace(hour=hora_dt.hour, minute=hora_dt.minute)

                        print(f"""
   📦 CLASE: {clase}
   📅 {dia} {hora}
   🧠 Fecha: {fecha}
""")

                        # 🔥 VER HTML COMPLETO (CLAVE)
                        html = c.get_attribute("outerHTML")
                        print(f"   🔎 HTML: {html[:120]}...")  # recortado para no explotar log

                    except:
                        continue

            except Exception as e:
                print("❌ Error pista:", e)

    # ========= SEMANA ACTUAL =========
    semana_base = semana_actual
    debug_semana("SEMANA ACTUAL")

    # ========= CAMBIO A SEMANA SIGUIENTE =========
    print("\n🔁 CAMBIANDO A SEMANA SIGUIENTE...")

    fecha_str = target_day.strftime("%d/%m/%Y")

    driver.execute_script(f"""
    document.getElementById('calendario-selector-semana').value = '{fecha_str}';
    """)
    driver.execute_script("$('#calendario-selector-semana').trigger('change');")

    time.sleep(4)

    # ========= SEMANA SIGUIENTE =========
    semana_base = semana_actual + datetime.timedelta(days=7)
    debug_semana("SEMANA SIGUIENTE")

    driver.quit()
