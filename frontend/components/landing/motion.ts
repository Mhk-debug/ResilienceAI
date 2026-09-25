"use client";

/**
 * Motion primitives for the landing page.
 *
 * One rAF director owns the scroll value and the pointer position; every hook subscribes to it.
 * That keeps the page to a single animation loop no matter how many layers move, and makes the
 * reduced-motion path a single switch rather than a per-component concern.
 *
 * Rules this file enforces:
 *  - only `transform` and `opacity` are ever animated (no layout thrash);
 *  - nothing runs while the tab is hidden, or when the visitor asks for reduced motion;
 *  - an element that is off-screen is never transformed.
 */

import { useEffect, useRef, useState, type RefObject } from "react";

type Listener = (state: DirectorState) => void;

interface DirectorState {
  /** raw scroll position, px */
  scrollY: number;
  /** lerped scroll position, px — what animations should read */
  smoothed: number;
  /** viewport height, px */
  viewportHeight: number;
  /** pointer position, normalised to −1…1 from the viewport centre */
  pointerX: number;
  pointerY: number;
  /** false when motion is suppressed (reduced motion, hidden tab) */
  motionAllowed: boolean;
}

const state: DirectorState = {
  scrollY: 0,
  smoothed: 0,
  viewportHeight: 0,
  pointerX: 0,
  pointerY: 0,
  motionAllowed: true,
};

const listeners = new Set<Listener>();
let rafId = 0;
let running = false;
let reducedMotion = false;

function anyListenerWantsPointer(): boolean {
  return listeners.size > 0;
}

function frame() {
  state.scrollY = window.scrollY || window.pageYOffset || 0;
  // critically-damped-ish easing; 0.12 settles in ~10 frames without overshoot
  state.smoothed += (state.scrollY - state.smoothed) * 0.12;
  if (Math.abs(state.scrollY - state.smoothed) < 0.1) state.smoothed = state.scrollY;
  state.viewportHeight = window.innerHeight;

  for (const listener of listeners) listener(state);
  rafId = requestAnimationFrame(frame);
}

function start() {
  if (running) return;
  running = true;
  state.scrollY = window.scrollY || 0;
  state.smoothed = state.scrollY;
  state.viewportHeight = window.innerHeight;
  rafId = requestAnimationFrame(frame);
}

function stop() {
  if (!running) return;
  running = false;
  cancelAnimationFrame(rafId);
}

function onVisibility() {
  // A hidden tab stops the loop; on return we resync so nothing animates a jump.
  if (document.hidden) {
    stop();
  } else if (listeners.size > 0 && !reducedMotion) {
    state.smoothed = window.scrollY || 0;
    start();
  }
}

function onPointerMove(event: PointerEvent) {
  if (!anyListenerWantsPointer() || !state.motionAllowed) return;
  state.pointerX = (event.clientX / window.innerWidth) * 2 - 1;
  state.pointerY = (event.clientY / window.innerHeight) * 2 - 1;
}

function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  if (listeners.size === 1) {
    // Reveal-on-scroll only hides content once JS is running to reveal it again. Without this
    // class the `.reveal` rule never applies, so a no-JS or failed-hydration visitor still gets
    // the whole page instead of a hero over blank sections.
    document.documentElement.classList.add("js-motion");
    window.addEventListener("scroll", onScrollHint, { passive: true });
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    document.addEventListener("visibilitychange", onVisibility);
    start();
  }
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0) {
      window.removeEventListener("scroll", onScrollHint);
      window.removeEventListener("pointermove", onPointerMove);
      document.removeEventListener("visibilitychange", onVisibility);
      stop();
    }
  };
}

// The loop polls scroll itself; this listener exists only to wake a stopped loop (e.g. after a
// visibilitychange that we decided to honour).
function onScrollHint() {
  if (!running && !reducedMotion && listeners.size > 0) start();
}

/** True when the visitor has asked for reduced motion, or the environment cannot animate. */
export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => {
      reducedMotion = query.matches;
      state.motionAllowed = !query.matches;
      if (query.matches) {
        stop();
        state.smoothed = state.scrollY;
      } else {
        start();
      }
      setReduced(query.matches);
    };
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  return reduced;
}

/** `true` once the page has scrolled past `threshold` px. For the header's solid state.
 *  Pass `active: false` on routes that never change the header (no subscription, no re-renders). */
export function useScrolled(threshold = 80, active = true): boolean {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    if (!active) {
      setScrolled(false);
      return;
    }
    let last = 0;
    return subscribe((s) => {
      const now = performance.now();
      if (now - last < 80) return;
      last = now;
      setScrolled((prev) => (prev !== s.scrollY > threshold ? s.scrollY > threshold : prev));
    });
  }, [threshold, active]);

  return scrolled;
}

/**
 * Pointer/scroll parallax for a layer. Writes `transform` straight to the node — no React re-render
 * per frame. `depth` is in px-per-100px-of-scroll and px-per-unit-of-pointer offset.
 */
