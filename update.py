#!/usr/bin/python3

import os
import re
import sys
#import json

items = {}

extensions = [ "net.tar.xz", "os.tar.xz", "img.xz", "img.bmap",
        "img.vmdk.xz", "sh", "zip", "incr.upd", "full.upd", "manifest" ]

flavours = [ "sdk", "sde", "sre" ]

description = {
        "mvme2500":                     "Artesyn MVME2500 P2010 PowerPC SPE e500v2",
        "mvme5100":                     "Artesyn MVME5100 PowerPC",
        "mvme7100":                     "Artesyn MVME7100 PowerPC",
        "dinet":                        "ElettraST Dinet",
        "arria10-daq":                  "ElettraST Arria10-daq",
        "kvm-nehalem":                  "KVM Virtual machine using Nehalem",
        "kvm-naples":                   "KVM Virtual machine using Naples",
        "kvm-ivybridge":                "KVM Virtual machine using Ivybridge",
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

ref = { "ccd": "G.Gaio", "a2720": "M.Cautero", 
       "ec": "L.Pivetta", "ds": "L.Pivetta", "enpg": "G.Brajnik",
       "ebpm": "G.Brajnik", "st4": "Paolo Sigalotti"}

for subdir, dirs, files in os.walk('../ftp/voltumna/'):
    dir = os.path.basename(subdir)
    for file in sorted(files):
        for extension in extensions:
            m = re.search(".*" + extension,file)
            if m:
                data = m.string[m.span()[0]:m.span()[1]-len("."+extension)]
                for flavour in flavours:
                    m = re.search(flavour, data)
                    if m:
                        image = m.string[0:m.span()[0]-1]
                        data = m.string[m.span()[1]:]
                        m = re.search('[0-9]\.[0-9]', data)
                        if extension == "full.upd":
                            board = m.string[1:m.span()[0]-2]
                        else:
                            board = m.string[1:m.span()[0]-1]
                        if flavour == "sdk":
                            board = board[7:]
                            if board[0:7] == "mingw32":
                                board = board[8:]
                        version = m.string[m.span()[0]:]
                        if extension == "incr.upd":
                            m = re.search('[0-9]\.[0-9]', version)
                            m = re.search('[0-9]\.[0-9]', m.string[m.span()[1]:])
                            version = m.string[m.span()[0]:]

                        if items.get(image) == None:
                            items[image] = {}
                        if items[image].get(board) == None:
                            items[image][board] = {}
                        if items[image][board].get(version) == None:
                            items[image][board][version] = {}
                        if items[image][board][version].get(flavour) == None:
                            items[image][board][version][flavour] = {}
                        if items[image][board][version][flavour].get(extension) == None:
                            items[image][board][version][flavour][extension] = {"file": dir + "/" + file}

#print(json.dumps(items))
#sys.exit(0)
print("""<!doctype html>
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
<base href="https://www.elettra.eu/images/Documents/Voltumna/" target="_blank">
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
<th scope="col">Version</th>
<th scope="col">SDK</th>
<th scope="col">SDE</th>
<th scope="col">SRE</th>
</tr>
</thead>
<tbody>""");

image = "voltumna"
try:
    for board in items[image]:
        for version in items[image][board]:
            if board in description:
                print("""<tr>
                <td>basic</td>
                <td>A.Bogani</td>
                <td>""" + board + """ (""" + description[board] + """)</td>
                <td>""" + version + """</td>
                <td></td>
                <td>""");
            else:
                print("""<tr>
                <td>basic</td>
                <td>A.Bogani</td>
                <td>""" + board + """</td>
                <td>""" + version + """</td>
                <td></td>
                <td>""");

            if "sde" in items[image][board][version]:
                if "img.xz" in items[image][board][version]["sde"]:
                    print("""<a href='""" + items[image][board][version]["sde"]["img.xz"]["file"] + """'>img.xz</a>
                            (<a href='""" + items[image][board][version]["sde"]["img.bmap"]["file"] + """'>img.bmap</a>)""");
                    print("<br>");
                if "net.tar.xz" in items[image][board][version]["sde"]:
                    print("<a href='" + items[image][board][version]["sde"]["net.tar.xz"]["file"] + "'>net.tar.xz</a>");
                if "os.tar.xz" in items[image][board][version]["sde"]:
                    print("<a href='" + items[image][board][version]["sde"]["os.tar.xz"]["file"] + "'>os.tar.xz</a>");
                    print("<br>");
                if "manifest" in items[image][board][version]["sde"]:
                    print("<a href='" + items[image][board][version]["sde"]["manifest"]["file"] + "'>manifest</a>");
                print("</td>");
            else:
                print("""<td></td>""");
            
            print("<td></td></tr>");
except:
    pass

print("""<tr>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>""");


for image in items:
    if image != "voltumna":
        for board in items[image]:
            for version in items[image][board]:
                if board in description:
                    print("""<tr>
                    <td>""" + image + """</td>
                    <td>""" + ref[image] + """</td>
                    <td>""" + board + """ (""" + description[board] + """)</td>
                    <td>""" + version + """</td>""");
                else:
                    print("""<tr>
                    <td>""" + image + """</td>
                    <td>""" + ref[image] + """</td>
                    <td>""" + board + """</td>
                    <td>""" + version + """</td>""");

                if "sdk" in items[image][board][version]:
                    if "zip" in items[image][board][version]["sdk"]:
                        print("<td><a href='" + items[image][board][version]["sdk"]["sh"]["file"] + "'>Ubuntu18/22/24.04</a><br><a href='" 
                                + items[image][board][version]["sdk"]["zip"]["file"] + "'>Windows10</a></td>");
                    else:
                        print("<td><a href='" + items[image][board][version]["sdk"]["sh"]["file"] + "'>Ubuntu18/22/24.04</a><br>Windows10</td>");
                else:
                    print("<td></td>");
                
                if "sde" in items[image][board][version]:
                    print("<td>")
                    if "img.xz" in items[image][board][version]["sde"]:
                        print("""<a href='""" + items[image][board][version]["sde"]["img.xz"]["file"] + """'>img.xz</a>
                        (<a href='""" + items[image][board][version]["sde"]["img.bmap"]["file"] + """'>img.bmap</a>)""");
                        print("<br>");
                    if "net.tar.xz" in items[image][board][version]["sde"]:
                        print("<a href='" + items[image][board][version]["sde"]["net.tar.xz"]["file"] + "'>net.tar.xz</a>");
                    if "os.tar.xz" in items[image][board][version]["sde"]:
                        print("<a href='" + items[image][board][version]["sde"]["os.tar.xz"]["file"] + "'>os.tar.xz</a>");
                        print("<br>");
                    if "img.vmdk.xz" in items[image][board][version]["sde"]:
                        print("<a href='" + items[image][board][version]["sde"]["img.vmdk.xz"]["file"] + "'>img.vmdk.xz</a>");
                        print("<br>");
                    if "manifest" in items[image][board][version]["sde"]:
                        print("<a href='" + items[image][board][version]["sde"]["manifest"]["file"] + "'>manifest</a>");
                        print("<br>");
                    print("</td>");
                else:
                    print("<td></td>");

                if "sre" in items[image][board][version]:
                    print("<td>")
                    if "img.xz" in items[image][board][version]["sre"]:
                        print("""<a href='""" + items[image][board][version]["sre"]["img.xz"]["file"] + """'>img.xz</a>""");
                        if "img.bmap" in items[image][board][version]["sre"]:
                            print("""(<a href='""" + items[image][board][version]["sre"]["img.bmap"]["file"] + """'>img.bmap</a>)""");
                        print("<br>");
                    if "net.tar.xz" in items[image][board][version]["sre"]:
                        print("<a href='" + items[image][board][version]["sre"]["net.tar.xz"]["file"] + "'>net.tar.xz</a>");
                    if "os.tar.xz" in items[image][board][version]["sre"]:
                        print("<a href='" + items[image][board][version]["sre"]["os.tar.xz"]["file"] + "'>os.tar.xz</a>");
                        print("<br>");
                    if "img.vmdk.xz" in items[image][board][version]["sre"]:
                        print("<a href='" + items[image][board][version]["sre"]["img.vmdk.xz"]["file"] + "'>img.vmdk.xz</a>");
                        print("<br>");
                    if "manifest" in items[image][board][version]["sre"]:
                        print("<a href='" + items[image][board][version]["sre"]["manifest"]["file"] + "'>manifest</a>");
                        print("<br>");
                    if "incr.upd" in items[image][board][version]["sre"]:
                        print("<a href='" + items[image][board][version]["sre"]["incr.upd"]["file"] + "'>incr.upd</a>");
                    if "full.upd" in items[image][board][version]["sre"]:
                        print("<a href='" + items[image][board][version]["sre"]["full.upd"]["file"] + "'>full.upd</a>");
                        print("<br>");
                    print("</td>");
                else:
                    print("""<td></td>""")

                print("</tr>")
        print("""<tr>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
        </tr>
        <tr>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
        </tr>""");

print("""</tbody>
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
</html>""");
