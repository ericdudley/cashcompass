<script lang="ts">
	import CreateIcon from '$lib/components/ui/icons/create-icon.svelte';
	import { getDbContext } from '$lib/context';
	import { liveQuery } from 'dexie';

	let { label = $bindable('') }: { label: string } = $props();

	let amount = $state(0);
	let categoryId = $state('');

	const db = getDbContext();

	const categories = $derived.by(() => {
		return liveQuery(() => db.category.toArray());
	});

	async function handleSubmit(event: Event) {
		event.preventDefault();

		const selectedCategory = $categories?.find((c) => c.id === categoryId) || {
			id: '',
			label: ''
		};

		await db.tx.add({
			id: crypto.randomUUID(),
			label,
			amount: amount,
			category: selectedCategory,
			unixMs: Date.now(),
			yyyyMMDd: new Date().toISOString().slice(0, 10)
		});

		label = '';
		amount = 0;
		categoryId = '';
	}
</script>

<form class="flex flex-col gap-4" onsubmit={handleSubmit}>
	<div>
		<label for="label-input" class="block text-sm font-medium">Label</label>
		<input
			type="text"
			id="label-input"
			value={label}
			oninput={(e) => {
				label = e.target.value;
			}}
			class="input w-full input-bordered"
			placeholder="Transaction label"
			required
			autofocus
		/>
	</div>

	<div>
		<label for="amount-input" class="block text-sm font-medium">Amount</label>
		<input
			type="number"
			id="amount-input"
			value={amount}
			oninput={(e) => {
				amount = parseFloat(e.target.value);
			}}
			class="input w-full input-bordered"
			placeholder="Transaction amount"
			required
		/>
	</div>

	<div>
		<label for="category-select" class="block text-sm font-medium">Category</label>
		<select
			id="category-select"
			value={categoryId}
			onchange={(e) => {
				categoryId = e.target.value;
			}}
			class="select w-full select-bordered"
			required
		>
			{#if $categories}
				<option value="" disabled selected>Select category</option>
				{#each $categories as category}
					<option value={category.id}>{category.label}</option>
				{/each}
			{/if}
		</select>
	</div>

	<button type="submit" class="btn btn-primary flex items-center gap-2">
		<CreateIcon />
		<span>Create Transaction</span>
	</button>
</form>
