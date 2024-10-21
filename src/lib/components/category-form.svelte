<script lang="ts">
	import CreateIcon from '$lib/components/ui/icons/create-icon.svelte';
	import { getDbContext } from '$lib/context';

	let { label = $bindable('') }: { label: string } = $props();

	const db = getDbContext();

	async function handleSubmit() {
		await db.category.add({ id: crypto.randomUUID(), label });
		label = '';
	}
</script>

<form class="flex items-center w-full" onsubmit={handleSubmit}>
	<label for="simple-search" class="sr-only">Search</label>
	<div class="flex items-center gap-2 w-full justify-between">
		<div class="relative w-full">
			<input
				type="text"
				bind:value={label}
				id="simple-search"
				class="input w-full flex-1 input-bordered"
				placeholder="Search categories"
				required
				autofocus
			/>
			{#if !!label}
				<span
					class="absolute left-0 bottom-0 text-xs font-medium text-neutral-400 transform translate-y-[120%] translate-x-0.5"
				>
					Submit to create a new category
				</span>
			{/if}
		</div>
		<button type="submit" class="btn btn-primary btn-square">
			<CreateIcon />
			<span class="sr-only">Create</span>
		</button>
	</div>
</form>
