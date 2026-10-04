# -*- coding: utf-8 -*-
"""validate_svg.py — 逐个检查 fig*.svg 是否 well-formed XML，并定位问题行。

validate_svg.py — checks each fig*.svg for well-formed XML and locates the offending line."""
import glob
import xml.etree.ElementTree as ET

for f in sorted(glob.glob(r"E:\LOGIC AI\logic papers\DELTA S\fig*.svg")):
    try:
        ET.parse(f)
        print("OK   ", f)
    except ET.ParseError as e:
        print("FAIL ", f, "->", e)
