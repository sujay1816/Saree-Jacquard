/**
 * Output format info panel.
 *
 * As of v1.1, the export panel has no user-adjustable controls. The output
 * format is fixed (24-bit BMP, black=active) and the cleanup pipeline is
 * always-on aggressive smoothing + morphology + region cleanup.
 *
 * Kept as a labeled component so the user understands what they'll get.
 */
export default function ExportSettings() {
  return (
    <section className="panel p-6">
      <header className="mb-4">
        <p className="panel-label mb-1">Output format</p>
        <h2 className="text-2xl font-semibold">What you'll get</h2>
      </header>

      <ul className="text-sm text-ink-700 space-y-1.5 font-mono">
        <li>· One 24-bit RGB BMP per shuttle</li>
        <li>· Black pixels = thread active</li>
        <li>· White pixels = thread inactive</li>
        <li>· Stretched to exact pins × cards</li>
        <li>· Background auto-detected and not exported</li>
        <li>· Aggressive smoothing baked in for clean weaving</li>
      </ul>
    </section>
  );
}
