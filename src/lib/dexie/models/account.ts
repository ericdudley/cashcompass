import type { CashCompassDexie } from "..";

export type Account = {
	id: string;
	label: string;
	accountType: 'expenses' | 'net_worth';
	isArchived: 0 | 1;
};

export const AccountUtils = {
	getUnarchived: (db: CashCompassDexie) => db.account.filter(a => !a.isArchived),
	getArchived: (db: CashCompassDexie) => db.account.filter(a => !!a.isArchived)
};
