<script lang="ts">
	import { dbManager } from '$lib/rxdb/db';
	import CreateIcon from '$lib/components/ui/icons/create-icon.svelte';

	let { label = $bindable('') }: { label: string } = $props();

	// let label = $state('');

	async function handleSubmit() {
		const db = await dbManager.getDB();
		await db.category.insert({ id: crypto.randomUUID(), label });
		label = '';
	}
</script>

<form class="flex items-center w-full" onsubmit={handleSubmit}>
	<label for="simple-search" class="sr-only">Search</label>
	<div class="flex items-center gap-2 w-full justify-between">
		<input
			type="text"
			bind:value={label}
			id="simple-search"
			class="input w-full flex-1 input-bordered"
			placeholder="Search categories"
			required
			autofocus
		/>
		<button type="submit" class="btn btn-primary btn-square">
			<CreateIcon />
			<span class="sr-only">Create</span>
		</button>
	</div>
</form>
