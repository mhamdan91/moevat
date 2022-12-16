import click
import typing

CONTEXT_SETTINGS    = dict(help_option_names=['-h', '--help'])
FILE_TYPE           = click.Path(exists=True, dir_okay=False, resolve_path=True)
DIRECTORY_TYPE      = click.Path(exists=True, file_okay=False, resolve_path=True)

@click.command(short_help="Command-line interface to label images for Post-Saw FM",
             context_settings=CONTEXT_SETTINGS)
@click.option('--images-path',  '-i', type=DIRECTORY_TYPE, required=True, help="input directory containing images")
@click.option('--output-name',  '-o', type=click.Path(exists=False, dir_okay=False, resolve_path=True),
                                      help="(optional) Output csv filename to store labeled data in, default: 'labels.csv'", default="labels.csv")
@click.option('--show-tooltip', '-a', is_flag=True, help="(optional) Show tooltip")                                      
def cli(images_path: DIRECTORY_TYPE, output_name: str, show_tooltip: bool, *args: typing.Any, **kwargs: typing.Any) -> None:
    from annotator import annotate
    labeler(images_path, output_name, show_tooltip)


def main() -> None:
    cli(prog_name='moevat')

if __name__ == '__main__':
    main()
