project('com.github.hezral.keystrokes',
          version: '1.0.2',
    meson_version: '>= 0.50.0',
  default_options: [ 'warning_level=2',
                   ],
)

i18n = import('i18n')

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
rdnn = meson.project_name().split('.')
project_domain = '.'.join([rdnn[0],rdnn[1],rdnn[2]])
project_short_name = rdnn[3]

subdir('data')
subdir('src')
subdir('po')

meson.add_install_script('build-aux/meson/postinstall.py')
