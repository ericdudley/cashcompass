export const accountSchema = {
    title: 'account',
    description: 'An account',
    version: 0,
    primaryKey: 'id',
    type: 'object',
    properties: {
        id: {
            type: 'string',
            maxLength: 100,
        },
        label: {
            type: 'string',
            maxLength: 100,
        },
        isIncludedInNetWorth: {
            type: 'boolean',
        },
    },
    required: ['id', 'label'],
}
