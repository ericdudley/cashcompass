import isEqual from 'lodash-es/isEqual';
import { db } from '..';
import type { Account } from '../models/account';
import type { Category } from '../models/category';

export const UNKNOWN_LABELS = {
	category: 'Uncategorized',
	account: 'Unknown Account'
} as const;

export async function deleteAllData() {
	db.transaction('rw', db.category, db.tx, db.account, async () => {
		await db.category.clear();
		await db.tx.clear();
		await db.account.clear();
	});
}

export async function repairData() {
	console.log('Starting data repair...');
	db.transaction('rw', db.category, db.tx, db.account, async () => {
		console.log('Transaction started.');

		// Ensure that all labels are defined
		await db.category.toCollection().modify((category) => {
			if (!category.label) {
				console.log(
					`Category ${category.id} missing label. Setting to '${UNKNOWN_LABELS.category}'.`
				);
				category.label = UNKNOWN_LABELS.category;
			}
		});

		// Ensure that all accounts have a label
		await db.account.toCollection().modify((account) => {
			if (!account.label) {
				console.log(`Account ${account.id} missing label. Setting to '${UNKNOWN_LABELS.account}'.`);
				account.label = UNKNOWN_LABELS.account;
			}
		});

		const categories = await db.category.toArray();
		const categoriesById = categories.reduce(
			(acc, category) => {
				acc[category.id] = category;
				return acc;
			},
			{} as Record<string, Category>
		);
		const accounts = await db.account.toArray();
		const accountsById = accounts.reduce(
			(acc, account) => {
				acc[account.id] = account;
				return acc;
			},
			{} as Record<string, Account>
		);
		await db.tx.toCollection().modify((tx) => {
			// Ensure that all transactions have a date
			if (!tx.iso8601) {
				console.log(`Transaction ${tx.id} missing date. Setting current date.`);
				tx.iso8601 = new Date().toISOString();
				tx.yyyyMMDd = tx.iso8601.slice(0, 10);
			}

			// Synchronize denormalized data
			if (tx.category) {
				const category = categoriesById[tx.category.id];
				if (category && !isEqual(tx.category, category)) {
					console.log(
						`Synchronizing category label for transaction ${tx.id}.`,
						tx.category,
						category
					);
					tx.category = category;
				}
			}
			if (tx.account) {
				const account = accountsById[tx.account.id];
				if (account && !isEqual(tx.account, account)) {
					console.log(`Synchronizing account label for transaction ${tx.id}.`, tx.account, account);
					tx.account = account;
				}
			}
		});

		console.log('Transaction completed.');
	});
}
