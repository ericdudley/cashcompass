<script lang="ts">
	import { dbManager } from '$lib/rxdb/db';
	import type { Category } from '$lib/rxdb/models/types';

	let { prefix }: { prefix: string } = $props();

	let categories: Category[] = $state([]);
	$effect(() => {
		prefix;

		dbManager.getDB().then((db) => {
			db.category
				.find({
					selector: {
						label: {
							$regex: `^${prefix || '.*'}`
						}
					}
				})
				.$.subscribe((newCategories) => {
					console.log('NEW', newCategories);
					categories = newCategories;
				});
		});
	});

	async function handleChange(id: string, label: string) {
		const db = await dbManager.getDB();
		await db.category.find({ selector: { id } }).modify((category) => {
			category.label = label;
			return category;
		});
	}

	async function handleDelete(id: string) {
		const db = await dbManager.getDB();
		await db.category
			.find({
				selector: {
					id
				}
			})
			.remove();
	}
</script>

<ul>
	{#each categories as category}
		<li>
			<input
				type="text"
				bind:value={category.label}
				oninput={(e) => handleChange(category.id, e.currentTarget?.value ?? '')}
			/>
			<button class="btn btn-error" onclick={() => handleDelete(category.id)}> Delete </button>
		</li>
	{/each}
</ul>
