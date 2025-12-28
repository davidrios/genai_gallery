<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { api } from '@/services/api';
import type { Image, Directory } from '@/types';

const route = useRoute();
const router = useRouter();

const images = ref<Image[]>([]);
const directories = ref<Directory[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const selectedImage = ref<Image | null>(null);
const isLoadingDetails = ref(false);

// Derived state from URL
const currentPath = computed(() => (route.query.path as string) || '');
const sortOrder = computed(() => (route.query.sort as 'asc' | 'desc') || 'desc');

const fetchContent = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await api.browse(currentPath.value, sortOrder.value);
    images.value = response.images;
    directories.value = response.directories;
  } catch (e) {
    error.value = 'Failed to load content. Is the backend running?';
    console.error(e);
  } finally {
    loading.value = false;
  }
};

watch(
  () => route.query,
  () => {
    fetchContent();
  }
);

const toggleSort = () => {
  const newSort = sortOrder.value === 'desc' ? 'asc' : 'desc';
  router.push({ query: { ...route.query, sort: newSort } });
};

const navigateTo = (path: string) => {
  // If path is empty, remove it from query
  const query = { ...route.query };
  if (path) {
    query.path = path;
  } else {
    delete query.path;
  }
  router.push({ query });
};

const breadcrumbs = computed(() => {
    if (!currentPath.value) return [];
    const parts = currentPath.value.split('/');
    let accum = '';
    return parts.map(part => {
        accum = accum ? `${accum}/${part}` : part;
        return { name: part, path: accum };
    });
});

const isVideo = (path: string) => {
    const ext = path.split('.').pop()?.toLowerCase();
    return ['mp4', 'webm', 'mov'].includes(ext || '');
};

const openImage = async (image: Image) => {
  selectedImage.value = image;
  isLoadingDetails.value = true;
  try {
    const details = await api.getImage(image.id);
    selectedImage.value = details;
  } catch (e) {
    console.error("Failed to load image details", e);
  } finally {
    isLoadingDetails.value = false;
  }
};

const closeOverlay = () => {
    selectedImage.value = null;
    isLoadingDetails.value = false;
};

// Navigation
const currentImageIndex = computed(() => {
    if (!selectedImage.value) return -1;
    // Match by ID, but simple array index is enough since we have full list
    // Use the ID to match against list
    return images.value.findIndex(img => img.id === selectedImage.value?.id || img.path === selectedImage.value?.path);
});

const hasPrevious = computed(() => currentImageIndex.value > 0);
const hasNext = computed(() => currentImageIndex.value !== -1 && currentImageIndex.value < images.value.length - 1);

const sortedMetadata = computed(() => {
    if (!selectedImage.value?.metadata_items) return [];
    return [...selectedImage.value.metadata_items].sort((a, b) => a.key.localeCompare(b.key));
});

const navigateImage = async (direction: 'next' | 'prev') => {
    if (currentImageIndex.value === -1) return;
    
    const newIndex = direction === 'next' ? currentImageIndex.value + 1 : currentImageIndex.value - 1;
    
    if (newIndex >= 0 && newIndex < images.value.length) {
        // Optimistic update
        selectedImage.value = images.value[newIndex];
        // Fetch details
        openImage(images.value[newIndex]);
    }
};

const handleKeydown = (e: KeyboardEvent) => {
    if (!selectedImage.value) return;
    
    if (e.key === 'ArrowLeft') {
        navigateImage('prev');
    } else if (e.key === 'ArrowRight') {
        navigateImage('next');
    } else if (e.key === 'Escape') {
        closeOverlay();
    }
};

onMounted(() => {
    fetchContent();
    window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
    window.removeEventListener('keydown', handleKeydown);
});
</script>

