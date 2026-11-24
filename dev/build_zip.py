# -*- coding: utf-8 -*-
"""Build the prebuilt plugin zip from the files tracked by git, then check that the plugin loads from it.

Run from the repository root with the QGIS Python (needed for the check):

    & "C:\\Program Files\\QGIS 4.0.1\\bin\\python-qgis.bat" dev\\build_zip.py

The zip contains every tracked file of the GlobeBuilder folder except tests and git configuration files, so a
new module can never be forgotten (it once was: "No module named GlobeBuilder.definitions.language").
After building, the zip is extracted to a temporary folder and the plugin's main module is imported from there
in a fresh interpreter, the way QGIS does it.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_DIR = "GlobeBuilder"
EXCLUDED = re.compile(r"(^|/)(test|\.github)(/|$)|(^|/)\.git[^/]*$|^GlobeBuilder/logs/\.gitignore$")


def version():
    with open(os.path.join(ROOT, PLUGIN_DIR, "metadata.txt"), encoding="utf-8") as f:
        return re.search(r"^version=(\S+)", f.read(), re.M).group(1)


def find_git():
    for candidate in (shutil.which("git"), r"C:\Program Files\Git\cmd\git.exe", r"C:\Program Files\Git\bin\git.exe"):
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def tracked_files():
    git = find_git()
    if git:
        out = subprocess.run([git, "ls-files", PLUGIN_DIR], cwd=ROOT, capture_output=True, text=True, check=True)
        names = [p for p in out.stdout.splitlines() if p]
    else:  # no git available: walk the folder, skipping generated files
        names = []
        for folder, dirs, files in os.walk(os.path.join(ROOT, PLUGIN_DIR)):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "logs", ".pytest_cache")]
            for f in files:
                if not f.endswith((".pyc", ".log")):
                    names.append(os.path.relpath(os.path.join(folder, f), ROOT).replace(os.sep, "/"))
    return [p for p in names if not EXCLUDED.search(p)]


def build(path):
    files = tracked_files()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(PLUGIN_DIR + "/logs/", "")  # the plugin writes its log file there
        for name in files:
            archive.write(os.path.join(ROOT, name), name)
    return files


def check(path):
    """Import the plugin from the extracted zip in a fresh interpreter."""
    with tempfile.TemporaryDirectory() as folder:
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None, "corrupted zip"
            archive.extractall(folder)
        code = (
            "import os, sys\n"
            "os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "from qgis.core import QgsApplication\n"
            "app = QgsApplication([], False); app.initQgis()\n"
            "import GlobeBuilder\n"
            "from GlobeBuilder.plugin import GlobeBuilder as Plugin\n"
            "from GlobeBuilder.ui.globe_builder_dockwidget import GlobeBuilderDockWidget\n"
            "print('plugin modules import OK:', GlobeBuilder.__file__)\n"
        )
        result = subprocess.run([sys.executable, "-c", code, folder], capture_output=True, text=True, cwd=folder)
        if result.returncode != 0:
            raise SystemExit("The plugin does NOT load from the zip:\n" + result.stderr[-2000:])
        print(result.stdout.strip())


if __name__ == "__main__":
    target_dir = os.path.join(ROOT, "releases")
    zip_path = os.path.join(target_dir, "GlobeBuilder-{}-qt6fix.zip".format(version()))
    built = build(zip_path)
    print("built {} ({} files)".format(os.path.relpath(zip_path, ROOT), len(built)))
    if "--no-check" not in sys.argv:
        check(zip_path)
