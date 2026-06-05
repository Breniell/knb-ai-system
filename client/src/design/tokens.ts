// KNB design tokens — refined editorial light theme.
export const KNB = {
  paper: "#FBFAF7", surface: "#FFFFFF", surface2: "#F4F2EC",
  line: "#E6E3DA", ink: "#1B1A16", muted: "#6E6B61", faint: "#9A968A",
  brand: "#0E7C66", brandSoft: "#129E76", clay: "#D08A3C",
} as const;

export type Pole = "Business" | "Technique" | "Créatif" | "Coordination" | "Veille";

export const POLE_STYLE: Record<Pole, { chip: string; dot: string; ring: string }> = {
  Business:     { chip: "text-info border-info/25 bg-info/[0.08]",            dot: "bg-info",      ring: "text-info bg-info/10 ring-info/15" },
  Technique:    { chip: "text-brand-700 border-brand-600/25 bg-brand-600/[0.08]", dot: "bg-brand-600", ring: "text-brand-700 bg-brand-600/10 ring-brand-600/20" },
  "Créatif":    { chip: "text-clay-700 border-clay-500/30 bg-clay-500/10",    dot: "bg-clay-500",  ring: "text-clay-700 bg-clay-500/12 ring-clay-500/25" },
  Coordination: { chip: "text-[#7A5AA8] border-[#7A5AA8]/25 bg-[#7A5AA8]/[0.08]", dot: "bg-[#7A5AA8]", ring: "text-[#7A5AA8] bg-[#7A5AA8]/10 ring-[#7A5AA8]/20" },
  Veille:       { chip: "text-muted border-line-strong bg-surface-2",         dot: "bg-faint",     ring: "text-muted bg-surface-2 ring-line" },
};
