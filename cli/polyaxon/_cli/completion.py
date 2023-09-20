import click

from clipped.formatting import Printer

from polyaxon.logger import clean_outputs


@click.command()
@click.argument("shell")
@clean_outputs
def completion(shell):
    """Show documentation for installing the auto-completion for polyaxon cli.

    Valid options: [bash, zsh, fish]

    \b
    $ polyaxon completion SHELL
    """

    if shell == "bash":
        Printer.heading(
            "Please save the following scripts:",
        )
        Printer.print(
            "_POLYAXON_COMPLETE=bash_source polyaxon > ~/.polyaxon-complete.bash"
        )
        Printer.print("_PLX_COMPLETE=bash_source plx > ~/.plx-complete.bash")
        Printer.heading(
            "Add the following lines to your: `~/.bashrc`",
        )
        Printer.print_text(
            "# Polyaxon completion\n. ~/.polyaxon-complete.bash\n. ~/.plx-complete.bash"
        )
        Printer.heading(
            "Reload your shell.",
        )
    elif shell == "zsh":
        Printer.heading(
            "Please save the following scripts:",
        )
        Printer.print(
            "_POLYAXON_COMPLETE=zsh_source polyaxon > ~/.polyaxon-complete.zsh"
        )
        Printer.print("_PLX_COMPLETE=zsh_source plx > ~/.plx-complete.zsh")
        Printer.heading(
            "Add the following lines to your: `~/.zshrc`",
        )
        Printer.print_text(
            "# Polyaxon completion\n. ~/.polyaxon-complete.zsh\n. ~/.plx-complete.zsh"
        )
        Printer.heading(
            "Reload your shell.",
        )
    elif shell == "fish":
        Printer.heading(
            "Please save the following scripts under `~/.config/fish/completions`:",
        )
        Printer.print(
            "_POLYAXON_COMPLETE=fish_source polyaxon > ~/.config/fish/completions/polyaxon-complete.fish"  # noqa
        )
        Printer.print(
            "_PLX_COMPLETE=fish_source plx > ~/.config/fish/completions/plx-complete.fish"
        )
    else:
        Printer.print("Shell {} is not supported.".format(shell))
