import { useEffect, useState } from 'react';
import JSZipReader from '../utils/jszipLite';

/**
 * After conversion: side-by-side comparison and per-shuttle thumbnails.
 *
 * The backend zips up everything, so to show shuttle thumbnails we extract
 * the relevant BMPs in-browser. We use a minimal hand-rolled zip reader
 * (jszipLite) to avoid adding another dependency just for this.
 */
export default function ResultPanel({ originalPreviewUrl, zipBlob, metadata, shuttleNames }) {
  const [extracted, setExtracted] = useState({ previewUrl: null, shuttles: [] });

  useEffect(() => {
    if (!zipBlob || !metadata) return;
    let cancelled = false;
    let createdUrls = [];

    (async () => {
      try {
        const entries = await JSZipReader.read(zipBlob);
        if (cancelled) return;

        let previewUrl = null;
        const shuttles = [];

        for (const entry of entries) {
          if (entry.name === 'preview.png') {
            const blob = new Blob([entry.data], { type: 'image/png' });
            previewUrl = URL.createObjectURL(blob);
            createdUrls.push(previewUrl);
          } else if (entry.name.endsWith('.bmp')) {
            const blob = new Blob([entry.data], { type: 'image/bmp' });
            const url = URL.createObjectURL(blob);
            createdUrls.push(url);
            shuttles.push({ filename: entry.name, url });
          }
        }

        if (!cancelled) {
          setExtracted({ previewUrl, shuttles });
        }
      } catch (err) {
        console.error('Could not extract preview from zip:', err);
      }
    })();

    return () => {
      cancelled = true;
      createdUrls.forEach((u) => URL.revokeObjectURL(u));
    };
  }, [zipBlob, metadata]);

  if (!zipBlob || !metadata) return null;

  return (
    <div className="space-y-6">
      {/* Side-by-side comparison */}
      <section className="panel p-6">
        <header className="mb-4">
          <p className="panel-label mb-1">Comparison</p>
          <h3 className="text-xl font-semibold">Original vs converted</h3>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ComparisonPane label="Original" imageUrl={originalPreviewUrl} />
          <ComparisonPane
            label={`Converted · ${metadata.output_size?.join(' × ') ?? ''}`}
            imageUrl={extracted.previewUrl}
          />
        </div>
      </section>

      {/* Per-shuttle thumbnails */}
      <section className="panel p-6">
        <header className="mb-4">
          <p className="panel-label mb-1">Shuttle BMPs</p>
          <h3 className="text-xl font-semibold">
            {extracted.shuttles.length} thread mask{extracted.shuttles.length !== 1 ? 's' : ''}
          </h3>
          <p className="text-sm text-ink-600 mt-1">
            Each BMP is 24-bit. Black = thread active. These render with
            inverted contrast at thumbnail size.
          </p>
        </header>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {extracted.shuttles.map((s, i) => (
            <ShuttleThumb
              key={s.filename}
              filename={s.filename}
              url={s.url}
              shuttleNumber={metadata.shuttles?.[i]?.shuttle_number}
              swatchColor={metadata.shuttles?.[i]?.hex}
            />
          ))}
        </div>
      </section>
    </div>
  );
}

function ComparisonPane({ label, imageUrl }) {
  return (
    <div>
      <p className="panel-label mb-2">{label}</p>
      <div className="aspect-[2/3] bg-cream-100 border border-ink-700/15 rounded overflow-hidden flex items-center justify-center">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={label}
            className="w-full h-full object-contain"
          />
        ) : (
          <span className="font-mono text-xs text-ink-500">Loading...</span>
        )}
      </div>
    </div>
  );
}

function ShuttleThumb({ filename, url, shuttleNumber, swatchColor }) {
  return (
    <div className="border border-ink-700/15 rounded overflow-hidden bg-white">
      <div className="aspect-[2/3] flex items-center justify-center bg-cream-50">
        {url ? (
          <img src={url} alt={filename} className="w-full h-full object-contain" />
        ) : (
          <span className="font-mono text-xs text-ink-500">…</span>
        )}
      </div>
      <div className="p-2 border-t border-ink-700/10 bg-cream-100/40 flex items-center gap-2">
        {swatchColor && (
          <div
            className="w-3 h-3 rounded-sm border border-ink-700/20"
            style={{ backgroundColor: swatchColor }}
          />
        )}
        <span className="font-mono text-xs text-ink-700 truncate flex-1">
          {filename}
        </span>
        {shuttleNumber !== undefined && (
          <span className="font-mono text-[10px] text-ink-500">
            #{shuttleNumber}
          </span>
        )}
      </div>
    </div>
  );
}
