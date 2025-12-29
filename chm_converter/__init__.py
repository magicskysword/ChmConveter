#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CHM Converter 包

将CHM文件转换为静态网站
"""

from .models import TocItem, ChmInfo
from .extractor import ChmExtractor
from .parser import parse_hhc_file, extract_title_from_hhc
from .generator import StaticSiteGenerator

__version__ = '1.0.0'
__all__ = [
    'TocItem',
    'ChmInfo',
    'ChmExtractor',
    'parse_hhc_file',
    'extract_title_from_hhc',
    'StaticSiteGenerator',
]
