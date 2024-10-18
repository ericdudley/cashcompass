<script lang="ts">
	import { dbManager } from '$lib/rxdb/db';
	import type { Category } from '$lib/rxdb/models/types';
	import TrashIcon from 'virtual:icons/mdi/trash';
	import DisplayInput from './ui/display-input.svelte';
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

<ul class="list-none flex flex-col gap-2">
	{#each categories as category}
		<li class="flex items-center justify-between">
			<span class="flex items-center text-sm font-medium me-3"
				><span class="flex w-2.5 h-2.5 bg-blue-600 rounded-full me-1.5 flex-shrink-0"></span>
				<DisplayInput value={category.label} onSave={(value) => handleChange(category.id, value)} />
			</span>
			<button
				class="btn btn-square btn-sm btn-error btn-ghost"
				onclick={() => handleDelete(category.id)}
			>
				<TrashIcon />
			</button>
		</li>
	{/each}
</ul>
