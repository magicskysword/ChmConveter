#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
静态网站生成器模块

负责将解压后的CHM内容转换为静态网站
"""

import json
import shutil
import re
from pathlib import Path
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

from .models import TocItem
from .extractor import ChmExtractor
from .parser import parse_hhc_file, extract_title_from_hhc
from .template_manager import TemplateManager


class StaticSiteGenerator:
    """静态网站生成器
    
    Attributes:
        chm_path: CHM文件路径
        output_dir: 输出目录
        extractor: CHM解压器
        template_manager: 模板管理器
        search_index: 搜索索引数据
        available_css: 可用的CSS文件列表
        has_dark_theme: 是否有暗色主题CSS
    """
    
    # 可能存在的CSS文件（用于检测）
    CSS_FILES_LIGHT = [
        'lesson_light.css',
        'custom_lesson_light.css',
    ]
    
    CSS_FILES_DARK = [
        'lesson_dark.css',
        'custom_lesson_dark.css',
    ]
    
    # 需要排除的文件/目录模式
    EXCLUDE_PATTERNS = [
        '#*',  # CHM内部元数据
        '$*',  # CHM内部数据
        '*.hhc',
        '*.hhk',
        '*.hhp',
    ]
    
    def __init__(self, chm_path: str, output_dir: str):
        """初始化生成器
        
        Args:
            chm_path: CHM文件路径
            output_dir: 输出目录路径
        """
        self.chm_path = Path(chm_path)
        self.output_dir = Path(output_dir)
        self.extractor = ChmExtractor(chm_path)
        self.template_manager = TemplateManager()
        self.search_index: List[Dict] = []
        self.extracted_dir: Optional[Path] = None
        
        # CSS检测结果
        self.available_css: List[str] = []
        self.has_dark_theme: bool = False
        
        # 配置选项
        self.search_content_max_length = 500
        self.verbose = True
    
    def generate(self) -> bool:
        """生成静态网站
        
        Returns:
            是否成功生成
        """
        try:
            self._log(f"开始转换CHM文件...")
            self._log(f"源文件: {self.chm_path}")
            self._log(f"输出目录: {self.output_dir}")
            
            # 解压CHM文件
            self._log("正在解压CHM文件...")
            self.extracted_dir = self.extractor.extract()
            self._log(f"已解压到: {self.extracted_dir}")
            
            # 查找并解析目录文件
            hhc_file = self.extractor.find_hhc_file()
            if not hhc_file:
                self._log("警告: 未找到.hhc目录文件，将扫描HTML文件")
                toc = self._build_toc_from_files()
            else:
                self._log(f"解析目录文件: {hhc_file.name}")
                toc = parse_hhc_file(hhc_file)
            
            # 获取文档标题
            title = extract_title_from_hhc(toc)
            self._log(f"文档标题: {title}")
            
            # 统计
            counts = toc.count_items()
            self._log(f"发现 {counts['folders']} 个文件夹, {counts['files']} 个文件")
            
            # 创建输出目录
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建资源文件
            self._create_assets()
            
            # 复制并处理内容文件
            self._copy_content_files(toc)
            
            # 生成目录数据
            tree_data = toc.to_dict()
            self._write_json('assets/tree-data.js', 
                           f'const treeData = {json.dumps(tree_data, ensure_ascii=False, indent=2)};')
            
            # 生成搜索索引
            self._write_json('assets/search-index.js', 
                           f'const searchIndex = {json.dumps(self.search_index, ensure_ascii=False)};')
            
            # 生成主页
            self._generate_index_page(title)
            
            self._log(f"\n✓ 静态网站生成完成！")
            self._log(f"  输出目录: {self.output_dir}")
            self._log(f"  打开 index.html 查看网站")
            self._log(f"  共生成 {len(self.search_index)} 个可搜索页面")
            
            return True
            
        except Exception as e:
            self._log(f"错误: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # 清理临时文件
            if self.extractor:
                self.extractor.cleanup()
    
    def _log(self, message: str):
        """输出日志信息"""
        if self.verbose:
            print(message)
    
    def _build_toc_from_files(self) -> TocItem:
        """从HTML文件构建目录树
        
        Returns:
            目录树根节点
        """
        root = TocItem(name="目录")
        
        html_files = self.extractor.list_html_files()
        for html_file in html_files:
            rel_path = html_file.relative_to(self.extracted_dir)
            
            # 提取标题
            title = self._extract_title(html_file)
            if not title:
                title = html_file.stem
            
            root.children.append(TocItem(
                name=title,
                local=str(rel_path).replace('\\', '/')
            ))
        
        return root
    
    def _extract_title(self, html_path: Path) -> str:
        """从HTML文件提取标题"""
        try:
            encodings = ['gb18030', 'gbk', 'utf-8', 'gb2312']
            content = None
            
            for encoding in encodings:
                try:
                    with open(html_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if not content:
                return ""
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # 尝试从各种位置获取标题
            for selector in ['.fileheader', 'h1', 'title']:
                elem = soup.select_one(selector)
                if elem and elem.get_text().strip():
                    return elem.get_text().strip()
            
            return ""
        except Exception:
            return ""
    
    def _create_assets(self):
        """创建资源文件"""
        assets_dir = self.output_dir / 'assets'
        assets_dir.mkdir(exist_ok=True)
        
        # 写入CSS文件（用于主页面）
        self._write_file(assets_dir / 'style.css', 
                        self.template_manager.get_style_css())
        
        # 写入JavaScript文件
        self._write_file(assets_dir / 'app.js', 
                        self.template_manager.get_app_js())
        
        # 复制原CHM的CSS文件到content目录
        self._copy_source_css()
        
        # 复制图片目录和其他资源
        self._copy_resources()
    
    def _copy_source_css(self):
        """复制原CHM的CSS文件到content目录，并检测可用的CSS"""
        content_dir = self.output_dir / 'content'
        content_dir.mkdir(exist_ok=True)
        
        self.available_css = []
        light_css_found = False
        dark_css_found = False
        
        # 检测并复制亮色主题CSS
        for css_file in self.CSS_FILES_LIGHT:
            src = self.extracted_dir / css_file
            if src.exists():
                dst = content_dir / css_file
                shutil.copy2(src, dst)
                self.available_css.append(css_file)
                light_css_found = True
        
        # 检测并复制暗色主题CSS
        for css_file in self.CSS_FILES_DARK:
            src = self.extracted_dir / css_file
            if src.exists():
                dst = content_dir / css_file
                shutil.copy2(src, dst)
                self.available_css.append(css_file)
                dark_css_found = True
        
        # 只有当同时存在亮色和暗色主题时才启用主题切换
        self.has_dark_theme = light_css_found and dark_css_found
        
        if self.available_css:
            self._log(f"已复制 {len(self.available_css)} 个主题CSS文件到content目录")
            if self.has_dark_theme:
                self._log("检测到暗色主题CSS，启用主题切换功能")
            else:
                self._log("未检测到完整的暗色主题CSS，禁用主题切换功能")
        
        # 复制CHM中的所有其他CSS文件（保持相对路径）
        other_css_count = 0
        for css_file in self.extracted_dir.rglob('*.css'):
            try:
                rel_path = css_file.relative_to(self.extracted_dir)
            except ValueError:
                continue
            
            # 跳过CHM内部目录
            if any(part.startswith('#') or part.startswith('$') for part in rel_path.parts):
                continue
            
            # 跳过已复制的主题CSS
            if rel_path.name in self.CSS_FILES_LIGHT + self.CSS_FILES_DARK:
                continue
            
            dst = content_dir / rel_path
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(css_file, dst)
                other_css_count += 1
        
        if other_css_count > 0:
            self._log(f"已复制 {other_css_count} 个其他CSS文件")
    
    def _copy_resources(self):
        """复制所有图片和资源文件
        
        扫描解压目录中的所有图片文件和可能的资源目录，
        保持相对路径结构复制到content目录
        """
        content_dir = self.output_dir / 'content'
        content_dir.mkdir(exist_ok=True)
        
        # 图片扩展名
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp'}
        
        # 可能的资源目录名（不区分大小写）
        resource_folder_patterns = {'images', 'images~', 'img', 'imgs', 'image', 'assets', 'res', 'resources', 'pics', 'pictures'}
        
        copied_folders = set()
        copied_files = 0
        
        # 1. 先复制资源目录（保持目录结构）
        for item in self.extracted_dir.iterdir():
            if item.is_dir():
                folder_lower = item.name.lower()
                if folder_lower in resource_folder_patterns or folder_lower.startswith('image'):
                    dst_folder = content_dir / item.name
                    try:
                        if dst_folder.exists():
                            shutil.rmtree(dst_folder, ignore_errors=True)
                        shutil.copytree(item, dst_folder, dirs_exist_ok=True)
                        copied_folders.add(item.name)
                        self._log(f"已复制资源文件夹: {item.name}")
                    except Exception as e:
                        self._log(f"警告: 复制资源文件夹时出错: {e}")
        
        # 2. 扫描所有子目录中的图片文件（不在已复制的资源目录中）
        for img_file in self.extracted_dir.rglob('*'):
            if not img_file.is_file():
                continue
            
            if img_file.suffix.lower() not in image_extensions:
                continue
            
            # 计算相对路径
            try:
                rel_path = img_file.relative_to(self.extracted_dir)
            except ValueError:
                continue
            
            # 跳过已复制的资源目录中的文件
            if rel_path.parts and rel_path.parts[0] in copied_folders:
                continue
            
            # 跳过CHM内部目录
            if any(part.startswith('#') or part.startswith('$') for part in rel_path.parts):
                continue
            
            # 复制图片文件
            dst_file = content_dir / rel_path
            if not dst_file.exists():
                try:
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(img_file, dst_file)
                    copied_files += 1
                except Exception as e:
                    self._log(f"警告: 复制图片文件时出错 {rel_path}: {e}")
        
        if copied_files > 0:
            self._log(f"已复制 {copied_files} 个散落的图片文件")
    
    def _copy_content_files(self, toc: TocItem):
        """复制并处理内容文件
        
        Args:
            toc: 目录树
        """
        content_dir = self.output_dir / 'content'
        content_dir.mkdir(exist_ok=True)
        
        # 获取所有文件
        all_files = toc.get_all_files()
        
        for item in all_files:
            if not item.local:
                continue
            
            src = self.extracted_dir / item.local
            if not src.exists():
                continue
            
            # 目标路径
            dst = content_dir / item.local
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # 处理HTML文件
            if src.suffix.lower() in ['.html', '.htm']:
                self._process_html_file(src, dst, item.name)
                
                # 添加到搜索索引
                text_content = self._extract_text(src)
                if text_content:
                    self.search_index.append({
                        'title': item.name,
                        'path': f'content/{item.local}',
                        'content': text_content[:self.search_content_max_length]
                    })
            else:
                # 直接复制其他文件
                shutil.copy2(src, dst)
    
    def _process_html_file(self, src: Path, dst: Path, title: str):
        """处理HTML文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            title: 页面标题
        """
        try:
            # 读取源文件
            content = self._read_file(src)
            if content is None:
                shutil.copy2(src, dst)
                return
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # 提取原始的样式和脚本信息
            original_styles = ""
            original_css_links = ""
            original_scripts = ""
            
            head = soup.find('head')
            if head:
                # 提取<style>标签
                style_tags = head.find_all('style')
                if style_tags:
                    original_styles = '\n    '.join(str(tag) for tag in style_tags)
                
                # 提取<link rel="stylesheet">标签
                link_tags = head.find_all('link', rel='stylesheet')
                if link_tags:
                    original_css_links = '\n    '.join(str(tag) for tag in link_tags)
            
            # 提取所有<script>标签（包括head和body中的）
            script_tags = soup.find_all('script')
            if script_tags:
                original_scripts = '\n    '.join(str(tag) for tag in script_tags)
            
            # 提取body内容
            body = soup.find('body')
            body_content = ""
            
            if body:
                # 移除导航面板
                for nav in body.find_all('div', class_='lme_nav_panel_cls'):
                    nav.decompose()
                for nav in body.find_all('div', id='lme_nav_panel'):
                    nav.decompose()
                
                # 移除页脚
                for foot in body.find_all('div', class_='foot'):
                    foot.decompose()
                for hr in body.find_all('hr', class_='footline'):
                    hr.decompose()
                
                # 移除主题切换按钮
                for img in body.find_all('img', id='theme_switcher'):
                    parent = img.parent
                    if parent and parent.name == 'div':
                        parent.decompose()
                    else:
                        img.decompose()
                
                # 移除幻灯片控制
                for elem in body.find_all('div', id='slide_control_panel'):
                    elem.decompose()
                for elem in body.find_all('div', id='slides_trigger'):
                    elem.decompose()
                for elem in body.find_all('div', id='popup_base_panel'):
                    elem.decompose()
                for elem in body.find_all('div', id='popup_panel'):
                    elem.decompose()
                
                # 获取内容
                body_content = ''.join(str(child) for child in body.children)
            
            # 计算CSS路径前缀
            rel_path = dst.relative_to(self.output_dir / 'content')
            depth = len(rel_path.parts) - 1
            css_prefix = '../' * depth if depth > 0 else './'
            
            # 创建新的HTML，传递可用的CSS信息、原始样式和脚本
            new_html = self.template_manager.get_content_html(
                title, body_content, css_prefix, 
                self.available_css, self.has_dark_theme,
                original_styles, original_css_links, original_scripts)
            
            with open(dst, 'w', encoding='utf-8') as f:
                f.write(new_html)
                
        except Exception as e:
            self._log(f"警告: 处理 {src} 时出错: {e}")
            shutil.copy2(src, dst)
    
    def _read_file(self, path: Path) -> Optional[str]:
        """尝试用多种编码读取文件"""
        encodings = ['gb18030', 'gbk', 'utf-8', 'gb2312']
        
        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        return None
    
    def _extract_text(self, html_path: Path) -> str:
        """提取纯文本内容"""
        try:
            content = self._read_file(html_path)
            if not content:
                return ""
            
            soup = BeautifulSoup(content, 'html.parser')
            
            for elem in soup.find_all(['script', 'style']):
                elem.decompose()
            
            return soup.get_text(separator=' ', strip=True)
        except Exception:
            return ""
    
    def _generate_index_page(self, title: str):
        """生成主页"""
        index_html = self.template_manager.get_index_html(title, self.has_dark_theme)
        self._write_file(self.output_dir / 'index.html', index_html)
    
    def _write_file(self, path: Path, content: str):
        """写入文件"""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _write_json(self, rel_path: str, content: str):
        """写入JSON/JS文件"""
        path = self.output_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
