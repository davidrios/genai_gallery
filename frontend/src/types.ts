export interface Image {
  id: string;
  path: string;
  created_at: string;
  prompt?: string;
  metadata_items?: { key: string; value: string }[];
}

export interface Directory {
  name: string;
  path: string;
}

export interface BrowseResponse {
  directories: Directory[];
  images: Image[];
}
