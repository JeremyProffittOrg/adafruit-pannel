Panel case shortcuts
====================

start-panelweb.cmd
  Builds bin\panelweb.exe if missing, starts the site, opens the browser.
  URL: http://127.0.0.1:8787/

Panel-case-builder.url
  Internet shortcut to the same URL. The Go app must already be running.

open-case-in-bambu.cmd
  Opens the two-piece print kit in Bambu Studio:
  C:\dev\adafruit-pannel\print-kits\sliders-quads-case\sliders-quads-case.3mf

From a terminal in the repo:
  go run ./web
  then open http://127.0.0.1:8787/

Print: top.stl as exported (already flipped). Bottom tray countersink on the bed.
