export const categorySchema = {
    title: 'category',
    description: 'A category',
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
    },
    required: ['id', 'label'],
};
