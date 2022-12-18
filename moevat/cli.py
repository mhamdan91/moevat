# @mhamdan
# MIT License

# Copyright (c) 2022 Muhammad Hamdan

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import click
import typing
import yaml
import os
import logging
from pathlib import Path
from moevat.annotator import annotate
import ctypes



CONTEXT_SETTINGS    = dict(help_option_names=['-h', '--help'], max_content_width=150)
FILE_TYPE           = click.Path(exists=True, dir_okay=False, resolve_path=True)
DIRECTORY_TYPE      = click.Path(exists=True, file_okay=False, resolve_path=True)

logger = logging.getLogger(__name__)
# logger_format='[%(asctime)s | %(name)s | LN%(lineno)s | %(levelname)s]: %(message)s'
logger_format='[%(asctime)s | MOEVAT | %(levelname)s]: %(message)s'
logging.basicConfig(level=logging.INFO, format=logger_format)

# Control help message...
def command_required_option_from_option(require_name, require_map):
    # https://stackoverflow.com/questions/55585564/python-click-formatting-help-text
    class CommandOptionRequiredClass(click.Command):
        def get_help(self, ctx):
            orig_wrap_test = click.formatting.wrap_text
            def wrap_text(text, width=78, initial_indent='',
                          subsequent_indent='',
                          preserve_paragraphs=False):
                return orig_wrap_test(text.replace('\n', '\n\n'), width,
                                      initial_indent=initial_indent,
                                      subsequent_indent=subsequent_indent,
                                      preserve_paragraphs=True
                                      ).replace('\n\n', '\n')
            click.formatting.wrap_text = wrap_text
            return super(CommandOptionRequiredClass, self).get_help(ctx)
    return CommandOptionRequiredClass

