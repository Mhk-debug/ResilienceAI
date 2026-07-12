/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * Calculates risk score based on hazard and resilience scores.
 * riskScore = (hazard_score * 0.6) + ((100 - resilience_score) * 0.4)
 */
export function calculateRiskScore(hazardScore: number, resilienceScore: number): number {
  const score = (hazardScore * 0.6) + ((100 - resilienceScore) * 0.4);
  return Math.min(100, Math.max(0, Math.round(score)));
}

/**
 * Categorizes risk scores into Safe, Moderate, or Critical categories.
 */
export function getRiskLevel(riskScore: number): 'Safe' | 'Moderate' | 'Critical' {
  if (riskScore <= 33) return 'Safe';
  if (riskScore <= 66) return 'Moderate';
  return 'Critical';
}

/**
 * Gets the color hexes or Tailwind classes associated with risk levels.
 */
export function getRiskColorClasses(level: 'Safe' | 'Moderate' | 'Critical'): {
  text: string;
  bg: string;
  border: string;
  indicator: string;
} {
  switch (level) {
    case 'Safe':
      return {
        text: 'text-emerald-700',
        bg: 'bg-emerald-50',
        border: 'border-emerald-200',
        indicator: 'bg-emerald-500',
      };
    case 'Moderate':
      return {
        text: 'text-amber-700',
        bg: 'bg-amber-50',
        border: 'border-amber-200',
        indicator: 'bg-amber-500',
      };
    case 'Critical':
      return {
        text: 'text-rose-700',
        bg: 'bg-rose-50',
        border: 'border-rose-200',
        indicator: 'bg-rose-500',
      };
  }
}
