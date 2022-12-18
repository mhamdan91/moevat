Moevat (Moe visual annotation tool)
=======================================
## Table of Contents

 * [Overview](#overview)
 * [Library Installalion](#library-installalion)
 * [Library Usage](#library-usage)


## Overview
This tool allows you to quickly label images of up to 10 classes and this is basically because we  only have 10 numbers in NumPad :(O). If you have more than 10 classes, you can choose one class to be all others and reclassfiy others afterwards. This tool is meant for quick labeling and is not meant to be an extensive and manually controlled GUI.


## Library Installalion
To install the library simply run the following command in a cmd, shell or whatever...

```bash
# It's recommended to create a virtual environment

# Windows
pip install moevat

# Linux
pip3 install moevat
```

## Library usage?
To use this tool you need to provide:
- To show usage message run the following command `moevat -u`
- a directory containing images to label.
- an output file path to store labeled images in and this file can only be of type [json, csv]
- If you mislabel an image and wish to correct this, simply go back to that image and apply the new label.
- If you wish to copy or move labeled images after completing labeling, you must specify the
  `data-transfer` option where (**cp** -> copy, and **mv** -> move). You also need to specify a
  destination folder to transfer images to, this would be specifying the `dst-folder` option.
- If you wish to resize window size that displays image and labeling instructions, you can
  provide an integer value that is greater than 0. This value will translate into a percentage,
  e.g [60] == 60% of the original image size and [200] == 200% of the original image size.
- By default the tool will display the class names along with their human readable labels if
  you provide a labels.yaml file. This file contains classes and human readable labels in
  the following format: (See example: [labels.yaml](https://github.com/mhamdan91/moevat/blob/main/labels.yml))
```yaml
    # ** Good class names **
    classes:
        0: "dog"
        1: "cat"
        2: "horse"
        3: "mouse"
        4: "rabbit"
        5: "bird"
        6: "car"
        7: "human"
        8: "elephant"
        9: "house"

    # ** Okay class names **
    classes:
        0: "brown dog"
        1: "small cat"
        2: "original horse"
        3: "black mouse"
        4: "white rabbit"
        5: "big bird"
        6: "red car"
        7: "tall human"
        8: "tiny elephant"
        9: "huge house"

    # ** Bad class names **
    classes:
        0: "dog is barking at the mailman"
        1: "cat is sleeping deeply"
        2: "horse is racing very fast"
        3: "mouse is ticking extremely fast"
        4: "rabbit is jumping around"
        5: "bird is flying"
        6: "car is very ice"
        7: "human is playing well"
        8: "elephant is too huge to move"
        9: "house without windows"
```
- The tool will allow you navigate forward and backward, by default the tool allows you loop through
  images as long as you not labeled them all. This means you can start from **left -> right** or
  **right -> left**, i.e. from **last-image --> first-image** or from **first-image -> last-image**.
- The tool will automatically cache data while you are labeling, and if you wish to end your labeling
  session, simply click on **ESCAPE**.
- If you wish to resume labeling from where you stopped last time, simply provide the labels file which
  you used in the previous session and the tool will only show images that have not been labeled yet.


### Example use
Example use (in a terminal run the following command):
```bash
moevat -i <images_dir> -o <output_file_path.csv> -t <cp_or_mv> -d <destination_folder> -l <path_to_labels.yaml>
```

----------------------------------------
Author: Hamdan, Muhammad (@mhamdan91 - ©)
