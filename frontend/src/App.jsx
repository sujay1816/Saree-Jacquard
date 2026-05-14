import { useEffect, useMemo, useState } from 'react';
import LoomSetup from './components/LoomSetup';
import UploadZone from './components/UploadZone';
import ExportSettings from './components/ExportSettings';
import ConvertButton from './components/ConvertButton';
import PalettePreview from './components/PalettePreview';
import ResultPanel from './components/ResultPanel';
import DownloadButton from './components/DownloadButton';
import { convertImage } from './api/convert';
import {
  validatePins,
  validateCards,
  validateImageFile,
  sanitizeFilename,
  LIMITS,
} from './utils/validators';

export default function App() {
  // ---- Step 1: loom setup ----
  const [pins, setPins] = useState('');
  const [cards, setCards] = useState('');
  const [shuttles, setShuttles] = useState(null);

  // ---- Step 2: upload ----
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [imageDims, setImageDims] = useState(null);

  // ---- Export settings ----
  const [motifCleanup, setMotifCleanup] = useState(false);
  const [motifMinSize, setMotifMinSize] = useState(2);

  // ---- Conversion state ----
  const [isLoading, setIsLoading] = useState(false);
  const [isReExporting, setIsReExporting] = useState(false);
  const [serverError, setServerError] = useState(null);

  // ---- Result ----
  const [zipBlob, setZipBlob] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [shuttleNames, setShuttleNames] = useState([]);
  const [defaultShuttleNames, setDefaultShuttleNames] = useState([]);

  // Clean up object URLs on unmount
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- Step 1 completion check ----
  const step1Complete = useMemo(() => {
    return (
      pins !== '' &&
      cards !== '' &&
      validatePins(pins) === null &&
      validateCards(cards) === null &&
      shuttles !== null
    );
  }, [pins, cards, shuttles]);

  // ---- Step 2 completion check ----
  const step2Complete = useMemo(() => {
    return file !== null && validateImageFile(file) === null;
  }, [file]);

  const canConvert = step1Complete && step2Complete && !isLoading;

  // ---- Setup handlers ----
  function onSetupChange(patch) {
    if (patch.pins !== undefined) setPins(patch.pins);
    if (patch.cards !== undefined) setCards(patch.cards);
    if (patch.shuttles !== undefined) setShuttles(patch.shuttles);
    // Any setup change invalidates a previous conversion
    if (zipBlob) {
      setZipBlob(null);
      setMetadata(null);
      setShuttleNames([]);
      setDefaultShuttleNames([]);
    }
  }

  function onFileSelect(f, url, dims) {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(f);
    setPreviewUrl(url);
    setImageDims(dims);
    // Reset prior conversion since the source image changed
    setZipBlob(null);
    setMetadata(null);
    setShuttleNames([]);
    setDefaultShuttleNames([]);
    setServerError(null);
  }

  function onExportChange(patch) {
    if (patch.motifCleanup !== undefined) setMotifCleanup(patch.motifCleanup);
    if (patch.motifMinSize !== undefined) setMotifMinSize(patch.motifMinSize);
  }

  function onShuttleRename(idx, value) {
    setShuttleNames((prev) => {
      const next = [...prev];
      next[idx] = value;
      return next;
    });
  }

  async function runConvert() {
    if (!canConvert) return;
    setIsLoading(true);
    setServerError(null);
    setZipBlob(null);
    setMetadata(null);

    try {
      const { zipBlob: blob, metadata: meta } = await convertImage({
        imageFile: file,
        pins: Number(pins),
        cards: Number(cards),
        shuttles,
        motifCleanup,
        motifMinSize,
        // No filename overrides on first pass; user renames after seeing palette
        shuttleFilenames: null,
      });
      setZipBlob(blob);
      setMetadata(meta);
      const defaults = (meta?.shuttles ?? []).map((s) => s.name);
      setDefaultShuttleNames(defaults);
      setShuttleNames(defaults);
    } catch (err) {
      console.error('Conversion failed:', err);
      setServerError(err);
    } finally {
      setIsLoading(false);
    }
  }

  async function reExportWithRenames() {
    if (!file || !metadata) return;
    setIsReExporting(true);
    setServerError(null);

    try {
      const cleanedNames = shuttleNames.map((n) => sanitizeFilename(n) || 'shuttle');
      const { zipBlob: blob, metadata: meta } = await convertImage({
        imageFile: file,
        pins: Number(pins),
        cards: Number(cards),
        shuttles,
        motifCleanup,
        motifMinSize,
        shuttleFilenames: cleanedNames,
      });
      // Trigger download immediately
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'jacquard-output.zip';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      // Update displayed metadata names too
      setMetadata(meta);
      const defaults = (meta?.shuttles ?? []).map((s) => s.name);
      setDefaultShuttleNames(defaults);
    } catch (err) {
      console.error('Re-export failed:', err);
      setServerError(err);
    } finally {
      setIsReExporting(false);
    }
  }

  const hasRenames =
    shuttleNames.length > 0 &&
    defaultShuttleNames.length > 0 &&
    shuttleNames.some((n, i) => sanitizeFilename(n) !== sanitizeFilename(defaultShuttleNames[i]));

  return (
    <div className="min-h-screen px-4 py-10 sm:py-14">
      <div className="max-w-4xl mx-auto">
        <Header />

        <div className="space-y-6">
          <LoomSetup
            pins={pins}
            cards={cards}
            shuttles={shuttles}
            onChange={onSetupChange}
            disabled={isLoading}
          />

          <UploadZone
            file={file}
            preview={previewUrl}
            onSelect={onFileSelect}
            disabled={isLoading}
            locked={!step1Complete}
            lockedReason="Enter pins, cards, and shuttle count first"
          />

          <ExportSettings
            motifCleanup={motifCleanup}
            motifMinSize={motifMinSize}
            onChange={onExportChange}
            disabled={isLoading}
          />

          <ConvertButton
            canConvert={canConvert}
            isLoading={isLoading}
            onConvert={runConvert}
          />

          {serverError && (
            <div className="panel p-4 border-madder-500/40 bg-madder-500/5">
              <p className="font-medium text-madder-700">{serverError.message}</p>
              {serverError.suggestion && (
                <p className="text-sm text-ink-700 mt-1">{serverError.suggestion}</p>
              )}
            </div>
          )}

          {zipBlob && metadata && (
            <>
              <PalettePreview
                metadata={metadata}
                shuttleNames={shuttleNames}
                onRename={onShuttleRename}
              />

              <ResultPanel
                originalPreviewUrl={previewUrl}
                zipBlob={zipBlob}
                metadata={metadata}
                shuttleNames={shuttleNames}
              />

              <DownloadButton
                zipBlob={zipBlob}
                hasRenames={hasRenames}
                onReExportWithRenames={reExportWithRenames}
                isReExporting={isReExporting}
              />
            </>
          )}
        </div>

        <Footer />
      </div>
    </div>
  );
}

function Header() {
  return (
    <header className="mb-10 sm:mb-14">
      <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-ink-500 mb-3">
        Saree → Jacquard
      </p>
      <h1 className="text-4xl sm:text-5xl font-semibold leading-[1.05] mb-2">
        Weaving-ready BMPs from any saree image.
      </h1>
      <p className="text-ink-700 max-w-2xl text-base sm:text-lg">
        Upload a close-up of your saree design. Pick the number of shuttles
        and the dimensions of your loom. Get back one 24-bit BMP per thread,
        ready for the jacquard.
      </p>
      <div className="weave-line mt-6 max-w-md" />
    </header>
  );
}

function Footer() {
  return (
    <footer className="mt-20 pt-6 border-t border-ink-700/10">
      <p className="font-mono text-xs text-ink-500">
        24-bit RGB BMP · black = thread active · stretched to exact pins × cards
      </p>
    </footer>
  );
}
