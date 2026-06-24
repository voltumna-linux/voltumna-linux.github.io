#!/usr/bin/python3
"""Genera index.html dai file di rilascio presenti in ../ftp/voltumna/.

Ogni file di rilascio ha un nome nella forma:

    standard : <image>-<flavour>-<board>-<version>.<ext>
    sdk      : <image>-sdk-<arch>-<board>-<version>.<sh|zip>
    incr.upd : <image>-<flavour>-<board>-<vfrom>-<vto>.incr.upd
    full.upd : <image>-<flavour>-<board>--<version>.full.upd   (doppio trattino)

dove flavour e' sdk|sde|sre e arch e' x86_64|mingw32. La sotto-cartella che
contiene il file (public|intranet) diventa il prefisso URL del link.

Lo script scansiona la directory sorgente, interpreta i nomi dei file e scrive
una tabella HTML di link in modo atomico. I file con un'estensione di rilascio
nota ma con un nome non interpretabile vengono saltati con un avviso su stderr;
i file senza estensione nota sono ignorati. La pagina viene comunque prodotta.
"""

import argparse
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configurazione (dati)
# --------------------------------------------------------------------------- #

EXTENSIONS = [
    "net.tar.xz", "os.tar.xz", "img.xz", "img.bmap", "img.vmdk.xz",
    "sh", "zip", "incr.upd", "full.upd", "manifest",
]

FLAVOURS = ("sdk", "sde", "sre")

DESCRIPTION = {
    "mvme2500":                     "Artesyn MVME2500 P2010 PowerPC SPE e500v2",
    "mvme5100":                     "Artesyn MVME5100 PowerPC",
    "mvme6100":                     "Artesyn MVME6100 PowerPC",
    "mvme7100":                     "Artesyn MVME7100 PowerPC",
    "dinet":                        "ElettraST Dinet",
    "arria10-daq":                  "ElettraST Arria10-daq",
    "nehalem-kvm":                  "KVM Virtual machine using Nehalem",
    "naples-kvm":                   "KVM Virtual machine using Naples<br>(grongo, srv-hyp-srf-01/05.fcs)",
    "ivybridge-kvm":                "KVM Virtual machine using Ivybridg<br>(srv-hyp-srf-06/07.fcs)",
    "skylake-kvm":                  "KVM Virtual machine using Skylake<br>(sofa-cli-07/10)",
    "cascadelake-kvm":              "KVM Virtual machine using Cascadelake<br>(sofa-cli-14/16/19, srv-hyp-sre-01/05.ecs)",
    "rome-kvm":                     "KVM Virtual machine using Rome<br>(sofa-cli-11/12)",
    "beaglebone":                   "Beaglebone White/Black/Red/Blue/Green",
    "beagleboneai":                 "Beaglebone AI",
    "sockit":                       "Terasic Sockit with Altera CycloneV FPGA",
    "d-6244-x11dph-t":              "Supermicro ssg-6039p-e1cr16h",
    "d-6244-x11dph-t-rnm":          "Supermicro ssg-6039p-e1cr16h RNM",
    "d-6346-06v45n":                "Dell powerEdge R750",
    "d-6346-06v45n-gof":            "Dell powerEdge R750 GOF",
    "s-4125r-x11spw-tf":            "Supermicro sys-5019p-wtr",
    "s-4125r-x11spw-tf-rnm":        "Supermicro sys-5019p-wtr RNM",
    "s-4125r-x11spw-tf-myricom":    "Supermicro sys-5019p-wtr Myricom",
    "s-4305ue-up-whl01":            "Up-board Xtreme 11 Celeron",
    "d-e5462-x7dwu":                "Supermicro unknown model",
    "d-e5462-x7dwu-rnm":            "Supermicro unknown model RNM",
    "d-e5472-x7dwu":                "Supermicro unknown model",
    "d-e5472-x7dwu-rnm":            "Supermicro unknown model RNM",
    "d-e52637v3-x10drw-i":          "Supermicro sys-6018r-wtr",
    "d-e52637v3-x10drw-i-rnm":      "Supermicro sys-6018r-wtr RNM",
    "d-e52637v4-x10dru-iplus":      "Supermicro sys-1028u-e1crtp+",
    "d-e52637v4-x10dru-iplus-rnm":  "Supermicro sys-1028u-e1crtp+ RNM",
    "d-e52643v4-x10dru-iplus":      "Supermicro sys-1028u-e1crtp+",
    "d-e52643v4-x10dru-iplus-rnm":  "Supermicro sys-1028u-e1crtp+ RNM",
    "s-d1718t-x12sdv-4c-sp6f":      "Supermicro sys-510d-4c-fn6p",
    "s-d1718t-x12sdv-4c-sp6f-rnm":  "Supermicro sys-510d-4c-fn6p RNM",
    "s-x6425e-a3sev-4c-ln4":        "Supermicro sys-e302-12e",
    "s-x6425e-a3sev-4c-ln4-rnm":    "Supermicro sys-e302-12e RNM",
    "d-9755-h14dsh":                "Supermicro as-2126hs-tn",
    "d-9755-h14dsh-fast":           "Supermicro as-2126hs-tn FAST",
}

