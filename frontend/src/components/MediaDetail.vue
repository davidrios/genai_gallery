<script setup lang="ts">
import type { MediaItem } from '@/types'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Button } from '@/components/ui/button'
import { Copy, Download, Share2, MoreHorizontal } from 'lucide-vue-next'

defineProps<{
  item: MediaItem
}>()

function copyPrompt(prompt: string) {
  navigator.clipboard.writeText(prompt)
}
</script>

<template>
  <div class="bg-background text-foreground flex h-full w-full flex-col md:flex-row">
    <!-- Left: Image Canvas (Darker, centered) -->
    <div class="relative flex flex-1 items-center justify-center overflow-hidden bg-zinc-950/50">
      <!-- Background blur effect (optional, subtle) -->
      <div
        class="pointer-events-none absolute inset-0 scale-150 opacity-20 blur-3xl"
        :style="{
          backgroundImage: `url(${item.url})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }"
      ></div>

      <!-- Main Image -->
      <img
        :src="item.url"
        :alt="item.name"
        class="relative z-10 max-h-full max-w-full object-contain p-4 transition-opacity duration-300 md:p-8"
      />
    </div>

    <!-- Right: Sidebar (Metadata) -->
    <div
      class="border-border bg-card z-20 flex h-full w-full flex-col border-l shadow-xl md:w-[400px]"
    >
      <!-- Header -->
      <div class="border-border flex items-start justify-between gap-4 border-b p-4">
        <div>
          <h2 class="text-xl leading-tight font-bold">{{ item.name }}</h2>
          <div class="text-muted-foreground mt-1 text-xs">
            {{ item.width }}x{{ item.height }} • {{ item.type }}
          </div>
        </div>
        <div class="flex gap-1">
          <Button variant="ghost" size="icon" class="h-8 w-8">
            <MoreHorizontal class="h-4 w-4" />
          </Button>
        </div>
      </div>

      <!-- Scrollable Content -->
      <ScrollArea class="flex-1">
        <div class="space-y-6 p-4">
          <!-- Actions Bar -->
          <div class="grid grid-cols-2 gap-2">
            <Button class="w-full"> <Download class="mr-2 h-4 w-4" /> Download </Button>
            <Button variant="outline" class="w-full">
              <Share2 class="mr-2 h-4 w-4" /> Share
            </Button>
          </div>

          <Separator />

          <!-- Prompt Section -->
          <div v-if="item.metadata.prompt" class="space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-semibold tracking-wide">Prompt</h3>
              <Button
                variant="ghost"
                size="sm"
                class="h-6 px-2 text-xs"
                @click="copyPrompt(item.metadata.prompt!)"
              >
                <Copy class="mr-1 h-3 w-3" /> Copy
              </Button>
            </div>
            <div
              class="border-border/50 bg-muted/30 text-muted-foreground rounded-lg border p-3 font-mono text-sm leading-relaxed break-words whitespace-pre-wrap select-text"
            >
              {{ item.metadata.prompt }}
            </div>
          </div>

          <!-- Negative Prompt (Mock if not exists) -->
          <div v-if="item.metadata.negative_prompt" class="space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="text-destructive/80 text-sm font-semibold tracking-wide">
                Negative Prompt
              </h3>
              <Button
                variant="ghost"
                size="sm"
                class="h-6 px-2 text-xs"
                @click="copyPrompt(item.metadata.negative_prompt!)"
              >
                <Copy class="mr-1 h-3 w-3" /> Copy
              </Button>
            </div>
            <div
              class="border-destructive/10 bg-destructive/5 text-muted-foreground rounded-lg border p-3 font-mono text-sm leading-relaxed break-words whitespace-pre-wrap select-text"
            >
              {{ item.metadata.negative_prompt }}
            </div>
          </div>

          <Separator />

          <!-- Generation Details Grid -->
          <div class="space-y-4">
            <h3 class="text-sm font-semibold">Generation Details</h3>
            <div class="grid grid-cols-2 gap-x-4 gap-y-4 text-sm">
              <div v-if="item.metadata.model_name" class="col-span-2">
                <div class="text-muted-foreground mb-1 text-xs">Model</div>
                <div class="flex items-center gap-2">
                  <Badge variant="secondary" class="font-normal">{{
                    item.metadata.model_name
                  }}</Badge>
                </div>
              </div>

              <div v-if="item.metadata.sampler_name">
                <div class="text-muted-foreground mb-1 text-xs">Sampler</div>
                <div class="font-medium">{{ item.metadata.sampler_name }}</div>
              </div>

              <div v-if="item.metadata.cfg">
                <div class="text-muted-foreground mb-1 text-xs">CFG Scale</div>
                <div class="font-medium">{{ item.metadata.cfg }}</div>
              </div>

              <div v-if="item.metadata.steps">
                <div class="text-muted-foreground mb-1 text-xs">Steps</div>
                <div class="font-medium">{{ item.metadata.steps }}</div>
              </div>

              <div v-if="item.metadata.seed">
                <div class="text-muted-foreground mb-1 text-xs">Seed</div>
                <div class="font-mono text-xs">{{ item.metadata.seed }}</div>
              </div>

              <div v-if="item.metadata.scheduler">
                <div class="text-muted-foreground mb-1 text-xs">Scheduler</div>
                <div class="font-medium">{{ item.metadata.scheduler }}</div>
              </div>
            </div>
          </div>

          <Separator />

          <!-- Resources / LoRAs (Placeholder for future) -->
          <div class="space-y-2">
            <h3 class="text-sm font-semibold">Resources</h3>
            <div
              class="border-muted-foreground/20 text-muted-foreground rounded-lg border border-dashed p-3 text-center text-xs"
            >
              No additional resources detected
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  </div>
</template>
