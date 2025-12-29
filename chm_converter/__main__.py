#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CHM Converter - 支持直接运行模块

python -m chm_converter input.chm output/
"""

from .cli import main

if __name__ == '__main__':
    main()
