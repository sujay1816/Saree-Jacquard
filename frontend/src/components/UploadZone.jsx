import { useCallback, useRef, useState } from 'react';
import { LIMITS, validateImageFile } from '../utils/validators';

/**
 * Step 2: drag-drop or click to upload a saree image. Disabled until
 * Step 1 (loom setup) is complete.
 */
export default function UploadZone({ file, preview, onSelect, disabled, locked, lockedReason }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState(null);

  const handleFile = useCallback(
    (f) => {
      const err = validateImageFile(f);
      if (err) {
        setError(err);
        return;
      }
      setError(null);

      // Generate preview URL
      const url = URL.createObjectURL(f);
      // Also probe the image to check its actual pixel dimensions
      const img = new Image();
      img.onload = () => {
        const shortEdge = Math.min(img.width, img.height);
        if (shortEdge < LIMITS.MIN_IMAGE_SHORT_EDGE) {
          setError(
            `Image is only ${shortEdge}px on its shortest side. ` +
              `Upload at least ${LIMITS.MIN_IMAGE_SHORT_EDGE}px wide for usable detail.`
          );
          URL.revokeObjectURL(url);
          onSelect(null, null, null);
          return;
        }
        onSelect(f, url, { width: img.width, height: img.height });
      };
      img.onerror = () => {
        setError('Could not read this image. It may be corrupt.');
        URL.revokeObjectURL(url);
      };
      img.src = url;
    },
    [onSelect]
  );

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    if (disabled || locked) return;
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) handleFile(dropped);
  };

  const onDragOver = (e) => {
    e.preventDefault();
    if (disabled || locked) return;
    setDragging(true);
  };

  const onDragLeave = () => setDragging(false);

  const onPickClick = () => {
    if (disabled || locked) return;
    inputRef.current?.click();
  };

  const onInputChange = (e) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
    // Reset so the same file can be re-uploaded
    e.target.value = '';
  };

  const reallyDisabled = disabled || locked;

  return (
    <section className="panel p-6">
      <header className="mb-5">
        <p className="panel-label mb-1">Step 2</p>
        <h2 className="text-2xl font-semibold">Upload saree image</h2>
        <p className="text-sm text-ink-600 mt-1">
          Drag and drop or click to browse. JPG, PNG, or WEBP. Minimum{' '}
          {LIMITS.MIN_IMAGE_SHORT_EDGE}px on the shortest side.
        </p>
      </header>

      <div
        onClick={onPickClick}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        role="button"
        tabIndex={reallyDisabled ? -1 : 0}
        onKeyDown={(e) => {
          if (!reallyDisabled && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            onPickClick();
          }
        }}
        aria-disabled={reallyDisabled}
        className={`
          relative rounded border-2 border-dashed transition-all
          ${
            reallyDisabled
              ? 'border-ink-700/15 bg-cream-100/30 cursor-not-allowed'
              : dragging
              ? 'border-ink-900 bg-cream-100 cursor-copy'
              : 'border-ink-700/30 hover:border-ink-700/60 hover:bg-cream-100/50 cursor-pointer'
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept={LIMITS.ALLOWED_EXTENSIONS.join(',')}
          onChange={onInputChange}
          className="sr-only"
          disabled={reallyDisabled}
        />

        {preview ? (
          <div className="p-4 flex items-center gap-4">
            <img
              src={preview}
              alt="Uploaded saree"
              className="w-32 h-32 object-cover rounded border border-ink-700/15"
            />
            <div className="flex-1 min-w-0">
              <p className="font-mono text-sm text-ink-900 truncate">
                {file?.name}
              </p>
              <p className="font-mono text-xs text-ink-500 mt-0.5">
                {file && (file.size / 1024).toFixed(0)} KB
              </p>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onSelect(null, null, null);
                  setError(null);
                }}
                className="mt-2 text-xs text-ink-600 hover:text-madder-600 underline underline-offset-2"
                disabled={reallyDisabled}
              >
                Remove and re-upload
              </button>
            </div>
          </div>
        ) : (
          <div className="p-10 text-center">
            <div className="inline-block mb-3 text-ink-500">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <p className="text-ink-700">
              {locked
                ? lockedReason || 'Complete Step 1 first'
                : dragging
                ? 'Drop the image here'
                : 'Drop a saree image, or click to browse'}
            </p>
            <p className="font-mono text-xs text-ink-500 mt-1">
              JPG · PNG · WEBP
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 px-3 py-2 bg-madder-500/8 border border-madder-500/30 rounded text-sm text-madder-700">
          {error}
        </div>
      )}
    </section>
  );
}
