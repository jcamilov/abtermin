from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.common.exceptions import TimeoutException
import time
import sys
from datetime import datetime
import os
from notify import send_photo_notification, send_notification
from dotenv import load_dotenv

load_dotenv()   

URL = os.getenv('URL')  

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--headless') # to run in "invisible" mode
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"Failed to initialize Chrome: {str(e)}")
        try:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
                options=chrome_options
            )
        except Exception as e:
            print("Error: Could not initialize either Chrome or Chromium.")
            print("Please make sure either Google Chrome or Chromium is installed on your system.")
            print(f"Error details: {str(e)}")
            sys.exit(1)
    
    return driver

def wait_and_click(driver, wait, by, selector, message):
    print(message)
    try:
        element = wait.until(EC.element_to_be_clickable((by, selector)))
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
        # Try JavaScript click first
        try:
            driver.execute_script("arguments[0].click();", element)
        except:
            # If JavaScript click fails, try regular click
            element.click()
        return True
    except TimeoutException:
        print(f"Timeout waiting for element: {selector}")
        return False
    except Exception as e:
        print(f"Error clicking element: {str(e)}")
        return False

def select_dropdown_option(driver, wait, option_text):
    print(f"Looking for option: {option_text}")
    try:
        # Using the JavaScript approach that worked
        selector = f"//a[@data-option-name='{option_text}']"
        elements = driver.find_elements(By.XPATH, selector)
        if elements:
            driver.execute_script("arguments[0].click();", elements[0])
            print("Clicked element using JavaScript")
            return True
        return False
    except Exception as e:
        print(f"Error in select_dropdown_option: {str(e)}")
        return False

def save_screenshot(driver, filename, caption):
    """
    Save screenshot and send notification with the image
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshots/{timestamp}_{filename}.png"
    
    # Create screenshots directory if it doesn't exist
    os.makedirs("screenshots", exist_ok=True)
    
    # Save the screenshot
    driver.save_screenshot(screenshot_path)
    
    # Send notification with screenshot
    send_photo_notification(screenshot_path, caption)
    
    return screenshot_path

def keep_browser_open():
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nScript terminated by user. You can close the browser window now.")

def book_appointment():
    print("Starting the appointment booking process...")
    driver = setup_driver()
    wait = WebDriverWait(driver, 10)
    success = False
    
    try:
        # Navigate to the website
        print("Navigating to the website...")
        driver.get(URL)
        time.sleep(2)  # Wait for page to fully load
        
        # Click on "Ausländerbehörde - eAT-Ausgabe"
        if not wait_and_click(driver, wait, By.XPATH, 
                            "//span[contains(text(), 'Ausländerbehörde - eAT-Ausgabe')]",
                            "Clicking on section..."):
            raise Exception("Could not click on 'Ausländerbehörde - eAT-Ausgabe'")
        
        time.sleep(1)  # Wait for animation
        
        # Click the dropdown using its specific ID
        print("Opening options dropdown...")
        try:
            dropdown_button = wait.until(EC.element_to_be_clickable((By.ID, "process-options-dropdown-14_66")))
            driver.execute_script("arguments[0].scrollIntoView(true);", dropdown_button)
            time.sleep(0.5)
            dropdown_button.click()
            print("Dropdown clicked successfully")
            
            time.sleep(1)  # Wait for dropdown to open
            
            # Select the option
            if not select_dropdown_option(driver, wait, "1 Person und 2 Familienangehörige"):
                raise Exception("Could not select '1 Person und 2 Familienangehörige'")
            
        except Exception as e:
            print(f"Error with dropdown interaction: {str(e)}")
            raise
        
        time.sleep(1)  # Wait for selection to register
        
        # Click the first "Weiter" button
        if not wait_and_click(driver, wait, By.CSS_SELECTOR,
                            "a.btn_formcontroll_next[data-action='ota_form_control']",
                            "Clicking first 'Weiter' button..."):
            raise Exception("Could not click first 'Weiter' button")
        
        # Wait for confirmation page and take screenshot
        time.sleep(2)  # Wait for page to load
        # print("Taking screenshot of confirmation page...")
        # save_screenshot(driver, "confirmation_page")
        
        # Try to click the second "Weiter" button with a more specific selector
        print("Clicking second 'Weiter' button...")
        try:
            # Wait for the button to be present and visible
            weiter_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 
                "a.btn.btn-primary.btn-block.pull-left.btn_save.btn_formcontroll.btn_formcontroll_next[data-action='ota_form_control']")))
            
            # Scroll to the button
            driver.execute_script("arguments[0].scrollIntoView(true);", weiter_button)
            time.sleep(1)
            
            # Try JavaScript click first
            try:
                driver.execute_script("arguments[0].click();", weiter_button)
            except:
                # If JavaScript click fails, try regular click
                weiter_button.click()
            
            print("Second 'Weiter' button clicked successfully")
            time.sleep(2)
            
            # Check for the "no appointments" message
            try:
                no_appointments_msg = wait.until(EC.presence_of_element_located((
                    By.XPATH, "//div[@class='alert alert-danger']//strong[contains(text(), 'Keine verfügbaren Termine!')]"
                )))
                print("No appointments available")
                #save_screenshot(driver, "no_appointments", "Keine verfügbaren Termine / No appointments available yet")

            except TimeoutException:
                # This means the "no appointments" message was not found
                print("Possible appointments found!")
                save_screenshot(driver, "appointments_available", "Appointments available! Move fast!!!")
                send_notification(URL)
                
            except Exception as e:
                # This catches any other unexpected errors
                print(f"Error: {str(e)}")
                send_notification(f"❌ Error occurred while checking appointments: {str(e)}")
        
        except Exception as e:
            print(f"Error clicking second 'Weiter' button: {str(e)}")
            raise Exception("Could not click second 'Weiter' button")
        
        print("Process completed successfully!")
        success = True
        
    except Exception as e:
        print(f"An error occurred during the booking process:")
        print(f"Error details: {str(e)}")
        try:
            save_screenshot(driver, "error")
        except:
            pass
            
    driver.quit()
    if not success:
        print("Closing browser due to error...")
        return None
    else:
        print("Process finished successfully!")
        return driver

if __name__ == "__main__":
    # check if the current time is 8:01am ECT or earlier. If so, send a notification
    current_time = datetime.now().strftime("%H:%M")
    current_date = datetime.now().strftime("%d.%m.%Y")
    if current_time <= "08:04":
        send_notification("Starting the search for appointments on " + current_date)
    book_appointment()
