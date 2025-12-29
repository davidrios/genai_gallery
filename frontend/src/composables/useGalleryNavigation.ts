import { computed, watch, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

// Debounce helper
export const debounce = (fn: Function, ms: number) => {
    let timeoutId: any;
    return (...args: any[]) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn(...args), ms);
    };
};

export function useGalleryNavigation(
    initCallback: () => void,
    isUrlSyncing: { value: boolean }
) {
    const route = useRoute();
    const router = useRouter();

    const currentPath = computed(() => (route.query.path as string) || '');
    const sortOrder = computed(() => (route.query.sort as 'asc' | 'desc') || 'desc');
    const searchQuery = ref((route.query.q as string) || '');

    const breadcrumbs = computed(() => {
        if (!currentPath.value) return [];
        const parts = currentPath.value.split('/');
        let accum = '';
        return parts.map(part => {
            accum = accum ? `${accum}/${part}` : part;
            return { name: part, path: accum };
        });
    });

    const updateRoutePage = debounce((page: number) => {
        const currentUrlPage = parseInt(route.query.page as string) || 1;
        if (page === currentUrlPage) return;

        isUrlSyncing.value = true;
        router.replace({
            query: { ...route.query, page: page.toString() }
        }).catch(() => { }).finally(() => {
            setTimeout(() => { isUrlSyncing.value = false; }, 100);
        });
    }, 300);

    const navigateTo = (path: string) => {
        const query: any = { ...route.query, page: '1' };
        if (path) query.path = path;
        else delete query.path;
        router.push({ query });
    };

    const toggleSort = () => {
        const newSort = sortOrder.value === 'desc' ? 'asc' : 'desc';
        router.push({ query: { ...route.query, sort: newSort, page: '1' } });
    };

    const performSearch = debounce((queryVal: string) => {
        const query: any = { ...route.query, page: '1' };
        if (queryVal) query.q = queryVal;
        else delete query.q;
        router.push({ query });
    }, 500);

    // Watcher for critical route changes
    watch(() => route.query, (newQ, oldQ) => {
        if (isUrlSyncing.value) return;

        const getSig = (q: any) => {
            const { page, view, ...rest } = q;
            return JSON.stringify(rest);
        };

        // Core params changed (path, sort, q)
        if (getSig(newQ) !== getSig(oldQ || {})) {
            initCallback();
        } else {
            // Only page changed, check for jump
            // We defer this check to the consumer usually, or handle initCallback smart logic
            const newPage = parseInt(newQ.page as string) || 1;
            // The consumer (Gallery) will check if this newPage is loaded or needs a full reload
            // We'll pass specific info or let initCallback decide
            initCallback();
        }
    });

    return {
        currentPath,
        sortOrder,
        searchQuery,
        breadcrumbs,
        updateRoutePage,
        navigateTo,
        toggleSort,
        performSearch,
        route
    };
}
