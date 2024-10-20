import { getContext } from 'svelte';
import type { CashCompassDexie } from './dexie';

export function getDbContext() {
	return getContext<CashCompassDexie>('db');
}
