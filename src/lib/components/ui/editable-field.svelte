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

	let isEditing = $state(false);
	let tempValue = $state(value);

	function enableEdit() {
		tempValue = value;
		isEditing = true;
	}

	function save() {
		value = tempValue;
		isEditing = false;
		onSave(value);
	}

	function cancel() {
		tempValue = value;
		isEditing = false;
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			save();
		} else if (event.key === 'Escape') {
			cancel();
		}
	}

	function handleClickOutside(event: MouseEvent) {
		if (!(event.target as HTMLElement).closest('.editable-field')) {
			cancel();
		}
	}

	onDestroy(() => {
		window.removeEventListener('click', handleClickOutside);
	});
</script>

{#if isEditing}
	<div class="relative">
		{#if InputComponent}
			<InputComponent
				bind:value={tempValue}
				onkeydown={handleKeydown}
				onblur={save}
				autofocus
				class="input input-sm input-bordered w-full"
			/>
		{:else}
			<input
				bind:value={tempValue}
				onkeydown={handleKeydown}
				class="input input-sm input-bordered w-full"
				autofocus
				onblur={save}
			/>
		{/if}
		<div
			class="absolute top-0 left-1/2 flex items-center transform -translate-y-full -translate-x-1/2 gap-2 z-[100]"
		>
			<button onclick={save} class="flex-1 btn btn-sm btn-success flex-nowrap">
				Save
				<IconParkOutlineEnterKey />
			</button>
			<button onclick={cancel} class="flex-1 btn btn-sm btn-error ml-2 flex-nowrap">
				Cancel
				<KeyboardEsc />
			</button>
		</div>
	</div>
{:else}
	<span
		class="editable-field flex items-center gap-1 hover:cursor-pointer hover:border-b-2 hover:border-b-primary focus:border-b-2 focus:border-b-primary"
		onclick={enableEdit}
		tabindex="0"
		onfocus={enableEdit}
	>
		{#if displaySnippet}
			{@render displaySnippet()}
		{:else}
			<span>
				{value}
			</span>
		{/if}
		{#if !!showEditIcon}
			<span>
				<Pencil />
			</span>
		{/if}
	</span>
{/if}

<style>
	.editable-field .edit-icon {
		opacity: 0;
		transition: opacity 0.3s ease;
	}

	.editable-field:hover .edit-icon {
		opacity: 1;
	}
</style>
