import tkinter as tk
from tkinter import messagebox, ttk
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from selenium import webdriver
from datetime import datetime
import pytz
import threading
import os

driver = None
running = False
redial_counts = {}
campaigns = []
current_keyword = None

options = Options()
options.add_experimental_option("excludeSwitches", ["enable-logging"])

ENV_LINKS = {
    "Envi 1": "https://texxen-voliapp.spmadridph.com/admin",
    "Envi 2": "https://texxen-voliappe2.spmadridph.com/admin",
    "Envi 3": "https://texxen-voliappe3.spmadridph.com/admin"
}

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
        username_field.send_keys("KK")
        print("✅ KK")

        password_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Password']")))
        print("✅ Found password field")
        password_field.clear()
        password_field.send_keys("$PMadr!d141")
        print("✅ $PMadr!d141")

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

# Function to initialize a new drivers
def initialize_driver():
    global driver
    if driver is not None:
        try:
            driver.quit()
        except:
            pass
    driver = webdriver.Chrome(options=options)
    return driver

def auto_redial(username, password, keywords_input, env_link):
    global running, driver, redial_counts, campaigns
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
    if not keywords:
        return

    while running and not is_8pm_philippine_time():
        try:
            driver = initialize_driver()
            wait = WebDriverWait(driver, 15)
            driver.get(env_link)

            wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Username']"))).send_keys(username)
            wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Password']"))).send_keys(password)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#normalLogin > button"))).click()
            time.sleep(1)

            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[1]/div/div/ul/li[3]"))).click()
            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[1]/div/div/ul/li[3]/ul/li[2]/a"))).click()
            time.sleep(1)

            while running and not is_8pm_philippine_time():
                try:
                    campaign_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div/div[2]/div/div[1]/div/select")))
                    driver.execute_script("arguments[0].scrollIntoView(true);", campaign_dropdown)

                    options = driver.execute_script("return Array.from(arguments[0].options).map(option => ({value: option.value, text: option.text}));", campaign_dropdown)
                    campaigns = []
                    for opt in options:
                        for keyword in keywords:
                            if keyword in opt['text'] and opt['text'] not in campaigns:
                                campaigns.append(opt['text'])
                                break
                    for campaign in campaigns:
                        if campaign not in redial_counts:
                            redial_counts[campaign] = 0
                    update_campaign_list()

                    for option in options:
                        if not running or is_8pm_philippine_time():
                            break
                        matches_keyword = False
                        for keyword in keywords:
                            if keyword in option['text']:
                                matches_keyword = True
                                break
                        if not matches_keyword:
                            continue

                        current_campaign = option['text']
                        driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", campaign_dropdown, option['value'])
                        time.sleep(1)

                        dialed = int(wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[2]/div/div[2]/div/div[2]/div/small[1]/span"))).text.strip())
                        total = int(wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[2]/div/div[2]/div/div[2]/div/small[2]/span"))).text.strip())

                        if dialed >= total:
                            try:
                                status_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div/div[3]/div/div[2]/div/div[1]/button/div/div")))
                                driver.execute_script("arguments[0].click();", status_dropdown)
                                time.sleep(1)

                                status_option = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div/div[3]/div/div[2]/div/div[1]/div/div[2]/div/button[1]")))
                                driver.execute_script("arguments[0].click();", status_option)
                                time.sleep(1)

                                redial_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div/div[3]/div/div[2]/div/div[2]/button")))
                                driver.execute_script("arguments[0].click();", redial_button)
                                redial_counts[current_campaign] += 1
                                update_campaign_list()
                                time.sleep(2)
                            except:
                                continue
                    time.sleep(1)
                except:
                    break
            if driver:
                driver.quit()
        except:
            if driver:
                driver.quit()
    running = False
    if driver:
        driver.quit()

def save_credentials():
    username = username_entry.get()
    password = password_entry.get()
    if username and password:
        with open("credentials.txt", "w") as f:
            f.write(f"{username}\n{password}")
        messagebox.showinfo("Info", "Credentials saved!", parent=root)
    else:
        messagebox.showerror("Error", "Please enter both username and password!", parent=root)

def load_credentials():
    try:
        with open("credentials.txt", "r") as f:
            lines = f.readlines()
            if len(lines) >= 2:
                username_entry.insert(0, lines[0].strip())
                password_entry.insert(0, lines[1].strip())
    except FileNotFoundError:
        pass

def save_keyword(keywords_input):
    with open("keyword.txt", "w") as f:
        f.write(keywords_input)

def load_keyword():
    try:
        with open("keyword.txt", "r") as f:
            keywords_input = f.read().strip()
            if keywords_input:
                keyword_entry.delete(0, tk.END)
                keyword_entry.insert(0, keywords_input)
    except FileNotFoundError:
        pass

def save_environment(selected_env):
    with open("environment.txt", "w") as f:
        f.write(selected_env)

def load_environment():
    try:
        with open("environment.txt", "r") as f:
            selected_env = f.read().strip()
            if selected_env in env_vars:
                for env, var in env_vars.items():
                    var.set(env == selected_env)
    except FileNotFoundError:
        env_vars["Envi 1"].set(True)  # Default to Envi 1 if no file exists

def toggle_env(var, env):
    for e, v in env_vars.items():
        if e != env:
            v.set(False)
    if not var.get():
        var.set(True)
    save_environment(selected_env=env)  # Save the selected environment

def start_automation():
    global running, redial_counts, campaigns, current_keyword
    username = username_entry.get()
    password = password_entry.get()
    keywords_input = keyword_entry.get().strip()
    if not username or not password:
        messagebox.showerror("Error", "Please enter username and password!", parent=root)
        return
    if not keywords_input:
        messagebox.showerror("Error", "Please enter at least one campaign keyword!", parent=root)
        return
    keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
    if not keywords:
        messagebox.showerror("Error", "Please enter valid campaign keywords!", parent=root)
        return
    selected_env = None
    for env, var in env_vars.items():
        if var.get():
            selected_env = env
            break
    if not selected_env:
        messagebox.showerror("Error", "Please select an environment!", parent=root)
        return
    env_link = ENV_LINKS[selected_env]
    if not running:
        if current_keyword != keywords_input:
            campaigns.clear()
            redial_counts.clear()
            current_keyword = keywords_input
        save_keyword(keywords_input)
        update_campaign_list()
        running = True
        status_label.config(text="Status: Running", bg="#1a3c34", fg="#00ff00")
        threading.Thread(target=lambda: auto_redial(username, password, keywords_input, env_link), daemon=True).start()
    else:
        messagebox.showinfo("Info", "Automation is already running!", parent=root)

def stop_automation():
    global running, driver
    if running:
        running = False
        status_label.config(text="Status: Stopped", bg="#3c1a1a", fg="#ff3333")
        if driver:
            try:
                driver.quit()
            except:
                pass
        messagebox.showinfo("Info", "Automation stopped.", parent=root)
    else:
        messagebox.showinfo("Info", "Automation is not running!", parent=root)

def update_campaign_list():
    campaign_list.delete(0, tk.END)
    for i, campaign in enumerate(campaigns):
        count = redial_counts.get(campaign, 0)
        campaign_list.insert(tk.END, f"{campaign} - Redials: {count}")
        campaign_list.itemconfig(i, {'bg': '#2a2a2a' if i % 2 == 0 else '#333333'})

def on_enter_run(e):
    run_button.config(style="Hover.TButton")

def on_leave_run(e):
    run_button.config(style="TButton")

def on_enter_stop(e):
    stop_button.config(style="Hover.TButton")

def on_leave_stop(e):
    stop_button.config(style="TButton")

def on_enter_save(e):
    save_button.config(style="Hover.TButton")

def on_leave_save(e):
    save_button.config(style="TButton")

def on_closing():
    global running, driver
    if running:
        running = False
        if driver:
            try:
                driver.quit()
            except:
                pass
    root.destroy()

# GUI Setup
root = tk.Tk()
root.title("Auto Redial Application")
root.state('zoomed')

root.configure(bg="#1c2526")

try:
    root.iconbitmap("app_icon.ico")
except:
    pass

style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", background="#00ccff", foreground="#ffffff", font=("Montserrat", 12, "bold"), borderwidth=0, relief="flat", padding=10)
style.map("TButton", background=[("active", "#00b3e6")])
style.configure("Hover.TButton", background="#ff00ff", foreground="#ffffff", font=("Montserrat", 12, "bold"), borderwidth=0, relief="flat", padding=10)
style.configure("TEntry", fieldbackground="#2a2a2a", foreground="#ffffff", font=("Montserrat", 12), borderwidth=0, relief="flat", padding=8)
style.configure("Vertical.TScrollbar", background="#00ccff", troughcolor="#1c2526", arrowcolor="#ffffff")
style.configure("TCheckbutton", background="#1c2526", foreground="#ffffff", font=("Montserrat", 12), indicatorcolor="#2a2a2a", indicatorbackground="#2a2a2a")
style.map("TCheckbutton", background=[("active", "#1c2526")], foreground=[("active", "#00ccff")], indicatorcolor=[("selected", "#00ccff")])

main_frame = tk.Frame(root, bg="#1c2526")
main_frame.pack(padx=30, pady=30, fill="both", expand=True)

header_label = tk.Label(main_frame, text="Auto Redial Dashboard", font=("Montserrat", 28, "bold"), bg="#1c2526", fg="#00ccff")
header_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))