<template>
  <div class="container mx-auto p-4">
    <div class="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
      <div class="flex items-center gap-2 overflow-x-auto w-full sm:w-auto">
        <button 
            @click="navigateTo('')" 
            class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="Home"
        >
             <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-gray-600 dark:text-gray-300">
               <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
               <polyline points="9 22 9 12 15 12 15 22"></polyline>
             </svg>
        </button>
        <template v-for="(crumb, index) in breadcrumbs" :key="crumb.path">
             <span class="text-gray-400">/</span>
             <button 
                @click="navigateTo(crumb.path)"
                class="hover:text-indigo-600 dark:hover:text-indigo-400 font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap"
             >
                {{ crumb.name }}
             </button>
        </template>
      </div>
      
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
      <p class="mt-4 text-gray-600 dark:text-gray-400">Loading content...</p>
    </div>

    <div v-else-if="error" class="bg-red-100 dark:bg-red-900 border border-red-400 text-red-700 dark:text-red-200 px-4 py-3 rounded relative" role="alert">
      <strong class="font-bold">Error!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <div v-else>
      <!-- Subdirectories -->
      <div v-if="directories.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
          <div 
            v-for="dir in directories" 
            :key="dir.path"
            @click="navigateTo(dir.path)"
            class="cursor-pointer group flex flex-col items-center justify-center p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-indigo-400 dark:hover:border-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-all duration-200"
          >
             <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-indigo-400 dark:text-indigo-300 group-hover:scale-110 transition-transform">
               <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 2H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2Z"></path>
             </svg>
             <span class="mt-2 text-sm font-medium text-gray-700 dark:text-gray-200 truncate w-full text-center">{{ dir.name }}</span>
          </div>
      </div>

      <!-- Images -->
      <div v-if="images.length > 0" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        <div v-for="image in images" :key="image.id" class="group relative bg-white dark:bg-gray-800 rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-all duration-300">
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
               <button @click.stop="openImage(image)" class="px-4 py-2 bg-white text-black rounded-full font-medium hover:bg-gray-100 transition-colors">
                   View Details
               </button>
          </div>
        </div>
      </div>
      
      <!-- Overlay -->
      <div v-if="selectedImage" class="fixed inset-0 z-50 flex items-center justify-center bg-black/90" @click="closeOverlay">
        
        <!-- Close Button -->
        <button @click="closeOverlay" class="absolute top-4 right-4 text-white hover:text-gray-300 z-50 p-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </button>

        <div class="flex w-full h-full max-w-7xl mx-auto p-4 gap-6" @click.stop>
            <!-- Media Viewer -->
            <div class="flex-1 flex items-center justify-center overflow-hidden bg-black/50 rounded-lg relative group/media">
                <!-- Navigation Buttons -->
                <button 
                    v-if="hasPrevious"
                    class="absolute left-4 top-1/2 -translate-y-1/2 p-3 bg-black/40 hover:bg-black/70 text-white rounded-full opacity-0 group-hover/media:opacity-100 transition-all duration-300 backdrop-blur-sm z-10"
                    @click.stop="navigateImage('prev')"
                    title="Previous (Left Arrow)"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
                </button>
                
                <button 
                    v-if="hasNext"
                    class="absolute right-4 top-1/2 -translate-y-1/2 p-3 bg-black/40 hover:bg-black/70 text-white rounded-full opacity-0 group-hover/media:opacity-100 transition-all duration-300 backdrop-blur-sm z-10"
                    @click.stop="navigateImage('next')"
                    title="Next (Right Arrow)"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
                </button>

                <video 
                  v-if="isVideo(selectedImage.path)"
                  :src="api.getImageUrl(selectedImage.path)" 
                  controls
                  autoplay
                  class="max-w-full max-h-full object-contain"
                ></video>
                <img 
                  v-else
                  :src="api.getImageUrl(selectedImage.path)" 
                  :alt="selectedImage.path" 
                  class="max-w-full max-h-full object-contain"
                />
            </div>

            <!-- Sidebar -->
            <div class="w-96 flex flex-col bg-gray-900 border-l border-gray-800 rounded-r-lg shadow-xl overflow-hidden transition-all duration-300" :class="{'w-0 opacity-0': !selectedImage}">
                <div class="p-4 border-b border-gray-800 bg-gray-900/95 sticky top-0">
                    <h2 class="text-lg font-semibold text-gray-100 truncate" :title="selectedImage.path">{{ selectedImage.path.split('/').pop() }}</h2>
                    <p class="text-sm text-gray-500 mt-1">{{ new Date(selectedImage.created_at).toLocaleString() }}</p>
                </div>
                
                <div class="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                    <div v-if="isLoadingDetails" class="text-center py-8">
                        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mx-auto"></div>
                    </div>
                    
                    <div v-else-if="selectedImage.metadata_items && selectedImage.metadata_items.length > 0">
                        <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Generation Params</h3>
                        <div class="space-y-3">
                            <div v-for="item in sortedMetadata" :key="item.key" class="group">
                                <dt class="text-xs text-indigo-400 font-medium mb-1 break-all">{{ item.key }}</dt>
                                <dd class="text-sm text-gray-300 bg-gray-800/50 p-2 rounded border border-transparent group-hover:border-gray-700 break-words font-mono transition-colors">
                                    {{ item.value }}
                                </dd>
                            </div>
                        </div>
                    </div>
                    
                    <div v-else class="text-center py-10 text-gray-600 italic">
                        No metadata available for this image.
                    </div>
                </div>
            </div>
        </div>
      </div>
      
      <div v-if="directories.length === 0 && images.length === 0" class="text-center py-20 text-gray-500">
          Empty directory.
      </div>
    </div>
  </div>
</template>
