import json
import requests
import os
from utils.helper import zip_folder
from utils.model import convert_kvps_to_number1d_or_stirng1d_list
from utils.object import traverse_and_collect_numbers, traverse_and_collect_strings

def post(obj, url):
    # POST the result.json to the API
    headers = {'Content-Type': 'application/json'}

    print(f'Sending result.json to {url}...')
    response = requests.post(url, json=obj, headers=headers)

    # Check if the request was successful
    if response.status_code in [200, 201]:
        print("Record successfully sent to the server.")
        return response.json()
    else:
        raise Exception(f"Failed to send record: {response.status_code} - {response.text}")

def upload_zip_file(filepath, url):

    # Open the zip file in binary mode
    with open(filepath, 'rb') as file:
        # Create a dictionary for the file to upload
        files = {'file': (os.path.basename(filepath), file, 'application/zip')}
        
        # Make a POST request to upload the file
        response = requests.post(url, files=files)

        # Check the response status code
        if response.status_code in (200, 201):
            print(f"File {filepath} uploaded successfully.")
            return response.json()
        else:
            raise Exception(f"Failed to upload file: {response.status_code} - {response.text}")
        
def post_analysis_result(result_folder, config, url, log_message):
    
    temp_folder = config['temp_folder']
    
    if not result_folder or not os.path.exists(result_folder):
        raise Exception("The result folder not found.")
    
    # Zip the input folder
    log_message(f"Zipping input folder: {result_folder}")
    zip_filepath = zip_folder(result_folder, f'catphan_', temp_folder)
    log_message(f"Result folder zipped at: {zip_filepath}")
    
    # Get the upload URL from config
    zip_upload_url = config['webservice_url'] + '/upload'

    # Upload the zip file to the server
    log_message(f"Uploading zip file: {zip_filepath} to {zip_upload_url}")
    res = upload_zip_file(zip_filepath, zip_upload_url)

    if res != None:
        log_message("Zip file uploaded successfully.")
        log_message(f"Removing zip file....{zip_filepath}")
        os.remove(zip_filepath)

        uploaded_zip_filename = res['fileName']
    else:
        raise Exception("Failed uplaoding zip file!")

    # Ensure the result.json file exists
    result_json = os.path.join(result_folder, 'result.json')

    if not os.path.exists(result_json):
        raise Exception("The result.json file does not exist. Run the analysis first.")

    # Read the result.json file
    with open(result_json, 'r') as json_file:
        result_data = json.load(json_file)

    # add zip filename
    result_data['file'] = uploaded_zip_filename

    # POST the result.json to the API
    res = post(obj=result_data, url=url)

    if res != None:
        # Assuming the API returns the created document with the _id field
        if '_id' in res:
            document_id = res['_id']
    else:
        raise Exception('Failed posting phantom analysis result!')

    return result_data

def post_result_as_number1ds(result_data, app, site_id, device_id, phantom_id, url, log):
    # travese the result object and collect numbers
    log('collecting numbers from the result file...')
    kvps = traverse_and_collect_numbers(result_data)

    # convert the numbers key value pairs to number1d objects
    log('converting numbers kvps to number1d objects...')
    number1ds = convert_kvps_to_number1d_or_stirng1d_list(key_value_pairs=kvps, 
                                                            key_prefix=f'{phantom_id.lower()}_',
                                                            device_id=f'{site_id}|{device_id}', 
                                                            app=app)

    log(f'posting the number1d array to the server... url={url}')
    res = post(number1ds, url=url)
    if res != None:
        log("Post succeeded!")
        return res
    else:
        raise Exception("Post failed!")
    
def post_result_as_string1ds(result_data, app, site_id, device_id, phantom_id, url, log):
    # travese the result object and collect numbers
    log('collecting strings from the result file...')
    kvps = traverse_and_collect_strings(result_data)

    # convert the numbers key value pairs to number1d objects
    log('converting numbers kvps to string1d objects...')
    string1ds = convert_kvps_to_number1d_or_stirng1d_list(key_value_pairs=kvps, 
                                                            key_prefix=f'{phantom_id.lower()}_',
                                                            device_id=f'{site_id}|{device_id}', 
                                                            app=app)

    log(f'posting the string1d array to the server... url={url}')
    res = post(string1ds, url=url)
    if res != None:
        log("Post succeeded!")
        return res
    else:
        raise Exception("Post failed!")
          
if __name__ == '__main__':
    # Example usage with a result.json object
    result_json = {
        "measurement": {
            "temperature": 25.4,
            "pressure": 101.3,
            "details": {
                "humidity": 60,
                "altitude": 300.2,
                "complex_data": {
                    "value-1": 42.0,
                    "value 2": 19.5,
                    "Value!": 37
                }
            }
        }
    }

