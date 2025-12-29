import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { api } from '@/services/api';
import type { Image } from '@/types';

export function useMediaOverlay(images: { value: Image[] }) {
    const router = useRouter();
    const route = useRoute();

    const selectedImage = ref<Image | null>(null);
    const isLoadingDetails = ref(false);

    const openImage = async (image: Image, updateRoute = true) => {
        selectedImage.value = image;
        if (updateRoute) {
            router.replace({ query: { ...route.query, view: image.path } });
        }

        isLoadingDetails.value = true;
        try {
            const details = await api.getImage(image.id);
            // Only update if current is still the one we requested
            if (selectedImage.value?.id === image.id) {
                selectedImage.value = details;
            }
        } catch (e) {
            console.error(e);
        } finally {
            isLoadingDetails.value = false;
        }
    };

    const closeOverlay = (updateRoute = true) => {
        selectedImage.value = null;
        isLoadingDetails.value = false;
        if (updateRoute) {
            const query = { ...route.query };
            delete query.view;
            router.replace({ query });
        }
    };

    const currentImageIndex = computed(() => {
        if (!selectedImage.value) return -1;
        return images.value.findIndex(
            img => img.id === selectedImage.value?.id || img.path === selectedImage.value?.path
        );
    });

    const navigateImage = (dir: 'next' | 'prev') => {
        if (currentImageIndex.value === -1) return;
        const newIdx = dir === 'next' ? currentImageIndex.value + 1 : currentImageIndex.value - 1;
        if (newIdx >= 0 && newIdx < images.value.length) {
            const nextImg = images.value[newIdx];
            if (nextImg) openImage(nextImg);
        }
    };

    const handleKeydown = (e: KeyboardEvent) => {
        if (!selectedImage.value) return;
        if (e.key === 'ArrowLeft') navigateImage('prev');
        else if (e.key === 'ArrowRight') navigateImage('next');
        else if (e.key === 'Escape') closeOverlay();
    };

    onMounted(() => {
        window.addEventListener('keydown', handleKeydown);
    });

    onUnmounted(() => {
        window.removeEventListener('keydown', handleKeydown);
    });

    return {
        selectedImage,
        isLoadingDetails,
        openImage,
        closeOverlay,
        navigateImage,
        hasPrevious: computed(() => currentImageIndex.value > 0),
        hasNext: computed(() => currentImageIndex.value !== -1 && currentImageIndex.value < images.value.length - 1),
    };
}