export function useParallax<T extends HTMLElement | SVGElement>(
  depth: number,
  options: { pointer?: number; idle?: number; disabled?: boolean } = {},
): RefObject<T | null> {
  const ref = useRef<T | null>(null);
  const { pointer = 0, idle = 0, disabled = false } = options;

  useEffect(() => {
    const node = ref.current;
    if (!node || disabled) return;

    // Baseline = the page's scroll position when this layer mounted. Offsets are measured from
    // there, so a layer is never displaced at rest — only layers separate as the visitor scrolls.
    // (Measuring from the element's own centre instead shifts bottom-anchored layers off-screen.)
    const baseline = window.scrollY || 0;
    let docTop = 0;
    let layerHeight = 0;
    const idlePhase = Math.random() * Math.PI * 2;

    const measure = () => {
      const rect = node.getBoundingClientRect();
      docTop = rect.top + (window.scrollY || 0);
      layerHeight = rect.height;
    };
    measure();

    const unsubscribe = subscribe((s) => {
      if (!s.motionAllowed) {
        node.style.transform = "translate3d(0,0,0)";
        return;
      }
      // Off-screen: leave the layer alone rather than transforming it.
      const layerCentre = docTop + layerHeight / 2;
      const viewCentre = s.scrollY + s.viewportHeight / 2;
      if (Math.abs(viewCentre - layerCentre) > s.viewportHeight * 1.8) return;

      const scrollOffset = (s.smoothed - baseline) * (depth / 100);
      const pointerOffsetX = s.pointerX * pointer;
      const pointerOffsetY = s.pointerY * pointer;
      const idleOffset = idle ? Math.sin(idlePhase + s.smoothed / 320) * idle : 0;
      node.style.transform =
        `translate3d(${pointerOffsetX.toFixed(2)}px, ${(scrollOffset + pointerOffsetY + idleOffset).toFixed(2)}px, 0)`;
    });

    const remeasure = () => measure();
    window.addEventListener("resize", remeasure);

    return () => {
      unsubscribe();
      window.removeEventListener("resize", remeasure);
      node.style.transform = "";
    };
  }, [depth, pointer, idle, disabled]);

  return ref;
}

/** Adds `is-in` to the node the first time it enters the viewport. Reveals are pure CSS from there. */
export function useReveal<T extends Element>(rootMargin = "0px 0px -12% 0px"): RefObject<T | null> {
  const ref = useRef<T | null>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    // No observer support (or reduced motion): reveal immediately rather than hiding content.
    if (typeof IntersectionObserver === "undefined" || reducedMotion) {
      node.classList.add("is-in");
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            observer.unobserve(entry.target);
          }
        }
      },
      { rootMargin, threshold: 0.15 },
    );
    observer.observe(node);

    // Safety sweep. A fast scroll, an anchor jump, a restored scroll position or the End key can
    // carry the viewport past this element without it ever intersecting — and then it would stay
    // invisible for the rest of the visit. Anything at or above the fold line is content the
    // visitor has arrived at, so reveal it after the scrolling settles.
    let timer = 0;
    const sweep = () => {
      if (node.getBoundingClientRect().top < window.innerHeight * 0.9) {
        node.classList.add("is-in");
        observer.disconnect();
        window.removeEventListener("scroll", onScroll);
        window.removeEventListener("resize", onScroll);
      }
    };
    const onScroll = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(sweep, 140);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });

    return () => {
      window.clearTimeout(timer);
      observer.disconnect();
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, [rootMargin]);

  return ref;
}

/** Progress of an element through the viewport: 0 when its top reaches the bottom, 1 at the top. */
export function useElementProgress<T extends Element>(
  onProgress?: (progress: number) => void,
): RefObject<T | null> {
  const ref = useRef<T | null>(null);
  const callback = useRef(onProgress);
  callback.current = onProgress;

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    let top = 0;
    let height = 0;

    const measure = () => {
      const rect = node.getBoundingClientRect();
      top = rect.top + state.scrollY;
      height = rect.height;
    };
    measure();

    const unsubscribe = subscribe((s) => {
      const travelled = s.smoothed + s.viewportHeight - top;
      const span = height + s.viewportHeight;
      const progress = span > 0 ? Math.min(1, Math.max(0, travelled / span)) : 0;
      callback.current?.(progress);
    });

    window.addEventListener("resize", measure);
    return () => {
      unsubscribe();
      window.removeEventListener("resize", measure);
    };
  }, []);

  return ref;
}

/**
 * Counts up to `value` when the node enters view.
 *
 * The server renders the FINAL value, so the real number is always in the HTML — for crawlers, for
 * social previews, and for a visitor whose JS never runs. The count-up is an enhancement armed at
 * hydration, not the source of the number.
 */
export function useCountUp<T extends Element = HTMLElement>(
  value: number,
  durationMs = 1100,
): { ref: RefObject<T | null>; display: string } {
  const ref = useRef<T | null>(null);
  const [display, setDisplay] = useState(() => formatCount(value, value));

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    // No animation available: leave the server-rendered final value in place.
    if (reducedMotion || typeof IntersectionObserver === "undefined") {
      setDisplay(formatCount(value, value));
      return;
    }

    let raf = 0;
    const startCount = () => {
      const start = performance.now();
      const tick = (now: number) => {
        const t = Math.min(1, (now - start) / durationMs);
        const eased = 1 - Math.pow(1 - t, 3);
        setDisplay(formatCount(value * eased, value));
        if (t < 1) raf = requestAnimationFrame(tick);
      };
      raf = requestAnimationFrame(tick);
    };

    // Already on screen: start from zero so the count is visible from the beginning.
    const rect = node.getBoundingClientRect();
    const onScreen = rect.top < window.innerHeight && rect.bottom > 0;
    if (onScreen) {
      setDisplay(formatCount(0, value));
      startCount();
      return () => cancelAnimationFrame(raf);
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries.some((e) => e.isIntersecting)) return;
        observer.disconnect();
        setDisplay(formatCount(0, value));
        startCount();
      },
      { threshold: 0.4 },
    );
    observer.observe(node);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(raf);
    };
  }, [value, durationMs]);

  return { ref, display };
}

function formatCount(current: number, target: number): string {
  // Preserve the target's precision so the animation can never invent a more precise number.
  const decimals = Number.isInteger(target) ? 0 : (String(target).split(".")[1]?.length ?? 0);
  const rounded = decimals === 0 ? Math.round(current) : Number(current.toFixed(decimals));
  return rounded.toLocaleString("en-GB", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}
