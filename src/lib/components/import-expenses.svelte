<script lang="ts">
	import { db } from '$lib/dexie';
	import Papa from 'papaparse';

	let files = $state(null);
	let loading = $state(false);
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

				db.transaction('rw', db.tx, db.category, db.account, async () => {
					const importAccount = {
						id: crypto.randomUUID(),
						label: 'Cash Compass Imported'
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

					for (const tx of data.data) {
						const matchingCategory = categoryMap.get(tx.Category);

						await db.tx.add({
							id: crypto.randomUUID(),
							label: tx.Description,
							amount: -1 * parseFloat(tx.Amount?.replace('$', '').replace(',', '') ?? '0'),
							category: matchingCategory,
							account: importAccount,
							unixMs: new Date(tx.Date).getTime(),
							yyyyMMDd: tx.Date
						});
					}

					loading = false;
				});
			};
			reader.readAsText(files[0]);
		}
	});
</script>

<p>Import your data from the previous version of Cash Compass</p>
<input type="file" class="file-input file-input-bordered w-full max-w-xs" bind:files />

{#if loading}
	<p>Loading...</p>
{/if}
