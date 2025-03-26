from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
from selenium import webdriver

KEYWORD = "PD MC21"
# Step 1: Configure Chrome Options
options = Options()
options.add_experimental_option("excludeSwitches", ["enable-logging"])

# Step 2: Launch WebDriver
print("Testing started...")
driver = webdriver.Chrome(options=options)
print("Automation script is running!")

# Step 3: Open the website
main_url = "https://texxen-voliappe2.spmadridph.com/admin"
driver.get(main_url)

# Step 4: Wait for the page to fully load
wait = WebDriverWait(driver, 15)

# Step 5: Automate Login with Debugging
try:
    # Locate username field
    username_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Username']")))
    print("✅ Found username field with placeholder='Username'")
    username_field.clear()
    username_field.send_keys("KK")
    print("✅ Entered username: KK")

    # Locate password field
    password_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Password']")))
    print("✅ Found password field with placeholder='Password'")
    password_field.clear()
    password_field.send_keys("$PMadr!d141")
    print("✅ Entered password: $PMadr!d141")

    # Locate and click login button
    login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#normalLogin > button")))
    print("✅ Found login button with selector '#normalLogin > button'")
    time.sleep(1)
    try:
        login_button.click()
        print("✅ Clicked 'Log in' button using standard click")
    except:
        driver.execute_script("arguments[0].click();", login_button)
        print("✅ Clicked 'Log in' button using JavaScript click")

    # Wait for the page to redirect after login
    time.sleep(1)

except Exception as e:
    print(f"Login failed: {e}")
    driver.quit()
    exit()

# Step 6: Navigate to Predictive Dialer Monitor
try:
    parent_menu = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[1]/div/div/ul/li[3]")))
    parent_menu.click()
    print("✅ Clicked parent menu item to expand submenu")
    time.sleep(1)

    predictive_dialer_monitor = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[1]/div/div/ul/li[3]/ul/li[2]/a")))
    predictive_dialer_monitor.click()
    print("✅ Clicked 'Predictive Dialer Monitor' using XPath.")

except Exception as e:
    print(f"Failed to click Predictive Dialer Monitor or parent menu: {e}")
    driver.quit()
    exit()

# Function to automate redial by looping through all campaigns in the dropdown
def auto_redial():
    try:
        # Step 1: Locate the campaign dropdown
        campaign_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div/div[2]/div/div[1]/div/select")))
        driver.execute_script("arguments[0].scrollIntoView(true);", campaign_dropdown)

        # Get all options in the dropdown
        options = driver.execute_script("return Array.from(arguments[0].options).map(option => ({value: option.value, text: option.text}));", campaign_dropdown)
        print(f"Found {len(options)} campaigns in the dropdown: {[option['text'] for option in options]}")

        # Loop through each campaign in the dropdown
        for option in options:
            campaign_value = option['value']
            campaign_text = option['text']
            print(f"\nProcessing campaign: {campaign_text} (Value: {campaign_value})")

            if KEYWORD not in campaign_text:
                print(f"❌ Campaign '{campaign_text}' does not contain the keyword '{KEYWORD}'. Skipping.")
                continue

            print(f"✅ Campaign '{campaign_text}' matches the keyword '{KEYWORD}'. Proceeding to check Dialed/Total.")
            # Select the campaign
            try:
                driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", campaign_dropdown, campaign_value)
                print(f"✅ Selected campaign '{campaign_text}' (Value: {campaign_value}) from dropdown")
            except Exception as e:
                print(f"❌ Failed to select campaign '{campaign_text}': {e}")
                continue

            # Wait for the page to update after selecting the campaign
            time.sleep(2)

            # Step 2: Get the "Dialed" and "Total" values
            try:
                dialed_element = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[2]/div/div[2]/div/div[2]/div/small[1]/span")))
                total_element = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div[2]/div/div[2]/div/div[2]/div/small[2]/span")))

                dialed = int(dialed_element.text.strip())
                total = int(total_element.text.strip())
                print(f"Dialed: {dialed}, Total: {total}")
            except Exception as e:
                print(f"❌ Failed to retrieve Dialed/Total values for campaign '{campaign_text}': {e}")
                continue

            # Step 3: Check if Dialed equals Total
            if dialed >= total:
                print(f"✅ Dialed equals Total for campaign '{campaign_text}'. Proceeding to redial.")

                # Step 4: Click the "Choose call status" dropdown
                try:
                    status_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div/div[3]/div/div[2]/div/div[1]/button/div/div")))
                    driver.execute_script("arguments[0].scrollIntoView(true);", status_dropdown)
                    try:
                        status_dropdown.click()
                        print("✅ Clicked 'Choose call status' dropdown using full XPath '/html/body/div[2]/div[2]/div/div[3]/div/div[2]/div/div[1]/button/div/div'")
                    except:
                        driver.execute_script("arguments[0].click();", status_dropdown)
                        print("✅ Clicked 'Choose call status' dropdown using JavaScript click with full XPath")
                except Exception as e:
                    print(f"❌ Failed to click 'Choose call status' dropdown for campaign '{campaign_text}': {e}")
                    continue

                # Step 5: Select the first option from the dropdown menu
                try:
                    status_option = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div/div[3]/div/div[2]/div/div[1]/div/div[2]/div/button[1]")))
                    driver.execute_script("arguments[0].scrollIntoView(true);", status_option)
                    try:
                        status_option.click()
                        print("✅ Selected first option from 'Choose call status' dropdown using full XPath '/html/body/div[2]/div[2]/div/div[3]/div/div[2]/div/div[1]/div/div[2]/div/button[1]'")
                    except:
                        driver.execute_script("arguments[0].click();", status_option)
                        print("✅ Selected first option from 'Choose call status' dropdown using JavaScript click with full XPath")
                except Exception as e:
                    print(f"❌ Failed to select first option from 'Choose call status' dropdown for campaign '{campaign_text}': {e}")
                    continue

                time.sleep(1)  # Wait for the selection to register

                # Step 5: Click the Redial button
                try:
                    redial_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div/div[3]/div/div[2]/div/div[2]/button")))
                    driver.execute_script("arguments[0].scrollIntoView(true);", redial_button)
                    try:
                        redial_button.click()
                        print(f"✅ Redialed campaign '{campaign_text}' using full XPath '/html/body/div[2]/div[2]/div/div[3]/div/div[2]/div/div[2]/button'")
                    except:
                        driver.execute_script("arguments[0].click();", redial_button)
                        print(f"✅ Redialed campaign '{campaign_text}' using JavaScript click with full XPath")
                except Exception as e:
                    print(f"❌ Failed to click 'Redial' button for campaign '{campaign_text}': {e}")
                    continue

                # Wait for the redial to process
                time.sleep(1)
            else:
                print(f"❌ Dialed ({dialed}) does not equal Total ({total}) for campaign '{campaign_text}'. Moving to the next campaign.")

    except Exception as e:
        print(f"An error occurred during redial process: {e}")

# Run continuously every 5 seconds
try:
    while True:
        auto_redial()
        print("Waiting 1 seconds before the next cycle...")
        time.sleep(2)  # Check every minute
except KeyboardInterrupt:
    print("Automation stopped by user.")
    driver.quit()

# Close browser when script ends
driver.quit()
print("Browser closed")