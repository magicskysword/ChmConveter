// ===== 应用状态 =====
const state = {
    currentPath: null,
    currentAnchor: null,
    theme: localStorage.getItem('theme') || 'light',
    sidebarCollapsed: false,
    bookmarks: JSON.parse(localStorage.getItem('bookmarks') || '[]'),
    currentTab: 'toc'
};

// ===== DOM元素 =====
const elements = {
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    menuToggle: document.getElementById('menuToggle'),
    themeToggle: document.getElementById('themeToggle'),
    tocTree: document.getElementById('tocTree'),
    quickSearchInput: document.getElementById('quickSearchInput'),
    quickSearchResults: document.getElementById('quickSearchResults'),
    searchInput: document.getElementById('searchInput'),
    searchButton: document.getElementById('searchButton'),
    searchResultsPanel: document.getElementById('searchResultsPanel'),
    searchStats: document.getElementById('searchStats'),
    searchResultsList: document.getElementById('searchResultsList'),
    contentBody: document.getElementById('contentBody'),
    contentFrame: document.getElementById('contentFrame'),
    welcomeScreen: document.getElementById('welcomeScreen'),
    breadcrumb: document.getElementById('breadcrumb'),
    bookmarksPanel: document.getElementById('bookmarksPanel'),
    bookmarksToggle: document.getElementById('bookmarksToggle'),
    bookmarksOpenToggle: document.getElementById('bookmarksOpenToggle'),
    addPageBookmark: document.getElementById('addPageBookmark'),
    bookmarksList: document.getElementById('bookmarksList')
};

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initTabs();
    initTocTree();
    initQuickSearch();
    initFullSearch();
    initSidebar();
    initNavigation();
    initBookmarks();
    initTextSelection();
    initMobileLayout(); // 初始化移动端布局
});

// ===== 标签页切换 =====
function initTabs() {
    document.querySelectorAll('.sidebar-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    state.currentTab = tabName;
    
    // 更新标签按钮状态
    document.querySelectorAll('.sidebar-tab').forEach(tab => {
        tab.classList.toggle('active', tab.getAttribute('data-tab') === tabName);
    });
    
    // 更新内容区域
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    if (tabName === 'toc') {
        document.getElementById('tocTab').classList.add('active');
    } else if (tabName === 'search') {
        document.getElementById('searchTab').classList.add('active');
        elements.searchInput.focus();
    }
}

// ===== 主题切换 =====
function initTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    
    if (elements.themeToggle) {
        elements.themeToggle.addEventListener('click', () => {
            state.theme = state.theme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', state.theme);
            localStorage.setItem('theme', state.theme);
            
            // 通知iframe更新主题
            if (elements.contentFrame.contentWindow) {
                elements.contentFrame.contentWindow.postMessage({type: 'themeChange', theme: state.theme}, '*');
            }
        });
    }
}

// ===== 侧边栏 =====
function initSidebar() {
    elements.sidebarToggle.addEventListener('click', () => {
        elements.sidebar.classList.add('collapsed');
    });
    
    elements.menuToggle.addEventListener('click', () => {
        elements.sidebar.classList.remove('collapsed');
    });
    
    // 移动端点击内容区域关闭侧边栏
    elements.contentBody.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
            elements.sidebar.classList.add('collapsed');
        }
    });
}

// ===== 目录树 =====
function initTocTree() {
    if (typeof treeData !== 'undefined') {
        elements.tocTree.innerHTML = buildTocTree(treeData);
        
        // 绑定文件夹点击事件 - 点击整个文件夹区域展开并加载
        document.querySelectorAll('.toc-folder').forEach(folder => {
            folder.addEventListener('click', (e) => {
                e.stopPropagation();
                
                // 展开/折叠子项
                folder.classList.toggle('expanded');
                const children = folder.nextElementSibling;
                if (children && children.classList.contains('toc-children')) {
                    children.classList.toggle('expanded');
                }
                
                // 如果有内容链接，也加载它
                const link = folder.querySelector('.toc-folder-link');
                if (link && link.hasAttribute('data-path')) {
                    loadContent(link.getAttribute('data-path'));
                }
            });
        });
        
        // 绑定文件点击事件
        document.querySelectorAll('.toc-file:not(.toc-folder-link)').forEach(file => {
            file.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const path = file.getAttribute('data-path');
                loadContent(path);
            });
        });
        
        // 默认展开第一层
        document.querySelectorAll('.toc-tree > .toc-item > .toc-folder').forEach(folder => {
            folder.classList.add('expanded');
            const children = folder.nextElementSibling;
            if (children) children.classList.add('expanded');
        });
    }
}