REF = {
    "ccd": "G.Gaio", "a2720": "M.Cautero",
    "ec": "L.Pivetta", "ds": "L.Pivetta", "enpg": "G.Brajnik",
    "ebpm": "G.Brajnik", "st4": "Paolo Sigalotti",
}

# voltumna e' l'immagine base: in tabella appare per prima, etichettata "basic"
# con referente "A.Bogani".
BASE_IMAGE = "voltumna"
BASE_IMAGE_LABEL = "basic"
BASE_IMAGE_REF = "A.Bogani"

# --------------------------------------------------------------------------- #
# Parsing dei nomi file
# --------------------------------------------------------------------------- #

# Una versione: 2.8, 1.4-6, 2.7-0, 1.10-0, 4.0-0, 3.0beta
_VER = r"\d+\.\d+(?:-\d+)?[a-z]*"

_RE_SDK = re.compile(
    rf"^(?P<image>[^-]+)-sdk-(?P<arch>x86_64|mingw32)-(?P<board>.+)-(?P<version>{_VER})$")
_RE_INCR = re.compile(
    rf"^(?P<image>[^-]+)-(?P<flavour>sde|sre|sdk)-(?P<board>.+)-(?P<vfrom>{_VER})-(?P<version>{_VER})$")
_RE_FULL = re.compile(
    rf"^(?P<image>[^-]+)-(?P<flavour>sde|sre|sdk)-(?P<board>.+)--(?P<version>{_VER})$")
_RE_STD = re.compile(
    rf"^(?P<image>[^-]+)-(?P<flavour>sde|sre)-(?P<board>.+)-(?P<version>{_VER})$")

_EXTENSIONS_BY_LEN = sorted(EXTENSIONS, key=len, reverse=True)


@dataclass
class Release:
    """Un singolo artefatto scaricabile."""
    image: str
    flavour: str       # sdk | sde | sre
    board: str
    version: str       # per incr.upd e' la versione di arrivo (vto)
    area: str          # public | intranet -> prefisso URL
    ext: str           # chiave canonica dell'estensione
    filename: str

    @property
    def href(self):
        return f"{self.area}/{self.filename}"


def split_extension(filename):
    """Ritorna (stem, ext) per la piu' lunga estensione nota, altrimenti None.

    Richiede il punto separatore, quindi "sh" dentro "h14dsh" non viene mai
    scambiato per l'estensione .sh.
    """
    for ext in _EXTENSIONS_BY_LEN:
        suffix = "." + ext
        if filename.endswith(suffix):
            return filename[:-len(suffix)], ext
    return None


