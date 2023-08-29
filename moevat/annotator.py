import glob, csv, os, typing
import logging
import shutil
import json
import cv2
import numpy as np
from pathlib import Path
from moethread import parallel_call
from pynput import mouse, keyboard

logger = logging.getLogger(__name__)
lines = []
line_width = 1
x_scaling, y_scaling = 1, 1
t_image = None # Training image...
original_image = None
drawing = False
start_x, start_y = -1, -1
window_name = ''
line_width = 2
x_pos, y_pos = -1,-1
delete_line = False
overlayed_img = None

# Keyboard listener to detect Ctrl + Z
def on_key_release(key):
    if "\\x1a'" in str(key):
        pass
        # lines.pop() if lines else None
        # redraw_image()

def draw_line(event, x, y, flags, param):
    global drawing, start_x, start_y, t_image
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start_x, start_y = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            image_copy = np.copy(t_image)
            cv2.line(image_copy, (start_x, start_y), (x, y), (0, 0, 255), line_width)
            cv2.imshow(window_name, image_copy)


    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        end_x, end_y = x, y
        lines.append(((start_x, start_y), (end_x, end_y)))
        length = np.sqrt(((end_x - start_x)*x_scaling)**2 + ((end_y - start_y)*y_scaling)**2)
        lines[-1] = lines[-1] + (length,)
        redraw_image(t_image)
        

def redraw_image(image: np.ndarray):
    for line in lines:
        px_x_pos, px_y_pos = abs(line[1][0]-line[0][0]), abs(line[1][1]-line[0][1])
        _pos = (10 + line[0][0], line[0][1]) if px_x_pos < px_y_pos else (10 + line[1][0], line[1][1])
        cv2.line(image, line[0], line[1], (0, 0, 255), line_width)
        cv2.putText(image, f"{line[2]:.2f} px", tuple(_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), line_width)
    cv2.imshow(window_name, image)

# Set up the listener for Ctrl + Z
keyboard_listener = keyboard.Listener(on_release=on_key_release)
keyboard_listener.start()



def overlay_text(image, text, pos, font_color=(255, 255, 255)):
    # Calculate the font scale based on the image dimensions
    font_scale = min(image.shape[1], image.shape[0]) / 1100.0  # Adjust 800 as needed
    # Set the font, color, thickness, and other parameters
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_thickness = 1
    # Calculate the size of the text bounding box
    text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
    text_width, text_height = text_size
    # Calculate the position to center the text
    text_x = text_width + pos[1]
    text_y = text_height + pos[0]

    cv2.putText(image, text, pos, font, font_scale, font_color, font_thickness)

def resize_img(image, size):
    return cv2.resize(image, size, interpolation=cv2.INTER_AREA)

def write_results(output_name: str, labels_dict: typing.Dict):
    if os.path.splitext(output_name)[-1].lower() == '.csv':
        header = ['image_name', 'label', 'class']
        with open(output_name, newline='', mode='w') as of:
            writer = csv.DictWriter(of, fieldnames=header)
            writer.writeheader()
            for value in labels_dict.values():
                writer.writerow(value)
    else:
        with open(output_name, mode='w') as of:
            json.dump(labels_dict, of, separators=[',', ':'], indent=4)

def load_existing_labels(output_name: str) -> typing.Dict:
    existing_labels = {}
    existing_labels_dict = {}
    file_format = os.path.splitext(output_name)[-1].lower()
    if os.path.isfile(output_name):
        with open(output_name) as f:
            if file_format == '.csv':
                existing_labels = list(csv.DictReader(f))
            elif file_format == '.json':
                existing_labels = json.load(f)
            else:
                return existing_labels_dict
    if existing_labels:
        iterator = existing_labels if file_format == '.csv' else existing_labels.values()
        for _dict in iterator:
            image_name = os.path.splitext(_dict.get('image_name'))[0]
            existing_labels_dict[image_name] = _dict
    return existing_labels_dict