# Dependable options...
class RequiredIf(click.Option):
    # https://stackoverflow.com/questions/44247099/click-command-line-interfaces-make-options-required-if-other-optional-option-is
    def __init__(self, *args, **kwargs):
        self.required_if = kwargs.pop('required_if')
        assert self.required_if, "'required_if' parameter required"
        kwargs['help'] = (kwargs.get('help', '') + ' NOTE: This argument is required with %s' %
                          self.required_if).strip()
        super(RequiredIf, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        present = self.name in opts
        dependency_not_present = self.required_if not in opts
        if dependency_not_present and present:
            raise click.UsageError(
                "Invalid usage: `%s` is required with `%s`" % (
                    self.name, self.required_if))
        else:
            self.prompt = None
        return super(RequiredIf, self).handle_parse_result(ctx, opts, args)

# Dependable options...
class NotRequiredIf(click.Option):
    # https://stackoverflow.com/questions/44247099/click-command-line-interfaces-make-options-required-if-other-optional-option-is
    def __init__(self, *args, **kwargs):
        self.not_required_if = kwargs.pop('not_required_if')
        assert self.not_required_if, "'not_required_if' parameter required"
        kwargs['help'] = (kwargs.get('help', '') + ' NOTE: This argument is required').strip()
        super(NotRequiredIf, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        not_present = self.name not in opts
        exclusive_option_present = self.not_required_if in opts
        if not exclusive_option_present and not_present:
            raise click.UsageError(
                "Invalid usage: `%s` is required" % (self.name))
        else:
            self.prompt = None
        return super(NotRequiredIf, self).handle_parse_result(ctx, opts, args)


@click.command(short_help="Command-line interface to label images. " \
                          "Refer to https://github.com/mhamdan91/moevat",
             context_settings=CONTEXT_SETTINGS)
@click.option('--images-path',  '-i',   type=DIRECTORY_TYPE,
                                        cls=NotRequiredIf,
                                        not_required_if='show_usage',
                                        help="Directory containing images.")
@click.option('--output-name',  '-o',   type=click.Path(exists=False, dir_okay=False, resolve_path=False),
                                        cls=NotRequiredIf,
                                        not_required_if='show_usage',
                                        show_default=True,
                                        help="Output file path where labels will be to stored. (supported file formats are [csv, json])")                                 
@click.option('--labels-path',  '-l',   type=click.Path(exists=True, dir_okay=False, resolve_path=True),
                                        help="(optional) Required only if you wish to provide human readable classes to your data. " \
                                             "See example labels yaml file: https://github.com/mhamdan91/moevat/blob/main/labels.yml")
@click.option('--dst-folder',   '-d',   type=click.Path(exists=False, file_okay=False, resolve_path=False),
                                        help="(optional) Destination folder for labeled images.")
@click.option('--data-transfer','-t',   type=click.Choice(['cp', 'mv', 'none'], case_sensitive=False),
                                        cls=RequiredIf,
                                        required_if='dst_folder',
                                        default="none",
                                        show_default=True,
                                        help="(optional) Copy [cp] or move [mv] data from source to destination folder " \
                                             "after completing labeling.")
@click.option('--window-size',  '-w',   type=int,
                                        default=60,
                                        show_default=True,
                                        help="(optional) Percentage (integer greater than zero) of original image size. " \
                                             "Default display 60% of the original image size.")
@click.option('--hide-labels',  '-x',   is_flag=True,
                                        help="(optional) Flag to hide class/label names while annotating.")
@click.option('--no-loop',      '-n',   is_flag=True,
                                        help="(optional) Flag to stop looping over the dataset. " \
                                             "By default user can navigate forward and backward, "
                                             "e.g. start from left to right or right to left.")
@click.option('--show-usage',   '-u',   is_flag=True,
                                        help="(optional) Show detailed usage of the tool with examples and exit.")
def cli(images_path: str, output_name: str, labels_path: str, data_transfer: bool,
        dst_folder, window_size, hide_labels, no_loop: str, show_usage: bool, *args: typing.Any, **kwargs: typing.Any) -> None:
    if show_usage:
        print(
        """ 
This tool allows you to quickly label images of up to 10 classes and this is basically because we 
only have 10 numbers in NumPad :(O). If you have more than 10 classes, you can choose one class 
to be all others and reclassfiy others afterwards. This tool is meant for quick labeling and is
not meant to be an extensive and manually controlled GUI. 

To use this tool you need to provide:
- a directory containing images to label.
- an output file path to store labeled images in and this file can only be of type [json, csv]
- If you mislabel an image and wish to correct this, simply go back to that image and apply the new label.
- If you wish to copy or move labeled images after completing labeling, you must specify the 
  `data-transfer` option where (cp -> copy, and mv -> move). You also need to specify a 
  destination folder to transfer images to, this would be specifying the `dst-folder` option.
- If you wish to resize window size that displays image and labeling instructions, you can 
  provide an integer value that is greater than 0. This value will translate into a percentage, 
  e.g [60] == 60% of the original image size and [200] == 200% of the original image size.
- By default the tool will display the class names along with their human readable labels if
  you provide a labels.yaml file. This file contains classes and human readable labels in 
  the following format: (you can download this example from: https://github.com/mhamdan91/moevat/blob/main/labels.yml)
    
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

- The tool will allow you navigate forward and backward, by default the tool allows you loop through
  images as long as you not labeled them all. This means you can start from left -> right or 
  right -> left, i.e. from last-image --> first-image or from first-image -> last-image.
- The tool will automatically cache data while you are labeling, and if you wish to end your labeling
  session, simply click on ESCAPE.
- If you wish to resume labeling from where you stopped last time, simply provide the labels file which
  you used in the previous session and the tool will only show images that have not been labeled yet.

Example use (in a terminal run the following command):
> moevat -i <images_dir> -o <output_file_path.csv> -t <cp_or_mv> -d <destination_folder> -l <path_to_labels.yaml>


        """)
        return
    
    logger.info("MAKE SURE NumLock is ON...")
    loop = False if no_loop else True
    show_class_names = False if hide_labels else True
    
    tmp = list(os.path.splitext(output_name))
    if tmp[-1].lower() not in ['.csv', '.json']:
        logger.warning(f'Unsupported file format [{tmp[-1]}]. Defaulting to [csv]. Supported formats are [csv, json].')
        tmp[-1] = '.csv'
    output_dir = Path(f'{os.sep}'.join(tmp[0].split(os.sep)[:-1]))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_name = f''.join(tmp)

    if window_size < 1:
        logger.warning(f"Received improper window size [{window_size}], setting to default: [60] (%).")
        window_size = 60
    classes = {}
    if labels_path:
        try:
            with open(labels_path) as f:
                classes = yaml.safe_load(f)
        except Exception as e:
            logger.exception(f"Invalid labels file ['{labels_path}']\n\n{e}")
            return
        else:
            classes = classes.get(next(iter(classes)), {})
    logger.info(f"Labeled data will be saved to: {os.path.abspath(output_name)}")
    annotate(images_path, output_name, classes, data_transfer, dst_folder, window_size, show_class_names, loop)

def main() -> None:
    cli(prog_name='moevat')

if __name__ == '__main__':
    main()
