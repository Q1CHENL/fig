project('fig',
  version: '1.0.7',
  meson_version: '>= 0.59.0'
)

python = import('python').find_installation('python3')
python_dir = python.get_install_dir()

# Install Python package
install_subdir('fig',
  install_dir: python_dir
)

# Install style and assets directly inside the fig package directory
install_subdir('style',
  install_dir: python_dir / 'fig'
)
install_subdir('assets',
  install_dir: python_dir / 'fig'
)
install_subdir('screenshots',
  install_dir: python_dir / 'fig'
)

# Install desktop file
install_data('io.github.Q1CHENL.fig.desktop',
  install_dir: get_option('datadir') / 'applications'
)

# Install icons
install_data('assets/icons/io.github.Q1CHENL.fig.svg',
  install_dir: get_option('datadir') / 'icons/hicolor/scalable/apps'
)
install_data('assets/icons/io.github.Q1CHENL.fig-symbolic.svg',
  install_dir: get_option('datadir') / 'icons/hicolor/symbolic/apps'
)

# Install metainfo
install_data('io.github.Q1CHENL.fig.metainfo.xml',
  install_dir: get_option('datadir') / 'metainfo'
)

# Install main executable
configure_file(
  configuration: {
    'PYTHON': python.full_path(),
    'PKGNAME': 'fig',
  },
  input: 'bin/fig.in',
  output: 'fig',
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)