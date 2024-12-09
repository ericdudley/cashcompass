<script lang="ts">
	import { BrowserStorage } from '$lib/browser-storage';
	import CreateIcon from '$lib/components/ui/icons/create-icon.svelte';
	import { getDbContext } from '$lib/context';
	import type { Account } from '$lib/dexie/models/account';
	import { asTransaction } from '$lib/dexie/models/transaction';
	import { currentIso8601 } from '$lib/utils/date';
	import { liveQuery } from 'dexie';
	import { onMount } from 'svelte';
	import ComboBox from './ui/combobox.svelte';
	import CurrencyInput from './ui/currency-input.svelte';
	import DateInput from './ui/date-input.svelte';
	import MinusIcon from './ui/icons/minus-icon.svelte';
	import PlusIcon from './ui/icons/plus-icon.svelte';
	import AccountIcon from './ui/icons/account-icon.svelte';
	import { getLatestBalance, getTransactionsForAccount } from '$lib/dexie/utils/transactions';

	let label = $state('');
	let iso8601 = $state(currentIso8601());
	let amount = $state(0);
	let categoryId = $state('');
	let accountId = $state('');
	let transactionAmountType = $state<'debit' | 'credit' | 'reconcile'>('debit');

	const db = getDbContext();

	const categories = $derived.by(() => {
		return liveQuery(() => db.category.toArray());
	});

	const accounts = $derived.by(() => {
		return liveQuery(() => db.account.toArray());
	});

	async function handleSubmit(event: Event) {
		event.preventDefault();

		// Save the last account id to local storage
		BrowserStorage.from(localStorage).patchItem('localSettings', { lastAccountId: accountId });

		const selectedCategory = await db.category.get(categoryId);
		const selectedAccount = await db.account.get(accountId);

		let usedAmount = amount;
		if (transactionAmountType === 'reconcile') {
			const transactions = await getTransactionsForAccount(accountId);
			const latestBalance = getLatestBalance(transactions);
			usedAmount = amount - latestBalance;
		}

		await db.tx.add(
			asTransaction({
				id: crypto.randomUUID(),
				label,
				amount: transactionAmountType === 'debit' ? -usedAmount : usedAmount,
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

	onMount(() => {
		const lastAccountId = BrowserStorage.from(localStorage).getItem('localSettings')?.lastAccountId;

		if (lastAccountId) {
			accountId = lastAccountId;
		}
	});
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
	</div>

	<div class="form-control">
		<div class="label">
			<span class="label-text">Amount</span>
		</div>
		<CurrencyInput bind:value={amount} />
		<div class="join flex items-center mt-2">
			<button
				type="button"
				class="btn btn-xs join-item flex-1 {transactionAmountType === 'debit' ? 'btn-info' : ''}"
				onclick={() => {
					transactionAmountType = 'debit';
				}}
				tabindex={-1}
			>
				<MinusIcon />
				<span>Debit</span>
			</button>

			<button
				type="button"
				class="btn btn-xs join-item flex-1 {transactionAmountType === 'reconcile'
					? 'btn-info'
					: ''}"
				onclick={() => {
					// FIXME This is a nice helper, but it should probably be a user setting.
					const reconciliationCategoryId = $categories?.find((category) =>
						category?.label?.startsWith('Reconcil')
					)?.id;
					if (reconciliationCategoryId) {
						categoryId = reconciliationCategoryId;
					}
					transactionAmountType = 'reconcile';
				}}
				tabindex={-1}
			>
				<AccountIcon />
				<span>Reconcile</span>
			</button>
			<button
				type="button"
				class="btn btn-xs join-item flex-1 {transactionAmountType === 'credit' ? 'btn-info' : ''}"
				onclick={() => {
					transactionAmountType = 'credit';
				}}
				tabindex={-1}
			>
				<PlusIcon />
				<span>Credit</span>
			</button>
		</div>
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

	<button type="submit" class="btn btn-primary flex items-center gap-2 mt-4">
		<CreateIcon />
		<span>Create Transaction</span>
	</button>
</form>
