# Database Documentation

Cash Compass uses an offline-first approach for data storage. This means that all data is stored locally on the user's device by default.

## Collections

### Category

Categories are used to group transactions.

| Field   | Type     | Description                           |
| ------- | -------- | ------------------------------------- |
| `id`    | `string` | Unique identifier for the category.   |
| `label` | `string` | The name of the category.             |
| `color` | `string` | Color code for visual representation. |

JSON Schema:
