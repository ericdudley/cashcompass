<script lang="ts">
	import { browser } from '$app/environment';
	import { beforeNavigate } from '$app/navigation';
	import { page } from '$app/stores';
	import AppLogo from '$lib/components/ui/app-logo.svelte';
	import AccountIcon from '$lib/components/ui/icons/account-icon.svelte';
	import CategoryIcon from '$lib/components/ui/icons/category-icon.svelte';
	import HomeIcon from '$lib/components/ui/icons/home-icon.svelte';
	import MenuIcon from '$lib/components/ui/icons/menu-icon.svelte';
	import TransactionIcon from '$lib/components/ui/icons/transaction-icon.svelte';
	import UserIcon from '$lib/components/ui/icons/user-icon.svelte';
	import { db, initDb } from '$lib/dexie';
	import { Routes } from '$lib/routes';
	import { onMount, setContext, type Component, type Snippet } from 'svelte';
	import '../app.css';

	onMount(async () => {
		const flowbite = await import('flowbite');
		flowbite.initFlowbite();
	});

	if (browser) {
		setContext('db', initDb());
	}

	beforeNavigate((navigation) => {
		const sidebar = document.getElementById('logo-sidebar');
		const sidebarToggle = document.getElementById('logo-sidebar-toggle');

		// If the sidebar is not open, do nothing
		if (sidebar?.getAttribute('role') !== 'dialog') {
			return;
		}

		// Close the sidebar
		sidebarToggle?.click();
	});

	let {
		children
	}: {
		children: Snippet;
	} = $props();

	let onSync = async () => {
		await db.cloud.sync();
	};

	let onLogout = () => {
		db.cloud.logout();
	};
</script>

<nav class="fixed top-0 z-50 w-full bg-base-200 border-b border-base-200">
	<div class="px-3 py-3 lg:px-5 lg:pl-3">
		<div class="flex items-center justify-between">
			<div class="flex items-center justify-start rtl:justify-end">
				<button
					id="logo-sidebar-toggle"
					data-drawer-target="logo-sidebar"
					data-drawer-toggle="logo-sidebar"
					aria-controls="logo-sidebar"
					type="button"
					class="inline-flex items-center p-2 text-sm rounded-lg sm:hidden hover:bg-neutral focus:outline-none focus:ring-2 focus:ring-neutral-300"
				>
					<span class="sr-only">Open sidebar</span>
					<MenuIcon />
				</button>
				<a href="/" class="flex ms-2 md:me-24">
					<AppLogo showTitle />
				</a>
			</div>
			<div class="flex items-center">
				<div class="flex items-center ms-3">
					<div>
						<button
							type="button"
							class="flex text-sm rounded-full focus:ring-4 focus:ring-primary p-1 hover:bg-primary"
							aria-expanded="false"
							data-dropdown-toggle="dropdown-user"
						>
							<span class="sr-only">Open user menu</span>
							<UserIcon />
						</button>
					</div>
					<div
						class="z-50 hidden my-4 list-none bg-base-300 divide-y divide-neutral rounded shadow"
						id="dropdown-user"
					>
						<div class="px-4 py-3" role="none">
							<p class="text-sm">Sims</p>
							<p class="text-sm font-medium truncate" role="none">neil.sims@flowbite.com</p>
						</div>
						<ul class="py-1" role="none">
							{#snippet menuItem({ route, title }: { route: string; title: string })}
								<li>
									<a
										href={route}
										class="block px-4 py-2 text-sm hover:bg-primary-400 {$page.route.id === route
											? 'bg-primary-700 text-primary-content'
											: ''}"
										role="menuitem">{title}</a
									>
								</li>
							{/snippet}
							{@render menuItem({ route: Routes.settings, title: 'Settings' })}
							<li>
								<button
									class="block w-full px-4 py-2 text-sm text-left hover:bg-primary-400"
									role="menuitem"
									onclick={onSync}
								>
									Sync
								</button>
							</li>
							<li>
								<button
									class="block w-full px-4 py-2 text-sm text-left hover:bg-primary-400"
									role="menuitem"
									onclick={onLogout}
								>
									Logout
								</button>
							</li>
						</ul>
					</div>
				</div>
			</div>
		</div>
	</div>
</nav>

<aside
	id="logo-sidebar"
	class="fixed top-0 left-0 z-40 w-screen h-screen pt-20 transition-transform -translate-x-full bg-base-300 sm:w-64 sm:translate-x-0"
	aria-label="Sidebar"
>
	<div class="h-full px-3 pb-4 overflow-y-auto bg-base-300">
		<ul class="space-y-2 font-medium">
			{#snippet sidebarItem({
				route,
				Icon,
				title
			}: {
				route: string;
				Icon: Component;
				title: string;
			})}
				<li>
					<a
						href={route}
						class="flex items-center p-2 rounded-lg group hover:text-base-content hover:bg-base-200 {(route === '/' &&
							$page.route.id === route) ||
						(route !== '/' && $page.route.id?.startsWith(route))
							? 'bg-primary text-primary-content'
							: ''}"
					>
						<Icon class="w-5 h-5 transition duration-75" />
						<span class="ms-3">{title}</span>
					</a>
				</li>
			{/snippet}
			{@render sidebarItem({ route: Routes.home, Icon: HomeIcon, title: 'Home' })}
			{@render sidebarItem({ route: Routes.accounts, Icon: AccountIcon, title: 'Accounts' })}
			{@render sidebarItem({
				route: Routes.transactions,
				Icon: TransactionIcon,
				title: 'Transactions'
			})}
			{@render sidebarItem({ route: '/categories', Icon: CategoryIcon, title: 'Categories' })}
		</ul>
	</div>
</aside>

<div class="p-8 sm:ml-64 mt-14">
	{@render children()}
</div>
