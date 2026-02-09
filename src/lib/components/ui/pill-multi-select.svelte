<script lang="ts">
	let {
		items,
		selectedIds = $bindable([]),
		displayProperty,
		valueProperty,
		label,
		rows = 3
	} = $props<{
		items: { [key: string]: any }[];
		// `valueProperty` should point to a stable, string ID used in `selectedIds`.
		selectedIds: string[];
		displayProperty: string;
		valueProperty: string;
		label?: string;
		maxWidth?: string;
		rows?: number;
	}>();

	function toggleItem(id: string) {
		if (selectedIds.includes(id)) {
			selectedIds = selectedIds.filter((selectedId: string) => selectedId !== id);
		} else {
			selectedIds = [...selectedIds, id];
		}
	}

	function clearAll() {
		selectedIds = [];
	}

	const hasSelection = $derived(selectedIds.length > 0);
</script>

<div class="flex flex-col gap-2">
	{#if label}
		<div class="flex items-center justify-between">
			<label class="text-sm font-medium">{label}</label>
			{#if hasSelection}
				<button class="btn btn-ghost btn-xs" onclick={clearAll}>Clear</button>
			{/if}
		</div>
	{/if}
	<div
		class="pill-scroll grid gap-2 overflow-x-auto pb-2 -mx-2 px-2 snap-x snap-mandatory"
		style={`grid-auto-flow: column; grid-auto-columns: max-content; grid-template-rows: repeat(${rows}, minmax(0, auto)); align-content: flex-start; -webkit-overflow-scrolling: touch;`}
	>
		{#each items as item}
			{@const id = item[valueProperty]}
			{@const isSelected = selectedIds.includes(id)}
			<button
				class="badge badge-lg flex-shrink-0 cursor-pointer transition-colors snap-start {isSelected
					? 'badge-primary'
					: 'badge-ghost hover:badge-outline'}"
				style="min-height: 2rem; padding: 0.5rem 0.75rem;"
				onclick={() => toggleItem(id)}
			>
				{item[displayProperty]}
			</button>
		{/each}
	</div>
</div>

<style>
	.pill-scroll {
		scrollbar-width: none;
	}

	.pill-scroll::-webkit-scrollbar {
		display: none;
	}
</style>
