<script lang="ts">
	import CreateIcon from '$lib/components/ui/icons/create-icon.svelte';
	import { getDbContext } from '$lib/context';
	import { parseISO } from 'date-fns';
	import { liveQuery } from 'dexie';
	import ComboBox from './ui/combobox.svelte';
	import CurrencyInput from './ui/currency-input.svelte';
	import DateInput from './ui/date-input.svelte';
	import MinusIcon from './ui/icons/minus-icon.svelte';
	import PlusIcon from './ui/icons/plus-icon.svelte';
	import { format } from 'date-fns';

	let label = $state('');
	let dateString = $state(format(new Date(), 'yyyy-MM-dd'));
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

		// Convert dateString to Unix milliseconds if needed
		const unixMs = parseISO(dateString).getTime();

		await db.tx.add({
			id: crypto.randomUUID(),
			label,
			amount: isDebit ? -amount : amount,
			category: selectedCategory!,
			account: selectedAccount!,
			unixMs,
			yyyyMMDd: dateString
		});

		// Reset form fields
		label = '';
		amount = 0;
		categoryId = '';
		dateString = format(new Date(), 'yyyy-MM-dd');
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

<form class="flex flex-col gap-2" onsubmit={handleSubmit}>
	<div class="form-control">
		<div class="label">
			<span class="label-text">Date</span>
		</div>
		<DateInput bind:value={dateString} />
	</div>

	<div class="form-control">
		<div class="label">
			<span class="label-text">Label</span>
		</div>
		<input
			type="text"
			id="label-input"
			bind:value={label}
			class="input w-full input-bordered input-sm"
			placeholder="Transaction label"
			required
			autofocus
		/>
		<div class="join flex items-center mt-2">
			<button
				type="button"
				class="btn btn-sm join-item flex-1 {isDebit ? 'btn-info' : ''}"
				onclick={() => (isDebit = true)}
			>
				<MinusIcon />
				<span>Debit</span>
			</button>
			<button
				type="button"
				class="btn btn-sm join-item flex-1 {!isDebit ? 'btn-info' : ''}"
				onclick={() => (isDebit = false)}
			>
				<PlusIcon />
				<span>Credit</span>
			</button>
		</div>
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
			bind:value={categoryId}
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
			bind:value={accountId}
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
