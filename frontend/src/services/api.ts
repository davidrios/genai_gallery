import type { Image, BrowseResponse } from '../types';

export const api = {
    async getImages(sort: 'asc' | 'desc' = 'desc'): Promise<Image[]> {
        const response = await fetch(`/api/images?sort=${sort}`);
        if (!response.ok) {
            throw new Error('Failed to fetch images');
        }
        return response.json();
    },

    async browse(path: string = "", sort: 'asc' | 'desc' = 'desc'): Promise<BrowseResponse> {
        const params = new URLSearchParams({ path, sort });
        const response = await fetch(`/api/browse?${params.toString()}`);
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
