export interface ComfyMetadata {
  prompt?: string
  negative_prompt?: string
  seed?: number
  steps?: number
  cfg?: number
  sampler_name?: string
  scheduler?: string
  model_name?: string
  positive_prompt?: string
  [key: string]: unknown
}

export interface MediaItem {
  id: string
  url: string
  type: 'image' | 'video'
  name: string
  width: number
  height: number
  createdAt: Date
  metadata: ComfyMetadata
}
