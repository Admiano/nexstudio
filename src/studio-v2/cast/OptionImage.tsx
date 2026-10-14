import type { CastCharacter } from './spec';

export type CastImageCategory = 'character' | 'face' | 'hair' | 'neck' | 'dress' | 'top' | 'bottom' | 'shoes' | 'watch' | 'formal';

export function castOptionImage(character: CastCharacter, category: CastImageCategory, key: string | number) {
  if (category === 'formal') return '/cast/options/formal/' + character + '-' + String(key).replace(/^formal-/, '') + '.webp';
  if (category === 'character' || category === 'face' || category === 'hair' || category === 'dress' || category === 'top' || category === 'bottom') {
    return '/cast/options/v21/' + character + '/' + category + '/' + key + '.webp';
  }
  return '/cast/options/' + character + '/' + category + '/' + key + '.svg';
}

export default function OptionImage({ character, category, option, label, note, selected, disabled=false, onSelect }: {
  character: CastCharacter;
  category: CastImageCategory;
  option: string | number;
  label: string;
  note?: string;
  selected: boolean;
  disabled?: boolean;
  onSelect: () => void;
}) {
  return (
    <button type="button" className="cast-image-option" aria-label={label} aria-pressed={selected} disabled={disabled} onClick={onSelect}>
      <span className="cast-image-option-art">
        {category==='formal'&&disabled?<span aria-hidden="true" style={{display:"grid",placeItems:"center",minHeight:110,padding:12,textAlign:"center"}}>Verified render pending</span>:
         <img src={castOptionImage(character, category, option)} alt="" width={224} height={224} loading="lazy" decoding="async" />}
        {selected && <span className="cast-image-option-check" aria-hidden="true">✓</span>}
      </span>
      <span className="cast-image-option-label">{label}</span>
      {note && <small>{note}</small>}
    </button>
  );
}
