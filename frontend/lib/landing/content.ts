/**
 * Landing page copy and structure. All wording lives here so it can be reviewed without touching
 * components, and so no component ever invents a claim.
 *
 * NUMBERS ARE NOT WRITTEN HERE. Anything quantitative comes from `shake-lab.json`, which is
 * generated from the shipped model bundle by `scripts/generate_shake_lab.py`. If you need a new
 * figure on the page, add it to the generator.
 */

export type ArchetypeKey = "mud_stone" | "brick_cement" | "timber_bamboo" | "engineered_rc";

export const META = {
  title: "ResilienceAI — earthquake risk screening for buildings",
  description:
    "Answer a handful of questions about a building and get a damage estimate, the shaking it faces, " +
    "and the retrofits that would help most. Built for Myanmar.",
};

export const HERO = {
  eyebrow: "Earthquake risk screening · Myanmar",
  headline: ["See what an earthquake", "would do to your building."],
  // Kept short: this is the one paragraph a visitor reads before scrolling.
  lede:
    "Describe the building — floors, age, materials, the ground it stands on — and ResilienceAI " +
    "estimates how it would perform when the shaking comes, then tells you which fixes would help most.",
  primaryCta: { label: "Screen a building", href: "/form" },
  secondaryCta: { label: "How it works", href: "#descent" },
  scrollCue: "Scroll",
  resume: {
    title: "Continue where you left off",
    body: "You have a saved screening. Jump straight back to it, or start a new one.",
    cta: "Open my last screening",
    fresh: "Start a new screening",
  },
  trace: {
    // aria description for the drawn seismograph; the mark itself is decorative
    label: "Illustrative seismograph trace",
  },
} as const;

/**
 * The descent: what the engine actually measures, told as strata. Each horizon names its own data
 * source so the page can be audited rather than believed.
 */
export const DESCENT = {
  eyebrow: "Beneath the building",
  title: "Five things decide whether a building survives.",
  lede:
    "ResilienceAI reads them in order — from the fault that will move, to the ground that will " +
    "carry the shaking, to the building standing on it. Keep scrolling to go down.",
  horizons: [
    {
      id: "fault",
      index: "01",
      depth: "0 km",
      title: "The fault",
      body:
        "Where the ground will actually break. Distance to a mapped active fault is the first number " +
        "in the assessment — close faults mean harder shaking for the same earthquake.",
      source: "Active fault traces",
    },
    {
      id: "history",
      index: "02",
      depth: "50 yr",
      title: "The record",
      body:
        "What this exact coordinate has already felt. The engine queries the earthquake catalogue " +
        "around the site and identifies the event that governs the shaking there now.",
      source: "USGS earthquake catalogue",
    },
    {
      id: "soil",
      index: "03",
      depth: "30 cm",
      title: "The ground",
      body:
        "Soft soil amplifies shaking; loose saturated sand can liquefy and take the foundation with " +
        "it. Soil texture and a liquefaction screen come from the ground itself.",
      source: "SoilGrids soil texture",
    },
    {
      id: "shaking",
      index: "04",
      depth: "→ MMI",
      title: "The shaking",
      body:
        "Fault, record and soil combine into the site's expected ground motion — peak acceleration " +
        "and intensity on the MMI scale. This is the demand the building has to meet.",
      source: "Attenuation model + intensity conversion",
    },
    {
      id: "building",
      index: "05",
      depth: "1–5",
      title: "The building",
      body:
        "Finally the structure itself: what it is made of, how it was built, how it has aged. The " +
        "damage model returns a full distribution over five damage grades, not a single score.",
      source: "Damage model, trained on the 2015 Nepal building survey",
    },
  ],
} as const;

