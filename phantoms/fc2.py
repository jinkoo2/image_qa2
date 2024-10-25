import os
from pylinac import StandardImagingFC2
import phantoms.helper

def run_analysis(device_id, input_file, output_dir, config, notes, metadata, log_message):

    if not input_file:
        raise Exception(f"input_file not valid - {input_file}")

    if not os.path.exists(input_file):
        raise Exception(f"input_file not found - {input_file}")

    if not output_dir:
        raise Exception(f"output_dir not valid - {output_dir}")

    log_message(f'Input File: {input_file}')
    log_message(f'Output directory: {output_dir}')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Catphan analysis logic
    log_message('Running analysis...')
    phantom = StandardImagingFC2(input_file)
    params = config['analysis_params']
    
    phantom.analyze(
        invert=False,
        fwxm=params['fwxm'],
        bb_edge_threshold_mm=params['bb_edge_threshold_mm']
    )

    # print results
    log_message(phantom.results())

    file = os.path.join(output_dir, 'analyzed_image.png')
    log_message(f'saving image: {file}')
    phantom.save_analyzed_image(filename=file)

    phantoms.helper.copy_logo(config=config, output_dir=output_dir, log_message=log_message)
    
    phantoms.helper.save_result_as_pdf(phantom=phantom, output_dir=output_dir, config=config, notes=notes, metadata=metadata, log_message=log_message)

    phantoms.helper.save_result_as_txt(phantom=phantom, output_dir=output_dir, log_message=log_message)
    
    phantoms.helper.save_result_as_json(phantom=phantom, output_dir=output_dir, device_id=device_id, notes=notes, config=config, metadata=metadata, log_message=log_message)
    
    phantoms.helper.append_result_to_phantom_csv(phantom=phantom, output_dir=output_dir, device_id=device_id, notes=notes, metadata=metadata, log_message=log_message)


    log_message('Analysis completed.')

