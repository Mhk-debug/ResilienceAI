export const BASE_API_URL = "http://127.0.0.1:8000";

export type TailwindBaseColor =
  | 'slate' | 'gray' | 'zinc' | 'neutral' | 'stone'
  | 'red' | 'orange' | 'amber' | 'yellow' | 'lime'
  | 'green' | 'emerald' | 'teal' | 'cyan' | 'sky'
  | 'blue' | 'indigo' | 'violet' | 'purple' | 'fuchsia'
  | 'pink' | 'rose';

export const ColorClasses: Record<TailwindBaseColor, { background: string; border: string; text: string; toggle: string }> = {
  slate: { background: "#f8fafc", border: "#e2e8f0", text: "#0f172a", toggle: "#475569" },
  gray: { background: "#f9fafb", border: "#e5e7eb", text: "#111827", toggle: "#4b5563" },
  zinc: { background: "#fafafa", border: "#e4e4e7", text: "#18181b", toggle: "#52525b" },
  neutral: { background: "#fafafa", border: "#e5e5e5", text: "#171717", toggle: "#525252" },
  stone: { background: "#fafaf9", border: "#e7e5e4", text: "#1c1917", toggle: "#57534e" },
  red: { background: "#fef2f2", border: "#fecaca", text: "#7f1d1d", toggle: "#dc2626" },
  orange: { background: "#fff7ed", border: "#fed7aa", text: "#7c2d12", toggle: "#ea580c" },
  amber: { background: "#fffbeb", border: "#fde68a", text: "#78350f", toggle: "#d97706" },
  yellow: { background: "#fefce8", border: "#fef08a", text: "#713f12", toggle: "#ca8a04" },
  lime: { background: "#f7fee7", border: "#d9f99d", text: "#365314", toggle: "#65a30d" },
  green: { background: "#f0fdf4", border: "#bbf7d0", text: "#14532d", toggle: "#16a34a" },
  emerald: { background: "#ecfdf5", border: "#a7f3d0", text: "#064e3b", toggle: "#059669" },
  teal: { background: "#f0fdfa", border: "#99f6e4", text: "#134e4a", toggle: "#0d9488" },
  cyan: { background: "#ecfeff", border: "#a5f3fc", text: "#164e63", toggle: "#0891b2" },
  sky: { background: "#f0f9ff", border: "#bae6fd", text: "#0c4a6e", toggle: "#0284c7" },
  blue: { background: "#eff6ff", border: "#bfdbfe", text: "#1e3a8a", toggle: "#2563eb" },
  indigo: { background: "#eef2ff", border: "#c7d2fe", text: "#312e81", toggle: "#4f46e5" },
  violet: { background: "#f5f3ff", border: "#ddd6fe", text: "#4c1d95", toggle: "#7c3aed" },
  purple: { background: "#faf5ff", border: "#e9d5ff", text: "#581c87", toggle: "#9333ea" },
  fuchsia: { background: "#fdf4ff", border: "#f5d0fe", text: "#701a75", toggle: "#c026d3" },
  pink: { background: "#fdf2f8", border: "#fbcfe8", text: "#831843", toggle: "#db2777" },
  rose: { background: "#fff1f2", border: "#fecdd3", text: "#881337", toggle: "#e11d48" },
};