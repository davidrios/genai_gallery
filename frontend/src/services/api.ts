import type { Image } from '../types';

export const api = {
    async getImages(): Promise<Image[]> {
        const response = await fetch('/api/images');
        if (!response.ok) {
            throw new Error('Failed to fetch images');
        }
        return response.json();
    },

    getImageUrl(filename: string): string {
        return `/images/${filename}`;
    }
};
