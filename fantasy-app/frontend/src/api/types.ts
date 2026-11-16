export interface Health {
  status: string;
  data_dir: string;
  season: string;
}

export interface Category {
  key: string;
  label: string;
}

export type PlayerRow = {
  PLAYER_ID: number;
  PLAYER_NAME: string;
  GP: number;
  MIN: number;
  TOTAL: number;
  AVAIL: number;
  ADJ_TOTAL: number;
} & Record<string, number | string | null>;

export interface Rankings {
  season: string;
  categories: Category[];
  meta: Record<string, string>;
  players: PlayerRow[];
}

export interface DraftPicks {
  taken: string[];
  mine: string[];
  history: string[];
}