function buildTocTree(item, level = 0) {
    if (!item.children || item.children.length === 0) {
        // 叶子节点
        if (item.path) {
            const htmlPath = item.path.replace('.md', '.html');
            return `<div class="toc-item">
                <a class="toc-file" data-path="content/${htmlPath}" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</a>
            </div>`;
        }
        return '';
    }
    
    const childrenHtml = item.children.map(child => buildTocTree(child, level + 1)).join('');
    
    if (level === 0) {
        return childrenHtml;
    }
    
    // 文件夹节点
    const hasOwnContent = item.path && item.path.trim() !== '';
    const htmlPath = hasOwnContent ? item.path.replace('.md', '.html') : '';
    
    const titleHtml = hasOwnContent 
        ? `<a class="toc-folder-link toc-file" data-path="content/${htmlPath}" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</a>`
        : `<span class="toc-folder-title">${escapeHtml(item.title)}</span>`;
    
    return `<div class="toc-item">
        <div class="toc-folder">
            <svg class="toc-folder-icon" viewBox="0 0 24 24">
                <path fill="currentColor" d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
            </svg>
            ${titleHtml}
        </div>
        <div class="toc-children">${childrenHtml}</div>
    </div>`;
}

// ===== 快速搜索（目录页） =====
function initQuickSearch() {
    let searchTimeout;
    
    elements.quickSearchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            elements.quickSearchResults.classList.remove('active');
            return;
        }
        
        searchTimeout = setTimeout(() => {
            performQuickSearch(query);
        }, 300);
    });
    
    elements.quickSearchInput.addEventListener('focus', () => {
        if (elements.quickSearchInput.value.trim().length >= 2) {
            elements.quickSearchResults.classList.add('active');
        }
    });
    
    // 点击外部关闭搜索结果
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.quick-search-container')) {
            elements.quickSearchResults.classList.remove('active');
        }
    });
}

function performQuickSearch(query) {
    if (typeof searchIndex === 'undefined') return;
    
    const results = searchIndex.filter(item => {
        const searchText = (item.title + ' ' + item.content).toLowerCase();
        return searchText.includes(query.toLowerCase());
    }).slice(0, 10);
    
    if (results.length === 0) {
        elements.quickSearchResults.innerHTML = '<div class="search-result-item"><div class="search-result-title">未找到结果</div></div>';
    } else {
        elements.quickSearchResults.innerHTML = results.map(item => {
            const preview = highlightText(item.content.substring(0, 100), query);
            return `<div class="search-result-item" data-path="${escapeHtml(item.path)}">
                <div class="search-result-title">${escapeHtml(item.title)}</div>
                <div class="search-result-preview">${preview}...</div>
            </div>`;
        }).join('');
        
        document.querySelectorAll('.quick-search-results .search-result-item[data-path]').forEach(item => {
            item.addEventListener('click', () => {
                loadContent(item.getAttribute('data-path'));
                elements.quickSearchResults.classList.remove('active');
                elements.quickSearchInput.value = '';
            });
        });
    }
    
    elements.quickSearchResults.classList.add('active');
}

// ===== 全文搜索（搜索页） =====
function initFullSearch() {
    elements.searchButton.addEventListener('click', () => {
        performFullSearch();
    });
    
    elements.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performFullSearch();
        }
    });
}

