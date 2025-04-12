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
redial_counts = {}  # Track redial clicks per campaign
campaigns = []  # Store campaign names
current_keyword = None  # Track the current keyword to detect changes

options = Options()
options.add_experimental_option("excludeSwitches", ["enable-logging"])

# Environment URLs
ENVIRONMENTS = {
    "Environment 1": "https://texxen-voliapp.spmadridph.com/admin",
    "Environment 2": "https://texxen-voliappe2.spmadridph.com/admin",
    "Environment 3": "https://texxen-voliappe3.spmadridph.com/admin"
}

def is_8pm_philippine_time():
    ph_tz = pytz.timezone('Asia/Manila')
    return datetime.now(ph_tz).hour >= 20

def initialize_driver():
    global driver
    if driver is not None:
        try:
            driver.quit()
        except:
            pass
    driver = webdriver.Chrome(options=options)
    return driver

def auto_redial(username, password, keyword, environment_url):
    global running, driver, redial_counts, campaigns
    while running and not is_8pm_philippine_time():
        try:
            driver = initialize_driver()
            wait = WebDriverWait(driver, 15)
            driver.get(environment_url)

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
                    campaigns = [opt['text'] for opt in options if keyword in opt['text']]
                    for campaign in campaigns:
                        if campaign not in redial_counts:
                            redial_counts[campaign] = 0
                    update_campaign_list()

                    for option in options:
                        if not running or is_8pm_philippine_time():
                            break

                        if keyword not in option['text']:
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

def save_keyword(keyword):
    with open("keyword.txt", "w") as f:
        f.write(keyword)

def load_keyword():
    try:
        with open("keyword.txt", "r") as f:
            keyword = f.read().strip()
            if keyword:
                keyword_entry.delete(0, tk.END)
                keyword_entry.insert(0, keyword)
    except FileNotFoundError:
        pass

def save_environment(environment):
    with open("environment.txt", "w") as f:
        f.write(environment)

def load_environment():
    try:
        with open("environment.txt", "r") as f:
            environment = f.read().strip()
            if environment in ENVIRONMENTS:
                environment_var.set(environment)
    except FileNotFoundError:
        environment_var.set("Environment 2")  # Default to Environment 2

def on_environment_change(*args):
    """Save environment immediately when selection changes."""
    save_environment(environment_var.get())

def start_automation():
    global running, redial_counts, campaigns, current_keyword
    username = username_entry.get()
    password = password_entry.get()
    keyword = keyword_entry.get().strip()
    environment = environment_var.get()
    environment_url = ENVIRONMENTS.get(environment)

    if not username or not password:
        messagebox.showerror("Error", "Please enter username and password!", parent=root)
        return
    if not keyword:
        messagebox.showerror("Error", "Please enter a campaign keyword!", parent=root)
        return
    if not environment:
        messagebox.showerror("Error", "Please select an environment!", parent=root)
        return
    if not running:
        # Check if keyword has changed
        if current_keyword != keyword:
            campaigns.clear()
            redial_counts.clear()
            current_keyword = keyword
        save_keyword(keyword)
        update_campaign_list()
        running = True
        status_label.config(text="Status: Running", foreground="#00ff00")
        threading.Thread(target=lambda: auto_redial(username, password, keyword, environment_url), daemon=True).start()
    else:
        messagebox.showinfo("Info", "Automation is already running!", parent=root)

def stop_automation():
    global running, driver
    if running:
        running = False
        status_label.config(text="Status: Stopped", foreground="#ff3333")
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
    for campaign in campaigns:
        count = redial_counts.get(campaign, 0)
        campaign_list.insert(tk.END, f"{campaign} - Redials: {count}")

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

# Button hover effects
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

# GUI Setup
root = tk.Tk()
root.title("Auto Redial Application")
root.state('zoomed')
root.configure(bg="#1a1a1a")

try:
    root.iconbitmap("futuristic_icon.ico")
except:
    pass

# Style configuration
style = ttk.Style()
style.theme_use("clam")

style.configure("TButton", background="#333333", foreground="#00ccff", font=("Orbitron", 12), borderwidth=1, relief="flat", padding=10)
style.map("TButton", background=[("active", "#444444")])
style.configure("Hover.TButton", background="#00ccff", foreground="#1a1a1a", font=("Orbitron", 12), borderwidth=1, relief="flat", padding=10)
style.configure("TEntry", fieldbackground="#2a2a2a", foreground="#ffffff", font=("Orbitron", 12), borderwidth=1, relief="flat", padding=5)
style.configure("Vertical.TScrollbar", background="#333333", troughcolor="#1a1a1a", arrowcolor="#00ccff")

# Main Frame
main_frame = tk.Frame(root, bg="#1a1a1a")
main_frame.pack(padx=20, pady=20, fill="both", expand=True)

# Header
header_label = tk.Label(main_frame, text="Auto Redial Dashboard", font=("Orbitron", 28, "bold"), bg="#1a1a1a", fg="#00ccff")
header_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

