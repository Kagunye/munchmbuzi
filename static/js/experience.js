/* The Mbuzi Munch Experience: chapters, secret blend, doneness, plate builder
 * with a typed receipt, bottle-to-glass slider and grill embers. */
(function () {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* "Put the record on" → the site's music button */
  $$("[data-play-music]").forEach((b) => b.addEventListener("click", () => {
    const disc = $(".mm-music__disc");
    if (disc && disc.getAttribute("aria-pressed") !== "true") disc.click();
  }));

  /* Chapter progress */
  const links = $$(".xp-progress a");
  if (links.length && "IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) links.forEach((l) => l.classList.toggle("is-on", l.dataset.ch === e.target.id));
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    $$(".xp-chapter").forEach((c) => io.observe(c));
  }

  /* Typewriter title */
  const typed = $(".xp-type");
  if (typed && !reduce) {
    const text = typed.textContent;
    typed.textContent = ""; typed.classList.add("is-typing");
    let i = 0;
    const tick = () => {
      typed.textContent = text.slice(0, ++i);
      if (i < text.length) setTimeout(tick, text[i - 1] === " " ? 40 : 95);
      else typed.classList.remove("is-typing");
    };
    setTimeout(tick, 500);
  }

  /* II · Secret blend */
  const jars = $$(".jar");
  const meter = $(".blend-meter span");
  const blendMsg = $(".blend-msg");
  const added = new Set();
  jars.forEach((jar) => jar.addEventListener("click", () => {
    const s = jar.dataset.spice;
    if (added.has(s)) { added.delete(s); jar.classList.remove("is-in"); }
    else { added.add(s); jar.classList.add("is-in"); }
    jar.setAttribute("aria-pressed", String(added.has(s)));
    meter.style.width = (added.size / jars.length) * 100 + "%";
    if (added.size === jars.length) {
      blendMsg.innerHTML = "<b>That's it!</b> The authentic Kenyan Nyama Choma taste.";
      blendMsg.classList.add("is-done");
    } else {
      blendMsg.classList.remove("is-done");
      blendMsg.textContent = added.size ? [...added].join(" + ") + "…" : "The blend is waiting…";
    }
  }));

  /* III · Doneness (carried onto the receipt) */
  let doneness = "Medium";
  const doneMsg = $(".done-msg");
  const steak = $(".xp-steak");
  const DONE_TEXT = {
    "Rare": "Rare. Just let your waitress know, and choose your preferred sauce.",
    "Medium": "Medium. Just let your waitress know, and choose your preferred sauce.",
    "Well done": "Well done. Just let your waitress know, and choose your preferred sauce.",
  };
  $$(".doneness button").forEach((b) => b.addEventListener("click", () => {
    doneness = b.dataset.done;
    $$(".doneness button").forEach((x) => { const on = x === b; x.classList.toggle("is-on", on); x.setAttribute("aria-checked", String(on)); });
    doneMsg.textContent = DONE_TEXT[doneness];
    if (steak) {
      steak.dataset.done = doneness;
      $(".xp-steak__cap").textContent = "T-Bone · " + doneness;
    }
    renderReceipt(false);
  }));

  /* IV · Plate builder + receipt */
  const receipt = $(".receipt");
  const linesEl = $(".receipt__lines");
  const totalEl = $(".r-total");
  const bookLink = $("[data-book-plate]");
  let slip = 1;
  const pad = (n) => String(n).padStart(4, "0");
  const fmt = (n) => n.toLocaleString("en-KE");

  function picks() {
    return ["nyama", "side", "drink"].map((g) => $(`input[name="${g}"]:checked`)).filter(Boolean)
      .map((i) => ({ label: i.dataset.label, price: +i.dataset.price, serves: i.dataset.serves }));
  }

  function renderReceipt(animate) {
    if (!receipt) return;
    const items = picks();
    const total = items.reduce((s, i) => s + i.price, 0);
    linesEl.innerHTML = "";
    items.forEach((it, n) => {
      const row = document.createElement("div");
      row.className = "receipt__line";
      row.innerHTML = `<span></span><i></i><b>${fmt(it.price)}/-</b>`;
      row.querySelector("span").textContent = it.label + (it.serves ? ` (${it.serves})` : "");
      if (animate && !reduce) { row.style.animationDelay = n * 0.12 + "s"; row.classList.add("is-printing"); }
      linesEl.appendChild(row);
    });
    totalEl.textContent = fmt(total);
    $(".r-done").textContent = doneness;
    $(".r-no").textContent = pad(slip);
    $(".r-date").textContent = new Date().toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
    if (bookLink) {
      const note = `My Mbuzi Munch plate: ${items.map((i) => i.label).join(", ")} (${doneness}). Est. KES ${fmt(total)}`;
      bookLink.href = bookLink.href.split("?")[0] + "?notes=" + encodeURIComponent(note);
    }
    if (animate && !reduce) {
      receipt.classList.remove("is-printing"); void receipt.offsetWidth; receipt.classList.add("is-printing");
      // never leave the slip stuck on its first animation frame (e.g. a throttled background tab)
      clearTimeout(renderReceipt.t);
      renderReceipt.t = setTimeout(() => {
        receipt.classList.remove("is-printing");
        $$(".receipt__line.is-printing").forEach((r) => r.classList.remove("is-printing"));
      }, 1200);
    }
  }

  $$(".builder input[type=radio]").forEach((i) => i.addEventListener("change", () => { slip++; renderReceipt(true); }));
  const reprint = $("[data-reprint]");
  if (reprint) reprint.addEventListener("click", () => { slip++; renderReceipt(true); });
  renderReceipt(false);

  /* V · Bottle to glass */
  const range = $("#bottle-range");
  if (range) {
    const svg = $(".bottle-svg");
    const steps = $$(".bottle-steps span");
    const neck = $(".bottle-neck", svg), cut = $(".cut-line", svg), tea = $(".tea", svg), rim = $(".rim", svg), lime = $(".lime", svg);
    const labels = $$(".label", svg);
    const update = () => {
      const v = +range.value / 100;
      const lift = Math.min(1, v / 0.5);              // 0 → .5: neck lifts away
      const fill = Math.max(0, (v - 0.5) / 0.5);      // .5 → 1: tea pours in
      neck.style.transform = `translate(${lift * 40}px, ${-lift * 60}px) rotate(${lift * 25}deg)`;
      neck.style.opacity = String(1 - lift);
      cut.style.opacity = String(v < 0.5 ? 1 - lift * 0.6 : 0);
      labels.forEach((l) => { l.style.opacity = String(1 - lift); });
      rim.style.opacity = String(lift);
      tea.style.opacity = String(fill);
      tea.setAttribute("y", String(244 - fill * 120));
      tea.setAttribute("height", String(fill * 120 + 4));
      lime.style.opacity = String(fill > 0.85 ? 1 : 0);
      const step = v < 0.25 ? 0 : v < 0.75 ? 1 : 2;
      steps.forEach((s, i) => s.classList.toggle("is-on", i === step));
      range.setAttribute("aria-valuetext", steps[step].textContent);
    };
    range.addEventListener("input", update);
    update();
  }

  /* Grill embers */
  if (!reduce) {
    $$("canvas.embers").forEach((cv) => {
      const ctx = cv.getContext("2d");
      let w, h, parts = [], running = false;
      const size = () => { w = cv.width = cv.offsetWidth; h = cv.height = cv.offsetHeight; };
      const spawn = () => ({ x: Math.random() * w, y: h + 10, r: Math.random() * 2.2 + 0.6, vy: -(Math.random() * 1.2 + 0.5), vx: (Math.random() - 0.5) * 0.6, life: 1, hue: 15 + Math.random() * 30 });
      size(); window.addEventListener("resize", size);
      parts = Array.from({ length: 70 }, () => { const p = spawn(); p.y = Math.random() * h; return p; });
      const frame = () => {
        if (!running) return;
        ctx.clearRect(0, 0, w, h);
        parts.forEach((p, i) => {
          p.x += p.vx + Math.sin(p.y / 40) * 0.3; p.y += p.vy; p.life -= 0.0035;
          if (p.y < -10 || p.life <= 0) parts[i] = spawn();
          ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
          ctx.fillStyle = `hsla(${p.hue}, 100%, 60%, ${Math.max(0, p.life) * 0.9})`;
          ctx.shadowColor = "rgba(255, 120, 30, .9)"; ctx.shadowBlur = 8;
          ctx.fill();
        });
        requestAnimationFrame(frame);
      };
      new IntersectionObserver((es) => es.forEach((e) => {
        if (e.isIntersecting && !running) { running = true; size(); frame(); } else if (!e.isIntersecting) running = false;
      })).observe(cv);
    });
  }
})();
