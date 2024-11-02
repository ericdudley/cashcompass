<script lang="ts">
	import { onDestroy, type Snippet } from 'svelte';
	import Pencil from 'virtual:icons/mdi/pencil';
	import IconParkOutlineEnterKey from 'virtual:icons/icon-park-outline/enter-key';
	import KeyboardEsc from 'virtual:icons/mdi/keyboard-esc';

	let {
		value,
		onSave,
		showEditIcon,
		InputComponent,
		displaySnippet
	}: {
		value: any;
		onSave: (value: any) => void;
		showEditIcon?: boolean;
		InputComponent?: any;
		displaySnippet?: Snippet;
	} = $props();

	let inputRef: HTMLInputElement | null = $state(null);

	let isEditing = $state(false);
	let tempValue = $state(value);

	$effect(() => {
		if (isEditing && !!inputRef) {
			inputRef.focus();
		}
	});

	function enableEdit() {
		tempValue = value;
		isEditing = true;
		window.addEventListener('click', handleClickOutside);
	}

	function save() {
		value = tempValue;
		isEditing = false;
		onSave(value);
		window.removeEventListener('click', handleClickOutside);
	}

	function cancel() {
		tempValue = value;
		isEditing = false;
		window.removeEventListener('click', handleClickOutside);
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			save();
		} else if (event.key === 'Escape') {
			cancel();
		}
	}

	function handleClickOutside(event: MouseEvent) {
		if (
			!(event.target as HTMLElement).closest('.editable-field') &&
			!(event.target as HTMLElement).closest('.editing-overlay')
		) {
			cancel();
		}
	}

	onDestroy(() => {
		window.removeEventListener('click', handleClickOutside);
	});
</script>

<div class="relative inline-block editable-field">
	<!-- Display component -->
	<button
		class="editable-field flex items-center gap-1 hover:cursor-pointer hover:border-b-2 hover:border-b-primary focus:border-b-2 focus:border-b-primary"
		onclick={enableEdit}
		tabindex="0"
		onfocus={enableEdit}
	>
		{#if displaySnippet}
			{@render displaySnippet()}
		{:else}
			<span>{value}</span>
		{/if}
		{#if !!showEditIcon}
			<span>
				<Pencil />
			</span>
		{/if}
	</button>

	{#if isEditing}
		<!-- Input and buttons -->
		<div
			class="absolute top-0 left-1/2 h-full flex items-center justify-center z-10 transform -translate-x-1/2 editing-overlay"
		>
			<div class="relative w-fit h-fit min-w-32 bg-base-300/90 p-6 rounded-md">
				{#if InputComponent}
					<InputComponent
						bind:value={tempValue}
						onkeydown={handleKeydown}
						autofocus
						class="input input-sm input-bordered w-fit editable-field"
					/>
				{:else}
					<input
						bind:this={inputRef}
						bind:value={tempValue}
						onkeydown={handleKeydown}
						class="input input-sm input-bordered w-fit editable-field"
						autofocus
					/>
				{/if}

				<!-- Save/Cancel buttons above the input -->
				<div
					class="flex items-center gap-4 absolute bottom-full mb-1 left-1/2 transform -translate-x-1/2"
				>
					<button onclick={save} class="btn btn-sm btn-success flex-nowrap">
						Save
						<IconParkOutlineEnterKey />
					</button>
					<button onclick={cancel} class="btn btn-sm btn-error flex-nowrap">
						Cancel
						<KeyboardEsc />
					</button>
				</div>
			</div>
		</div>
	{/if}
</div>
