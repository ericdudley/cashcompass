import type { createRxDatabase, RxCollectionCreator, RxDatabaseBase } from 'rxdb';
import { categorySchema } from './category';
import { transactionSchema } from './transaction';
import { accountSchema } from './accounts';

export const schemas: { [key: string]: RxCollectionCreator<any> } = {
    category: {
        schema: categorySchema,
    },
    account: {
        schema: accountSchema,
    },
    transaction: {
        schema: transactionSchema,
    },
}
