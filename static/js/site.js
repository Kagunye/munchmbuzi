(function () {
  "use strict";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Mobile navigation */
  const toggle = $(".nav-toggle");
  const nav = $("#site-nav");
  if (toggle && nav) {
    const setOpen = (open) => {
      nav.classList.toggle("is-open", open);
      document.body.classList.toggle("nav-open", open);
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      const icon = toggle.querySelector("use");
      if (icon) icon.setAttribute("href", open ? "#i-close" : "#i-menu");
    };
    toggle.addEventListener("click", () => setOpen(!nav.classList.contains("is-open")));
    $$("a", nav).forEach((a) => a.addEventListener("click", () => setOpen(false)));
    document.addEventListener("keydown", (e) => e.key === "Escape" && setOpen(false));
  }

  /* Vintage mode: clean by default, vintage film look on request (remembered) */
  const vintageBtns = $$("[data-vintage-toggle]");
  const syncVintage = () => {
    const on = document.documentElement.classList.contains("vintage");
    vintageBtns.forEach((b) => {
      b.setAttribute("aria-pressed", String(on));
      if (b.dataset.labelOn) b.querySelector(".btn-label").textContent = on ? b.dataset.labelOn : b.dataset.labelOff;
    });
  };
  vintageBtns.forEach((b) => b.addEventListener("click", () => {
    const on = document.documentElement.classList.toggle("vintage");
    try { localStorage.setItem("mm-vintage", on ? "on" : "off"); } catch (e) {}
    syncVintage();
  }));
  syncVintage();

  /* Mark when the page is scrolled (the home pennant slides under the header) */
  const markScroll = () => document.documentElement.classList.toggle("is-scrolled", window.scrollY > 4);
  window.addEventListener("scroll", markScroll, { passive: true });
  markScroll();

  /* Pause the endless sliding rows while they're off screen */
  if ("IntersectionObserver" in window) {
    const mio = new IntersectionObserver((entries) => entries.forEach((e) => {
      e.target.querySelectorAll(".dish-marquee__track, .photo-slide__track, .marquee__track")
        .forEach((t) => { t.style.animationPlayState = e.isIntersecting ? "" : "paused"; });
    }), { rootMargin: "200px 0px" });
    $$(".dish-marquee, .photo-slide, .marquee").forEach((el) => mio.observe(el));
  }

  /* Let the browser decode images off the main thread */
  $$("img[loading=lazy]").forEach((img) => { img.decoding = "async"; });  // not the logo / first screen

  /* Hero slideshow (slides after the first load their photo just before they show) */
  const loadSlide = (s) => { if (s && s.dataset.bg) { s.style.backgroundImage = `url('${s.dataset.bg}')`; delete s.dataset.bg; } };
  window.addEventListener("load", () => setTimeout(() => loadSlide($$(".hero__slide")[1]), 1500));
  const slides = $$(".hero__slide");
  const dots = $$(".hero__dots button");
  if (slides.length > 1) {
    let i = 0, timer;
    const show = (n) => {
      slides[i].classList.remove("is-active"); dots[i] && dots[i].classList.remove("is-active");
      i = (n + slides.length) % slides.length;
      loadSlide(slides[i]);
      slides[i].classList.add("is-active"); dots[i] && dots[i].classList.add("is-active");
      loadSlide(slides[(i + 1) % slides.length]);  // fetch the next photo ahead of time
    };
    const start = () => { if (!reduceMotion) timer = setInterval(() => show(i + 1), 6000); };
    dots.forEach((d, n) => d.addEventListener("click", () => { clearInterval(timer); show(n); start(); }));
    start();
  }

  /* Reveal on scroll */
  const reveals = $$(".reveal");
  if ("IntersectionObserver" in window && !reduceMotion) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("is-visible"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add("is-visible"));
  }

  /* Lazy-load background video only when visible and motion is allowed */
  const vid = $("video[data-lazy]");
  if (vid && !reduceMotion && "IntersectionObserver" in window) {
    const vio = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          $$("source", vid).forEach((s) => { s.src = s.dataset.src; });
          vid.load(); vid.play().catch(() => {});
          vio.disconnect();
        }
      });
    });
    vio.observe(vid);
  }

  /* Instagram reels: only ONE plays at a time (the one most in view, or the one
     you hover / turn the sound on for). A video file is only downloaded when its
     reel is about to play, so a row of reels never loads and decodes all at once. */
  const reels = $$(".reel__video");
  if (reels.length) {
    const load = (v) => {
      if (!v.dataset.loaded) {
        $$("source", v).forEach((s) => { s.src = s.dataset.src; });
        v.preload = "auto"; v.load(); v.dataset.loaded = "1";
      }
    };
    const ratios = new Map();
    let chosen = null;   // reel picked by hover or sound; wins while it's on screen
    let active = null;

    const pickActive = () => {
      // a hovered / sound-on reel plays while it's still (mostly) on screen;
      // if visibility hasn't been reported yet, trust the user's action
      if (chosen && (!ratios.has(chosen) || ratios.get(chosen) > 0.2)) return chosen;
      let best = null, bestRatio = 0.45;
      reels.forEach((v) => { const r = ratios.get(v) || 0; if (r > bestRatio) { best = v; bestRatio = r; } });
      return best;
    };
    const update = () => {
      const next = pickActive();
      if (next === active) return;
      if (active) active.pause();
      active = next;
      if (active && (!reduceMotion || active.dataset.user)) { load(active); active.play().catch(() => {}); }
    };

    if ("IntersectionObserver" in window) {
      const rio = new IntersectionObserver((entries) => {
        entries.forEach((e) => ratios.set(e.target, e.isIntersecting ? e.intersectionRatio : 0));
        update();
      }, { threshold: [0, 0.2, 0.45, 0.7, 1] });
      reels.forEach((v) => rio.observe(v));
    }
    // hovering (or focusing) a reel makes it the one that plays
    reels.forEach((v) => {
      const reel = v.closest(".reel");
      const choose = () => { chosen = v; update(); };
      reel.addEventListener("pointerenter", (e) => { if (e.pointerType === "mouse") choose(); });
      reel.addEventListener("focusin", choose);
    });
    // pause when the tab is hidden, resume when it's back
    document.addEventListener("visibilitychange", () => {
      if (!active) return;
      if (document.hidden) active.pause(); else active.play().catch(() => {});
    });

    $$(".reel__sound").forEach((btn) => btn.addEventListener("click", () => {
      const v = btn.closest(".reel").querySelector("video");
      const turnOn = v.muted;
      reels.forEach((other) => { other.muted = true; });
      $$(".reel__sound").forEach((b) => { b.setAttribute("aria-pressed", "false"); b.setAttribute("aria-label", "Turn sound on"); });
      if (turnOn) {
        v.muted = false; v.dataset.user = "1";
        chosen = v; update();  // make this the playing reel (pauses the previous one)
        load(v); v.play().catch(() => {});
        btn.setAttribute("aria-pressed", "true"); btn.setAttribute("aria-label", "Mute");
        window.dispatchEvent(new CustomEvent("mm:reel-sound")); // pauses the site music
      }
    }));
    // site music started: silence the reels
    window.addEventListener("mm:music-play", () => {
      reels.forEach((v) => { v.muted = true; });
      $$(".reel__sound").forEach((b) => { b.setAttribute("aria-pressed", "false"); b.setAttribute("aria-label", "Turn sound on"); });
    });
  }

  /* Menu: tabs + search */
  const tabs = $$(".tab[data-section]");
  const sections = $$(".menu-section");
  if (tabs.length) {
    const activate = (key, push) => {
      tabs.forEach((t) => { const on = t.dataset.section === key; t.classList.toggle("is-active", on); t.setAttribute("aria-selected", on); });
      sections.forEach((s) => s.classList.toggle("is-active", s.id === key));
      if (push) history.replaceState(null, "", "#" + key);
    };
    tabs.forEach((t) => t.addEventListener("click", () => { clearSearch(); activate(t.dataset.section, true); }));
    const hash = location.hash.replace("#", "");
    if (hash && sections.some((s) => s.id === hash)) activate(hash, false);

    const search = $("#menu-search");
    const empty = $(".menu-empty");
    const items = $$(".menu-item");
    function clearSearch() { if (search && search.value) { search.value = ""; filter(""); } }
    function filter(q) {
      q = q.trim().toLowerCase();
      if (!q) {
        items.forEach((it) => (it.hidden = false));
        $$(".menu-cat").forEach((c) => (c.hidden = false));
        const active = tabs.find((t) => t.classList.contains("is-active"));
        sections.forEach((s) => s.classList.toggle("is-active", active && s.id === active.dataset.section));
        if (empty) empty.style.display = "none";
        return;
      }
      let hits = 0;
      items.forEach((it) => { const m = it.dataset.search.includes(q); it.hidden = !m; if (m) hits++; });
      $$(".menu-cat").forEach((c) => (c.hidden = !$$(".menu-item:not([hidden])", c).length));
      sections.forEach((s) => s.classList.toggle("is-active", !!$$(".menu-item:not([hidden])", s).length));
      if (empty) empty.style.display = hits ? "none" : "block";
    }
    if (search) search.addEventListener("input", (e) => filter(e.target.value));
  }
})();
