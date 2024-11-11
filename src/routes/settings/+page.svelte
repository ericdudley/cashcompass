<script lang="ts">
	import ImportAccounts from '$lib/components/import-accounts.svelte';
	import ImportExpenses from '$lib/components/import-expenses.svelte';
	import { deleteAllData, repairData } from '$lib/dexie/utils/common';

	let isDeleting = $state(false);
	let isRepairing = $state(false);

	async function onDeleteAllData() {
		if (!confirm('Are you sure you want to delete all data?')) return;
		isDeleting = true;
		try {
			await deleteAllData();
		} catch (error) {
			console.error(error);
			alert('An error occurred while deleting data');
		} finally {
			isDeleting = false;
		}
	}

	async function onRepairData() {
		if (!confirm('Are you sure you want to repair data?')) return;
		isRepairing = true;
		try {
			await repairData();
		} catch (error) {
			console.error(error);
			alert('An error occurred while repairing data');
		} finally {
			isRepairing = false;
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

	<button class="btn btn-danger w-fit" onclick={onRepairData}> Repair data </button>
	{#if isRepairing}
		<div class="text-danger">Repairing...</div>
	{/if}
</div>
