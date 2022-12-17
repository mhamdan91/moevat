import glob, csv, os, typing
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)
logger_format='[%(asctime)s | %(name)s | LN%(lineno)s | %(levelname)s]: %(message)s'
logging.basicConfig(level=logging.INFO, format=logger_format)

def resize_img(image, x=850, y=640):
    shape = image.shape
    _y = shape[0]
    _x = shape[1]
    if _y < y:
        x = _x
        y = _y
    return cv2.resize(image, (x, y), interpolation=cv2.INTER_AREA)

def write_results(output_path: str, labels_dict: typing.Dict):
    header = ['image_name', 'label', 'class']
    with open(output_path, newline='', mode='w') as of:
        writer = csv.DictWriter(of, fieldnames=header)
        writer.writeheader()
        for key, value in labels_dict.items():
            writer.writerow(value)

def annotate(images_path: str, output_path: str, config: typing.Dict, tooltip: bool=False, loop: bool=True):
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
    supported_formats       = ['.bmp', '.dib', '.jpg', '.jpeg', '.jpe', '.jp2', '.png', '.webp', '.pmb', '.pmg',
                               '.ppm', '.pxm', '.pnm', '.pfm', '.sr', '.ras', '.tiff', '.tif', '.exr', '.hdr', '.pic']
    font                    = cv2.FONT_HERSHEY_SIMPLEX
    fontScale               = 0.8
    fontColor               = (0,100,0)
    thickness               = 2
    lineType                = 1
    
    classes = {"0": "unknown", "1": "fm_strings", "2": "fm_blob", "3": "fm_spots", "4": "burn", "5": "ring", "6": "rust_spots", "7": "big_metal", "8": "nvd"}
    existing_labels = {}
    if os.path.isfile(output_path):
        with open(output_path) as f:
            existing_labels = list(csv.DictReader(f))

    existing_labels_dict = {}
    if existing_labels:
        for _dict in existing_labels:
            image_name = os.path.splitext(_dict.get('image_name'))[0]
            existing_labels_dict[image_name] = _dict

    items = glob.glob(images_path, recursive=True)
    # Filter items based on existing labeled images and supported formats...
    items = [item for item in items if os.path.splitext(item.split(os.sep)[-1])[0] not in existing_labels_dict and \
             os.path.splitext(item.split(os.sep)[-1])[1].lower() in supported_formats]
    num_items   = len(items)
    forward     = 0
    labels_dict = {}
    while forward < num_items:
        image_path  = items[forward]
        img         = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        path_list   = image_path.split(os.sep)
        full_image_name  = path_list[-1]
        image_name       = os.path.splitext(full_image_name)[0]
        if tooltip:
            description_area = img[:30, :]
            description_area[:,:, 0]  = 255
            description_area[:,:, 1]  = 255
            description_area[:,:, 2]  = 255
            img = np.vstack((description_area, img))
            cv2.putText(img, "UNKNOWN: 0 | FM_STRINGS: 1 | FM_BLOB: 2 | FM_SPOTS: 3 | BURN: 4 | RING: 5 | RUST_SPOTS: 6 | BIG_METAL: 7 | NVD: 8", 
                        (7, 20), font, 0.6, (180,0,0), thickness, lineType)
            cv2.putText(img, "NEXT: RIGHT/UP ARROW | PREVIOUS: LEFT/DOWN ARROW", (7, 50), font, fontScale, (0,180,0), thickness, lineType)

        title = f"current_image: {forward+1} | out of {num_items} || Click Escape to terminate labeling session."
        cv2.imshow(title, resize_img(img))
        cv2.moveWindow(title, 250, 96)
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
        elif key == 27:
            cv2.destroyAllWindows()
            break
        elif 47 < key < 58:
            label = key - 48
            forward += 1
        else:
            logger.warning("Invalid keystroke...")
            continue
        if loop:
            forward = forward % num_items
        cv2.destroyAllWindows()

        if label > -1:
            labels_dict[image_name] = {"image_name": full_image_name, "label": label, "class": classes[str(label)]}
            logger.info(f" Labeled: {len(labels_dict)} out of {num_items} | {labels_dict[image_name]}")
        if len(labels_dict) == num_items:
            message = np.ones((50, 900, 3))
            title = "THANK YOU! Labeling is complete, program will exit shortly..."
            cv2.putText(message, title, (7, 25), font, fontScale, fontColor, thickness, lineType)
            cv2.imshow("THANK YOU", message)
            cv2.moveWindow("THANK YOU", 350, 300)
            cv2.waitKey(2000)
            break

    logger.info("Writing data to disk...")
    labels_dict.update(existing_labels_dict)
    write_results(output_path, labels_dict)
    cv2.destroyAllWindows()