function performFullSearch() {
    const query = elements.searchInput.value.trim();
    
    if (query.length < 2) {
        elements.searchStats.textContent = '请输入至少2个字符';
        elements.searchResultsList.innerHTML = '';
        return;
    }
    
    if (typeof searchIndex === 'undefined') {
        elements.searchStats.textContent = '搜索索引未加载';
        return;
    }
    
    const results = searchIndex.filter(item => {
        const searchText = (item.title + ' ' + item.content).toLowerCase();
        return searchText.includes(query.toLowerCase());
    });
    
    elements.searchStats.textContent = `找到 ${results.length} 个结果`;
    
    if (results.length === 0) {
        elements.searchResultsList.innerHTML = '<div class="no-results">未找到匹配的内容</div>';
    } else {
        elements.searchResultsList.innerHTML = results.map((item, index) => {
            const preview = highlightText(item.content.substring(0, 200), query);
            return `<div class="search-result-card" data-path="${escapeHtml(item.path)}">
                <div class="search-result-number">${index + 1}</div>
                <div class="search-result-content">
                    <div class="search-result-title">${highlightText(item.title, query)}</div>
                    <div class="search-result-preview">${preview}...</div>
                    <div class="search-result-path">${escapeHtml(item.path)}</div>
                </div>
            </div>`;
        }).join('');
        
        document.querySelectorAll('.search-result-card[data-path]').forEach(card => {
            card.addEventListener('click', () => {
                loadContent(card.getAttribute('data-path'));
                switchTab('toc'); // 切回目录页
            });
        });
    }
}

function highlightText(text, query) {
    const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
    return escapeHtml(text).replace(regex, '<span class="search-highlight">$1</span>');
}

// ===== 内容加载 =====
function loadContent(path, scrollToText = null, anchor = null) {
    state.currentPath = path;
    state.currentAnchor = anchor; // 保存锚点信息
    
    // 更新活动状态
    document.querySelectorAll('.toc-file').forEach(file => {
        file.classList.remove('active');
        if (file.getAttribute('data-path') === path) {
            file.classList.add('active');
            expandParentFolders(file);
        }
    });
    
    // 加载内容
    elements.contentFrame.src = path;
    elements.contentBody.classList.add('active');
    elements.welcomeScreen.classList.add('hidden');
    
    // 等待iframe加载完成后注入脚本
    const handleLoad = () => {
        // 先注入脚本
        setTimeout(() => {
            const injected = injectIframeScript();
            
            // 如果有锚点，滚动到对应位置
            if (anchor && injected) {
                setTimeout(() => {
                    try {
                        const iframeWin = elements.contentFrame.contentWindow;
                        const iframeDoc = elements.contentFrame.contentDocument;
                        if (iframeDoc && anchor) {
                            // 移除开头的 # 获取id
                            const anchorId = anchor.startsWith('#') ? anchor.substring(1) : anchor;
                            // 尝试多种方式查找元素
                            let targetElement = iframeDoc.getElementById(anchorId);
                            if (!targetElement) {
                                // 尝试通过name属性查找
                                targetElement = iframeDoc.querySelector(`[name="${anchorId}"]`);
                            }
                            if (!targetElement) {
                                // 尝试通过 CSS 选择器（处理特殊字符）
                                try {
                                    targetElement = iframeDoc.querySelector(`#${CSS.escape(anchorId)}`);
                                } catch (e) {
                                    // CSS.escape 可能不存在于旧浏览器
                                }
                            }
                            if (targetElement) {
                                targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            }
                        }
                    } catch (e) {
                        console.error('Failed to scroll to anchor:', e);
                    }
                }, 150);
            }
            // 如果需要滚动到书签位置
            else if (scrollToText && injected) {
                // 等待脚本初始化完成后再发送消息
                setTimeout(() => {
                    try {
                        const iframeWin = elements.contentFrame.contentWindow;
                        if (iframeWin && iframeWin.__bookmarkScriptInjected) {
                            iframeWin.postMessage({
                                type: 'scrollToBookmark',
                                range: scrollToText // scrollToText现在包含range数据
                            }, '*');
                            console.log('Scroll to bookmark message sent');
                        } else {
                            console.warn('Iframe script not ready, retrying...');
                            // 重试一次
                            setTimeout(() => {
                                if (iframeWin && iframeWin.__bookmarkScriptInjected) {
                                    iframeWin.postMessage({
                                        type: 'scrollToBookmark',
                                        range: scrollToText
                                    }, '*');
                                }
                            }, 200);
                        }
                    } catch (e) {
                        console.error('Failed to scroll to bookmark:', e);
                    }
                }, 150);
            }
        }, 50);
        
        elements.contentFrame.removeEventListener('load', handleLoad);
    };
    elements.contentFrame.addEventListener('load', handleLoad);
    
    // 更新面包屑
    updateBreadcrumb(path);
    
    // 更新URL（包含锚点）
    const urlHash = anchor ? '#' + path + anchor : '#' + path;
    history.pushState({path, anchor}, '', urlHash);
    
    // 移动端关闭侧边栏
    if (window.innerWidth <= 768) {
        elements.sidebar.classList.add('collapsed');
    }
}

