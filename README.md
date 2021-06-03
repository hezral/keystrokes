# keystrokes

requires io.elementary.Platform and io.elementary.Sdk flatpak runtimes

```
flatpak remote-add --if-not-exists elementary https://flatpak.elementary.io/repo.flatpakrepo

flatpak install io.elementary.Platform
flatpak install io.elementary.Sdk
```

then clone this repo
```
git clone https://github.com/hezral/keystrokes
```

then build using flatpak-builder
```
flatpak-builder --user --force-clean --install build-dir com.github.hezral.keystrokes.yml
```

the launcher should appear in the desktop app launcher menu. if not, run with
```
flatpak run com.github.hezral.keystrokes
```

