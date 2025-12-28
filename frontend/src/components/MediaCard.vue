<script setup lang="ts">
import { computed } from 'vue'
import type { MediaItem } from '@/types'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AspectRatio } from '@/components/ui/aspect-ratio'

const props = defineProps<{
  item: MediaItem
}>()

const aspectRatio = computed(() => {
  return props.item.width / props.item.height
})

const modelBadge = computed(() => {
  if (!props.item.metadata.model_name) return null
  return props.item.metadata.model_name.replace('.safetensors', '').replace('.ckpt', '')
})
</script>

<template>
  <Card
    class="group cursor-pointer overflow-hidden border-0 bg-transparent shadow-none transition-all duration-300 hover:shadow-lg"
  >
    <CardContent class="relative overflow-hidden rounded-xl p-0">
      <div class="relative">
        <!-- Image with Aspect Ratio -->
        <AspectRatio :ratio="aspectRatio" class="bg-muted">
          <img
            :src="item.url"
            :alt="item.name"
            class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
          />
        </AspectRatio>

        <!-- Overlay on Hover -->
        <div
          class="absolute inset-0 flex flex-col justify-end bg-gradient-to-t from-black/60 via-black/0 to-transparent p-4 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        >
          <div class="mb-2 flex flex-wrap gap-2">
            <Badge
              v-if="modelBadge"
              variant="secondary"
              class="border-white/20 bg-black/50 text-xs text-white backdrop-blur-md hover:bg-black/70"
            >
              {{ modelBadge }}
            </Badge>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
