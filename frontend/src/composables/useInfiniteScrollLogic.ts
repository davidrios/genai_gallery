import { ref, nextTick } from 'vue';
import { useIntersectionObserver, useInfiniteScroll as useVueUseInfiniteScroll } from '@vueuse/core';

interface ScrollOptions {
    loadUp: () => Promise<boolean>;
    loadDown: () => Promise<boolean>;
    canLoadUp: () => boolean;
    canLoadDown: () => boolean;
    isLoading: () => boolean;
}

export function useInfiniteScrollLogic(options: ScrollOptions) {
    const topSentinel = ref<HTMLElement | null>(null);
    const isFetchingPrev = ref(false);
    const isFetchingNext = ref(false);

    // Scroll Up
    useIntersectionObserver(topSentinel, async (entries) => {
        const entry = entries[0];
        if (entry?.isIntersecting && !isFetchingPrev.value && options.canLoadUp() && !options.isLoading()) {
            isFetchingPrev.value = true;
            const success = await options.loadUp();

            if (success) {
                // Scroll restoration logic
                const oldHeight = document.documentElement.scrollHeight;
                const oldScrollTop = document.documentElement.scrollTop;

                await nextTick();

                const newHeight = document.documentElement.scrollHeight;
                document.documentElement.scrollTop = oldScrollTop + (newHeight - oldHeight);
            }
            isFetchingPrev.value = false;
        }
    }, { threshold: 0.1 });

    // Scroll Down
    useVueUseInfiniteScroll(
        window,
        async () => {
            if (options.isLoading() || isFetchingNext.value || !options.canLoadDown()) return;

            isFetchingNext.value = true;
            await options.loadDown();
            isFetchingNext.value = false;
        },
        { distance: 100 }
    );

    return {
        topSentinel,
        isFetchingPrev,
        isFetchingNext
    };
}