def parse_release(filename, area):
    """Interpreta un nome file.

    Ritorna (Release|None, recognised: bool). recognised=True significa che il
    file aveva un'estensione di rilascio nota: se Release e' None in quel caso,
    il nome non e' interpretabile e va segnalato.
    """
    split = split_extension(filename)
    if split is None:
        return None, False
    stem, ext = split

    if ext in ("sh", "zip"):
        m = _RE_SDK.match(stem)
        flavour = "sdk"
    elif ext == "incr.upd":
        m = _RE_INCR.match(stem)
        flavour = m.group("flavour") if m else None
    elif ext == "full.upd":
        m = _RE_FULL.match(stem)
        flavour = m.group("flavour") if m else None
    else:
        m = _RE_STD.match(stem)
        flavour = m.group("flavour") if m else None

    if m is None:
        return None, True

    return Release(image=m.group("image"), flavour=flavour, board=m.group("board"),
                   version=m.group("version"), area=area, ext=ext,
                   filename=filename), True


def scan(root):
    """Scansiona root e ritorna (releases, skipped)."""
    releases = []
    skipped = []
    for subdir, _dirs, files in os.walk(root):
        area = os.path.basename(subdir)
        for filename in sorted(files):
            release, recognised = parse_release(filename, area)
            if release is not None:
                releases.append(release)
            elif recognised:
                skipped.append(os.path.join(area, filename))
    return releases, skipped


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def version_sort_key(version):
    """Chiave per ordinare le versioni numericamente: 1.4-6 < 1.10-0 < 4.0-0."""
    m = re.match(r"(\d+)\.(\d+)(?:-(\d+))?", version)
    if not m:
        return ((0, 0, 0), version)
    nums = (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))
    return (nums, version[m.end():])


def _link(release, label):
    return f"<a href='{release.href}'>{label}</a>"


def sdk_cell(node):
    """Contenuto della colonna SDK per un dato (image, board, version)."""
    if "sh" in node:
        inner = _link(node["sh"], "Ubuntu18/22/24.04")
        inner += "<br>" + (_link(node["zip"], "Windows10") if "zip" in node else "Windows10")
        return inner
    if "zip" in node:
        return _link(node["zip"], "Windows10")
    return ""


def image_cell(node, with_updates):
    """Contenuto di una colonna immagine (SDE o SRE).

    with_updates=True aggiunge i link incr.upd/full.upd (colonna SRE).
    """
    parts = []
    if "img.xz" in node:
        line = _link(node["img.xz"], "img.xz")
        if "img.bmap" in node:
            line += " (" + _link(node["img.bmap"], "img.bmap") + ")"
        parts.append(line + "<br>")
    if "net.tar.xz" in node:
        parts.append(_link(node["net.tar.xz"], "net.tar.xz"))
    if "os.tar.xz" in node:
        parts.append(_link(node["os.tar.xz"], "os.tar.xz") + "<br>")
    if "img.vmdk.xz" in node:
        parts.append(_link(node["img.vmdk.xz"], "img.vmdk.xz") + "<br>")
    if "manifest" in node:
        parts.append(_link(node["manifest"], "manifest") + "<br>")
    if with_updates:
        if "incr.upd" in node:
            parts.append(_link(node["incr.upd"], "incr.upd"))
        if "full.upd" in node:
            parts.append(_link(node["full.upd"], "full.upd") + "<br>")
    # I frammenti sono separati da newline (come i print del vecchio script):
    # in HTML diventa uno spazio tra link adiacenti privi di <br>.
    return "\n".join(parts)


def _td(inner):
    return f"<td>{inner}</td>"


def _row(cells):
    return "<tr>\n" + "\n".join(_td(c) for c in cells) + "\n</tr>"


_EMPTY_ROW = "<tr>\n" + "\n".join(["<td></td>"] * 8) + "\n</tr>"
_SEPARATOR = _EMPTY_ROW + "\n" + _EMPTY_ROW


def _ordered_images(items):
    """Immagini in ordine alfabetico, con BASE_IMAGE forzata per prima."""
    images = sorted(items)
    if BASE_IMAGE in items:
        images.remove(BASE_IMAGE)
        images.insert(0, BASE_IMAGE)
    return images


