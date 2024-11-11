<script lang="ts">
	import { db } from '$lib/dexie';
	import type { Account } from '$lib/dexie/models/account';
	import { asTransaction } from '$lib/dexie/models/transaction';
	import { getIso8601AtMidnight } from '$lib/utils/date';
	import Papa from 'papaparse';

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
					Account: string;
					Date: string;
					Balance: string;
				}>(result, { header: true });

				await db.transaction('rw', db.tx, db.category, db.account, async () => {
					// Ensure "Reconciliation" category exists
					let reconciliationCategory = await db.category.get({ label: 'Reconciliation' });
					if (!reconciliationCategory) {
						reconciliationCategory = {
							id: crypto.randomUUID(),
							label: 'Reconciliation'
						};
						await db.category.add(reconciliationCategory);
					}

					// Get existing accounts
					const existingAccounts = await db.account.toArray();
					const accountMap = new Map<string, Account>();

					// Create accounts based on the Account column
					for (const row of data.data) {
						const accountLabel = row.Account;
						if (!accountMap.has(accountLabel)) {
							let matchingAccount = existingAccounts.find((a) => a.label === accountLabel);

							if (!matchingAccount) {
								matchingAccount = {
									id: crypto.randomUUID(),
									label: accountLabel,
									accountType: 'net_worth'
								};
								await db.account.add(matchingAccount);
								existingAccounts.push(matchingAccount);
							}

							accountMap.set(accountLabel, matchingAccount);
						}
					}

					// Group data by account
					const accountDataMap = new Map<
						string,
						Array<{ Account: string; Date: string; Balance: string }>
					>();

					for (const row of data.data) {
						const accountLabel = row.Account;
						if (!accountDataMap.has(accountLabel)) {
							accountDataMap.set(accountLabel, []);
						}
						accountDataMap.get(accountLabel)!.push(row);
					}

					// Process balance updates for each account
					for (const [accountLabel, accountData] of accountDataMap) {
						// Sort data by date
						accountData.sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime());

						let previousBalance = 0;
						const account = accountMap.get(accountLabel)!;

						for (const row of accountData) {
							const balanceStr = row.Balance?.replace(/\$|,/g, '') ?? '0';
							const balance = parseFloat(balanceStr);

							const amount = balance - previousBalance;

							if (amount !== 0) {
								await db.tx.add(
									asTransaction({
										id: crypto.randomUUID(),
										label: 'Reconciliation',
										amount: amount,
										category: reconciliationCategory,
										account: account,
										iso8601: getIso8601AtMidnight(row.Date)
									})
								);
							}

							previousBalance = balance;
						}
					}

					loading = false;
				});
			};
			reader.readAsText(files[0]);
		}
	});

	async function exportData() {
		exporting = true;

		// Get all accounts
		const accounts = await db.account.where('accountType').equals('net_worth').toArray();

		// Initialize an array to hold the export data
		const exportDataArray = [];

		// For each account
		for (const account of accounts) {
			// Get all transactions for this account
			const transactions = await db.tx.where('account.id').equals(account.id).toArray();

			// Sort transactions by date
			transactions.sort((a, b) => new Date(a.iso8601).getTime() - new Date(b.iso8601).getTime());

			// Initialize cumulative balance
			let balance = 0;

			// Create a map to hold balance per date
			const dateBalanceMap = new Map<string, number>();

			// For each transaction
			for (const tx of transactions) {
				const date = tx.iso8601;
				balance += tx.amount;

				// Store balance for this date
				dateBalanceMap.set(date, balance);
			}

			// Now, for each date, create a row in the export data
			for (const [date, balance] of dateBalanceMap) {
				exportDataArray.push({
					Account: account.label,
					Date: date,
					Balance: balance.toFixed(2)
				});
			}
		}

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

<p>Import your account data from the previous version of Cash Compass</p>
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
