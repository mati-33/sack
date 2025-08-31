from sack import __version__


SACK_ASCII = r"""
█▀ ▄▀█ █▀▀ █▄▀
▄█ █▀█ █▄▄ █ █
"""

SACK_ABOUT = f"""
version: {__version__}

sack is an open-source chat application for the terminal,
built with the Textual framework and TCP sockets.

sack is distributed under the MIT license."""

WELCOME_HELP = """\
The welcome screen is the first screen you see when you run sack.

From there, you can start or join a server,
view the about page, and open the help popup."""

SERVER_HELP = """\
On the 'Create server' form, you will be asked to enter a server port.

If the chosen port is available, a new server will be started
on your machine and visible to all devices connected to your local network.
You will then be asked to choose a nickname.

If you exit sack, your server will stop running
and all connected users will be disconnected."""

JOIN_HELP = """\
On the 'Join server' form, you will be asked to enter the server host and port.
If the server is reachable, you will be connected and then asked to choose a nickname.

Make sure you enter the correct address and port,
otherwise the connection will not be established."""

CHAT_HELP = """\
The chat screen consists of a message area and a text input field.

When the input field is focused, you can type and send messages
to other users.

When the message area is focused, you can use
the available keybindings to scroll through messages."""
