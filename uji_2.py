import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from multiprocessing import Process, Queue
import statistics
import traceback

time.sleep(random.uniform(0.5, 2.0))
URL = "http://localhost:8501"
N_USER = 5

input_mapping = {
    "Age (years)": "5.7",
    "Weight (kg)": "16.0",
    "PRISM III Score *": "14.0",
    "Vasoactive-Inotropic Score *": "9.36",
    "PICU Stay (days)": "13.0",
    "Interval from Admission (hours)": "18.17",
    "Duration of CRRT (days)": "4.23",
    "pH Level *": "7.33",
    "Lactic Acid (mmol/L) *": "2.24",
    "Hemoglobin (g/dL)": "9.45",
    "Platelet (10³/µL)": "109.54",
    "Urine Volume (mL/Kg/h) *": "0.90",
    "Albumin (g/dL) *": "3.05",
    "Creatinine (mg/dL)": "1.5",
    "PELOD Score *": "12.22",
    "pSOFA Score *": "9.56",
    "Bicarbonate (mmEq/L)": "21.7",
    "Sodium (mmol/L)": "138.72",
    "Potassium (mmol/L)": "3.61"
}

dropdown_mapping = {
    "Sex": "Male",
    "Ventilator Usage *": "No",
    "Fluid Overload *": "No",
    "Sepsis": "No",
    "Acute Liver Failure": "No",
    "Respiratory System Disease *": "No",
    "Tumor Lysis Syndrome": "Yes",
    "Hyperammonemia": "Yes"
}

def run_test(user_id, queue):
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=options)
        print(f"[User-{user_id}] Browser started")

        driver.get(URL)
        print(f"[User-{user_id}] Opened {URL}")
        time.sleep(5)

        start_time = time.time()

        # Masukkan nama dan ID
        try:
            driver.find_element(By.CSS_SELECTOR, "input[aria-label='Patient Name']").send_keys("Test Patient")
            driver.find_element(By.CSS_SELECTOR, "input[aria-label='Patient ID']").send_keys(f"TP{user_id:03}")
            print(f"[User-{user_id}] Patient info input successful")
        except Exception as e:
            raise Exception(f"[User-{user_id}] Gagal isi nama/ID: {e}")

        # Input numerik
        for label, val in input_mapping.items():
            try:
                input_box = driver.find_element(By.CSS_SELECTOR, f"input[aria-label='{label}']")
                input_box.send_keys(val)
                print(f"[User-{user_id}] Input '{label}' = {val}")
            except Exception as e:
                raise Exception(f"[User-{user_id}] Gagal input '{label}': {e}")

        # Dropdown
        # for label, choice in dropdown_mapping.items():
        #     try:
        #         dropdown_box = driver.find_element(By.XPATH, f"//label[contains(text(),'{label}')]/following-sibling::div//div[contains(@class,'stSelectbox')]")
        #         dropdown_box.click()
        #         time.sleep(0.3)
        #         opt = driver.find_element(By.XPATH, f"//div[@data-baseweb='menu']//div[text()='{choice}']")
        #         opt.click()
        #         time.sleep(0.2)
        #         print(f"[User-{user_id}] Dropdown '{label}' = {choice}")
        #     except Exception as e:
        #         raise Exception(f"[User-{user_id}] Gagal dropdown '{label}': {e}")

        # Klik tombol "Calculate"
        try:
            driver.find_element(By.XPATH, "//button[@class='st-emotion-cache-15hul6a ef3psqc16']").click()
            print(f"[User-{user_id}] Clicked Calculate")
            time.sleep(5)
        except Exception as e:
            raise Exception(f"[User-{user_id}] Gagal klik tombol Calculate: {e}")

        # Ambil hasil
        try:
            wait = WebDriverWait(driver, 10)
            result_elem = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-testid='stAlertContentSuccess']")))
            #result = driver.find_element(By.XPATH, "//div[@data-testid='stAlertContentSuccess']").text
            result = result_elem.text
            score = float(result.split(":")[1].replace("%", "").strip())
            print(f"[User-{user_id}] Result = {score}%")
        except Exception as e:
            raise Exception(f"[User-{user_id}] Gagal membaca hasil: {e}")

        end_time = time.time()
        duration = round(end_time - start_time, 2)

        queue.put((user_id, "SUCCESS", score, duration))
        driver.quit()
    except Exception as e:
        print(f"[User-{user_id}] ❌ ERROR:\n{traceback.format_exc()}")
        queue.put((user_id, "FAILED", None, None))

def main():
    print("🔄 Memulai uji skalabilitas paralel...")
    processes = []
    q = Queue()

    for i in range(N_USER):
        p = Process(target=run_test, args=(i + 1, q))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    results = []
    while not q.empty():
        results.append(q.get())

    print("\n📊 Hasil Uji Skalabilitas:")
    success_durations = []
    for uid, status, score, dur in sorted(results):
        if status == "SUCCESS":
            print(f"User-{uid}: ✅ Score = {score}%, Time = {dur}s")
            success_durations.append(dur)
        else:
            print(f"User-{uid}: ❌ Gagal")

    if success_durations:
        print("\n📈 Statistik:")
        print(f"Rata-rata waktu respon: {round(statistics.mean(success_durations), 2)} detik")
        print(f"Max: {max(success_durations)} s | Min: {min(success_durations)} s | Jumlah sukses: {len(success_durations)} dari {N_USER}")
    else:
        print("❌ Tidak ada simulasi yang berhasil.")

if __name__ == "__main__":
    main()
