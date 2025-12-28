import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { MediaItem } from '@/types'

export const useGalleryStore = defineStore('gallery', () => {
  const items = ref<MediaItem[]>([
    {
      id: '1',
      url: 'https://placehold.co/600x800/18181b/FFF?text=Cyberpunk+City',
      type: 'image',
      name: 'Cyberpunk City',
      width: 600,
      height: 800,
      createdAt: new Date(),
      metadata: {
        prompt: 'cyberpunk city, neon lights, rain, 8k, masterpiece',
        negative_prompt: 'blur, low quality, distortion, ugly, text, watermark',
        seed: 123456789,
        steps: 30,
        cfg: 7,
        sampler_name: 'euler_a',
        model_name: 'sd_xl_base_1.0.safetensors',
      },
    },
    {
      id: '2',
      url: 'https://placehold.co/800x600/27272a/FFF?text=Landscape',
      type: 'image',
      name: 'Mountain Landscape',
      width: 800,
      height: 600,
      createdAt: new Date(),
      metadata: {
        prompt: 'mountain landscape, snowy peaks, river, sunset',
        negative_prompt: 'people, buildings, cars, low res',
        seed: 987654321,
        steps: 25,
        cfg: 6.5,
        sampler_name: 'dpmpp_2m_karras',
        model_name: 'dreamshaper_8.safetensors',
      },
    },
    {
      id: '3',
      url: 'https://placehold.co/600x600/3f3f46/FFF?text=Portrait',
      type: 'image',
      name: 'Future Portrait',
      width: 600,
      height: 600,
      createdAt: new Date(),
      metadata: {
        prompt: 'portrait of a cyborg woman, intricate details',
        seed: 1122334455,
        steps: 40,
        cfg: 8,
        sampler_name: 'euler',
        model_name: 'realistic_vision_v5.safetensors',
      },
    },
    {
      id: '4',
      url: 'https://placehold.co/500x800/52525b/FFF?text=Abstract',
      type: 'image',
      name: 'Abstract Fluid',
      width: 500,
      height: 800,
      createdAt: new Date(),
      metadata: {
        prompt: 'abstract fluid art, colorful, swirling',
        seed: 5544332211,
        steps: 20,
        cfg: 5,
        sampler_name: 'uni_pc',
        model_name: 'sd_1.5.safetensors',
      },
    },
    {
      id: '5',
      url: 'https://placehold.co/900x600/18181b/FFF?text=Space+Station',
      type: 'image',
      name: 'Space Station',
      width: 900,
      height: 600,
      createdAt: new Date(),
      metadata: {
        prompt: 'space station orbiting earth, photorealistic',
        seed: 6677889900,
        steps: 50,
        cfg: 9,
        sampler_name: 'heun',
        model_name: 'juggernaut_xl.safetensors',
      },
    },
    {
      id: '1',
      url: 'https://placehold.co/600x800/18181b/FFF?text=Cyberpunk+City',
      type: 'image',
      name: 'Cyberpunk City',
      width: 600,
      height: 800,
      createdAt: new Date(),
      metadata: {
        prompt: 'cyberpunk city, neon lights, rain, 8k, masterpiece',
        negative_prompt: 'blur, low quality, distortion, ugly, text, watermark',
        seed: 123456789,
        steps: 30,
        cfg: 7,
        sampler_name: 'euler_a',
        model_name: 'sd_xl_base_1.0.safetensors',
      },
    },
    {
      id: '2',
      url: 'https://placehold.co/800x600/27272a/FFF?text=Landscape',
      type: 'image',
      name: 'Mountain Landscape',
      width: 800,
      height: 600,
      createdAt: new Date(),
      metadata: {
        prompt: 'mountain landscape, snowy peaks, river, sunset',
        negative_prompt: 'people, buildings, cars, low res',
        seed: 987654321,
        steps: 25,
        cfg: 6.5,
        sampler_name: 'dpmpp_2m_karras',
        model_name: 'dreamshaper_8.safetensors',
      },
    },
    {
      id: '3',
      url: 'https://placehold.co/600x600/3f3f46/FFF?text=Portrait',
      type: 'image',
      name: 'Future Portrait',
      width: 600,
      height: 600,
      createdAt: new Date(),
      metadata: {
        prompt: 'portrait of a cyborg woman, intricate details',
        seed: 1122334455,
        steps: 40,
        cfg: 8,
        sampler_name: 'euler',
        model_name: 'realistic_vision_v5.safetensors',
      },
    },
    {
      id: '4',
      url: 'https://placehold.co/500x800/52525b/FFF?text=Abstract',
      type: 'image',
      name: 'Abstract Fluid',
      width: 500,
      height: 800,
      createdAt: new Date(),
      metadata: {
        prompt: 'abstract fluid art, colorful, swirling',
        seed: 5544332211,
        steps: 20,
        cfg: 5,
        sampler_name: 'uni_pc',
        model_name: 'sd_1.5.safetensors',
      },
    },
    {
      id: '5',
      url: 'https://placehold.co/900x600/18181b/FFF?text=Space+Station',
      type: 'image',
      name: 'Space Station',
      width: 900,
      height: 600,
      createdAt: new Date(),
      metadata: {
        prompt: 'space station orbiting earth, photorealistic',
        seed: 6677889900,
        steps: 50,
        cfg: 9,
        sampler_name: 'heun',
        model_name: 'juggernaut_xl.safetensors',
      },
    },
  ])

  const searchQuery = ref('')

  const filteredItems = computed(() => {
    if (!searchQuery.value) return items.value
    const query = searchQuery.value.toLowerCase()
    return items.value.filter((item) => {
      // Search in name or prompt metadata
      return (
        item.name.toLowerCase().includes(query) ||
        (item.metadata.prompt && item.metadata.prompt.toLowerCase().includes(query))
      )
    })
  })

  function addItem(item: MediaItem) {
    items.value.push(item)
  }

  function setSearchQuery(query: string) {
    searchQuery.value = query
  }

  return { items, addItem, searchQuery, setSearchQuery, filteredItems }
})
