<script setup lang="ts">
import { ref } from 'vue'
import { useGalleryStore } from '@/stores/gallery'
import { storeToRefs } from 'pinia'
import SiteHeader from '@/components/SiteHeader.vue'
import MediaCard from '@/components/MediaCard.vue'
import MediaDetail from '@/components/MediaDetail.vue'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import type { MediaItem } from '@/types'

const store = useGalleryStore()
const { filteredItems } = storeToRefs(store)

const selectedItem = ref<MediaItem | null>(null)
const isDialogOpen = ref(false)

function openDetail(item: MediaItem) {
  selectedItem.value = item
  isDialogOpen.value = true
}
</script>

<template>
  <div class="flex min-h-screen flex-col">
    <SiteHeader />

    <main class="container mx-auto flex-1 p-4">
      <div class="columns-1 gap-4 sm:columns-2 md:columns-3 lg:columns-4 xl:columns-5">
        <div v-for="item in filteredItems" :key="item.id">
          <MediaCard :item="item" @click="openDetail(item)" />
        </div>
      </div>

      <div v-if="filteredItems.length === 0" class="text-muted-foreground py-20 text-center">
        <p>No items found.</p>
      </div>
    </main>

    <!-- Detail Dialog -->
    <Dialog v-model:open="isDialogOpen">
      <DialogContent
        class="bg-background/95 h-[95vh] max-h-[95vh] w-[95vw] max-w-[95vw] overflow-hidden border-white/10 p-0 backdrop-blur-xl sm:rounded-xl"
      >
        <div class="h-full w-full">
          <MediaDetail v-if="selectedItem" :item="selectedItem" />
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped></style>
