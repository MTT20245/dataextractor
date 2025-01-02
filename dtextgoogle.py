import tkinter as tk
from tkinter import messagebox, Scrollbar, filedialog
from tkinter import ttk
from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import os
import re
import threading
import requests
import platform
import random
import string
from datetime import datetime
import uuid 
import time
import json
import base64
import openpyxl 
import subprocess

# Constants for the API URLs
ADMIN_SERVER_URL = "https://newmarketing.mediatechtemple.com/_api/userapi/get-api/"
DATA_SEND_URL = "https://newmarketing.mediatechtemple.com/_api/userapi/get-api/"

decoded_config_data = None  # Declare a global variable outside the class
business_list = None

class LicenseManager:
    def __init__(self):
        self.mac_address = self.get_mac_address()  # Get the machine's unique identifier (MAC Address)

    def get_mac_address(self):
        """Retrieve the MAC address of the machine."""
        mac = hex(uuid.getnode()).replace('0x', '').upper()
        return ':'.join(mac[i:i + 2] for i in range(0, 12, 2))

            
    def read_config_file(self):
        """Reads and decodes the Base64-encoded config.txt file and returns its contents as a dictionary."""
        global decoded_config_data  # Access the global variable

        config_file_path = os.path.join(os.getcwd(), 'config.txt')
        
        try:
            with open(config_file_path, "r") as file:
                # Read the Base64-encoded content
                encoded_config_data = file.read()

            # Decode the Base64 content
            decoded_config_data = base64.b64decode(encoded_config_data).decode('utf-8')

            # Parse the decoded data into a dictionary
            config_dict = {}
            for line in decoded_config_data.splitlines():
                if "=" in line:  # Only process lines with key=value format
                    key, value = line.split("=", 1)  # Split only on the first '='
                    config_dict[key.strip()] = value.strip()

            return config_dict

        except FileNotFoundError:
            print("Config file not found.")
            return None
        except base64.binascii.Error:
            print("Error decoding the Base64 config file. Please check the file format.")
            return None
        except Exception as e:
            print(f"Unexpected error reading config file: {e}")
            return None

    def validate_license(self, user_license_key):
        """Validates the license key by sending it to the server."""
        url = ADMIN_SERVER_URL
        
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
        }
        
        # Simulate sending a license key and mac_address
        data = {
            "license_key": user_license_key,
            "mac_address": self.mac_address,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current timestamp
        }
        
        try:
            # Send a POST request to validate the license key
            response = requests.post(url, json=data, headers=headers)
            print(f"Response Text: {response.text}")
            if response.status_code == 200:
                response_json = response.json()
                if response_json.get("status") == "success":
                    return response_json
                else:
                    return {"error": response_json["message"]}
            else:
                return {"error": f"Failed to validate license. Status code: {response.status_code}"}
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to the API: {e}")
            return {"error": str(e)}

    def send_machine_data(self, license_key):
        """Sends machine data (mac address, license key, timestamp) to the admin's portal."""
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_payload = {
            "mac_address": self.mac_address,
            "license_key": license_key,  # Include license key in the payload
            "timestamp": current_datetime
        }
        
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
        }

        try: 
            response = requests.post(DATA_SEND_URL, json=data_payload, headers=headers)
            if response.status_code == 200:
                print("Machine data sent successfully.")
            else:
                print(f"Failed to send data. Status Code: {response.status_code}\n{response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending machine data: {e}")

    def write_config_file(self, auth_token, license_key, remaining_days, user_type):
        """
        Writes registration details to config.txt, updates `remain_days` based on time, and overwrites the file.
        
        Args:
            auth_token (str): Authorization token.
            license_key (str): License key.
            remaining_days (int): Remaining days of validity.
            user_type (str): Type of user.
        """
        config_file_path = os.path.join(os.getcwd(), 'config.txt')


        try:
            # Check if the config file already exists
            if os.path.exists(config_file_path):
                # Decode and read existing data to retrieve the last write time and remaining days
                with open(config_file_path, 'r') as f:
                    encoded_content = f.read()
                    decoded_content = base64.b64decode(encoded_content).decode('utf-8')

                # Parse the existing config data
                lines = decoded_content.splitlines()
                last_write_time = None
                for line in lines:
                    if line.startswith("last_write_time="):
                        last_write_time = datetime.strptime(line.split('=')[1], '%Y-%m-%d %H:%M:%S')
                    elif line.startswith("remaining_days="):
                        remaining_days = int(line.split('=')[1])  # Ensure remain_days is converted to an integer

                if last_write_time:
                    # Calculate elapsed time and reduce remaining days
                    elapsed_days = (datetime.now() - last_write_time).days
                    remaining_days = max(0, int(remaining_days) - elapsed_days)  # Convert remain_days again, just to be safe

            # Stop if remain_days is already zero
            remaining_days = int(remaining_days)  # Final conversion to integer before comparison
            if remaining_days <= 0:
                print("No remaining days left. Config file will not be updated.")
                return

            # Prepare the data to be written to the config file
            config_data = f"Registration_number={self.mac_address}\n"
            config_data += f"auth_token={auth_token}\n"
            config_data += f"license_key={license_key}\n"
            config_data += f"remaining_days={remaining_days}\n"
            config_data += f"user_type={user_type}\n"
            config_data += f"last_write_time={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

            # Adding dummy data as placeholders (for illustration)
            for _ in range(10):
                dummy_key = ''.join(random.choices(string.ascii_letters + string.digits, k=100))
                dummy_value = ''.join(random.choices(string.ascii_letters + string.digits, k=116))
                config_data += f"{dummy_key}={dummy_value}\n"

            # Encode the config data in Base64
            encoded_config_data = base64.b64encode(config_data.encode('utf-8')).decode('utf-8')

            # Write the encoded content to the config file
            with open(config_file_path, 'w') as f:
                f.write(encoded_config_data)

            # Change the file to read-only (chmod 444 means read-only for all users)
            os.chmod(config_file_path, 0o444)

            print(f"Config file successfully written and encoded in Base64 at {config_file_path}")

        except Exception as e:
            print(f"Error writing config file: {e}")
        except OSError as e:
            print(f"Error with file system (permission issue?): {e}")

