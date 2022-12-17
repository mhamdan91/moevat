import click
import typing
import yaml
import os
from pathlib import Path

CONTEXT_SETTINGS    = dict(help_option_names=['-h', '--help'], max_content_width=150)
FILE_TYPE           = click.Path(exists=True, dir_okay=False, resolve_path=True)
DIRECTORY_TYPE      = click.Path(exists=True, file_okay=False, resolve_path=True)


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
        not_present = self.name not in opts
        dependency_present = self.required_if in opts
        if dependency_present and not not_present:
            raise click.UsageError(
                "Invalid usage: `%s` is required with `%s`" % (
                    self.name, self.required_if))
        else:
            self.prompt = None
        return super(RequiredIf, self).handle_parse_result(ctx, opts, args)


@click.command(short_help="Command-line interface to label images. Refer to https://github.com/mhamdan91/moevat",
             context_settings=CONTEXT_SETTINGS)
@click.option('--images-path',  '-i',   required=True,
                                        type=DIRECTORY_TYPE,
                                        help="Directory containing images.")
@click.option('--output-name',  '-o',   type=click.Path(exists=False, dir_okay=False, resolve_path=False),
                                        default="labels.csv",
                                        show_default=True,
                                        help="(optional) Output csv filename to store labels.",)
@click.option('--labels-path',  '-l',   required=True,
                                        type=click.Path(exists=True, dir_okay=False, resolve_path=True),
                                        help="Path to yaml labels file. See example: https://github.com/mhamdan91/moevat")
@click.option('--data-transfer','-d',   type=click.Choice(['cp', 'mv'], case_sensitive=False),
                                        cls=RequiredIf,
                                        required_if='dst_folder',
                                        default="NONE",
                                        show_default=True,
                                        help="(optional) Copy (cp) or move (mv) data from source to destination folder " \
                                             "after completing labeling.")
@click.option('--dst-folder',   '-f',   type=DIRECTORY_TYPE,
                                        default="labeled_data",
                                        show_default=True,
                                        help="(optional) Destination folder for labeled images.")
@click.option('--window-size',  '-w',   type=int,
                                        default=800,
                                        show_default=True,
                                        help="(optional) Annotation window size (integer between 200-2000) to display images.")
@click.option('--show-tooltip', '-t',   is_flag=True,
                                        help="(optional) Flag to show tooltip while annotating.")
def cli(images_path: DIRECTORY_TYPE, output_name: str, labels_path: str, data_transfer: bool,
        dst_folder, window_size, show_tooltip, *args: typing.Any, **kwargs: typing.Any) -> None:
    
    if not os.path.isdir(dst_folder):
        dst_folder = Path(dst_folder)
        dst_folder.mkdir(parents=True, exist_ok=True)

    
    from annotator import annotate
    classes = {}
    with open(labels_path) as f:
        classes = yaml.safe_load(f)
    annotate(images_path, output_name, classes, data_transfer, dst_folder, window_size, show_tooltip)


def main() -> None:
    cli(prog_name='moevat')

if __name__ == '__main__':
    main()
