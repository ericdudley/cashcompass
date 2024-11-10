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
	import type { Account } from '$lib/dexie/models/account';
	import { asTransaction, type TransactionInput } from '$lib/dexie/models/transaction';
	import { currentIso8601 } from '$lib/utils/date';

	let label = $state('');
	let iso8601 = $state(currentIso8601());
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

		await db.tx.add(
			asTransaction({
				id: crypto.randomUUID(),
				label,
				amount: isDebit ? -amount : amount,
				category: selectedCategory!,
				account: selectedAccount!,
				iso8601
			})
		);

		// Reset form fields
		label = '';
		amount = 0;
		categoryId = '';
		iso8601 = currentIso8601();
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
		const newAccount: Account = {
			id: crypto.randomUUID(),
			label: inputValue,
			accountType: 'expenses'
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
		<DateInput bind:value={iso8601} />
	</div>

	<div class="form-control">
		<div class="label">
			<span class="label-text">Label</span>
		</div>
		<!-- svelte-ignore a11y_autofocus -->
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
