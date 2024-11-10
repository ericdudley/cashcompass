<script lang="ts">
	import { db } from '$lib/dexie';
	import type { Account } from '$lib/dexie/models/account';
	import { asTransaction } from '$lib/dexie/models/transaction';
	import { getIso8601AtMidnight } from '$lib/utils/date';
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
					Account: string;
					Date: string;
					Balance: string;
				}>(result, { header: true });

				db.transaction('rw', db.tx, db.category, db.account, async () => {
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
</script>

<p>Import your account data from the previous version of Cash Compass</p>
<input type="file" class="file-input file-input-bordered w-full max-w-xs" bind:files />

{#if loading}
	<p>Loading...</p>
{/if}
