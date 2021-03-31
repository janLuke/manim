"""Manim's default subcommand, render.

Manim's render subcommand is accessed in the command-line interface via
``manim``, but can be more explicitly accessed with ``manim render``. Here you
can specify options, subcommands, and subgroups for the render command.

"""
import sys
from pathlib import Path
from textwrap import dedent

import click
import cloup

from .ease_of_access_options import ease_of_access_options
from .global_options import global_options
from .output_options import output_options
from .render_options import render_options
from ... import config, console, logger
from ...constants import CONTEXT_SETTINGS, EPILOG
from ...utils.module_ops import scene_classes_from_file


@cloup.command(
    context_settings=CONTEXT_SETTINGS,
    epilog=EPILOG,
)
@click.argument("file", type=Path, required=False)
@click.argument("scenes", required=False, nargs=-1)
@global_options
@output_options
@render_options
@ease_of_access_options
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
    write_to_movie,
    media_dir,
    log_dir,
    log_to_file,
    from_animation_number,
    write_all,
    file_format,
    save_last_frame,
    quality,
    resolution,
    frame_rate,
    renderer,
    use_opengl_renderer,  # Deprecated
    use_webgl_renderer,  # Deprecated
    webgl_renderer_path,
    transparent,
    background_color,
    progress_bar,
    preview,
    show_in_file_browser,
    jupyter,
):
    """Render SCENE(S) from the input FILE.

    FILE is the file path of the script.

    SCENES is an optional list of scenes in the file.
    """
    for scene in scenes:
        if str(scene).startswith("-"):
            logger.warning(
                dedent(
                    """\
                Manim Community has moved to Click for the CLI.

                This means that options in the CLI are provided BEFORE the positional
                arguments for your FILE and SCENE(s):
                `manim render [OPTIONS] [FILE] [SCENES]...`

                For example:
                New way - `manim -p -ql file.py SceneName1 SceneName2 ...`
                Old way - `manim file.py SceneName1 SceneName2 ... -p -ql`

                To see the help page for the new available options, run:
                `manim render -h`
                """
                )
            )
            sys.exit()

    # TODO: this dictionary is not needed if you declare render(**args); the
    #       total number of lines would decrease by 30*2=60
    args = {
        "ctx": ctx,
        "file": file,
        "scene_names": scenes,
        "config_file": config_file,
        "custom_folders": custom_folders,
        "disable_caching": disable_caching,
        "flush_cache": flush_cache,
        "tex_template": tex_template,
        "verbosity": verbose,
        "output_file": output,
        "write_to_movie": write_to_movie,
        "media_dir": media_dir,
        "log_dir": log_dir,
        "log_to_file": log_to_file,
        "from_animation_number": from_animation_number,
        "write_all": write_all,
        "format": file_format,
        "save_last_frame": save_last_frame,
        "quality": quality,
        "resolution": resolution,
        "frame_rate": frame_rate,
        "renderer": renderer,
        "use_opengl_renderer": use_opengl_renderer,  # Deprecated
        "use_webgl_renderer": use_webgl_renderer,  # Deprecated
        "webgl_renderer_path": webgl_renderer_path,
        "transparent": transparent,
        "background_color": background_color,
        "progress_bar": progress_bar,
        "preview": preview,
        "show_in_file_browser": show_in_file_browser,
        "jupyter": jupyter,
    }

    # TODO: renderer is never used [likely a bug]
    if use_opengl_renderer:
        logger.warning(
            "--use_opengl_renderer is deprecated, please use --render=opengl instead!"
        )
        renderer = "opengl"
    if use_webgl_renderer:
        logger.warning(
            "--use_webgl_renderer is deprecated, please use --render=webgl instead!"
        )
        renderer = "webgl"
    if use_webgl_renderer and use_opengl_renderer:
        logger.warning("You may select only one renderer!")
        sys.exit()

    class ClickArgs:
        def __init__(self, args):
            for name in args:
                setattr(self, name, args[name])

        def _get_kwargs(self):
            return list(self.__dict__.items())

        def __eq__(self, other):
            if not isinstance(other, ClickArgs):
                return NotImplemented
            return vars(self) == vars(other)

        def __contains__(self, key):
            return key in self.__dict__

        def __repr__(self):
            return str(self.__dict__)

    click_args = ClickArgs(args)
    if jupyter:
        return click_args
    config.digest_args(click_args)

    if config.renderer == "opengl":
        from manim.renderer.opengl_renderer import OpenGLRenderer

        for SceneClass in scene_classes_from_file(file):
            try:
                renderer = OpenGLRenderer()
                scene = SceneClass(renderer)
                scene.render()
            except Exception:
                console.print_exception()
    elif config.renderer == "webgl":
        try:
            from manim.grpc.impl import frame_server_impl

            server = frame_server_impl.get(file)
            server.start()
            server.wait_for_termination()
        except ModuleNotFoundError:
            console.print(
                "Dependencies for the WebGL render are missing. Run "
                "pip install manim[webgl_renderer] to install them."
            )
            console.print_exception()
    else:
        for SceneClass in scene_classes_from_file(file):
            try:
                scene = SceneClass()
                scene.render()
            except Exception:
                console.print_exception()
    return args
