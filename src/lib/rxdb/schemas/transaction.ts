import { categorySchema } from './category';
import { accountSchema } from './accounts';

// add the string to validate a JSON schema type


export const transactionSchema = {
    $schema: "http://json-schema.org/draft-07/schema#",
    title: 'transaction',
    description: 'A financial transaction',
    version: 0,
    primaryKey: 'id',
    type: 'object',
    properties: {
        id: {
            type: 'string',
            maxLength: 100,
        },
        date: {
            type: 'string',
            format: 'date-time',
        },
        amount: {
            type: 'number',
        },
        category: {
            type: 'object',
            ...categorySchema.properties,
        },
        note: {
            type: 'string',
            maxLength: 500,
        },
        account: {
            type: 'object',
            ...accountSchema.properties,
        },
    },
    required: ['id', 'transactionType', 'date', 'amount', 'category', 'account'],
};