function expandParentFolders(element) {
    let parent = element.parentElement;
    while (parent && !parent.classList.contains('toc-tree')) {
        if (parent.classList.contains('toc-children')) {
            parent.classList.add('expanded');
            const folder = parent.previousElementSibling;
            if (folder && folder.classList.contains('toc-folder')) {
                folder.classList.add('expanded');
            }
        }
        parent = parent.parentElement;
    }
}

function updateBreadcrumb(path) {
    const parts = path.replace('content/', '').split('/');
    let breadcrumbHtml = '';
    
    const title = findTitleByPath(path, treeData);
    if (title) {
        breadcrumbHtml = `<span class="breadcrumb-item">${escapeHtml(title)}</span>`;
    }
    
    elements.breadcrumb.innerHTML = breadcrumbHtml;
}

function findTitleByPath(path, item) {
    if (item.path && path.includes(item.path.replace('.md', '.html'))) {
        return item.title;
    }
    if (item.children) {
        for (const child of item.children) {
            const result = findTitleByPath(path, child);
            if (result) return result;
        }
    }
    return null;
}

// ===== 书签功能 =====
function initBookmarks() {
    // 收起/展开书签面板
    elements.bookmarksToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        elements.bookmarksPanel.classList.add('collapsed');
    });
    
    // 打开书签面板
    if (elements.bookmarksOpenToggle) {
        elements.bookmarksOpenToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            elements.bookmarksPanel.classList.remove('collapsed');
        });
    }
    
    // 添加整页书签
    elements.addPageBookmark.addEventListener('click', () => {
        if (state.currentPath) {
            const title = findTitleByPath(state.currentPath, treeData) || '未命名页面';
            addBookmark({
                type: 'page',
                path: state.currentPath,
                title: title,
                timestamp: Date.now()
            });
        }
    });
    
    // 清空所有书签
    const clearBookmarksBtn = document.getElementById('clearBookmarks');
    if (clearBookmarksBtn) {
        clearBookmarksBtn.addEventListener('click', () => {
            if (state.bookmarks.length === 0) {
                return;
            }
            if (confirm(`确定要清空所有书签吗？\n当前共有 ${state.bookmarks.length} 个书签，此操作不可恢复。`)) {
                state.bookmarks = [];
                localStorage.setItem('bookmarks', JSON.stringify(state.bookmarks));
                renderBookmarks();
            }
        });
    }
    
    // 渲染书签列表
    renderBookmarks();
}

function initTextSelection() {
    // 监听iframe内的文本选择
    window.addEventListener('message', (e) => {
        if (e.data.type === 'textSelected') {
            showBookmarkButton(e.data);
        } else if (e.data.type === 'selectionCleared') {
            hideBookmarkButton();
        }
    });
}

