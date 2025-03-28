import tkinter as tk
from tkinter import messagebox
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from selenium import webdriver
from datetime import datetime
import pytz
import threading

KEYWORD = "PD MC21"
driver = None
running = False

# Configure Chrome Options
options = Options()
options.add_experimental_option("excludeSwitches", ["enable-logging"])

# Function to check 8:00 PM Philippine time
def is_8pm_philippine_time():
    ph_tz = pytz.timezone('Asia/Manila')
    return datetime.now(ph_tz).hour >= 20

# Function to perform login with minimal delays
def perform_login(driver, is_restart=False):
    try:
        main_url = "https://texxen-voliappe2.spmadridph.com/admin"
        driver.get(main_url)
        wait = WebDriverWait(driver, 15)

        username_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Username']")))
        print("✅ Found username field")
        username_field.clear()
        username_field.send_keys("kpilustrisimo")
        print("✅ Entered username")

        password_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Password']")))
        print("✅ Found password field")
        password_field.clear()
        password_field.send_keys("$PMadr!d1234")
        print("✅ Entered password")

        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#normalLogin > button")))
        print("✅ Found login button")
        if is_restart:
            driver.execute_script("arguments[0].click();", login_button)  # Faster JS click on restart
            print("✅ Clicked login button (JS)")
        else:
            login_button.click()
            print("✅ Clicked login button")
            time.sleep(1)  # Only delay on initial login

        return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False

# Function to navigate to Predictive Dialer Monitor with minimal delays
def navigate_to_predictive_dialer(driver, is_restart=False):
    try:
        wait = WebDriverWait(driver, 15)
        parent_menu = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[1]/div/div/ul/li[3]")))
        parent_menu.click()
        print("✅ Clicked parent menu")

        predictive_dialer_monitor = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[1]/div/div/ul/li[3]/ul/li[2]/a")))
        predictive_dialer_monitor.click()
        print("✅ Clicked Predictive Dialer Monitor")
        if not is_restart:
            time.sleep(1)  # Only delay on initial navigation
        return True
    except Exception as e:
        print(f"Failed to navigate: {e}")
        return False

# Function to initialize a new driver
def initialize_driver():
    global driver
    if driver is not None:
        try:
            driver.quit()
        except:
            pass
    driver = webdriver.Chrome(options=options)
    return driver

# Function to automate redial with fast restart on error
def auto_redial():
    global running, driver
    while running and not is_8pm_philippine_time():
        try:
            driver = initialize_driver()
            if not perform_login(driver, is_restart=False) or not navigate_to_predictive_dialer(driver, is_restart=False):
                print("❌ Initial setup failed. Restarting immediately...")
                continue

            wait = WebDriverWait(driver, 15)
            while running and not is_8pm_philippine_time():
                try:
                    campaign_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div/div[2]/div/div[1]/div/select")))
                    driver.execute_script("arguments[0].scrollIntoView(true);", campaign_dropdown)
                    time.sleep(1)

                    options = driver.execute_script("return Array.from(arguments[0].options).map(option => ({value: option.value, text: option.text}));", campaign_dropdown)
                    print(f"Found {len(options)} campaigns: {[option['text'] for option in options]}")

                    for option in options:
                        if not running or is_8pm_philippine_time():
                            break

                        campaign_value = option['value']
                        campaign_text = option['text']

                        if KEYWORD not in campaign_text:
                            continue

                        print(f"\nProcessing campaign: {campaign_text} (Value: {campaign_value})")
                        time.sleep(1)

                        try:
                            driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", campaign_dropdown, campaign_value)
                            time.sleep(2)
                            new_value = campaign_dropdown.get_attribute('value')
                            if new_value != campaign_value:
                                raise Exception("Campaign switch failed")
                            print(f"✅ Selected campaign '{campaign_text}'")
                        except Exception as e:
                            print(f"❌ Failed to select campaign: {e}")
                            break

                        try:
                            dialed_element = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[2]/div/div[2]/div/div[2]/div/small[1]/span")))
                            total_element = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[2]/div/div[2]/div/div[2]/div/small[2]/span")))
                            time.sleep(1)

                            dialed = int(dialed_element.text.strip())
                            total = int(total_element.text.strip())
                            print(f"Dialed: {dialed}, Total: {total}")
                        except Exception as e:
                            print(f"❌ Failed to retrieve Dialed/Total: {e}")
                            break

                        if dialed >= total:
                            print(f"✅ Dialed equals Total. Proceeding to redial.")
                            try:
                                status_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div/div[3]/div/div[2]/div/div[1]/button/div/div")))
                                driver.execute_script("arguments[0].click();", status_dropdown)
                                print("✅ Clicked 'Choose call status'")
                                time.sleep(1)
                            except:
                                print("✅ Clicked 'Choose call status' (JS fallback)")

                            try:
                                status_option = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div/div[3]/div/div[2]/div/div[1]/div/div[2]/div/button[1]")))
                                driver.execute_script("arguments[0].click();", status_option)
                                print("✅ Selected status option")
                                time.sleep(1)
                            except:
                                print("✅ Selected status option (JS fallback)")

                            try:
                                redial_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div/div[3]/div/div[2]/div/div[2]/button")))
                                driver.execute_script("arguments[0].click();", redial_button)
                                print(f"✅ Redialed campaign '{campaign_text}'")
                                time.sleep(1)
                            except:
                                print(f"✅ Redialed campaign '{campaign_text}' (JS fallback)")
                        else:
                            print(f"❌ Dialed ({dialed}) < Total ({total})")

                    if running:
                        print("Waiting 2 seconds before next cycle...")
                        time.sleep(2)

                except Exception as e:
                    print(f"Unexpected error in main loop: {e}")
                    break

            if driver is not None:
                try:
                    driver.quit()
                except:
                    pass
            print("Restarting from login immediately...")

        except Exception as e:
            print(f"Critical error in auto_redial: {e}")
            if driver is not None:
                try:
                    driver.quit()
                except:
                    pass

    if is_8pm_philippine_time():
        print("🕗 It's 8:00 PM or later in Philippine time. Closing browser...")
        running = False
    if driver is not None:
        try:
            driver.quit()
        except:
            pass

# Start automation in a separate thread
def start_automation():
    global running, driver
    if not running:
        running = True
        status_label.config(text="Status: Running")
        threading.Thread(target=auto_redial, daemon=True).start()
    else:
        messagebox.showinfo("Info", "Automation is already running!")

# Stop automation
def stop_automation():
    global running, driver
    if running:
        running = False
        status_label.config(text="Status: Stopped")
        if driver is not None:
            try:
                driver.quit()
                driver = None
            except:
                pass
        messagebox.showinfo("Info", "Automation stopped.")
    else:
        messagebox.showinfo("Info", "Automation is not running!")

# GUI Setup
root = tk.Tk()
root.title("Auto Redial App")
root.geometry("300x150")

status_label = tk.Label(root, text="Status: Stopped")
status_label.pack(pady=10)

run_button = tk.Button(root, text="Run", command=start_automation)
run_button.pack(pady=5)

stop_button = tk.Button(root, text="Stop", command=stop_automation)
stop_button.pack(pady=5)

# Run the GUI
root.mainloop()