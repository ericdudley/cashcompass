import type { Category } from './category';

export type Account = {
	id: string;
	label: string;
	accountType: 'expenses' | 'net_worth';
};