def render(releases):
    """Costruisce l'intera pagina HTML dai release."""
    # items[image][board][version][flavour][ext] = Release
    items = {}
    for r in releases:
        (items.setdefault(r.image, {})
              .setdefault(r.board, {})
              .setdefault(r.version, {})
              .setdefault(r.flavour, {})[r.ext]) = r

    out = [HEAD]
    for image in _ordered_images(items):
        if image == BASE_IMAGE:
            display, ref = BASE_IMAGE_LABEL, BASE_IMAGE_REF
        else:
            display, ref = image, REF.get(image, "")

        for board in sorted(items[image]):
            board_label = board
            notes = DESCRIPTION.get(board, "")
            for version in sorted(items[image][board], key=version_sort_key):
                node = items[image][board][version]
                out.append(_row([
                    display,
                    ref,
                    board_label,
                    notes,
                    version,
                    sdk_cell(node.get("sdk", {})),
                    image_cell(node.get("sde", {}), with_updates=False),
                    image_cell(node.get("sre", {}), with_updates=True),
                ]))
        out.append(_SEPARATOR)

    out.append(FOOT)
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
# I/O
# --------------------------------------------------------------------------- #

def write_atomic(path, text):
    """Scrive text su path in modo atomico (tmp nella stessa dir + os.replace)."""
    path = os.fspath(path)
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".update-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SRC = SCRIPT_DIR.parent / "ftp" / "voltumna"
DEFAULT_OUT = SCRIPT_DIR / "index.html"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--src", default=str(DEFAULT_SRC),
                        help="directory dei file di rilascio (default: %(default)s)")
    parser.add_argument("--out", default=str(DEFAULT_OUT),
                        help="file HTML da generare (default: %(default)s)")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.src):
        # Errore di setup: non sovrascrivo una pagina valida con una vuota.
        print(f"update.py: directory sorgente non trovata: {args.src}", file=sys.stderr)
        return 2

    releases, skipped = scan(args.src)
    if skipped:
        print(f"update.py: {len(skipped)} file con estensione nota non interpretati "
              f"(ignorati):", file=sys.stderr)
        for name in sorted(skipped):
            print(f"  - {name}", file=sys.stderr)

    write_atomic(args.out, render(releases))
    return 0


# --------------------------------------------------------------------------- #
# Scaffold HTML statico (copiato verbatim dalla pagina esistente)
# --------------------------------------------------------------------------- #

HEAD = """<!doctype html>
<html lang="en">
<head>
<!-- Required meta tags -->
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
<!-- Bootstrap CSS -->
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
<!-- jQuery first, then Popper.js, then Bootstrap JS -->
<script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
<style>
body {
font-family: 'PT Sans Narrow', Arial, sans-serif;
font-size: 12px;
}
</style>
<title>Voltumna Linux</title>
<base href="https://www-int.elettra.eu/images/Documents/Voltumna/" target="_blank">
</head>
<body>
<div class="container">
<div class="row">
<div class="col-12 center-block text-center">
<img src='https://voltumna-linux.github.io/elettra.jpg'/>
<br><br><br><br>
<h4>Voltumna Linux images downloads</h4>
<br><br>
</div>
</div>
<div class="row">
<table class="table table-borderless table-hover table-condensed">
<thead>
<tr>
<th scope="col">Image</th>
<th scope="col">Ref</th>
                <th scope="col">Board</th>
                <th scope="col">Notes</th>
                <th scope="col">Version</th>
<th scope="col">SDK</th>
<th scope="col">SDE</th>
<th scope="col">SRE</th>
</tr>
</thead>
<tbody>"""

FOOT = """</tbody>
</table>
</div>
<br>
<div class="row">
<div class="col-12 center-block text-center">
<small>
<address>
<strong>Sincrotrone Trieste S.C.p.A.</strong><br>
Strada Statale 14 - km 163,5 in AREA Science Park<br>
34149 Basovizza, Trieste ITALY<br>
Tel. +39 040 37581 - Fax. +39 040 9380902<br>
</address>
<small>
</div>
</div>
</div>
</body>
</html>"""


if __name__ == "__main__":
    sys.exit(main())