def annotate(images_path: str, output_name: str, classes: typing.Any, data_transfer: str,
             dst_folder: str, window_size: int, monitor_dims: tuple, show_class_names: bool=True,
             loop: bool=True, measure: bool=False, save_overlay: bool=False):
    """
        https://docs.opencv.org/4.x/d4/da8/group__imgcodecs.html

        Windows bitmaps - .bmp, .dib (always supported)
        JPEG files - .jpeg, .jpg, *.jpe (see the Note section)
        JPEG 2000 files - *.jp2 (see the Note section)
        Portable Network Graphics - *.png (see the Note section)
        WebP - *.webp (see the Note section)
        Portable image format - .pbm, .pgm, .ppm .pxm, *.pnm (always supported)
        PFM files - *.pfm (see the Note section)
        Sun rasters - .sr, .ras (always supported)
        TIFF files - .tiff, .tif (see the Note section)
        OpenEXR Image files - *.exr (see the Note section)
        Radiance HDR - .hdr, .pic (always supported)

    """
    global t_image, x_pos, y_pos, window_name
    window_width = 130
    tooltip_string = ""
    if classes and show_class_names:
        tmp = []
        for key, value in classes.items():
            tmp.append(f"{value.upper()}: {key}")
        tooltip_string = ' | '.join(tmp)
    if len(tooltip_string) > window_width:
        rows = np.ceil(len(tooltip_string) / window_width)
        break_point = int(len(classes) / rows)
        tmp = []
        tooltip_strings =[]
        for i, (key, value) in enumerate(classes.items()):
            if i % break_point == 0 and i != 0:
                tooltip_strings.append(' | '.join(tmp))
                tmp = []
            tmp.append(f"{value.upper()}: {key}")
        tooltip_strings.append(' | '.join(tmp))
    else:
        tooltip_strings = [tooltip_string]
    if len(tooltip_strings) > 3:
        logger.warning("You have very long class names, this is not recommened. Tooltip will look confusing.")
    supported_formats = ['.bmp', '.dib', '.jpg', '.jpeg', '.jpe', '.jp2', '.png', '.webp', '.pmb', '.pmg',
                         '.ppm', '.pxm', '.pnm', '.pfm', '.sr', '.ras', '.tiff', '.tif', '.exr', '.hdr', '.pic']
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 0.8
    fontColor = (0,100,0)
    thickness = 2
    lineType = 1
    existing_labels_dict = load_existing_labels(output_name)
    items = glob.glob(os.path.join(images_path, "**"), recursive=True)
    # Filter items based on existing labeled images and supported formats...
    items = [item for item in items if os.path.splitext(item.split(os.sep)[-1])[0] not in existing_labels_dict and \
             os.path.splitext(item.split(os.sep)[-1])[1].lower() in supported_formats]
    if not items:
        logger.warning("No items to label. If you wish to relabel, then delete the labels file in path. Early termination")
        return
    key = 0
    forward = 0
    labels_dict = {}
    num_items   = len(items)
    # Description area size...
    dsize = int(50 * (75 + 25 * len(tooltip_strings)) / 90) if show_class_names else 40
    while forward < num_items:
        image_path = items[forward]
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        path_list = image_path.split(os.sep)
        full_image_name = path_list[-1]
        description_area = img[:dsize, :]
        description_area[:,:, 0] = 245
        description_area[:,:, 1] = 245
        description_area[:,:, 2] = 245
        y_start = int(window_size[1]/360 * 15) # Smallest supported y-size is 360...
        y_end = int(y_start * 35/15) # Smallest supported y-size is 360...
        img = np.vstack((description_area, img))
        org_image = resize_img(img, window_size)
        text = f"CURRENT ITEM: {forward + 1} | OUT OF {num_items} || CLICK ESACPE TO TERMINATE LABELING SESSION"
        overlay_text(org_image, text, (7, y_start), (0, 0, 180))
        text = "NEXT: RIGHT/UP ARROW | PREVIOUS: LEFT/DOWN ARROW"
        overlay_text(org_image, text, (7, y_end), (0, 180, 0))
        t_image = np.copy(org_image)
        if show_class_names:
            for i, tooltip_string in enumerate(tooltip_strings):
                red = min(255, 75*i)
                green = min(25*i, 255)
                cv2.putText(img, tooltip_string, (7, 100 + 25*i), font, 0.6, (150, green, red), thickness, lineType)
        # Show GUI...
        window_name = f"Moevat"
        x_pos = (monitor_dims[0] - window_size[0]) // 2
        y_pos = (monitor_dims[1] - window_size[1]) // 2
        if key != 26:
            cv2.imshow(window_name, t_image)
            cv2.moveWindow(window_name, x_pos, y_pos)
            cv2.setMouseCallback(window_name, draw_line)

        key = cv2.waitKeyEx(0)
        label = -1
        # up or right
        if key == 2490368 or key == 2555904:
            forward += 1
        # down or left
        elif key == 2621440 or key == 2424832:
            forward -= 1
            forward = forward % num_items
        # escape
        elif key == 27 or key == ord('q'):
            cv2.destroyAllWindows()
            break
        elif 47 < key < 58:
            label = key - 48
            forward += 1
        elif key == 26: # Update image...
            lines.pop()
            redraw_image(org_image)
        else:
            logger.warning(f"Invalid keystroke.")
            continue
        if loop:
            forward = forward % num_items
        

        if label > -1:
            klass = classes[label] if classes else label
            labels_dict[image_path] = {"image_name": full_image_name, "label": str(label), "class": str(klass)}
            logger.info(f" Labeled: {len(labels_dict)} out of {num_items} | {labels_dict[image_path]}")
            # Cache labeled data...
            tmp = {}
            tmp.update(existing_labels_dict)
            tmp.update(labels_dict)
            write_results(output_name, tmp)
        if len(labels_dict) == num_items:
            message = np.ones((50, 900, 3))
            title = "THANK YOU! Labeling is complete, program will exit shortly..."
            cv2.putText(message, title, (7, 25), font, fontScale, fontColor, thickness, lineType)
            cv2.imshow("THANK YOU", message)
            cv2.moveWindow("THANK YOU", 350, 300)
            cv2.waitKey(2000)
            break

    cv2.destroyAllWindows()
    new_labeled_data = labels_dict.copy()
    if new_labeled_data:
        logger.info("Writing data to file...")
        labels_dict.update(existing_labels_dict)
        write_results(output_name, labels_dict)
    if data_transfer in ['mv', 'cp'] and new_labeled_data:
        if not os.path.isdir(dst_folder):
            _dst_folder = Path(dst_folder)
            _dst_folder.mkdir(parents=True, exist_ok=True)

        logger.info(f"Data/images will be transfered to: {dst_folder}")
        if data_transfer == 'mv':
            # Moving images from source directory to destination directory
            command = shutil.move
        else:
            # Copying images from source directory to destination directory
            command = shutil.copyfile

        @parallel_call
        def transfer_data(**kwargs):
            image_path = kwargs.get('data', {}).get('image_path', '')
            image_name = image_path.split(os.sep)[-1]
            class_label = kwargs.get('data', {}).get('class_label', '')
            dist_path = Path(os.path.join(dst_folder, class_label))
            dist_path.mkdir(parents=True, exist_ok=True)
            command(image_path, os.path.join(dist_path, image_name))
        paths = []
        class_labels = []
        for key, value in new_labeled_data.items():
            paths.append(key)
            class_labels.append(value.get('class', ''))
        action = 'Moving' if command == shutil.move else 'Copying'
        logger.info(f"{action} data from source directory to destination directory...")
        transfer_data(data={'image_path': paths, 'class_label': class_labels}, threads=1)

