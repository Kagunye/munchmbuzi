/* Mbuzi Munch music button
 * Plays the track uploaded in Django admin (Music tracks). With no upload it
 * synthesises an original kalimba + drums groove with the Web Audio API, so
 * the site never ships music it has no licence for.
 */
(function () {
  "use strict";
  const root = document.getElementById("mm-music");
  if (!root) return;

  const btn = root.querySelector(".mm-music__disc");
  const titleEl = root.querySelector(".mm-music__title");
  const subEl = root.querySelector(".mm-music__sub");
  const STORE = "mm-music";
  const TIME = "mm-music-time";
  const trackTitle = root.dataset.title || "Mbuzi Munch vibes";
  const trackArtist = root.dataset.artist || "";
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
  };

  /* ---------- Engine 1: uploaded audio file ---------- */
  function FileEngine(url) {
    const audio = new Audio();
    audio.src = url; audio.loop = true; audio.preload = "none"; audio.volume = 0;
    let fade;
    const ramp = (to, ms, done) => {
      clearInterval(fade);
      const from = audio.volume, steps = Math.max(1, ms / 30); let i = 0;
      fade = setInterval(() => {
        i++; audio.volume = Math.min(1, Math.max(0, from + (to - from) * (i / steps)));
        if (i >= steps) { clearInterval(fade); done && done(); }
      }, 30);
    };
    window.addEventListener("pagehide", () => { if (!audio.paused) store.set(TIME, String(audio.currentTime)); });
    return {
      progress() { return audio.duration ? audio.currentTime / audio.duration : 0; },
      seek(f) { if (audio.duration) audio.currentTime = Math.max(0, Math.min(1, f)) * audio.duration; },
      start() {
        const t = parseFloat(store.get(TIME) || "0");
        if (t && !audio.currentTime) { try { audio.currentTime = t; } catch (e) {} }
        return audio.play().then(() => ramp(0.7, 1200));
      },
      stop() { ramp(0, 500, () => { audio.pause(); store.set(TIME, String(audio.currentTime)); }); },
    };
  }

  /* ---------- Engine 2: original synthesised groove ---------- */
  function SynthEngine() {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    let ctx, master, delay, noiseBuf, timer, step = 0, nextTime = 0;
    const BPM = 106, S16 = 60 / BPM / 4;

    // A minor pentatonic, kalimba register
    const SCALE = [220, 261.63, 293.66, 329.63, 392, 440, 523.25, 587.33, 659.25, 783.99];
    const BASS = [110, 87.31, 130.81, 98];                 // Am · F · C · G
    const PAD = [[220, 261.63, 329.63], [174.61, 220, 261.63], [196, 261.63, 329.63], [196, 246.94, 293.66]];
    const MELODY = [
      [5, -1, 7, -1, 6, -1, 8, -1, 7, -1, -1, 5, 6, -1, 4, -1],
      [3, -1, 5, -1, 4, -1, 6, -1, 5, -1, 3, -1, 4, -1, -1, 2],
      [4, -1, 6, -1, 7, -1, 8, 7, 6, -1, 4, -1, 5, -1, 6, -1],
      [4, -1, 5, -1, 6, -1, -1, 4, 9, -1, 8, -1, 7, -1, 6, 5],
    ];
    const BASS_STEPS = { 0: 1, 3: 0.6, 8: 0.9, 11: 0.6, 14: 0.7 };
    const CONGA = { 7: 220, 10: 180, 15: 165 };

    function init() {
      ctx = new AC();
      const comp = ctx.createDynamicsCompressor();
      comp.threshold.value = -18; comp.ratio.value = 4;
      master = ctx.createGain(); master.gain.value = 0;
      master.connect(comp); comp.connect(ctx.destination);
      // echo for the kalimba
      delay = ctx.createDelay(1); delay.delayTime.value = S16 * 3;
      const fb = ctx.createGain(); fb.gain.value = 0.32;
      const lp = ctx.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 2400;
      const wet = ctx.createGain(); wet.gain.value = 0.35;
      delay.connect(lp); lp.connect(fb); fb.connect(delay); lp.connect(wet); wet.connect(master);
      noiseBuf = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
      const d = noiseBuf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    }

    function env(g, t, peak, attack, decay) {
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(peak, t + attack);
      g.gain.exponentialRampToValueAtTime(0.0001, t + attack + decay);
    }

    function kalimba(f, t, vel) {
      const g = ctx.createGain(); env(g, t, 0.22 * vel, 0.003, 1.3);
      const o1 = ctx.createOscillator(); o1.type = "sine"; o1.frequency.value = f;
      const g2 = ctx.createGain(); env(g2, t, 0.06 * vel, 0.002, 0.18);
      const o2 = ctx.createOscillator(); o2.type = "sine"; o2.frequency.value = f * 5.43; // metal tine overtone
      o1.connect(g); o2.connect(g2); g.connect(master); g2.connect(master); g.connect(delay);
      o1.start(t); o2.start(t); o1.stop(t + 1.5); o2.stop(t + 0.3);
    }

    function kick(t, vel) {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.frequency.setValueAtTime(140, t); o.frequency.exponentialRampToValueAtTime(45, t + 0.12);
      env(g, t, 0.8 * vel, 0.002, 0.32);
      o.connect(g); g.connect(master); o.start(t); o.stop(t + 0.4);
    }

    function noise(t, type, freq, q, peak, decay) {
      const s = ctx.createBufferSource(); s.buffer = noiseBuf;
      const f = ctx.createBiquadFilter(); f.type = type; f.frequency.value = freq; f.Q.value = q;
      const g = ctx.createGain(); env(g, t, peak, 0.001, decay);
      s.connect(f); f.connect(g); g.connect(master); s.start(t); s.stop(t + decay + 0.05);
    }

    function conga(f, t) {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.frequency.setValueAtTime(f, t); o.frequency.exponentialRampToValueAtTime(f * 0.78, t + 0.15);
      env(g, t, 0.28, 0.002, 0.2);
      o.connect(g); g.connect(master); o.start(t); o.stop(t + 0.25);
    }

    function bass(f, t, vel) {
      const o = ctx.createOscillator(); o.type = "triangle"; o.frequency.value = f;
      const lp = ctx.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 420;
      const g = ctx.createGain(); env(g, t, 0.42 * vel, 0.01, S16 * 2.6);
      o.connect(lp); lp.connect(g); g.connect(master); o.start(t); o.stop(t + S16 * 3);
    }

    function pad(chord, t) {
      chord.forEach((f) => {
        const o = ctx.createOscillator(); o.type = "sine"; o.frequency.value = f;
        const g = ctx.createGain();
        g.gain.setValueAtTime(0.0001, t);
        g.gain.linearRampToValueAtTime(0.035, t + 0.6);
        g.gain.linearRampToValueAtTime(0.0001, t + S16 * 16);
        o.connect(g); g.connect(master); o.start(t); o.stop(t + S16 * 16 + 0.05);
      });
    }

    function schedule(s, t) {
      const pos = s % 16, bar = Math.floor(s / 16) % 4, cycle = Math.floor(s / 64);
      if (pos === 0) pad(PAD[bar], t);
      if (pos % 4 === 0) kick(t, pos === 0 ? 1 : 0.75);
      noise(t, "highpass", 7500, 0.7, pos % 4 === 2 ? 0.12 : 0.05, 0.05);   // shaker
      if (pos === 4 || pos === 12) noise(t, "bandpass", 1900, 1.2, 0.22, 0.12); // rim
      if (CONGA[pos] && (cycle + bar) % 2 === 0) conga(CONGA[pos], t);
      if (BASS_STEPS[pos]) bass(BASS[bar], t, BASS_STEPS[pos]);
      const n = MELODY[bar][pos];
      // the melody joins on the second pass, so the groove builds in
      if (n >= 0 && cycle > 0) kalimba(SCALE[n], t, pos % 4 === 0 ? 1 : 0.75);
      else if (n >= 0 && pos % 8 === 0) kalimba(SCALE[n], t, 0.6);
    }

    function tick() {
      while (nextTime < ctx.currentTime + 0.15) {
        schedule(step, nextTime);
        nextTime += S16 * (step % 2 ? 0.94 : 1.06); // a little swing
        step++;
      }
    }

    return {
      progress() { return (step % 64) / 64; },  // position in the 4-bar loop
      seek() {},
      start() {
        if (!ctx) init();
        return ctx.resume().then(() => {
          if (ctx.state !== "running") throw new Error("blocked");
          nextTime = ctx.currentTime + 0.05;
          clearInterval(timer); timer = setInterval(tick, 25);
          master.gain.cancelScheduledValues(ctx.currentTime);
          master.gain.setValueAtTime(master.gain.value, ctx.currentTime);
          master.gain.linearRampToValueAtTime(0.6, ctx.currentTime + 1.5);
        });
      },
      stop() {
        if (!ctx) return;
        master.gain.cancelScheduledValues(ctx.currentTime);
        master.gain.setValueAtTime(master.gain.value, ctx.currentTime);
        master.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.5);
        setTimeout(() => { clearInterval(timer); ctx.suspend(); }, 550);
      },
    };
  }

  /* ---------- Button behaviour ---------- */
  const engine = root.dataset.src ? FileEngine(root.dataset.src) : SynthEngine();
  if (!engine) { root.hidden = true; return; }
  let playing = false;

  const listeners = [];
  function render() {
    listeners.forEach((fn) => fn(playing));
    root.classList.toggle("is-playing", playing);
    btn.setAttribute("aria-pressed", String(playing));
    btn.setAttribute("aria-label", playing ? "Pause Mbuzi Munch music" : "Play Mbuzi Munch music");
    titleEl.textContent = playing ? trackTitle : "Play the Mbuzi vibe";
    subEl.textContent = playing ? (trackArtist || "Now playing") : "Tap the goat for music";
  }

  function play() {
    return engine.start().then(() => {
      playing = true; root.classList.remove("is-hint"); store.set(STORE, "on"); render();
      // only one sound at a time: mute any reel that has sound on
      window.dispatchEvent(new CustomEvent("mm:music-play"));
      if ("mediaSession" in navigator) {
        navigator.mediaSession.metadata = new MediaMetadata({
          title: trackTitle, artist: trackArtist || "Mbuzi Munch", album: "Mbuzi Munch",
          artwork: [{ src: root.querySelector("img").src, sizes: "512x512", type: "image/png" }],
        });
        navigator.mediaSession.setActionHandler("pause", () => pause(true));
        navigator.mediaSession.setActionHandler("play", () => play());
      }
    });
  }

  function pause(remember) {
    if (!playing) return;
    engine.stop(); playing = false; render();
    if (remember) store.set(STORE, "off");
  }

  btn.addEventListener("click", () => {
    if (playing) pause(true);
    else play().catch(() => { subEl.textContent = "Tap again to play"; });
  });

  // Shared controls for other players on the page (e.g. the hero pennant)
  window.mmMusic = {
    toggle() { btn.click(); },
    isPlaying: () => playing,
    onChange(fn) { listeners.push(fn); fn(playing); },
    progress: () => engine.progress(),
    seek: (f) => engine.seek(f),
    hasTrack: !!root.dataset.src,
  };

  /* Hero pennant player */
  const pennant = document.querySelector(".pennant");
  if (pennant) {
    const pBtn = pennant.querySelector(".pennant__play");
    const bar = pennant.querySelector(".pennant__bar");
    const fill = bar.querySelector("span");
    let timer;
    const paint = () => {
      const pct = Math.round(window.mmMusic.progress() * 1000) / 10;
      fill.style.width = pct + "%";
      bar.setAttribute("aria-valuenow", String(Math.round(pct)));
    };
    window.mmMusic.onChange((on) => {
      pennant.classList.toggle("is-playing", on);
      pBtn.setAttribute("aria-pressed", String(on));
      pBtn.setAttribute("aria-label", on ? "Pause music" : "Play music");
      clearInterval(timer);
      if (on) { paint(); timer = setInterval(paint, 200); }
    });
    pBtn.addEventListener("click", () => window.mmMusic.toggle());
    bar.addEventListener("click", (e) => {
      const r = bar.getBoundingClientRect();
      window.mmMusic.seek((e.clientX - r.left) / r.width);
      paint();
    });
  }

  // a reel turned its sound on: step aside
  window.addEventListener("mm:reel-sound", () => pause(false));

  // the visitor had music on at the previous page: browsers need a tap before
  // sound can start, so carry on at their first interaction with this page
  if (store.get(STORE) === "on") {
    root.classList.add("is-hint");
    subEl.textContent = "Tap anywhere to keep the vibe going";
    const resume = (e) => {
      // A tap on any music control (goat button, pennant, "Put the record on") handles
      // play/pause itself; resuming here too would start the music and the control
      // would then immediately pause it again.
      if (e.target.closest && e.target.closest("[data-music-control], .mm-music__disc")) return cleanup();
      if (playing) return cleanup();
      play().catch(() => {}).finally(cleanup);
    };
    const cleanup = () => {
      document.removeEventListener("pointerdown", resume, true);
      document.removeEventListener("keydown", resume, true);
    };
    document.addEventListener("pointerdown", resume, true);
    document.addEventListener("keydown", resume, true);
    play().catch(() => {}); // works when the browser already allows sound for this site
  }

  // background tabs throttle timers, which would make the groove stutter
  document.addEventListener("visibilitychange", () => {
    if (!root.dataset.src && playing && document.hidden) { engine.stop(); root.dataset.wasPlaying = "1"; }
    else if (!root.dataset.src && root.dataset.wasPlaying && !document.hidden) { delete root.dataset.wasPlaying; engine.start().catch(() => {}); }
  });
})();
