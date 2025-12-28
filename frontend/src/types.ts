export interface Image {
  id: string;
  path: string;
  created_at: string;
  prompt?: string;
}

export interface Directory {
  name: string;
  path: string;
}

export interface BrowseResponse {
  directories: Directory[];
  images: Image[];
}