class RegistrationApp:
    def __init__(self, license_manager, on_registration_complete):
        self.license_manager = license_manager
        self.on_registration_complete = on_registration_complete
        self.start_time = datetime.now()
        self.root = None  # Will be initialized later
        self.periodic_validator = None

        if self.config_file_exists():
            if self.validate_existing_config():
                # If validation succeeds, proceed to the main application
                self.on_registration_complete()
            else:
                # If validation fails, prompt for re-registration
                print("License validation failed. Please register again.")
                self.initialize_gui()
        else:
            # If no config file exists, show the registration GUI
            self.initialize_gui()

    def config_file_exists(self):
        """Checks if the configuration file exists."""
        # Replace 'config_file_path' with the actual path to your config file
        config_file_path = os.path.join(os.getcwd(), 'config.txt')  # Update with actual config file path
        return os.path.isfile(config_file_path)
        
    def validate_existing_config(self):
        """Reads and validates the license information from the config file."""
        try:
            # Read and decode the existing config file
            config_data = self.license_manager.read_config_file()

            if not config_data:
                print("Config file could not be read or is empty.")
                return False

            # Extract the required fields from the config
            license_key = config_data.get("license_key")
            mac_address = config_data.get("Registration_number")  # Stored as the machine ID
            last_write_time_str = config_data.get("last_write_time")
            remain_days_str = config_data.get("remaining_days")

            # Validate required fields
            if not license_key or not mac_address or not last_write_time_str or not remain_days_str:
                print("Incomplete data in config file.")
                return False

            try:
                # Parse last_write_time and remain_days
                last_write_time = datetime.strptime(last_write_time_str, "%Y-%m-%d %H:%M:%S")
                remaining_days = int(remain_days_str)
            except (ValueError, TypeError):
                print("Invalid format for last_write_time or remain_days in config file.")
                return False

            # Calculate elapsed days and update remain_days
            elapsed_days = (datetime.now() - last_write_time).days
            remaining_days = max(0, remaining_days - elapsed_days)

            # Stop if remain_days is zero
            if remaining_days <= 0:
                print("No remaining days left in license.")
                return False

            # Prepare data to validate license
            data = {
                "license_key": license_key,
                "mac_address": mac_address,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # API URL (replace with your actual URL)
            url = "https://newmarketing.mediatechtemple.com/_api/userapi/get-api/"

            # Set headers for the POST request
            headers = {
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
            }

            try:
                # Send POST request with the validation data
                response = requests.post(url, json=data, headers=headers)

                # Check if the API returned a successful response
                if response.status_code == 200:
                    response_json = response.json()  # Parse the response JSON
                    
                    # Debugging response
                    print(f"Response JSON: {json.dumps(response_json, indent=2)}")

                    # Validate the server response
                    if response_json.get("status") == "success":
                        # Verify the mac_address matches
                        if response_json.get("mac_address") == mac_address:
                            print(mac_address)
                            print("Machine ID mismatch.")
                            return False
                        
                        config_file_path = os.path.join(os.getcwd(), 'config.txt')

                        try:
                            if os.path.exists(config_file_path):
                                # Temporarily change permissions to writable
                                os.chmod(config_file_path, 0o666)

                            # Write updated data back to the config file
                            self.license_manager.write_config_file(
                                auth_token=response_json.get("auth_token"),
                                license_key=license_key,
                                remaining_days=response_json["data"][0]["remaining_days"],
                                user_type=response_json["data"][0]["user_type"],
                            )

                        finally:
                            # Revert permissions back to read-only
                            os.chmod(config_file_path, 0o444)

                        print("License validation succeeded, and config file updated.")
                        return True
                    
                    else:
                        print(f"Validation error: {response_json.get('error', 'Unknown error')}")
                        return False
                else:
                    # Handle non-200 status codes
                    print(f"Failed to validate license. Status code: {response.status_code}")
                    return False

            except requests.exceptions.RequestException as e:
                print(f"Error connecting to the API: {e}")
                return False

        except Exception as e:
            print(f"Error during license validation: {e}")
            return False        
        
    def start(self):
        """Start the application and periodic validation."""
        if self.register_license():
            # Only start periodic validation after successful registration
            self.periodic_validator = PeriodicValidator(
                license_manager=self.license_manager,
                on_validation_success=self.on_registration_complete,
                on_validation_failure=self.handle_validation_failure
            )
            self.periodic_validator.start()  # Start the periodic validation
        else:
            print("Registration failed. Exiting application.")

    def register_license(self):
        """Handles license registration logic."""
        # Simulate the registration process, e.g., validating license key, etc.
        license_key = input("Enter your license key: ")
        result = self.license_manager.validate_license(license_key)

        if result.get("status") == "success":
            print("License successfully registered.")
            return True
        else:
            print(f"Registration failed: {result.get('error')}")
            return False
        
    def initialize_gui(self):
        """Initializes the registration GUI."""
        self.root = tk.Tk()  # Create the main Tkinter window
        self.root.title("REGISTER YOURSELF!")
        self.root.geometry("450x300")  # Adjusted height for a simpler UI
        self.root.resizable(0, 0)

        # License key label and entry box
        self.license_key_label = tk.Label(self.root, text="Enter License Key:", font=("Helvetica", 14))
        self.license_key_label.grid(row=0, column=0, padx=10, pady=(30, 10))

        self.license_key_entry = tk.Entry(self.root, font=('Helvetica', 16), width=30)
        self.license_key_entry.grid(row=1, column=0, padx=40, pady=(0, 30))

        # Submit button
        self.submit_button = tk.Button(self.root, text="Submit", bg='blue', fg='white', font=('Arial', 14), command=self.submit_form)
        self.submit_button.grid(row=2, column=0, padx=10, pady=20)

    def submit_form(self):
        """Handles form submission and sends the license key to the API."""
        user_license_key = self.license_key_entry.get().strip()  # Get the entered license key

        if not user_license_key:
            messagebox.showerror("Error", "Please enter a valid License Key.")
            return

        try:
            # Validate the license key with the server
            response_json = self.license_manager.validate_license(user_license_key)
            if "error" in response_json:
                messagebox.showerror("Error", response_json["error"])
            else:
                self.handle_response(response_json, user_license_key)
        except Exception as e:
            messagebox.showerror("Error", str(e))
                
    def handle_response(self, response_json, user_license_key):
        """Handles the server response."""
        if "error" in response_json:
            messagebox.showerror("Error", f"Server returned an error: {response_json['error']}")
            return

        # Check for a successful response
        if response_json.get('status') == "success" and 'data' in response_json:
            user_data = response_json['data'][0]

            license_key = user_data['license_key']
            remaining_days = user_data['remaining_days']
            user_type = user_data['user_type']  # Assuming the server response includes the user type ("demo" or "full")

            if license_key.strip() != user_license_key.strip():
                messagebox.showerror("Error", "License Key does not match. Registration failed.")
                return

            # Success message
            messagebox.showinfo("Registration Successful", "License Key validated successfully!")

            # Send machine data to the server (for licensing purposes)
            self.license_manager.send_machine_data(license_key)

            # Dynamically handle `remain_days` and write to the config file
            self.license_manager.write_config_file(
                auth_token=response_json.get("auth_token"),
                license_key=license_key,
                remaining_days=remaining_days,
                user_type=user_type
            )

            # Proceed to the main app (Call the function to set up user input GUI)
            # self.on_registration_complete()  # Pass the user type to the next step
            self.root.destroy()  # Close the registration window or move to the next screen

        else:
            messagebox.showerror("Error", "Invalid response from server.")

    def run(self):
        """Starts the registration GUI or skips if already registered."""
        try:
            # Check if the attribute 'root' exists
            if hasattr(self, 'root'):
                # Attempt to call mainloop
                self.root.mainloop()
            else:
                # Raise an AttributeError if 'root' isn't set
                raise AttributeError("The 'root' attribute is not initialized. GUI cannot be started.")
        except AttributeError as ae:
            # Handle the specific error
            print(f"AttributeError: {ae}")
        except Exception as e:
            # Catch any other unforeseen errors
            print(f"An unexpected error occurred: {e}")



class PeriodicValidator:
    def __init__(self, license_manager, interval_hours=3, on_validation_success=None, on_validation_failure=None):
        """
        Initializes the PeriodicValidator.

        Args:
            license_manager: Instance of LicenseManager for handling license-related operations.
            interval_hours: Number of hours between periodic validations.
            on_validation_success: Callback for successful validation.
            on_validation_failure: Callback for failed validation.
        """
        self.license_manager = license_manager
        self.interval_seconds = interval_hours * 60 * 60  # Convert hours to seconds
        self.on_validation_success = on_validation_success
        self.on_validation_failure = on_validation_failure

    def start(self):
        """Starts the periodic validation after a delay of 3 hours."""
        # Wait for 3 hours before starting the validation
        print("Waiting for 3 hours before starting periodic validation...")
        time.sleep(3 * 60 * 60)  # Sleep for 3 hours
        print("Starting periodic validation after 3-hour wait...")
        
        threading.Thread(target=self._validate_periodically, daemon=True).start()

    def _validate_periodically(self):
        """Performs periodic license validation."""
        while True:
            try:
                # Load data from the config file
                config_data = self.license_manager.read_config_file()
                if not config_data:
                    print("Config file is missing or invalid. Cannot validate credentials.")
                    if self.on_validation_failure:
                        self.on_validation_failure("Config file missing or invalid.")
                    return

                license_key = config_data.get("license_key")
                machine_id = self.license_manager.get_mac_address()

                # Prepare payload
                payload = {
                    "license_key": license_key,
                    "machine_id": machine_id,
                    "timestamp": datetime.now().isoformat(),
                }

                # Send request to server
                response = requests.post(self.license_manager.server_url, json=payload)
                
                # Ensure we handle cases where the server does not respond as expected
                if response.status_code != 200:
                    print(f"Failed to connect to the server. Status code: {response.status_code}")
                    if self.on_validation_failure:
                        self.on_validation_failure(f"Failed to connect. Status code: {response.status_code}")
                    return

                response_json = response.json()

                # Handle the response
                if response_json.get("status") == "success":
                    print("Periodic validation successful.")
                    if self.on_validation_success:
                        self.on_validation_success()  # Run this only if validation is successful
                else:
                    print(f"Periodic validation failed: {response_json.get('error')}")
                    if self.on_validation_failure:
                        self.on_validation_failure(response_json.get("error"))

            except requests.exceptions.Timeout as e:
                print(f"Request timeout error: {e}")
                if self.on_validation_failure:
                    self.on_validation_failure(f"Timeout error: {e}")
            except requests.exceptions.RequestException as e:
                print(f"Error during HTTP request: {e}")
                if self.on_validation_failure:
                    self.on_validation_failure(f"Request error: {e}")
            except Exception as e:
                print(f"Unexpected error during periodic validation: {e}")
                if self.on_validation_failure:
                    self.on_validation_failure(f"Unexpected error: {e}")

            # Wait for the specified interval before the next validation
            print(f"Waiting for {self.interval_seconds} seconds before the next validation...")
            time.sleep(self.interval_seconds)



# Define the main function
def main():
    # License Manager setup (assuming you have a LicenseManager class elsewhere)
    license_manager = LicenseManager()

    def on_registration_complete():
        # Create the main window for Google Maps extraction
        @dataclass
        class Business:
            """Holds business data"""
            dealer_name: str = None
            dealer_address: str = None
            dealer_phone: str = None
            dealer_website: str = None
            dealer_status: str = None
            dealer_reviews: str = None
            dealer_review_avg: str = None
            latitude: float = None
            longitude: float = None
            location: str = None
            keyword: str = None 

            
        @dataclass
        class BusinessList:
            """Holds list of Business objects and saves to Excel"""
            business_list: list[Business] = field(default_factory=list)

            def dataframe(self):
                """Transform business_list to pandas DataFrame and reorder columns"""
                df = pd.json_normalize(
                    (asdict(business) for business in self.business_list), sep="_"
                )
                
                # Reorder columns: location and keyword first
                column_order = ['location', 'keyword'] + [col for col in df.columns if col not in ['location', 'keyword']]
                return df.reindex(columns=column_order)

            def save_to_excel(self, filename):
                """Saves pandas DataFrame to Excel (xlsx) file"""
                self.dataframe().to_excel(filename, index=False)

                    
            def get_unique_businesses(self):
                """Return unique businesses based on location and keyword."""
                # Convert business_list to a DataFrame
                df = self.dataframe()

                # Drop duplicates based on location and keyword
                unique_df = df.drop_duplicates(subset=['location', 'keyword'])

                # Convert back to a list of Business objects
                unique_businesses = [Business(**row) for index, row in unique_df.iterrows()]
                return unique_businesses

            def print_unique_businesses(self):
                """Print unique businesses to the console."""
                unique_businesses = self.get_unique_businesses()
                for business in unique_businesses:
                    print(f"Location: {business.location}, Keyword: {business.keyword}, Other: {business.other_field}")


        def extract_dealer_info(search_query, location, keyword, update_status, update_table, stop_event, business_list):
            update_status("Extracting data...")  # Update status to extracting

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)  # Set headless=True for production
                page = browser.new_page()

                # Go to Google Maps
                page.goto("https://www.google.com/maps", timeout=60000)
                page.wait_for_timeout(5000)

                # Input the search query
                page.locator('xpath=//input[@id="searchboxinput"]').fill(search_query)
                page.keyboard.press("Enter")
                page.wait_for_timeout(5000)

                # Initialize a set to keep track of already processed listings
                processed_dealers = set()

                # Perform scrolling to load all results
                while True:
                    if stop_event.is_set():
                        update_status("Data extraction stopped by user.")
                        break

                    listings = page.locator('xpath=//a[@class="hfpxzc"]').all()
                    current_listing_count = len(listings)

                    print(f"Found {current_listing_count} dealers so far...")

                    for dealer in listings:
                        if stop_event.is_set():
                            update_status("Data extraction stopped by user.")
                            break
                        try:
                            dealer_url = dealer.get_attribute('href')
                            if dealer_url in processed_dealers:
                                continue
                            processed_dealers.add(dealer_url)

                            dealer.scroll_into_view_if_needed()
                            dealer.click(force=True)

                            page.wait_for_timeout(5000)
                            page.wait_for_selector('xpath=//h1[@class="DUwDvf lfPIob"]', timeout=5000)

                            business = Business()
                            business.dealer_name = page.locator('xpath=//h1[@class="DUwDvf lfPIob"]').first.inner_text() if page.locator('xpath=//h1[@class="DUwDvf lfPIob"]').count() > 0 else "N/A"
                            
                            address_text = page.locator('xpath=//div[@class="rogA2c "]').all_text_contents()
                            business.dealer_address = address_text[0] if address_text else "N/A"
                            business.dealer_phone = extract_phone_number(address_text)
                            business.dealer_status = page.locator('xpath=//span[@class="ZDu9vd"]').inner_text() if page.locator('xpath=//span[@class="ZDu9vd"]').count() > 0 else "N/A"
                            business.dealer_website = extract_website_from_address(address_text)
                            business.dealer_reviews = page.locator('xpath=//button[@class="HHrUdb fontTitleSmall rqjGif"]').inner_text() if page.locator('xpath=//button[@class="HHrUdb fontTitleSmall rqjGif"]').count() > 0 else "N/A"
                            business.dealer_review_avg = page.locator('xpath=//div[@class="fontDisplayLarge"]').inner_text() if page.locator('xpath=//div[@class="fontDisplayLarge"]').count() > 0 else "N/A"
                            business.latitude, business.longitude = extract_coordinates_from_url(page.url)

                            # Tag the business with location and keyword
                            business.location = location
                            business.keyword = keyword

                            business_list.business_list.append(business)

                            # Update the table with extracted data
                            update_table(business)

                        except Exception as e:
                            print(f"Error extracting details for a dealer: {e}")

                    page.mouse.wheel(0, 10000)
                    page.wait_for_timeout(5000)

                    new_listings = page.locator('xpath=//a[@class="hfpxzc"]').all()
                    new_listing_count = len(new_listings)

                    if new_listing_count == current_listing_count:
                        print("No new dealers found after scrolling. Stopping...")
                        break

                update_status("Data extraction complete.")  # Update status to completed
                browser.close()

        def extract_coordinates_from_url(url: str) -> tuple:
            """Helper function to extract latitude and longitude from the URL."""
            try:
                coordinates_part = url.split('/@')[1].split('/')[0]
                latitude, longitude, _ = coordinates_part.split(',')
                return float(latitude), float(longitude)
            except Exception as e:
                print(f"Error extracting coordinates from URL: {url}. Error: {e}")
                return None, None

        def extract_phone_number(text: list) -> str:
            """Uses regex to extract a phone number from the provided text."""
            phone_pattern = r"^(\d{6})\s(\d{5})$"
            phone_number = ""
            
            for line in text:
                match = re.search(phone_pattern, line)
                if match:
                    phone_number = match.group(0)
                    break
            return phone_number if phone_number else "N/A"

        def extract_website_from_address(address_text: list) -> str:
            """Extracts a website URL from the dealer address using regex."""
            url_pattern = r"(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.(com|net|org|in)(?:/[^\s]*)?"
            website_url = "N/A"
            
            for line in address_text:
                match = re.search(url_pattern, line)   
                if match:
                    website_url = match.group(0)
                    break
            return website_url

        # GUI part to get user input
        def get_user_input_gui():
            global decoded_config_data  # Access the global variable

            # Check if decoded_config_data is available and contains user_type
            if decoded_config_data:
                # Parse the decoded configuration data manually
                config_dict = {}
                for line in decoded_config_data.splitlines():
                    if '=' in line:  # Only process lines with key=value format
                        key, value = line.split('=', 1)  # Split on the first '='
                        config_dict[key.strip()] = value.strip()
                    remaining_days = config_dict.get("remaining_days")
                    full_remain_days_label = f"Days remaining:{remaining_days}"
                    print(f"remaining_days: {remaining_days}")  # Debugging output

            def submit_action():
                # Reset the stop event to allow the search to proceed
                stop_event.clear()  # Ensure the stop flag is cleared when starting a new search

                # Get the city and keyword entries and split them into lists
                cities = city_entry.get().split(',')  # Split cities by comma
                keywords = keyword_entry.get().split(',')  # Split keywords by comma

                # Strip any extra spaces from cities and keywords
                cities = [city.strip() for city in cities]
                keywords = [keyword.strip() for keyword in keywords]

                # Function to handle the search process for each city and keyword
                def search_for_all():
                    for city in cities:
                        for keyword in keywords:
                            # Check if the stop event is set
                            if stop_event.is_set():
                                update_status("Extraction stopped by user.")
                                print("Extraction stopped by user.")
                                return  # Exit the function to stop further processing

                            # Create search query
                            search_query = f"{keyword} in {city}"
                            print(f"Searching for {search_query}...")

                            # Update status and call the function to extract dealer data
                            update_status(f"Searching for {search_query}...")

                            # Start the search
                            extract_dealer_info(
                                search_query, city, keyword, update_status, update_table, stop_event, business_list
                            )

                            # Allow time for the current search to complete (or simulate cleanup)
                            time.sleep(2)  # Adjust the sleep time based on search completion duration

                    # Notify that all searches are done
                    update_status("All searches completed.")

                # Start the search process in a separate thread
                threading.Thread(target=search_for_all).start()


            def stop_action():
                stop_event.set()  # Set the stop event to signal stopping the process
                update_status("Stopping extraction...")  # Update status in the GUI

            def download_action():
                """Handle the download action for the Excel file."""
                global decoded_config_data  # Access the global variable
                print(decoded_config_data)  # Print the decoded config data for debugging

                # Check if decoded_config_data is available and contains user_type
                if decoded_config_data:
                    # Parse the decoded configuration data manually
                    config_dict = {}
                    for line in decoded_config_data.splitlines():
                        if '=' in line:  # Only process lines with key=value format
                            key, value = line.split('=', 1)  # Split on the first '='
                            config_dict[key.strip()] = value.strip()

                    user_type = config_dict.get("user_type", "")
                    print(f"User type: {user_type}")  # Debugging output

                    # Check user_type and define actions
                    if user_type == "demo":
                        # messagebox.showerror("Error", "Demo license. Cannot download Excel file.")
                        return None
                        return  # Stop execution if it's a demo user
                    # elif user_type == "trial":
                    #     messagebox.showwarning("Warning", "You are on a trial license. Limited features available.")
                    elif user_type == "custom":
                        # Implement custom functionality for custom user type
                        print("Custom user type functionality can be added here.")

                # Continue with the existing functionality for all other user types
                if not business_list.business_list:
                    # messagebox.showerror("Error", "No data available to download. Please run the extraction first.")
                    return None

                # Prepare the filename based on user input (if applicable)
                filename = f"google_maps_data_{state_entry.get().replace(' ', '_')}_{city_entry.get().replace(' ', '_')}_{keyword_entry.get().replace(' ', '_')}.xlsx"
                file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")], initialfile=filename)
                
                if file_path:
                    business_list.save_to_excel(file_path)
                    messagebox.showinfo("Success", f"File saved to: {file_path}")

            if __name__ == "__main__":
                license_manager = LicenseManager()
                business_list = BusinessList()
                config_data = license_manager.read_config_file()  # Read the config file
                print("Decoded Config Data:", config_data)  # Show the raw decoded data
                download_action()  # Call the download action              

            def clear_results():
                """Clear the search results and sidebar information."""
                business_list.business_list.clear()  # Clear the business list
                tree.delete(*tree.get_children())  # Clear the Treeview
                update_status("Search results cleared.")

            def update_status(status):
                status_label.config(text=status.capitalize())  # Capitalize first letter

            def update_table(business: Business):
                """Updates the Treeview with new business data."""
                tree.insert('', 'end', values=(business.dealer_name, business.dealer_address, business.dealer_phone, business.dealer_website, business.dealer_status.capitalize(), business.dealer_reviews, business.dealer_review_avg))

                # Update status with count
                status_label.config(text=f"Status: {len(business_list.business_list)} results found.".capitalize())

            # Create a stop event for threading
            global stop_event
            stop_event = threading.Event()


            if __name__ == "__main__":
                license_manager = LicenseManager()
                business_list = BusinessList()
                config_data = license_manager.read_config_file()  # Read the config file
                print("Decoded Config Data:", config_data)  # Show the raw decoded data
                download_action()  # Call the download action              

            # GUI setup
            main_window = tk.Tk()
            main_window.title("Google Maps Data Extractor (Version : 1.11.o)")
            main_window.geometry("800x600")

            # Center Frame
            center_frame = tk.Frame(main_window)
            center_frame.pack(pady=10)

            # Input fields
            state_label = tk.Label(center_frame, text="State:", font=('Helvetica', 12))
            state_label.grid(row=0, column=0, padx=10)
            state_entry = tk.Entry(center_frame, font=('Helvetica', 12))
            state_entry.grid(row=0, column=1, padx=10)

            city_label = tk.Label(center_frame, text="City:", font=('Helvetica', 12))
            city_label.grid(row=1, column=0, padx=10)
            city_entry = tk.Entry(center_frame, font=('Helvetica', 12))
            city_entry.grid(row=1, column=1, padx=10)

            keyword_label = tk.Label(center_frame, text="Keyword:", font=('Helvetica', 12))
            keyword_label.grid(row=2, column=0, padx=10)
            keyword_entry = tk.Entry(center_frame, font=('Helvetica', 12))
            keyword_entry.grid(row=2, column=1, padx=10)

            # Setup for buttons in a horizontal arrangement
            button_frame = tk.Frame(center_frame)
            button_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))

            submit_button = tk.Button(button_frame, text="Search", font=('Helvetica', 14, 'bold'), bg='#4CAF50', fg='white', command=submit_action)
            submit_button.pack(side='left', padx=5)

            stop_button = tk.Button(button_frame, text="Stop", font=('Helvetica', 14, 'bold'), bg='#f44336', fg='white', command=stop_action)
            stop_button.pack(side='left', padx=5)

            download_button = tk.Button(button_frame, text="Download", font=('Helvetica', 14, 'bold'), bg='#2196F3', fg='white', command=download_action)
            download_button.pack(side='left', padx=5)

            clear_button = tk.Button(button_frame, text="Clear Results", font=('Helvetica', 14, 'bold'), bg='#FF9800', fg='white', command=clear_results)
            clear_button.pack(side='left', padx=5)

            # Status Label
            status_label = tk.Label(center_frame, text="Status: Ready", font=('Helvetica', 12, 'bold'))
            status_label.grid(row=4, column=0, columnspan=2)

            # Label for remain_days
            remain_days_label = tk.Label(center_frame, text=full_remain_days_label, font=('Helvetica', 12, 'bold'), fg='blue')
            remain_days_label.grid(row=5, column=0, columnspan=2)

            # Treeview for results
            columns = ("Dealer Name", "Address", "Phone", "Website", "Status", "Reviews", "Avg Review")
            tree = ttk.Treeview(main_window, columns=columns, show='headings')

            # Bold headers
            style = ttk.Style()
            style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'))
            
            for col in columns:
                tree.heading(col, text=col, anchor='center')
                tree.column(col, anchor="w", stretch=True)
                
            # Add separation lines
            tree.tag_configure('separator', font=('Helvetica', 10, 'bold'), foreground='black')

            tree.pack(expand=True, fill='both')

            # Scrollbars
            y_scroll = Scrollbar(main_window, orient='vertical', command=tree.yview)
            y_scroll.pack(side='right', fill='y')
            tree.configure(yscrollcommand=y_scroll.set)

            
            if __name__ == "__main__":
                license_manager = LicenseManager()
                business_list = BusinessList()
                config_data = license_manager.read_config_file()  # Read the config file
                print("Decoded Config Data:", config_data)  # Show the raw decoded data


            # Make the Treeview full screen
            main_window.grid_rowconfigure(1, weight=1)
            main_window.grid_columnconfigure(0, weight=1)

            main_window.mainloop()

        # Run the GUI
        get_user_input_gui()
    # Run the Registration app
    registration_app = RegistrationApp(license_manager, on_registration_complete)
    registration_app.run()


if __name__ == "__main__":
    license_manager = LicenseManager()
    config = license_manager.read_config_file()
    print("Global decoded_config_data:", decoded_config_data)
    
    main()


def main(self):
    root = tk.Tk()

    # Check if config.txt is present
    if os.path.exists('config.txt'):
        app = self.on_registration_complete()
        # app.read_config_and_verify_token()
    else:
        registration_app = RegistrationApp()
        # registration_app.run()

if __name__ == "_main_":
    # cProfile.run("main()", sort="time")
    
    main()


