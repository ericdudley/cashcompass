<script lang="ts">
	import CreateIcon from '$lib/components/ui/icons/create-icon.svelte';
	import { getDbContext } from '$lib/context';
	import { liveQuery } from 'dexie';
	import CurrencyInput from './ui/currency-input.svelte';
	import DateInput from './ui/date-input.svelte';
	import { format } from 'date-fns';
	import CategoryCombobox from './ui/category-combobox.svelte';

	let { label = $bindable('') }: { label: string } = $props();

	let unixMs = $state(Date.now());
	let amount = $state(0);
	let categoryId = $state('');

	const db = getDbContext();

	const categories = $derived.by(() => {
		return liveQuery(() => db.category.toArray());
	});

	async function handleSubmit(event: Event) {
		event.preventDefault();

		const selectedCategory = await db.category.get(categoryId);

		await db.tx.add({
			id: crypto.randomUUID(),
			label,
			amount,
			category: selectedCategory!,
			unixMs,
			yyyyMMDd: format(unixMs, 'yyyy-MM-dd')
		});

		label = '';
		amount = 0;
		categoryId = '';
	}
</script>

<form class="flex flex-col gap-4" onsubmit={handleSubmit}>
	<div class="form-control">
		<div class="label">
			<span class="label-text">Date</span>
		</div>
		<DateInput bind:unixMs />
	</div>

	<div class="form-control">
		<div class="label">
			<span class="label-text">Label</span>
		</div>
		<input
			type="text"
			id="label-input"
			value={label}
			oninput={(e) => {
				label = (e.target as HTMLInputElement).value;
			}}
			class="input w-full input-bordered"
			placeholder="Transaction label"
			required
			autofocus
		/>
	</div>

	<div class="form-control">
		<div class="label">
			<span class="label-text">Amount</span>
		</div>
		<CurrencyInput bind:value={amount} />
	</div>

	<div class="form-control">
		<div class="label">
			<span class="label-text">Category</span>
		</div>
		<CategoryCombobox bind:selectedCategoryId={categoryId} />
	</div>

	<button type="submit" class="btn btn-primary flex items-center gap-2">
		<CreateIcon />
		<span>Create Transaction</span>
	</button>
</form>