// ===== Iframe注入脚本（作为独立函数以获得语法检查）=====
function createIframeScript() {
    // 这个函数会被序列化后注入到iframe中
    // 防止重复注入
    if (window.__bookmarkScriptInjected) {
        return;
    }
    window.__bookmarkScriptInjected = true;
    
    let selectionTimeout;
    let lastMouseX = 0;
    let lastMouseY = 0;
    
    // ===== 链接拦截处理 =====
    // 拦截页面内的链接点击，修正跳转路径
    document.addEventListener('click', function(e) {
        // 查找最近的 <a> 标签
        const link = e.target.closest('a');
        if (!link) return;
        
        const href = link.getAttribute('href');
        if (!href) return;
        
        // 跳过锚点链接（仅#开头，不含路径）
        if (href.startsWith('#') && !href.includes('/')) {
            return; // 让页面内锚点跳转正常工作
        }
        
        // 跳过外部链接
        if (href.startsWith('http://') || href.startsWith('https://') || href.startsWith('//')) {
            return;
        }
        
        // 跳过 javascript: 和 mailto: 链接
        if (href.startsWith('javascript:') || href.startsWith('mailto:')) {
            return;
        }
        
        // 阻止默认行为
        e.preventDefault();
        e.stopPropagation();
        
        // 解析链接路径和锚点
        let targetPath = href;
        let anchor = '';
        
        const hashIndex = href.indexOf('#');
        if (hashIndex !== -1) {
            targetPath = href.substring(0, hashIndex);
            anchor = href.substring(hashIndex); // 包含 #
        }
        
        // 处理绝对路径（以 / 开头）
        if (targetPath.startsWith('/')) {
            targetPath = targetPath.substring(1); // 移除开头的 /
        }
        
        // 处理相对路径
        if (!targetPath.startsWith('/')) {
            // 获取当前页面路径
            const currentPath = window.location.pathname;
            const currentDir = currentPath.substring(0, currentPath.lastIndexOf('/') + 1);
            
            // 如果是相对路径，需要解析相对于当前目录
            if (targetPath.startsWith('./')) {
                targetPath = targetPath.substring(2);
            }
            
            // 处理 ../ 相对路径
            if (targetPath.startsWith('../')) {
                let basePath = currentDir;
                let relPath = targetPath;
                
                while (relPath.startsWith('../')) {
                    relPath = relPath.substring(3);
                    // 移除最后一个目录
                    basePath = basePath.substring(0, basePath.lastIndexOf('/', basePath.length - 2) + 1);
                }
                
                targetPath = basePath + relPath;
                // 移除开头的 /
                if (targetPath.startsWith('/')) {
                    targetPath = targetPath.substring(1);
                }
            } else if (!targetPath.includes('/') || targetPath.startsWith('./')) {
                // 同目录下的文件
                // 从当前路径提取目录部分（相对于content）
                // 当前iframe的src类似 content/xxx/yyy.html
                // 我们需要获取 xxx/ 部分
                const contentPrefix = 'content/';
                let idx = currentPath.indexOf(contentPrefix);
                if (idx !== -1) {
                    const afterContent = currentPath.substring(idx + contentPrefix.length);
                    const lastSlash = afterContent.lastIndexOf('/');
                    if (lastSlash !== -1) {
                        targetPath = afterContent.substring(0, lastSlash + 1) + targetPath;
                    }
                }
            }
        }
        
        // 确保路径不以 content/ 开头（稍后会添加）
        if (targetPath.startsWith('content/')) {
            targetPath = targetPath.substring(8);
        }
        
        // 构建完整的content路径
        const fullPath = 'content/' + targetPath;
        
        // 通知父页面加载新内容
        window.parent.postMessage({
            type: 'navigateToContent',
            path: fullPath,
            anchor: anchor
        }, '*');
    }, true); // 使用捕获阶段
    
    // 获取节点的XPath路径
    function getXPath(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            return getXPath(node.parentNode) + '/text()[' + (getTextNodeIndex(node) + 1) + ']';
        }
        if (node === document.body) {
            return '/html/body';
        }
        const siblings = Array.from(node.parentNode.children);
        const sameTagSiblings = siblings.filter(s => s.tagName === node.tagName);
        const index = sameTagSiblings.indexOf(node);
        const tagName = node.tagName.toLowerCase();
        const position = sameTagSiblings.length > 1 ? '[' + (index + 1) + ']' : '';
        return getXPath(node.parentNode) + '/' + tagName + position;
    }
    
    // 获取文本节点在父节点中的索引
    function getTextNodeIndex(textNode) {
        let index = 0;
        let node = textNode.parentNode.firstChild;
        while (node) {
            if (node === textNode) {
                return index;
            }
            if (node.nodeType === Node.TEXT_NODE) {
                index++;
            }
            node = node.nextSibling;
        }
        return index;
    }
    
    // 监听鼠标移动以记录位置
    document.addEventListener('mousemove', (e) => {
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
    });
    
    // 监听文本选择
    document.addEventListener('mouseup', (e) => {
        clearTimeout(selectionTimeout);
        selectionTimeout = setTimeout(() => {
            const selection = window.getSelection();
            const text = selection.toString().trim();
            if (text.length > 0 && selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                // 获取选择范围的起始和结束节点路径
                const startPath = getXPath(range.startContainer);
                const endPath = getXPath(range.endContainer);
                
                window.parent.postMessage({
                    type: 'textSelected',
                    text: text,
                    x: lastMouseX,
                    y: lastMouseY,
                    range: {
                        startPath: startPath,
                        startOffset: range.startOffset,
                        endPath: endPath,
                        endOffset: range.endOffset
                    }
                }, '*');
            } else {
                window.parent.postMessage({type: 'selectionCleared'}, '*');
            }
        }, 100);
    });
    
    // 监听滚动到书签的消息
    window.addEventListener('message', (e) => {
        if (e.data.type === 'scrollToBookmark') {
            scrollToBookmark(e.data.range);
        }
    });
    
    // 根据XPath获取节点
    function getNodeByXPath(xpath) {
        try {
            const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
            return result.singleNodeValue;
        } catch (e) {
            console.error('Failed to evaluate XPath:', xpath, e);
            return null;
        }
    }
    
    // 滚动到书签位置并高亮
    function scrollToBookmark(rangeData) {
        try {
            if (!rangeData || !rangeData.startPath) {
                console.error('Invalid range data:', rangeData);
                return;
            }
            
            // 根据XPath获取起始和结束节点
            const startNode = getNodeByXPath(rangeData.startPath);
            const endNode = getNodeByXPath(rangeData.endPath);
            
            if (!startNode || !endNode) {
                console.error('Failed to find nodes by XPath:', {
                    startPath: rangeData.startPath,
                    endPath: rangeData.endPath,
                    startNode: startNode,
                    endNode: endNode
                });
                return;
            }
            
            // 创建range对象
            const range = document.createRange();
            try {
                range.setStart(startNode, rangeData.startOffset);
                range.setEnd(endNode, rangeData.endOffset);
            } catch (e) {
                // 如果偏移量超出范围，使用节点的边界
                console.warn('Offset out of range, using node boundaries:', e);
                try {
                    range.selectNode(startNode.nodeType === Node.TEXT_NODE ? startNode.parentNode : startNode);
                } catch (e2) {
                    console.error('Failed to select node:', e2);
                    return;
                }
            }
            
            // 滚动到目标位置
            const rect = range.getBoundingClientRect();
            const scrollTop = window.scrollY + rect.top - window.innerHeight / 3;
            window.scrollTo({
                top: Math.max(0, scrollTop),
                behavior: 'smooth'
            });
            
            // 高亮显示
            highlightRange(range);
            console.log('Successfully scrolled to bookmark');
        } catch (e) {
            console.error('Failed to scroll to bookmark:', e);
        }
    }
    
    // 高亮显示range - 使用覆盖层方式
    function highlightRange(range) {
        try {
            // 获取选中区域的所有矩形（支持跨行选择）
            const rects = range.getClientRects();
            if (rects.length === 0) {
                // 如果getClientRects为空，使用getBoundingClientRect
                const rect = range.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    createHighlightOverlay([rect]);
                }
                return;
            }
            
            // 转换为数组并创建高亮覆盖层
            createHighlightOverlay(Array.from(rects));
        } catch (e) {
            console.error('Failed to highlight range:', e);
        }
    }
    
    // 创建高亮覆盖层
    function createHighlightOverlay(rects) {
        // 创建容器（如果不存在）
        let container = document.getElementById('__bookmark_highlight_container__');
        if (!container) {
            container = document.createElement('div');
            container.id = '__bookmark_highlight_container__';
            container.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 99999;';
            document.body.appendChild(container);
        }
        
        // 清除之前的高亮
        container.innerHTML = '';
        
        // 为每个矩形创建高亮块
        const highlights = [];
        rects.forEach((rect, index) => {
            // 过滤掉太小的矩形（可能是空白）
            if (rect.width < 2 || rect.height < 2) return;
            
            const highlight = document.createElement('div');
            highlight.className = '__bookmark_highlight_block__';
            highlight.style.cssText = `
                position: fixed;
                left: ${rect.left}px;
                top: ${rect.top}px;
                width: ${rect.width}px;
                height: ${rect.height}px;
                background-color: rgba(255, 235, 59, 0.2);
                border-radius: 2px;
                pointer-events: none;
                transition: opacity 0.5s ease;
                opacity: 1;
            `;
            container.appendChild(highlight);
            highlights.push(highlight);
        });
        
        // 动画：2秒后开始淡出
        setTimeout(() => {
            highlights.forEach(h => {
                h.style.opacity = '0';
            });
            // 淡出完成后移除
            setTimeout(() => {
                if (container && container.parentNode) {
                    container.innerHTML = '';
                }
            }, 500);
        }, 2000);
    }
}

