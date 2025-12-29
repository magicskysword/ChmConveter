#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CHM解压模块

负责将CHM文件解压到临时目录
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List


class ChmExtractor:
    """CHM文件解压器
    
    使用7-Zip解压CHM文件，如果7-Zip不可用则尝试使用hh.exe
    """
    
    # 常见的7-Zip安装路径
    SEVEN_ZIP_PATHS = [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
    ]
    
    def __init__(self, chm_path: str):
        """初始化解压器
        
        Args:
            chm_path: CHM文件路径
        """
        self.chm_path = Path(chm_path)
        if not self.chm_path.exists():
            raise FileNotFoundError(f"CHM文件不存在: {chm_path}")
        
        self._7z_path = self._find_7zip()
        self._extracted_dir: Optional[Path] = None
    
    def _find_7zip(self) -> Optional[str]:
        """查找7-Zip可执行文件
        
        Returns:
            7z.exe的路径，如果未找到则返回None
        """
        # 首先检查PATH中是否有7z
        try:
            result = subprocess.run(
                ['7z', '--help'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return '7z'
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # 检查常见安装路径
        for path in self.SEVEN_ZIP_PATHS:
            if os.path.exists(path):
                return path
        
        return None
    
    def extract(self, output_dir: Optional[str] = None) -> Path:
        """解压CHM文件
        
        Args:
            output_dir: 输出目录，如果为None则创建临时目录
            
        Returns:
            解压后的目录路径
            
        Raises:
            RuntimeError: 解压失败
        """
        if output_dir:
            extract_path = Path(output_dir)
            extract_path.mkdir(parents=True, exist_ok=True)
        else:
            # 创建临时目录
            extract_path = Path(tempfile.mkdtemp(prefix='chm_'))
        
        self._extracted_dir = extract_path
        
        # 优先使用7-Zip
        if self._7z_path:
            success = self._extract_with_7zip(extract_path)
            if success:
                return extract_path
        
        # 尝试使用hh.exe
        success = self._extract_with_hh(extract_path)
        if success:
            return extract_path
        
        raise RuntimeError("无法解压CHM文件，请确保安装了7-Zip或HTML Help Workshop")
    
    def _extract_with_7zip(self, output_dir: Path) -> bool:
        """使用7-Zip解压
        
        Args:
            output_dir: 输出目录
            
        Returns:
            是否成功
        """
        try:
            cmd = [
                self._7z_path,
                'x',
                str(self.chm_path),
                f'-o{output_dir}',
                '-y'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60
            )
            
            return result.returncode == 0
        except subprocess.SubprocessError:
            return False
    
    def _extract_with_hh(self, output_dir: Path) -> bool:
        """使用hh.exe解压
        
        Args:
            output_dir: 输出目录
            
        Returns:
            是否成功
        """
        try:
            cmd = [
                'hh',
                '-decompile',
                str(output_dir),
                str(self.chm_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60,
                shell=True
            )
            
            # hh.exe 即使成功也可能返回非0
            # 检查是否有文件被解压
            files = list(output_dir.iterdir())
            return len(files) > 0
        except subprocess.SubprocessError:
            return False
    
    def cleanup(self):
        """清理解压的临时目录"""
        if self._extracted_dir and self._extracted_dir.exists():
            if str(self._extracted_dir).startswith(tempfile.gettempdir()):
                shutil.rmtree(self._extracted_dir, ignore_errors=True)
                self._extracted_dir = None
    
    def get_extracted_dir(self) -> Optional[Path]:
        """获取解压目录
        
        Returns:
            解压目录路径
        """
        return self._extracted_dir
    
    def find_hhc_file(self) -> Optional[Path]:
        """查找.hhc目录文件
        
        Returns:
            .hhc文件路径
        """
        if not self._extracted_dir:
            return None
        
        for f in self._extracted_dir.glob('*.hhc'):
            return f
        
        return None
    
    def find_hhk_file(self) -> Optional[Path]:
        """查找.hhk索引文件
        
        Returns:
            .hhk文件路径
        """
        if not self._extracted_dir:
            return None
        
        for f in self._extracted_dir.glob('*.hhk'):
            return f
        
        return None
    
    def list_html_files(self) -> List[Path]:
        """列出所有HTML文件
        
        Returns:
            HTML文件路径列表
        """
        if not self._extracted_dir:
            return []
        
        return list(self._extracted_dir.rglob('*.html')) + \
               list(self._extracted_dir.rglob('*.htm'))
