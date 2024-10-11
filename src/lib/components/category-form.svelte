<script lang="ts">
	import { dbManager } from '$lib/rxdb/db';

	let label = $state('');

	async function handleSubmit() {
		const db = await dbManager.getDB();
		await db.category.insert({ id: crypto.randomUUID(), label });
		label = '';
	}
</script>

<form onsubmit={handleSubmit}>
	<input type="text" bind:value={label} placeholder="Groceris, Rent, etc." />
	<button type="submit">Add Category</button>
</form>
