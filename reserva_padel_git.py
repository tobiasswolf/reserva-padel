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

semana_actual = hoy - datetime.timedelta(days=hoy.weekday())

dias_map = {
    "lunes": 0, "martes": 1, "miercoles": 2,
    "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6
}

for user in usuarios:

    print("\n========================")
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

    pistas = [("pista-58", "Pista 2"), ("pista-30", "Pista 1")]

    for pista_id, pista_nombre in pistas:

        print(f"\n🎾 Revisando {pista_nombre}")

        try:
            driver.find_element(By.ID, pista_id).click()
            time.sleep(2)

            # ✅ TODAS las reservas
            todas = driver.find_elements(By.XPATH, "//div[contains(@class,'celda')]")

            print(f"Total celdas: {len(todas)}")

            for r in todas:
                try:
                    clase = r.get_attribute("class")
                    dia = r.get_attribute("data-dia")
                    hora = r.get_attribute("data-hora")

                    if not dia or not hora:
                        continue

                    print(f"\n   📦 CLASE: {clase}")
                    print(f"   📅 {dia} {hora}")

                    # construir fecha
                    fecha = semana_actual + datetime.timedelta(days=dias_map[dia])
                    hora_dt = datetime.datetime.strptime(hora, "%H%M")

                    fecha = fecha.replace(hour=hora_dt.hour, minute=hora_dt.minute)

                    print(f"   🧠 Fecha: {fecha}")

                except Exception as e:
                    continue

        except Exception as e:
            print("❌ Error pista:", e)

    driver.quit()
