import { LIMITS, validatePins, validateCards } from '../utils/validators';

const SHUTTLE_OPTIONS = [2, 3, 4, 5, 6, 7, 8];

/**
 * Step 1 of the workflow: user enters loom dimensions and shuttle count
 * BEFORE uploading the image. This is intentional - per the spec, it forces
 * the user to commit to a loom target before getting attached to a preview.
 */
export default function LoomSetup({ pins, cards, shuttles, onChange, disabled }) {
  const pinsError = pins !== '' ? validatePins(pins) : null;
  const cardsError = cards !== '' ? validateCards(cards) : null;

  return (
    <section className="panel p-6">
      <header className="mb-5">
        <p className="panel-label mb-1">Step 1</p>
        <h2 className="text-2xl font-semibold">Loom setup</h2>
        <p className="text-sm text-ink-600 mt-1">
          Output BMPs will be created at exactly these dimensions, one per shuttle.
        </p>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
        <div>
          <label htmlFor="pins" className="panel-label block mb-1.5">
            Pins <span className="text-ink-400">(width)</span>
          </label>
          <input
            id="pins"
            type="number"
            inputMode="numeric"
            min={LIMITS.MIN_PINS}
            max={LIMITS.MAX_PINS}
            value={pins}
            onChange={(e) => onChange({ pins: e.target.value })}
            disabled={disabled}
            placeholder="e.g. 480"
            className="field-input w-full"
          />
          {pinsError && (
            <p className="text-xs text-madder-600 mt-1">{pinsError}</p>
          )}
        </div>

        <div>
          <label htmlFor="cards" className="panel-label block mb-1.5">
            Cards <span className="text-ink-400">(height)</span>
          </label>
          <input
            id="cards"
            type="number"
            inputMode="numeric"
            min={LIMITS.MIN_CARDS}
            max={LIMITS.MAX_CARDS}
            value={cards}
            onChange={(e) => onChange({ cards: e.target.value })}
            disabled={disabled}
            placeholder="e.g. 720"
            className="field-input w-full"
          />
          {cardsError && (
            <p className="text-xs text-madder-600 mt-1">{cardsError}</p>
          )}
        </div>
      </div>

      <div>
        <p className="panel-label mb-2">
          Shuttles <span className="text-ink-400">(thread count)</span>
        </p>
        <div className="flex flex-wrap gap-2">
          {SHUTTLE_OPTIONS.map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => onChange({ shuttles: n })}
              disabled={disabled}
              className={`shuttle-btn ${
                shuttles === n ? 'shuttle-btn-active' : ''
              }`}
              aria-pressed={shuttles === n}
            >
              {n}
            </button>
          ))}
        </div>
        <p className="text-xs text-ink-500 mt-2">
          Background is auto-detected and not exported. {shuttles || 'N'} shuttles
          produces {shuttles || 'N'} BMP file{shuttles !== 1 ? 's' : ''}.
        </p>
      </div>
    </section>
  );
}
