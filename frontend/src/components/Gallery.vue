<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useGalleryData } from '@/composables/useGalleryData';
import { useGalleryNavigation } from '@/composables/useGalleryNavigation';
import { useInfiniteScrollLogic } from '@/composables/useInfiniteScrollLogic';
import { useMediaOverlay } from '@/composables/useMediaOverlay';

// Components
import GalleryHeader from './gallery/GalleryHeader.vue';
import GalleryGrid from './gallery/GalleryGrid.vue';
import MediaOverlay from './gallery/MediaOverlay.vue';

// ----------------------------------------------------------------------
// 1. Data Store
// ----------------------------------------------------------------------
const { 
    pages, directories, images, loading, error, 
    totalPages, firstLoadedPage, lastLoadedPage,
    loadPageContent, resetData, addPageChunk 
} = useGalleryData();

// ----------------------------------------------------------------------
// 2. Navigation & Sync
// ----------------------------------------------------------------------
// This lock is shared between nav and infinite scroll logic if needed,
// but for now Nav manages "isUrlSyncing" internally or effectively via the debounce guard.
// However, the issue described by user ("reset to page 1") was about the watcher firing on scroll spy.
// So we need to pass a shared ref for that lock.
const isUrlSyncing = ref(false);

const initGallery = async () => {
    loading.value = true;
    resetData();
    
    // Get params from route via composable helper or direct access if easier, 
    // but better to keep it decoupled. 
    // Actually `useGalleryNavigation` has access to `route` so we can read from it inside `loadPageContent` calls
    // OR we just read values here.
    const targetPage = parseInt(route.query.page as string) || 1;
    const path = currentPath.value;
    const sort = sortOrder.value;
    const q = searchQuery.value;

    const result = await loadPageContent(path, sort, q, targetPage);
    
    if (result) {
        addPageChunk(
            { pageNum: targetPage, images: result.images }, 
            'push', // first chunk is effectively a push
            result.directories, 
            result.totalPages
        );
        firstLoadedPage.value = targetPage;
        lastLoadedPage.value = targetPage;
        
        // Handle Deep Link
        const viewPath = route.query.view as string;
        if (viewPath) {
             const img = result.images.find(i => i.path === viewPath);
             if (img) openImage(img, false);
        }
    }
    loading.value = false;
};

const { 
    currentPath, sortOrder, searchQuery, breadcrumbs, 
    updateRoutePage, navigateTo, toggleSort, performSearch, route 
} = useGalleryNavigation(initGallery, isUrlSyncing);

// ----------------------------------------------------------------------
// 3. Infinite Scroll
// ----------------------------------------------------------------------
const { topSentinel, isFetchingPrev, isFetchingNext } = useInfiniteScrollLogic({
    isLoading: () => loading.value,
    canLoadUp: () => firstLoadedPage.value > 1,
    canLoadDown: () => lastLoadedPage.value < totalPages.value,
    loadUp: async () => {
        const prevPage = firstLoadedPage.value - 1;
        const result = await loadPageContent(currentPath.value, sortOrder.value, searchQuery.value, prevPage);
        if (result) {
            addPageChunk({ pageNum: prevPage, images: result.images }, 'unshift', [], result.totalPages);
            return true;
        }
        return false;
    },
    loadDown: async () => {
        const nextPage = lastLoadedPage.value + 1;
        const result = await loadPageContent(currentPath.value, sortOrder.value, searchQuery.value, nextPage);
        if (result) {
            addPageChunk({ pageNum: nextPage, images: result.images }, 'push', [], result.totalPages);
            return true;
        }
        return false;
    }
});

// ----------------------------------------------------------------------
// 4. Overlay
// ----------------------------------------------------------------------
const { 
    selectedImage, isLoadingDetails, hasPrevious, hasNext, 
    openImage, closeOverlay, navigateImage 
} = useMediaOverlay(images);

onMounted(() => {
    initGallery();
});
</script>

<template>
  <div class="container mx-auto p-4 min-h-screen">
      <GalleryHeader 
          :breadcrumbs="breadcrumbs"
          v-model:searchQuery="searchQuery"
          :sortOrder="sortOrder"
          @navigate="navigateTo"
          @search="performSearch"
          @toggleSort="toggleSort"
      />

      <div ref="topSentinel" class="w-full h-1"></div>

      <GalleryGrid 
          :directories="directories"
          :pages="pages"
          :loading="loading"
          :isFetchingPrev="isFetchingPrev"
          :isFetchingNext="isFetchingNext"
          :firstLoadedPage="firstLoadedPage"
          :lastLoadedPage="lastLoadedPage"
          :totalPages="totalPages"
          :error="error"
          @navigate="navigateTo"
          @selectImage="openImage"
          @pageVisible="updateRoutePage"
      />

      <MediaOverlay 
          :selectedImage="selectedImage"
          :isLoadingDetails="isLoadingDetails"
          :hasPrevious="hasPrevious"
          :hasNext="hasNext"
          @close="closeOverlay"
          @navigate="navigateImage"
      />
  </div>
</template>
