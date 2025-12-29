import type { Image, BrowseResponse } from '../types';

export const api = {
    async getImages(sort: 'asc' | 'desc' = 'desc', search: string = '', signal?: AbortSignal): Promise<Image[]> {
        const params = new URLSearchParams({ sort });
        if (search) params.append('q', search);

        const response = await fetch(`/api/images?${params.toString()}`, { signal });
        if (!response.ok) {
            throw new Error('Failed to fetch images');
        }
        return response.json();
    },

    async browse(path: string = "", sort: 'asc' | 'desc' = 'desc', search: string = '', page: number = 1, signal?: AbortSignal): Promise<BrowseResponse> {
        const params = new URLSearchParams({ path, sort, page: page.toString() });
        if (search) params.append('q', search);

        const response = await fetch(`/api/browse?${params.toString()}`, { signal });
        if (!response.ok) {
            throw new Error('Failed to browse directory');
        }
        return response.json();
    },

    async getImage(id: string): Promise<Image> {
        const response = await fetch(`/api/images/${id}`);
        if (!response.ok) {
            throw new Error('Failed to fetch image details');
        }
        return response.json();
    },

    getImageUrl(path: string): string {
        return `/images/${path}`;
    }
};
