export interface ReleaseNote {
  version: string;
  date: string;
  title: string;
  body: string;
}

export const RELEASE_NOTES: ReleaseNote[] = [
  {
    version: 'v1.0',
    date: 'Jun 2026',
    title: 'Field Intel is live',
    body: 'Log competitor moves, pricing intel, rep activity, and account news in seconds. The app automatically tags your notes with competitor names, geography, and topics — no manual categorization needed. Search finds everything instantly across all notes, even with partial matches and typos.',
  },
];

export const CURRENT_VERSION = RELEASE_NOTES[0].version;
