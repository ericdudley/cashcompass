<script lang="ts">
	import { getDbContext } from '$lib/context';
	import type { Account } from '$lib/dexie/models/account';
	import TrashIcon from 'virtual:icons/mdi/trash';
	import ArchiveIcon from 'virtual:icons/mdi/archive';
	import UnarchiveIcon from 'virtual:icons/mdi/unarchive';
	import EditableField from './ui/editable-field.svelte';
	import AccountIcon from './ui/icons/account-icon.svelte';
	import Tooltip from './ui/tooltip.svelte';

	let { account }: { account: Account } = $props();
	const db = getDbContext();

	async function onLabelChange(label: string) {
		// Update all transactions that reference this account
		db.transaction('rw', db.account, db.tx, async () => {
			await db.account.update(account.id, { label });

			const newAccount = await db.account.get(account.id);

			await db.tx.where('account.id').equals(account.id).modify({ account: newAccount });
		});
	}

	async function onAccountTypeChange(accountType: Account['accountType']) {
		// Update all transactions that reference this account
		db.transaction('rw', db.account, db.tx, async () => {
			await db.account.update(account.id, { accountType });

			const newAccount = await db.account.get(account.id);

			await db.tx.where('account.id').equals(account.id).modify({ account: newAccount });
		});
	}

	async function handleDelete() {
		if (!confirm('Are you sure you want to delete this account?')) return;

		// Update all transactions that reference this account
		db.transaction('rw', db.account, db.tx, async () => {
			await db.account.delete(account.id);

			await db.tx.where('account.id').equals(account.id).modify({ account: undefined });
		});
	}

	async function toggleArchive(isArchived: 0 | 1) {
		await db.account.update(account.id, { isArchived });
	}
</script>

<li class="flex items-center justify-between">
	<span class="flex items-center text-sm font-medium me-3 gap-1">
		<AccountIcon />
		<EditableField value={account.label} onSave={(value) => onLabelChange(value)} />
	</span>
	<div class="ml-auto flex items-center gap-2">
		<div class="join">
			<button
				class="btn btn-xs join-item {account.accountType === 'expenses' && 'btn-primary'}"
				onclick={() => onAccountTypeChange('expenses')}
			>
				Expenses
			</button>
			<button
				class="btn btn-xs join-item {account.accountType === 'net_worth' && 'btn-primary'}"
				onclick={() => onAccountTypeChange('net_worth')}
			>
				Net Worth
			</button>
		</div>
		<Tooltip tip={account.isArchived ? 'Unarchive' : 'Archive'}>
			<button
				class="btn btn-square btn-sm btn-ghost"
				onclick={() => toggleArchive(account.isArchived === 0 ? 1 : 0)}
				title={account.isArchived === 0 ? 'Archive account' : 'Unarchive account'}
			>
				{#if account.isArchived === 0}
					<ArchiveIcon />
				{:else}
					<UnarchiveIcon />
				{/if}
			</button>
		</Tooltip>
		<button class="btn btn-square btn-sm btn-error btn-ghost" onclick={() => handleDelete()}>
			<TrashIcon />
		</button>
	</div>
</li>
