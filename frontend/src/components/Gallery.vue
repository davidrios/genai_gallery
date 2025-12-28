<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { api } from '@/services/api';
import type { Image } from '@/types';

const images = ref<Image[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const sortOrder = ref<'asc' | 'desc'>('desc');

const fetchImages = async () => {
  loading.value = true;
  error.value = null;
  try {
    images.value = await api.getImages(sortOrder.value);
  } catch (e) {
    error.value = 'Failed to load images. Is the backend running?';
    console.error(e);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchImages();
});

const toggleSort = () => {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc';
  fetchImages();
};
</script>

<template>
  <div class="container mx-auto p-4">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold text-gray-800 dark:text-gray-100">GenAI Gallery</h1>
      <button 
        @click="toggleSort"
        class="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm font-medium text-gray-700 dark:text-gray-200"
      >
        <span>Sort by Date</span>
        <span class="text-xs uppercase bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded">{{ sortOrder }}</span>
      </button>
    </div>
    
    <div v-if="loading" class="text-center py-10">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
      <p class="mt-4 text-gray-600 dark:text-gray-400">Loading your masterpieces...</p>
    </div>

    <div v-else-if="error" class="bg-red-100 dark:bg-red-900 border border-red-400 text-red-700 dark:text-red-200 px-4 py-3 rounded relative" role="alert">
      <strong class="font-bold">Error!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
      <div v-for="image in images" :key="image.id" class="group relative bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-all duration-300">
        <div class="aspect-w-1 aspect-h-1 w-full overflow-hidden bg-gray-200 dark:bg-gray-700 xl:aspect-w-7 xl:aspect-h-8">
          <img 
            :src="api.getImageUrl(image.path)" 
            :alt="image.path" 
            class="h-full w-full object-cover object-center group-hover:opacity-75 transition-opacity duration-300"
            loading="lazy"
          />
        </div>
        <div class="p-4">
          <h3 class="mt-1 text-sm text-gray-500 dark:text-gray-400 truncate">{{ image.path }}</h3>
          <p class="mt-1 text-xs text-gray-400 dark:text-gray-500">{{ new Date(image.created_at).toLocaleDateString() }}</p>
        </div>
        
        <!-- Hover overlay with rudimentary prompt view (expandable later) -->
        <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
             <a :href="api.getImageUrl(image.path)" target="_blank" class="px-4 py-2 bg-white text-black rounded-full font-medium hover:bg-gray-100 transition-colors">
                 View Full
             </a>
        </div>
      </div>
    </div>
    
    <div v-if="!loading && !error && images.length === 0" class="text-center py-20 text-gray-500">
        No images found. Generate something cool!
    </div>
  </div>
</template>
