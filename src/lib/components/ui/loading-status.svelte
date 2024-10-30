<script lang="ts">
	import CircularLoader from './circular-loader.svelte';

	let { items, label } = $props<{ items: unknown[] | undefined | null; label?: string }>();
</script>

{#if !items}
	<CircularLoader class="mx-auto self-center" isAbsolute={false} />
{:else if items.length === 0}
	<p>No {label ?? 'items'} found</p>
{/if}
