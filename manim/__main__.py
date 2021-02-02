import os
import sys
import traceback
import click
from click.testing import CliRunner
from click_default_group import DefaultGroup
from manim.constants import EPILOG
from manim.constants import CONTEXT_SETTINGS
from manim.cli.cfg.commands import cfg
from manim.cli.plugin.commands import plugin
from manim.cli.render.commands import render

from manim import logger, config
from manim.utils.module_ops import (
    get_module,
    get_scene_classes_from_module,
    get_scenes_to_render,
    scene_classes_from_file,
)
from manim.plugins.plugins_flags import list_plugins
from manim.utils.file_ops import open_file as open_media_file
from manim._config.main_utils import parse_args


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


def main():
    args = parse_args(sys.argv)
    print("ARGS:", type(args),args, sep="\n")
    if hasattr(args, "cmd"):
        if args.cmd == "cfg":
            if args.subcmd:
                from manim._config import cfg_subcmds

                if args.subcmd == "write":
                    cfg_subcmds.write(args.level, args.open)
                elif args.subcmd == "show":
                    cfg_subcmds.show()
                elif args.subcmd == "export":
                    cfg_subcmds.export(args.dir)
            else:
                logger.error("No subcommand provided; Exiting...")

        elif args.cmd == "plugins":
            from manim.plugins import plugins_flags

            if args.list:
                plugins_flags.list_plugins()
            elif not args.list:
                logger.error("No flag provided; Exiting...")

        # elif args.cmd == "some_other_cmd":
        #     something_else_here()

    else:
        print("config",config)
        config.digest_args(args)
        print("config",config)
        input_file = config.get_dir("input_file")
        if config["use_webgl_renderer"]:
            try:
                from manim.grpc.impl import frame_server_impl

                server = frame_server_impl.get(input_file)
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
            for SceneClass in scene_classes_from_file(input_file):
                try:
                    scene = SceneClass()
                    scene.render()
                    open_file_if_needed(scene.renderer.file_writer)
                except Exception:
                    print("\n\n")
                    traceback.print_exc()
                    print("\n\n")


@click.group(
    cls=DefaultGroup,
    default="render",
    no_args_is_help=True,
    context_settings=CONTEXT_SETTINGS,
    help="Animation engine for explanatory math videos",
    epilog=EPILOG,
)
@click.version_option()
@click.pass_context
def cli(ctx):
    """The entry point for manim."""
    pass


cli.add_command(cfg)
cli.add_command(plugin)
cli.add_command(render)

if __name__ == "__main__":
    runner = CliRunner()
    result = runner.invoke(cli, ["render", "--help"])
    assert result.exit_code == 0
