import type { CastCharacter } from './spec';

export type CastImageCategory = 'character' | 'face' | 'hair' | 'neck' | 'dress' | 'top' | 'bottom' | 'shoes' | 'watch' | 'formal';

export function castOptionImage(character: CastCharacter, category: CastImageCategory, key: string | number) {
  if (category === 'character' || category === 'face' || category === 'hair' || category === 'dress' || category === 'top' || category === 'bottom' || category === 'formal') {
    return '/cast/options/v21/' + character + '/' + category + '/' + key + '.webp';
  }
  return '/cast/options/' + character + '/' + category + '/' + key + '.svg';
}

export default function OptionImage({ character, category, option, label, note, selected, onSelect, disabled = false }: {
  character: CastCharacter;
  category: CastImageCategory;
  option: string | number;
  label: string;
  note?: string;
  selected: boolean;
  onSelect: () => void;
  disabled?: boolean;
}) {
  return (
    <button type="button" className="cast-image-option" aria-label={label} aria-pressed={selected} onClick={onSelect} disabled={disabled} title={disabled ? 'Awaiting verified production wardrobe assets' : label}>
      <span className="cast-image-option-art">
        <img src={castOptionImage(character, category, option)} alt="" width={224} height={224} loading="lazy" decoding="async" />
        {selected && <span className="cast-image-option-check" aria-hidden="true">✓</span>}
      </span>
      <span className="cast-image-option-label">{label}</span>
      {note && <small>{note}</small>}
    </button>
  );
}
