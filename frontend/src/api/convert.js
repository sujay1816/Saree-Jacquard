/**
 * API client for the conversion backend.
 *
 * The backend URL is read from VITE_API_URL at build time. For local dev,
 * set this in frontend/.env. For production, set it in the Vercel project
 * Environment Variables UI.
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * POST /api/convert with the image + settings.
 *
 * Returns: { zipBlob, metadata } on success.
 * Throws: { message, suggestion } on validation/conversion failure.
 */
export async function convertImage({
  imageFile,
  pins,
  cards,
  shuttles,
  shuttleFilenames, // optional array of strings
}) {
  const form = new FormData();
  form.append('image', imageFile);
  form.append('pins', String(pins));
  form.append('cards', String(cards));
  form.append('shuttles', String(shuttles));
  if (shuttleFilenames && shuttleFilenames.length) {
    form.append('shuttle_filenames', JSON.stringify(shuttleFilenames));
  }

  // 130s client timeout (slightly higher than server's 120s cap)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 130_000);

  let response;
  try {
    response = await fetch(`${API_URL}/api/convert`, {
      method: 'POST',
      body: form,
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw {
        message: 'Conversion timed out after 130 seconds.',
        suggestion: 'Try smaller pins/cards or fewer shuttles.',
      };
    }
    throw {
      message: 'Could not reach the conversion server.',
      suggestion:
        'Check that the backend is running and that VITE_API_URL is set correctly.',
    };
  }
  clearTimeout(timeoutId);

  if (!response.ok) {
    // Backend returns { detail: { error, suggestion } } on 422/500
    let errBody;
    try {
      errBody = await response.json();
    } catch {
      errBody = null;
    }
    const detail = errBody?.detail || {};
    throw {
      message: detail.error || `Server returned ${response.status}.`,
      suggestion: detail.suggestion || '',
    };
  }

  // Success: response body is the zip; metadata is in an X-header.
  const metadataHeader = response.headers.get('X-Palette-Metadata');
  let metadata = null;
  if (metadataHeader) {
    try {
      metadata = JSON.parse(metadataHeader);
    } catch (e) {
      console.warn('Could not parse palette metadata header', e);
    }
  }

  const zipBlob = await response.blob();
  return { zipBlob, metadata };
}

/**
 * Trigger a browser download for a Blob.
 */
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  // Defer revoke so Safari doesn't drop the download
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
