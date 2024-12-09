import type { Category } from '$lib/dexie/models/category';
import Dexie, { type EntityTable } from 'dexie';
import type { Transaction } from './models/transaction';
import { dexieCloud } from 'dexie-cloud-addon';
import type { Account } from './models/account';
import { UNKNOWN_LABELS } from './utils/common';

export type CashCompassDexie = Dexie & {
	category: EntityTable<Category, 'id'>;
	tx: EntityTable<Transaction, 'id'>;
	account: EntityTable<Account, 'id'>;
};

export let db: CashCompassDexie;

export function initDb() {
	if (db) {
		return;
	}

	db = new Dexie('cashcompass', {
		addons: [dexieCloud]
	}) as CashCompassDexie;

	// Schema declaration:
	db.version(1).stores({
		category: 'id, label',
		tx: 'id, iso8601, yyyyMMDd, amount, category.id, category.label, label, account.id, account.accountType',
		account: 'id, label, accountType'
	});

	const isLocal = window.location.hostname === 'localhost';
	const databaseUrl = isLocal ? 'https://zosfaqgud.dexie.cloud' : 'https://zknh9tjsp.dexie.cloud';
	db.cloud.configure({
		databaseUrl,
		requireAuth: true
	});

	// TODO Integrate this state into the UI
	db.cloud.syncState.subscribe((state) => {
		console.log('Sync state:', state);
	});
	// Ensure that all categories have a label
	db.category.hook('creating', function (primKey, category, transaction) {
		if (!category.label) {
			category.label = UNKNOWN_LABELS.category;
		}
	});
	db.category.hook('updating', function (mods: Partial<Category>, primKey, category, transaction) {
		if (
			// If the label is being set to an empty string
			(mods.hasOwnProperty('label') && !mods.label) ||
			// If the label isn't being touched but is empty
			(!mods.hasOwnProperty('label') && !category.label)
		) {
			return {
				label: UNKNOWN_LABELS.category
			};
		}
	});

	db.account.hook('creating', function (primKey, account, transaction) {
		if (!account.label) {
			account.label = UNKNOWN_LABELS.account;
		}
	});
	db.account.hook('updating', function (mods: Partial<Account>, primKey, account, transaction) {
		if (
			// If the label is being set to an empty string
			(mods.hasOwnProperty('label') && !mods.label) ||
			// If the label isn't being touched but is empty
			(!mods.hasOwnProperty('label') && !account.label)
		) {
			return {
				label: UNKNOWN_LABELS.account
			};
		}
	});

	db.tx.hook('creating', function (primKey, tx, transaction) {
		tx.yyyyMMDd = tx.iso8601.slice(0, 10);
	});
	db.tx.hook('updating', function (mods: Partial<Transaction>, primKey, tx, transaction) {
		if (mods.hasOwnProperty('iso8601') && typeof mods.iso8601 === 'string') {
			return {
				yyyyMMDd: mods.iso8601.slice(0, 10)
			};
		}
	});

	return db;
}
