import type { Account } from './account';
import type { Category } from './category';

export type Transaction = {
	id: string;
	unixMs: number;
	yyyyMMDd: string;
	amount: number;
	category?: Category;
	account?: Account;
	label?: string;
};
