<script setup lang="ts">
import { computed } from 'vue';
import type { Image } from '@/types';
import { api } from '@/services/api';

const props = defineProps<{
  selectedImage: Image | null;
  isLoadingDetails: boolean;
  hasPrevious: boolean;
  hasNext: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'navigate', dir: 'next' | 'prev'): void;
}>();

const isVideo = (path: string) => {
    const ext = path.split('.').pop()?.toLowerCase();
    return ['mp4', 'webm', 'mov'].includes(ext || '');
};

const sortedMetadata = computed(() => {
    if (!props.selectedImage?.metadata_items) return [];
    const grouped: Record<string, string[]> = {};
    for (const item of props.selectedImage.metadata_items) {
        if (!grouped[item.key]) grouped[item.key] = [];
        const group = grouped[item.key];
        if (group) group.push(item.value);
    }
    return Object.keys(grouped).sort().map(key => ({ key, values: grouped[key] }));
});
</script>

<template>
    <div v-if="selectedImage" class="fixed inset-0 z-50 flex items-center justify-center bg-black/90" @click="emit('close')">
      <!-- Close Button -->
      <button @click="emit('close')" class="absolute top-4 right-4 text-white hover:text-gray-300 z-50 p-2">
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
                  @click.stop="emit('navigate', 'prev')"
                  title="Previous (Left Arrow)"
              >
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
              </button>

              <button
                  v-if="hasNext"
                  class="absolute right-4 top-1/2 -translate-y-1/2 p-3 bg-black/40 hover:bg-black/70 text-white rounded-full opacity-0 group-hover/media:opacity-100 transition-all duration-300 backdrop-blur-sm z-10"
                  @click.stop="emit('navigate', 'next')"
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
                                  <ul v-if="item.values && item.values.length > 1" class="list-disc list-inside">
                                       <li v-for="(val, idx) in item.values" :key="idx">{{ val }}</li>
                                  </ul>
                                  <span v-else>{{ item.values?.[0] }}</span>
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
</template>
