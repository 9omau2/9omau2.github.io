const $ = (selector) => document.querySelector(selector);

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  $("#theme-toggle").checked = theme === "light";
  $("meta[name='theme-color']").content = theme === "dark" ? "#0e1118" : "#fbfcff";
  try { localStorage.setItem("security-profile-theme", theme); } catch {}
}

setTheme(document.documentElement.dataset.theme === "light" ? "light" : "dark");
$("#theme-toggle").addEventListener("change", (event) => {
  setTheme(event.target.checked ? "light" : "dark");
});

function makeElement(tag, value, className) {
  const element = document.createElement(tag);
  element.textContent = value ?? "";
  if (className) element.className = className;
  return element;
}

function validLink(value) {
  if (!value) return null;
  try {
    const url = new URL(value);
    return ["https:", "http:", "mailto:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

function renderProfile(profile) {
  const name = profile.name || "이름";
  document.title = "9omau2";
  $("#profile-initials").textContent = profile.initials || "HN";
  if (profile.resumePdf) {
    try {
      const pdfUrl = new URL(profile.resumePdf, document.baseURI);
      if (pdfUrl.origin === location.origin && pdfUrl.pathname.toLowerCase().endsWith(".pdf")) {
        const download = $("#resume-download");
        download.href = pdfUrl.href;
        download.hidden = false;
      }
    } catch {
      // PDF 경로가 잘못되면 다운로드 링크를 표시하지 않습니다.
    }
  }
  if (profile.image) {
    try {
      const imageUrl = new URL(profile.image, document.baseURI);
      if (imageUrl.origin === location.origin || imageUrl.protocol === "https:") {
        const image = $("#profile-image");
        image.onload = () => {
          image.hidden = false;
          $("#profile-initials").hidden = true;
        };
        image.onerror = () => {
          image.hidden = true;
          $("#profile-initials").hidden = false;
        };
        image.src = imageUrl.href;
      }
    } catch {
      // 이미지 경로가 잘못되면 이니셜을 그대로 보여줍니다.
    }
  }
  $("#profile-name").textContent = name;
  $("#profile-handle").textContent = profile.handle || "";
  $("#profile-role").textContent = profile.role || "";
  $("#profile-intro").textContent = profile.intro || "";
  $("#footer-name").textContent = name;

  for (const item of profile.highlights || []) {
    $("#profile-highlights").append(makeElement("li", item));
  }
  for (const item of profile.links || []) {
    const href = validLink(item.url);
    if (!href) continue;
    const link = makeElement("a", item.label || href);
    link.href = href;
    if (!href.startsWith("mailto:")) {
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    }
    $("#profile-links").append(link);
  }
}

function renderSections(sections) {
  sections.forEach((section, index) => {
    const wrapper = makeElement("section", "", "resume-section");
    wrapper.id = `section-${index + 1}`;
    const heading = makeElement("div", "", "section-heading");
    heading.append(makeElement("span", String(index + 1).padStart(2, "0"), "section-number"));
    heading.append(makeElement("h2", section.title));
    wrapper.append(heading);

    for (const item of section.items || []) {
      const entry = makeElement("article", "", "entry");
      entry.append(makeElement("span", item.date, "entry-date"));
      const body = document.createElement("div");
      const titleRow = makeElement("div", "", "entry-title-row");
      titleRow.append(makeElement("h3", item.title));
      if (item.tags?.length) {
        const tags = makeElement("ul", "", "entry-tags");
        for (const tag of item.tags) tags.append(makeElement("li", tag));
        titleRow.append(tags);
      }
      body.append(titleRow);
      if (item.subtitle) body.append(makeElement("p", item.subtitle, "entry-subtitle"));
      if (item.description) body.append(makeElement("p", item.description, "entry-description"));
      const href = validLink(item.url);
      if (href) {
        const link = makeElement("a", item.linkLabel || "자세히 보기", "entry-link");
        link.href = href;
        if (!href.startsWith("mailto:")) {
          link.target = "_blank";
          link.rel = "noopener noreferrer";
        }
        body.append(link);
      }
      entry.append(body);
      wrapper.append(entry);
    }
    $("#sections").append(wrapper);
  });
}

function renderToc(sections) {
  const entries = [{ id: "about", title: "About Me" }, ...sections.map((section, index) => ({
    id: `section-${index + 1}`,
    title: section.title || `Section ${index + 1}`,
  }))];
  const toc = $("#page-toc");
  const list = $("#toc-list");
  for (const entry of entries) {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.className = "toc-link";
    link.href = `#${entry.id}`;
    link.setAttribute("aria-label", entry.title);
    link.append(makeElement("span", entry.title, "toc-label"));
    item.append(link);
    list.append(item);
  }
  toc.hidden = false;

  const targets = entries.map((entry) => document.getElementById(entry.id));
  const links = [...list.querySelectorAll("a")];
  let scheduled = false;
  function updateToc() {
    scheduled = false;
    const maxScroll = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
    let active = 0;
    const threshold = window.innerHeight * 0.35;
    targets.forEach((target, index) => {
      if (target.getBoundingClientRect().top <= threshold) active = index;
    });
    if (maxScroll && window.scrollY >= maxScroll - 2) active = links.length - 1;
    links.forEach((link, index) => {
      link.classList.toggle("is-active", index === active);
      link.classList.toggle("is-past", index < active);
      if (index === active) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
    toc.style.setProperty("--toc-progress", `${list.children[active].offsetTop - list.children[0].offsetTop}px`);
  }
  function scheduleUpdate() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(updateToc);
  }
  window.addEventListener("scroll", scheduleUpdate, { passive: true });
  window.addEventListener("resize", scheduleUpdate);
  window.addEventListener("hashchange", scheduleUpdate);
  updateToc();
}

async function start() {
  try {
    const response = await fetch("./content.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    renderProfile(data.profile || {});
    renderSections(data.sections || []);
    renderToc(data.sections || []);
    $("#updated-at").textContent = data.updatedAt || "";
  } catch (error) {
    $("#error-message").hidden = false;
    $("#error-message").textContent = "content.json을 읽지 못했습니다. 로컬 서버와 JSON 문법을 확인해 주세요.";
    console.error(error);
  }
}

start();
