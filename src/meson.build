pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'keystrokes')
gnome = import('gnome')

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'keystrokes.in',
  output: 'keystrokes',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

keystrokes_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'custom_widgets.py',
  'keystrokes_backend.py',
  'active_window_manager.py',
  'utils.py'
]

install_data(keystrokes_sources, install_dir: moduledir)