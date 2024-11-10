import type { Account } from './account';
import type { Category } from './category';

export type Transaction = {
	id: string;
	iso8601: string;
	yyyyMMDd: string; // Set in a Dexie.js hook automatically
	amount: number;
	category?: Category;
	account?: Account;
	label?: string;
};

export type TransactionInput = Omit<Transaction, 'yyyyMMDd'>;

export function asTransaction(input: TransactionInput): Transaction {
	return {
		...input,
		// Will be set by Dexie.js hook
		yyyyMMDd: ''
	};
}
