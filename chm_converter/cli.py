#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
命令行接口模块

提供CHM转网站的命令行工具
"""

import argparse
import sys
from pathlib import Path

from .generator import StaticSiteGenerator


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description='CHM Converter - 将CHM文件转换为静态网站',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  chm_converter input.chm output/
  chm_converter "C:/docs/help.chm" "D:/website/"
  python -m chm_converter input.chm output/
        '''
    )
    
    parser.add_argument(
        'chm_path',
        type=str,
        help='CHM文件路径'
    )
    
    parser.add_argument(
        'output_dir',
        type=str,
        help='输出目录路径'
    )
    
    parser.add_argument(
        '-t', '--title',
        type=str,
        default=None,
        help='自定义网站标题（默认从CHM文件提取）'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='安静模式，减少输出'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='CHM Converter 1.0.0'
    )
    
    args = parser.parse_args()
    
    # 验证输入文件
    chm_path = Path(args.chm_path)
    if not chm_path.exists():
        print(f"错误: CHM文件不存在: {chm_path}", file=sys.stderr)
        sys.exit(1)
    
    if chm_path.suffix.lower() != '.chm':
        print(f"警告: 文件扩展名不是.chm: {chm_path}")
    
    # 创建生成器并执行
    generator = StaticSiteGenerator(
        chm_path=str(chm_path),
        output_dir=args.output_dir,
        custom_title=args.title
    )
    
    generator.verbose = not args.quiet
    
    success = generator.generate()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