function injectIframeScript() {
    try {
        const iframeDoc = elements.contentFrame.contentDocument || elements.contentFrame.contentWindow.document;
        if (!iframeDoc || !iframeDoc.body) {
            console.error('Iframe document not ready');
            return false;
        }
        
        // 检查是否已经注入过
        const iframeWin = elements.contentFrame.contentWindow;
        if (iframeWin.__bookmarkScriptInjected) {
            console.log('Script already injected, skipping');
            return true;
        }
        
        // 创建并注入脚本
        const script = iframeDoc.createElement('script');
        // 将函数转换为字符串并立即执行
        script.textContent = '(' + createIframeScript.toString() + ')()';
        iframeDoc.body.appendChild(script);
        
        console.log('Iframe script injected successfully');
        return true;
    } catch (e) {
        console.error('Failed to inject iframe script:', e);
        return false;
    }
}

let bookmarkButton = null;

function showBookmarkButton(data) {
    hideBookmarkButton();
    
    bookmarkButton = document.createElement('button');
    bookmarkButton.className = 'floating-bookmark-button';
    bookmarkButton.innerHTML = `
        <svg viewBox="0 0 24 24" width="16" height="16">
            <path fill="currentColor" d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/>
        </svg>
        收藏
    `;
    
    // 获取iframe的位置和滚动信息
    const frameRect = elements.contentFrame.getBoundingClientRect();
    // data.x和data.y是相对于iframe内容的，需要加上iframe的位置
    bookmarkButton.style.left = (frameRect.left + data.x) + 'px';
    // data.y是相对于可视区域的，不需要额外偏移，只需要相对于主窗口定位
    bookmarkButton.style.top = (frameRect.top + data.y - 40) + 'px';
    
    bookmarkButton.addEventListener('click', () => {
        // 使用文本的前20个字符作为书签标题
        const bookmarkTitle = data.text.length > 20 ? data.text.substring(0, 20) + '...' : data.text;
        addBookmark({
            type: 'text',
            path: state.currentPath,
            title: bookmarkTitle,
            text: data.text,
            range: data.range, // 保存DOM节点路径信息
            timestamp: Date.now()
        });
        hideBookmarkButton();
    });
    
    document.body.appendChild(bookmarkButton);
}