# Credentials Frame (Compact size)
cred_frame = tk.Frame(main_frame, bg="#2a2a2a", bd=0, relief="flat")
cred_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
cred_frame.configure(highlightbackground="#00ccff", highlightcolor="#00ccff", highlightthickness=1)

tk.Label(cred_frame, text="Username:", font=("Montserrat", 12), bg="#2a2a2a", fg="#ffffff").grid(row=0, column=0, padx=10, pady=5, sticky="e")
username_entry = ttk.Entry(cred_frame, width=20, style="TEntry")  # Reduced width
username_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(cred_frame, text="Password:", font=("Montserrat", 12), bg="#2a2a2a", fg="#ffffff").grid(row=1, column=0, padx=10, pady=5, sticky="e")
password_entry = ttk.Entry(cred_frame, width=20, show="*", style="TEntry")  # Reduced width
password_entry.grid(row=1, column=1, padx=10, pady=5)

save_button = ttk.Button(cred_frame, text="Save Credentials", command=save_credentials, style="TButton")
save_button.grid(row=2, column=0, columnspan=2, pady=10)
save_button.bind("<Enter>", on_enter_save)
save_button.bind("<Leave>", on_leave_save)

# Environment Selection Frame
env_frame = tk.Frame(main_frame, bg="#2a2a2a", bd=0, relief="flat")
env_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
env_frame.configure(highlightbackground="#00ccff", highlightcolor="#00ccff", highlightthickness=1)

