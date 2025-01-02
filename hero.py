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

class HeroDealerDetails:
    def __init__(self):
        # Define the target URL
        self.url = "https://dealers.heromotocorp.com/"
        
        # XPaths for the new elements
        self.dealer_container_xpath = "//section[@class='storelocator-default']//div[@class='outlet-list']"
        self.state_selector_xpath = "//*[@id='OutletState']"
        self.city_selector_xpath = "//*[@id='OutletCity']"
        self.locality_selector_xpath = "//*[@id='OutletLocality']"
        self.dealer_selector_xpath = "//div[@class='custom-checkbox']//div[@class='checkbox']"
        self.submit_button_xpath = "//div[@class='submit']//input[@type='submit' and @value='SEARCH']"
        self.phone_selector_xpath = "//div[@class='store-info-box']//li[@class='outlet-actions']//a[@class='btn btn-call' and starts-with(@href, 'tel:')]/@href"
        self.firm_name_selector_xpath = "//div[@class='store-info-box']//div[@class='info-text']/a/text()"
        self.address_selector_xpath = "//div[@class='store-info-box']//div[@class='info-text']//span//text()"
        
        
        # Path to the Excel file (will be created if doesn't exist)
        self.excel_file_path = "live_dealer_details.xlsx"
        self.all_dealer_data = []  # Initialize an empty list to hold all the dealer data

        # List of states
        self.states = [
            "Andaman and Nicobar", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chandigarh", "Chhattisgarh","Dadra and Nagar Haveli", "Delhi", "Goa",
            "Gujarat", "Haryana", "Himachal Pradesh","Jammu and Kashmir", "Jharkhand", "Karnataka", "Kerala",
            "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
            "Odisha","pondicherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
            "Uttar Pradesh", "Uttarakhand", "West Bengal"
        ]
        
        # Tkinter setup
        self.root = tk.Tk()
        self.root.title("Hero dealer locator")
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
        self.state_combobox.bind("<<ComboboxSelected>>", self.combined_pack)

        # City selection
        self.city_label = tk.Label(self.left_frame, text="Select City:", font=("Arial", 14))
        self.city_label.pack(pady=5)

        self.city_combobox = ttk.Combobox(self.left_frame, font=("Arial", 12))
        self.city_combobox.pack(pady=10)
        
        #dealer type selection 
        self.dealer_type_label = tk.Label(self.left_frame , text="select Dealer type :" , font=("Arisl" , 14))
        self.dealer_type_label.pack(pady=5)
        
        self.dealer_combobox = ttk.Combobox(self.left_frame , font=("Arial" , 12))
        self.dealer_combobox.pack(pady=10)
        self.dealer_combobox.bind("<<ComboboxSelected>>", self.update_dealer_type)


        # Button frame
        self.button_frame = tk.Frame(self.left_frame)
        self.button_frame.pack(pady=20)

        # Buttons
        self.select_button = tk.Button(
            self.button_frame, text="Extract", font=("Arial", 15), bg='blue', fg='white', command=self.download_selected_state_city, width=20
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
        self.tree = ttk.Treeview(self.right_frame, columns=("Dealer Type","State", "City", "Locaity", "Firm Name", "Address", "Phone"), show="headings")
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
        
    def combined_pack(self , event) :
        self.update_city_list(event)   
        self.update_dealer_type(event)
        
    def update_city_list(self ,event):
        state = self.state_combobox.get()
        if state:
            cities = self.get_cities_for_state(state)
            self.city_combobox['values'] = cities
            
    def update_dealer_type(self ,event):
        state = self.state_combobox.get()
        if state:
            dealer_types = self.get_dealer_types_for_state(state)
            print(dealer_types)
            self.dealer_combobox['values'] = dealer_types

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
    
    def get_dealer_types_for_state(self, state):
        """Fetch the dealer types based on the selected state."""
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
            time.sleep(1)  # Allow some time for dealer types to load

            # Get the list of dealer types (similar to how we fetch cities)
            dealer_types = self.get_checkbox_labels(page)
            browser.close()

        return dealer_types # Exclude the first entry (e.g., "Select Dealer Type")
    
    def get_checkbox_labels(self, page):
        """Fetch the text of all checkboxes from the page."""
        dealer_labels = page.locator(self.dealer_selector_xpath)  # XPath for dealer checkboxes
        labels = dealer_labels.all_text_contents()  # Fetch the labels of checkboxes
        return labels  # Return the list of dealer types from the checkbox labels
    
    

    def get_dropdown_options(self, page, dropdown_xpath):
        dropdown = page.locator(dropdown_xpath)
        dropdown.click()
        time.sleep(0.5)  # Small delay to allow dropdown to open
        options = dropdown.locator("option")
        options_list = [options.nth(i).text_content().strip() for i in range(options.count())]
        return options_list

    def download_selected_state_city(self):
        state = self.state_combobox.get()
        city = self.city_combobox.get()
        dealer_type = self.dealer_combobox.get()
        if not state:
            messagebox.showwarning("Warning", "Please select a state!")
            return
        if not city:
            cities = self.get_cities_for_state(state)
            if not cities:
                messagebox.showwarning("Warning", "No cities found for this state!")
                return
            
            self.fetch_dealer_details_threaded(state, cities ,dealer_type)
        else:
            self.fetch_dealer_details_threaded(state, [city] , dealer_type)

    def fetch_dealer_details_threaded(self, state, city , dealear_type):
        # Handle the data fetching in a separate thread
        threading.Thread(target=self.fetch_dealer_details, args=(state, city , dealear_type), daemon=True).start()
        
        
    def fetch_dealer_details(self, state, cities, dealer_type):
        self.update_status(f"Processing state: {state}")
        self.stop_event.clear()  # Ensure the event is cleared before starting
        
        
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
            pd.DataFrame(columns=["Dealer Type", "State", "City", "Locality", "Firm Name", "Address","Phone"]).to_excel(
                excel_file, index=False
            )
        
        
        with sync_playwright() as p:
            # Launch the browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Navigate to the target URL
            page.goto(self.url)
            print("Page loaded successfully.")

            for city in cities:
                if self.stop_event.is_set():
                    self.update_status("Stopped fetching data.")
                    break
                if city == "Aurangabad" :
                    continue
                
                print(f"Processing city: {city}")
                
                try:
                    # Select the state and city
                    page.locator(self.state_selector_xpath).select_option(label=state)
                    page.locator(self.city_selector_xpath).select_option(label=city)
                    self.update_status(f"Fetching data for {state} - {city}...")
                    time.sleep(1)

                    # Get Localities for this city
                    localities = self.get_dropdown_options(page, self.locality_selector_xpath)
                    print(f"Found localities: {localities}")

                    # Iterate through pincodes and fetch data for each
                    for locality in localities[1:]:  # Exclude first empty option
                        
                        if self.stop_event.is_set():
                            self.update_status("Stopped fetching data.")
                            break
                        
                        try:
                            # If Locality is valid, proceed with selection and data fetching
                            page.locator(self.locality_selector_xpath).select_option(label=locality)
                            print(f"Selected locality: {locality}")
                            page.locator(self.submit_button_xpath).click()
                            time.sleep(2)  # Wait for results to load

                            # Extract dealer details
                            dealer_data = self.get_dealer_data(page, state, city, locality , dealer_type)
                            if dealer_data:
                                for data in dealer_data:
                                    self.append_data_to_excel(excel_file, data)
                                    self.all_dealer_data.append(data)
                                    # Use Tkinter's after() method to update the Treeview safely
                                    self.root.after(0, self.insert_into_treeview, data)
                        except Exception as e:
                            print(f"Error processing locality {locality} in city {city}: {e}")
                            continue  # Skip to the next locality        
                except Exception as e:
                    print(f"Error processing city {city}: {e}")
                    continue
                    
                self.update_status(f"Process complete for : {city}")
                
                    
            browser.close()
        self.update_status("All processing completed.")  
        self.root.after(0, lambda: messagebox.showinfo("Completed", f"Data fetching for state '{state}' is completed!"))
        
    def append_data_to_excel(self, file_name, data):
        """Append data to an existing Excel file."""
        df = pd.DataFrame([data], columns=["Dealer Type", "State", "City", "Locality", "Firm Name", "Address","Phone"])
        try:
            with pd.ExcelWriter(file_name, mode="a", if_sheet_exists="overlay", engine="openpyxl") as writer:
                df.to_excel(writer, index=False, header=False, startrow=writer.sheets["Sheet1"].max_row)
        except Exception as e:
            print(f"Error appending to Excel: {e}")
            self.update_status(f"Error saving data to Excel: {e}")
        
      
    
    def get_dealer_data(self, page, state, city, locality , dealer_type):
        dealer_data = []
        try:
            # Wait for dealer container to appear
            page.wait_for_selector(self.dealer_container_xpath, timeout=500000000)
            dealers = page.locator(self.dealer_container_xpath)
            

           # Use JavaScript logic to extract details
            dealer_details = dealers.evaluate_all(
                """(nodes) => nodes.map(node => {
                    const phone = node.querySelector("li.outlet-actions a.btn-call")?.getAttribute('href');
                    const name = node.querySelector("div.info-text a")?.innerText;
                    const address = [...node.querySelectorAll("div.info-text span")].map(el => el.innerText).join(', ');
                    return { phone, name, address };
                })"""
            )

            # Format the extracted data
            for dealer in dealer_details:
                dealer_data.append({
                    "Dealer Type" : dealer_type, 
                    "State": state,
                    "City": city,
                    "Locality": locality,
                    "Firm Name": dealer['name'] or "N/A",
                    "Address": dealer['address'] or "N/A",
                    "Phone": dealer['phone'] or "N/A"
                })

        except Exception as e:
            print(f"Error retrieving dealer data: {e}")

        return dealer_data



    def insert_into_treeview(self, data):
        # Insert rows with alternating colors to simulate grid lines
        tag = "odd" if len(self.tree.get_children()) % 2 == 0 else "even"
        self.tree.insert("", "end", values=(
            data["Dealer Type"],
            data["State"],
            data["City"],
            data["Locality"],
            data["Firm Name"],
            data["Address"],
            data["Phone"]
        ), tags = (tag,))
        
        # Apply alternating row colors
        self.tree.tag_configure("odd", background="lightgray", borderwidth=1, relief="solid")
        self.tree.tag_configure("even", background="white", borderwidth=1, relief="solid")
        
    def clear_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.all_dealer_data.clear()  # Clear the data from the list as well
        
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
        df = pd.DataFrame(self.all_dealer_data, columns=["Dealer Type",
            "State", "City", "Locality", "Firm Name", "Address","Phone"
        ])

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
    app = HeroDealerDetails()
    app.run()