# Credentials Frame
cred_frame = tk.Frame(main_frame, bg="#2a2a2a", bd=2, relief="flat", highlightbackground="#00ccff", highlightcolor="#00ccff", highlightthickness=1)
cred_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

tk.Label(cred_frame, text="Username:", font=("Orbitron", 12), bg="#2a2a2a", fg="#ffffff").grid(row=0, column=0, padx=10, pady=5, sticky="e")
username_entry = ttk.Entry(cred_frame, width=30, style="TEntry")
username_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(cred_frame, text="Password:", font=("Orbitron", 12), bg="#2a2a2a", fg="#ffffff").grid(row=1, column=0, padx=10, pady=5, sticky="e")
password_entry = ttk.Entry(cred_frame, width=30, show="*", style="TEntry")
password_entry.grid(row=1, column=1, padx=10, pady=5)

# Environment Selection
tk.Label(cred_frame, text="Environment:", font=("Orbitron", 12), bg="#2a2a2a", fg="#ffffff").grid(row=2, column=0, padx=10, pady=5, sticky="e")
environment_frame = tk.Frame(cred_frame, bg="#2a2a2a")
environment_frame.grid(row=2, column=1, padx=10, pady=5, sticky="w")
environment_var = tk.StringVar(value="Environment 2")  # Default to Environment 2
environment_var.trace("w", on_environment_change)  # Save environment when selection changes
for idx, env in enumerate(ENVIRONMENTS.keys()):
    tk.Radiobutton(environment_frame, text=env, variable=environment_var, value=env, bg="#2a2a2a", fg="#ffffff", selectcolor="#2a2a2a", font=("Orbitron", 10), activebackground="#2a2a2a", activeforeground="#00ccff").grid(row=0, column=idx, padx=5)

save_button = ttk.Button(cred_frame, text="Save Credentials", command=save_credentials, style="TButton")
save_button.grid(row=3, column=0, columnspan=2, pady=10)
save_button.bind("<Enter>", on_enter_save)
save_button.bind("<Leave>", on_leave_save)

# Control Frame
control_frame = tk.Frame(main_frame, bg="#1a1a1a")
control_frame.grid(row=2, column=0, columnspan=2, pady=10)

tk.Label(control_frame, text="Campaign Keyword:", font=("Orbitron", 12), bg="#1a1a1a", fg="#ffffff").grid(row=0, column=0, padx=10, pady=5, sticky="e")
keyword_entry = ttk.Entry(control_frame, width=30, style="TEntry")
keyword_entry.grid(row=0, column=1, padx=10, pady=5)

run_button = ttk.Button(control_frame, text="Run", command=start_automation, width=15, style="TButton")
run_button.grid(row=1, column=0, padx=5, pady=5)
run_button.bind("<Enter>", on_enter_run)
run_button.bind("<Leave>", on_leave_run)

stop_button = ttk.Button(control_frame, text="Stop", command=stop_automation, width=15, style="TButton")
stop_button.grid(row=1, column=1, padx=5, pady=5)
stop_button.bind("<Enter>", on_enter_stop)
stop_button.bind("<Leave>", on_leave_stop)

# Status Frame
status_frame = tk.Frame(main_frame, bg="#1a1a1a")
status_frame.grid(row=3, column=0, columnspan=2, pady=10)

status_label = tk.Label(status_frame, text="Status: Stopped", font=("Orbitron", 14), bg="#1a1a1a", fg="#ff3333")
status_label.pack()

# Campaign Frame
campaign_frame = tk.Frame(main_frame, bg="#2a2a2a", bd=2, relief="flat", highlightbackground="#00ccff", highlightcolor="#00ccff", highlightthickness=1)
campaign_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

campaign_label = tk.Label(campaign_frame, text="Campaigns", font=("Orbitron", 12, "bold"), bg="#2a2a2a", fg="#00ccff")
campaign_label.pack(anchor="w", padx=10, pady=5)

listbox_frame = tk.Frame(campaign_frame, bg="#2a2a2a")
listbox_frame.pack(fill="both", expand=True, padx=10, pady=5)

campaign_list = tk.Listbox(listbox_frame, height=15, width=80, font=("Orbitron", 11), bg="#2a2a2a", fg="#ffffff", bd=0, highlightthickness=0, selectbackground="#00ccff", selectforeground="#1a1a1a")
campaign_list.pack(side="left", fill="both", expand=True)

scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=campaign_list.yview, style="Vertical.TScrollbar")
scrollbar.pack(side="right", fill="y")
campaign_list.config(yscrollcommand=scrollbar.set)

# Configure grid weights for responsiveness
main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)
main_frame.rowconfigure(4, weight=1)

# Status Bar
status_bar = tk.Label(root, text="Auto Redial Application v1.0", bd=1, relief="flat", anchor="w", bg="#333333", fg="#00ccff", font=("Orbitron", 10))
status_bar.pack(side="bottom", fill="x")

# Load credentials, keyword, and environment
load_credentials()
load_keyword()
load_environment()
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()