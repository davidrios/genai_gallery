<script setup lang="ts">


defineProps<{
  breadcrumbs: Array<{ name: string; path: string }>;
  searchQuery: string;
  sortOrder: 'asc' | 'desc';
}>();

const emit = defineEmits<{
  (e: 'navigate', path: string): void;
  (e: 'update:searchQuery', value: string): void;
  (e: 'search', value: string): void;
  (e: 'toggleSort'): void;
}>();

</script>

<template>
<div class="flex flex-col sm:flex-row justify-between items-center mb-6 gap-4">
  <div class="flex items-center gap-2 overflow-x-auto w-full sm:w-auto">
    <button
        @click="emit('navigate', '')"
        class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        title="Home"
    >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-gray-600 dark:text-gray-300">
        <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
        <polyline points="9 22 9 12 15 12 15 22"></polyline>
        </svg>
    </button>
    <template v-for="crumb in breadcrumbs" :key="crumb.path">
        <span class="text-gray-400">/</span>
        <button
            @click="emit('navigate', crumb.path)"
            class="hover:text-indigo-600 dark:hover:text-indigo-400 font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap"
        >
            {{ crumb.name }}
        </button>
    </template>
  </div>
  
  <div class="flex-1 max-w-lg mx-4">
    <div class="relative group">
        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg class="h-5 w-5 text-gray-400 group-focus-within:text-indigo-500 transition-colors" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
            </svg>
        </div>
        <input 
            :value="searchQuery"
            @input="(e) => {
                emit('update:searchQuery', (e.target as HTMLInputElement).value);
                emit('search', (e.target as HTMLInputElement).value);
            }"
            type="text" 
            class="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg leading-5 bg-white dark:bg-gray-800 placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 sm:text-sm transition-all shadow-sm text-gray-900 dark:text-gray-100" 
            placeholder="Search metadata (e.g. seed:123 or 'cyberpunk')" 
        />
    </div>
  </div>

  <button 
    @click="emit('toggleSort')"
    class="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg shadow-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm font-medium text-gray-700 dark:text-gray-200"
  >
    <span>Sort by Date</span>
    <span class="text-xs uppercase bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded">{{ sortOrder }}</span>
  </button>
</div>
</template>
