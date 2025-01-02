import threading
import time
import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from playwright.sync_api import sync_playwright
from tkinter import filedialog, messagebox
import re
import os


class HondaDealerDetails:
    def __init__(self):
        # Define the target URL
        self.url = "https://www.honda2wheelersindia.com/network/dealerLocator"

        # Relative locators for dealer details
        self.dealer_container_xpath = "//div[@id='divDealer']//div[@class='repeat-dealor']"
        self.dealer_name_selector = "i.fa-user"  # Reference icon
        self.dealer_phone_selector = "i.fa-phone"  # Reference icon
        self.dealer_mobile_selector = "i.fa-mobile"  # Reference icon
        self.dealer_email_selector = "i.fa-envelope + a"  # Anchor tag following the email icon
        self.dealer_firm_selector = "//div[@class='col-md-12 col-sm-12 col-xs-12']/span"  # Selector for firm name
        self.dealer_address_selector = "//div[@class='col-md-12 col-sm-12 col-xs-12']/p"
        
        # Locator for different sections (Dealer Locator, Parts Locator, Service Locator)
        self.dealer_locator_xpath = "//*[@href='dealerLocator' and text()='Dealer Locator']"
        self.parts_locator_xpath = "//*[@href='#' and text()='Parts Locator']"
        self.service_locator_xpath = "//*[@href='serviceLocator' and text()='Service Locator']"

        # Locators for form elements
        self.state_selector_xpath = "//*[@id='StateID']"
        self.city_selector_xpath = "//*[@id='CityID']"
        self.pincode_selector_xpath = "//*[@id='PinCodeID']"
        self.submit_button_xpath = "//div[@class='col-md-3 col-sm-6 network-input']//button[@type='submit']"
        self.reset_button_xpath = "//div[@class='col-md-3 col-sm-6 network-input']//button[@id='btnReset']"

        # Path to the Excel file (will be created if doesn't exist)
        self.excel_file_path = "live_dealer_details.xlsx"
        self.all_dealer_data = []  # Initialize an empty list to hold all the dealer data

        # List of states
        self.states = [ "All",
            "Andaman and Nicobar", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chandigarh", "Chhattisgarh","Dadra and Nagar Haveli", "Delhi", "Goa",
            "Gujarat", "Haryana", "Himachal Pradesh","Jammu and Kashmir", "Jharkhand", "Karnataka", "Kerala",
            "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
            "Odisha","pondicherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
            "Uttar Pradesh", "Uttarakhand", "West Bengal"
        ]

        # Tkinter setup
        self.root = tk.Tk()
        self.root.title("Honda dealer locator")
        self.root.state("zoomed")  # Maximize the window to full screen
        
        # Add a main frame for layout
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # Create left and right frames
        self.left_frame = tk.Frame(self.main_frame, width=300)
        self.left_frame.pack(side="left", fill="y", padx=20, pady=20)

        # Add components to the left frame
        self.label = tk.Label(self.left_frame, text="List of State & City", bg="yellow", fg="black", font=("Arial", 20))
        self.label.pack(pady=20)
        
        # State selection
        self.state_label = tk.Label(self.left_frame, text="Select State:", font=("Arial", 14))
        self.state_label.pack(pady=5)

        self.state_combobox = ttk.Combobox(self.left_frame, values=self.states, font=("Arial", 12))
        self.state_combobox.pack(pady=10)
        self.state_combobox.bind("<<ComboboxSelected>>", self.update_city_list)

        # City selection
        self.city_label = tk.Label(self.left_frame, text="Select City:", font=("Arial", 14))
        self.city_label.pack(pady=5)

        self.city_combobox = ttk.Combobox(self.left_frame, font=("Arial", 12))
        self.city_combobox.pack(pady=10)

        # Button frame
        self.button_frame = tk.Frame(self.left_frame)
        self.button_frame.pack(pady=20)

        # Buttons
        self.select_button = tk.Button(
            self.button_frame, text="Search", font=("Arial", 15), bg='blue', fg='white', command=self.download_selected_state_city, width=20
        )
        self.select_button.grid(row=0, column=0, padx=20)
        
        self.download_excel_file =tk.Button(
            self.left_frame, text="Download Data", font=("Arial", 15), bg='green', fg='white', command=self.download_excel_file, width=20
        )
        self.download_excel_file.pack(pady=10)

        # Create right frame
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # Add Treeview to display dealer data
        self.tree = ttk.Treeview(self.right_frame, columns=("Segment", "State", "City", "Pincode", "Firm Name", "Address", "Name", "Phone", "Mobile", "Email"), show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Add headings to the Treeview
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER , width=150 , stretch=True)
            
        # Adding Scrollbars for the Treeview
        tree_scroll_y = tk.Scrollbar(self.right_frame, orient="vertical", command=self.tree.yview)
        tree_scroll_y.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=tree_scroll_y.set)

        tree_scroll_x = tk.Scrollbar(self.right_frame, orient="horizontal", command=self.tree.xview)
        tree_scroll_x.pack(side="bottom", fill="x")
        self.tree.configure(xscrollcommand=tree_scroll_x.set)

        # Apply Style to simulate grid lines
        self.style = ttk.Style()
        self.style.configure("Treeview",borderwidth=1,relief="solid",font=("Arial", 12),rowheight=25)  # You can adjust row height here for better spacing
        self.style.configure("Treeview.Heading",font=("Arial", 14, "bold"),anchor="center")

        # Add a Clear Data button to clear the Treeview
        self.clear_button = tk.Button(
            self.right_frame, text="Clear Data", font=("Arial", 15), bg='red', fg='white', command=self.clear_data
        )
        self.clear_button.pack(pady=20)
        
        # Add a status bar
        self.status_label = tk.Label(self.left_frame, text="Ready", bg="yellow", fg="black", font=("Arial", 12), anchor="w")
        self.status_label.pack(side="bottom", fill="x")
        
        self.stop_event = threading.Event()
        
        # Add Stop button
        self.stop_button = tk.Button(
            self.left_frame, text="Stop", font=("Arial", 15), bg='red', fg='black', command=self.stop_fetching, width=20
        )
        self.stop_button.pack(pady=10)

    def update_city_list(self, event):
        state = self.state_combobox.get()
        if state:
            cities = self.get_cities_for_state(state)
            self.city_combobox['values'] = cities

    def get_cities_for_state(self, state):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url)

            # Wait for the state selector to load and become visible
            page.wait_for_selector(self.state_selector_xpath)
            print(f"State selector found for {state}")

            # Select the state in the dropdown
            page.locator(self.state_selector_xpath).select_option(label=state)
            print(f"State {state} selected")
            time.sleep(1)  # Allow some time for cities to load

            # Get the list of cities
            cities = self.get_dropdown_options(page, self.city_selector_xpath)
            browser.close()

        return cities[1:]  # Exclude the first entry (e.g., "Select City")

    def get_dropdown_options(self, page, dropdown_xpath):
        dropdown = page.locator(dropdown_xpath)
        dropdown.click()
        time.sleep(0.5)  # Small delay to allow dropdown to open
        options = dropdown.locator("option")
        options_list = [options.nth(i).text_content().strip() for i in range(options.count())]
        return options_list

    def download_selected_state_city(self):
        state = self.state_combobox.get()
        if not state:
            messagebox.showwarning("Warning", "Please select a state!")
            return

        if state == "All":
            self.process_all_states_threaded()
        else:
            city = self.city_combobox.get()
            if not city:
                cities = self.get_cities_for_state(state)
                if not cities:
                    messagebox.showwarning("Warning", "No cities found for this state!")
                    return
                self.fetch_dealer_details_threaded(state, cities)
            else:
                self.fetch_dealer_details_threaded(state, [city])

                
    def process_all_states_threaded(self):
        # Handle the processing in a separate thread
        threading.Thread(target=self.process_all_states, daemon=True).start()

    def process_all_states(self):
        self.update_status("Processing all states...")
        self.stop_event.clear()  # Ensure the stop event is cleared before starting
        

        for state in self.states[1:]:  # Skip the "All" option
            if self.stop_event.is_set():
                self.update_status("Stopped processing.")
                break

            self.update_status(f"Processing state: {state}")
            cities = self.get_cities_for_state(state)
            if not cities:
                self.update_status(f"No cities found for state: {state}")
                continue

            self.fetch_dealer_details(state, cities)

        self.update_status("Completed processing all states.")
        

        
        
    def fetch_dealer_details_threaded(self, state, city):
        # Handle the data fetching in a separate thread
        threading.Thread(target=self.fetch_dealer_details, args=(state, city), daemon=True).start()
        
    def fetch_dealer_details(self, state, cities):
        self.update_status(f"Processing state: {state}")
        
        
        # Check if a file for this state already exists and increment the number until it's unique
        base_file_name = f"{state.replace(' ', '_')}"
        excel_file = f"{base_file_name}.xlsx"
        counter = 1

        # Ensure the file name is unique
        while os.path.exists(excel_file):
            excel_file = f"{base_file_name}_{counter}.xlsx"
            counter += 1

        # Create an empty Excel file if not exists
        if not os.path.exists(excel_file):
            pd.DataFrame(columns=["Segment", "State", "City", "Pincode", "Firm Name", "Address", "Name", "Phone", "Mobile", "Email"]).to_excel(
                excel_file, index=False
            )

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(self.url)
            for city in cities:
                if self.stop_event.is_set():
                    self.update_status("Stopped fetching data.")
                    break

                try:
                    page.locator(self.state_selector_xpath).select_option(label=state)
                    page.locator(self.city_selector_xpath).select_option(label=city)
                    self.update_status(f"Fetching data for {state} - {city}...")
                    time.sleep(1)

                    pincodes = self.get_dropdown_options(page, self.pincode_selector_xpath)
                    for pincode in pincodes[1:]:  # Skip first option
                        if self.stop_event.is_set():
                            self.update_status("Stopped fetching data.")
                            break

                        if ' ' in pincode:  # Check if pincode contains a space
                            print(f"Skipping pincode '{pincode}' as it contains a space.")
                            continue  # Skip pincodes with spaces

                        page.locator(self.pincode_selector_xpath).select_option(label=pincode)
                        page.locator(self.submit_button_xpath).click()
                        time.sleep(2)

                        dealer_data = self.get_dealer_data(page, state, city, pincode)
                        for data in dealer_data:
                            self.append_data_to_excel(excel_file, data)
                            self.all_dealer_data.append(data)
                            self.root.after(0, self.insert_into_treeview, data)
                except Exception as e:
                    print(f"Error processing {city}: {e}")
                    self.update_status(f"Error processing {city}: {e}")

            browser.close()

        self.update_status(f"Completed processing state: {state}.")
        if self.state_combobox.get() != "All":
            self.root.after(0, lambda: messagebox.showinfo("Completed", f"Data fetching for state '{state}' is completed!"))



    def append_data_to_excel(self, file_name, data):
        """Append data to an existing Excel file."""
        df = pd.DataFrame([data], columns=["Segment", "State", "City", "Pincode", "Firm Name", "Address", "Name", "Phone", "Mobile", "Email"])
        try:
            with pd.ExcelWriter(file_name, mode="a", if_sheet_exists="overlay", engine="openpyxl") as writer:
                df.to_excel(writer, index=False, header=False, startrow=writer.sheets["Sheet1"].max_row)
        except Exception as e:
            print(f"Error appending to Excel: {e}")
            self.update_status(f"Error saving data to Excel: {e}")



    

    def get_dealer_data(self, page, state, city, pincode):
        dealer_data = []

        # Wait for the dealer container to appear
        page.wait_for_selector(self.dealer_container_xpath, timeout=500000000)

        dealers = page.locator(self.dealer_container_xpath)
        dealers_count = dealers.count()
        
        segment = self.get_active_segment(page)

        print(f"Found {dealers_count} dealers for {state}, {city}, {pincode}.")

        if dealers_count == 0:
            print(f"No dealers found for {state}, {city}, {pincode}")
            return []

        for i in range(dealers_count):
            dealer = dealers.nth(i)
            firm_name = dealer.locator(self.dealer_firm_selector).text_content().strip() if dealer.locator(self.dealer_firm_selector).count() > 0 else "N/A"
            address = dealer.locator(self.dealer_address_selector).text_content().strip() if dealer.locator(self.dealer_address_selector).count() > 0 else "N/A"
            name = dealer.locator(self.dealer_name_selector).element_handle().evaluate("node => node.nextSibling.textContent.trim()")
            phone = dealer.locator(self.dealer_phone_selector).element_handle().evaluate("node => node.nextSibling.textContent.trim()")
            mobile = dealer.locator(self.dealer_mobile_selector).element_handle().evaluate("node => node.nextSibling.textContent.trim()")
            email = dealer.locator(self.dealer_email_selector).text_content().strip()

            # Append the dealer data to the list
            dealer_data.append({
                "Segment": segment,
                "State": state,
                "City": city,
                "Pincode": pincode,
                "Firm Name": firm_name,
                "Address": address,
                "Name": name,
                "Phone": phone,
                "Mobile": mobile,
                "Email": email
            })

        return dealer_data
    def get_active_segment(self, page):
        if page.locator(self.dealer_locator_xpath).is_visible():
            return "Dealer"
        elif page.locator(self.parts_locator_xpath).is_visible():
            return "Parts Locator"
        elif page.locator(self.service_locator_xpath).is_visible():
            return "Service Locator"
        else:
            return "Unknown"


    def insert_into_treeview(self, data):
        # Insert rows with alternating colors to simulate grid lines
        tag = "odd" if len(self.tree.get_children()) % 2 == 0 else "even"
        self.tree.insert("", "end", values=(
            data["Segment"],
            data["State"],
            data["City"],
            data["Pincode"],
            data["Firm Name"],
            data["Address"],
            data["Name"],
            data["Phone"],
            data["Mobile"],
            data["Email"]
        ), tags = (tag,))

        # Apply alternating row colors
        self.tree.tag_configure("odd", background="lightgray", borderwidth=1, relief="solid")
        self.tree.tag_configure("even", background="white", borderwidth=1, relief="solid")
        
        
    def clear_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.all_dealer_data.clear()  # Clear the data from the list as well
        
    #     from tkinter import filedialog, messagebox
    # import pandas as pd  # Ensure pandas is installed and imported

    def download_excel_file(self):
        # Ask user for file save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Save Excel File"
        )
        if not file_path:
            return  # If user cancels, do nothing

        # Convert all_dealer_data to a pandas DataFrame
        df = pd.DataFrame(self.all_dealer_data)

        if df.empty:
            messagebox.showwarning("No Data", "No dealer data available to download!")
            return

        # Save the DataFrame to the selected file path
        try:
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Success", f"Excel file saved successfully at {file_path}!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save Excel file: {e}")


    def save_to_excel_file(self):
        # Create a Pandas DataFrame from the list of dealer data
        df = pd.DataFrame(self.all_dealer_data, columns=[
            "Segment", "State", "City", "Pincode", "Firm Name", "Address", "Name", "Phone", "Mobile", "Email"
        ])

        # # Write the DataFrame to an Excel file
        # df.to_excel(self.excel_file_path, index=False)
        # print(f"Data written to {self.excel_file_path}")
        
    def validate_pin_with_spaces(pin_code):
        # Remove spaces and check if the cleaned pin code is of length 6 and contains only digits
        cleaned_pin = re.sub(r"\s+", "", pin_code)
        return len(cleaned_pin) == 6 and cleaned_pin.isdigit()
    
    
        
        
    
    # Add this method to the HondaDealerDetails class
    def update_status(self, message):
        """Update the status bar message."""
        self.status_label.config(text=message)
        self.root.update_idletasks()  # Ensure the UI updates immediately
        
    def stop_fetching(self):
        """Set the stop event and update the status."""
        self.stop_event.set()
        self.update_status("Stop fetching...")


    def run(self):
        self.root.mainloop()


# Running the application
if __name__ == "__main__":
    app = HondaDealerDetails()
    app.run()
  