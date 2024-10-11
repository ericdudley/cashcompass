<script lang="ts">
	import CircularLoader from './circular-loader.svelte';

	let { isLoading, showTitle }: { isLoading?: boolean; showTitle?: boolean } = $props();
</script>

<div class="flex items-center gap-2">
	<div class="flex-shrink-0">
		{#if isLoading}
			<div class="absolute h-12 w-12">
				<CircularLoader size={10} />
			</div>
		{/if}
		<img src="/logo.svg" alt="logo" class="w-10 h-10" />
	</div>
	{#if showTitle}
		<h1 class="text-2xl font-bold">Cash Compass</h1>
	{/if}
</div>
