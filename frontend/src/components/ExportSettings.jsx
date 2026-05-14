/**
 * Export settings panel: optional motif-size cleanup.
 *
 * Note from spec: bit depth toggle and active-color toggle were removed
 * after we locked the output format to 24-bit black=active to exactly
 * match the user's sample BMPs.
 */
export default function ExportSettings({
  motifCleanup,
  motifMinSize,
  onChange,
  disabled,
}) {
  return (
    <section className="panel p-6">
      <header className="mb-5">
        <p className="panel-label mb-1">Optional</p>
        <h2 className="text-2xl font-semibold">Export settings</h2>
        <p className="text-sm text-ink-600 mt-1">
          Defaults work for most designs. Adjust only if needed.
        </p>
      </header>

      <div className="space-y-4">
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={motifCleanup}
            onChange={(e) => onChange({ motifCleanup: e.target.checked })}
            disabled={disabled}
            className="mt-0.5 w-4 h-4 accent-ink-900"
          />
          <div>
            <div className="font-medium text-ink-900">
              Enforce minimum motif size
            </div>
            <p className="text-xs text-ink-600 mt-0.5 max-w-md">
              Merges any color region smaller than the threshold into its
              largest neighbor. Useful for cleaner weaving; turn off if your
              design has deliberate fine detail like zari hairlines.
            </p>
          </div>
        </label>

        {motifCleanup && (
          <div className="ml-7 flex items-center gap-3">
            <label htmlFor="motif-size" className="panel-label">
              Min size (px)
            </label>
            <select
              id="motif-size"
              value={motifMinSize}
              onChange={(e) =>
                onChange({ motifMinSize: Number(e.target.value) })
              }
              disabled={disabled}
              className="field-input py-1"
            >
              {[2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>
                  {n} × {n}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="mt-5 pt-4 border-t border-ink-700/10">
        <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-ink-500 mb-2">
          Output format (fixed)
        </p>
        <ul className="text-xs text-ink-600 space-y-1 font-mono">
          <li>· 24-bit RGB BMP per shuttle</li>
          <li>· Black = thread active · White = inactive</li>
          <li>· Stretched to exact pins × cards</li>
        </ul>
      </div>
    </section>
  );
}
