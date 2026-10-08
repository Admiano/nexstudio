export const ENVIRONMENTS = [{"key": "living_room", "label": "Contemporary living room"}, {"key": "home_office", "label": "Home office"}, {"key": "creator_studio", "label": "Creator studio"}, {"key": "workplace", "label": "Modern workplace"}, {"key": "cafe", "label": "Neighborhood caf\u00e9"}, {"key": "kitchen", "label": "Contemporary kitchen"}, {"key": "library", "label": "Library and study"}, {"key": "classroom", "label": "Training classroom"}, {"key": "terrace", "label": "Garden terrace"}, {"key": "neutral_studio", "label": "Neutral illustrated studio"}, {"key": "lesson_board", "label": "Animated lesson board"}, {"key": "kids_book", "label": "Kids lesson book"}] as const;
// Lesson boards are mode internals (the lesson/kids subtypes own them), not
// user-facing background choices — the presenter picker shows exactly these 10.
export const PICKER_ENVIRONMENTS = ENVIRONMENTS.filter((e) => e.key !== "lesson_board" && e.key !== "kids_book");
export type EnvironmentId = typeof ENVIRONMENTS[number]['key'];
export type EnvironmentFormat = 'landscape' | 'square' | 'portrait';
export const environmentImage=(id:EnvironmentId,format:EnvironmentFormat)=>`/cast/environments/${format}/${id}.jpg`;
export const environmentAspect={landscape:'16 / 9',square:'1 / 1',portrait:'9 / 16'} as const;
