<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import AppLogo from '$lib/components/ui/app-logo.svelte';
	import { page } from '$app/stores';
	import type { Snippet } from 'svelte';
	import { BrowserStorage } from '$lib/browser-storage';
	import MenuIcon from 'virtual:icons/mdi/menu';

	let { children }: { children: Snippet } = $props();

	let isDrawerOpen = $state(false);
	let isDrawerPinned = $state(false);

	onMount(() => {
		const pinned = BrowserStorage.from(localStorage).getItem('localSettings')?.isSidebarPinned;

		if (pinned) {
			isDrawerPinned = true;
			isDrawerOpen = true;
		}
	});

	function toggleDrawer() {
		if (!isDrawerPinned) {
			isDrawerOpen = !isDrawerOpen;
		}
	}

	function togglePin() {
		isDrawerPinned = !isDrawerPinned;
		if (isDrawerPinned) {
			isDrawerOpen = true;
		}
	}

	$effect(() => {
		if (isDrawerPinned) {
			isDrawerOpen = true;
			BrowserStorage.from(localStorage).patchItem('localSettings', { isSidebarPinned: true });
		} else {
			BrowserStorage.from(localStorage).patchItem('localSettings', { isSidebarPinned: false });
		}
	});
</script>

<div class="flex h-screen overflow-hidden">
	<!-- Sidebar -->
	<div class="sidebar {isDrawerOpen ? 'open' : 'closed'}">
		<!-- Sidebar content -->
		<ul class="h-full overflow-y-auto pt-4">
			<li>
				<a href="/" class:font-bold={$page.url.pathname === '/'}> Dashboard </a>
			</li>
			<li>
				<a href="/transactions" class:font-bold={$page.url.pathname === '/transactions'}>
					Transactions
				</a>
			</li>
			<li>
				<a href="/categories" class:font-bold={$page.url.pathname === '/categories'}>
					Categories
				</a>
			</li>
			<li>
				<a href="/accounts" class:font-bold={$page.url.pathname === '/accounts'}> Accounts </a>
			</li>
			<li>
				<a href="/settings" class:font-bold={$page.url.pathname === '/settings'}> Settings </a>
			</li>
		</ul>
	</div>

	<!-- Main Content -->
	<div class="content {isDrawerOpen ? 'shifted' : ''}">
		<!-- Navbar -->
		<div class="flex items-center bg-base-300 shadow px-4 h-16">
			<!-- Drawer Toggle Button -->
			<button onclick={toggleDrawer} class="mr-4">
				<MenuIcon />
			</button>
			<!-- Pin Button -->
			<button onclick={togglePin} class="mr-4">
				{isDrawerPinned ? 'Unpin' : 'Pin'}
			</button>
			<!-- App Logo -->
			<div class="flex-1">
				<AppLogo />
			</div>
		</div>

		<!-- Main Content Area -->
		<div class="flex-1 overflow-auto p-4">
			{@render children()}
		</div>
	</div>
</div>

<style>
	/* Sidebar styles */
	.sidebar {
		transition: width 0.3s ease-in-out;
		overflow: hidden;
	}
	.sidebar.open {
		width: 16rem; /* 256px */
	}
	.sidebar.closed {
		width: 0;
	}

	/* Content styles */
	.content {
		flex: 1;
		display: flex;
		flex-direction: column;
		transition: margin-left 0.3s ease-in-out;
	}
	.content.shifted {
		margin-left: 0rem; /* 256px */
	}
</style>
