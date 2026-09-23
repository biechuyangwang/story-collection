/* 故事集前端：hash 路由 + 分类浏览 + 搜索 + 夜读模式 + 网页朗读 */
(function () {
  "use strict";

  var DATA = null;
  var app = document.getElementById("app");
  var searchBox = document.getElementById("search-box");
  var themeBtn = document.getElementById("theme-btn");
  var speaking = null;
  var pendingAutoPlay = false; // 连播：跨页待自动播放标志（hash SPA 不刷新页面，模块级变量即可传递）

  /* ---------- 主题 ---------- */
  function applyTheme() {
    var saved = localStorage.getItem("theme");
    var night = saved === "night" ||
      (!saved && window.matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.dataset.theme = night ? "night" : "day";
    themeBtn.textContent = night ? "☀️" : "🌙";
  }
  themeBtn.addEventListener("click", function () {
    var night = document.documentElement.dataset.theme === "night";
    localStorage.setItem("theme", night ? "day" : "night");
    applyTheme();
  });
  applyTheme();

  /* ---------- 工具 ---------- */
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function md(text) {
    if (window.marked) return marked.parse(text);
    // 极简兜底渲染
    return esc(text)
      .split(/\n{2,}/).map(function (p) {
        p = p.trim();
        if (!p) return "";
        if (/^#{2,}\s/.test(p)) return "<h2>" + p.replace(/^#{2,}\s*/, "") + "</h2>";
        return "<p>" + p.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>") + "</p>";
      }).join("");
  }
  function chips(meta) {
    return Object.keys(meta).map(function (k) {
      return '<span class="chip"><b>' + esc(k) + '</b>　' + esc(meta[k]) + "</span>";
    }).join("");
  }
  function stopSpeak() {
    if (window.speechSynthesis) { window.speechSynthesis.cancel(); speaking = null; }
  }
  function speak(story, btn) {
    if (!window.speechSynthesis) { btn.textContent = "浏览器不支持朗读"; return; }
    if (speaking === story.id) { stopSpeak(); btn.textContent = "▶ 朗读这篇"; return; }
    stopSpeak();
    var u = new SpeechSynthesisUtterance(story.title + "。" + (story._plain || ""));
    u.lang = "zh-CN"; u.rate = 0.85;
    u.onend = function () { speaking = null; btn.textContent = "▶ 朗读这篇"; };
    speaking = story.id;
    btn.textContent = "⏸ 停止朗读";
    window.speechSynthesis.speak(u);
  }

  /* ---------- 数据 ---------- */
  fetch("docs/data.json").then(function (r) { return r.json(); }).then(function (d) {
    DATA = d;
    document.getElementById("foot-meta").textContent = "共 " + d.total + " 篇 · 更新于 " + d.generatedAt;
    route();
  });

  function byId(id) {
    for (var i = 0; i < DATA.stories.length; i++)
      if (DATA.stories[i].id === id) return DATA.stories[i];
    return null;
  }

  /* ---------- 路由 ---------- */
  function route() {
    stopSpeak();
    var h = location.hash.replace(/^#\/?/, "");
    if (!h) return renderHome();
    var parts = h.split("/").map(decodeURIComponent);
    if (parts[0] === "cat" && parts[1]) return renderCategory(parts[1]);
    if (parts[0] === "s" && parts[1]) return renderStory(parts.slice(1).join("/"));
    if (parts[0] === "search") return renderSearch(parts.slice(1).join("/"));
    renderHome();
  }
  window.addEventListener("hashchange", route);

  /* ---------- 首页 ---------- */
  function renderHome() {
    document.title = "故事集 · 寓言 · 神话 · 童话 · 电台";
    function catCards(cats) {
      return cats.map(function (c) {
        var n = DATA.stories.filter(function (s) { return s.cat === c.id; }).length;
        return '<a class="cat-card" href="#/cat/' + encodeURIComponent(c.id) + '">' +
          '<span class="icon">' + c.icon + "</span><h3>" + esc(c.name) + "</h3>" +
          "<p>" + esc(c.desc) + "</p>" +
          '<span class="count">' + n + " 篇</span></a>";
      }).join("");
    }
    var kidCats = DATA.categories.filter(function (c) { return c.zone !== "adult"; });
    var adultCats = DATA.categories.filter(function (c) { return c.zone === "adult"; });
    var adultSection = adultCats.length
      ? '<section class="adult-zone"><h2 class="section-title">🛋️ 成年人专区</h2>' +
        '<p class="section-desc">给大人自己的内容：更深的书、更远的历史、更静的夜。</p>' +
        '<div class="cat-grid">' + catCards(adultCats) + "</div></section>"
      : "";
    app.innerHTML =
      '<section class="hero">' +
      '<span class="moon">🌙</span><h1>今晚想听点什么？</h1>' +
      "<p>寓言 · 神话 · 童话 · 成语 · 励志 · 反转 · 电台 · 节日，都在这里。</p>" +
      '<div class="stat-row"><span><b>' + DATA.total + "</b> 篇故事</span>" +
      "<span><b>3~5</b> 分钟一篇</span><span><b>8</b> 大分类</span></div>" +
      '<div class="quick-entries">' +
      '<a href="#/cat/' + encodeURIComponent("睡前故事") + '">🌙 睡前读一篇</a>' +
      '<a href="#/cat/' + encodeURIComponent("电台故事") + '">🎧 深夜电台</a>' +
      '<a href="#/cat/' + encodeURIComponent("节日故事") + '">🎉 节日应景</a>' +
      "</div></section>" +
      '<section class="cat-grid">' + catCards(kidCats) + "</section>" +
      adultSection;
  }

  /* ---------- 分类页 ---------- */
  function storyLink(s) {
    return "#/s/" + s.id.split("/").map(encodeURIComponent).join("/");
  }
  /* ---------- 睡前连播 ---------- */
  function autoNextOn() {
    return localStorage.getItem("autoplay-next") === "1";
  }
  // 从当前篇往后找同分类下一篇有配音的（跳过无配音的；到分类末尾返回 null，不循环）
  function nextPlayable(s) {
    var list = DATA.stories.filter(function (x) { return x.cat === s.cat; });
    var i = list.indexOf(s);
    for (var j = i + 1; j < list.length; j++)
      if (list[j].audio || list[j].audio_m) return list[j];
    return null;
  }
  function renderCategory(cid) {
    var cat = DATA.categories.filter(function (c) { return c.id === cid; })[0];
    if (!cat) return renderHome();
    document.title = cat.name + " · 故事集";
    var list = DATA.stories.filter(function (s) { return s.cat === cid; });

    function items(stories) {
      return '<div class="story-list">' + stories.map(function (s) {
        var mi = [s.meta["适读年龄"], s.meta["朗读时长"] || s.meta["时长"], s.meta["出处"] || s.meta["主题"] || s.meta["成语出处"]]
          .filter(Boolean).join("　·　");
        return '<a class="story-item" href="' + storyLink(s) + '">' +
          '<div class="t"><span class="num">' + esc(s.num) + "</span>" + esc(s.title) +
          (s.audio ? ' <span class="audio-flag" title="有真人配音">🎧</span>' : "") + "</div>" +
          (mi ? '<div class="m">' + esc(mi) + "</div>" : "") +
          '<div class="e">' + esc(s.excerpt) + "</div></a>";
      }).join("") + "</div>";
    }

    var html = '<p class="crumb"><a href="#/">首页</a> / ' + esc(cat.name) + "</p>" +
      '<h2 class="section-title">' + cat.icon + " " + esc(cat.name) + "</h2>" +
      '<p class="section-desc">' + esc(cat.desc) + "</p>";

    if (cat.subs && cat.subs.length) {
      html += cat.subs.map(function (sub) {
        var subList = list.filter(function (s) { return s.sub === sub; });
        if (!subList.length) return "";
        return '<h3 class="sub-head">「 ' + esc(sub) + " 」</h3>" + items(subList);
      }).join("");
    } else {
      html += items(list);
    }
    app.innerHTML = html;
    window.scrollTo(0, 0);
  }

  /* ---------- 故事页 ---------- */
  function renderStory(sid) {
    var s = byId(sid);
    if (!s) return renderHome();
    document.title = s.title + " · 故事集";
    var list = DATA.stories.filter(function (x) { return x.cat === s.cat; });
    var i = list.indexOf(s);
    var prev = list[i - 1], next = list[i + 1];

    var fontBtns =
      '<button class="tool-btn" id="fs-dec">A−</button>' +
      '<button class="tool-btn" id="fs-inc">A+</button>' +
      (s.audio ? "" : '<button class="tool-btn" id="tts-btn">▶ 朗读这篇</button>');
    var audioBox = "";
    if (s.audio || s.audio_m) {
      var hasF = !!s.audio, hasM = !!s.audio_m;
      // 沿用本会话上次选中的声线版本（连播跨页时继续用同一种声音）
      var startM = hasM && sessionStorage.getItem("audio-ver") === "m";
      var tabs = "";
      if (hasF && hasM) {
        tabs = '<div class="ver-tabs">' +
          '<button class="ver-btn' + (startM ? "" : " active") + '" data-src="' + encodeURI(s.audio) + '">♀ 女声版</button>' +
          '<button class="ver-btn' + (startM ? " active" : "") + '" data-src="' + encodeURI(s.audio_m) + '">♂ 男声版</button></div>';
      }
      var src = startM ? s.audio_m : (hasF ? s.audio : s.audio_m);
      audioBox = '<div class="audio-box"><span class="audio-tag">🎧 有声朗读</span>' +
        tabs + '<audio controls preload="none" id="story-audio" src="' +
        encodeURI(src) + '"></audio>' +
        '<button class="ver-btn auto-next' + (autoNextOn() ? " active" : "") +
        '" id="auto-next-btn" title="睡前连播：本篇播完后，自动播放同分类下一篇（有配音的）">🌙 连播 ' +
        (autoNextOn() ? "开" : "关") + "</button></div>";
    }

    app.innerHTML =
      '<p class="crumb"><a href="#/">首页</a> / <a href="#/cat/' + encodeURIComponent(s.cat) + '">' +
      esc(s.cat) + "</a>" + (s.sub ? " / " + esc(s.sub) : "") + "</p>" +
      '<div class="story-head"><h1>' + esc(s.title) + "</h1>" +
      '<div class="meta-chips">' + chips(s.meta) + "</div></div>" +
      '<div class="story-tools">' + fontBtns + "</div>" +
      audioBox +
      '<article class="content"><p class="section-desc">正文加载中…</p></article>' +
      '<div class="story-nav">' +
      (prev ? '<a href="' + storyLink(prev) + '">← ' + esc(prev.title) + "</a>" : "<span></span>") +
      (next ? '<a href="' + storyLink(next) + '">' + esc(next.title) + " →</a>" : "<span></span>") +
      "</div>";

    // 正文按需加载：列表页秒开，进文章页再取单篇 JSON（含正文/结尾/小启示）
    fetch("docs/story/" + encodeURI(sid) + ".json")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!app.querySelector(".content")) return; // 用户已切走
        app.querySelector(".content").innerHTML = md(d.content) +
          (d.ending
            ? '<div class="ending-block"><span class="label">『 ' + esc(d.endingLabel) + ' 』</span><p>' +
              esc(d.ending) + "</p></div>"
            : "") +
          (d.card ? '<div class="card-block">' + esc(d.card.replace(/^> /gm, "")) + "</div>" : "");
        s._plain = d.plain;
        var ttsBtn = app.querySelector("#tts-btn");
        if (ttsBtn) ttsBtn.onclick = function () { speak(s, this); };
      })
      .catch(function () {
        if (app.querySelector(".content"))
          app.querySelector(".content").innerHTML = '<p class="section-desc">正文加载失败，请刷新重试。</p>';
      });

    var fs = +(localStorage.getItem("fs") || 18);
    var contentEl = app.querySelector(".content");
    function setFs(v) {
      fs = Math.min(26, Math.max(14, v));
      localStorage.setItem("fs", fs);
      contentEl.style.setProperty("--fs", fs + "px");
    }
    setFs(fs);
    app.querySelector("#fs-inc").onclick = function () { setFs(fs + 2); };
    app.querySelector("#fs-dec").onclick = function () { setFs(fs - 2); };
    // tts-btn 在正文 fetch 完成后绑定（需要 plain 全文）
    app.querySelectorAll(".ver-tabs .ver-btn").forEach(function (b) {
      b.onclick = function () {
        app.querySelectorAll(".ver-tabs .ver-btn").forEach(function (x) { x.classList.remove("active"); });
        b.classList.add("active");
        var player = app.querySelector("#story-audio");
        if (player) { player.pause(); player.src = b.dataset.src; }
        // 记住声线偏好，连播跨页沿用（f=女声 m=男声）
        sessionStorage.setItem("audio-ver", b.dataset.src === encodeURI(s.audio) ? "f" : "m");
      };
    });
    /* ---------- 睡前连播 ---------- */
    var autoBtn = app.querySelector("#auto-next-btn");
    if (autoBtn) {
      autoBtn.onclick = function () {
        var on = !autoNextOn();
        localStorage.setItem("autoplay-next", on ? "1" : "0");
        this.classList.toggle("active", on);
        this.textContent = on ? "🌙 连播 开" : "🌙 连播 关";
      };
    }
    var player = app.querySelector("#story-audio");
    if (player) {
      player.addEventListener("ended", function () {
        if (!autoNextOn()) return;
        var nx = nextPlayable(s);
        if (!nx) return; // 已是分类末尾：停止，不循环
        pendingAutoPlay = true;
        location.hash = storyLink(nx);
      });
      // 上一页播完自动跳过来：恢复声线版本后自动播放
      if (pendingAutoPlay) {
        pendingAutoPlay = false;
        var pr = player.play();
        if (pr && typeof pr.catch === "function") {
          pr.catch(function (err) {
            console.warn("[连播] 浏览器拦截了自动播放，本篇请手动点播放：", err);
          });
        }
      }
    }
    window.scrollTo(0, 0);
  }

  /* ---------- 搜索 ---------- */
  // 全文索引单独成文件，首次搜索时才加载；加载完成前先用标题/摘要顶上
  var searchIndex = null, searchIndexLoading = false;
  function renderSearch(q) {
    q = (q || "").trim();
    document.title = "搜索：" + q + " · 故事集";
    var res, note = "";
    if (searchIndex) {
      res = q
        ? searchIndex.filter(function (row) { return row.t.indexOf(q) > -1; })
            .map(function (row) { return byId(row.id); }).filter(Boolean)
        : [];
    } else {
      res = q
        ? DATA.stories.filter(function (s) {
            return (s.title + s.excerpt +
              Object.keys(s.meta).map(function (k) { return s.meta[k]; }).join("")).indexOf(q) > -1;
          })
        : [];
      note = '<p class="section-desc" style="color:var(--ink-soft)">正在加载全文索引…加载完成后会自动补全正文匹配的结果</p>';
      if (!searchIndexLoading) {
        searchIndexLoading = true;
        fetch("docs/search.json")
          .then(function (r) { return r.json(); })
          .then(function (idx) { searchIndex = idx; searchIndexLoading = false; renderSearch(q); })
          .catch(function () { searchIndexLoading = false; });
      }
    }
    app.innerHTML =
      '<p class="crumb"><a href="#/">首页</a> / 搜索</p>' +
      '<h2 class="section-title">🔍 “' + esc(q) + "”</h2>" +
      '<p class="section-desc">找到 ' + res.length + " 篇</p>" + note +
      (res.length
        ? '<div class="story-list">' + res.map(function (s) {
            return '<a class="story-item" href="' + storyLink(s) + '">' +
              '<div class="t"><span class="num">' + esc(s.cat) + "</span>" + esc(s.title) + "</div>" +
              '<div class="e">' + esc(s.excerpt) + "</div></a>";
          }).join("") + "</div>"
        : "<p style='color:var(--ink-soft)'>换个词试试？比如：月亮、坚持、狐狸。</p>");
  }

  searchBox.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && searchBox.value.trim()) {
      location.hash = "#/search/" + encodeURIComponent(searchBox.value.trim());
      searchBox.blur();
    }
  });
})();
