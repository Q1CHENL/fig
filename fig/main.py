#!/usr/bin/env python3

import gi
from fig.app import FigApplication

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')


def main():
    app = FigApplication()
    return app.run(None)
