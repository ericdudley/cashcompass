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

	let { transaction }: { transaction: Transaction } = $props();

	const db = getDbContext();

	async function onAmountChange(amount: number) {
		await db.tx.update(transaction.id, { amount });
	}

	async function onLabelChange(label: string) {
		await db.tx.update(transaction.id, { label });
	}

	async function onCategoryChange(categoryId: string) {
		const category = await db.category.get(categoryId);
		if (!category) {
			alert('Category not found');
			return;
		}
		await db.tx.update(transaction.id, { category });
	}

	async function onDateChange(yyyyMMDd: string) {
		await db.tx.update(transaction.id, {
			unixMs: parse(yyyyMMDd, 'yyyy-MM-dd', Date.now()).getTime(),
			yyyyMMDd
		});
	}

	async function onDelete() {
		if (!confirm('Are you sure you want to delete this transaction?')) return;
		await db.tx.delete(transaction.id);
	}
</script>

<li class="flex items-center justify-between">
	<span class="flex items-center text-sm font-medium me-3 gap-1">
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
		<!-- <DisplayInput value={transaction.label ?? 'Unknown'} onSave={(value) => onLabelChange(value)} /> -->
	</span>
	<div class="flex gap-1 items-center">
		{#if transaction.category}
			{#snippet categoryPill()}
				<CategoryPill label={transaction.category?.label ?? 'Unknown'} />
			{/snippet}
			<EditableField
				onSave={(value) => onCategoryChange(value)}
				value={transaction.category.id}
				InputComponent={CategoryCombobox}
				displaySnippet={categoryPill}
			/>
		{/if}
		{#snippet clock()}
			<ClockIcon />
		{/snippet}
		<EditableField
			onSave={(value) => onDateChange(value)}
			value={transaction.yyyyMMDd}
			InputComponent={DateInput}
			displaySnippet={clock}
		/>
		<button class="btn btn-square btn-sm btn-error btn-ghost" onclick={() => onDelete()}>
			<TrashIcon />
		</button>
	</div>
</li>
