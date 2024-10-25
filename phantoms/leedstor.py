import os
from pylinac import LeedsTOR
import phantoms

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
    phantom = LeedsTOR(input_file)
    params = config['analysis_params']
    
    phantom.analyze(low_contrast_threshold=params['low_contrast_threshold'],
                high_contrast_threshold=params['high_contrast_threshold'],
                #invert=False,
                #angle_override=False,
                #center_override=False,
                #size_override=False,
                ssd=params['ssd'],
                low_contrast_method=params['low_contrast_method'],
                visibility_threshold=params['visibility_threshold'],
                #x_adjustment=params['x_adjustment'],
                #y_adjustment=params['y_adjustment'],
                #angle_adjustment=params['angle_adjustment'],
                #roi_size_factor=params['roi_size_factor'],
                #scaling_factor=params['scaling_factor']
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

