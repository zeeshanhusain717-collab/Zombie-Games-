[app]
title = Zombie Z Elite
package.name = zombiez
package.domain = org.zombie.zgame

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.include_patterns = icon.png
icon.filename = icon.png

version = 1.0

requirements = python3,pygame,pillow
orientation = landscape
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
fullscreen = 1

android.api = 31
android.min_api = 21
android.sdk = 30
android.ndk = 23b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1

