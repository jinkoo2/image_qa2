import os
from pylinac import CatPhan604, CatPhan600, CatPhan504, CatPhan503
import phantoms.helper 

def run_analysis(device_id, input_dir, output_dir, config, notes, metadata, log_message):

    if not input_dir:
        log_message("Error: Please select the input folder.")
        return

    if not output_dir:
        output_dir = os.path.join(input_dir, 'out')

    log_message(f'Input directory: {input_dir}')
    log_message(f'Output directory: {output_dir}')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Catphan analysis logic
    catphan_model = config['catphan_model']
    log_message(f'Phantom model: {catphan_model}')
    
    if catphan_model == '604':
        phantom = CatPhan604(input_dir)
    elif catphan_model == '600':
        phantom = CatPhan600(input_dir)
    elif catphan_model == '504':
        phantom = CatPhan504(input_dir)
    elif catphan_model == '503':
        phantom = CatPhan503(input_dir)
    else:
        log_message(f'Error:Unknown CatPhan model: {catphan_model}!')
        return
    
    log_message('Running analysis...')
    params = config['analysis_params']
    phantom.analyze(
        hu_tolerance=params['hu_tolerance'],
        scaling_tolerance=params['scaling_tolerance'],
        thickness_tolerance=params['thickness_tolerance'],
        low_contrast_tolerance=params['low_contrast_tolerance'],
        cnr_threshold=params['cnr_threshold'],
        zip_after=False,
        contrast_method=params['contrast_method'],
        visibility_threshold=params['visibility_threshold'],
        thickness_slice_straddle=params['thickness_slice_straddle'],
        expected_hu_values=params['expected_hu_values']
    )

    # print results
    log_message(phantom.results())

    file = os.path.join(output_dir, 'analyzed_image.png')
    log_message(f'saving image: {file}')
    phantom.save_analyzed_image(filename=file)
    
    sub_image_header = os.path.join(output_dir, 'analyzed_subimage')
    #* ``hu`` draws the HU linearity image.
    #* ``un`` draws the HU uniformity image.
    #* ``sp`` draws the Spatial Resolution image.
    #* ``lc`` draws the Low Contrast image (if applicable).
    #* ``mtf`` draws the RMTF plot.
    #* ``lin`` draws the HU linearity values. Used with ``delta``.
    #* ``prof`` draws the HU uniformity profiles.
    #* ``side`` draws the side view of the phantom with lines of the module locations.
    sub_image_list = ['hu', 'un', 'sp', 'lc', 'mtf', 'lin', 'prof', 'side']
    for sub in sub_image_list:
        try:
            dst = f'{sub_image_header}.{sub}.png'
            log_message(f'saving sub image: {dst}')
            phantom.save_analyzed_subimage(filename=dst, subimage=sub)
        except:
            pass

    phantoms.helper.copy_logo(config=config, output_dir=output_dir, log_message=log_message)
    
    phantoms.helper.save_result_as_pdf(phantom=phantom, output_dir=output_dir, config=config, notes=notes, metadata=metadata, log_message=log_message)

    phantoms.helper.save_result_as_txt(phantom=phantom, output_dir=output_dir, log_message=log_message)
    
    phantoms.helper.save_result_as_json(phantom=phantom, output_dir=output_dir, device_id=device_id, notes=notes, config=config, metadata=metadata, log_message=log_message)
    
    phantoms.helper.append_result_to_phantom_csv(phantom=phantom, output_dir=output_dir, device_id=device_id, notes=notes, metadata=metadata, log_message=log_message)

    log_message('Analysis completed.')
