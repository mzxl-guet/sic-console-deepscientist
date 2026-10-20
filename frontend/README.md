# 信通智研台 · 前端皮肤工程

桂林电子科技大学 · 信息与通信学院 · 电子信息方向

把 DeepScientist 的本地网页改造成"自己的科研工作台"外观。**只换皮，不动功能**：
所有业务逻辑、数据、接口保持官方原样，出问题一条命令就能还原。

---

## 1. 一句话说清原理

DeepScientist 的网页是一份编译好的前端（`src/ui/dist`）。我们没有源码，所以不去改它，
而是在它外面套一层：

```
浏览器 → index.html（注入两行标签） → 官方 JS/CSS（原样不动，功能全在）
                                   ↘ brand.css（换配色、字体、底纹）
                                   ↘ brand.js （换文案、加装饰、改标题）
```

好处是：**官方代码一行没动**，升级/还原都简单；坏处是：**升级 DeepScientist 后要重新部署一次**。

---

## 2. 目录结构

```
my-ui/
├── brand.css        ← 主题样式（配色、字体、网格、按钮、水印都在这）
├── brand.js         ← 文案映射 + 学院标识 + 示波器动画
├── assets/          ← 图片素材（由脚本生成，可重新生成）
│   ├── logo.svg                 页头 logo（浅色版）
│   ├── logo-inverted.svg        页头 logo（深色版）
│   ├── logo-small.png           200px 图标
│   ├── hero-signal.png          主视觉：频谱山峦
│   ├── fog-cool.png             冷色水汽层
│   └── seal-sic.png             朱红印章「信通智研」
├── tools/
│   ├── gen_art.py    ← 生成主视觉 + 印章（需 D:\conda 的 numpy/PIL/scipy）
│   ├── gen_logo.py   ← 生成 logo 与 favicon
│   ├── shot.js       ← 无头浏览器截图（改设计时用来看效果）
│   ├── dom.js        ← 导出页面 DOM 结构
│   └── eval.js       ← 在页面里执行任意 JS
├── deploy.py        ← 部署（自动备份）
├── restore.py       ← 一键还原官方原版
└── _backup/         ← 官方原始文件备份（别删！）
```

---

## 3. 设计说明

### 3.1 色彩

| 变量 | 色值 | 用途 |
|---|---|---|
| `--sic-ink` | `#0A2338` | 主文字（深海军蓝，替代原来的暖黑） |
| `--sic-navy` | `#0B4A8F` | 主色（按钮、logo 主色） |
| `--sic-cyan` | `#00A9B5` | 信号青（强调、高亮、示波器波形） |
| `--sic-paper` | `#EDF3F9` | 页面底色（冷白，替代原来的米色纸张） |
| `--sic-muted` | `#4E6C86` | 弱化文字 |

原版是"米色纸张 + 土黄"的编辑风；这套改成"冷白蓝图 + 桂电蓝 + 信号青"的
仪器面板风，更适合电子信息专业的语境。

### 3.2 三个专业符号

1. **工程网格底纹** —— 铺在页面底层，像画在坐标纸上的实验记录。
2. **频谱山峦** —— 主视觉用桂林喀斯特山形做剪影，叠一条示波器波形和频谱柱；
   既是本地情感连接，也是"信号"的隐喻。
3. **示波器装饰** —— 主视觉右上方一块实时波形（HTML5 Canvas 绘制，`prefers-reduced-motion` 下自动隐藏）。

### 3.3 字体

把官方默认的思源宋体（`NotoSerifSC`，15 MB）换成了系统中文字体。
**中文首屏少下载约 15 MB**，观感也更"工科"。

---

## 4. 日常操作

```bat
:: 部署（改完 brand.css / brand.js 后跑一次）
python deploy.py

:: 还原成官方原版
python restore.py
```

部署完在浏览器按 **Ctrl + F5** 强制刷新即可看到效果。

> 用哪个 python？本机用 `C:\Users\18015\AppData\Local\Programs\Python\Python314\python.exe`，
> 只用到标准库，不需要装任何包。

---

## 5. 怎么改成你自己的

### 换配色
打开 `brand.css`，改文件顶部 `:root` 里的 6 个变量，整站跟着变。
比如把主色改成紫色：`--sic-navy: #5B3FA8;`

### 换文案
打开 `brand.js`，改 `MAP_ZH`（中文界面）和 `MAP_EN`（英文界面）两张表。
键是"界面原本显示的字"，值是"你想显示的字"。**键必须一字不差**，
改完记得把译文里出现的新词也加进表，否则第二次渲染会被漏掉。

### 换主视觉
改 `tools/gen_art.py` 里的 `layers`（层数、峰高、颜色）和波形参数，然后：

```bat
D:\conda\python.exe tools\gen_art.py
python deploy.py
```

### 换 logo
改 `tools/gen_logo.py` 里的 `CHIP`（外框）、`WAVE_*`（波形）参数，然后：

```bat
D:\conda\python.exe tools\gen_logo.py
python deploy.py
```

---

## 6. 需要注意

1. **升级 DeepScientist 会覆盖皮肤**。升级后重跑 `python deploy.py` 即可；
   如果新版前端结构变了，可能需要同步更新 `brand.css` 里的选择器。
2. `_backup/` 是官方原版文件，**不要删**，否则 `restore.py` 失效。
3. 文案替换依赖"界面原文完全一致"。官方改文案后，对应条目会失效（不会报错，
   只是那一条不生效），按第 5 节重新对一下即可。
4. 皮肤只改视觉层，不涉及数据与接口，`restore.py` 之后功能与官方完全一致。

---

## 7. 验证记录（2026-10-17）

| 检查项 | 结果 |
|---|---|
| 中文首页 | 标题、大标题、副标题、按钮、页脚全部替换 |
| 英文首页 | `New Study` / `Quest Library` / `Baseline…Converged` 全部替换 |
| 新建研究弹窗 | 暖色卡片已转冷色，按钮为品牌蓝 |
| 窄屏 820px | 布局正常，装饰层自动隐藏 |
| 还原脚本 | `_backup/` 内 11 个原版文件齐全 |
