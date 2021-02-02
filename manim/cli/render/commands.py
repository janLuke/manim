from inspect import Traceback
import os
import sys
import click

from manim import config, logger

from manim.constants import EPILOG
from manim.constants import CONTEXT_SETTINGS
from manim.utils.module_ops import scene_classes_from_file
from manim.utils.file_ops import open_file as open_media_file

from pathlib import Path

from click_option_group import optgroup


def open_file_if_needed(file_writer):
    if config["verbosity"] != "DEBUG":
        curr_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    open_file = any([config["preview"], config["show_in_file_browser"]])

    if open_file:
        file_paths = []

        if config["save_last_frame"]:
            file_paths.append(file_writer.image_file_path)
        if config["write_to_movie"] and not config["save_as_gif"]:
            file_paths.append(file_writer.movie_file_path)
        if config["save_as_gif"]:
            file_paths.append(file_writer.gif_file_path)

        for file_path in file_paths:
            if config["show_in_file_browser"]:
                open_media_file(file_path, True)
            if config["preview"]:
                open_media_file(file_path, False)

    if config["verbosity"] != "DEBUG":
        sys.stdout.close()
        sys.stdout = curr_stdout


class _AttributeHolder(object):
    """Abstract base class that provides __repr__.

    The __repr__ method returns a string in the format::
        ClassName(attr=name, attr=name, ...)
    The attributes are determined either by a class-level attribute,
    '_kwarg_names', or by inspecting the instance __dict__.
    """

    def __repr__(self):
        type_name = type(self).__name__
        arg_strings = []
        star_args = {}
        for arg in self._get_args():
            arg_strings.append(repr(arg))
        for name, value in self._get_kwargs():
            if name.isidentifier():
                arg_strings.append("%s=%r" % (name, value))
            else:
                star_args[name] = value
        if star_args:
            arg_strings.append("**%s" % repr(star_args))
        return "%s(%s)" % (type_name, ", ".join(arg_strings))

    def _get_kwargs(self):
        return list(self.__dict__.items())

    def _get_args(self):
        return []


class ClickSpace(_AttributeHolder):
    def __init__(self, **kwargs):
        for name in kwargs:
            setattr(self, name, kwargs[name])


