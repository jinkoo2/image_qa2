import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry  # Date picker widget
from tkinter import ttk  # For progress bar
import threading
import time

from utils import helper, webservice

import importlib

import sys

import phantoms.catphan
import phantoms.fc2
import phantoms.lasvegas
import phantoms.qckv
import phantoms.qc3
import phantoms.helper
import phantoms.leedstor

from dicom_chooser import DicomChooser, SelectionMode
import dicom_helper

SETTINGS_FILE = '_settings.json'
APP_VERSION = '0.1.1'

# Initialize the logger
from app_logger import logger

# Splash Screen
def show_splash_screen():
    splash = tk.Tk()
    splash.overrideredirect(True)  # Hide window borders and controls
    splash.geometry("300x200+500+300")  # Set the position and size of the splash screen
    splash_label = tk.Label(splash, text="Loading...", font=("Helvetica", 16))
    splash_label.pack(expand=True)
    splash.update()
    time.sleep(2)  # Simulate some loading time (2 seconds)
    splash.destroy()  # Close the splash screen

def get_cwd():
    if getattr(sys, 'frozen', False):
        # If running as a compiled executable
        current_folder = os.path.dirname(sys.executable)
    else:
        # If running as a script
        current_folder = os.path.dirname(os.path.abspath(__file__))
    
    return current_folder

def find_obj_of_id(objs, id):
    for obj in objs:
        if obj["id"] == id:
            return obj

def get_obj_id_list(objs):
    return [obj["id"] for obj in objs]
                  
class PyLinacGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f'PyLinac GUI {APP_VERSION}')

        # Set the application icon (ensure app.ico is in the same directory as this script)
        self.root.iconbitmap('app.ico')

        # Set the default font for all widgets
        self.root.option_add("*Font", "Helvetica 10")

        # Load saved settings
        self.settings = self.load_settings()
        self.config = self.load_config()
    
        # Site, Device, and Phantom Selection Comboboxes
        self.selection_frame = tk.Frame(root)
        self.selection_frame.pack(pady=5, padx=5, fill="x")

        # Site selection
        tk.Label(self.selection_frame, text="Site:").pack(side="left", padx=5)
        
        sites = self.config["sites"]
        site_ids = get_obj_id_list(sites)
        self.site_combobox = ttk.Combobox(self.selection_frame, values=site_ids)
        self.site_combobox.pack(side="left", fill="x", expand=True)
        self.site_combobox.bind('<<ComboboxSelected>>', self.on_site_combobox_changed)

        # Device selection
        tk.Label(self.selection_frame, text="Device:").pack(side="left", padx=5)
        self.device_combobox = ttk.Combobox(self.selection_frame, values=[""])
        self.device_combobox.pack(side="left", fill="x", expand=True)

        # Phantom selection
        tk.Label(self.selection_frame, text="Phantom:").pack(side="left", padx=5)
        phantoms = self.config.get('phantoms', [])
        self.phantom_combobox = ttk.Combobox(self.selection_frame, values=get_obj_id_list(phantoms))
        self.phantom_combobox.pack(side="left", fill="x", expand=True)

        # Set default selections from settings if available
        self.site_combobox.set(self.settings.get('site', ''))
        self.on_site_combobox_changed({})
        self.device_combobox.set(self.settings.get('device', ''))
        self.phantom_combobox.set(self.settings.get('phantom', ''))

        # Add Performed By Dropdown (Combobox) and Performed Date Entry
        self.user_frame = tk.Frame(root)
        self.user_frame.pack(pady=5, padx=5, fill="x")

        # Performed By Label and Combobox
        self.performed_by_label = tk.Label(self.user_frame, text="Performed By:")
        self.performed_by_label.pack(side="left", padx=5)
        self.performed_by_combobox = ttk.Combobox(self.user_frame)
        self.performed_by_combobox.pack(side="left", fill="x", expand=True)

        # Performed Date Label and Entry
        self.date_frame = tk.Frame(root)
        self.date_frame.pack(pady=5, padx=5, fill="x")

        self.performed_date_label = tk.Label(self.date_frame, text="Performed Date:")
        self.performed_date_label.pack(side="left", padx=5)

        # Date picker (DateEntry) allowing both selection and manual entry
        self.performed_date_entry = DateEntry(self.date_frame, selectmode='day', date_pattern='y-mm-dd')
        self.performed_date_entry.pack(side="left", fill="x", expand=True)

        # Input folder frame (button + label)
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(pady=5, padx=5, fill="x")
        
        self.input_folder_button = tk.Button(self.input_frame, text="Input Folder", command=self.select_input_folder)
        self.input_folder_button.pack(side="left", padx=5)
        self.input_folder_path = tk.Label(self.input_frame, text=self.settings.get('input_folder', ''), relief=tk.SUNKEN, anchor="w")
        self.input_folder_path.pack(side="left", fill="x", expand=True)

        # Output folder frame (button + label)
        self.output_frame = tk.Frame(root)
        self.output_frame.pack(pady=5, padx=5, fill="x")
        
        self.output_folder_button = tk.Button(self.output_frame, text="Output Folder", command=self.select_output_folder)
        self.output_folder_button.pack(side="left", padx=5)
        #self.output_folder_button.config(state=tk.DISABLED, relief="flat", borderwidth=0, fg="black")
        output_folder = self.settings.get('output_folder', '')
        if output_folder == '':
            output_folder = self.config.get('output_folder', '')
        self.output_folder_path = tk.Label(self.output_frame, text=output_folder, relief=tk.SUNKEN, anchor="w")
        self.output_folder_path.pack(side="left", fill="x", expand=True)

        # Select Image frame (button + label)
        self.select_image_frame = tk.Frame(root)
        self.select_image_frame.pack(pady=5, padx=5, fill="x")
        self.select_image_button = tk.Button(self.select_image_frame, text="Select Image", command=self.select_dicom_image)
        self.select_image_button.pack(side="left", padx=5)
        self.select_image_label = tk.Label(self.select_image_frame, text='', relief=tk.SUNKEN, anchor="w")
        self.select_image_label.pack(side="left", fill="x", expand=True)

        # Notes Section
        self.notes_frame = tk.Frame(root)
        self.notes_frame.pack(pady=5, padx=5, fill="x")
        self.notes_label = tk.Label(self.notes_frame, text="Notes:")
        self.notes_label.pack(side="left", padx=5)
        self.notes_text = tk.Text(self.notes_frame, height=1, wrap="word")
        self.notes_text.pack(side=tk.LEFT, fill="x", padx=5, pady=5)

        # Buttons Section
        self.buttons_frame = tk.Frame(root)
        self.buttons_frame.pack(pady=5)
        self.run_button = tk.Button(self.buttons_frame, text="Run Analysis", command=self.run_analysis_thread, width=15)
        self.run_button.pack(side=tk.LEFT, padx=5, pady=10)
        self.push_to_server_button = tk.Button(self.buttons_frame, text="Push to Server", command=self.record_result_thread, width=15)
        self.push_to_server_button.pack(side=tk.LEFT, padx=5, pady=10)
        self.buttons_frame.pack(expand=True)
       
        # Create a frame to hold the Text widget and the Scrollbar for log output
        self.log_frame = tk.Frame(root)
        self.log_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create a Scrollbar
        self.scrollbar = tk.Scrollbar(self.log_frame)
        self.scrollbar.pack(side="right", fill="y")

        # Create the Text widget for logging messages
        self.log_output = tk.Text(self.log_frame, wrap="word", yscrollcommand=self.scrollbar.set)
        self.log_output.pack(side="left", fill="both", expand=True)

        # Configure the Scrollbar to work with the Text widget
        self.scrollbar.config(command=self.log_output.yview)

        # Create a frame to hold the status bar components
        self.status_frame = tk.Frame(root, relief=tk.SUNKEN, bd=1)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create a label for the status message
        #self.progress_label = tk.Label(self.status_frame, text="Ready", anchor=tk.W)
        #self.progress_label.pack(side=tk.LEFT, padx=5)

        # Create a progress bar
        self.progress_bar = ttk.Progressbar(self.status_frame, orient=tk.HORIZONTAL, mode='indeterminate')
        self.progress_bar.pack(side=tk.BOTTOM, fill= 'x', padx=5, pady=5)

        # Progress bar and status label at the bottom of the window
        #self.progress_label = tk.Label(root, text="")
        #self.progress_label.pack(side="bottom", pady=5)
        #self.progress_bar = ttk.Progressbar(root, mode="indeterminate")
        #self.progress_bar.pack(side="bottom", fill="x", padx=5, pady=5)

        # Set up the exit event to save settings
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # after all UIs created:
        self.populate_performed_by()  # Populate the combobox with data from config file
        # Set the default value from the loaded settings, if available
        performed_by = self.settings.get('performed_by', '')
        if performed_by:
            self.performed_by_combobox.set(performed_by)

    def on_site_combobox_changed(self, event):
        selected_value = self.site_combobox.get()
        print(f"Selected value: {selected_value}")

        if selected_value==None or selected_value=="":
            self.device_combobox.set('')
            self.device_combobox['values']=()
            return 
        
        sites = self.config.get('sites', [])

        site = find_obj_of_id(sites, selected_value)        
        if site == None:
            self.log("site not found in the configuration file.")
            return 
        
        devices = site["devices"]
        device_ids = get_obj_id_list(devices)

        self.device_combobox['values'] = device_ids
        self.device_combobox.set('')


    def load_config(self):
        # config file path
        current_dir = get_cwd()
        config_file = os.path.join(current_dir, 'config.json')

        if not os.path.exists(config_file):
            raise Exception(f"Config file ({config_file}) not found. It should be in the same folder of this executablel file")

        return helper.read_json_file(config_file)

    def site(self):
        if self.site_combobox.get() == "":
            raise Exception("Please select a site!")
            
        return self.site_combobox.get().strip()
    
    def device(self):
        if self.device_combobox.get() == "":
            raise Exception("Please select a device!")
            
        return self.device_combobox.get().strip()
    
    def device_id(self):
        return f'{self.site()}|{self.device()}'
    
    def phantom(self):
        if self.phantom_combobox.get() == "":
            raise Exception("Please select a phantom!")

        return self.phantom_combobox.get().strip()
    

    def load_phantom_config(self):
        # config file path
        current_dir = get_cwd()
        
        site = self.site().lower()
        device = self.device().lower()
        phantom = self.phantom().lower()

        config_file = os.path.join(current_dir, f'config.{site}.{device}.{phantom}.json')

        if not os.path.exists(config_file):
            raise Exception(f"Error:Phantom config file not found. {config_file}")
            return

        return helper.read_json_file(config_file)
    
    def populate_performed_by(self):
        users = self.config.get('users', [])
        user_list = [user.split('|')[1] for user in users]  # Extract the names from the 'Name|email' format
        self.performed_by_combobox['values'] = user_list

    def select_input_folder(self):
        initdir=self.input_folder_path.cget('text')
        if initdir.strip()=='':
            initdir = None
        folder = filedialog.askdirectory(initialdir=initdir)
        if folder:
            self.input_folder_path.config(text=folder)
            
    def select_output_folder(self):
        initdir=self.output_folder_path.cget('text')
        if initdir.strip()=='':
            initdir = None
        folder = filedialog.askdirectory(initialdir=initdir)
        if folder:
            self.output_folder_path.config(text=folder)

    def log(self, message):
        self.log_output.insert(tk.END, message + "\n")
        self.log_output.see(tk.END)

        logger.info(message)

    def select_dicom_image_2d(self):
        
        input_dir = self.get_input_folder()
        selection_mode = SelectionMode.FILE
        dicom_chooser = DicomChooser(self.root, input_dir, selection_mode=selection_mode)
        dicom_chooser.show()
        self.root.wait_window(dicom_chooser.window)

        # Get the selection
        selected_file = dicom_chooser.selected_file
        self.log(f'selected_file={selected_file}')

        if not os.path.exists(selected_file):
            self.log(f'selected file not found(file={selected_file}). probably a wrong selection. please selecte an image file.')
            return

        if selected_file:
            self.selected_file = selected_file
            self.select_image_label.config(text= os.path.basename(self.selected_file))
        else:
            self.log("No files selected for analysis.")

    def get_phantom_dim(self):
        phantom = find_obj_of_id(self.config['phantoms'], self.phantom())
        return phantom['dim']

    def select_dicom_image_3d(self):
        input_dir =  self.get_input_folder()

        if self.get_phantom_dim() == 3:
            selection_mode = SelectionMode.SERIES
        else:
            selection_mode = SelectionMode.FILE
        
        dicom_chooser = DicomChooser(self.root, input_dir, selection_mode=selection_mode)
        dicom_chooser.show()
        self.root.wait_window(dicom_chooser.window)
        selected_series_name, selected_files = dicom_chooser.get_selection()
        self.log(f"Selected image: {selected_series_name}")

        if selected_files and len(selected_files)>1:
            self.selected_files = selected_files
            self.selected_series_name = selected_series_name
            
            self.select_image_label.config(text= selected_series_name)
        else:
            self.log("No image selected.")
            return

    def select_dicom_image(self):
        
        if self.get_phantom_dim() == 3:
            self.select_dicom_image_3d()
        else:
            self.select_dicom_image_2d()

    def run_analysis_thread(self):
        
        # Disable the "Run Analysis" button to prevent multiple clicks
        # self.run_button.config(state=tk.DISABLED)
        
        # Show progress
        #self.progress_label.config(text="Running analysis...")
        self.progress_bar.start()

        # Run analysis in a separate thread
        threading.Thread(target=self.run_analysis).start()

    def run_analysis(self):
        try:
            module = self.get_phantom_module()
            self.phantom_config = self.load_phantom_config()

            metadata=self.phantom_config['publish_pdf_params']['metadata']
            metadata['Performed By'] = self.performed_by_combobox.get()
            metadata['Performed Date'] = self.performed_date_entry.get() 
            
            config_notes = self.phantom_config['publish_pdf_params'].get('notes', '')
            user_notes =  self.notes_text.get("1.0", tk.END).strip()

            notes = f'{user_notes}\n{config_notes}'                

            if self.get_phantom_dim() == 2:

                if self.selected_file == None or self.selected_file == "":
                    self.log('Please select an image first.')                 
                    return 
                
                # case output folder
                case_outdir = self.get_case_output_folder(self.selected_file)

                import shutil
                src_file = self.selected_file
                dst_file = os.path.join(case_outdir, 'input.dcm')
                shutil.copy(src_file, dst_file)
                
                self.analysis_input_file = dst_file
                self.analysis_result_folder = case_outdir

                
                module.run_analysis(device_id=self.device_id(),
                    input_file=self.analysis_input_file, 
                    output_dir=self.analysis_result_folder, 
                    config = self.phantom_config, 
                    notes=notes, 
                    metadata=metadata, 
                    log_message=self.log
                    )
            else: # 3d phantom
                
                if self.selected_series_name == None or self.selected_series_name == "":
                    self.log("Please select the phantom images first.")
                    return
                
                # copy files to the output folder
                # case output folder
                case_outdir = self.get_case_output_folder(self.selected_files[0])
                self.log(f'case output folder={case_outdir}')

                import shutil
                for i, src_file in enumerate(self.selected_files):
                    dst_file = os.path.join(case_outdir, f'input_{str(i).zfill(3)}.dcm' )
                    self.log(f'copying file...{src_file}-->{dst_file}')
                    shutil.copy(src_file, dst_file)
                
                self.analysis_input_folder = case_outdir
                self.analysis_result_folder = case_outdir
                
                
                module.run_analysis(device_id=self.device_id(),
                    input_dir = self.analysis_input_folder,
                    output_dir=self.analysis_result_folder, 
                    config = self.phantom_config, 
                    notes=notes, 
                    metadata=metadata, 
                    log_message=self.log
                    )
                

        except Exception as e:
            self.log(f"Error: {str(e)}")
        finally:
            self.run_button.config(state=tk.NORMAL)
            self.progress_bar.stop()
    
    def get_input_folder(self):

        intput_folder = self.input_folder_path.cget("text")
        if intput_folder == '':
            raise Exception("Please select an input folder")
        
        return intput_folder

    def get_output_folder(self):
        
        output_folder = self.output_folder_path.cget("text")
        if output_folder == '':
            raise Exception("Please select an output folder")

        if not os.path.exists(output_folder):
            self.log(f'output_folder not found. createing a folder: {output_folder}')
            os.makedirs(output_folder)
        
        return output_folder
    
    def get_phantom_folder(self):
        site = self.site()
        device = self.device()
        phantom = self.phantom()

        dirname = f'{site.lower()}_{device.lower()}_{phantom.lower()}'
        folder = os.path.join(self.get_output_folder(), dirname)

        if not os.path.exists(folder):
            self.log(f'folder not found. createing a folder: {folder}')
            os.makedirs(folder)
        
        return folder

    def get_case_output_folder(self, dicom_image_file):

        try:
            self.log('Getting instance creation date time from the dicom file...')
            dt_str = dicom_helper.get_instance_creation_datetime_str(dicom_image_file)
        except Exception as e:
            self.log('No instance creation date time found either. Using performed date.')
            dt_str = self.performed_by_combobox.get().replace('-', '')+'_000000'
        
        # copy all selected files 
        folder = os.path.join(self.get_phantom_folder(), dt_str)

        if not os.path.exists(folder):
            self.log(f'folder not found. createing a folder: {folder}')
            os.makedirs(folder)
        
        return folder

    
    def save_settings(self):
        # Save the current selections in a dictionary
        settings = {
            'input_folder': self.input_folder_path.cget("text"),
            'output_folder': self.output_folder_path.cget("text"),
            'performed_by': self.performed_by_combobox.get(), 
            'site': self.site_combobox.get(),
            'device': self.device_combobox.get(),
            'phantom': self.phantom_combobox.get(),
        }

        # Write the settings to the JSON file
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)

    def load_settings(self):
        # Load settings from the JSON file if it exists
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        return {}

    def on_closing(self):
        self.save_settings()
        self.root.destroy()

    def record_result_as_number1ds(self, result_data):
        # Configuration
        url = self.config['webservice_url'] + '/number1ds'
        app = f'{helper.get_app_name()} {APP_VERSION}'
        site_id = self.site()
        device_id = self.device()

        self.log(f'posting result number properties to {url}...')
        webservice.post_result_as_number1ds(
            result_data=result_data,
            app=app,
            site_id=site_id,
            device_id=device_id,
            phantom_id=self.phantom().lower(),
            url=url,
            log=self.log)
        
    def record_result_as_string1ds(self, result_data):
        # Configuration
        url = self.config['webservice_url'] + '/string1ds'
        app = f'{helper.get_app_name()} {APP_VERSION}'
        site_id = self.site()
        device_id = self.device()

        self.log(f'posting result string properties to {url}...')
        webservice.post_result_as_string1ds(
            result_data=result_data,
            app=app,
            site_id=site_id,
            device_id=device_id,
            phantom_id=self.phantom().lower(),
            url=url,
            log=self.log)

    def record_result_thread(self):
        if not hasattr(self, 'analysis_result_folder') or not os.path.exists(self.analysis_result_folder):
            self.log('Result folder not present. Please run your analysis first')
            return

        # Run analysis in a separate thread
        threading.Thread(target=self.record_result).start()


    def get_phantom_module(self):
        module_name =f'phantoms.{self.phantom().lower()}'
        self.log(f'Loading module...{module_name}')
        return importlib.import_module(module_name)

    def record_result(self):
        
        # Disable the "Run Analysis" button to prevent multiple clicks
        # self.push_to_server_button.config(state=tk.DISABLED)
        
        # Show progress
        #self.progress_label.config(text="Pushing data to server...")
        self.progress_bar.start()

        try:
            #phantom_module = self.get_phantom_module()

            #result_data = phantom_module.push_to_server(result_folder=self.analysis_result_folder, config = self.config, log_message=self.log)

            url = self.config['webservice_url'] +f'/{self.phantom().lower()}results'
            
            result_data = webservice.post_analysis_result(result_folder=self.analysis_result_folder, config = self.config, url=url, log_message=self.log)   
            

            self.record_result_as_number1ds(result_data)
            
            self.record_result_as_string1ds(result_data)

        except Exception as e:
            self.log(f"Error: {str(e)}")
            self.progress_bar.stop()

        finally:
            # Re-enable the button and stop progress indicator
            self.push_to_server_button.config(state=tk.NORMAL)
            #self.progress_label.config(text="Pushing to the server completed!")
            self.progress_bar.stop()

def main():
    # Show the splash screen first
    show_splash_screen()

    # Start the main application after splash
    root = tk.Tk()
    app = PyLinacGuiApp(root)
    root.mainloop()

# Main Application
if __name__ == "__main__":
    main()
