import { addRxPlugin, createRxDatabase, type RxCollection, type RxDatabase } from 'rxdb';
import { RxDBDevModePlugin } from 'rxdb/plugins/dev-mode';
import { getRxStorageDexie } from 'rxdb/plugins/storage-dexie';
import { schemas } from './schemas';
import type { Category } from './models/types';

type CashCompassDatabase = RxDatabase<{
	category: RxCollection<Category>
}>

class DatabaseManager {
	private static instance: DatabaseManager;
	private db: CashCompassDatabase | null = null;

	private constructor() {
		addRxPlugin(RxDBDevModePlugin);
	}

	public static getInstance(): DatabaseManager {
		if (!DatabaseManager.instance) {
			DatabaseManager.instance = new DatabaseManager();
		}
		return DatabaseManager.instance;
	}

	public async getDB(): Promise<CashCompassDatabase> {
		if (!this.db) {
			this.db = await createRxDatabase<CashCompassDatabase>({
				name: 'cash-compass-db',
				storage: getRxStorageDexie(),
				ignoreDuplicate: true
			});


			await this.db.addCollections(schemas);
		}
		return this.db;
	}
}

export const dbManager = DatabaseManager.getInstance();