tk.Label(env_frame, text="Select Environment:", font=("Montserrat", 12, "bold"), bg="#2a2a2a", fg="#00ccff").grid(row=0, column=0, columnspan=3, padx=15, pady=10)

env_vars = {
    "Envi 1": tk.BooleanVar(value=True),
    "Envi 2": tk.BooleanVar(value=False),
    "Envi 3": tk.BooleanVar(value=False)
}
for i, (env, var) in enumerate(env_vars.items(), start=1):
    cb = ttk.Checkbutton(env_frame, text=env, variable=var, command=lambda v=var, e=env: toggle_env(v, e), style="TCheckbutton")
    cb.grid(row=1, column=i-1, padx=10, pady=5, sticky="w")

# Campaign Frame (Increased size)
campaign_frame = tk.Frame(main_frame, bg="#2a2a2a", bd=0, relief="flat")
campaign_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
campaign_frame.configure(highlightbackground="#00ccff", highlightcolor="#00ccff", highlightthickness=1)

campaign_label = tk.Label(campaign_frame, text="Campaigns", font=("Montserrat", 12, "bold"), bg="#2a2a2a", fg="#00ccff")
campaign_label.pack(anchor="w", padx=15, pady=10)

listbox_frame = tk.Frame(campaign_frame, bg="#2a2a2a")
listbox_frame.pack(fill="both", expand=True, padx=15, pady=5)

campaign_list = tk.Listbox(listbox_frame, height=25, width=100, font=("Montserrat", 11), bg="#2a2a2a", fg="#ffffff", bd=0, highlightthickness=0, selectbackground="#00ccff", selectforeground="#ffffff")  # Increased height and width
campaign_list.pack(side="left", fill="both", expand=True)

scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=campaign_list.yview, style="Vertical.TScrollbar")
scrollbar.pack(side="right", fill="y")
campaign_list.config(yscrollcommand=scrollbar.set)

# Control Frame (Moved to bottom)
control_frame = tk.Frame(main_frame, bg="#1c2526")
control_frame.grid(row=4, column=0, columnspan=2, pady=20)

tk.Label(control_frame, text="Campaign Keyword:", font=("Montserrat", 12), bg="#1c2526", fg="#ffffff").grid(row=0, column=0, padx=15, pady=10, sticky="e")
keyword_entry = ttk.Entry(control_frame, width=30, style="TEntry")
keyword_entry.grid(row=0, column=1, padx=15, pady=10)

run_button = ttk.Button(control_frame, text="Run", command=start_automation, width=15, style="TButton")
run_button.grid(row=1, column=0, padx=10, pady=10)
run_button.bind("<Enter>", on_enter_run)
run_button.bind("<Leave>", on_leave_run)

stop_button = ttk.Button(control_frame, text="Stop", command=stop_automation, width=15, style="TButton")
stop_button.grid(row=1, column=1, padx=10, pady=10)
stop_button.bind("<Enter>", on_enter_stop)
stop_button.bind("<Leave>", on_leave_stop)

# Status Frame (Moved to bottom)
status_frame = tk.Frame(main_frame, bg="#1c2526")
status_frame.grid(row=5, column=0, columnspan=2, pady=20)

status_label = tk.Label(status_frame, text="Status: Stopped", font=("Montserrat", 14, "bold"), bg="#3c1a1a", fg="#ff3333", padx=20, pady=5, relief="flat", borderwidth=1, highlightbackground="#ff3333", highlightcolor="#ff3333", highlightthickness=1)
status_label.pack()

# Configure grid weights for responsiveness
main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)
main_frame.rowconfigure(3, weight=3)  # Increased weight for Campaigns section

# Status Bar
status_bar = tk.Label(root, text="Auto Redial Application v1.0", bd=0, relief="flat", anchor="w", bg="#1c2526", fg="#00ccff", font=("Montserrat", 10))
status_bar.pack(side="bottom", fill="x", padx=20, pady=5)

# Load credentials, keyword, and environment
load_credentials()
load_keyword()
load_environment()
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()