# -*- coding: utf-8 -*-
"""validate_svg.py — 逐个检查 fig*.svg 是否 well-formed XML，并定位问题行。

validate_svg.py — checks each fig*.svg for well-formed XML and locates the offending line."""
import glob
import os
import sys
import xml.etree.ElementTree as ET

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 校验脚本所在目录下的 fig*.svg（第三方克隆后即指克隆目录）
# Validates fig*.svg in the script's own directory (i.e., the clone directory for third parties).
HERE = os.path.dirname(os.path.abspath(__file__))
for f in sorted(glob.glob(os.path.join(HERE, "fig*.svg"))):
    try:
        ET.parse(f)
        print("OK   ", f)
    except ET.ParseError as e:
        print("FAIL ", f, "->", e)
