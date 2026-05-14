/**
 * Download button. Re-bundles the zip if the user has renamed shuttles
 * (so the filenames inside the zip reflect their choices).
 *
 * In v1 we keep this simple: if the names match the defaults from the
 * server, we just download the server's zip as-is. If any rename happened,
 * we re-request from the server with the overrides applied (avoids
 * client-side zip rewriting which is fiddly).
 */
export default function DownloadButton({
  zipBlob,
  hasRenames,
  onReExportWithRenames,
  isReExporting,
}) {
  if (!zipBlob) return null;

  function onDownload() {
    if (hasRenames) {
      onReExportWithRenames();
      return;
    }
    triggerDownload(zipBlob, 'jacquard-output.zip');
  }

  return (
    <div className="flex flex-col items-center gap-2 py-2">
      <button
        type="button"
        onClick={onDownload}
        disabled={isReExporting}
        className="btn-primary text-base min-w-64"
      >
        {isReExporting ? (
          <>
            <Spinner />
            <span>Repackaging...</span>
          </>
        ) : (
          <>
            <DownloadIcon />
            <span>Download jacquard-output.zip</span>
          </>
        )}
      </button>
      {hasRenames && !isReExporting && (
        <p className="text-xs text-ink-500 font-mono">
          Filenames will be regenerated with your custom names.
        </p>
      )}
    </div>
  );
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function Spinner() {
  return (
    <svg
      className="animate-spin"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M21 12a9 9 0 11-6.219-8.56" strokeLinecap="round" />
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path
        d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
