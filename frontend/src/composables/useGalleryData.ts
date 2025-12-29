import { ref, computed } from 'vue';
import { api } from '@/services/api';
import type { Image, Directory } from '@/types';

export interface PageChunk {
    pageNum: number;
    images: Image[];
}

export function useGalleryData() {
    const pages = ref<PageChunk[]>([]);
    const directories = ref<Directory[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);
    const totalPages = ref(1);
    const firstLoadedPage = ref(1);
    const lastLoadedPage = ref(1);

    const images = computed(() => pages.value.flatMap(p => p.images));

    const loadPageContent = async (
        path: string,
        sort: 'asc' | 'desc',
        query: string,
        page: number
    ) => {
        try {
            const response = await api.browse(path, sort, query, page);
            return {
                images: response.images,
                directories: response.directories,
                totalPages: response.pages,
            };
        } catch (e: any) {
            console.error('Failed to load page', page, e);
            error.value = 'Failed to load content.';
            return null;
        }
    };

    const resetData = () => {
        pages.value = [];
        directories.value = [];
        error.value = null;
        totalPages.value = 1;
        firstLoadedPage.value = 1;
        lastLoadedPage.value = 1;
    };

    // Helper to prepend/append pages safely
    const addPageChunk = (
        chunk: PageChunk,
        method: 'push' | 'unshift',
        dirs: Directory[],
        total: number
    ) => {
        if (method === 'push') {
            pages.value.push(chunk);
            lastLoadedPage.value = chunk.pageNum;
        } else {
            pages.value.unshift(chunk);
            firstLoadedPage.value = chunk.pageNum;
        }

        // Directories only need to be set once (usually from the first fetch)
        // or updated if we want to support paginated directories (not current case)
        if (directories.value.length === 0) {
            directories.value = dirs;
        }
        totalPages.value = total;
    };

    return {
        pages,
        directories,
        images,
        loading,
        error,
        totalPages,
        firstLoadedPage,
        lastLoadedPage,
        loadPageContent,
        resetData,
        addPageChunk
    };
}
