<script setup lang="ts">
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, Settings, FolderOpen } from 'lucide-vue-next'
import { useGalleryStore } from '@/stores/gallery'

const store = useGalleryStore()
</script>

<template>
  <header
    class="bg-background/80 supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50 w-full border-b backdrop-blur-md"
  >
    <div class="container mx-auto flex h-16 items-center gap-4 px-4">
      <div class="text-xl font-bold tracking-tight">GenAIGallery</div>

      <div class="flex-1">
        <div class="relative">
          <Search class="text-muted-foreground absolute top-2.5 left-2.5 h-4 w-4" />
          <Input
            type="search"
            placeholder="Search prompts, models, seeds..."
            class="border-transparent pl-9"
            @input="(e: Event) => store.setSearchQuery((e.target as HTMLInputElement).value)"
          />
        </div>
      </div>

      <div class="ml-auto flex items-center gap-2">
        <Button variant="outline" size="sm">
          <FolderOpen />
          Folders
        </Button>
        <Button variant="ghost" size="icon-sm">
          <Settings />
        </Button>
      </div>
    </div>
  </header>
</template>
