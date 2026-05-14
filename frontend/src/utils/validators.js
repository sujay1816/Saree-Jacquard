/**
 * Client-side validators. Backend re-validates everything; these just give
 * faster feedback before submission.
 */

export const LIMITS = {
  MIN_PINS: 1,
  MAX_PINS: 10_000,
  MIN_CARDS: 1,
  MAX_CARDS: 10_000,
  MIN_SHUTTLES: 2,
  MAX_SHUTTLES: 8,
  MIN_IMAGE_SHORT_EDGE: 500,
  ALLOWED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.webp'],
  MAX_UPLOAD_BYTES: 50 * 1024 * 1024,
};

export function validatePins(value) {
  const n = Number(value);
  if (!Number.isFinite(n) || !Number.isInteger(n)) {
    return 'Pins must be a whole number.';
  }
  if (n < LIMITS.MIN_PINS || n > LIMITS.MAX_PINS) {
    return `Pins must be between ${LIMITS.MIN_PINS} and ${LIMITS.MAX_PINS.toLocaleString()}.`;
  }
  return null;
}

export function validateCards(value) {
  const n = Number(value);
  if (!Number.isFinite(n) || !Number.isInteger(n)) {
    return 'Cards must be a whole number.';
  }
  if (n < LIMITS.MIN_CARDS || n > LIMITS.MAX_CARDS) {
    return `Cards must be between ${LIMITS.MIN_CARDS} and ${LIMITS.MAX_CARDS.toLocaleString()}.`;
  }
  return null;
}

export function validateImageFile(file) {
  if (!file) return 'No file selected.';

  const name = file.name.toLowerCase();
  const hasValidExt = LIMITS.ALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext));
  if (!hasValidExt) {
    return `Unsupported file type. Use ${LIMITS.ALLOWED_EXTENSIONS.join(', ')}.`;
  }
  if (file.size > LIMITS.MAX_UPLOAD_BYTES) {
    const mb = (file.size / 1024 / 1024).toFixed(1);
    const maxMb = LIMITS.MAX_UPLOAD_BYTES / 1024 / 1024;
    return `File is ${mb} MB. Maximum is ${maxMb} MB.`;
  }
  return null;
}

/**
 * Sanitize a user-supplied filename to keep it filesystem-safe.
 * Matches the backend's _sanitize_filename rules.
 */
export function sanitizeFilename(name) {
  if (!name) return '';
  const bad = /[\/\\"':*?<>|]/g;
  return name
    .replace(/\s+/g, '_')
    .replace(bad, '')
    .replace(/^[._]+|[._]+$/g, '')
    .toLowerCase()
    .slice(0, 64);
}
