#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模板管理器模块

负责加载和渲染HTML/CSS/JS模板
"""

import html
from pathlib import Path
from typing import Dict, Any


class TemplateManager:
    """模板管理器
    
    负责从templates目录加载模板文件并进行变量替换
    """
    
    def __init__(self, templates_dir: Path = None):
        """初始化模板管理器
        
        Args:
            templates_dir: 模板目录路径，默认为包内的templates目录
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / 'templates'
        
        self.templates_dir = templates_dir
        self._cache: Dict[str, str] = {}
    
    def load_template(self, name: str) -> str:
        """加载模板文件
        
        Args:
            name: 模板文件名
            
        Returns:
            模板内容
            
        Raises:
            FileNotFoundError: 模板文件不存在
        """
        if name in self._cache:
            return self._cache[name]
        
        template_path = self.templates_dir / name
        if not template_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self._cache[name] = content
        return content
    
    def render(self, name: str, variables: Dict[str, Any]) -> str:
        """渲染模板
        
        使用简单的变量替换，格式为 {{variable_name}}
        
        Args:
            name: 模板文件名
            variables: 变量字典
            
        Returns:
            渲染后的内容
        """
        template = self.load_template(name)
        
        for key, value in variables.items():
            placeholder = '{{' + key + '}}'
            template = template.replace(placeholder, str(value))
        
        return template
    
    def get_index_html(self, site_title: str, has_dark_theme: bool = True) -> str:
        """获取渲染后的主页HTML
        
        Args:
            site_title: 网站标题
            has_dark_theme: 是否有暗色主题
            
        Returns:
            渲染后的HTML内容
        """
        # 如果没有暗色主题，隐藏主题切换按钮
        theme_toggle_style = '' if has_dark_theme else 'display: none;'
        
        return self.render('index.html', {
            'site_title': html.escape(site_title),
            'theme_toggle_style': theme_toggle_style
        })
    
    def get_content_html(self, title: str, body_content: str, css_prefix: str,
                         available_css: list = None, has_dark_theme: bool = True,
                         original_styles: str = "", original_css_links: str = "",
                         original_scripts: str = "") -> str:
        """获取渲染后的内容页面HTML
        
        Args:
            title: 页面标题
            body_content: 正文内容
            css_prefix: CSS文件前缀路径（相对于内容文件的路径）
            available_css: 可用的CSS文件列表
            has_dark_theme: 是否有暗色主题
            original_styles: 原始HTML中的<style>标签内容
            original_css_links: 原始HTML中的<link>CSS引用
            original_scripts: 原始HTML中的<script>标签内容
            
        Returns:
            渲染后的HTML内容
        """
        if available_css is None:
            available_css = []
        
        # 生成CSS链接
        css_links = []
        for css_file in available_css:
            # 亮色主题CSS作为默认
            if 'light' in css_file:
                link_id = 'theme_link' if css_file == 'lesson_light.css' else 'custom_theme_link'
                css_links.append(f'<link id="{link_id}" rel="stylesheet" href="{css_prefix}{css_file}" type="text/css">')
        
        css_links_html = '\n    '.join(css_links) if css_links else ''
        
        # 添加原始CSS链接和样式
        all_styles = []
        if css_links_html:
            all_styles.append(css_links_html)
        if original_css_links:
            all_styles.append(original_css_links)
        if original_styles:
            all_styles.append(original_styles)
        
        combined_styles = '\n    '.join(all_styles)
        
        # 生成主题切换脚本
        if has_dark_theme:
            theme_script = f'''
        // 主题切换函数
        function setTheme(theme) {{
            const cssPrefix = '{css_prefix}';
            const themeLink = document.getElementById('theme_link');
            const customThemeLink = document.getElementById('custom_theme_link');
            
            if (theme === 'dark') {{
                if (themeLink) themeLink.href = cssPrefix + 'lesson_dark.css';
                if (customThemeLink) customThemeLink.href = cssPrefix + 'custom_lesson_dark.css';
            }} else {{
                if (themeLink) themeLink.href = cssPrefix + 'lesson_light.css';
                if (customThemeLink) customThemeLink.href = cssPrefix + 'custom_lesson_light.css';
            }}
        }}
        
        // 监听父窗口的主题变化消息
        window.addEventListener('message', function(e) {{
            if (e.data && e.data.type === 'themeChange') {{
                setTheme(e.data.theme);
            }}
        }});
        
        // 页面加载时，向父窗口请求当前主题
        if (window.parent && window.parent !== window) {{
            window.parent.postMessage({{type: 'pageLoaded', title: '{html.escape(title).replace("'", "\\'")}'}}, '*');
            window.parent.postMessage({{type: 'requestTheme'}}, '*');
        }}'''
        else:
            # 如果没有原始脚本，才添加postMessage通知
            theme_script = '' if original_scripts.strip() else f'''
        // 页面加载通知
        if (window.parent && window.parent !== window) {{
            window.parent.postMessage({{type: 'pageLoaded', title: '{html.escape(title).replace("'", "\\'")}'}}, '*');
        }}'''
        
        # 构建完整HTML
        content_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    {combined_styles}
</head>
<body>
{body_content}
{original_scripts}
<script>{theme_script}
</script>
</body>
</html>
'''
        return content_html
    
    def get_style_css(self) -> str:
        """获取主样式表内容"""
        return self.load_template('style.css')
    
    def get_content_style_css(self) -> str:
        """获取内容页面样式表内容"""
        return self.load_template('content-style.css')
    
    def get_app_js(self) -> str:
        """获取主JavaScript内容"""
        return self.load_template('app.js')
    
    def clear_cache(self):
        """清除模板缓存"""
        self._cache.clear()