function hideBookmarkButton() {
    if (bookmarkButton) {
        bookmarkButton.remove();
        bookmarkButton = null;
    }
}

function addBookmark(bookmark) {
    // 检查是否已存在
    const exists = state.bookmarks.some(b => 
        b.path === bookmark.path && 
        b.type === bookmark.type && 
        (b.type === 'page' || b.text === bookmark.text)
    );
    
    if (exists) {
        alert('该书签已存在');
        return;
    }
    
    state.bookmarks.unshift(bookmark);
    localStorage.setItem('bookmarks', JSON.stringify(state.bookmarks));
    renderBookmarks();
}

function removeBookmark(index) {
    state.bookmarks.splice(index, 1);
    localStorage.setItem('bookmarks', JSON.stringify(state.bookmarks));
    renderBookmarks();
}

function renderBookmarks() {
    if (state.bookmarks.length === 0) {
        elements.bookmarksList.innerHTML = '<div class="bookmarks-empty">暂无书签</div>';
        return;
    }
    
    elements.bookmarksList.innerHTML = state.bookmarks.map((bookmark, index) => {
        const dateStr = new Date(bookmark.timestamp).toLocaleDateString('zh-CN');
        if (bookmark.type === 'page') {
            return `<div class="bookmark-item" data-index="${index}">
                <div class="bookmark-icon">📄</div>
                <div class="bookmark-content">
                    <div class="bookmark-title">${escapeHtml(bookmark.title)}</div>
                    <div class="bookmark-date">${dateStr}</div>
                </div>
                <button class="bookmark-delete" onclick="removeBookmark(${index})" title="删除">
                    <svg viewBox="0 0 24 24" width="14" height="14">
                        <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                    </svg>
                </button>
            </div>`;
        } else {
            // 文本书签：直接使用标题（已经是文本前20字符）作为主标题
            return `<div class="bookmark-item" data-index="${index}">
                <div class="bookmark-icon">✏️</div>
                <div class="bookmark-content">
                    <div class="bookmark-title">${escapeHtml(bookmark.title)}</div>
                    <div class="bookmark-date">${dateStr}</div>
                </div>
                <button class="bookmark-delete" onclick="removeBookmark(${index})" title="删除">
                    <svg viewBox="0 0 24 24" width="14" height="14">
                        <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                    </svg>
                </button>
            </div>`;
        }
    }).join('');
    
    // 绑定点击事件
    document.querySelectorAll('.bookmark-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.closest('.bookmark-delete')) return;
            const index = parseInt(item.getAttribute('data-index'));
            const bookmark = state.bookmarks[index];
            
            // 如果是文本书签，传递range数据给loadContent
            if (bookmark.type === 'text' && bookmark.range) {
                loadContent(bookmark.path, bookmark.range);
            } else {
                loadContent(bookmark.path);
            }
        });
    });
}

