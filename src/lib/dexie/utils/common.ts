import { db } from '..';

export async function deleteAllData() {
	db.transaction('rw', db.category, db.tx, db.account, async () => {
		await db.category.clear();
		await db.tx.clear();
		await db.account.clear();
	});
}