@click.group(
    invoke_without_command=True,
    epilog=EPILOG,
)
@click.argument("file", required=False)
@click.argument("scenes", required=False, nargs=-1)
@optgroup.group("Global options")
@optgroup.option(
    "-c",
    "--config_file",
    type=click.File(),
    help="Specify the configuration file to use for render settings.",
)
@optgroup.option(
    "--custom_folders",
    is_flag=True,
    help="Use the folders defined in the [custom_folders] section of the config file to define the output folder structure.",
)
@optgroup.option(
    "--disable_caching",
    is_flag=True,
    help="Disable the use of the cache (still generates cache files).",
)
@optgroup.option(
    "--flush_cache", is_flag=True, help="Remove cached partial movie files."
)
@optgroup.option(
    "--tex_template", type=click.File(), help="Specify a custom TeX template file."
)
@optgroup.option(
    "-v",
    "--verbose",
    count=True,
    show_default=True,
    help="""
    Verbosity counter (-vv...). Changes ffmpeg log level unless 5+.
   
    {0:NONE,1:DEBUG,2:INFO,3:WARNING,4:ERROR,5+:CRITICAL}
    """,
)
@optgroup.group("Output options")
@optgroup.option(
    "-o",
    "--output",
    multiple=True,
    help="Specify the filename(s) of the rendered scene(s).",
)
@optgroup.option(
    "--media_dir", type=click.Path(), help="Path to store rendered videos and latex."
)
@optgroup.option("--log_dir", type=click.Path(), help="Path to store render logs.")
@optgroup.option(
    "--log_to_file",
    default=True,
    show_default=True,
    is_flag=True,
    help="Log terminal output to file",
)
@optgroup.group("Render Options")
@optgroup.option(
    "-n",
    "--from_animation_number",
    nargs=2,
    type=int,
    help="Start rendering from n_0 until n_1. If n_1 is left unspecified, renders all scenes after n_0.",
)
@optgroup.option(
    "-f",
    "--format",
    default="mp4",
    type=click.Choice(
        [
            "png",
            "gif",
            "mp4",
        ],
        case_sensitive=False,
    ),
)
@optgroup.option(
    "-q",
    "--quality",
    default="p",
    type=click.Choice(
        [
            "l",
            "m",
            "h",
            "p",
            "k",
        ],
        case_sensitive=False,
    ),
    help="""
    Render quality at the follow resolution framerates, respectively:
    854x480 30FPS, 
    1280x720 30FPS,
    1920x1080 60FPS,
    2560x1440 60FPS,
    3840x2160 60FPS
    """,
)
@optgroup.option(
    "-r",
    "--resolution",
    nargs=2,
    type=int,
    help="Resolution in (W,H) for when 16:9 aspect ratio isn't possible.",
)
@optgroup.option(
    "--fps",
    default=30,
    show_default=True,
    type=float,
    help="Render at this frame rate.",
)
@optgroup.option(
    "--webgl_renderer",
    # show_default=f"Current directory {os.getcwd()}",
    default=None,
    type=click.Path(),
    help="Render scenes using the WebGL frontend. Requires a path to the WebGL frontend.",
)
@optgroup.option(
    "-t", "--transparent", is_flag=True, help="Render scenes with alpha channel."
)
@optgroup.option(
    "-c",
    "--background_color",
    show_default=True,
    default="#000000",
    help="Render scenes with background color.",
)
@optgroup.group("Ease of access options")
@optgroup.option(
    "--progress_bar",
    default="display",
    show_default=True,
    type=click.Choice(
        [
            "display",
            "leave",
            "none",
        ],
        case_sensitive=False,
    ),
    help="Display progress bars and/or keep them displayed.",
)
@optgroup.option(
    "-p",
    "--preview",
    is_flag=True,
    help="Preview the rendered file(s) in default player.",
)
@optgroup.option(
    "-f",
    "--show_in_file_browser",
    is_flag=True,
    help="Show the output file in the file browser.",
)
@optgroup.option("--sound", is_flag=True, help="Play a success/failure sound.")
@click.pass_context
def render(
    ctx,
    file,
    scenes,
    config_file,
    custom_folders,
    disable_caching,
    flush_cache,
    tex_template,
    verbose,
    output,
    media_dir,
    log_dir,
    log_to_file,
    from_animation_number,
    format,
    quality,
    resolution,
    fps,
    webgl_renderer,
    transparent,
    background_color,
    progress_bar,
    preview,
    show_in_file_browser,
    sound,
):
    """Render SCENE(S) from the input FILE.

    FILE is the file path of the script.

    SCENES is an optional list of scenes in the file.
    """

    click.echo("render")
    args = {
        "ctx": ctx,
        "file": file,
        "scene_names": scenes,
        "config_file": config_file,
        "custom_folders": custom_folders,
        "disable_caching": disable_caching,
        "flush_cache": flush_cache,
        "tex_template": tex_template,
        "verbose": verbose,
        "output_file": output,
        "media_dir": media_dir,
        "log_dir": log_dir,
        "log_to_file": log_to_file,
        "from_animation_number": from_animation_number,
        "format": format,
        "quality": quality,
        "resolution": resolution,
        "frame_rate": fps,
        "webgl_renderer": webgl_renderer,
        "transparent": transparent,
        "background_color": background_color,
        "progress_bar": progress_bar,
        "preview": preview,
        "show_in_file_browser": show_in_file_browser,
        "sound": sound,
    }

    class ClickArgs:
        def __init__(self, args):
            for name in args:
                setattr(self, name, args[name])

        def _get_kwargs(self):
            return list(self.__dict__.items())

        def _get_args(self):
            return []

        def __eq__(self, other):
            if not isinstance(other, ClickArgs):
                return NotImplemented
            return vars(self) == vars(other)

        def __contains__(self, key):
            return key in self.__dict__

    click_args = ClickArgs(args)
    config.digest_args(click_args)

    if webgl_renderer:
        try:
            from manim.grpc.impl import frame_server_impl

            server = frame_server_impl.get(file)
            server.start()
            server.wait_for_termination()
        except ModuleNotFoundError as e:
            print("\n\n")
            print(
                "Dependencies for the WebGL render are missing. Run "
                "pip install manim[webgl_renderer] to install them."
            )
            print(e)
            print("\n\n")
    else:
        for SceneClass in scene_classes_from_file(Path(file)):
            try:
                scene = SceneClass()
                scene.render()
                open_file_if_needed(scene.renderer.file_writer)
            except Exception as e:
                print(f"Exception {e}")
