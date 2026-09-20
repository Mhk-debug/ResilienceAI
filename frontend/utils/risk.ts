/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * Composite risk, model v3.
 *
 * The damage model is now conditioned on the site's shaking, so the old
 * `hazard*0.6 + (100 - resilience)*0.4` counted shaking twice: the hazard score already expresses
 * how violent the shaking at the site can be. The replacement keeps both terms but composes them
 * the way a risk statement should read:
 *
 *     vulnerability = (expected grade - 1) / 4     0 = no damage expected, 1 = destruction
 *     risk          = (hazard score / 100) * vulnerability * 100
 *
 * hazard         how violent the shaking at this site can be
 * vulnerability  how much damage this building takes when it is shaken
 * risk           the expected damage
 */

/** The model's 0-100 resilience score inverts to an expected damage grade on the 1-5 scale. */
export function expectedGradeFromResilience(resilienceScore: number): number {
    const clamped = Math.min(100, Math.max(0, resilienceScore));
    return 5 - (4 * clamped) / 100;
}

/** Expected damage grade -> damage ratio in [0, 1]. Falls back to the resilience score when the
 *  stored assessment predates the model change and carries no expected grade. */
export function calculateVulnerability(
    expectedGrade?: number | null,
    resilienceScore?: number | null,
): number {
    const grade =
        expectedGrade ??
        (resilienceScore !== undefined && resilienceScore !== null
            ? expectedGradeFromResilience(resilienceScore)
            : 3);
    return Math.min(1, Math.max(0, (grade - 1) / 4));
}

/**
 * Composite risk score: (hazard / 100) * vulnerability * 100, clamped to 0-100.
 *
 * Prefer passing `expectedGrade` (from the assessment's `building.expected_grade`); pass the
 * resilience score as the third argument for assessments saved before model v3.
 */
export function calculateRiskScore(
    hazardScore: number,
    expectedGrade?: number | null,
    resilienceScore?: number | null,
): number {
    const vulnerability = calculateVulnerability(expectedGrade, resilienceScore);
    const score = (Math.min(100, Math.max(0, hazardScore)) / 100) * vulnerability * 100;
    return Math.round(Math.min(100, Math.max(0, score)));
}

/**
 * Categorizes risk scores into Low, Moderate, High, or Critical.
 *
 * Band edges are the vulnerability thresholds for *minor / moderate / severe* expected damage
 * (0.25 / 0.50 / 0.75 on the damage ratio) scaled by a reference hazard score of 60, i.e. 15 / 30 /
 * 45. They are deliberately not population terciles: the training population is a strongly shaken,
 * heavily damaged one (median vulnerability 0.72), so terciles would put almost every realistic
 * assessment in the top band and the label would stop carrying information.
 */
export type RiskLevel = 'Low' | 'Moderate' | 'High' | 'Critical';

export function getRiskLevel(riskScore: number): RiskLevel {
    if (riskScore <= 15) return 'Low';
    if (riskScore <= 30) return 'Moderate';
    if (riskScore <= 45) return 'High';
    return 'Critical';
}

/**
 * Gets the color hexes or Tailwind classes associated with risk levels.
 */
export function getRiskColorClasses(level: RiskLevel): {
    text: string;
    bg: string;
    border: string;
    indicator: string;
} {
    switch (level) {
        case 'Low':
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
        case 'High':
            return {
                text: 'text-orange-700',
                bg: 'bg-orange-50',
                border: 'border-orange-200',
                indicator: 'bg-orange-500',
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
