<script lang="ts">
	import TrashIcon from 'virtual:icons/mdi/trash';
	import DisplayInput from './ui/display-input.svelte';
	import { liveQuery } from 'dexie';
	import { getDbContext } from '$lib/context';
	import CategoryIcon from './ui/icons/category-icon.svelte';
	let { prefix }: { prefix: string } = $props();
	const db = getDbContext();

	let categories = $derived.by(() => {
		// noop just to make it reactive
		prefix;

		return liveQuery(() =>
			db.category
				.where('label')
				.startsWithIgnoreCase(prefix ?? '')
				.toArray()
		);
	});

	async function handleChange(id: string, label: string) {
		// Update all transactions that reference this category
		db.transaction('rw', db.category, db.tx, async () => {
			await db.category.update(id, { label });

			await db.tx.where('category.id').equals(id).modify({ category: { id, label } });
		});
	}

	async function handleDelete(id: string) {
		if (!confirm('Are you sure you want to delete this category?')) return;

		// Update all transactions that reference this category
		db.transaction('rw', db.category, db.tx, async () => {
			await db.category.delete(id);

			await db.tx.where('category.id').equals(id).modify({ category: undefined });
		});
	}
</script>

<ul class="list-none flex flex-col gap-2">
	{#if $categories}
		{#each $categories as category}
			<li class="flex items-center justify-between">
				<span class="flex items-center text-sm font-medium me-3 gap-1">
					<CategoryIcon />
					<DisplayInput
						value={category.label}
						onSave={(value) => handleChange(category.id, value)}
					/>
				</span>
				<button
					class="btn btn-square btn-sm btn-error btn-ghost"
					onclick={() => handleDelete(category.id)}
				>
					<TrashIcon />
				</button>
			</li>
		{/each}
		{#if $categories.length === 0}
			<li class="text-sm text-gray-500 mx-auto">No categories found</li>
		{/if}
	{/if}
</ul>