export const SHAKE_LAB = {
  eyebrow: "Shake it",
  title: "Move the fault. Watch the building answer.",
  lede:
    "This is the real model, not an animation of one. Pick a building type, set how far away the " +
    "fault is, and set the earthquake's size — the estimate below is what the deployed model returns.",
  controls: {
    archetype: "Building type",
    distance: "Distance to the fault",
    magnitude: "Earthquake magnitude",
    pause: "Pause motion",
    resume: "Resume motion",
  },
  panels: {
    hazard: "The shaking at the site",
    damage: "Damage expected in this building",
  },
  /** Shown verbatim under the controls — the honesty line for this section. */
  caveat:
    "Distances and magnitudes are rounded to the nearest modelled value. The damage model conditions " +
    "on distance to the governing event, so magnitude moves the shaking panel and not the damage " +
    "panel — that separation is how the pipeline actually works.",
  cta: "Screen a real building",
} as const;

export const EVIDENCE = {
  eyebrow: "The measured truth",
  title: "What this model is, and what it is not.",
  lede:
    "We would rather you trust it for the right reasons. Every number here is from a held-out run of " +
    "the model that ships.",
  limitations: [
    "Trained on one earthquake — the 2015 Gorkha survey in Nepal, 11 districts. It screens buildings " +
      "that resemble that building stock, and Myanmar's mid-rise concrete frames are barely in it.",
    "It is a screening ranker, not a grader. On districts it has never seen, absolute accuracy falls " +
      "well below the same-district figure; the ranking of buildings stays useful, the exact grade does not.",
    "Weakly shaken sites are outside its training range: every training building was strongly shaken, " +
      "so a very low-hazard site should be read with caution.",
  ],
  /** Labels for the stat tiles; values come from shake-lab.json → model_facts. */
  stats: {
    buildings: "Buildings in the training survey",
    features: "Inputs the model reads",
    crossDistrict: "Accuracy on unseen districts",
    adjacent: "Predictions within one grade",
  },
} as const;

export const MYANMAR = {
  eyebrow: "Built for Myanmar",
  title: "The ground here moves.",
  body:
    "Myanmar sits on one of the world's most active strike-slip systems. The Sagaing Fault runs the " +
    "length of the country, and in March 2025 a M7.7 rupture near Mandalay put it back in the news. " +
    "Most buildings at risk were never engineered for it — which is exactly why screening matters " +
    "more here than precision does.",
  workedExample: {
    label: "Worked example in the app",
    place: "Mandalay, 21.9769 N 96.0836 E",
    note: "A three-storey mud-mortar stone building in the current catalogue, scored against the " +
      "site's governing event.",
    cta: "See the assessment breakdown",
  },
} as const;

export const HOW_IT_WORKS = {
  eyebrow: "Under the bonnet",
  title: "How an assessment is built.",
  steps: [
    { index: "1", title: "Hazard engine", body: "Fault proximity, catalogue history, soil and the resulting ground motion for the coordinate." },
    { index: "2", title: "Governing event", body: "The engine reports which catalogued earthquake drives the shaking, and how far away it was." },
    { index: "3", title: "Damage model", body: "An ordinal model over grades 1–5 reads the building and the event distance, and returns a distribution." },
    { index: "4", title: "Risk", body: "Hazard and vulnerability combine into one expected-damage score, with the uncertainty kept visible." },
    { index: "5", title: "Retrieval", body: "Relevant guidance is retrieved from a curated knowledge base with citations attached." },
    { index: "6", title: "Saved", body: "The whole assessment is stored against your account so buildings can be compared over time." },
  ],
} as const;

export const FINALE = {
  title: "Screen a building in about a minute.",
  body:
    "No survey equipment, no engineer on site. Enough questions to know where to look first — and " +
    "what to fix before the ground moves again.",
  primaryCta: { label: "Start an assessment", href: "/form" },
  secondaryCta: { label: "Browse saved assessments", href: "/assessments" },
  signUpCta: { label: "Create an account", href: "/register" },
} as const;

export const FOOTER = {
  wordmark: "CODETRIO · STIMU",
  line: "ResilienceAI — earthquake risk screening for buildings.",
  credits: [
    "Hazard inputs: USGS earthquake catalogue, SoilGrids, mapped active faults",
    // The building count is deliberately not repeated here — it is generated into the evidence
    // section from the model artifact, so it is stated once and cannot drift.
    "Damage model: ordinal XGBoost trained on the 2015 Nepal Building Structure Survey",
    "Screening tool only — not a substitute for a structural engineer's assessment",
  ],
} as const;
