# Flathub

## Build & Install

flatpak run org.flatpak.Builder --force-clean --sandbox --user --install --install-deps-from=flathub\
 --ccache --mirror-screenshots-url=https://dl.flathub.org/media/ --repo=repo builddir io.github.Q1CHENL.fig.json

## Uninstall

flatpak uninstall --user io.github.Q1CHENL.fig --delete-data

## Run

flatpak run io.github.Q1CHENL.fig

## Screenshots commit

ostree commit --repo=repo --canonical-permissions --branch=screenshots/x86_64 builddir/files/share/app-info/media

## Linter

flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest io.github.Q1CHENL.fig.json
flatpak run --command=flatpak-builder-lint org.flatpak.Builder repo repo

## Submission

Submit PR against https://github.com/flathub/io.github.Q1CHENL.fig

https://docs.flathub.org/docs/for-app-authors/submission/

## Maintenance

https://docs.flathub.org/docs/for-app-authors/maintenance/

## Update

https://docs.flathub.org/docs/for-app-authors/updates/
