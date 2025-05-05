import type { CashCompassDexie } from "..";

export type Account = {
	id: string;
	label: string;
	accountType: 'expenses' | 'net_worth';
	isArchived: 0 | 1;
};

export const AccountUtils = {
	getUnarchived: (db: CashCompassDexie) => db.account.where('isArchived').equals(0),
	getArchived: (db: CashCompassDexie) => db.account.where('isArchived').notEqual(0),
};
