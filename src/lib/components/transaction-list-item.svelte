<script lang="ts">
	import { getDbContext } from '$lib/context';
	import type { Transaction } from '$lib/dexie/models/transaction';
	import { formatAmount } from '$lib/format';
	import { parse } from 'date-fns';
	import TrashIcon from 'virtual:icons/mdi/trash';
	import CategoryCombobox from './category-combobox.svelte';
	import CategoryPill from './category-pill.svelte';
	import CurrencyInput from './ui/currency-input.svelte';
	import DateInput from './ui/date-input.svelte';
	import EditableField from './ui/editable-field.svelte';
	import ClockIcon from './ui/icons/clock-icon.svelte';
	import TransactionIcon from './ui/icons/transaction-icon.svelte';
	import AccountCombobox from './account-combobox.svelte';
	import AccountPill from './account-pill.svelte';

	let { transaction }: { transaction: Transaction } = $props();

	const db = getDbContext();

	async function onAmountChange(amount: number) {
		await db.tx.update(transaction.id, { amount });
	}

	async function onLabelChange(label: string) {
		await db.tx.update(transaction.id, { label });
	}

	async function onAccountChange(accountId: string) {
		const account = await db.account.get(accountId);
		if (!account) {
			alert('Account not found');
			return;
		}
		await db.tx.update(transaction.id, { account });
	}

	async function onCategoryChange(categoryId: string) {
		const category = await db.category.get(categoryId);
		if (!category) {
			alert('Category not found');
			return;
		}
		await db.tx.update(transaction.id, { category });
	}

	async function onDateChange(iso8601: string) {
		await db.tx.update(transaction.id, {
			iso8601
		});
	}

	async function onDelete() {
		if (!confirm('Are you sure you want to delete this transaction?')) return;
		await db.tx.delete(transaction.id);
	}
</script>

<li class="flex flex-col sm:flex-row sm:items-center sm:justify-between sm:flex-wrap p-2">
	<div class="flex items-center text-sm font-medium me-3 gap-1">
		<TransactionIcon />
		<span>
			<EditableField
				value={formatAmount(transaction.amount) || '$0'}
				onSave={(value) => onAmountChange(Number(value))}
				InputComponent={CurrencyInput}
			/>
		</span>
		<EditableField
			value={transaction.label ?? 'Unknown'}
			onSave={(value) => onLabelChange(value)}
		/>
	</div>
	<div class="flex gap-1 items-center">
		{#snippet accountPill()}
			<AccountPill label={transaction.account?.label ?? 'Unknown'} />
		{/snippet}
		<EditableField
			onSave={(value) => onAccountChange(value)}
			value={transaction?.account?.id ?? ''}
			InputComponent={AccountCombobox}
			displaySnippet={accountPill}
		/>
		{#snippet categoryPill()}
			<CategoryPill label={transaction.category?.label ?? 'Unknown'} />
		{/snippet}
		<EditableField
			onSave={(value) => onCategoryChange(value)}
			value={transaction?.category?.id ?? ''}
			InputComponent={CategoryCombobox}
			displaySnippet={categoryPill}
		/>
		{#snippet clock()}
			<ClockIcon />
		{/snippet}
		<EditableField
			onSave={(value) => onDateChange(value)}
			value={transaction.iso8601}
			InputComponent={DateInput}
			displaySnippet={clock}
		/>
		<button class="btn btn-square btn-sm btn-error btn-ghost" onclick={() => onDelete()}>
			<TrashIcon />
		</button>
	</div>
</li>
