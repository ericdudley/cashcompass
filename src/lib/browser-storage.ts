// browser-storage.ts

// Define the type for localSettings
interface LocalSettings {
	isSidebarPinned: boolean;
	lastAccountId?: string;
}

// Map keys to their corresponding types
interface StorageSchema {
	localSettings: LocalSettings;
}

// Type alias for the keys of the storage schema
type StorageKey = keyof StorageSchema;

const DEFAULT_VALUES: Record<StorageKey, StorageSchema[StorageKey]> = {
	localSettings: {
		isSidebarPinned: false
	}
};

// Create a class to handle storage operations
export class BrowserStorage {
	private storage: Storage;

	constructor(storage: Storage) {
		this.storage = storage;
	}

	// Set an item in storage with type safety
	setItem<K extends StorageKey>(key: K, value: StorageSchema[K]): void {
		const serializedValue = JSON.stringify(value);
		this.storage.setItem(key, serializedValue);
	}

	// Get an item from storage with type safety
	getItem<K extends StorageKey>(key: K): StorageSchema[K] | null {
		const serializedValue = this.storage.getItem(key);
		if (serializedValue === null) {
			return null;
		}
		try {
			return JSON.parse(serializedValue) as StorageSchema[K];
		} catch (error) {
			console.error(`Error parsing storage key "${key}":`, error);
			return null;
		}
	}

	// Merges the current item with the new item
	patchItem<K extends StorageKey>(key: K, value: Partial<StorageSchema[K]>): void {
		const currentValue = this.getItem(key) || DEFAULT_VALUES[key];
		const mergedValue = {
			...currentValue,
			...value
		};
		this.setItem(key, mergedValue);
	}

	// Remove an item from storage
	removeItem<K extends StorageKey>(key: K): void {
		this.storage.removeItem(key);
	}

	// Clear all items from storage
	clear(): void {
		this.storage.clear();
	}

	static from(storage: Storage) {
		return new BrowserStorage(storage);
	}
}
