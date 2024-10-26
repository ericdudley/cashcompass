<script lang="ts">
	import CreateIcon from '$lib/components/ui/icons/create-icon.svelte';
	import { getDbContext } from '$lib/context';
	import { liveQuery } from 'dexie';
	import CurrencyInput from './ui/currency-input.svelte';
	import DateInput from './ui/date-input.svelte';
	import { format } from 'date-fns';
	import ComboBox from './ui/combobox.svelte';
	import PlusIcon from './ui/icons/plus-icon.svelte';
	import MinusIcon from './ui/icons/minus-icon.svelte';

	let { label = $bindable('') }: { label: string } = $props();

	let unixMs = $state(Date.now());
	let amount = $state(0);
	let categoryId = $state('');
	let accountId = $state('');
	let isDebit = $state(true);

	const db = getDbContext();

	const categories = $derived.by(() => {
		return liveQuery(() => db.category.toArray());
	});

	const accounts = $derived.by(() => {
		return liveQuery(() => db.account.toArray());
	});

	async function handleSubmit(event: Event) {
		event.preventDefault();

		const selectedCategory = await db.category.get(categoryId);
		const selectedAccount = await db.account.get(accountId);

		await db.tx.add({
			id: crypto.randomUUID(),
			label,
			amount: isDebit ? -amount : amount,
			category: selectedCategory!,
			account: selectedAccount!,
			unixMs,
			yyyyMMDd: format(unixMs, 'yyyy-MM-dd')
		});

		// Reset form fields
		label = '';
		amount = 0;
		categoryId = '';
	}

	async function createCategory(inputValue: string) {
		const newCategory = {
			id: crypto.randomUUID(),
			label: inputValue
		};
		await db.category.add(newCategory);
		return newCategory;
	}

	async function createAccount(inputValue: string) {
		const newAccount = {
			id: crypto.randomUUID(),
			label: inputValue
		};
		await db.account.add(newAccount);
		return newAccount;
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
			bind:value={label}
			class="input w-full input-bordered"
			placeholder="Transaction label"
			required
			autofocus
		/>
	</div>

	<div class="join flex items-center">
		<button
			type="button"
			class="btn join-item flex-1 {isDebit ? 'btn-info' : ''}"
			onclick={() => (isDebit = true)}
		>
			<MinusIcon />
			<span>Debit</span>
		</button>
		<button
			type="button"
			class="btn join-item flex-1 {!isDebit ? 'btn-info' : ''}"
			onclick={() => (isDebit = false)}
		>
			<PlusIcon />
			<span>Credit</span>
		</button>
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
		<ComboBox
			bind:selectedValue={categoryId}
			items={$categories ? $categories : []}
			displayProperty="label"
			valueProperty="id"
			placeholder="Select or type a category"
			onCreateItem={createCategory}
			required
		/>
	</div>

	<div class="form-control">
		<div class="label">
			<span class="label-text">Account</span>
		</div>
		<ComboBox
			bind:selectedValue={accountId}
			items={$accounts ? $accounts : []}
			displayProperty="label"
			valueProperty="id"
			placeholder="Select or type an account"
			onCreateItem={createAccount}
			required
		/>
	</div>

	<button type="submit" class="btn btn-primary flex items-center gap-2">
		<CreateIcon />
		<span>Create Transaction</span>
	</button>
</form>
