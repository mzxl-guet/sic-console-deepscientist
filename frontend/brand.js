/* ==========================================================================
   信通智研台 · 品牌注入脚本
   职责：
     1. 修改浏览器标签页标题
     2. 顶栏加"信息与通信学院"标识
     3. 主视觉区叠加示波器波形装饰（纯装饰，不影响交互）
     4. 按当前界面语言，把文案换成本项目的话术（中英各一套）
   原则：只改文本与装饰，不碰任何业务逻辑；所有步骤出错都静默，保证页面可用。
   ========================================================================== */
(function () {
  'use strict';

  var BRAND = '信通智研台';
  var DOC_TITLE = '信通智研台 · 桂电信息与通信学院';

  /* --------------------- 英文界面 → 本项目的英文话术 --------------------- */
  var MAP_EN = {
    'DeepScientist': 'SIC Console',
    'Automated Research': 'Information & Communication',
    'AUTOMATED RESEARCH': 'INFORMATION & COMMUNICATION',
    'Automated scientific discovery, driven by autonomous AI research':
      'Signal in, insight out — a research console for electronic information',
    'SURVEY · EXPERIMENT · PUBLISH': 'MODEL · SIMULATE · MEASURE',
    'Start Research': 'New Study',
    'List Quests': 'Quest Library',
    'DeepScientist keeps your full research loop local, reproducible, and continuously moving.':
      'Local-first, reproducible, and traceable from question to validation.',
    'More content at': 'Built on the open-source project',
    'https://deepscientist.cc': 'DeepScientist',
    'DeepScientist v1.5.17': 'SIC Console v1.5.17 · Electronic Information',
    'Exploring Unknown Scientific Frontiers':
      'SIGNAL · CHANNEL · SPECTRUM · INTELLIGENCE',
    'EXPLORING UNKNOWN SCIENTIFIC FRONTIERS':
      'SIGNAL · CHANNEL · SPECTRUM · INTELLIGENCE',
    'LOCAL OPTIMUM': 'BASELINE',
    'MIDPOINT': 'ABLATION',
    'GLOBAL OPTIMUM': 'OPTIMUM',
    'Local Optimum': 'Baseline',
    'Learn & Adapt': 'Param Sweep',
    'Escape Local': 'Escape Local',
    'Global Optimum': 'Converged',
    'Scroll to explore': 'Scroll to enter the console'
  };

  /* --------------------- 中文界面 → 本项目的中文话术 --------------------- */
  var MAP_ZH = {
    'DeepScientist': BRAND,
    'DeepScientist v1.5.17': 'v1.5.17 · 电子信息方向',
    'Exploring Unknown Scientific Frontiers': '探索未知的科学前沿',
    'EXPLORING UNKNOWN SCIENTIFIC FRONTIERS': '探索未知的科学前沿',
    'Local optimum': '基线结果',
    'Midpoint': '参数扫描',
    'Global optimum': '收敛最优',
    'SURVEY · EXPERIMENT · PUBLISH': '建模 · 仿真 · 实测',
    '自动化科研': '信息与通信 · 智能科研',
    '由自治 AI 研究驱动的自动化科学发现':
      '由信号到洞见：面向电子信息的自主科研工作台',
    '调研 · 实验 · 发表': '建模 · 仿真 · 实测',
    '查看 Quest': '课题库',
    'DeepScientist 让完整研究闭环保持本地、可复现，并持续推进。':
      '信通智研台 · 本地运行、可复现，从选题到验证一路留痕。',
    '更多内容见': '基于开源项目',
    'https://deepscientist.cc': 'DeepScientist',
    '局部最优': '基线结果',
    '学习与调整': '参数扫描',
    '全局最优': '收敛最优',
    '滚动继续探索': '向下滚动 · 进入工作台',
    '无论哪种，DeepScientist 都会在你身边。': '无论哪种方式，信通智研台都陪着你推进。'
  };

  /* 这些是功能开关的文案，禁止替换 */
  var SKIP = ['中文', 'English', 'Tutorial', 'Docs', 'Settings', '教程', '文档', '设置'];

  /* 判断当前界面语言：语言按钮上写着 "English" 说明现在是中文界面 */
  function currentMap() {
    var btns = document.querySelectorAll('header button, header a');
    for (var i = 0; i < btns.length; i++) {
      var t = (btns[i].textContent || '').replace(/\s+/g, ' ').trim();
      if (t === 'English') return MAP_ZH;
      if (t === '中文') return MAP_EN;
    }
    return MAP_ZH;
  }

  var MAP = MAP_ZH;

  function translateNode(node) {
    var raw = node.nodeValue;
    if (!raw) return;
    if (node.__sicLast === raw) return;   // 这条正是我们自己写的，跳过
    // React 有时会渲染不间断空格，统一成普通空格再匹配
    var key = raw.replace(/\u00a0/g, ' ').replace(/\s+/g, ' ').trim();
    if (!key) return;
    if (SKIP.indexOf(key) !== -1) return;
    if (!Object.prototype.hasOwnProperty.call(MAP, key)) return;
    var out = raw.replace(raw.trim(), MAP[key]);
    if (out === raw) return;
    node.nodeValue = out;
    node.__sicLast = out;
  }

  function translateTree(root) {
    if (!root) return;
    try {
      var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
      var batch = [];
      var n;
      while ((n = walker.nextNode())) batch.push(n);
      batch.forEach(translateNode);
    } catch (e) { /* 静默 */ }
  }

  /* ---------------------------- 标题 ---------------------------- */
  function fixTitle() {
    if (document.title !== DOC_TITLE) document.title = DOC_TITLE;
  }

  /* ------------------------- 顶栏学院标识 ------------------------- */
  function addBrandTag() {
    if (document.getElementById('sic-brand-tag')) return;
    var link = document.querySelector('header a[href="/"]');
    if (!link) return;
    var tag = document.createElement('span');
    tag.id = 'sic-brand-tag';
    tag.textContent = '信息与通信学院';
    link.appendChild(tag);
  }

  /* ---------------------- 示波器波形装饰层 ---------------------- */
  function addScope() {
    if (document.getElementById('sic-scope')) return;
    var section = document.querySelector('section.relative.min-h-\\[100svh\\]')
      || document.querySelector('section');
    if (!section) return;

    var cvs = document.createElement('canvas');
    cvs.id = 'sic-scope';
    cvs.setAttribute('aria-hidden', 'true');
    section.appendChild(cvs);          // 挂在末尾，避免打乱框架的子节点顺序

    var ctx = cvs.getContext('2d');
    if (!ctx) return;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var W = 0, H = 0;

    function resize() {
      var r = cvs.getBoundingClientRect();
      W = Math.max(1, Math.round(r.width));
      H = Math.max(1, Math.round(r.height));
      cvs.width = W * dpr;
      cvs.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    window.addEventListener('resize', resize);

    var t0 = performance.now();
    var raf = null;

    function frame(now) {
      var t = (now - t0) / 1000;
      var mid = H * 0.52;
      ctx.clearRect(0, 0, W, H);

      ctx.font = '600 10px "DS-Inter", "Microsoft YaHei UI", sans-serif';
      ctx.fillStyle = 'rgba(11,74,143,0.40)';
      ctx.fillText('CH1  ·  SIG', 14, 18);
      ctx.fillStyle = 'rgba(0,169,181,0.45)';
      ctx.fillText('CH2  ·  REF', 14, 34);

      ctx.strokeStyle = 'rgba(11,74,143,0.09)';
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 6]);
      for (var g = 1; g <= 3; g++) {
        var gy = (H * g) / 4;
        ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(W, gy); ctx.stroke();
      }
      ctx.setLineDash([]);

      function trace(phase, amp, fA, fB, color, width, alpha) {
        ctx.beginPath();
        for (var x = 0; x <= W; x += 2) {
          var p = x / W;
          var env = 0.55 + 0.45 * Math.sin(p * Math.PI * 1.2 + t * 0.35 + phase);
          var y = mid
            + Math.sin(p * fA + t * 1.1 + phase) * amp * env
            + Math.sin(p * fB + t * 0.6 + phase * 2) * amp * 0.28 * env;
          if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.globalAlpha = alpha;
        ctx.strokeStyle = color;
        ctx.lineWidth = width;
        ctx.shadowColor = color;
        ctx.shadowBlur = 8;
        ctx.stroke();
        ctx.shadowBlur = 0;
        ctx.globalAlpha = 1;
      }

      trace(0, H * 0.20, 9.0, 21.0, 'rgba(11,74,143,0.55)', 1.6, 0.75);
      trace(1.7, H * 0.12, 13.0, 27.0, 'rgba(0,169,181,0.75)', 1.1, 0.5);

      if (!document.hidden) raf = requestAnimationFrame(frame);
    }

    raf = requestAnimationFrame(frame);
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden && !raf) raf = requestAnimationFrame(frame);
      if (document.hidden) { cancelAnimationFrame(raf); raf = null; }
    });
  }

  /* ---------------------------- 启动 ---------------------------- */
  function boot() {
    try { MAP = currentMap(); } catch (e) { MAP = MAP_ZH; }
    try { fixTitle(); } catch (e) {}
    try { translateTree(document.body); } catch (e) {}
    try { addBrandTag(); } catch (e) {}
    try { addScope(); } catch (e) {}
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  // React 渲染晚于首屏，用 MutationObserver 兜住后续变化
  try {
    var mo = new MutationObserver(function (records) {
      for (var i = 0; i < records.length; i++) {
        var r = records[i];
        if (r.type === 'childList') {
          for (var j = 0; j < r.addedNodes.length; j++) {
            var node = r.addedNodes[j];
            if (node.nodeType === 3) translateNode(node);
            else if (node.nodeType === 1) translateTree(node);
          }
          addBrandTag();
        } else if (r.type === 'characterData') {
          translateNode(r.target);
        }
      }
      fixTitle();
    });
    mo.observe(document.documentElement, {
      childList: true,
      subtree: true,
      characterData: true
    });
  } catch (e) {}

  // 切换语言后立即补扫，避免用户看到语言残留
  document.addEventListener('click', function (e) {
    var el = e.target;
    if (!el || !el.closest) return;
    var btn = el.closest('button, a');
    if (!btn) return;
    var t = (btn.textContent || '').replace(/\s+/g, ' ').trim();
    if (t === '中文' || t === 'English') {
      [120, 400, 900, 1600, 2600].forEach(function (d) { setTimeout(boot, d); });
    }
  }, true);

  // 首页有动画会反复重渲染，被覆盖的文案要持续补扫；
  // 其它页面（长会话）不扫，避免性能负担。
  var timer = setInterval(function () {
    if (!document.querySelector('section.relative.min-h-\\[100svh\\]')) return;
    boot();
  }, 1200);
})();
