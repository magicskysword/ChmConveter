#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据模型模块

定义用于表示目录树结构的数据类
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class TocItem:
    """表示目录树中的一个节点
    
    Attributes:
        name: 节点名称/标题
        local: 本地文件路径
        image_number: 图标编号（可选）
        children: 子节点列表
    """
    name: str
    local: str = ""
    image_number: Optional[int] = None
    children: List['TocItem'] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于JSON序列化
        
        Returns:
            包含节点信息的字典
        """
        result = {
            'title': self.name,
            'path': self.local,
            'type': 'Folder' if self.children else 'File',
            'children': [child.to_dict() for child in self.children]
        }
        return result
    
    def get_all_files(self) -> List['TocItem']:
        """获取所有文件节点
        
        Returns:
            所有有local路径的节点列表
        """
        files = []
        
        if self.local:
            files.append(self)
        
        for child in self.children:
            files.extend(child.get_all_files())
        
        return files
    
    def count_items(self) -> Dict[str, int]:
        """统计节点数量
        
        Returns:
            包含各类型节点数量的字典
        """
        counts = {'folders': 0, 'files': 0}
        
        if self.children:
            counts['folders'] = 1
        if self.local:
            counts['files'] = 1
        
        for child in self.children:
            child_counts = child.count_items()
            counts['folders'] += child_counts['folders']
            counts['files'] += child_counts['files']
        
        return counts


@dataclass
class ChmInfo:
    """CHM文件信息
    
    Attributes:
        title: 文档标题
        default_topic: 默认主题文件
        toc_file: 目录文件(.hhc)路径
        index_file: 索引文件(.hhk)路径
    """
    title: str = ""
    default_topic: str = ""
    toc_file: str = ""
    index_file: str = ""