// ===== 导航处理 =====
function initNavigation() {
    const hash = window.location.hash.slice(1);
    if (hash) {
        // 解析 hash 中的路径和锚点
        // 格式可能是: content/path/file.html#anchor 或 content/path/file.html
        const parsed = parseHashWithAnchor(hash);
        loadContent(parsed.path, null, parsed.anchor);
    }
    
    window.addEventListener('popstate', (e) => {
        if (e.state && e.state.path) {
            loadContent(e.state.path, null, e.state.anchor || null);
        }
    });
    
    window.addEventListener('message', (e) => {
        if (e.data.type === 'pageLoaded') {
            syncThemeToIframe();
        } else if (e.data.type === 'requestTheme') {
            syncThemeToIframe();
        } else if (e.data.type === 'navigateToContent') {
            // 处理iframe内链接点击的导航请求
            loadContent(e.data.path, null, e.data.anchor || null);
        }
    });
}

/**
 * 解析带锚点的 hash
 * 输入: "content/path/file.html#anchor" 或 "content/path/file.html"
 * 输出: { path: "content/path/file.html", anchor: "#anchor" 或 null }
 */
function parseHashWithAnchor(hash) {
    // 先检查是否是 content/ 开头
    if (!hash.startsWith('content/')) {
        return { path: hash, anchor: null };
    }
    
    // 查找 .html# 或 .htm# 的位置（文件扩展名后的锚点）
    const htmlAnchorMatch = hash.match(/\.(html?)(#.*)$/i);
    if (htmlAnchorMatch) {
        const anchorIndex = hash.lastIndexOf('#');
        return {
            path: hash.substring(0, anchorIndex),
            anchor: hash.substring(anchorIndex)
        };
    }
    
    return { path: hash, anchor: null };
}

function syncThemeToIframe() {
    if (elements.contentFrame && elements.contentFrame.contentWindow) {
        elements.contentFrame.contentWindow.postMessage({
            type: 'themeChange', 
            theme: state.theme
        }, '*');
    }
}

// ===== 工具函数 =====
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ===== 移动端布局 =====
function initMobileLayout() {
    // 检测是否为移动端
    const isMobile = () => window.innerWidth <= 768;
    
    // 移动端默认收起侧边栏
    if (isMobile()) {
        elements.sidebar.classList.add('collapsed');
    }
    
    // 监听窗口大小变化
    window.addEventListener('resize', () => {
        if (isMobile() && !state.currentPath) {
            // 移动端且未加载内容时，收起侧边栏
            elements.sidebar.classList.add('collapsed');
        }
    });
}
