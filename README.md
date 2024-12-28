<h1 align="center" style="border-bottom: none;">
  <img alt="Fig" src="assets/icons/io.github.Q1CHENL.fig.svg" width="128" height="128"/>
  <br>
  Fig
</h1>
<h4 align="center">Sleek GIF editor.</h4>

<p align="center">
  <a href="https://flathub.org/apps/details/io.github.Q1CHENL.fig">
    <img alt="Download on Flathub" src="https://flathub.org/api/badge?svg&locale=en&light" width="200"/>
  </a>
</p>

![UI](assets/screenshots/screenshot-home-split.png)
![UI](assets/screenshots/screenshot-editor-split.png)

## Features

- Crop GIF
- Trim GIF to any frame range
- Reverse GIF
- Remove specific frames
- Insert GIF/image(s) at any position
- Change playback speed for specific frames
- Extract frames
- Export GIF as video
- Play GIF at the original speed

> [!TIP]
> View the Help page for more advanced actions

## Build and Run

- Run as python module:

  `pip install -r requirements.txt` (Install dependencies)

  `python -m fig.main`

  - Install stubs for better code completion (optional)

    `pip install pygobject-stubs`

- Flatpak:

  - Build and install

    `flatpak run org.flatpak.Builder --force-clean --sandbox --user --install --install-deps-from=flathub --ccache --mirror-screenshots-url=https://dl.flathub.org/media/ --repo=repo builddir io.github.Q1CHENL.fig.json`

  - Run

    `flatpak run io.github.Q1CHENL.fig`

## Test

`pip install pytest`

`pytest test/test.py`

## Todos

- ~~Improve UI~~
- ~~Previews frames~~
- ~~Preview trimmed gif~~
- ~~Crop GIF~~
- ~~Export frame(s)~~
- Combine frames to GIF
- ~~Stop icon for the play button~~
- ~~Reverse GIF: switch handles~~
- ~~Port to GTK4~~
- Capture GIF
- Web version of Fig
- ~~Make GIF slower/faster~~
- Make GIF black-and-white
- ~~Reverse playback~~
- ~~Append/Insert/Remove frames in frameline~~
- ~~Design GTK-Style icon~~
- ~~Button and handles hover effects~~
- ~~Load GIF faster~~
- ~~Improve tests and solve warnings~~
- ~~Use FileDialog instead of FileChooserDialog/Native(GTK-4.10)~~
- ~~Light mode~~
- Undo last action
- ~~Proper default name for edited GIF when saving~~
- Menu in headerbar: ~~new window~~, ~~about~~, open, ~~help~~ etc.
- ~~New About page~~
- ~~Better info label UI~~
- Loop playback option
- ~~Light/Dark mode screenshots~~
- Preferences: fixed color mode, default save folder etc.
- ~~Info label changes along with frameline changes~~
- ~~Better controls UI~~
- ~~Extract frames~~
- ~~Export to video~~
- Pixelize single/all frames
- Rotate gif
- Text embedding
- ~~Drag and drop file~~
- Flip image

## Credits

- Homepage UI is inspired by [sly](https://github.com/kra-mo/sly)
- Thanks to Cursor/Windsurf/Copilot :)

## Contribute

PRs and Issues are always welcome.
