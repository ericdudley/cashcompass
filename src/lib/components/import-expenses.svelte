<script lang="ts">
	import { db } from '$lib/dexie';
	import type { Account } from '$lib/dexie/models/account';
	import Papa from 'papaparse';
	import { startOfDay, parseISO } from 'date-fns';
	import { asTransaction } from '$lib/dexie/models/transaction';
	import { UNKNOWN_LABELS } from '$lib/dexie/utils/common';

	let files = $state(null);
	let loading = $state(false);
	let exporting = $state(false);

	$effect(() => {
		if (files) {
			const reader = new FileReader();
			reader.onload = async (event) => {
				const result = event.target?.result;
				if (!result || typeof result !== 'string') {
					return;
				}
				loading = true;

				const data = Papa.parse<{
					Amount: string;
					Category: string;
					Date: string;
					Description: string;
				}>(result, { header: true });

				console.log('data', data);

				await db.transaction('rw', db.tx, db.category, db.account, async () => {
					const importAccount: Account = {
						id: crypto.randomUUID(),
						label: `Imported Expenses ${new Date().toISOString()}`,
						accountType: 'expenses'
					};
					await db.account.add(importAccount);

					const categories = await db.category.toArray();

					// First, create all categories
					const categoryMap = new Map<string, { id: string; label: string }>();
					for (const tx of data.data) {
						if (!categoryMap.has(tx.Category)) {
							let matchingCategory = categories.find((c) => c.label === tx.Category);

							if (!matchingCategory) {
								matchingCategory = {
									id: crypto.randomUUID(),
									label: tx.Category
								};

								await db.category.add(matchingCategory);
								categories.push(matchingCategory);
							}

							categoryMap.set(tx.Category, matchingCategory);
						}
					}
					try {
						for (let i = 0; i < data.data.length; i++) {
							const tx = data.data[i];
							const matchingCategory = categoryMap.get(tx.Category);

							if (!tx.Date) {
								console.error('No date for tx', tx);
								continue;
							}

							const dateAtMidnight = startOfDay(parseISO(tx.Date)).toISOString();

							console.count(`adding tx ${i + 1}/${data.data.length}`);

							console.log(tx);
							await db.tx.add(
								asTransaction({
									id: crypto.randomUUID(),
									label: tx.Description,
									amount: -1 * parseFloat(tx.Amount?.replace('$', '').replace(',', '') ?? '0'),
									category: matchingCategory,
									account: importAccount,
									iso8601: dateAtMidnight
								})
							);
							console.log('DONE');
						}
					} catch (e) {
						console.error(e);
						throw e;
					}

					console.log('DONE!');

					loading = false;
				});
			};
			reader.readAsText(files[0]);
		}
	});

	async function exportData() {
		exporting = true;

		// Get all transactions
		const transactions = await db.tx.where('account.accountType').equals('expenses').toArray();

		// Prepare the export data array
		const exportDataArray = transactions.map((tx) => {
			return {
				Amount: (-tx.amount).toFixed(2),
				Category: tx.category?.label ?? UNKNOWN_LABELS.category,
				Date: tx.iso8601,
				Description: tx.label
			};
		});

		// Convert the export data to CSV format
		const csv = Papa.unparse(exportDataArray);

		// Create a Blob from the CSV
		const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });

		// Create a link and trigger download
		const url = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.setAttribute('href', url);
		link.setAttribute('download', 'export.csv');
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);

		// Clean up
		URL.revokeObjectURL(url);

		exporting = false;
	}
</script>

<p>Import your data from the previous version of Cash Compass</p>
<input type="file" class="file-input file-input-bordered w-full max-w-xs" bind:files />

{#if loading}
	<p>Loading...</p>
{/if}

<button class="btn btn-primary" onclick={exportData} disabled={exporting}>
	{#if exporting}
		Exporting...
	{:else}
		Export Data
	{/if}
</button>
