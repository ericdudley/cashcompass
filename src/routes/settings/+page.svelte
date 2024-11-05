<script lang="ts">
	import ImportAccounts from '$lib/components/import-accounts.svelte';
	import ImportExpenses from '$lib/components/import-expenses.svelte';
	import { getDbContext } from '$lib/context';
	import { deleteAllData } from '$lib/dexie/utils/common';

	let isDeleting = $state(false);

	async function onDeleteAllData() {
		if (!confirm('Are you sure you want to delete all data?')) return;
		isDeleting = true;
		try {
			await deleteAllData();
		} finally {
			isDeleting = false;
		}
	}
</script>

<div class="flex flex-col gap-8">
	<ImportExpenses />

	<ImportAccounts />

	<button class="btn btn-warning w-fit" onclick={onDeleteAllData}> Delete all data </button>
	{#if isDeleting}
		<div class="text-warning">Deleting...</div>
	{/if}
</div>
