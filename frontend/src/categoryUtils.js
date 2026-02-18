export const CATEGORY_OPTIONS = [
  { value: 'metal', label: 'Metal' },
  { value: 'ahsap', label: 'Ahşap' },
  { value: 'cam', label: 'Cam' },
  { value: 'harita', label: 'Harita' },
  { value: 'mobilya', label: 'Mobilya' },
];

export function getCategoryBadgeClass(kategori) {
  const key = String(kategori || '').trim().toLowerCase();
  if (key === 'metal') return 'badge-metal';
  if (key === 'ahsap' || key === 'ahşap') return 'badge-ahsap';
  if (key === 'cam') return 'badge-cam';
  if (key === 'harita') return 'badge-harita';
  if (key === 'mobilya') return 'badge-mobilya';
  return 'badge-default';
}
