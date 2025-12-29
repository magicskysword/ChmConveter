#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HHC解析器模块

负责解析CHM的目录文件(.hhc)，生成目录树结构
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple
from html.parser import HTMLParser

from .models import TocItem


class HhcParser(HTMLParser):
    """解析.hhc文件的HTML解析器
    
    .hhc文件使用嵌套的<UL>/<LI>结构表示目录层级，
    每个条目是一个<OBJECT>元素，包含Name和Local参数。
    """
    
    def __init__(self):
        super().__init__()
        self.root = TocItem(name="Root")
        self.stack: List[TocItem] = [self.root]
        self.current_item: Optional[TocItem] = None
        self.in_object = False
        self.current_params: dict = {}
    
    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        tag = tag.lower()
        
        if tag == 'ul':
            # 开始新的层级
            if self.current_item:
                self.stack.append(self.current_item)
                self.current_item = None
        
        elif tag == 'object':
            # 开始一个新条目
            self.in_object = True
            self.current_params = {}
        
        elif tag == 'param' and self.in_object:
            # 提取参数
            attrs_dict = dict(attrs)
            name = attrs_dict.get('name', '').lower()
            value = attrs_dict.get('value', '')
            
            if name == 'name':
                self.current_params['name'] = value
            elif name == 'local':
                self.current_params['local'] = value
            elif name == 'imagenumber':
                try:
                    self.current_params['image_number'] = int(value)
                except ValueError:
                    pass
    
    def handle_endtag(self, tag: str):
        tag = tag.lower()
        
        if tag == 'ul':
            # 结束当前层级
            if len(self.stack) > 1:
                self.stack.pop()
            self.current_item = None
        
        elif tag == 'object':
            # 完成一个条目
            self.in_object = False
            
            if 'name' in self.current_params:
                item = TocItem(
                    name=self.current_params.get('name', ''),
                    local=self.current_params.get('local', ''),
                    image_number=self.current_params.get('image_number')
                )
                
                # 添加到当前层级
                if self.stack:
                    self.stack[-1].children.append(item)
                
                self.current_item = item
            
            self.current_params = {}
    
    def get_toc(self) -> TocItem:
        """获取解析后的目录树
        
        Returns:
            根节点
        """
        return self.root


def parse_hhc_file(hhc_path: Path) -> TocItem:
    """解析.hhc文件
    
    Args:
        hhc_path: .hhc文件路径
        
    Returns:
        目录树根节点
    """
    # 尝试多种编码读取
    encodings = ['gb18030', 'gbk', 'utf-8', 'gb2312', 'cp936']
    content = None
    
    for encoding in encodings:
        try:
            with open(hhc_path, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        raise ValueError(f"无法读取文件: {hhc_path}")
    
    # 预处理：修复一些常见的格式问题
    # 移除DOCTYPE和HTML标签外的内容
    content = re.sub(r'<!DOCTYPE[^>]*>', '', content, flags=re.IGNORECASE)
    
    parser = HhcParser()
    parser.feed(content)
    
    return parser.get_toc()


def extract_title_from_hhc(toc: TocItem) -> str:
    """从目录树中提取文档标题
    
    通常第一个条目或第二个条目是文档标题
    
    Args:
        toc: 目录树根节点
        
    Returns:
        文档标题
    """
    if toc.children:
        # 跳过"目录"节点，查找实际标题
        for child in toc.children:
            if child.name and child.name != "目录":
                return child.name
        # 如果都是"目录"，返回第一个
        return toc.children[0].name
    
    return "未命名文档"
