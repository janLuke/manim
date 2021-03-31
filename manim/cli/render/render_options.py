import re

import click
from cloup import option, option_group

from ... import logger


def validate_scene_range(ctx, param, value):
    try:
        start = int(value)
        return (start,)
    except Exception:
        pass

    if value:
        try:
            start, end = map(int, re.split(";|,|-", value))
            return start, end
        except Exception:
            logger.error("Couldn't determine a range for -n option.")
            exit()


def validate_resolution(ctx, param, value):
    if value:
        try:
            start, end = map(int, re.split(";|,|-", value))
            return (
                start,
                end,
            )
        except Exception:
            logger.error("Resolution option is invalid.")
            exit()


render_options = option_group(
    "Render Options",
    option(
        "-n",
        "--from_animation_number",
        callback=validate_scene_range,
        help="Start rendering from n_0 until n_1. If n_1 is left unspecified, "
        "renders all scenes after n_0.",
    ),
    option(
        "-a",
        "--write_all",
        is_flag=True,
        help="Render all scenes in the input file.",
    ),
    option(
        "-f",
        "--format",
        "file_format",
        default="mp4",
        type=click.Choice(["png", "gif", "mp4"], case_sensitive=False),
    ),
    option("-s", "--save_last_frame", is_flag=True),
    option(
        "-q",
        "--quality",
        default="h",
        type=click.Choice(["l", "m", "h", "p", "k"], case_sensitive=False),
        help="""
            Render quality at the follow resolution framerates, respectively:
            854x480 30FPS,
            1280x720 30FPS,
            1920x1080 60FPS,
            2560x1440 60FPS,
            3840x2160 60FPS
            """,
    ),
    option(
        "-r",
        "--resolution",
        callback=validate_resolution,
        help="Resolution in (W,H) for when 16:9 aspect ratio isn't possible.",
    ),
    option(
        "--fps",
        "--frame_rate",
        "frame_rate",
        type=float,
        help="Render at this frame rate.",
    ),
    option(
        "--renderer",
        type=click.Choice(["cairo", "opengl", "webgl"], case_sensitive=False),
        help="Select a renderer for your Scene.",
    ),
    option("--use_opengl_renderer", is_flag=True, help="Render scenes using OpenGL."),
    option(
        "--use_webgl_renderer",
        is_flag=True,
        help="Render scenes using the WebGL frontend.",
    ),
    option(
        "--webgl_renderer_path",
        default=None,
        type=click.Path(),
        help="The path to the WebGL frontend.",
    ),
    option(
        "-t", "--transparent", is_flag=True, help="Render scenes with alpha channel."
    ),
    option(
        "--background_color",
        help="Render scenes with background color.",
    ),
)
