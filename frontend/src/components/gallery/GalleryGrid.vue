<script setup lang="ts">
import type { Directory, Image } from '@/types';
import PageBlock from '../PageBlock.vue';
import { api } from '@/services/api';

defineProps<{
  directories: Directory[];
  pages: { pageNum: number; images: Image[] }[];
  loading: boolean;
  isFetchingPrev: boolean;
  isFetchingNext: boolean;
  firstLoadedPage: number;
  lastLoadedPage: number;
  totalPages: number;
  error: string | null;
}>();

const emit = defineEmits<{
  (e: 'navigate', path: string): void;
  (e: 'selectImage', image: Image): void;
  (e: 'pageVisible', page: number): void;
}>();

const isVideo = (path: string) => {
    const ext = path.split('.').pop()?.toLowerCase();
    return ['mp4', 'webm', 'mov'].includes(ext || '');
};
</script>

<template>
<div>
    <!-- Error State -->
    <div v-if="error" class="bg-red-100 dark:bg-red-900 border border-red-400 text-red-700 dark:text-red-200 px-4 py-3 rounded relative mb-4" role="alert">
      <strong class="font-bold">Error!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <!-- Subdirectories -->
    <div v-if="directories.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
        <div
            v-for="dir in directories"
            :key="dir.path"
            @click="emit('navigate', dir.path)"
            class="cursor-pointer group flex flex-col items-center justify-center p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-indigo-400 dark:hover:border-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-all duration-200"
        >
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-indigo-400 dark:text-indigo-300 group-hover:scale-110 transition-transform">
            <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 2H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2Z"></path>
            </svg>
            <span class="mt-2 text-sm font-medium text-gray-700 dark:text-gray-200 truncate w-full text-center">{{ dir.name }}</span>
        </div>
    </div>

    <!-- Top Sentinel Area -->
    <div v-if="firstLoadedPage > 1" class="h-10 flex justify-center items-center">
        <!-- Sentinel is managed by parent via ref, but we can visualize it here -->
        <div v-if="isFetchingPrev" class="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
    </div>

    <!-- Pages Content -->
    <div class="flex flex-col gap-6">
        <PageBlock v-for="page in pages" :key="page.pageNum" :page="page.pageNum" @visible="emit('pageVisible', page.pageNum)">
            <div class="relative">
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    <div v-for="image in page.images" :key="image.id" class="group relative bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-all duration-300">
                      <div class="aspect-w-1 aspect-h-1 w-full overflow-hidden bg-gray-200 dark:bg-gray-700 xl:aspect-w-7 xl:aspect-h-8">
                        <video
                          v-if="isVideo(image.path)"
                          :src="api.getImageUrl(image.path)"
                          controls
                          preload="metadata"
                          class="h-full w-full object-cover object-center bg-black"
                          @click.stop
                        ></video>
                        <img
                          v-else
                          :src="api.getImageUrl(image.path)"
                          :alt="image.path"
                          class="h-full w-full object-cover object-center group-hover:opacity-75 transition-opacity duration-300"
                          loading="lazy"
                        />
                      </div>
                      <div class="p-4">
                        <h3 class="mt-1 text-sm text-gray-500 dark:text-gray-400 truncate">{{ image.path.split('/').pop() }}</h3>
                        <p class="mt-1 text-xs text-gray-400 dark:text-gray-500">{{ new Date(image.created_at).toLocaleDateString() }}</p>
                      </div>

                      <div v-if="!isVideo(image.path)" class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                           <button @click.stop="emit('selectImage', image)" class="px-4 py-2 bg-white text-black rounded-full font-medium hover:bg-gray-100 transition-colors">
                               View Details
                           </button>
                      </div>
                    </div>
                </div>
            </div>
        </PageBlock>
    </div>

    <!-- Bottom Loader -->
    <div class="h-20 flex justify-center items-center">
        <div v-if="isFetchingNext || loading && pages.length === 0" class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        <span v-else-if="lastLoadedPage >= totalPages && pages.length > 0" class="text-gray-400 text-sm">End of results</span>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && directories.length === 0 && pages.length > 0 && pages[0]?.images.length === 0" class="text-center py-20 text-gray-500">
        Empty directory.
    </div>
</div>
</template>
