/**
 * Formats a score from [0.0, 1.0] to a percentage string (e.g. "94%").
 * Also clamps the score so it does not exceed 1.0 or fall below 0.0.
 *
 * @param {number} score 
 * @returns {string} Formatted percentage
 */
export function formatScore(score) {
  if (score == null || isNaN(score)) return "0%";
  
  // Clamp score between 0 and 1
  const clampedScore = Math.min(Math.max(score, 0), 1);
  
  // Convert to percentage and round to nearest integer
  const percentage = Math.round(clampedScore * 100);
  
  return `${percentage}%`;
}

/**
 * Formats seconds into MM:SS or HH:MM:SS string.
 *
 * @param {number} seconds 
 * @returns {string} Formatted time string
 */
export function formatTimestamp(seconds) {
  if (seconds == null || isNaN(seconds)) return "00:00";
  
  const totalSeconds = Math.floor(seconds);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const secs = totalSeconds % 60;
  
  const paddedMinutes = String(minutes).padStart(2, '0');
  const paddedSeconds = String(secs).padStart(2, '0');
  
  if (hours > 0) {
    const paddedHours = String(hours).padStart(2, '0');
    return `${paddedHours}:${paddedMinutes}:${paddedSeconds}`;
  }
  
  return `${paddedMinutes}:${paddedSeconds}`;
}
