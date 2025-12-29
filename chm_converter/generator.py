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
    
    def __init__(self, chm_path: str, output_dir: str, verbose: bool = True, custom_title: Optional[str] = None):
        """初始化生成器
        
        Args:
            chm_path: CHM文件路径
            output_dir: 输出目录路径
            verbose: 是否显示详细信息
            custom_title: 自定义标题（优先级最高）
        """
        self.chm_path = Path(chm_path)
        self.output_dir = Path(output_dir)
        self.custom_title = custom_title
        self.extractor = ChmExtractor(chm_path)
        self.template_manager = TemplateManager()
        self.search_index: List[Dict] = []
        self.extracted_dir: Optional[Path] = None
        
        # CSS检测结果
        self.available_css: List[str] = []
        self.has_dark_theme: bool = False
        
        # 配置选项
        self.search_content_max_length = 500
        self.verbose = verbose
    
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
            
            # 获取文档标题（优先级：自定义 > CHM标题 > .hhc提取）
            if self.custom_title:
                title = self.custom_title
                self._log(f"使用自定义标题: {title}")
            else:
                # 尝试从CHM的.hhp文件提取标题
                chm_title = self.extractor.get_chm_title()
                if chm_title:
                    title = chm_title
                    self._log(f"从CHM提取标题: {title}")
                else:
                    # 回退到从.hhc目录结构提取
                    title = extract_title_from_hhc(toc)
                    self._log(f"从目录结构提取标题: {title}")
            
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
    
    def _should_exclude_item(self, path: Path) -> bool:
        """判断是否应该排除某个文件或目录
        
        Args:
            path: 文件或目录路径
            
        Returns:
            是否应该排除
        """
        name = path.name
        return self._should_exclude_by_name(name)
    
    def _should_exclude_by_name(self, name: str) -> bool:
        """根据名称判断是否应该排除
        
        Args:
            name: 文件或目录名
            
        Returns:
            是否应该排除
        """
        # CHM内部元数据文件和目录
        if name.startswith('#') or name.startswith('$'):
            return True
        
        # CHM项目文件
        if name.lower().endswith(('.hhc', '.hhk', '.hhp')):
            return True
        
        return False
    
    def _find_title_in_toc(self, toc: TocItem, local_path: str) -> Optional[str]:
        """在目录树中查找文件的标题
        
        Args:
            toc: 目录树根节点
            local_path: 文件的相对路径
            
        Returns:
            文件标题，如果未找到则返回None
        """
        def search(item: TocItem) -> Optional[str]:
            if item.local and item.local == local_path:
                return item.name
            
            for child in item.children:
                result = search(child)
                if result:
                    return result
            
            return None
        
        return search(toc)
    
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
        
        # 复制所有文件（使用黑名单机制）
        self._copy_all_files()
        
        # 检测CSS主题
        self._detect_css_themes()
    
    def _detect_css_themes(self):
        """检测可用的CSS主题文件"""
        content_dir = self.output_dir / 'content'
        
        self.available_css = []
        light_css_found = False
        dark_css_found = False
        
        # 检测亮色主题CSS
        for css_file in self.CSS_FILES_LIGHT:
            css_path = content_dir / css_file
            if css_path.exists():
                self.available_css.append(css_file)
                light_css_found = True
        
        # 检测暗色主题CSS
        for css_file in self.CSS_FILES_DARK:
            css_path = content_dir / css_file
            if css_path.exists():
                self.available_css.append(css_file)
                dark_css_found = True
        
        # 只有当同时存在亮色和暗色主题时才启用主题切换
        self.has_dark_theme = light_css_found and dark_css_found
        
        if self.available_css:
            self._log(f"检测到 {len(self.available_css)} 个主题CSS文件")
            if self.has_dark_theme:
                self._log("启用主题切换功能")
            else:
                self._log("未检测到完整的暗色主题，禁用主题切换功能")
    
    def _copy_all_files(self):
        """使用黑名单机制复制所有文件
        
        复制CHM解压目录中的所有文件和目录到content目录，
        只排除CHM内部元数据文件（#*、$*等）
        """
        content_dir = self.output_dir / 'content'
        content_dir.mkdir(exist_ok=True)
        
        copied_folders = 0
        copied_files = 0
        
        # 遍历解压目录中的所有项
        for item in self.extracted_dir.iterdir():
            # 检查是否应该排除
            if self._should_exclude_item(item):
                continue
            
            dst_item = content_dir / item.name
            
            if item.is_dir():
                # 复制整个目录
                try:
                    if dst_item.exists():
                        shutil.rmtree(dst_item, ignore_errors=True)
                    shutil.copytree(item, dst_item, 
                                  ignore=lambda src, names: [n for n in names if self._should_exclude_by_name(n)],
                                  dirs_exist_ok=True)
                    copied_folders += 1
                    self._log(f"已复制目录: {item.name}")
                except Exception as e:
                    self._log(f"警告: 复制目录时出错 {item.name}: {e}")
            
            elif item.is_file():
                # 复制文件
                try:
                    shutil.copy2(item, dst_item)
                    copied_files += 1
                except Exception as e:
                    self._log(f"警告: 复制文件时出错 {item.name}: {e}")
        
        self._log(f"已复制 {copied_folders} 个目录和 {copied_files} 个文件")
    
    def _copy_content_files(self, toc: TocItem):
        """处理HTML内容文件并构建搜索索引
        
        Args:
            toc: 目录树
        
        注意：文件已经在_copy_all_files中复制完成，
        这里只需要处理HTML文件和构建搜索索引
        """
        content_dir = self.output_dir / 'content'
        
        # 扫描所有已复制的HTML文件并处理
        processed_count = 0
        for html_file in content_dir.rglob('*'):
            if not html_file.is_file():
                continue
            
            if html_file.suffix.lower() not in ['.html', '.htm']:
                continue
            
            # 计算相对路径
            try:
                rel_path = html_file.relative_to(content_dir)
            except ValueError:
                continue
            
            # 获取源文件（用于重新读取和处理）
            src = self.extracted_dir / rel_path
            if not src.exists():
                continue
            
            # 从toc中查找标题
            title = self._find_title_in_toc(toc, str(rel_path).replace('\\', '/'))
            if not title:
                title = html_file.stem
            
            # 处理HTML文件（会覆盖已复制的文件，添加导航等）
            self._process_html_file(src, html_file, title)
            processed_count += 1
            
            # 添加到搜索索引
            text_content = self._extract_text(src)
            if text_content:
                self.search_index.append({
                    'title': title,
                    'path': f'content/{rel_path.as_posix()}',
                    'content': text_content[:self.search_content_max_length]
                })
        
        self._log(f"已处理 {processed_count} 个HTML文件")

    
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
                
                # 修复CSS table布局：为display:table-row的div添加table容器
                divs_to_wrap = []
                for div in body.find_all('div'):
                    style = div.get('style', '')
                    if style and ('display: table-row' in style.lower() or 'display:table-row' in style.lower()):
                        # 检查父元素是否已经是table
                        parent = div.parent
                        if parent and parent.name == 'body':
                            # 直接在body下的table-row需要包裹
                            divs_to_wrap.append(div)
                        elif parent and parent.name == 'div':
                            parent_style = parent.get('style', '')
                            if not (parent_style and ('display: table' in parent_style.lower() or 'display:table' in parent_style.lower())):
                                # 父div不是table，需要包裹
                                divs_to_wrap.append(div)
                
                # 执行包裹操作
                for div in divs_to_wrap:
                    wrapper = soup.new_tag('div', style='display: table')
                    div.insert_before(wrapper)
                    wrapper.append(div.extract())
                
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
