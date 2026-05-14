/**
 * Step 3 / action button.
 *
 * Disabled until all required inputs are valid. While loading, shows a
 * spinner and a small "this can take up to a minute on large designs"
 * note so the user knows it's not frozen.
 */
export default function ConvertButton({ canConvert, isLoading, onConvert }) {
  return (
    <div className="flex flex-col items-center gap-3 py-4">
      <button
        type="button"
        onClick={onConvert}
        disabled={!canConvert || isLoading}
        className="btn-primary text-base min-w-64"
        aria-busy={isLoading}
      >
        {isLoading ? (
          <>
            <Spinner />
            <span>Converting</span>
          </>
        ) : (
          <>
            <span>Convert to jacquard BMPs</span>
            <Arrow />
          </>
        )}
      </button>
      {isLoading && (
        <p className="text-xs text-ink-500 font-mono">
          This can take up to a minute on large designs.
        </p>
      )}
    </div>
  );
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
      <path
        d="M21 12a9 9 0 11-6.219-8.56"
        strokeLinecap="round"
      />
    </svg>
  );
}

function Arrow() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M5 12h14M13 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
