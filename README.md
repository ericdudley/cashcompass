
IOS Deploy
1. `npm run tauri ios build -- --export-method app-store-connect`
2. `xcrun altool --upload-app --type ios --file "[PATHTOREPO]/src-tauri/gen/apple/build/arm64/cashcompass.ipa" --apiKey $APPLE_API_KEY_ID --apiIssuer $APPLE_API_ISSUER`

Make sure to get dexie-cloud.json and dexie-cloud.key setup for local development.


# create-svelte

Everything you need to build a Svelte project, powered by [`create-svelte`](https://github.com/sveltejs/kit/tree/main/packages/create-svelte).

## Creating a project

If you're seeing this, you've probably already done this step. Congrats!

```bash
# create a new project in the current directory
npm create svelte@latest

# create a new project in my-app
npm create svelte@latest my-app
```

## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```bash
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of your app:

```bash
npm run build
```

You can preview the production build with `npm run preview`.

> To deploy your app, you may need to install an [adapter](https://kit.svelte.dev/docs/adapters) for your target environment.
