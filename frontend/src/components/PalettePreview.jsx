import { sanitizeFilename } from '../utils/validators';

/**
 * After conversion: shows the auto-detected palette as color swatches.
 * Each shuttle has an editable filename. The background is shown but not
 * editable (it isn't exported).
 */
export default function PalettePreview({ metadata, shuttleNames, onRename }) {
  if (!metadata) return null;

  const { background, shuttles } = metadata;

  return (
    <section className="panel p-6">
      <header className="mb-4">
        <p className="panel-label mb-1">Palette</p>
        <h3 className="text-xl font-semibold">Detected colors</h3>
        <p className="text-sm text-ink-600 mt-1">
          Rename each shuttle to match your mill's thread inventory. Click a
          name to edit.
        </p>
      </header>

      <div className="space-y-2">
        {/* Background row - greyed out, not editable */}
        <PaletteRow
          swatchColor={background.hex}
          rgb={background.rgb}
          hex={background.hex}
          fraction={background.pixel_fraction}
          name="background"
          editable={false}
          subtitle="No BMP exported"
        />

        {/* One row per shuttle */}
        {shuttles.map((s, idx) => (
          <PaletteRow
            key={s.shuttle_number}
            swatchColor={s.hex}
            rgb={s.rgb}
            hex={s.hex}
            fraction={s.pixel_fraction}
            name={shuttleNames[idx] ?? s.name}
            shuttleNumber={s.shuttle_number}
            editable
            onRename={(val) => onRename(idx, val)}
          />
        ))}
      </div>
    </section>
  );
}

function PaletteRow({
  swatchColor,
  rgb,
  hex,
  fraction,
  name,
  shuttleNumber,
  editable,
  onRename,
  subtitle,
}) {
  return (
    <div
      className={`flex items-center gap-3 p-2.5 rounded border ${
        editable
          ? 'border-ink-700/15 bg-cream-100/40'
          : 'border-ink-700/10 bg-cream-100/20 opacity-70'
      }`}
    >
      {/* Color swatch with a thin border so light colors are still visible */}
      <div
        className="w-10 h-10 rounded border border-ink-700/20 shrink-0"
        style={{ backgroundColor: swatchColor }}
        title={`RGB ${rgb.join(', ')}`}
      />

      {/* Name + meta */}
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline gap-2">
          {editable ? (
            <input
              type="text"
              value={name}
              onChange={(e) => onRename(e.target.value)}
              onBlur={(e) => {
                const cleaned = sanitizeFilename(e.target.value);
                if (cleaned && cleaned !== e.target.value) {
                  onRename(cleaned);
                }
              }}
              maxLength={64}
              className="font-mono text-sm bg-transparent border-b border-dashed border-ink-700/30 focus:outline-none focus:border-ink-700 px-0.5 min-w-0 flex-shrink"
              aria-label={`Shuttle ${shuttleNumber} filename`}
            />
          ) : (
            <span className="font-mono text-sm text-ink-700">{name}</span>
          )}
          {editable && (
            <span className="font-mono text-xs text-ink-500">.bmp</span>
          )}
        </div>
        <div className="font-mono text-xs text-ink-500 mt-0.5">
          {hex} · {(fraction * 100).toFixed(1)}%
          {subtitle && <> · {subtitle}</>}
        </div>
      </div>

      {shuttleNumber !== undefined && (
        <span className="font-mono text-xs text-ink-500 shrink-0">
          #{shuttleNumber}
        </span>
      )}
    </div>
  );
}
