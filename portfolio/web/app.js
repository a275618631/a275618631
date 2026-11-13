(() => {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const list = byId("project-list");
  const detail = byId("detail");
  const search = byId("search");
  const category = byId("category");
  const tag = byId("tag");
  const featured = byId("featured");
  const count = byId("result-count");
  let projects = [];
  let categories = [];

  const text = (tagName, value, className) => {
    const node = document.createElement(tagName);
    if (className) node.className = className;
    node.textContent = value == null ? "" : String(value);
    return node;
  };

  function safeExternalLink(link) {
    if (!link.url || link.status === "expired") return null;
    const node = document.createElement("a");
    const state = link.kind === "local_http" ? "（未檢查）" : link.status === "unverified" || link.status === "manual" ? "（尚未驗證）" : "";
    node.textContent = `${link.label}${state}`;
    node.href = link.url;
    node.rel = "noopener noreferrer";
    node.target = "_blank";
    return node;
  }

  function renderCategories() {
    const previous = category.value;
    category.replaceChildren(new Option("全部分類", ""));
    for (const value of categories) category.add(new Option(value, value));
    category.value = categories.includes(previous) ? previous : "";
    const tags = [...new Set(projects.flatMap((p) => p.tags || []))].sort((a, b) => a.localeCompare(b, "zh-Hant"));
    tag.replaceChildren(new Option("全部標籤", ""));
    for (const value of tags) tag.add(new Option(value, value));
  }

  function makeCard(project) {
    const article = document.createElement("article");
    article.className = "project-card";
    article.dataset.projectId = project.project_id;
    article.append(text("p", (project.categories || []).join(" · "), "eyebrow"));
    const heading = document.createElement("h2");
    const titleLink = document.createElement("a");
    titleLink.href = `#/projects/${encodeURIComponent(project.project_id)}`;
    titleLink.textContent = project.title;
    heading.append(titleLink);
    article.append(heading, text("p", project.summary));
    const features = document.createElement("ul");
    features.className = "feature-list";
    for (const feature of project.capabilities || []) {
      const item = document.createElement("li");
      item.append(text("span", feature.title), text("span", feature.status, "state"));
      features.append(item);
    }
    article.append(features);
    article.append(text("p", `證據：${project.evidence?.status || "unverified"} · 版本：${project.snapshot?.revision || "未發布"}`, "evidence"));
    const nav = document.createElement("nav");
    nav.setAttribute("aria-label", `${project.title} 的作品連結`);
    for (const link of project.links || []) {
      const anchor = safeExternalLink(link);
      if (anchor) nav.append(anchor);
    }
    if (!nav.childElementCount) nav.append(text("span", "請查看作品說明", "quiet"));
    article.append(nav);
    return article;
  }

  function renderList() {
    const query = search.value.trim().toLocaleLowerCase();
    const selectedCategory = category.value;
    const selectedTag = tag.value;
    const visible = projects.filter((project) => {
      if (featured.checked && !project.featured) return false;
      if (selectedCategory && !(project.categories || []).includes(selectedCategory)) return false;
      if (selectedTag && !(project.tags || []).includes(selectedTag)) return false;
      const haystack = [project.title, project.summary, ...(project.tags || []), ...(project.categories || []), ...(project.capabilities || []).flatMap((f) => [f.title, f.description, f.status])]
        .join(" ").toLocaleLowerCase();
      return !query || haystack.includes(query);
    });
    list.replaceChildren(...visible.map(makeCard));
    count.textContent = `顯示 ${visible.length} 件作品`;
  }

  function renderDetail() {
    const match = location.hash.match(/^#\/projects\/([a-z0-9]+(?:-[a-z0-9]+)*)$/);
    if (!match) {
      detail.hidden = true;
      list.hidden = false;
      return;
    }
    const project = projects.find((p) => p.project_id === match[1]);
    list.hidden = true;
    detail.hidden = false;
    detail.replaceChildren();
    const back = document.createElement("a");
    back.href = "#/";
    back.className = "back-link";
    back.textContent = "← 返回所有作品";
    detail.append(back);
    if (!project) {
      detail.append(text("h2", "找不到這件作品"), text("p", "作品識別碼不存在或已變更。"));
      return;
    }
    detail.append(text("p", (project.categories || []).join(" · "), "eyebrow"), text("h2", project.title), text("p", project.summary));
    detail.append(text("p", `展示版本：${project.snapshot?.revision || "未發布"} · 查核日期：${project.snapshot?.reviewed_at || "尚未查核"}`, "evidence"));
    detail.append(text("p", `證據狀態：${project.evidence?.status || "unverified"}。${project.evidence?.scope || "尚未記錄查核範圍。"}`, "evidence"));
    const capabilities = document.createElement("section");
    capabilities.append(text("h3", "功能範圍"));
    const items = document.createElement("ul");
    items.className = "feature-list detail-features";
    for (const feature of project.capabilities || []) {
      const item = document.createElement("li");
      item.append(text("strong", `${feature.title} · ${feature.status}`), text("span", feature.description));
      items.append(item);
    }
    capabilities.append(items);
    detail.append(capabilities);
    const linksSection = document.createElement("section");
    linksSection.append(text("h3", "作品與 Demo 入口"));
    const links = document.createElement("nav");
    links.setAttribute("aria-label", `${project.title} 的作品連結`);
    for (const link of project.links || []) {
      const anchor = safeExternalLink(link);
      if (anchor) links.append(anchor);
      else links.append(text("span", `${link.label}：${link.status === "expired" ? "已過期" : "未設定，尚未檢查"}`, "quiet"));
    }
    if (!links.childElementCount) links.append(text("p", "目前沒有已設定的 Demo；程式與文件仍可查閱。", "quiet"));
    linksSection.append(links);
    detail.append(linksSection);
    if (project.lifecycle === "archived") detail.append(text("p", "此作品已封存；保留歷史版本與識別碼。", "notice"));
  }

  async function start() {
    try {
      const response = await fetch(new URL("projects.json", document.baseURI), { cache: "no-store", credentials: "omit" });
      if (!response.ok) throw new Error("manifest unavailable");
      const data = await response.json();
      if (!Array.isArray(data.projects)) throw new Error("invalid manifest");
      projects = data.projects;
      categories = data.categories || [...new Set(projects.flatMap((p) => p.categories || []))];
      renderCategories();
      renderList();
      renderDetail();
      byId("enhancement-status").textContent = "搜尋、分類與作品詳情已啟用。";
    } catch (_error) {
      // Keep the build-time HTML fallback readable when JavaScript data loading is unavailable.
      byId("enhancement-status").textContent = "互動功能暫不可用；下方靜態作品清單仍可閱讀。";
    }
  }

  for (const control of [search, category, tag, featured]) control.addEventListener("input", renderList);
  for (const control of [category, tag, featured]) control.addEventListener("change", renderList);
  window.addEventListener("hashchange", renderDetail);
  window.addEventListener("popstate", renderDetail);
  start();
})();
